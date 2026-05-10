"""
Aegis Backend - Crop Lifecycle Router
Tracks lifecycle events for crop instances and preserves tenant isolation.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user, get_current_admin
from backend import schemas
from backend.blockchain_connector import get_blockchain_connector
from backend.audit_utils import record_audit_event
from backend.models_db import CropLifecycleEvent, CropInstance, SpatialZone

router = APIRouter(prefix="/api/v1", tags=["Crop Lifecycle"])


def _record_lifecycle_audit(db: Session, tenant_id: int, event_type: str, metadata: Dict[str, Any]) -> None:
    blockchain = get_blockchain_connector()
    try:
        record_audit_event(db, blockchain, tenant_id, event_type, metadata)
    except Exception:
        pass


@router.post("/crops/{crop_id}/lifecycle", response_model=schemas.CropLifecycleEventResponse)
async def create_crop_lifecycle_event(
    crop_id: int,
    event: schemas.CropLifecycleEventCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
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

    db_event = CropLifecycleEvent(crop_instance_id=crop_id, **event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    _record_lifecycle_audit(
        db,
        current_admin["tenant_id"],
        "crop_lifecycle_event",
        {
            "crop_id": crop_id,
            "event_type": event.event_type,
            "event_date": str(event.event_date),
            "data": event.data,
            "action_taken": event.action_taken,
            "blockchain_tx": event.blockchain_tx,
        },
    )

    return db_event


@router.get("/crops/{crop_id}/lifecycle", response_model=List[schemas.CropLifecycleEventResponse])
async def list_crop_lifecycle_events(
    crop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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

    events = (
        db.query(CropLifecycleEvent)
        .filter(CropLifecycleEvent.crop_instance_id == crop_id)
        .order_by(CropLifecycleEvent.event_date.desc())
        .all()
    )
    return events
