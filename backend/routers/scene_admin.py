from fastapi import APIRouter, HTTPException
from typing import Dict

from backend.database import SessionLocal
from backend import models_scene as models
from backend.services import scene_simulator
from backend.services import scene as scene_service
from backend import realtime
from backend.models.lab_automation import AutomationJob
from datetime import datetime
from fastapi import Request
try:
    from croniter import croniter
except Exception:
    croniter = None
try:
    from dateutil import parser as dateutil_parser
except Exception:
    dateutil_parser = None

router = APIRouter(prefix="/api/v1/scene/admin", tags=["scene-admin"])


@router.post("/pause")
def pause_simulation():
    scene_simulator.pause_simulation()
    return {"status": "paused"}


@router.post("/resume")
def resume_simulation():
    scene_simulator.resume_simulation()
    return {"status": "running"}


@router.post("/speed")
def set_speed(payload: Dict[str, float]):
    """Set simulation tick speed in seconds via JSON `{ "seconds": 0.5 }`"""
    sec = payload.get("seconds")
    if sec is None:
        raise HTTPException(status_code=400, detail="Missing 'seconds' in payload")
    ok = scene_simulator.set_tick_seconds(sec)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid seconds value; must be > 0")
    return {"status": "ok", "seconds": scene_simulator.get_tick_seconds()}


@router.get("/status")
def simulation_status():
    return {"running": scene_simulator.is_running(), "tick_seconds": scene_simulator.get_tick_seconds()}



@router.post("/command")
def send_command(payload: Dict):
    """Send a generic command to realtime clients. Example payload: {"event":"robot:command","target_id":1,"command":"start","params":{}}"""
    event = payload.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing 'event' in payload")
    try:
        # best-effort emit
        realtime.sio.emit(event, payload)
    except Exception:
        realtime.logger.exception("Failed to emit command event")
    return {"sent": True, "event": event}


@router.post("/job")
def create_job(request: Request, payload: Dict):
    """Create a one-off AutomationJob for the automation scheduler.

    Example payload: {"name":"Move Tractor","command":"move","parameters":{"dx":1}, "scheduled_at": "2026-08-15T12:00:00"}
    """
    try:
        # Role-based basic check via header 'X-User-Role' (operator/admin)
        role = (request.headers.get('x-user-role') or '').lower()
        if role not in ('admin', 'operator'):
            raise HTTPException(status_code=403, detail='Insufficient role to create jobs')

        name = payload.get("name") or payload.get("command")
        cmd = payload.get("command")
        params = payload.get("parameters") or {}
        scheduled = payload.get("scheduled_at")
        recurring = bool(payload.get("recurring", False))
        tenant_id = payload.get("tenant_id", 1)
        device_id = payload.get("device_id")
        cron_expr = payload.get("cron")

        # If device_id is provided, require admin role
        if device_id and role != 'admin':
            raise HTTPException(status_code=403, detail='Admin role required to target devices')

        # Parse scheduled_at with timezone-aware parser if available
        scheduled_at = None
        if scheduled:
            try:
                if dateutil_parser:
                    scheduled_at = dateutil_parser.isoparse(scheduled)
                else:
                    scheduled_at = datetime.fromisoformat(scheduled)
            except Exception:
                scheduled_at = None

        # If cron is provided and no explicit scheduled_at, try to compute next occurrence
        if cron_expr and not scheduled_at:
            if croniter is None:
                # croniter not available: store cron string but do not compute next run
                scheduled_at = None
            else:
                try:
                    base = datetime.utcnow()
                    it = croniter(cron_expr, base)
                    scheduled_at = it.get_next(datetime)
                except Exception:
                    scheduled_at = None

        job = AutomationJob(
            tenant_id=tenant_id,
            device_id=device_id,
            name=name,
            command=cmd,
            parameters=params,
            scheduled_at=scheduled_at,
            cron=cron_expr,
            recurring=recurring,
            status="pending",
        )
        with SessionLocal() as db:
            db.add(job)
            db.commit()
            db.refresh(job)
            return {"id": job.id, "name": job.name, "status": job.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
def list_jobs():
    try:
        with SessionLocal() as db:
            rows = db.query(AutomationJob).order_by(AutomationJob.created_at.desc()).limit(50).all()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "command": r.command,
                    "parameters": r.parameters,
                    "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
                    "status": r.status,
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job/{job_id}/cancel")
def cancel_job(job_id: int):
    try:
        with SessionLocal() as db:
            job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            job.status = "cancelled"
            db.add(job)
            db.commit()
            return {"id": job.id, "status": job.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/logs")
def job_logs(job_id: int):
    try:
        from backend.models.lab_automation import AutomationExecutionLog
        with SessionLocal() as db:
            rows = db.query(AutomationExecutionLog).filter(AutomationExecutionLog.job_id == job_id).order_by(AutomationExecutionLog.started_at.desc()).all()
            return [
                {
                    "id": r.id,
                    "status": r.status,
                    "output": r.output,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
def clear_entities():
    try:
        with SessionLocal() as db:
            deleted = db.query(models.SceneEntity).delete()
            db.commit()
        return {"deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed")
def seed_demo():
    demo = [
        {"name": "Tractor Alpha", "type": "robot", "x": 12.5, "y": 3.2, "z": 0.0, "rotation": 45.0, "state": {"status": "idle"}},
        {"name": "Irrigation Pump 1", "type": "pump", "x": -4.0, "y": 8.1, "z": 0.0, "rotation": 0.0, "state": {"running": False}},
        {"name": "Soil Sensor A", "type": "sensor", "x": 0.5, "y": -2.2, "z": 0.0, "rotation": 0.0, "state": {"moisture": 42}},
    ]
    created = []
    created_info = []
    with SessionLocal() as db:
        for item in demo:
            # deduplicate by name
            existing = db.query(models.SceneEntity).filter(models.SceneEntity.name == item["name"]).first()
            if existing:
                existing.x = item["x"]
                existing.y = item["y"]
                existing.z = item["z"]
                existing.rotation = item["rotation"]
                existing.state = item.get("state", {})
                db.add(existing)
                db.commit()
                db.refresh(existing)
                created.append(existing)
                created_info.append({"id": existing.id, "name": existing.name})
            else:
                ent = models.SceneEntity(
                    name=item["name"], type=item["type"], x=item["x"], y=item["y"], z=item["z"], rotation=item["rotation"], state=item.get("state", {})
                )
                db.add(ent)
                db.commit()
                db.refresh(ent)
                created.append(ent)
                created_info.append({"id": ent.id, "name": ent.name})
                # broadcast
                try:
                    import asyncio
                    # schedule broadcast asynchronously on the running loop
                    asyncio.create_task(scene_service.broadcast_entity_update({
                        "id": ent.id, "name": ent.name, "type": ent.type, "x": ent.x, "y": ent.y, "z": ent.z, "rotation": ent.rotation, "state": ent.state or {}
                    }))
                except Exception:
                    pass

    return {"created": created_info}
