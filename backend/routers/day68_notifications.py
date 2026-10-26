from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.dependencies import get_current_user, get_db, require_permission
from backend import crud
from backend import notification_engine
from backend.models.digital_twin import DigitalTwinDevice


class DeliveryConfigCreate(BaseModel):
    provider: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"retries": 3, "backoff_seconds": 5})


class DeliveryConfigResponse(DeliveryConfigCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
        from_attributes = True

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


def _redact_config(value):
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            normalized_key = str(key).casefold().replace("-", "_")
            if any(token in normalized_key for token in ("password", "secret", "token", "api_key", "authorization")):
                redacted[key] = "********"
            else:
                redacted[key] = _redact_config(item)
        return redacted
    if isinstance(value, list):
        return [_redact_config(item) for item in value]
    return value


@router.post("/rules")
async def create_rule(payload: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        nr = crud.create_notification_rule(db, current_user["tenant_id"], current_user["id"], payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    from backend.audit_utils import record_actor_audit_event
    from backend.blockchain_connector import get_blockchain_connector
    record_actor_audit_event(
        db, current_user["tenant_id"], current_user, "notification_rule_created",
        "notification_rule", nr.id, {"name": nr.name, "enabled": nr.enabled},
        blockchain=get_blockchain_connector(),
    )
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
    from backend.audit_utils import record_actor_audit_event
    from backend.blockchain_connector import get_blockchain_connector
    record_actor_audit_event(
        db, current_user["tenant_id"], current_user, "notification_rule_deleted",
        "notification_rule", rule_id, {},
        blockchain=get_blockchain_connector(),
    )
    return {"status": "success"}


@router.post("/rules/{rule_id}/evaluate")
async def evaluate_rule_endpoint(rule_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user["tenant_id"]
    devices = db.query(DigitalTwinDevice).filter(
        DigitalTwinDevice.tenant_id == tenant_id,
        DigitalTwinDevice.kind == "sensor",
    ).all()
    sensor_context = {
        device.device_id: {
            **(device.state or {}),
            "name": device.name,
            "status": device.status,
            "zone_id": device.zone_id,
            "device_type": device.device_type,
        }
        for device in devices
    }
    alert_id = notification_engine.evaluate_rule(
        db,
        tenant_id,
        rule_id,
        current_user.get("id"),
        context={"sensors": sensor_context},
    )
    if alert_id is None:
        return {"status": "success", "triggered": False}
    from backend.audit_utils import record_actor_audit_event
    from backend.blockchain_connector import get_blockchain_connector
    record_actor_audit_event(
        db, tenant_id, current_user, "notification_rule_triggered",
        "notification_rule", rule_id, {"alert_id": alert_id},
        blockchain=get_blockchain_connector(),
    )
    return {"status": "success", "triggered": True, "alert_id": alert_id}


@router.post("/delivery-configs")
async def create_delivery_config(payload: DeliveryConfigCreate, current_user=Depends(require_permission("alerts.manage")), db: Session = Depends(get_db)):
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
    from backend.audit_utils import record_actor_audit_event
    from backend.blockchain_connector import get_blockchain_connector
    record_actor_audit_event(
        db, current_user["tenant_id"], current_user, "alert_delivery_config_created",
        "alert_delivery_config", cfg.id,
        {"provider": cfg.provider, "enabled": cfg.enabled},
        blockchain=get_blockchain_connector(),
    )
    return {"status": "success", "data": {"id": cfg.id, "provider": cfg.provider}}


@router.get("/delivery-configs")
async def list_delivery_configs(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    configs = crud.list_alert_delivery_configs(db, current_user["tenant_id"])
    return {"status": "success", "data": [
        {
            "id": c.id,
            "provider": c.provider,
            "enabled": c.enabled,
            "config": _redact_config(c.config or {}),
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
