"""
Aegis Backend - Zones Router
Zone management endpoints.
"""


from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_current_admin, get_current_user
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
    tenant_id: int | None = None


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
    tenant_id = current_admin.get("tenant_id") if isinstance(current_admin, dict) else getattr(current_admin, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current admin")

    # If caller provided a tenant_id in payload, enforce it matches current admin
    if zone.tenant_id is not None and zone.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot create zone for another tenant")

    db_zone = Zone(
        name=zone.name,
        description=zone.description,
        location=zone.location,
        tenant_id=tenant_id,
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    
    # Automatically create environmental control zone for living quarters
    try:
        from backend.models.environmental import EnvironmentalZone
        env_zone = EnvironmentalZone(
            zone_id=db_zone.id,
            tenant_id=tenant_id,
            current_temperature=22.0,
            setpoint=22.0,
            hvac_mode='auto',
            fan_mode='auto',
            active_scene='home',
            occupancy_count=0
        )
        db.add(env_zone)
        db.commit()
    except Exception as e:
        # If environmental zone creation fails, continue anyway
        print(f"Warning: Failed to create environmental zone: {e}")
        pass

    # Audit log for zone creation
    zone_data = f"name={db_zone.name}|tenant_id={db_zone.tenant_id}|location={db_zone.location}"
    data_hash = hashlib.sha256(zone_data.encode()).hexdigest()
    
    # FIXED: Removed sensor_id=0 to prevent SQLite foreign key crash
    audit = schemas.AuditLogCreate(
        event_type="zone_created",
        data_hash=data_hash,
        blockchain_tx=None,
    )
    try:
        from backend import crud
        crud.create_audit_log(db, audit, tenant_id=current_admin["tenant_id"])
    except Exception:
        pass
    return db_zone


@router.get("/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get zone by ID (tenant protected)."""
    # CHANGE: Use ["tenant_id"] instead of .tenant_id
    zone = db.query(Zone).filter(Zone.id == zone_id, Zone.tenant_id == current_user["tenant_id"]).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")
    return zone


@router.get("/zones", response_model=list[ZoneResponse])
async def list_zones(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """List all zones for current tenant."""
    # CHANGE: Use ["tenant_id"] instead of .tenant_id
    zones = db.query(Zone).filter(Zone.tenant_id == current_user["tenant_id"]).all()
    return zones


class ZoneUpdate(BaseModel):
    """Zone update request."""
    name: str | None = None
    description: str | None = None
    location: str | None = None


@router.put("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(zone_id: int, update: ZoneUpdate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    """Update a zone (admin only)."""
    tenant_id = current_admin.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current admin")

    db_zone = db.query(Zone).filter(Zone.id == zone_id, Zone.tenant_id == tenant_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")

    update_data = update.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_zone, k, v)

    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


@router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    """Delete a zone (admin only)."""
    tenant_id = current_admin.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current admin")

    db_zone = db.query(Zone).filter(Zone.id == zone_id, Zone.tenant_id == tenant_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")
    # Remove environmental zone row first (it has a NOT NULL zone_id constraint)
    try:
        from backend.models.environmental import EnvironmentalZone
        from backend.models_db import Sensor
        env = db.query(EnvironmentalZone).filter(EnvironmentalZone.zone_id == db_zone.id).first()
        if env:
            db.delete(env)

        # Nullify sensors' zone_id (sensors.zone_id is nullable)
        sensors = db.query(Sensor).filter(Sensor.zone_id == db_zone.id).all()
        for s in sensors:
            s.zone_id = None
            db.add(s)

        db.delete(db_zone)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete zone cleanly: {e}")

    return {"detail": "Zone deleted"}