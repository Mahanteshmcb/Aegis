"""
Aegis Backend - Zones Router
Zone management endpoints.
"""


import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from backend.dependencies import get_current_user, require_permission
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session
from backend.dependencies import get_db

from backend.models.zones import Zone
from backend.models.digital_twin import DigitalTwinDevice
from backend import schemas

router = APIRouter(prefix="/api/v1", tags=["zones"])


def _record_zone_audit(db: Session, actor: dict, tenant_id: int, event_type: str, zone_id, zone_name: str, details: dict | None = None):
    from backend.audit_utils import record_audit_event
    from backend.blockchain_connector import get_blockchain_connector

    metadata = {
        **(details or {}),
        "action": event_type,
        "actor_user_id": actor["id"],
        "actor_email": actor["email"],
        "entity_type": "zone",
        "entity_id": str(zone_id),
        "zone_id": zone_id,
        "zone_name": zone_name,
        "outcome": "success",
    }
    record_audit_event(db, get_blockchain_connector(), tenant_id, event_type, metadata)


def _zone_query(db: Session, tenant_id: int | None = None):
    query = db.query(Zone)
    if hasattr(Zone, "tenant_id") and tenant_id is not None:
        query = query.filter(Zone.tenant_id == tenant_id)
    return query


class ZoneCreate(BaseModel):
    """Zone creation request."""
    name: str
    description: str = ""
    location: str = ""
    tenant_id: int | None = None
    spatial_position: dict[str, float] | None = None
    dimensions: dict[str, float] | None = None
    spatial_status: Literal["inferred", "surveyed"] = "inferred"
    coordinate_system: str | None = None
    length_unit: str = "m"


class ZoneResponse(BaseModel):
    """Zone response."""
    model_config = ConfigDict(from_attributes=True)

    id: int | str
    name: str
    description: str
    location: str
    tenant_id: int | None = None
    zone_id: str | None = None
    spatial_position: dict[str, float] | None = None
    dimensions: dict[str, float] | None = None
    spatial_status: str = "inferred"
    coordinate_system: str | None = None
    length_unit: str = "m"
    position: list[float] | None = None
    size: list[float] | None = None

    @field_validator("spatial_status", mode="before")
    @classmethod
    def default_legacy_spatial_status(cls, value):
        return value if value is not None else "inferred"

    @field_validator("length_unit", mode="before")
    @classmethod
    def default_legacy_length_unit(cls, value):
        return value if value is not None else "m"


def _validate_geometry(position, dimensions, spatial_status, coordinate_system, length_unit):
    if position is not None:
        if set(position) != {"x", "y", "z"} or not all(math.isfinite(value) for value in position.values()):
            raise HTTPException(status_code=422, detail="spatial_position must contain finite x, y, and z coordinates")
    if dimensions is not None:
        if set(dimensions) != {"width", "height", "depth"} or not all(
            math.isfinite(value) and value > 0 for value in dimensions.values()
        ):
            raise HTTPException(status_code=422, detail="dimensions must contain positive width, height, and depth")
    if spatial_status == "surveyed" and (
        position is None or dimensions is None
        or not isinstance(coordinate_system, str) or not coordinate_system.strip()
    ):
        raise HTTPException(
            status_code=422,
            detail="Surveyed geometry requires spatial_position, dimensions, and coordinate_system",
        )
    if not isinstance(length_unit, str) or not length_unit.strip():
        raise HTTPException(status_code=422, detail="length_unit cannot be blank")


@router.post("/zones", response_model=ZoneResponse)
async def create_zone(zone: ZoneCreate, db: Session = Depends(get_db), current_admin=Depends(require_permission("zones.manage"))):
    """Create a new zone (admin only, tenant protected)."""
    tenant_id = current_admin.get("tenant_id") if isinstance(current_admin, dict) else getattr(current_admin, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current admin")

    if zone.tenant_id is not None and zone.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot create zone for another tenant")
    _validate_geometry(
        zone.spatial_position, zone.dimensions, zone.spatial_status,
        zone.coordinate_system, zone.length_unit,
    )

    db_zone = Zone(
        name=zone.name,
        description=zone.description,
        location=zone.location or zone.name,
        tenant_id=tenant_id,
        spatial_position=zone.spatial_position,
        dimensions=zone.dimensions,
        spatial_status=zone.spatial_status,
        coordinate_system=zone.coordinate_system,
        length_unit=zone.length_unit,
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)

    try:
        from backend.models.environmental import EnvironmentalZone
        env_zone = EnvironmentalZone(
            zone_id=getattr(db_zone, "id", None) or getattr(db_zone, "zone_id", None),
            tenant_id=tenant_id,
            current_temperature=22.0,
            setpoint=22.0,
            hvac_mode='auto',
            fan_mode='auto',
            active_scene='home',
            occupancy_count=0,
        )
        db.add(env_zone)
        db.commit()
    except Exception as e:
        print(f"Warning: Failed to create environmental zone: {e}")

    _record_zone_audit(db, current_admin, tenant_id, "zone_created", db_zone.id, db_zone.name, {"location": db_zone.location})
    return db_zone


@router.get("/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get zone by ID (tenant protected)."""
    tenant_id = current_user["tenant_id"]
    zone = _zone_query(db, tenant_id).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")
    return zone


@router.get("/zones", response_model=list[ZoneResponse])
async def list_zones(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """List all zones for current tenant."""
    tenant_id = current_user["tenant_id"]
    zones = _zone_query(db, tenant_id).all()
    return zones


class ZoneUpdate(BaseModel):
    """Zone update request."""
    name: str | None = None
    description: str | None = None
    location: str | None = None
    spatial_position: dict[str, float] | None = None
    dimensions: dict[str, float] | None = None
    spatial_status: Literal["inferred", "surveyed"] | None = None
    coordinate_system: str | None = None
    length_unit: str | None = None


@router.put("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(zone_id: int, update: ZoneUpdate, db: Session = Depends(get_db), current_admin=Depends(require_permission("zones.manage"))):
    """Update a zone (admin only)."""
    tenant_id = current_admin.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current admin")

    db_zone = _zone_query(db, tenant_id).filter(Zone.id == zone_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")

    update_data = update.dict(exclude_unset=True)
    if update_data.get("spatial_status", "inferred") is None or update_data.get("length_unit", "m") is None:
        raise HTTPException(status_code=422, detail="spatial_status and length_unit cannot be null")
    _validate_geometry(
        update_data.get("spatial_position", db_zone.spatial_position),
        update_data.get("dimensions", db_zone.dimensions),
        update_data.get("spatial_status", db_zone.spatial_status or "inferred"),
        update_data.get("coordinate_system", db_zone.coordinate_system),
        update_data.get("length_unit", db_zone.length_unit or "m"),
    )
    for k, v in update_data.items():
        setattr(db_zone, k, v)

    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    _record_zone_audit(db, current_admin, tenant_id, "zone_updated", db_zone.id, db_zone.name, {
        "changed_fields": list(update_data.keys()),
        "changes": update_data,
    })
    return db_zone


@router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: int, db: Session = Depends(get_db), current_admin=Depends(require_permission("zones.manage"))):
    """Delete a zone (admin only)."""
    tenant_id = current_admin.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current admin")

    db_zone = _zone_query(db, tenant_id).filter(Zone.id == zone_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")
    deleted_zone_id = db_zone.id
    deleted_zone_name = db_zone.name
    deleted_location = db_zone.location
    try:
        from backend.models.environmental import EnvironmentalZone
        from backend.models_db import Sensor
        env = db.query(EnvironmentalZone).filter(EnvironmentalZone.zone_id == zone_id).first()
        if env:
            db.delete(env)

        sensors = db.query(Sensor).filter(Sensor.zone_id == zone_id).all()
        for s in sensors:
            s.zone_id = None
            db.add(s)

        twin_devices = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.tenant_id == tenant_id,
            DigitalTwinDevice.zone_id == zone_id,
        ).all()
        for device in twin_devices:
            device.zone_id = None

        db.delete(db_zone)
        _record_zone_audit(db, current_admin, tenant_id, "zone_deleted", deleted_zone_id, deleted_zone_name, {"location": deleted_location})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete zone cleanly: {e}")

    return {"detail": "Zone deleted"}