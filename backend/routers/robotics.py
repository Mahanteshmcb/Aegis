"""
Aegis Backend - Robotics Router

Exposes backend endpoints for robotic fleet management and control.
"""

import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.dependencies import get_current_user
from backend.config import settings

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.robotics_connector import RoboticsConnector

router = APIRouter(prefix="/api/v1/robotics", tags=["Robotics"])

_robotics_connector = None

def get_robotics_connector() -> RoboticsConnector:
    global _robotics_connector
    if _robotics_connector is None:
        _robotics_connector = RoboticsConnector(
            host=settings.robotics_host,
            port=settings.robotics_port,
            timeout=settings.robotics_timeout,
            fallback_mode=settings.robotics_fallback_enabled,
        )
    return _robotics_connector


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
async def register_robot(request: RobotIdentityRequest, current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    result = connector.register_robot(
        robot_id=request.robot_id,
        robot_type=request.robot_type,
        firmware_version=request.firmware_version,
        model_year=request.model_year,
        capabilities=request.capabilities,
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
async def send_robot_task(request: RoboticTaskRequest, current_user=Depends(get_current_user)):
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
    return {
        "status": "success",
        "message": "Task dispatched",
        "data": result,
    }

@router.post("/navigate", response_model=StandardResponse)
async def navigate_robot(request: NavigationCommandRequest, current_user=Depends(get_current_user)):
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
