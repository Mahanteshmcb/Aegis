"""
Aegis Backend - Crop Management Router
Provides agricultural crop CRUD endpoints for tenant-aware crop lifecycle management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user, get_current_admin
from backend import schemas
from backend.blockchain_connector import get_blockchain_connector
from backend.audit_utils import record_audit_event
from backend.models_db import CropInstance, SpatialZone

router = APIRouter(prefix="/api/v1", tags=["Crop Management"])


def _record_crop_audit(db: Session, tenant_id: int, event_type: str, metadata: Dict[str, Any]) -> None:
    blockchain = get_blockchain_connector()
    try:
        record_audit_event(db, blockchain, tenant_id, event_type, metadata)
    except Exception:
        pass


@router.post("/crops", response_model=schemas.CropInstanceResponse)
async def create_crop_instance(
    crop: schemas.CropInstanceCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Create a new crop instance within the current tenant's spatial zone."""
    zone = db.query(SpatialZone).filter(
        SpatialZone.id == crop.spatial_zone_id,
        SpatialZone.tenant_id == current_admin["tenant_id"],
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Spatial zone not found or tenant mismatch")

    db_crop = CropInstance(**crop.dict())
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)

    _record_crop_audit(
        db,
        current_admin["tenant_id"],
        "crop_instance_created",
        {
            "crop_id": db_crop.id,
            "species_id": db_crop.species_id,
            "spatial_zone_id": db_crop.spatial_zone_id,
            "position": {
                "x": db_crop.position_x,
                "y": db_crop.position_y,
                "z": db_crop.position_z,
            },
            "planting_date": str(db_crop.planting_date) if db_crop.planting_date else None,
            "batch_id": db_crop.batch_id,
        },
    )

    return db_crop


@router.get("/crops/{crop_id}", response_model=schemas.CropInstanceResponse)
async def get_crop_instance(
    crop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get crop instance by ID for the current tenant."""
    crop = (
        db.query(CropInstance)
        .join(SpatialZone)
        .filter(
            CropInstance.id == crop_id,
            SpatialZone.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found or tenant mismatch")
    return crop


@router.get("/crops", response_model=List[schemas.CropInstanceResponse])
async def list_crop_instances(
    spatial_zone_id: Optional[int] = None,
    species_id: Optional[int] = None,
    health_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List crop instances for the current tenant with optional filters."""
    query = db.query(CropInstance).join(SpatialZone).filter(SpatialZone.tenant_id == current_user["tenant_id"])
    if spatial_zone_id is not None:
        query = query.filter(CropInstance.spatial_zone_id == spatial_zone_id)
    if species_id is not None:
        query = query.filter(CropInstance.species_id == species_id)
    if health_status is not None:
        query = query.filter(CropInstance.health_status == health_status)
    return query.offset(skip).limit(limit).all()


@router.put("/crops/{crop_id}", response_model=schemas.CropInstanceResponse)
async def update_crop_instance(
    crop_id: int,
    crop_update: schemas.CropInstanceUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Update a crop instance for the current tenant."""
    crop = (
        db.query(CropInstance)
        .join(SpatialZone)
        .filter(
            CropInstance.id == crop_id,
            SpatialZone.tenant_id == current_admin["tenant_id"],
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found or tenant mismatch")

    update_data = crop_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(crop, field, value)

    db.commit()
    db.refresh(crop)

    _record_crop_audit(
        db,
        current_admin["tenant_id"],
        "crop_instance_updated",
        {
            "crop_id": crop.id,
            "updated_fields": update_data,
        },
    )

    return crop


@router.delete("/crops/{crop_id}")
async def delete_crop_instance(
    crop_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Delete a crop instance for the current tenant."""
    crop = (
        db.query(CropInstance)
        .join(SpatialZone)
        .filter(
            CropInstance.id == crop_id,
            SpatialZone.tenant_id == current_admin["tenant_id"],
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop instance not found or tenant mismatch")

    db.delete(crop)
    db.commit()
    return {"detail": "Crop instance deleted"}
