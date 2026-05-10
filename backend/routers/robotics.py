"""
Aegis Backend - Robotics Router

Exposes backend endpoints for robotic fleet management and control.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.dependencies import get_current_user, get_db
from backend.config import settings
from backend.blockchain_connector import get_blockchain_connector
from backend.audit_utils import record_audit_event

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.robotics_connector import RoboticsConnector

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


def _record_robot_audit(db: Session, blockchain, tenant_id: int, event_type: str, metadata: Dict[str, Any]) -> None:
    try:
        record_audit_event(db, blockchain, tenant_id, event_type, metadata)
    except Exception as e:
        logger.warning(f"Failed to record robotics audit event: {e}")


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

class Coordinate3D(BaseModel):
    x: float
    y: float
    z: float

class NavigationTarget(BaseModel):
    destination: Coordinate3D
    waypoints: Optional[List[Coordinate3D]] = []
    speed_percent: Optional[float] = 50.0
    use_obstacles_map: Optional[bool] = False

class NavigationCommandRequest(BaseModel):
    command_id: str
    robot_id: str
    destination: Coordinate3D
    waypoints: Optional[List[Coordinate3D]] = []
    speed_percent: Optional[float] = 50.0
    use_obstacles_map: Optional[bool] = False
    timeout_seconds: Optional[int] = 60
    zone_id: Optional[str] = None

class RoboticTaskRequest(BaseModel):
    task_id: str
    robot_id: str
    operation_type: str
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

class FleetCoordinationRequest(BaseModel):
    task_type: str  # "HARVEST", "PLANT", "SPRAY", "INSPECT", "MAINTAIN"
    zone_id: str
    priority: Optional[int] = 5
    robot_count: Optional[int] = 1
    task_parameters: Optional[Dict[str, Any]] = None


class FleetOptimizationRequest(BaseModel):
    zone_id: str
    optimization_criteria: Dict[str, Any]  # e.g., {"efficiency": 0.8, "safety": 0.9, "energy": 0.7}


class EmergencyFleetStopRequest(BaseModel):
    zone_id: Optional[str] = None
    reason: Optional[str] = "manual_override"


class FleetStatusResponse(BaseModel):
    total_robots: int
    active_robots: int
    idle_robots: int
    robots_in_maintenance: int
    active_tasks: int
    queued_tasks: int
    safety_incidents: int
    last_safety_check: int
    fleet_efficiency_percent: float
    zone_status: Dict[str, Dict[str, Any]]


class FleetCoordinationResponse(BaseModel):
    task_id: str
    assigned_robots: List[str]
    coordination_status: str
    estimated_completion_minutes: int
    safety_protocols_active: bool
    collision_avoidance_active: bool
    load_balancing_active: bool


class FleetOptimizationResponse(BaseModel):
    optimization_id: str
    zone_id: str
    recommended_deployments: List[Dict[str, Any]]
    efficiency_gain_percent: float
    safety_score: float
    energy_savings_percent: float


class EmergencyFleetStopResponse(BaseModel):
    emergency_stop_issued: bool
    affected_robots: List[str]
    reason: str
    timestamp_ms: int
    safety_protocols_engaged: bool
    all_tasks_cancelled: bool


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


@router.post("/fleet/coordinate", response_model=FleetCoordinationResponse)
async def fleet_coordinate_task(request: FleetCoordinationRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
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


@router.post("/fleet/optimize", response_model=FleetOptimizationResponse)
async def fleet_optimize_deployment(request: FleetOptimizationRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
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


@router.get("/fleet/status", response_model=FleetStatusResponse)
async def fleet_status(zone_id: Optional[str] = None, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    return connector.get_fleet_status(zone_id=zone_id)


@router.post("/fleet/emergency-stop", response_model=EmergencyFleetStopResponse)
async def fleet_emergency_stop(request: EmergencyFleetStopRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
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
