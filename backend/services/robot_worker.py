import asyncio
import logging
from datetime import datetime

from backend import models_db
from backend.database import SessionLocal, Zone
from backend.models.digital_twin import DigitalTwinDevice

logger = logging.getLogger(__name__)


def _resolve_robot(db, task) -> DigitalTwinDevice | None:
    robots = (
        db.query(DigitalTwinDevice)
        .filter(
            DigitalTwinDevice.tenant_id == task.tenant_id,
            DigitalTwinDevice.kind == "robot",
            DigitalTwinDevice.simulation_enabled.is_(True),
        )
        .order_by(DigitalTwinDevice.id)
        .all()
    )
    requested_id = str(task.requested_robot_id).strip() if task.requested_robot_id else None
    if requested_id:
        robots = [
            robot for robot in robots
            if robot.device_id == requested_id or str(robot.id) == requested_id
        ]

    for robot in robots:
        state = robot.state or {}
        if robot.status.lower() == "offline" or state.get("active_task_id"):
            continue
        return robot
    return None


def _task_target_zone(db, task):
    if not task.zone_id:
        return None
    try:
        zone_id = int(task.zone_id)
    except (TypeError, ValueError):
        return None
    return db.query(Zone).filter(
        Zone.id == zone_id,
        Zone.tenant_id == task.tenant_id,
    ).first()


def _robot_snapshot(robot: DigitalTwinDevice) -> dict:
    return {
        "id": robot.id,
        "device_id": robot.device_id,
        "tenant_id": robot.tenant_id,
        "zone_id": robot.zone_id,
        "name": robot.name,
        "kind": robot.kind,
        "device_type": robot.device_type,
        "status": robot.status,
        "control_mode": robot.control_mode,
        "position": robot.position or {"x": 0.0, "y": 0.0, "z": 0.0},
        "state": robot.state or {},
        "last_updated": robot.last_updated.isoformat() if robot.last_updated else datetime.utcnow().isoformat(),
    }


async def _emit_transition(event_payload: dict, robot_payload: dict | None) -> None:
    from backend.realtime import emit_tenant_event

    await emit_tenant_event("robot:task_update", event_payload, event_payload["tenant_id"])
    if robot_payload:
        await emit_tenant_event(
            "digital_twin:device_update",
            robot_payload,
            robot_payload["tenant_id"],
        )


def _transition_task(db, task_id: int, expected_status: str, new_status: str):
    task = db.query(models_db.ScheduledRoboticTask).filter(
        models_db.ScheduledRoboticTask.id == task_id,
        models_db.ScheduledRoboticTask.status == expected_status,
    ).first()
    if task is None:
        return None

    robot = None
    if new_status == "assigned":
        robot = _resolve_robot(db, task)
        if robot is None:
            task.status = "conflicted"
            task.conflict_reason = (
                f"No available tenant-owned simulated robot matches "
                f"{task.requested_robot_id!r}."
            )
            db.commit()
            return task, None
        task.assigned_robot_id = robot.device_id
        task.assigned_time = datetime.utcnow()
        robot_state = dict(robot.state or {})
        robot_state.update({
            "active_task_id": task.task_id,
            "activity": "assigned",
            "task": {
                "task_id": task.task_id,
                "operation_type": task.operation_type,
                "zone_id": task.zone_id,
                "status": "assigned",
            },
        })
        robot.state = robot_state
    elif task.assigned_robot_id:
        robot = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.tenant_id == task.tenant_id,
            DigitalTwinDevice.device_id == task.assigned_robot_id,
            DigitalTwinDevice.kind == "robot",
        ).first()
        if robot is None:
            task.status = "conflicted"
            task.conflict_reason = "The assigned simulated robot is no longer available."
            db.commit()
            return task, None
        robot_state = dict(robot.state or {})
        if new_status in {"in_progress", "completed"} and robot_state.get("active_task_id") != task.task_id:
            task.status = "conflicted"
            task.conflict_reason = "The robot stopped or no longer owns this task."
            db.commit()
            return task, None
        robot_state["task"] = {
            **dict(robot_state.get("task") or {}),
            "task_id": task.task_id,
            "operation_type": task.operation_type,
            "zone_id": task.zone_id,
            "status": new_status,
        }
        if new_status == "in_progress":
            robot_state["activity"] = "working"
        elif new_status == "completed":
            robot_state.pop("active_task_id", None)
            robot_state["activity"] = "stationary"
            robot_state["last_task"] = robot_state.pop("task")
            zone = _task_target_zone(db, task)
            if zone:
                robot.zone_id = zone.id
                spatial_position = dict(zone.spatial_position or {})
                if all(axis in spatial_position for axis in ("x", "y", "z")):
                    robot.position = spatial_position
        robot.state = robot_state

    task.status = new_status
    task.updated_at = datetime.utcnow()
    if robot:
        robot.last_updated = datetime.utcnow()
    db.commit()
    if robot:
        db.refresh(robot)
    db.refresh(task)
    return task, robot


def _task_event(task) -> dict:
    return {
        "task_id": task.task_id,
        "status": task.status,
        "assigned_robot_id": task.assigned_robot_id,
        "tenant_id": task.tenant_id,
        "operation_type": task.operation_type,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def robot_task_worker(poll_interval: float = 2.0):
    """Execute queued tasks only on persisted, available robots in the task tenant."""
    while True:
        try:
            with SessionLocal() as db:
                pending_ids = [
                    row[0] for row in db.query(models_db.ScheduledRoboticTask.id)
                    .filter(models_db.ScheduledRoboticTask.status == "pending")
                    .order_by(models_db.ScheduledRoboticTask.priority.desc(),
                              models_db.ScheduledRoboticTask.enqueue_time.asc())
                    .all()
                ]

            for task_id in pending_ids:
                with SessionLocal() as db:
                    result = _transition_task(db, task_id, "pending", "assigned")
                    if result is None:
                        continue
                    task, robot = result
                    assigned_event = _task_event(task)
                    robot_snapshot = _robot_snapshot(robot) if robot else None
                await _emit_transition(assigned_event, robot_snapshot)
                if not robot:
                    continue

                await asyncio.sleep(0.25)
                with SessionLocal() as db:
                    result = _transition_task(db, task_id, "assigned", "in_progress")
                    if result is None:
                        continue
                    task, robot = result
                    progress_event = _task_event(task)
                    robot_snapshot = _robot_snapshot(robot) if robot else None
                await _emit_transition(progress_event, robot_snapshot)

                await asyncio.sleep(0.5)
                with SessionLocal() as db:
                    result = _transition_task(db, task_id, "in_progress", "completed")
                    if result is None:
                        continue
                    task, robot = result
                    completed_event = _task_event(task)
                    robot_snapshot = _robot_snapshot(robot) if robot else None
                await _emit_transition(completed_event, robot_snapshot)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error in robot task worker cycle")

        await asyncio.sleep(poll_interval)
