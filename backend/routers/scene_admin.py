from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from sqlalchemy.orm import Session

from backend.dependencies import get_current_admin, get_db, get_current_user, has_permission, require_permission
from backend.audit_utils import record_actor_audit_event
from backend.blockchain_connector import get_blockchain_connector
from backend import models_scene as models
from backend.services import scene_simulator
from backend.services import scene as scene_service
from backend import realtime
from backend.models.lab_automation import AutomationJob
from datetime import datetime
try:
    from croniter import croniter
except Exception:
    croniter = None
try:
    from dateutil import parser as dateutil_parser
except Exception:
    dateutil_parser = None

router = APIRouter(prefix="/api/v1/scene/admin", tags=["scene-admin"])


def _tenant_id(actor) -> int:
    return int(actor.tenant_id if hasattr(actor, "tenant_id") else actor["tenant_id"])


def _require_superadmin(actor):
    role = actor.role if hasattr(actor, "role") else actor.get("role")
    if role != "superadmin":
        raise HTTPException(status_code=403, detail="Global simulation control requires superadmin")


def _record_scene_admin_action(
    db: Session, actor, event_type: str, entity_id: str, details: dict,
    entity_type: str = "scene_simulator",
):
    return record_actor_audit_event(
        db, _tenant_id(actor), actor, event_type, entity_type, entity_id, details,
        blockchain=get_blockchain_connector(),
    )


@router.post("/pause")
def pause_simulation(current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_superadmin(current_admin)
    scene_simulator.pause_simulation()
    _record_scene_admin_action(db, current_admin, "scene_simulation_paused", "global", {})
    return {"status": "paused"}


@router.post("/resume")
def resume_simulation(current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_superadmin(current_admin)
    scene_simulator.resume_simulation()
    _record_scene_admin_action(db, current_admin, "scene_simulation_resumed", "global", {})
    return {"status": "running"}


@router.post("/speed")
def set_speed(payload: Dict[str, float], current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_superadmin(current_admin)
    """Set simulation tick speed in seconds via JSON `{ "seconds": 0.5 }`"""
    sec = payload.get("seconds")
    if sec is None:
        raise HTTPException(status_code=400, detail="Missing 'seconds' in payload")
    ok = scene_simulator.set_tick_seconds(sec)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid seconds value; must be > 0")
    _record_scene_admin_action(
        db, current_admin, "scene_simulation_speed_changed", "global", {"tick_seconds": sec}
    )
    return {"status": "ok", "seconds": scene_simulator.get_tick_seconds()}


@router.get("/status")
def simulation_status():
    return {"running": scene_simulator.is_running(), "tick_seconds": scene_simulator.get_tick_seconds()}



@router.post("/command")
def send_command(payload: Dict, current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_superadmin(current_admin)
    """Send a generic command to realtime clients. Example payload: {"event":"robot:command","target_id":1,"command":"start","params":{}}"""
    event = payload.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing 'event' in payload")
    try:
        # best-effort emit
        realtime.sio.emit(event, payload)
    except Exception:
        realtime.logger.exception("Failed to emit command event")
    _record_scene_admin_action(
        db, current_admin, "scene_command_dispatched", "global",
        {"event": event, "target_id": payload.get("target_id"), "command": payload.get("command")},
    )
    return {"sent": True, "event": event}


@router.post("/job")
def create_job(
    payload: Dict,
    current_user=Depends(require_permission("devices.manage")),
    db: Session = Depends(get_db),
):
    """Create a one-off AutomationJob for the automation scheduler.

    Example payload: {"name":"Move Tractor","command":"move","parameters":{"dx":1}, "scheduled_at": "2026-08-15T12:00:00"}
    """
    try:
        name = payload.get("name") or payload.get("command")
        cmd = payload.get("command")
        params = payload.get("parameters") or {}
        scheduled = payload.get("scheduled_at")
        recurring = bool(payload.get("recurring", False))
        tenant_id = _tenant_id(current_user)
        device_id = payload.get("device_id")
        cron_expr = payload.get("cron")

        # If device_id is provided, require admin role
        if device_id and not has_permission(current_user, "admin.access"):
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
        db.add(job)
        db.flush()
        _record_scene_admin_action(
            db, current_user, "scene_automation_job_created", str(job.id),
            {"name": job.name, "command": job.command, "device_id": job.device_id,
             "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
             "recurring": job.recurring, "parameter_names": sorted(params)},
            entity_type="automation_job",
        )
        db.refresh(job)
        return {"id": job.id, "name": job.name, "status": job.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
def list_jobs(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        rows = db.query(AutomationJob).filter(
            AutomationJob.tenant_id == _tenant_id(current_user)
        ).order_by(AutomationJob.created_at.desc()).limit(50).all()
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
def cancel_job(job_id: int, current_user=Depends(require_permission("devices.manage")), db: Session = Depends(get_db)):
    try:
        job = db.query(AutomationJob).filter(
            AutomationJob.id == job_id, AutomationJob.tenant_id == _tenant_id(current_user)
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job.status = "cancelled"
        db.add(job)
        _record_scene_admin_action(
            db, current_user, "scene_automation_job_cancelled", str(job.id), {"name": job.name},
            entity_type="automation_job",
        )
        return {"id": job.id, "status": job.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/logs")
def job_logs(job_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        from backend.models.lab_automation import AutomationExecutionLog
        job = db.query(AutomationJob.id).filter(
            AutomationJob.id == job_id, AutomationJob.tenant_id == _tenant_id(current_user)
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        rows = db.query(AutomationExecutionLog).filter(
            AutomationExecutionLog.job_id == job_id
        ).order_by(AutomationExecutionLog.started_at.desc()).all()
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
def clear_entities(current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        deleted = db.query(models.SceneEntity).filter(
            models.SceneEntity.tenant_id == _tenant_id(current_admin)
        ).delete(synchronize_session=False)
        _record_scene_admin_action(
            db, current_admin, "scene_entities_cleared", "tenant", {"deleted_count": deleted}
        )
        return {"deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed")
def seed_demo(current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    demo = [
        {"name": "Tractor Alpha", "type": "robot", "x": 12.5, "y": 3.2, "z": 0.0, "rotation": 45.0, "state": {"status": "idle"}},
        {"name": "Irrigation Pump 1", "type": "pump", "x": -4.0, "y": 8.1, "z": 0.0, "rotation": 0.0, "state": {"running": False}},
        {"name": "Soil Sensor A", "type": "sensor", "x": 0.5, "y": -2.2, "z": 0.0, "rotation": 0.0, "state": {"moisture": 42}},
    ]
    created = []
    created_info = []
    tenant_id = _tenant_id(current_admin)
    for item in demo:
        existing = db.query(models.SceneEntity).filter(
            models.SceneEntity.name == item["name"],
            models.SceneEntity.tenant_id == tenant_id,
        ).first()
        if existing:
            existing.x = item["x"]
            existing.y = item["y"]
            existing.z = item["z"]
            existing.rotation = item["rotation"]
            existing.state = item.get("state", {})
            db.add(existing)
            ent = existing
        else:
            ent = models.SceneEntity(
                tenant_id=tenant_id,
                name=item["name"],
                type=item["type"],
                x=item["x"],
                y=item["y"],
                z=item["z"],
                rotation=item["rotation"],
                state=item.get("state", {}),
            )
            db.add(ent)
        db.flush()
        created.append(ent)
        created_info.append({"id": ent.id, "name": ent.name})
        try:
            import asyncio
            asyncio.create_task(scene_service.broadcast_entity_update({
                "id": ent.id, "name": ent.name, "type": ent.type,
                "x": ent.x, "y": ent.y, "z": ent.z, "rotation": ent.rotation,
                "state": ent.state or {},
            }))
        except RuntimeError:
            pass

    _record_scene_admin_action(
        db, current_admin, "scene_demo_seeded", "tenant",
        {"entity_count": len(created_info), "entity_names": [item["name"] for item in created_info]},
    )

    return {"created": created_info}
