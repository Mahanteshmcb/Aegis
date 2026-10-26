"""
Aegis Backend - Estate Config Router
REST endpoints to load, export, and inspect the universal estate_config.json
layout. Powers the "swap one JSON file to change the estate" demo capability.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Query, WebSocket
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
import json
import os
import tempfile

from backend.dependencies import get_db, get_current_user, has_permission, require_permission
from backend.database import Device, Zone
from backend.estate_config import (
    load_estate_config,
    build_graph,
    persist_estate_config,
    export_estate_config,
    load_and_persist,
    EstateConfig,
)

router = APIRouter(prefix="/api/v1/estate-config", tags=["estate-config"])


def _record_estate_audit(db: Session, current_user: dict, event_type: str, entity_type: str, entity_id, details: dict):
    from backend.audit_utils import record_actor_audit_event
    from backend.blockchain_connector import get_blockchain_connector

    record_actor_audit_event(
        db,
        current_user["tenant_id"],
        current_user,
        event_type,
        entity_type,
        entity_id,
        details,
        blockchain=get_blockchain_connector(),
    )


def _require_estate_permissions(current_user: dict, *permissions: str) -> None:
    if any(not has_permission(current_user, permission) for permission in permissions):
        raise HTTPException(status_code=403, detail="Missing required estate management permission")


def _device_response(device: Device) -> dict:
    environment = json.loads(device.environment_data) if device.environment_data else {}
    return {
        "id": device.id,
        "device_id": device.device_id,
        "type": device.device_type,
        "subtype": device.subtype,
        "zone_id": str(device.zone_id) if device.zone_id is not None else None,
        "name": device.name,
        "position": {"x": device.position_x, "y": device.position_y, "z": device.position_z},
        "status": device.status,
        "asset_ratio": device.asset_ratio,
        "last_reading": device.last_reading,
        "units": device.units,
        "battery_level": device.battery_level,
        "payload_capacity": device.payload_capacity,
        "max_speed_m_s": device.max_speed_m_s,
        "dimensions": environment.get("dimensions"),
        "environment_data": environment,
    }


def _tenant_zone_id(db: Session, zone_id: str | None, tenant_id: int) -> int | None:
    if zone_id is None:
        return None
    try:
        numeric_id = int(zone_id)
    except (TypeError, ValueError):
        numeric_id = None
    query = db.query(Zone).filter(Zone.tenant_id == tenant_id)
    zone = query.filter(Zone.id == numeric_id).first() if numeric_id is not None else None
    if zone is None:
        zone = db.query(Zone).filter(
            Zone.tenant_id == tenant_id,
            Zone.name == zone_id,
        ).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found or tenant mismatch")
    return zone.id


# Pydantic models for API requests/responses

class DeviceCreate(BaseModel):
    """Schema for creating a new device in the digital twin."""
    device_id: str = Field(..., description="Unique device identifier")
    type: str = Field(..., description="Device type: sensor, rover, zone, actuator")
    subtype: Optional[str] = Field(None, description="Sensor or rover subtype")
    zone_id: Optional[str] = Field(None, description="Target zone ID")
    position: Optional[Dict[str, float]] = Field(
        None, description="Position in digital twin coordinates (x, y, z)"
    )
    status: Optional[str] = Field("idle", description="Initial status")
    asset_ratio: Optional[str] = Field(
        None, description="Model-to-real-world ratio (e.g., '1:100')"
    )
    battery_level: Optional[float] = Field(
        None, description="Battery level 0-100 (rovers only)"
    )
    payload_capacity: Optional[str] = Field(
        None, description="Payload capacity (rovers only), e.g., '20kg'"
    )
    max_speed_m_s: Optional[float] = Field(
        None, description="Max speed in m/s (rovers only)"
    )
    dimensions: Optional[Dict[str, float]] = Field(
        None, description="Device dimensions (length, width, height)"
    )
    threshold_low: Optional[float] = Field(None, description="Low threshold")
    threshold_high: Optional[float] = Field(None, description="High threshold")
    units: Optional[str] = Field("%", description="Units for readings")
    environment_data: Optional[Dict] = Field(None, description="Environment data JSON")


class DeviceUpdate(BaseModel):
    """Schema for updating device status and properties."""
    position: Optional[Dict[str, float]] = Field(None, description="New position")
    status: Optional[str] = Field(None, description="New status")
    last_reading: Optional[float] = Field(None, description="New sensor reading")
    units: Optional[str] = Field(None, description="New units")
    battery_level: Optional[float] = Field(
        None, description="Battery level 0-100 (rovers)"
    )
    payload_capacity: Optional[str] = Field(
        None, description="New payload capacity (rovers)"
    )
    max_speed_m_s: Optional[float] = Field(
        None, description="New max speed (rovers)"
    )
    dimensions: Optional[Dict[str, float]] = Field(None, description="New device dimensions")
    asset_ratio: Optional[str] = Field(None, description="New asset ratio")
    threshold_low: Optional[float] = Field(None, description="New low threshold")
    threshold_high: Optional[float] = Field(None, description="New high threshold")
    environment_data: Optional[Dict] = Field(None, description="New environment data")


class ZoneCreate(BaseModel):
    """Schema for creating/updating a zone."""
    zone_id: str = Field(..., description="Unique zone identifier")
    name: Optional[str] = Field(None, description="Zone name")
    coordinates: Optional[Dict] = Field(
        None, description="Zone coordinates {x, y, width_meters, depth_meters}"
    )
    asset_ratio: Optional[str] = Field(
        "1:100", description="Model-to-real-world ratio"
    )
    position_ratio: Optional[str] = None
    target_metrics: Optional[Dict[str, Any]] = None


class SensorEvaluation(BaseModel):
    """Schema for sensor reading evaluation."""
    sensor_type: str = Field(..., description="Type of sensor (soil_moisture, temperature, etc.)")
    value: float = Field(..., description="Sensor reading value")
    zone_id: str = Field(..., description="Zone ID to evaluate against")

class EstateConfigResponse(BaseModel):
    estate_id: str
    estate_type: str
    name: str
    zones: list[Any]
    devices: list[Any]


class LoadResponse(BaseModel):
    estate_id: str
    tenant_id: int
    zones_created: int
    devices_created: int
    graph: Dict[str, Any]
    zones: list[Any]
    devices: list[Any]


@router.post("/load", response_model=LoadResponse, summary="Load estate config from JSON file")
async def load_config(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload an estate_config.json and persist zones/devices to SQLite."""
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    _require_estate_permissions(current_user, "zones.manage", "devices.manage")

    contents = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    try:
        tmp.write(contents)
        tmp.close()
        summary = load_and_persist(tmp.name, tenant_id=tenant_id)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    _record_estate_audit(
        db, current_user, "estate_config_loaded", "estate", summary["estate_id"],
        {"zones_created": summary["zones_created"], "devices_created": summary["devices_created"]},
    )
    return LoadResponse(
        estate_id=summary["estate_id"],
        tenant_id=summary["tenant_id"],
        zones_created=summary["zones_created"],
        devices_created=summary["devices_created"],
        graph=summary["graph"],
        zones=summary["zones"],
        devices=summary["devices"],
    )


@router.post("/load/path", response_model=LoadResponse, summary="Load estate config from a server path")
async def load_config_path(
    payload: Dict[str, str],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Load estate_config.json from a path on the server (e.g. ./estate_config.json)."""
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    _require_estate_permissions(current_user, "zones.manage", "devices.manage")
    path = payload.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    summary = load_and_persist(path, tenant_id=tenant_id)
    _record_estate_audit(
        db, current_user, "estate_config_loaded", "estate", summary["estate_id"],
        {"zones_created": summary["zones_created"], "devices_created": summary["devices_created"]},
    )
    return LoadResponse(
        estate_id=summary["estate_id"],
        tenant_id=summary["tenant_id"],
        zones_created=summary["zones_created"],
        devices_created=summary["devices_created"],
        graph=summary["graph"],
        zones=summary["zones"],
        devices=summary["devices"],
    )


@router.get("/", response_model=EstateConfigResponse, summary="Export current tenant estate config")
def get_config(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("devices.manage")),
):
    """Round-trip export of the current tenant's zones as an estate config."""
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    data = export_estate_config(db, tenant_id)
    return EstateConfigResponse(
        estate_id=data["estate_id"],
        estate_type=data["estate_type"],
        name=data.get("name", data["estate_id"]),
        zones=data["zones"],
        devices=[],
    )


@router.get("/graph", summary="Get in-memory spatial graph summary for the sample config")
def graph_summary(path: Optional[str] = None):
    """Build (without persisting) a NetworkX graph summary from a config file path."""
    p = path or "./estate_config.json"
    try:
        cfg = load_estate_config(p)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Config file not found: {p}")
    graph = build_graph(cfg)
    return graph.as_dict()


@router.post("/devices", summary="Add new device to digital twin")
def add_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a new sensor or rover to the digital twin."""
    device_id = device_data.device_id
    if not device_id:
        raise HTTPException(400, "device_id is required")
    
    existing = db.query(Device).filter(Device.device_id == device_id).first()
    if existing:
        raise HTTPException(409, f"Device ID '{device_id}' already exists")
    
    dtype = device_data.type
    
    # Compute default asset ratio
    if device_data.asset_ratio:
        asset_ratio = device_data.asset_ratio
    elif dtype == "sensor":
        asset_ratio = "1:1"
    elif dtype == "rover":
        asset_ratio = "1:20"
    else:
        asset_ratio = "1:1"
    
    default_status = "active" if dtype == "sensor" else "idle"
    environment_data = dict(device_data.environment_data or {})
    if device_data.dimensions and dtype == "rover":
        environment_data["dimensions"] = device_data.dimensions
    if device_data.threshold_low is not None or device_data.threshold_high is not None:
        environment_data["thresholds"] = {
            "low": device_data.threshold_low,
            "high": device_data.threshold_high,
        }
    
    device = Device(
        device_id=device_id,
        device_type=dtype,
        subtype=device_data.subtype,
        zone_id=_tenant_zone_id(db, device_data.zone_id, current_user["tenant_id"]),
        name=device_data.subtype or device_id,
        asset_ratio=asset_ratio,
        
        # Position
        position_x=device_data.position.get("x", 0) if device_data.position else 0,
        position_y=device_data.position.get("y", 0) if device_data.position else 0,
        position_z=device_data.position.get("z", 0) if device_data.position else 0,
        
        # Status
        status=device_data.status or default_status,
        
        # Sensor readings
        last_reading=0,
        units=device_data.units or ("%" if dtype == "sensor" else ""),
        
        # Rover-specific
        battery_level=device_data.battery_level if dtype == "rover" else None,
        payload_capacity=device_data.payload_capacity if dtype == "rover" else "",
        max_speed_m_s=device_data.max_speed_m_s if dtype == "rover" else 0,
        
        # Environment
        environment_data=json.dumps(environment_data),
        
    )
    
    db.add(device)
    db.flush()
    _record_estate_audit(
        db, current_user, "estate_device_created", "estate_device", device.device_id,
        {"device_type": device.device_type, "subtype": device.subtype, "zone_id": device.zone_id,
         "position": device_data.position or {}, "status": device.status},
    )
    db.refresh(device)
    
    return {
        "status": "added",
        "device_id": device_id,
        "device": _device_response(device)
    }


@router.put("/devices/{device_id}", summary="Update device status and position")
def update_device(
    device_id: str,
    update_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("devices.manage")),
):
    """Update device status, position, reading, and battery in real-time."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(404, f"Device '{device_id}' not found")
    changed_fields = update_data.dict(exclude_unset=True)
    
    # Update position if provided
    pos = update_data.position
    if pos and isinstance(pos, dict):
        device.position_x = pos.get("x", device.position_x)
        device.position_y = pos.get("y", device.position_y)
        device.position_z = pos.get("z", device.position_z)
    
    # Update status
    status = update_data.status
    if status:
        device.status = status
    
    # Update last reading
    reading = update_data.last_reading
    if reading is not None:
        device.last_reading = float(reading)
    
    # Update units
    units = update_data.units
    if units:
        device.units = units
    
    # Rover-specific updates
    if device.device_type == "rover":
        battery = update_data.battery_level
        if battery is not None:
            device.battery_level = float(battery)
        
        payload = update_data.payload_capacity
        if payload:
            device.payload_capacity = str(payload)
        
        speed = update_data.max_speed_m_s
        if speed is not None:
            device.max_speed_m_s = float(speed)
        
    
    # Asset ratio
    ratio = update_data.asset_ratio
    if ratio:
        device.asset_ratio = ratio
    
    # Thresholds
    tl = update_data.threshold_low
    th = update_data.threshold_high
    # Environment
    env = update_data.environment_data
    dimensions = update_data.dimensions
    if (
        (env and isinstance(env, dict))
        or (dimensions and isinstance(dimensions, dict))
        or tl is not None
        or th is not None
    ):
        existing_environment = json.loads(device.environment_data) if device.environment_data else {}
        if env and isinstance(env, dict):
            existing_environment.update(env)
        if dimensions and isinstance(dimensions, dict):
            existing_environment["dimensions"] = dimensions
        thresholds = dict(existing_environment.get("thresholds") or {})
        if tl is not None:
            thresholds["low"] = float(tl)
        if th is not None:
            thresholds["high"] = float(th)
        if thresholds:
            existing_environment["thresholds"] = thresholds
        device.environment_data = json.dumps(existing_environment)
    
    _record_estate_audit(
        db, current_user, "estate_device_updated", "estate_device", device.device_id,
        {
            "changed_fields": list(changed_fields),
            "changes": {key: value for key, value in changed_fields.items() if key != "environment_data"},
            "environment_data_changed": "environment_data" in changed_fields,
        },
    )
    db.refresh(device)
    
    return {
        "status": "updated",
        "device_id": device_id,
        "device": _device_response(device)
    }

@router.delete("/devices/{device_id}", summary="Remove device from digital twin")
def remove_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("devices.manage")),
):
    """Remove a device from the digital twin and spatial graph."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(404, f"Device '{device_id}' not found")
    device_snapshot = _device_response(device)
    db.delete(device)
    _record_estate_audit(
        db, current_user, "estate_device_deleted", "estate_device", device_id,
        {"device": device_snapshot},
    )
    
    return {
        "status": "removed",
        "device_id": device_id
    }


@router.post("/zones", summary="Add or update a zone")
def add_zone(
    zone_data: ZoneCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("zones.manage")),
):
    """Add or update a zone with coordinates and asset ratio."""
    zone_id = zone_data.zone_id
    if not zone_id:
        raise HTTPException(400, "zone_id is required")
    
    try:
        lookup_id = int(zone_id)
    except (TypeError, ValueError):
        lookup_id = None

    existing = db.query(Zone).filter(
        Zone.id == lookup_id,
        Zone.tenant_id == current_user["tenant_id"],
    ).first() if lookup_id is not None else None
    if existing:
        zone = existing
    else:
        zone = Zone(name=zone_id, description="", location="", tenant_id=current_user["tenant_id"])
        db.add(zone)
    
    zone.name = zone_data.name or zone_id
    zone.coordinates = json.dumps(zone_data.coordinates) if zone_data.coordinates else "{}"
    zone.asset_ratio = zone_data.asset_ratio or "1:1"
    zone.position_ratio = zone_data.position_ratio or "50:50"
    zone.target_metrics = json.dumps(zone_data.target_metrics) if zone_data.target_metrics else "{}"
    
    db.flush()
    _record_estate_audit(
        db, current_user, "estate_zone_updated", "zone", zone.id,
        {"zone_id": zone_id, "name": zone.name, "coordinates": zone_data.coordinates or {},
         "asset_ratio": zone.asset_ratio},
    )
    db.refresh(zone)
    
    return {"status": "updated", "zone_id": zone_id}


@router.post("/ai/evaluate-reading", summary="Evaluate sensor reading against thresholds")
def evaluate_sensor_reading(
    sensor_type: str = Body(...),
    value: float = Body(...),
    zone_id: str = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Evaluate a sensor reading against zone thresholds.
    
    Returns events/dispatches if thresholds are crossed.
    """
    from backend.ai.orchestrator import evaluate_reading
    result = evaluate_reading(sensor_type, value, zone_id, db)
    return result


@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket, db_session: str = Query(...)):
    """WebSocket endpoint for real-time telemetry streaming.
    
    Clients can connect to receive live sensor and rover telemetry updates.
    """
    from backend.database import SessionLocal
    from backend.dependencies import get_db
    db = SessionLocal()
    try:
        await websocket.accept()
        while True:
            # Receive data from client (optional acknowledgment)
            data = await websocket.receive_json()
            # Could process acknowledgments here
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        db.close()
