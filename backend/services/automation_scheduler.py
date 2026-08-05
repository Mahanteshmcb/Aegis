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
from datetime import timedelta

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

        # Simulate doing work
        await asyncio.sleep(2)

        # Mark success
        log.status = "success"
        log.output = f"Simulated execution of '{job.command}'"
        log.finished_at = datetime.utcnow()
        session.add(log)

        job.status = "completed"
        if job.recurring and job.scheduled_at:
            # Simple recurring behaviour: schedule next occurrence +24h
            job.scheduled_at = job.scheduled_at + timedelta(days=1)
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

                pending_jobs = (
                    session.query(AutomationJob)
                    .filter(AutomationJob.status == "pending")
                    .filter(AutomationJob.scheduled_at != None)
                    .filter(AutomationJob.scheduled_at <= now)
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
