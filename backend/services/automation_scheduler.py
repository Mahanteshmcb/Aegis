"""
Simple automation scheduler and job-runner for demo/testing.

This module provides a background task that polls for pending jobs
and executes them (simulated). Designed to be lightweight and
easy to reason about for Day 63 work.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from backend.database import SessionLocal
from backend.models.lab_automation import AutomationJob, AutomationExecutionLog
from backend.models.hvac_schedule import HVACSchedule
from backend.models.safety import SafetyRule, SafetyEvent, EmergencyStop
from backend import models_db as models_db
from backend.services import broadcast
from backend import realtime
from backend import models_scene as scene_models
from backend.services import scene as scene_service
from datetime import timedelta
try:
    from croniter import croniter
except Exception:
    croniter = None

logger = logging.getLogger(__name__)


async def _execute_job(session, job: AutomationJob):
    """Execute a job (simulation) and write execution logs."""
    try:
        logger.info(f"Executing job id={job.id} name={job.name}")
        # Final safety check before turning devices on
        blocked, reason, rule_id = check_safety_for_tenant(session, job.tenant_id)
        if blocked:
            logger.warning(f"Job id={job.id} blocked by safety at execution time: {reason}")
            job.status = "blocked"
            session.add(job)
            evt = SafetyEvent(tenant_id=job.tenant_id, rule_id=rule_id, message=f"Job {job.id} blocked at execution: {reason}", severity="critical")
            session.add(evt)
            session.commit()
            # publish event to SSE clients
            try:
                await broadcast.publish({
                    "type": "safety_event",
                    "tenant_id": job.tenant_id,
                    "message": evt.message,
                    "severity": evt.severity,
                    "source": "scheduler",
                })
            except Exception:
                logger.exception("Failed to publish safety event")
            return

        job.status = "running"
        session.add(job)
        session.commit()

        log = AutomationExecutionLog(
            job_id=job.id,
            device_id=job.device_id,
            tenant_id=job.tenant_id,
            status="started",
            started_at=datetime.utcnow(),
        )
        session.add(log)
        session.commit()

        # Emit the command to realtime clients so devices/controllers can act on it
        try:
            payload = {
                "job_id": job.id,
                "device_id": job.device_id,
                "tenant_id": job.tenant_id,
                "command": job.command,
                "parameters": job.parameters or {},
            }
            # event name is flexible; use 'automation:job' and also emit a more specific event if available
            await realtime.sio.emit("automation:job", payload)
            # also emit specific command event for robot devices
            await realtime.sio.emit(f"{job.command}", payload)
        except Exception:
            logger.exception("Failed to emit automation job realtime event")

        # Apply simple effects for jobs that target scene entities (demo automation)
        try:
            if job.device_id:
                # interpret parameters for simple move: {dx, dy, dz}
                dx = (job.parameters or {}).get("dx") or (job.parameters or {}).get("x_delta") or 0
                dy = (job.parameters or {}).get("dy") or (job.parameters or {}).get("y_delta") or 0
                dz = (job.parameters or {}).get("dz") or (job.parameters or {}).get("z_delta") or 0
                ent = session.query(scene_models.SceneEntity).filter(scene_models.SceneEntity.id == job.device_id).first()
                if ent:
                    ent.x = (ent.x or 0) + float(dx)
                    ent.y = (ent.y or 0) + float(dy)
                    ent.z = (ent.z or 0) + float(dz)
                    session.add(ent)
                    session.commit()
                    session.refresh(ent)
                    # broadcast updated entity to clients
                    try:
                        await scene_service.broadcast_entity_update({
                            "id": ent.id,
                            "name": ent.name,
                            "type": ent.type,
                            "x": ent.x,
                            "y": ent.y,
                            "z": ent.z,
                            "rotation": ent.rotation,
                            "state": ent.state or {},
                        })
                    except Exception:
                        logger.exception("Failed to broadcast entity update after job execution")
        except Exception:
            logger.exception("Failed to apply job effects to scene entity")

        # Simulate doing work
        await asyncio.sleep(2)

        # Mark success
        log.status = "success"
        log.output = f"Simulated execution of '{job.command}'"
        log.finished_at = datetime.utcnow()
        session.add(log)

        job.status = "completed"
        if job.recurring:
            # Prefer cron expressions when available
            if job.cron and croniter is not None:
                try:
                    base = job.scheduled_at or datetime.utcnow()
                    it = croniter(job.cron, base)
                    job.scheduled_at = it.get_next(datetime)
                    job.status = "pending"
                except Exception:
                    # Fallback to daily recurrence if cron parsing fails
                    job.scheduled_at = (job.scheduled_at or datetime.utcnow()) + timedelta(days=1)
                    job.status = "pending"
            else:
                # Simple recurring behaviour: schedule next occurrence +24h
                job.scheduled_at = (job.scheduled_at or datetime.utcnow()) + timedelta(days=1)
                job.status = "pending"
        session.add(job)
        session.commit()
        logger.info(f"Job id={job.id} completed")

    except Exception as exc:
        logger.exception("Job execution failed: %s", exc)
        try:
            job.status = "failed"
            session.add(job)
            session.commit()
        except Exception:
            session.rollback()


async def _poll_loop(stop_event: asyncio.Event):
    """Polling loop that looks for due jobs and executes them."""
    logger.info("Automation scheduler started")
    try:
        while not stop_event.is_set():
            try:
                session = SessionLocal()
                now = datetime.utcnow()
                # First, handle HVAC schedules: create AutomationJob entries for due schedules
                due_schedules = (
                    session.query(HVACSchedule)
                    .filter(HVACSchedule.enabled == True)
                    .filter(HVACSchedule.scheduled_at <= now)
                    .all()
                )
                for sched in due_schedules:
                    try:
                        # Safety check: if estop active or rules violated, create event and skip
                        blocked, reason, rule_id = check_safety_for_tenant(session, sched.tenant_id)
                        if blocked:
                            evt = SafetyEvent(tenant_id=sched.tenant_id, rule_id=rule_id, message=f"Schedule {sched.id} blocked: {reason}", severity="critical")
                            session.add(evt)
                            session.commit()
                            try:
                                await broadcast.publish({
                                    "type": "safety_event",
                                    "tenant_id": sched.tenant_id,
                                    "message": evt.message,
                                    "severity": evt.severity,
                                    "source": "scheduler",
                                })
                            except Exception:
                                logger.exception("Failed to publish schedule safety event")
                            continue

                        job = AutomationJob(
                            tenant_id=sched.tenant_id,
                            device_id=None,
                            name=f"HVAC: {sched.name}",
                            command="set_setpoint",
                            parameters={"zone_id": sched.zone_id, "setpoint": sched.setpoint},
                            scheduled_at=now,
                            recurring=False,
                            status="pending",
                        )
                        session.add(job)
                        # update next run or disable
                        if sched.recurring and sched.interval_days:
                            sched.scheduled_at = sched.scheduled_at + timedelta(days=sched.interval_days)
                        else:
                            sched.enabled = False
                        session.add(sched)
                        session.commit()
                    except Exception:
                        session.rollback()

                from sqlalchemy import or_

                pending_jobs = (
                    session.query(AutomationJob)
                    .filter(AutomationJob.status == "pending")
                    .filter(or_(AutomationJob.scheduled_at == None, AutomationJob.scheduled_at <= now))
                    .all()
                )
                for job in pending_jobs:
                    # Safety check before execution
                    blocked, reason, rule_id = check_safety_for_tenant(session, job.tenant_id)
                    if blocked:
                        logger.warning(f"Job id={job.id} blocked by safety: {reason}")
                        job.status = "blocked"
                        session.add(job)
                        evt = SafetyEvent(tenant_id=job.tenant_id, rule_id=rule_id, message=f"Job {job.id} blocked before execution: {reason}", severity="critical")
                        session.add(evt)
                        session.commit()
                        try:
                            await broadcast.publish({
                                "type": "safety_event",
                                "tenant_id": job.tenant_id,
                                "message": evt.message,
                                "severity": evt.severity,
                                "source": "scheduler",
                            })
                        except Exception:
                            logger.exception("Failed to publish blocked job event")
                        continue
                    # Execute jobs sequentially for now
                    await _execute_job(session, job)
            except Exception as e:
                logger.exception("Error in scheduler poll loop: %s", e)
            finally:
                try:
                    session.close()
                except Exception:
                    pass

            await asyncio.wait([stop_event.wait()], timeout=5)

    except asyncio.CancelledError:
        logger.info("Automation scheduler cancelled")


def check_safety_for_tenant(session, tenant_id: int):
    """Return (blocked: bool, reason: str, rule_id: Optional[int])"""
    # Check emergency stop
    est = session.query(EmergencyStop).filter(EmergencyStop.tenant_id == tenant_id).first()
    if est and est.active:
        return True, f"Emergency Stop active: {est.reason}", None

    # Check safety rules
    rules = session.query(SafetyRule).filter(SafetyRule.tenant_id == tenant_id, SafetyRule.enabled == True).all()
    for rule in rules:
        # Find sensors of matching type for this tenant
        sensors = session.query(models_db.Sensor).filter(models_db.Sensor.tenant_id == tenant_id).filter(models_db.Sensor.type.ilike(f"%{rule.sensor_type}%")).all()
        for s in sensors:
            last = s.last_reading or {}
            # metric path e.g., 'co2.ppm' or 'value'
            parts = rule.metric.split('.')
            val = last
            try:
                for p in parts:
                    if isinstance(val, dict):
                        val = val.get(p)
                    else:
                        val = None
                        break
            except Exception:
                val = None
            if val is None:
                continue
            try:
                v = float(val)
            except Exception:
                continue
            if rule.operator == 'gt' and v > rule.threshold:
                return True, f"Rule '{rule.name}' violated: {rule.metric}={v} > {rule.threshold}", rule.id
            if rule.operator == 'lt' and v < rule.threshold:
                return True, f"Rule '{rule.name}' violated: {rule.metric}={v} < {rule.threshold}", rule.id
    return False, '', None


class AutomationScheduler:
    def __init__(self):
        self._task = None
        self._stop_event = asyncio.Event()

    def start(self):
        if self._task is None:
            self._stop_event = asyncio.Event()
            self._task = asyncio.create_task(_poll_loop(self._stop_event))
        return self._task

    async def stop(self):
        if self._task:
            self._stop_event.set()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


_global_scheduler = AutomationScheduler()


def get_scheduler():
    return _global_scheduler
