"""
Aegis Backend - Zones Router
Zone management endpoints.
"""


from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_current_user
from backend.dependencies import get_current_admin
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.dependencies import get_db

from backend.models_db import Zone
from backend.db import Base
from backend import schemas

router = APIRouter(prefix="/api/v1", tags=["zones"])



class ZoneCreate(BaseModel):
    """Zone creation request."""
    name: str
    description: str = ""
    location: str = ""
    tenant_id: int



class ZoneResponse(BaseModel):
    """Zone response."""
    id: int
    name: str
    description: str
    location: str
    tenant_id: int



@router.post("/zones", response_model=ZoneResponse)
async def create_zone(zone: ZoneCreate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    """Create a new zone (admin only, tenant protected)."""
    import hashlib
    if zone.tenant_id != current_admin["tenant_id"]:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    db_zone = Zone(
        name=zone.name,
        description=zone.description,
        location=zone.location,
        tenant_id=zone.tenant_id,
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    # Audit log for zone creation
    zone_data = f"name={db_zone.name}|tenant_id={db_zone.tenant_id}|location={db_zone.location}"
    data_hash = hashlib.sha256(zone_data.encode()).hexdigest()
    audit = schemas.AuditLogCreate(
        sensor_id=0,  # Not applicable for zone creation
        event_type="zone_created",
        data_hash=data_hash,
        blockchain_tx=None,
    )
    try:
        crud.create_audit_log(db, audit)
    except Exception:
        pass  # Do not block zone creation if audit log fails
    return db_zone



@router.get("/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get zone by ID (tenant protected)."""
    zone = db.query(Zone).filter(Zone.id == zone_id, Zone.tenant_id == current_user["tenant_id"]).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")
    return zone



@router.get("/zones", response_model=list[ZoneResponse])
async def list_zones(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """List all zones for current tenant."""
    zones = db.query(Zone).filter(Zone.tenant_id == current_user["tenant_id"]).all()
    return zones
