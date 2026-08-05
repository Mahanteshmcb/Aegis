"""
Day 61: Estate Dashboard APIs
Real-time estate status, system monitoring, and integrated timeline events.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import random

from backend.dependencies import get_db, get_current_user
from backend.models_db import User

router = APIRouter(prefix="/api/v1", tags=["estate"])

# ========== SCHEMAS ==========

class SystemStatus(BaseModel):
    """Status of a single system"""
    id: str
    name: str
    status: str  # connected, degraded, offline
    health_score: int  # 0-100
    last_update: str


class EstateStatusResponse(BaseModel):
    """Overall estate health dashboard"""
    systems_online: int
    systems_total: int
    overall_health: int
    critical_alerts: int
    warnings: int
    last_update: str
    climate: SystemStatus
    energy: SystemStatus
    security: SystemStatus
    water: SystemStatus
    communications: SystemStatus


class SystemDataResponse(BaseModel):
    """Detailed data for a specific system"""
    system_id: str
    name: str
    status: str
    health_score: int
    data: Dict[str, Any]
    last_updated: str
    metrics: Dict[str, Any]


class TimelineEvent(BaseModel):
    """Single event in the estate timeline"""
    event_id: str
    timestamp: str
    event_type: str
    severity: str
    system: str
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None


class EstateTimelineResponse(BaseModel):
    """Timeline of estate events with pagination"""
    events: List[TimelineEvent]
    total_events: int
    page: int
    page_size: int
    total_pages: int
    filters_applied: Dict[str, Any]


class SystemsListResponse(BaseModel):
    """List of all systems in the estate"""
    systems: List[SystemStatus]
    total_systems: int
    last_update: str


# ========== HELPERS ==========

def get_mock_system_status(system_id: str, name: str) -> SystemStatus:
    """Generate mock system status"""
    statuses = ["connected", "connected", "connected", "degraded"]
    health_scores = [95, 88, 92, 75, 85]
    return SystemStatus(
        id=system_id,
        name=name,
        status=random.choice(statuses),
        health_score=random.choice(health_scores),
        last_update=datetime.utcnow().isoformat()
    )


def get_mock_estate_timeline(system_filter: Optional[str] = None, severity_filter: Optional[str] = None) -> List[TimelineEvent]:
    """Generate mock timeline events"""
    events = [
        TimelineEvent(
            event_id="evt_001",
            timestamp=(datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            event_type="alert",
            severity="warning",
            system="climate",
            title="Temperature spike detected",
            message="Zone B temperature exceeded setpoint by 2°C",
            details={"zone": "B", "temp_delta": 2.0}
        ),
        TimelineEvent(
            event_id="evt_002",
            timestamp=(datetime.utcnow() - timedelta(minutes=15)).isoformat(),
            event_type="info",
            severity="info",
            system="energy",
            title="Battery charging initiated",
            message="Solar charge cycle started",
            details={"battery_level": 65, "target": 90}
        ),
        TimelineEvent(
            event_id="evt_003",
            timestamp=(datetime.utcnow() - timedelta(minutes=30)).isoformat(),
            event_type="alert",
            severity="critical",
            system="security",
            title="Perimeter breach detected",
            message="Motion detected at sector 4",
            details={"sector": 4, "confidence": 0.89}
        ),
        TimelineEvent(
            event_id="evt_004",
            timestamp=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            event_type="info",
            severity="info",
            system="water",
            title="Irrigation cycle complete",
            message="Zone B irrigation finished",
            details={"zone": "B", "water_used_liters": 250}
        ),
        TimelineEvent(
            event_id="evt_005",
            timestamp=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
            event_type="alert",
            severity="warning",
            system="communications",
            title="Network latency high",
            message="Average latency 45ms (target: <20ms)",
            details={"latency_ms": 45, "packet_loss": 0.02}
        ),
    ]
    
    filtered = events
    if system_filter:
        filtered = [e for e in filtered if e.system == system_filter]
    if severity_filter:
        filtered = [e for e in filtered if e.severity == severity_filter]
    
    return filtered


# ========== ENDPOINTS ==========

@router.get("/estate/status", response_model=EstateStatusResponse, summary="Get estate overall status")
async def get_estate_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time overall estate health status.
    
    Returns aggregated health metrics for all major systems including climate,
    energy, security, water, and communications.
    """
    try:
        return EstateStatusResponse(
            systems_online=4,
            systems_total=5,
            overall_health=89,
            critical_alerts=1,
            warnings=2,
            last_update=datetime.utcnow().isoformat(),
            climate=get_mock_system_status("climate", "Climate Control"),
            energy=get_mock_system_status("energy", "Energy Management"),
            security=get_mock_system_status("security", "Security System"),
            water=get_mock_system_status("water", "Water Management"),
            communications=get_mock_system_status("comms", "Communications")
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error retrieving estate status: {str(e)}")
        raise


@router.get("/systems/{system_id}/data", response_model=SystemDataResponse, summary="Get system-specific data")
async def get_system_data(
    system_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed data for a specific system.
    
    Returns current readings, metrics, and health information for the requested system.
    """
    try:
        system_data_map = {
            "climate": {
                "name": "Climate Control",
                "data": {
                    "current_temp": 22.5,
                    "target_temp": 22.0,
                    "humidity": 55,
                    "zones": ["A", "B", "C"],
                    "active_units": 3
                },
                "metrics": {
                    "avg_temp_24h": 22.1,
                    "temp_variance": 1.2,
                    "efficiency": 94
                }
            },
            "energy": {
                "name": "Energy Management",
                "data": {
                    "battery_soc": 78,
                    "solar_generation": 4.2,
                    "current_load": 3.1,
                    "grid_connected": True
                },
                "metrics": {
                    "daily_generation_kwh": 18.5,
                    "daily_consumption_kwh": 16.2,
                    "efficiency": 91
                }
            },
            "security": {
                "name": "Security System",
                "data": {
                    "cameras_online": 12,
                    "perimeter_status": "secure",
                    "intrusion_alerts": 0,
                    "access_points": 8
                },
                "metrics": {
                    "uptime_percent": 99.8,
                    "false_positives": 0,
                    "response_time_ms": 50
                }
            },
            "water": {
                "name": "Water Management",
                "data": {
                    "tank_level": 85,
                    "flow_rate": 2.5,
                    "quality_ph": 7.2,
                    "purification_status": "nominal"
                },
                "metrics": {
                    "daily_consumption_liters": 450,
                    "recycling_rate": 35,
                    "waste_percent": 2
                }
            }
        }
        
        sys_info = system_data_map.get(system_id, {
            "name": f"Unknown System ({system_id})",
            "data": {},
            "metrics": {}
        })
        
        return SystemDataResponse(
            system_id=system_id,
            name=sys_info.get("name", "Unknown"),
            status="connected",
            health_score=87,
            data=sys_info.get("data", {}),
            last_updated=datetime.utcnow().isoformat(),
            metrics=sys_info.get("metrics", {})
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error retrieving system data: {str(e)}")
        raise


@router.get("/estate/timeline", response_model=EstateTimelineResponse, summary="Get estate timeline events")
async def get_estate_timeline(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    system: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get timeline of estate events with pagination and filtering.
    
    Parameters:
    - page: Page number (1-indexed)
    - page_size: Events per page (1-100)
    - system: Optional system filter (climate, energy, security, water, communications)
    - severity: Optional severity filter (critical, warning, info)
    """
    try:
        all_events = get_mock_estate_timeline(system, severity)
        
        total = len(all_events)
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_events = all_events[start_idx:end_idx]
        
        return EstateTimelineResponse(
            events=page_events,
            total_events=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            filters_applied={"system": system, "severity": severity}
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error retrieving timeline: {str(e)}")
        raise


@router.get("/systems", response_model=SystemsListResponse, summary="List all monitored systems")
async def list_all_systems(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all monitored systems in the estate with their current status.
    """
    try:
        systems = [
            get_mock_system_status("climate", "Climate Control"),
            get_mock_system_status("energy", "Energy Management"),
            get_mock_system_status("security", "Security System"),
            get_mock_system_status("water", "Water Management"),
            get_mock_system_status("comms", "Communications"),
        ]
        
        return SystemsListResponse(
            systems=systems,
            total_systems=len(systems),
            last_update=datetime.utcnow().isoformat()
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error retrieving systems list: {str(e)}")
        raise
