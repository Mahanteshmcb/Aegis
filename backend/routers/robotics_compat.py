"""
Aegis Backend - Robotics Compatibility Router

Provides compatibility routes for frontend pages that use legacy /api/v1/robots URLs.
"""

from fastapi import APIRouter, Depends
from backend.dependencies import get_current_user
from backend.routers.robotics import get_robotics_connector

router = APIRouter(prefix="/api/v1", tags=["Robotics Compatibility"])

@router.get("/robots")
async def list_robots(current_user=Depends(get_current_user)):
    """Return active robots for legacy frontend compatibility."""
    connector = get_robotics_connector()
    return connector.list_active_robots()
