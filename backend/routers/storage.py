from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from backend.dependencies import get_db, get_current_user
from backend.models.storage import StorageFacility, InventoryItem
from backend.services.domain_simulation import advance_storage_simulation
from backend.services import broadcast

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


class SimulationAdvanceRequest(BaseModel):
    step_hours: float = Field(default=24.0, gt=0, le=720)

class FacilityCreate(BaseModel):
    name: str
    location: Optional[str] = None
    type: Optional[str] = None
    capacity: Optional[float] = None

class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    capacity: Optional[float] = None

class FacilityResponse(BaseModel):
    id: int
    name: str
    location: Optional[str]
    type: Optional[str]
    capacity: Optional[float]

class InventoryCreate(BaseModel):
    facility_id: int
    name: str
    description: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    lot_number: Optional[str] = None
    expires_at: Optional[datetime] = None

class InventoryUpdate(BaseModel):
    facility_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    lot_number: Optional[str] = None
    expires_at: Optional[datetime] = None

class InventoryResponse(BaseModel):
    id: int
    facility_id: int
    name: str
    description: Optional[str]
    quantity: float
    unit: Optional[str]
    lot_number: Optional[str]
    expires_at: Optional[datetime]

def _audit_storage_change(db: Session, current_user: dict, event_type: str, metadata: dict):
    from backend.audit_utils import record_audit_event
    from backend.blockchain_connector import get_blockchain_connector
    entity_type = "storage_facility" if "facility" in event_type else "inventory_item"
    entity_id = metadata.get("facility_id") if entity_type == "storage_facility" else metadata.get("item_id")
    record_audit_event(db, get_blockchain_connector(), current_user["tenant_id"], event_type, {
        **metadata,
        "action": event_type,
        "actor_user_id": current_user["id"],
        "actor_email": current_user["email"],
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id is not None else None,
        "outcome": "success",
    })

def _publish_storage_event(payload: dict):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast.publish(payload))
    except RuntimeError:
        return

@router.post("/facilities", response_model=FacilityResponse)
def create_facility(payload: FacilityCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    fac = StorageFacility(
        tenant_id=current_user["tenant_id"],
        name=payload.name,
        location=payload.location,
        type=payload.type,
        capacity=payload.capacity,
    )
    db.add(fac)
    db.commit()
    db.refresh(fac)
    _audit_storage_change(db, current_user, "storage_facility_created", {"facility_id": fac.id, "name": fac.name})
    # publish event
    _publish_storage_event({
        "type": "facility_update",
        "tenant_id": current_user["tenant_id"],
        "action": "created",
        "facility_id": fac.id,
        "name": fac.name,
    })
    return fac

@router.get("/facilities", response_model=List[FacilityResponse])
def list_facilities(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(StorageFacility).filter(StorageFacility.tenant_id == current_user["tenant_id"]).all()
    return items

@router.put("/facilities/{facility_id}", response_model=FacilityResponse)
def update_facility(facility_id: int, payload: FacilityUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    facility = db.query(StorageFacility).filter(
        StorageFacility.id == facility_id,
        StorageFacility.tenant_id == current_user["tenant_id"],
    ).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(facility, field, value)
    db.commit()
    db.refresh(facility)
    _audit_storage_change(db, current_user, "storage_facility_updated", {"facility_id": facility.id, "name": facility.name, "changes": payload.dict(exclude_unset=True)})
    return facility

@router.delete("/facilities/{facility_id}")
def delete_facility(facility_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    facility = db.query(StorageFacility).filter(
        StorageFacility.id == facility_id,
        StorageFacility.tenant_id == current_user["tenant_id"],
    ).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    if db.query(InventoryItem).filter(InventoryItem.facility_id == facility.id).first():
        raise HTTPException(status_code=409, detail="Move or remove inventory before deleting this facility")
    metadata = {"facility_id": facility.id, "name": facility.name}
    db.delete(facility)
    db.commit()
    _audit_storage_change(db, current_user, "storage_facility_deleted", metadata)
    return {"deleted": True, "facility_id": facility_id}

@router.post("/inventory", response_model=InventoryResponse)
def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    fac = db.query(StorageFacility).filter(StorageFacility.id == payload.facility_id, StorageFacility.tenant_id == current_user["tenant_id"]).first()
    if not fac:
        raise HTTPException(status_code=404, detail="Facility not found")
    item = InventoryItem(
        tenant_id=current_user["tenant_id"],
        facility_id=payload.facility_id,
        name=payload.name,
        description=payload.description,
        quantity=payload.quantity,
        unit=payload.unit,
        lot_number=payload.lot_number,
        expires_at=payload.expires_at,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    _audit_storage_change(db, current_user, "storage_inventory_created", {"item_id": item.id, "facility_id": item.facility_id, "name": item.name, "quantity": item.quantity, "unit": item.unit})
    # publish event
    _publish_storage_event({
        "type": "inventory_update",
        "tenant_id": current_user["tenant_id"],
        "action": "created",
        "item_id": item.id,
        "facility_id": payload.facility_id,
        "name": item.name,
        "quantity": item.quantity,
    })
    return item

@router.get("/inventory", response_model=List[InventoryResponse])
def list_inventory(facility_id: Optional[int] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(InventoryItem).filter(InventoryItem.tenant_id == current_user["tenant_id"])
    if facility_id:
        q = q.filter(InventoryItem.facility_id == facility_id)
    return q.all()

@router.put("/inventory/{item_id}", response_model=InventoryResponse)
def update_inventory(item_id: int, payload: InventoryUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.tenant_id == current_user["tenant_id"],
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    update_data = payload.dict(exclude_unset=True)
    if "facility_id" in update_data:
        facility = db.query(StorageFacility).filter(
            StorageFacility.id == update_data["facility_id"],
            StorageFacility.tenant_id == current_user["tenant_id"],
        ).first()
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    _audit_storage_change(db, current_user, "storage_inventory_updated", {"item_id": item.id, "facility_id": item.facility_id, "name": item.name, "changes": update_data})
    return item

@router.delete("/inventory/{item_id}")
def delete_inventory(item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.tenant_id == current_user["tenant_id"],
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    metadata = {"item_id": item.id, "facility_id": item.facility_id, "name": item.name}
    db.delete(item)
    db.commit()
    _audit_storage_change(db, current_user, "storage_inventory_deleted", metadata)
    return {"deleted": True, "item_id": item_id}


@router.post("/simulation/advance")
def advance_storage_demo(
    payload: SimulationAdvanceRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return advance_storage_simulation(db, current_user["tenant_id"], payload.step_hours)