"""
Safety API - rules management and emergency stop
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_current_user
from backend.models.safety import (
    SafetyRule,
    SafetyEvent,
    EmergencyStop,
    PerimeterLockdown,
    AccessControlEvent,
    SecurityPatrol,
    EvacuationProtocol,
)

router = APIRouter(prefix="/api/v1/safety", tags=["safety"])


class RuleCreate(BaseModel):
    name: str
    sensor_type: str
    metric: str
    operator: str
    threshold: float
    severity: Optional[str] = "warning"


class RuleResp(BaseModel):
    id: int
    name: str
    sensor_type: str
    metric: str
    operator: str
    threshold: float
    severity: str
    enabled: bool


class EstopRequest(BaseModel):
    reason: Optional[str] = None


class PerimeterStatus(BaseModel):
    active: bool
    reason: Optional[str] = None
    initiated_by: Optional[str] = None


class BiometricScanRequest(BaseModel):
    user_name: str
    scan_id: str
    biometric_type: Optional[str] = "fingerprint"
    location: Optional[str] = "Main Gate"


class BiometricScanResponse(BaseModel):
    success: bool
    status: str
    message: str
    event_id: int


class AccessControlEventResponse(BaseModel):
    id: int
    user_name: Optional[str]
    method: str
    status: str
    location: Optional[str]
    message: str
    created_at: str


class PatrolStatus(BaseModel):
    active: bool
    route_name: Optional[str] = None
    assigned_robot: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class PatrolRequest(BaseModel):
    route_name: str
    assigned_robot: Optional[str] = None
    zone_sequence: Optional[List[str]] = []
    reason: Optional[str] = None


class EvacuationRequest(BaseModel):
    incident_type: str
    affected_zones: Optional[List[str]] = []
    reason: Optional[str] = None


class EvacuationStatus(BaseModel):
    active: bool
    initiated_by: Optional[str] = None
    incident_type: Optional[str] = None
    affected_zones: Optional[List[str]] = []
    stage: str
    instructions: Optional[str] = None
    reason: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


def _create_access_control_event(
    db: Session,
    tenant_id: int,
    user_name: Optional[str],
    method: str,
    status: str,
    location: Optional[str],
    message: str,
) -> AccessControlEvent:
    event = AccessControlEvent(
        tenant_id=tenant_id,
        user_name=user_name,
        method=method,
        status=status,
        location=location,
        message=message,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/rules", response_model=RuleResp)
def create_rule(payload: RuleCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rule = SafetyRule(
        tenant_id=current_user["tenant_id"],
        name=payload.name,
        sensor_type=payload.sensor_type,
        metric=payload.metric,
        operator=payload.operator,
        threshold=payload.threshold,
        severity=payload.severity,
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/rules", response_model=List[RuleResp])
def list_rules(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(SafetyRule).filter(SafetyRule.tenant_id == current_user["tenant_id"]).all()
    return items


@router.get("/events")
def list_events(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    events = (
        db.query(SafetyEvent)
        .filter(SafetyEvent.tenant_id == current_user["tenant_id"])
        .order_by(SafetyEvent.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": e.id,
            "message": e.message,
            "severity": e.severity,
            "created_at": e.created_at.isoformat(),
            "rule_id": e.rule_id,
        }
        for e in events
    ]


@router.get("/access/logs", response_model=List[AccessControlEventResponse])
def access_logs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    events = (
        db.query(AccessControlEvent)
        .filter(AccessControlEvent.tenant_id == current_user["tenant_id"])
        .order_by(AccessControlEvent.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": e.id,
            "user_name": e.user_name,
            "method": e.method,
            "status": e.status,
            "location": e.location,
            "message": e.message,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


def _get_latest_patrol(db: Session, tenant_id: int) -> SecurityPatrol | None:
    return (
        db.query(SecurityPatrol)
        .filter(SecurityPatrol.tenant_id == tenant_id)
        .order_by(SecurityPatrol.updated_at.desc())
        .first()
    )


def _get_latest_evacuation(db: Session, tenant_id: int) -> EvacuationProtocol | None:
    return (
        db.query(EvacuationProtocol)
        .filter(EvacuationProtocol.tenant_id == tenant_id)
        .order_by(EvacuationProtocol.updated_at.desc())
        .first()
    )


@router.get("/patrols/status", response_model=PatrolStatus)
def patrol_status(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    patrol = _get_latest_patrol(db, current_user["tenant_id"])
    if not patrol:
        return {
            "active": False,
            "status": "idle",
            "route_name": None,
            "assigned_robot": None,
            "started_at": None,
            "completed_at": None,
        }
    return {
        "active": patrol.active,
        "route_name": patrol.route_name,
        "assigned_robot": patrol.assigned_robot,
        "status": patrol.status,
        "started_at": patrol.started_at.isoformat() if patrol.started_at else None,
        "completed_at": patrol.completed_at.isoformat() if patrol.completed_at else None,
    }


@router.post("/patrols/start", response_model=PatrolStatus)
def start_patrol(payload: PatrolRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    active_patrol = _get_latest_patrol(db, current_user["tenant_id"])
    if active_patrol and active_patrol.active:
        raise HTTPException(status_code=400, detail="A patrol is already in progress")

    now = datetime.utcnow()
    patrol = SecurityPatrol(
        tenant_id=current_user["tenant_id"],
        active=True,
        route_name=payload.route_name,
        assigned_robot=payload.assigned_robot or "Aegis Rover Patrol Unit",
        status="patrolling",
        started_at=now,
    )
    db.add(patrol)
    db.commit()
    db.refresh(patrol)
    _create_access_control_event(
        db=db,
        tenant_id=current_user["tenant_id"],
        user_name=current_user.get("email"),
        method="robotic_patrol",
        status="started",
        location="estate perimeter",
        message=f"Robotic patrol '{payload.route_name}' started by {current_user.get('email')}.",
    )
    return {
        "active": patrol.active,
        "route_name": patrol.route_name,
        "assigned_robot": patrol.assigned_robot,
        "status": patrol.status,
        "started_at": patrol.started_at.isoformat() if patrol.started_at else None,
        "completed_at": None,
    }


@router.post("/patrols/stop", response_model=PatrolStatus)
def stop_patrol(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    patrol = _get_latest_patrol(db, current_user["tenant_id"])
    if not patrol or not patrol.active:
        raise HTTPException(status_code=404, detail="No active patrol found")

    patrol.active = False
    patrol.status = "completed"
    patrol.completed_at = datetime.utcnow()
    db.add(patrol)
    db.commit()
    db.refresh(patrol)
    _create_access_control_event(
        db=db,
        tenant_id=current_user["tenant_id"],
        user_name=current_user.get("email"),
        method="robotic_patrol",
        status="stopped",
        location="estate perimeter",
        message=f"Robotic patrol '{patrol.route_name}' stopped by {current_user.get('email')}.",
    )
    return {
        "active": patrol.active,
        "route_name": patrol.route_name,
        "assigned_robot": patrol.assigned_robot,
        "status": patrol.status,
        "started_at": patrol.started_at.isoformat() if patrol.started_at else None,
        "completed_at": patrol.completed_at.isoformat() if patrol.completed_at else None,
    }


@router.get("/evacuation", response_model=EvacuationStatus)
def evacuation_status(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    protocol = _get_latest_evacuation(db, current_user["tenant_id"])
    if not protocol:
        return {
            "active": False,
            "initiated_by": None,
            "incident_type": None,
            "affected_zones": [],
            "stage": "standby",
            "instructions": None,
            "reason": None,
            "started_at": None,
            "ended_at": None,
        }
    zones = protocol.affected_zones.split(",") if protocol.affected_zones else []
    return {
        "active": protocol.active,
        "initiated_by": protocol.initiated_by,
        "incident_type": protocol.incident_type,
        "affected_zones": zones,
        "stage": protocol.stage,
        "instructions": protocol.instructions,
        "reason": protocol.reason,
        "started_at": protocol.started_at.isoformat() if protocol.started_at else None,
        "ended_at": protocol.ended_at.isoformat() if protocol.ended_at else None,
    }


@router.post("/evacuation/trigger", response_model=EvacuationStatus)
def trigger_evacuation(payload: EvacuationRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    active_protocol = _get_latest_evacuation(db, current_user["tenant_id"])
    if active_protocol and active_protocol.active:
        raise HTTPException(status_code=400, detail="Evacuation protocol already active")

    now = datetime.utcnow()
    instructions = (
        "Activate perimeter lockdown, initiate robotic perimeter patrols, direct personnel to the nearest safe assembly zone, "
        "and notify the emergency response team."
    )
    protocol = EvacuationProtocol(
        tenant_id=current_user["tenant_id"],
        active=True,
        initiated_by=current_user.get("email"),
        incident_type=payload.incident_type,
        affected_zones=",".join(payload.affected_zones) if payload.affected_zones else None,
        stage="initiated",
        instructions=instructions,
        reason=payload.reason,
        started_at=now,
    )
    db.add(protocol)
    db.commit()
    db.refresh(protocol)
    _create_access_control_event(
        db=db,
        tenant_id=current_user["tenant_id"],
        user_name=current_user.get("email"),
        method="evacuation_protocol",
        status="initiated",
        location="estate perimeter",
        message=f"Evacuation protocol triggered by {current_user.get('email')} for {payload.incident_type}.",
    )
    return {
        "active": protocol.active,
        "initiated_by": protocol.initiated_by,
        "incident_type": protocol.incident_type,
        "affected_zones": payload.affected_zones or [],
        "stage": protocol.stage,
        "instructions": protocol.instructions,
        "reason": protocol.reason,
        "started_at": protocol.started_at.isoformat() if protocol.started_at else None,
        "ended_at": None,
    }


@router.post("/evacuation/complete", response_model=EvacuationStatus)
def complete_evacuation(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    protocol = _get_latest_evacuation(db, current_user["tenant_id"])
    if not protocol or not protocol.active:
        raise HTTPException(status_code=404, detail="No active evacuation protocol found")

    protocol.active = False
    protocol.stage = "completed"
    protocol.ended_at = datetime.utcnow()
    db.add(protocol)
    db.commit()
    db.refresh(protocol)
    _create_access_control_event(
        db=db,
        tenant_id=current_user["tenant_id"],
        user_name=current_user.get("email"),
        method="evacuation_protocol",
        status="completed",
        location="estate perimeter",
        message=f"Evacuation protocol completed by {current_user.get('email')}.",
    )
    zones = protocol.affected_zones.split(",") if protocol.affected_zones else []
    return {
        "active": protocol.active,
        "initiated_by": protocol.initiated_by,
        "incident_type": protocol.incident_type,
        "affected_zones": zones,
        "stage": protocol.stage,
        "instructions": protocol.instructions,
        "reason": protocol.reason,
        "started_at": protocol.started_at.isoformat() if protocol.started_at else None,
        "ended_at": protocol.ended_at.isoformat() if protocol.ended_at else None,
    }


@router.post("/access/biometric", response_model=BiometricScanResponse)
def biometric_access(payload: BiometricScanRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    authorized = bool(payload.scan_id and payload.scan_id.strip())
    if authorized:
        authorized = payload.scan_id.strip().upper().startswith("BIO") or payload.scan_id.strip().upper().endswith("123")

    status = "granted" if authorized else "denied"
    message = (
        f"Biometric access {status} for {payload.user_name} at {payload.location}."
        if payload.location
        else f"Biometric access {status} for {payload.user_name}."
    )
    event = _create_access_control_event(
        db=db,
        tenant_id=current_user["tenant_id"],
        user_name=payload.user_name,
        method=f"biometric:{payload.biometric_type}",
        status=status,
        location=payload.location,
        message=message,
    )

    if not authorized:
        raise HTTPException(status_code=403, detail="Biometric verification failed")

    return {
        "success": True,
        "status": status,
        "message": message,
        "event_id": event.id,
    }


@router.get("/perimeter", response_model=PerimeterStatus)
def perimeter_status(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lockdown = (
        db.query(PerimeterLockdown)
        .filter(PerimeterLockdown.tenant_id == current_user["tenant_id"])
        .first()
    )
    return {
        "active": bool(lockdown.active) if lockdown else False,
        "reason": lockdown.reason if lockdown else None,
        "initiated_by": lockdown.initiated_by if lockdown else None,
    }


@router.post("/perimeter/lockdown", response_model=PerimeterStatus)
def activate_lockdown(payload: EstopRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lockdown = (
        db.query(PerimeterLockdown)
        .filter(PerimeterLockdown.tenant_id == current_user["tenant_id"])
        .first()
    )
    if not lockdown:
        lockdown = PerimeterLockdown(
            tenant_id=current_user["tenant_id"],
            active=True,
            reason=payload.reason,
            initiated_by=current_user.get("email"),
        )
    else:
        lockdown.active = True
        lockdown.reason = payload.reason
        lockdown.initiated_by = current_user.get("email")
    db.add(lockdown)
    db.commit()
    db.refresh(lockdown)
    _create_access_control_event(
        db=db,
        tenant_id=current_user["tenant_id"],
        user_name=current_user.get("email"),
        method="perimeter_lockdown",
        status="activated",
        location="estate perimeter",
        message=f"Perimeter lockdown activated by {current_user.get('email')}.",
    )
    return {
        "active": lockdown.active,
        "reason": lockdown.reason,
        "initiated_by": lockdown.initiated_by,
    }


@router.post("/perimeter/release", response_model=PerimeterStatus)
def release_lockdown(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lockdown = (
        db.query(PerimeterLockdown)
        .filter(PerimeterLockdown.tenant_id == current_user["tenant_id"])
        .first()
    )
    if not lockdown:
        lockdown = PerimeterLockdown(
            tenant_id=current_user["tenant_id"],
            active=False,
            reason="Released",
            initiated_by=current_user.get("email"),
        )
    else:
        lockdown.active = False
        lockdown.reason = "Released"
        lockdown.initiated_by = current_user.get("email")
    db.add(lockdown)
    db.commit()
    db.refresh(lockdown)
    _create_access_control_event(
        db=db,
        tenant_id=current_user["tenant_id"],
        user_name=current_user.get("email"),
        method="perimeter_lockdown",
        status="released",
        location="estate perimeter",
        message=f"Perimeter lockdown released by {current_user.get('email')}.",
    )
    return {
        "active": lockdown.active,
        "reason": lockdown.reason,
        "initiated_by": lockdown.initiated_by,
    }


@router.post("/estop")
def estop_activate(payload: EstopRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    est = db.query(EmergencyStop).filter(EmergencyStop.tenant_id == current_user["tenant_id"]).first()
    if not est:
        est = EmergencyStop(tenant_id=current_user["tenant_id"], active=True, reason=payload.reason)
    else:
        est.active = True
        est.reason = payload.reason
    db.add(est)
    db.commit()
    return {"status": "estop_activated", "reason": payload.reason}


@router.post("/estop/release")
def estop_release(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    est = db.query(EmergencyStop).filter(EmergencyStop.tenant_id == current_user["tenant_id"]).first()
    if not est:
        raise HTTPException(status_code=404, detail="E-Stop not found")
    est.active = False
    est.reason = None
    db.add(est)
    db.commit()
    return {"status": "estop_released"}


@router.get("/estop")
def estop_status(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    est = db.query(EmergencyStop).filter(EmergencyStop.tenant_id == current_user["tenant_id"]).first()
    return {"active": bool(est.active) if est else False, "reason": est.reason if est else None}
