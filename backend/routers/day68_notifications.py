from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.dependencies import get_current_user, get_db
from backend import crud
from backend import notification_engine


class DeliveryConfigCreate(BaseModel):
    provider: str
    enabled: bool = True
    config: Dict[str, Any] = {}
    retry_policy: Dict[str, Any] = {"retries": 3, "backoff_seconds": 5}


class DeliveryConfigResponse(DeliveryConfigCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DeliveryStatusResponse(BaseModel):
    id: int
    alert_id: int
    provider: str
    status: str
    attempts: int
    last_error: Optional[str] = None
    last_attempt_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.post("/rules")
async def create_rule(payload: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        nr = crud.create_notification_rule(db, current_user["tenant_id"], current_user["id"], payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success", "data": {"id": nr.id, "name": nr.name}}


@router.get("/rules")
async def list_rules(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    rules = crud.list_notification_rules(db, current_user["tenant_id"])
    out = []
    for r in rules:
        out.append({"id": r.id, "name": r.name, "condition": r.condition, "enabled": r.enabled})
    return {"status": "success", "data": out}


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    ok = crud.delete_notification_rule(db, current_user["tenant_id"], rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "success"}


@router.post("/rules/{rule_id}/evaluate")
async def evaluate_rule_endpoint(rule_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    alert_id = notification_engine.evaluate_rule(db, current_user["tenant_id"], rule_id, current_user.get("id"))
    if alert_id is None:
        return {"status": "success", "triggered": False}
    return {"status": "success", "triggered": True, "alert_id": alert_id}


@router.post("/delivery-configs")
async def create_delivery_config(payload: DeliveryConfigCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        cfg = crud.create_alert_delivery_config(
            db,
            current_user["tenant_id"],
            payload.provider,
            payload.config,
            enabled=payload.enabled,
            retry_policy=payload.retry_policy,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success", "data": {"id": cfg.id, "provider": cfg.provider}}


@router.get("/delivery-configs")
async def list_delivery_configs(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    configs = crud.list_alert_delivery_configs(db, current_user["tenant_id"])
    return {"status": "success", "data": [
        {
            "id": c.id,
            "provider": c.provider,
            "enabled": c.enabled,
            "config": c.config,
            "retry_policy": c.retry_policy,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in configs
    ]}


@router.get("/delivery-statuses")
async def list_delivery_statuses(alert_id: Optional[int] = None, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    statuses = crud.list_alert_delivery_statuses(db, current_user["tenant_id"], alert_id=alert_id)
    return {"status": "success", "data": [
        {
            "id": s.id,
            "alert_id": s.alert_id,
            "provider": s.provider,
            "status": s.status,
            "attempts": s.attempts,
            "last_error": s.last_error,
            "last_attempt_at": s.last_attempt_at.isoformat() if s.last_attempt_at else None,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in statuses
    ]}
