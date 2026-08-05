"""
HVAC schedule CRUD API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_current_user
from backend.models.hvac_schedule import HVACSchedule

router = APIRouter(prefix="/api/v1/hvac", tags=["hvac_schedules"])


class HVACCreate(BaseModel):
    name: str
    zone_id: int
    setpoint: float
    scheduled_at: datetime
    recurring: Optional[bool] = False
    interval_days: Optional[int] = None


class HVACResponse(BaseModel):
    id: int
    name: str
    zone_id: int
    setpoint: float
    scheduled_at: datetime
    recurring: bool
    enabled: bool


@router.post("/schedules", response_model=HVACResponse)
def create_schedule(payload: HVACCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sched = HVACSchedule(
        tenant_id=current_user["tenant_id"],
        zone_id=payload.zone_id,
        name=payload.name,
        setpoint=payload.setpoint,
        scheduled_at=payload.scheduled_at,
        recurring=bool(payload.recurring),
        interval_days=payload.interval_days,
        enabled=True,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


@router.get("/schedules", response_model=List[HVACResponse])
def list_schedules(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(HVACSchedule).filter(HVACSchedule.tenant_id == current_user["tenant_id"]).all()
    return items


@router.delete("/schedules/{sched_id}")
def delete_schedule(sched_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sched = db.query(HVACSchedule).filter(HVACSchedule.id == sched_id, HVACSchedule.tenant_id == current_user["tenant_id"]).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(sched)
    db.commit()
    return {"status": "deleted", "id": sched_id}


class HVACUpdate(BaseModel):
    name: Optional[str] = None
    zone_id: Optional[int] = None
    setpoint: Optional[float] = None
    scheduled_at: Optional[datetime] = None
    recurring: Optional[bool] = None
    interval_days: Optional[int] = None
    enabled: Optional[bool] = None


@router.put("/schedules/{sched_id}", response_model=HVACResponse)
def update_schedule(sched_id: int, payload: HVACUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sched = db.query(HVACSchedule).filter(HVACSchedule.id == sched_id, HVACSchedule.tenant_id == current_user["tenant_id"]).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if payload.name is not None:
        sched.name = payload.name
    if payload.zone_id is not None:
        sched.zone_id = payload.zone_id
    if payload.setpoint is not None:
        sched.setpoint = payload.setpoint
    if payload.scheduled_at is not None:
        sched.scheduled_at = payload.scheduled_at
    if payload.recurring is not None:
        sched.recurring = payload.recurring
    if payload.interval_days is not None:
        sched.interval_days = payload.interval_days
    if payload.enabled is not None:
        sched.enabled = payload.enabled
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched
