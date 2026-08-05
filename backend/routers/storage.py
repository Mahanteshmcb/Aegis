from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from backend.dependencies import get_db, get_current_user
from backend.models.storage import StorageFacility, InventoryItem
from backend.services import broadcast

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

class FacilityCreate(BaseModel):
    name: str
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

class InventoryResponse(BaseModel):
    id: int
    facility_id: int
    name: str
    description: Optional[str]
    quantity: float
    unit: Optional[str]
    lot_number: Optional[str]
    expires_at: Optional[datetime]

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
    # publish event
    try:
        asyncio.create_task(broadcast.publish({
            "type": "facility_update",
            "tenant_id": current_user["tenant_id"],
            "action": "created",
            "facility_id": fac.id,
            "name": fac.name,
        }))
    except Exception:
        pass
    return fac

@router.get("/facilities", response_model=List[FacilityResponse])
def list_facilities(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(StorageFacility).filter(StorageFacility.tenant_id == current_user["tenant_id"]).all()
    return items

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
    # publish event
    try:
        asyncio.create_task(broadcast.publish({
            "type": "inventory_update",
            "tenant_id": current_user["tenant_id"],
            "action": "created",
            "item_id": item.id,
            "facility_id": payload.facility_id,
            "name": item.name,
            "quantity": item.quantity,
        }))
    except Exception:
        pass
    return item

@router.get("/inventory", response_model=List[InventoryResponse])
def list_inventory(facility_id: Optional[int] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(InventoryItem).filter(InventoryItem.tenant_id == current_user["tenant_id"])
    if facility_id:
        q = q.filter(InventoryItem.facility_id == facility_id)
    return q.all()