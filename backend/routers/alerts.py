from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_serializer
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from backend.dependencies import get_db, get_current_user
from backend.models_db import SystemAlert

router = APIRouter(prefix="/api/v1", tags=["alerts"])


class AlertCreate(BaseModel):
    alert_type: str  # "robot_health", "fleet_efficiency", "safety_incident", "system_error"
    severity: str  # "low", "medium", "high", "critical"
    title: str
    message: str
    source: str  # robot_id, zone_id, or "system"
    data: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    source: str
    data: Optional[Dict[str, Any]]
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at', 'updated_at', 'acknowledged_at')
    def serialize_datetime(self, value: Optional[datetime], _info):
        if value is None:
            return None
        return value.isoformat() if isinstance(value, datetime) else value


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(payload: AlertCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else None
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Invalid tenant")
        alert = SystemAlert(
            tenant_id=tenant_id,
            alert_type=payload.alert_type,
            severity=payload.severity,
            title=payload.title,
            message=payload.message,
            source=payload.source,
            data=payload.data or {},
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "source": alert.source,
            "data": alert.data,
            "acknowledged": alert.acknowledged,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    alert_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Accept either dict-like mock or object for current_user
    tenant_id = None
    if isinstance(current_user, dict):
        tenant_id = current_user.get("tenant_id")
    else:
        tenant_id = getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Invalid tenant")
    query = db.query(SystemAlert).filter(SystemAlert.tenant_id == tenant_id)
    if alert_type:
        query = query.filter(SystemAlert.alert_type == alert_type)
    if severity:
        query = query.filter(SystemAlert.severity == severity)
    alerts = query.order_by(SystemAlert.created_at.desc()).limit(100).all()
    return [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "source": a.source,
            "data": a.data,
            "acknowledged": a.acknowledged,
            "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat(),
        }
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/ack", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else None
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id, SystemAlert.tenant_id == tenant_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "message": alert.message,
        "source": alert.source,
        "data": alert.data,
        "acknowledged": alert.acknowledged,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat(),
    }
