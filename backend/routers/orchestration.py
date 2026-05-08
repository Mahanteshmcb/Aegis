# Backend Router for Orchestration Engine
# Provides REST API endpoints for the Succession & Orchestration Engine

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ai.orchestrator import (
    run_orchestration_cycle,
    initialize_orchestration_engine,
    SuccessionEvent,
    RoboticAction
)
from ai.vryndara_connector import VryndaraConnector
from ai.robotics_connector import RoboticsConnector

router = APIRouter(prefix="/api/v1/orchestration", tags=["orchestration"])
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ZoneConfig(BaseModel):
    zone_id: int
    crop_sequence: List[Dict[str, Any]]
    companion_pairs: List[List[int]]  # Changed to List[List[int]] for JSON compatibility
    rotation_cycle_days: int
    last_rotation: datetime
    soil_health_targets: Dict[str, float]
    pest_monitoring_days: int

class OrchestrationStatus(BaseModel):
    zone_id: int
    last_cycle_time: Optional[datetime]
    active_triggers: int
    pending_actions: List[str]
    succession_plan_active: bool

class TriggerExecutionRequest(BaseModel):
    zone_id: int
    event_type: str
    parameters: Dict[str, Any] = {}

class OrchestrationCycleRequest(BaseModel):
    zone_id: int
    force_execution: bool = False

# Global variables for orchestration components
_orchestration_initialized = False
_vryndara_connector: Optional[VryndaraConnector] = None
_robotics_connector: Optional[RoboticsConnector] = None

@router.post("/initialize", summary="Initialize Orchestration Engine")
async def initialize_engine(zone_configs: List[ZoneConfig], background_tasks: BackgroundTasks):
    """
    Initialize the Succession & Orchestration Engine with zone configurations.

    This endpoint sets up the orchestration engine with succession plans,
    companion planting rules, and monitoring schedules for each zone.
    """
    global _orchestration_initialized, _vryndara_connector, _robotics_connector

    try:
        # Initialize connectors if not already done
        if not _vryndara_connector:
            _vryndara_connector = VryndaraConnector()
            await _vryndara_connector.connect()

        if not _robotics_connector:
            _robotics_connector = RoboticsConnector()
            await _robotics_connector.initialize()

        # Convert Pydantic models to dicts for the engine
        configs_dict = []
        for config in zone_configs:
            config_dict = config.dict()
            config_dict['companion_pairs'] = [tuple(pair) for pair in config.companion_pairs]
            configs_dict.append(config_dict)

        # Initialize the orchestration engine
        await initialize_orchestration_engine(
            _vryndara_connector,
            _robotics_connector,
            configs_dict
        )

        _orchestration_initialized = True

        return {
            "message": "Orchestration engine initialized successfully",
            "zones_configured": len(zone_configs),
            "status": "active"
        }

    except Exception as e:
        logger.error(f"Failed to initialize orchestration engine: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.post("/cycle", summary="Execute Orchestration Cycle")
async def execute_cycle(request: OrchestrationCycleRequest, background_tasks: BackgroundTasks):
    """
    Execute a complete orchestration cycle for a specific zone.

    This analyzes current conditions, evaluates succession events,
    and triggers appropriate robotic actions.
    """
    if not _orchestration_initialized:
        raise HTTPException(status_code=400, detail="Orchestration engine not initialized")

    try:
        # Run orchestration cycle in background
        background_tasks.add_task(run_orchestration_cycle, request.zone_id)

        return {
            "message": f"Orchestration cycle started for zone {request.zone_id}",
            "zone_id": request.zone_id,
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Failed to execute orchestration cycle: {e}")
        raise HTTPException(status_code=500, detail=f"Cycle execution failed: {str(e)}")

@router.post("/trigger", summary="Execute Manual Trigger")
async def execute_trigger(request: TriggerExecutionRequest):
    """
    Manually execute a specific orchestration trigger.

    Useful for testing or manual intervention in agricultural operations.
    """
    if not _orchestration_initialized:
        raise HTTPException(status_code=400, detail="Orchestration engine not initialized")

    try:
        # Validate event type
        try:
            event_type = SuccessionEvent(request.event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")

        # This would integrate with the orchestration engine's trigger execution
        # For now, return success
        logger.info(f"Manual trigger executed: {event_type.value} for zone {request.zone_id}")

        return {
            "message": f"Trigger {request.event_type} executed for zone {request.zone_id}",
            "event_type": request.event_type,
            "zone_id": request.zone_id,
            "parameters": request.parameters,
            "status": "executed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute manual trigger: {e}")
        raise HTTPException(status_code=500, detail=f"Trigger execution failed: {str(e)}")

@router.get("/status/{zone_id}", summary="Get Orchestration Status")
async def get_orchestration_status(zone_id: int):
    """
    Get the current status of the orchestration engine for a specific zone.

    Returns information about active triggers, pending actions, and succession plan status.
    """
    if not _orchestration_initialized:
        raise HTTPException(status_code=400, detail="Orchestration engine not initialized")

    try:
        # This would query the actual orchestration engine status
        # For now, return mock status
        status = OrchestrationStatus(
            zone_id=zone_id,
            last_cycle_time=datetime.now(),
            active_triggers=3,
            pending_actions=["irrigation", "pest_control", "planting"],
            succession_plan_active=True
        )

        return status

    except Exception as e:
        logger.error(f"Failed to get orchestration status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.get("/events", summary="Get Recent Orchestration Events")
async def get_recent_events(zone_id: Optional[int] = None, limit: int = 50):
    """
    Get recent orchestration events and decisions.

    Useful for monitoring system activity and decision-making history.
    """
    if not _orchestration_initialized:
        raise HTTPException(status_code=400, detail="Orchestration engine not initialized")

    try:
        # This would query the actual decision history
        # For now, return mock events
        mock_events = [
            {
                "timestamp": datetime.now().isoformat(),
                "zone_id": zone_id or 1,
                "event_type": "planting_season",
                "priority": 8,
                "actions": ["plant_seed"],
                "outcome": "success"
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "zone_id": zone_id or 1,
                "event_type": "pest_detection",
                "priority": 10,
                "actions": ["pest_control", "scouting"],
                "outcome": "success"
            }
        ]

        # Filter by zone if specified
        if zone_id:
            mock_events = [e for e in mock_events if e["zone_id"] == zone_id]

        return {
            "events": mock_events[:limit],
            "total_count": len(mock_events),
            "zone_filter": zone_id
        }

    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail=f"Events retrieval failed: {str(e)}")

@router.post("/maintenance/{zone_id}", summary="Schedule Maintenance Cycle")
async def schedule_maintenance(zone_id: int, maintenance_type: str):
    """
    Schedule a maintenance cycle for a specific zone.

    Triggers appropriate robotic actions for zone maintenance.
    """
    if not _orchestration_initialized:
        raise HTTPException(status_code=400, detail="Orchestration engine not initialized")

    valid_types = ["irrigation", "pruning", "soil_testing", "scouting"]
    if maintenance_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid maintenance type. Valid types: {valid_types}")

    try:
        # This would trigger maintenance through the orchestration engine
        logger.info(f"Maintenance scheduled: {maintenance_type} for zone {zone_id}")

        return {
            "message": f"Maintenance {maintenance_type} scheduled for zone {zone_id}",
            "zone_id": zone_id,
            "maintenance_type": maintenance_type,
            "scheduled_time": datetime.now(),
            "status": "scheduled"
        }

    except Exception as e:
        logger.error(f"Failed to schedule maintenance: {e}")
        raise HTTPException(status_code=500, detail=f"Maintenance scheduling failed: {str(e)}")

@router.get("/analytics/{zone_id}", summary="Get Orchestration Analytics")
async def get_orchestration_analytics(zone_id: int, days: int = 30):
    """
    Get analytics and insights from the orchestration engine for a zone.

    Provides data on decision patterns, success rates, and system performance.
    """
    if not _orchestration_initialized:
        raise HTTPException(status_code=400, detail="Orchestration engine not initialized")

    try:
        # This would analyze the decision history
        # For now, return mock analytics
        analytics = {
            "zone_id": zone_id,
            "period_days": days,
            "total_decisions": 245,
            "success_rate": 0.92,
            "most_common_events": [
                {"event": "irrigation", "count": 45},
                {"event": "pest_control", "count": 32},
                {"event": "planting", "count": 28}
            ],
            "average_response_time_minutes": 12.5,
            "crop_health_trend": "improving",
            "soil_health_trend": "stable",
            "automation_efficiency": 0.87
        }

        return analytics

    except Exception as e:
        logger.error(f"Failed to get orchestration analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")