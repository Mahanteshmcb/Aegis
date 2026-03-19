"""
Aegis Backend - Zones Router
Zone management endpoints.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.dependencies import get_db

router = APIRouter(prefix="/api/v1", tags=["zones"])


class ZoneCreate(BaseModel):
    """Zone creation request."""
    name: str
    description: str = ""
    location: str = ""


class ZoneResponse(BaseModel):
    """Zone response."""
    id: str
    name: str
    description: str
    location: str
    tenant_id: str


@router.post("/zones", response_model=ZoneResponse)
async def create_zone(zone: ZoneCreate, db=Depends(get_db)):
    """Create a new zone. Implemented in Day 9."""
    return {"message": "Zone creation not yet implemented"}


@router.get("/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone_id: str, db=Depends(get_db)):
    """Get zone by ID. Implemented in Day 9."""
    return {"message": "Zone retrieval not yet implemented"}


@router.get("/zones")
async def list_zones(db=Depends(get_db)):
    """List all zones. Implemented in Day 9."""
    return {"zones": []}
