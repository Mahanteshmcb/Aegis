"""
Aegis Backend - Robotics Router

Exposes backend endpoints for robotic fleet management and control.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.dependencies import get_current_user, get_db
from backend.config import settings
from backend.blockchain_connector import get_blockchain_connector
from backend.audit_utils import record_audit_event
from backend import crud, models_db, schemas

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.robotics_connector import RoboticsConnector
from ai.task_scheduler import RoboticTask, TaskScheduler

router = APIRouter(prefix="/api/v1/robotics", tags=["Robotics"])

logger = logging.getLogger(__name__)

_robotics_connector = None

def get_robotics_connector() -> RoboticsConnector:
    global _robotics_connector
    if _robotics_connector is None:
        _robotics_connector = RoboticsConnector(
            host=settings.robotics_host,
            port=settings.robotics_port,
            timeout=settings.robotics_timeout,
            fallback_mode=settings.robotics_fallback_enabled,
            max_workers=settings.grpc_max_workers,
            keepalive_time_ms=settings.grpc_keepalive_time_ms,
            keepalive_timeout_ms=settings.grpc_keepalive_timeout_ms,
            max_concurrent_streams=settings.grpc_max_concurrent_streams,
            compression_enabled=settings.grpc_compression_enabled,
        )
    return _robotics_connector


_task_scheduler: Optional[TaskScheduler] = None

def get_task_scheduler() -> TaskScheduler:
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler(get_robotics_connector())
    return _task_scheduler


def _record_robot_audit(db: Session, blockchain, tenant_id: int, event_type: str, metadata: Dict[str, Any]) -> None:
    try:
        record_audit_event(db, blockchain, tenant_id, event_type, metadata)
    except Exception as e:
        logger.warning(f"Failed to record robotics audit event: {e}")


def _scheduled_task_to_dict(db_task: models_db.ScheduledRoboticTask) -> Dict[str, Any]:
    return {
        "task_id": db_task.task_id,
        "operation_type": db_task.operation_type,
        "requested_robot_id": db_task.requested_robot_id,
        "assigned_robot_id": db_task.assigned_robot_id,
        "zone_id": db_task.zone_id,
        "priority": db_task.priority,
        "task_detail": db_task.task_detail or {},
        "metadata": db_task.task_metadata or {},
        "timeout_seconds": db_task.timeout_seconds,
        "status": db_task.status,
        "conflict_reason": db_task.conflict_reason,
        "enqueue_time": db_task.enqueue_time.isoformat() if db_task.enqueue_time else None,
        "assigned_time": db_task.assigned_time.isoformat() if db_task.assigned_time else None,
        "created_at": db_task.created_at.isoformat() if db_task.created_at else None,
        "updated_at": db_task.updated_at.isoformat() if db_task.updated_at else None,
    }


# --- SCHEMAS ---

class RobotIdentityRequest(BaseModel):
    robot_id: str
    robot_type: str = "AEGIS_ROVER"
    firmware_version: Optional[str] = None
    model_year: Optional[int] = None
    capabilities: Optional[Dict[str, str]] = {}

class RobotHealthQuery(BaseModel):
    robot_id: str
    robot_type: Optional[str] = None

class RoboticTaskRequest(BaseModel):
    task_id: str
    robot_id: str
    operation_type: str
    priority: Optional[int] = 5
    task_detail: Optional[Dict[str, Any]] = {}
    timeout_seconds: Optional[int] = 60
    metadata: Optional[Dict[str, str]] = {}

class ScheduledTaskRequest(BaseModel):
    task_id: str
    operation_type: str
    robot_id: Optional[str] = None
    zone_id: Optional[str] = None
    priority: Optional[int] = 5
    task_detail: Optional[Dict[str, Any]] = {}
    timeout_seconds: Optional[int] = 60
    metadata: Optional[Dict[str, str]] = {}

class SensorDataPayload(BaseModel):
    robot_id: str
    health: Dict[str, Any]
    environment: Dict[str, Any]
    observations: Optional[List[str]] = []
    timestamp_ms: Optional[int] = None

class Coordinate3D(BaseModel):
    x: float
    y: float
    z: float

class NavigationCommandRequest(BaseModel):
    command_id: str
    robot_id: str
    destination: Coordinate3D
    waypoints: Optional[List[Coordinate3D]] = []
    speed_percent: Optional[float] = 50.0
    use_obstacles_map: Optional[bool] = False
    timeout_seconds: Optional[int] = 60
    zone_id: Optional[str] = None


class StandardResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# --- ENDPOINTS ---

@router.get("/health", response_model=Dict[str, Any])
async def robotics_health(current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    healthy = connector.health_check()
    return {
        "status": "connected" if healthy else "fallback",
        "connected": healthy,
        "service_address": connector.address,
    }

@router.post("/register", response_model=StandardResponse)
async def register_robot(request: RobotIdentityRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    connector = get_robotics_connector()
    result = connector.register_robot(
        robot_id=request.robot_id,
        robot_type=request.robot_type,
        firmware_version=request.firmware_version,
        model_year=request.model_year,
        capabilities=request.capabilities,
    )
    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "robot_registration",
        {
            "robot_id": request.robot_id,
            "robot_type": request.robot_type,
            "firmware_version": request.firmware_version,
            "model_year": request.model_year,
            "capabilities": request.capabilities,
            "result": result,
        },
    )
    return {
        "status": "success",
        "message": "Robot registration processed",
        "data": result,
    }

@router.post("/status", response_model=Dict[str, Any])
async def get_robot_status(request: RobotHealthQuery, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    result = connector.get_robot_health(
        robot_id=request.robot_id,
        robot_type=request.robot_type,
    )
    return result

@router.post("/tasks", response_model=StandardResponse)
async def send_robot_task(request: RoboticTaskRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    connector = get_robotics_connector()
    result = connector.send_task(
        task_id=request.task_id,
        robot_id=request.robot_id,
        operation_type=request.operation_type,
        priority=request.priority,
        task_detail=request.task_detail,
        timeout_seconds=request.timeout_seconds,
        metadata=request.metadata,
    )
    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "robot_task_dispatched",
        {
            "task_id": request.task_id,
            "robot_id": request.robot_id,
            "operation_type": request.operation_type,
            "priority": request.priority,
            "task_detail": request.task_detail,
            "timeout_seconds": request.timeout_seconds,
            "metadata": request.metadata,
            "result": result,
        },
    )
    return {
        "status": "success",
        "message": "Task dispatched",
        "data": result,
    }

@router.post("/schedule/enqueue", response_model=StandardResponse)
async def enqueue_robot_task(request: ScheduledTaskRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    scheduled_request = schemas.ScheduledTaskCreate(
        task_id=request.task_id,
        operation_type=request.operation_type,
        requested_robot_id=request.robot_id,
        zone_id=request.zone_id,
        priority=request.priority or 5,
        task_detail=request.task_detail or {},
        metadata=request.metadata or {},
        timeout_seconds=request.timeout_seconds or 60,
        status="pending",
    )
    try:
        db_task = crud.create_scheduled_task(db, scheduled_request, current_user["tenant_id"])
    except ValueError as err:
        raise HTTPException(status_code=409, detail=str(err))

    scheduler = get_task_scheduler()
    scheduler.enqueue_task(
        RoboticTask(
            task_id=db_task.task_id,
            operation_type=db_task.operation_type,
            robot_id=db_task.requested_robot_id,
            zone_id=db_task.zone_id,
            priority=db_task.priority,
            task_detail=db_task.task_detail or {},
            metadata=db_task.task_metadata or {},
            timeout_seconds=db_task.timeout_seconds,
        )
    )

    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "robot_task_scheduled",
        {
            "task_id": db_task.task_id,
            "operation_type": db_task.operation_type,
            "requested_robot_id": db_task.requested_robot_id,
            "zone_id": db_task.zone_id,
            "priority": db_task.priority,
            "task_detail": db_task.task_detail,
            "metadata": db_task.task_metadata,
        },
    )

    queue_length = len(crud.list_scheduled_tasks(db, current_user["tenant_id"]))
    return {
        "status": "success",
        "message": "Task enqueued for scheduling",
        "data": {
            "task_id": db_task.task_id,
            "queue_length": queue_length,
        },
    }

@router.get("/schedule/queue", response_model=StandardResponse)
async def get_scheduled_task_queue(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_tasks = crud.list_scheduled_tasks(db, current_user["tenant_id"])
    queue = [_scheduled_task_to_dict(task) for task in db_tasks]
    assigned = [task for task in queue if task["status"] == "assigned"]
    conflicted = [task for task in queue if task["status"] == "conflicted"]
    return {
        "status": "success",
        "message": "Task queue fetched",
        "data": {
            "queue_length": len(queue),
            "assigned": len(assigned),
            "conflicted": len(conflicted),
            "tasks": queue,
        },
    }

@router.post("/schedule/assign", response_model=StandardResponse)
async def assign_scheduled_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_tasks = crud.list_scheduled_tasks(db, current_user["tenant_id"], status="pending")
    task_map: Dict[str, models_db.ScheduledRoboticTask] = {}
    scheduler = TaskScheduler(get_robotics_connector())
    scheduler.queue = []

    for db_task in db_tasks:
        robot_task = RoboticTask(
            task_id=db_task.task_id,
            operation_type=db_task.operation_type,
            robot_id=db_task.requested_robot_id,
            zone_id=db_task.zone_id,
            priority=db_task.priority,
            task_detail=db_task.task_detail or {},
            metadata=db_task.task_metadata or {},
            timeout_seconds=db_task.timeout_seconds,
            status=db_task.status,
            enqueue_time=db_task.enqueue_time,
        )
        scheduler.queue.append(robot_task)
        task_map[robot_task.task_id] = db_task

    assigned = scheduler.assign_pending_tasks()

    for updated_task in scheduler.get_queue():
        db_task = task_map.get(updated_task.task_id)
        if not db_task:
            continue
        assigned_robot_id = updated_task.robot_id if updated_task.status == "assigned" else None
        crud.update_scheduled_task_status(
            db,
            db_task,
            updated_task.status,
            assigned_robot_id=assigned_robot_id,
            conflict_reason=updated_task.conflict_reason,
        )

    assigned_task_ids = [task["task_id"] for task in assigned]
    queue_length = len(crud.list_scheduled_tasks(db, current_user["tenant_id"]))
    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "robot_task_assignment",
        {
            "assigned_tasks": assigned_task_ids,
            "queue_length": queue_length,
        },
    )
    return {
        "status": "success",
        "message": "Pending scheduled tasks assigned",
        "data": {
            "assigned_count": len(assigned),
            "assigned_tasks": assigned,
            "queue_length": queue_length,
        },
    }

@router.delete("/schedule/cancel/{task_id}", response_model=StandardResponse)
async def cancel_scheduled_task(task_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Cancel a scheduled task if it's still pending."""
    # Check if task exists and belongs to tenant
    db_task = crud.get_scheduled_task_by_task_id(db, current_user["tenant_id"], task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")

    # Only allow canceling pending tasks
    if db_task.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task with status '{db_task.status}'. Only pending tasks can be cancelled."
        )

    # Delete the task
    deleted = crud.delete_scheduled_task(db, current_user["tenant_id"], task_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to cancel scheduled task")

    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "robot_task_cancelled",
        {
            "task_id": task_id,
            "operation_type": db_task.operation_type,
            "reason": "user_cancelled",
        },
    )

    return {
        "status": "success",
        "message": "Scheduled task cancelled",
        "data": {
            "task_id": task_id,
            "operation_type": db_task.operation_type,
        },
    }

@router.post("/navigate", response_model=StandardResponse)
async def navigate_robot(request: NavigationCommandRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    connector = get_robotics_connector()
    result = connector.navigate_to(
        command_id=request.command_id,
        robot_id=request.robot_id,
        destination=request.destination.dict(),
        waypoints=[waypoint.dict() for waypoint in request.waypoints or []],
        speed_percent=request.speed_percent,
        use_obstacles_map=request.use_obstacles_map,
        timeout_seconds=request.timeout_seconds,
        zone_id=request.zone_id,
    )
    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "robot_navigation_command",
        {
            "command_id": request.command_id,
            "robot_id": request.robot_id,
            "destination": request.destination.dict(),
            "waypoints": [waypoint.dict() for waypoint in request.waypoints or []],
            "speed_percent": request.speed_percent,
            "use_obstacles_map": request.use_obstacles_map,
            "timeout_seconds": request.timeout_seconds,
            "zone_id": request.zone_id,
            "result": result,
        },
    )
    return {
        "status": "success",
        "message": "Navigation command sent",
        "data": result,
    }

@router.get("/navigation-status/{robot_id}", response_model=List[Dict[str, Any]])
async def get_navigation_status(robot_id: str, robot_type: Optional[str] = None, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    return connector.get_navigation_status(robot_id=robot_id, robot_type=robot_type)

@router.post("/sensor-data", response_model=StandardResponse)
async def report_sensor_data(request: SensorDataPayload, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    result = connector.report_sensor_data(
        robot_id=request.robot_id,
        health=request.health,
        environment=request.environment,
        observations=request.observations,
        timestamp_ms=request.timestamp_ms,
    )
    return {
        "status": "success",
        "message": result.get("message", "Sensor data reported"),
    }

@router.post("/emergency-stop", response_model=StandardResponse)
async def emergency_stop(request: RobotHealthQuery, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    result = connector.emergency_stop(
        robot_id=request.robot_id,
        robot_type=request.robot_type,
    )
    return {
        "status": "success",
        "message": result.get("message", "Emergency stop issued"),
    }

@router.post("/cancel-task", response_model=StandardResponse)
async def cancel_task(request: RobotHealthQuery, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    result = connector.cancel_task(
        robot_id=request.robot_id,
        robot_type=request.robot_type,
    )
    return {
        "status": "success",
        "message": result.get("message", "Task cancellation issued"),
    }

@router.get("/active", response_model=List[Dict[str, Any]])
async def list_active_robots(current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    return connector.list_active_robots()


@router.post("/fleet/coordinate", response_model=schemas.FleetCoordinationResponse)
async def fleet_coordinate_task(request: schemas.FleetCoordinationRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    connector = get_robotics_connector()
    result = connector.coordinate_fleet_task(
        task_type=request.task_type,
        zone_id=request.zone_id,
        priority=request.priority,
        robot_count=request.robot_count,
        task_parameters=request.task_parameters,
    )
    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "fleet_coordination",
        {
            "task_type": request.task_type,
            "zone_id": request.zone_id,
            "priority": request.priority,
            "robot_count": request.robot_count,
            "task_parameters": request.task_parameters,
            "result": result,
        },
    )
    return result


@router.post("/fleet/optimize", response_model=schemas.FleetOptimizationResponse)
async def fleet_optimize_deployment(request: schemas.FleetOptimizationRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    connector = get_robotics_connector()
    result = connector.optimize_fleet_deployment(
        zone_id=request.zone_id,
        optimization_criteria=request.optimization_criteria,
    )
    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "fleet_optimization",
        {
            "zone_id": request.zone_id,
            "optimization_criteria": request.optimization_criteria,
            "result": result,
        },
    )
    return result


@router.get("/fleet/status", response_model=schemas.FleetStatusResponse)
async def fleet_status(zone_id: Optional[str] = None, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    return connector.get_fleet_status(zone_id=zone_id)


@router.post("/fleet/emergency-stop", response_model=schemas.EmergencyFleetStopResponse)
async def fleet_emergency_stop(request: schemas.EmergencyFleetStopRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    connector = get_robotics_connector()
    result = connector.emergency_fleet_stop(
        zone_id=request.zone_id,
        reason=request.reason,
    )
    blockchain = get_blockchain_connector()
    _record_robot_audit(
        db,
        blockchain,
        current_user["tenant_id"],
        "fleet_emergency_stop",
        {
            "zone_id": request.zone_id,
            "reason": request.reason,
            "result": result,
        },
    )
    return result


@router.post("/emergency/events", response_model=schemas.EmergencyEventResponse)
async def create_emergency_event(
    request: schemas.EmergencyEventCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = crud.create_emergency_event(db, request, current_user["tenant_id"], triggered_by_user=current_user["id"])
    _record_robot_audit(
        db,
        get_blockchain_connector(),
        current_user["tenant_id"],
        "emergency_event_created",
        {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "severity": event.severity,
        },
    )
    return event


@router.get("/emergency/events", response_model=List[schemas.EmergencyEventResponse])
async def list_emergency_events(status: Optional[str] = None, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    events = crud.list_emergency_events(db, current_user["tenant_id"], status=status, limit=200)
    return events


@router.post("/emergency/events/{event_id}/responses", response_model=schemas.EmergencyResponseResponse)
async def add_emergency_response(
    event_id: str,
    request: schemas.EmergencyResponseCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = crud.get_emergency_event(db, current_user["tenant_id"], event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Emergency event not found")
    response = crud.create_emergency_response(db, event.id, request)
    _record_robot_audit(
        db,
        get_blockchain_connector(),
        current_user["tenant_id"],
        "emergency_response_created",
        {
            "event_id": event.event_id,
            "action_type": request.action_type,
            "action_name": request.action_name,
        },
    )
    return response


@router.post("/emergency/events/{event_id}/responses/{response_id}/complete", response_model=schemas.EmergencyResponseResponse)
async def complete_emergency_response(
    event_id: str,
    response_id: int,
    request: schemas.EmergencyResponseCompleteRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = crud.get_emergency_event(db, current_user["tenant_id"], event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Emergency event not found")
    response = crud.update_emergency_response_status(
        db,
        response_id,
        status="completed",
        success=request.success,
        error_message=request.error_message,
        result_data=request.result_data,
    )
    if request.success and event.status != "resolved":
        event.status = "resolved"
        event.resolution_timestamp = datetime.utcnow()
        db.commit()
        db.refresh(event)

    return response


@router.get("/emergency/events/{event_id}/status", response_model=schemas.EmergencyStatusResponse)
async def emergency_status(event_id: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    event = crud.get_emergency_event(db, current_user["tenant_id"], event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Emergency event not found")
    responses = db.query(models_db.EmergencyResponse).filter(models_db.EmergencyResponse.event_id == event.id).all()
    backup_states = crud.list_backup_power_states(db, current_user["tenant_id"], limit=50)
    active_backup = any(state.is_active for state in backup_states)
    recovery_in_progress = any(state.recovery_status == "in_progress" for state in backup_states)
    return schemas.EmergencyStatusResponse(
        event_id=event.event_id,
        event_type=event.event_type,
        severity=event.severity,
        status=event.status,
        response_count=len(responses),
        active_responses=[resp.action_name for resp in responses if resp.status != "completed"],
        backup_power_active=active_backup,
        recovery_in_progress=recovery_in_progress,
        estimated_recovery_time_minutes=next((state.recovery_eta_seconds for state in backup_states if state.recovery_status == "in_progress"), None),
        affected_systems_count=len(event.affected_systems or []),
        timestamp=datetime.utcnow(),
    )


@router.post("/emergency/power-state", response_model=schemas.BackupPowerStateResponse)
async def create_power_state(
    request: schemas.BackupPowerStateCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    power_state = crud.create_backup_power_state(db, current_user["tenant_id"], request)
    return power_state


@router.get("/emergency/power-state", response_model=List[schemas.BackupPowerStateResponse])
async def list_power_states(current_user=Depends(get_current_user), db: Session = Depends(get_db), limit: int = 100):
    return crud.list_backup_power_states(db, current_user["tenant_id"], limit=limit)


@router.post("/emergency/manual-override", response_model=schemas.ManualOverrideResponse)
async def manual_override(
    request: schemas.ManualOverrideRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = crud.create_emergency_event(
        db,
        schemas.EmergencyEventCreate(
            event_type="manual_override",
            severity="critical",
            description=f"Manual override requested: {request.reason}",
            triggered_by="manual_override",
            affected_systems=request.target_systems or [],
            metadata={"force": request.force},
        ),
        current_user["tenant_id"],
        triggered_by_user=current_user["id"],
    )
    response = crud.create_emergency_response(
        db,
        event.id,
        schemas.EmergencyResponseCreate(
            action_type=request.action_type,
            action_name=f"Manual override: {request.action_type}",
            description=request.reason,
            priority=100,
            affected_robots=request.target_systems or [],
            affected_zones=request.target_systems or [],
        ),
    )
    response = crud.update_emergency_response_status(
        db,
        response.id,
        status="completed",
        success=True,
        result_data={"target_systems": request.target_systems, "force": request.force},
    )
    override_id = f"override-{response.id}"
    return schemas.ManualOverrideResponse(
        override_id=override_id,
        action_type=request.action_type,
        status=response.status,
        executed_at=response.completed_at or datetime.utcnow(),
        affected_count=len(request.target_systems or []),
        confirmation_required=False,
    )


@router.post("/sync/backups", response_model=schemas.DataBackupSnapshotResponse)
async def create_data_backup_snapshot(
    request: schemas.DataBackupSnapshotCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot = crud.create_data_backup_snapshot(db, current_user["tenant_id"], request)
    _record_robot_audit(
        db,
        get_blockchain_connector(),
        current_user["tenant_id"],
        "data_backup_snapshot_created",
        {
            "snapshot_id": snapshot.snapshot_id,
            "source": snapshot.source,
            "record_count": snapshot.record_count,
            "storage_uri": snapshot.storage_uri,
        },
    )
    return snapshot


@router.get("/sync/backups", response_model=List[schemas.DataBackupSnapshotResponse])
async def list_data_backup_snapshots(current_user=Depends(get_current_user), db: Session = Depends(get_db), limit: int = 100):
    return crud.list_data_backup_snapshots(db, current_user["tenant_id"], limit=limit)


@router.post("/sync/backups/{snapshot_id}/verify", response_model=schemas.DataBackupSnapshotResponse)
async def verify_data_backup_snapshot(
    snapshot_id: str,
    verification: schemas.DataBackupSnapshotVerifyRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot = crud.verify_data_backup_snapshot(
        db,
        current_user["tenant_id"],
        snapshot_id,
        verification_hash=verification.verification_hash,
        verification_notes=verification.verification_notes,
        status=verification.status or "verified",
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="Backup snapshot not found")
    return snapshot


@router.post("/sync/jobs", response_model=schemas.DataSyncJobResponse)
async def create_data_sync_job(
    request: schemas.DataSyncJobCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = crud.create_data_sync_job(db, current_user["tenant_id"], request)
    _record_robot_audit(
        db,
        get_blockchain_connector(),
        current_user["tenant_id"],
        "data_sync_job_created",
        {
            "sync_id": job.sync_id,
            "source_system": job.source_system,
            "target_system": job.target_system,
        },
    )
    return job


@router.get("/sync/jobs", response_model=List[schemas.DataSyncJobResponse])
async def list_data_sync_jobs(current_user=Depends(get_current_user), db: Session = Depends(get_db), limit: int = 100):
    return crud.list_data_sync_jobs(db, current_user["tenant_id"], limit=limit)


@router.post("/sync/jobs/{sync_id}/complete", response_model=schemas.DataSyncJobResponse)
async def complete_data_sync_job(
    sync_id: str,
    request: schemas.DataSyncJobCompleteRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = crud.complete_data_sync_job(
        db,
        current_user["tenant_id"],
        sync_id,
        success=request.success,
        result_summary=request.result_summary,
        payload_hash=request.payload_hash,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Data sync job not found")
    _record_robot_audit(
        db,
        get_blockchain_connector(),
        current_user["tenant_id"],
        "data_sync_job_completed",
        {
            "sync_id": job.sync_id,
            "status": job.status,
            "result_summary": job.result_summary,
        },
    )
    return job


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@router.get("/monitoring/real-time-status", response_model=schemas.RealTimeStatusResponse)
async def get_real_time_status(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get comprehensive real-time system status for monitoring dashboard."""
    connector = get_robotics_connector()
    tenant_id = current_user["tenant_id"]

    # Get fleet status
    fleet_status = connector.get_fleet_status()

    # Get recent robot health snapshots
    robot_health_snapshots = crud.get_recent_robot_health_snapshots(db, tenant_id, hours=1)

    # Convert snapshots to response format
    robot_health = []
    for snapshot in robot_health_snapshots:
        robot_health.append(schemas.RobotHealthStatus(
            robot_id=snapshot.robot_id,
            status=snapshot.status,
            battery_level=snapshot.battery_level,
            cpu_usage_percent=snapshot.cpu_usage_percent,
            memory_usage_percent=snapshot.memory_usage_percent,
            temperature_c=snapshot.temperature_c,
            last_seen=snapshot.last_seen,
            uptime_seconds=snapshot.uptime_seconds,
            error_count=snapshot.error_count,
            warning_count=snapshot.warning_count,
            position=snapshot.position,
            current_task=snapshot.current_task,
            firmware_version=snapshot.firmware_version,
        ))

    # Get active alerts
    active_alerts = crud.list_system_alerts(db, tenant_id, acknowledged=False, limit=50)
    alert_responses = []
    for alert in active_alerts:
        alert_responses.append(schemas.SystemAlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            data=alert.data,
            acknowledged=alert.acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        ))

    # Get recent performance metrics
    performance_metrics = crud.get_system_performance_metrics(db, tenant_id, hours=1)
    perf_dict = {}
    for metric in performance_metrics:
        key = f"{metric.metric_category}.{metric.metric_name}"
        perf_dict[key] = {
            "value": metric.value,
            "unit": metric.unit,
            "timestamp": metric.timestamp.isoformat(),
            "context": metric.context_data,
        }

    # Determine overall system health
    system_health = "healthy"
    if any(robot.status in ["critical", "offline"] for robot in robot_health):
        system_health = "critical"
    elif any(robot.status == "warning" for robot in robot_health):
        system_health = "degraded"
    elif any(alert.severity in ["high", "critical"] for alert in active_alerts):
        system_health = "degraded"

    return schemas.RealTimeStatusResponse(
        timestamp=datetime.utcnow(),
        system_health=system_health,
        fleet_status=fleet_status,
        robot_health=robot_health,
        active_alerts=alert_responses,
        performance_metrics=perf_dict,
        last_updated=datetime.utcnow(),
    )


@router.get("/monitoring/alerts", response_model=List[schemas.SystemAlertResponse])
async def list_alerts(
    acknowledged: Optional[bool] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List system alerts with optional filtering."""
    alerts = crud.list_system_alerts(
        db,
        current_user["tenant_id"],
        acknowledged=acknowledged,
        severity=severity,
        alert_type=alert_type,
        limit=limit
    )

    return [
        schemas.SystemAlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            data=alert.data,
            acknowledged=alert.acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
        for alert in alerts
    ]


@router.post("/monitoring/alerts/{alert_id}/acknowledge", response_model=schemas.SystemAlertResponse)
async def acknowledge_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge a system alert."""
    alert = crud.acknowledge_system_alert(db, alert_id, current_user["tenant_id"], current_user["id"])
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return schemas.SystemAlertResponse(
        id=alert.id,
        tenant_id=alert.tenant_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        source=alert.source,
        data=alert.data,
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.get("/monitoring/robot-health/{robot_id}", response_model=List[schemas.RobotHealthStatus])
async def get_robot_health_history(
    robot_id: str,
    hours: int = 24,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health history for a specific robot."""
    snapshots = crud.get_recent_robot_health_snapshots(db, current_user["tenant_id"], robot_id=robot_id, hours=hours)

    return [
        schemas.RobotHealthStatus(
            robot_id=snapshot.robot_id,
            status=snapshot.status,
            battery_level=snapshot.battery_level,
            cpu_usage_percent=snapshot.cpu_usage_percent,
            memory_usage_percent=snapshot.memory_usage_percent,
            temperature_c=snapshot.temperature_c,
            last_seen=snapshot.last_seen,
            uptime_seconds=snapshot.uptime_seconds,
            error_count=snapshot.error_count,
            warning_count=snapshot.warning_count,
            position=snapshot.position,
            current_task=snapshot.current_task,
            firmware_version=snapshot.firmware_version,
        )
        for snapshot in snapshots
    ]


@router.post("/monitoring/health-snapshot", response_model=StandardResponse)
async def record_health_snapshot(
    robot_health: schemas.RobotHealthStatus,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a robot health snapshot (typically called by robots or monitoring systems)."""
    crud.create_robot_health_snapshot(db, current_user["tenant_id"], robot_health)

    # Check for anomalies and create alerts
    await _check_health_anomalies(db, current_user["tenant_id"], robot_health)

    return StandardResponse(
        status="success",
        message="Health snapshot recorded successfully",
        data={"robot_id": robot_health.robot_id}
    )


@router.get("/monitoring/dashboard", response_model=schemas.MonitoringDashboardResponse)
async def get_monitoring_dashboard(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get comprehensive monitoring dashboard data."""
    # Get real-time status
    real_time_status = await get_real_time_status(current_user, db)

    # Get historical data (last 7 days)
    historical_alerts = crud.list_system_alerts(db, current_user["tenant_id"], limit=1000)
    historical_metrics = crud.get_system_performance_metrics(db, current_user["tenant_id"], hours=168)  # 7 days

    # Generate alerts summary
    alerts_summary = {
        "total_alerts": len(historical_alerts),
        "active_alerts": len([a for a in historical_alerts if not a.acknowledged]),
        "acknowledged_alerts": len([a for a in historical_alerts if a.acknowledged]),
        "by_severity": {
            "low": len([a for a in historical_alerts if a.severity == "low"]),
            "medium": len([a for a in historical_alerts if a.severity == "medium"]),
            "high": len([a for a in historical_alerts if a.severity == "high"]),
            "critical": len([a for a in historical_alerts if a.severity == "critical"]),
        },
        "by_type": {}
    }

    for alert in historical_alerts:
        alerts_summary["by_type"][alert.alert_type] = alerts_summary["by_type"].get(alert.alert_type, 0) + 1

    # Generate recommendations based on current status
    recommendations = []
    if real_time_status.system_health == "critical":
        recommendations.append("Immediate attention required: Critical system issues detected")
    elif real_time_status.system_health == "degraded":
        recommendations.append("System performance degraded - review active alerts")

    if len(real_time_status.active_alerts) > 10:
        recommendations.append("High alert volume - consider reviewing alert thresholds")

    offline_robots = [r for r in real_time_status.robot_health if r.status == "offline"]
    if offline_robots:
        recommendations.append(f"{len(offline_robots)} robots offline - investigate connectivity issues")

    return schemas.MonitoringDashboardResponse(
        real_time_status=real_time_status,
        historical_data={
            "alerts_last_7_days": len(historical_alerts),
            "metrics_last_7_days": len(historical_metrics),
        },
        alerts_summary=alerts_summary,
        recommendations=recommendations,
    )


async def _check_health_anomalies(db: Session, tenant_id: int, robot_health: schemas.RobotHealthStatus):
    """Check for health anomalies and create alerts if needed."""
    alerts_created = []

    # Battery level alerts
    if robot_health.battery_level is not None:
        if robot_health.battery_level < 10:
            alert = crud.create_system_alert(db, schemas.SystemAlertCreate(
                tenant_id=tenant_id,
                alert_type="robot_health",
                severity="critical",
                title=f"Critical Battery Level: {robot_health.robot_id}",
                message=f"Robot {robot_health.robot_id} battery level is critically low at {robot_health.battery_level}%",
                source=robot_health.robot_id,
                data={"battery_level": robot_health.battery_level, "robot_id": robot_health.robot_id}
            ))
            alerts_created.append(alert)
        elif robot_health.battery_level < 20:
            alert = crud.create_system_alert(db, schemas.SystemAlertCreate(
                tenant_id=tenant_id,
                alert_type="robot_health",
                severity="high",
                title=f"Low Battery Warning: {robot_health.robot_id}",
                message=f"Robot {robot_health.robot_id} battery level is low at {robot_health.battery_level}%",
                source=robot_health.robot_id,
                data={"battery_level": robot_health.battery_level, "robot_id": robot_health.robot_id}
            ))
            alerts_created.append(alert)

    # Temperature alerts
    if robot_health.temperature_c is not None:
        if robot_health.temperature_c > 80:
            alert = crud.create_system_alert(db, schemas.SystemAlertCreate(
                tenant_id=tenant_id,
                alert_type="robot_health",
                severity="high",
                title=f"High Temperature: {robot_health.robot_id}",
                message=f"Robot {robot_health.robot_id} temperature is critically high at {robot_health.temperature_c}°C",
                source=robot_health.robot_id,
                data={"temperature_c": robot_health.temperature_c, "robot_id": robot_health.robot_id}
            ))
            alerts_created.append(alert)
        elif robot_health.temperature_c > 60:
            alert = crud.create_system_alert(db, schemas.SystemAlertCreate(
                tenant_id=tenant_id,
                alert_type="robot_health",
                severity="medium",
                title=f"Elevated Temperature: {robot_health.robot_id}",
                message=f"Robot {robot_health.robot_id} temperature is elevated at {robot_health.temperature_c}°C",
                source=robot_health.robot_id,
                data={"temperature_c": robot_health.temperature_c, "robot_id": robot_health.robot_id}
            ))
            alerts_created.append(alert)

    # Error count alerts
    if robot_health.error_count is not None and robot_health.error_count > 10:
        alert = crud.create_system_alert(db, schemas.SystemAlertCreate(
            tenant_id=tenant_id,
            alert_type="robot_health",
            severity="high",
            title=f"High Error Count: {robot_health.robot_id}",
            message=f"Robot {robot_health.robot_id} has accumulated {robot_health.error_count} errors",
            source=robot_health.robot_id,
            data={"error_count": robot_health.error_count, "robot_id": robot_health.robot_id}
        ))
        alerts_created.append(alert)

    # Offline status alert
    if robot_health.status == "offline":
        alert = crud.create_system_alert(db, schemas.SystemAlertCreate(
            tenant_id=tenant_id,
            alert_type="robot_health",
            severity="critical",
            title=f"Robot Offline: {robot_health.robot_id}",
            message=f"Robot {robot_health.robot_id} is offline and not responding",
            source=robot_health.robot_id,
            data={"status": robot_health.status, "robot_id": robot_health.robot_id}
        ))
        alerts_created.append(alert)

    return alerts_created
