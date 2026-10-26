"""
Aegis Backend - Sensors Router
Sensor data ingestion and retrieval.
"""




from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user, get_current_admin
from backend import models_db as models
from backend import schemas
from backend import crud
from backend.database import Zone
from backend.models.digital_twin import DigitalTwinDevice
from backend import realtime
from backend.services import digital_twin

router = APIRouter(prefix="/api/v1", tags=["sensors"])


def _record_sensor_audit(db: Session, current_user, event_type: str, sensor, details: dict | None = None):
    from backend.audit_utils import record_audit_event
    from backend.blockchain_connector import get_blockchain_connector

    metadata = {
        **(details or {}),
        "action": event_type,
        "actor_user_id": current_user["id"],
        "actor_email": current_user["email"],
        "entity_type": "sensor",
        "entity_id": str(sensor.id),
        "sensor_id": sensor.id,
        "sensor_name": sensor.name,
        "sensor_type": sensor.type,
        "zone_id": sensor.zone_id,
        "outcome": "success",
    }
    record_audit_event(db, get_blockchain_connector(), current_user["tenant_id"], event_type, metadata)


def _digital_twin_sensor_type(sensor_type: str | None) -> str:
    normalized = str(sensor_type or "sensor").strip().lower().replace(" ", "_")
    normalized = normalized.replace("sensor_", "", 1)
    for supported in digital_twin.SENSOR_PROFILES:
        if supported in normalized:
            return supported
    return normalized


def _ensure_twin_sensor(db: Session, sensor: models.Sensor) -> DigitalTwinDevice:
    legacy_device_id = f"legacy-sensor-{sensor.id}"
    device = db.query(DigitalTwinDevice).filter(
        DigitalTwinDevice.tenant_id == sensor.tenant_id,
        DigitalTwinDevice.device_id == legacy_device_id,
        DigitalTwinDevice.kind == "sensor",
    ).first()
    if device is None and sensor.name:
        candidate = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.tenant_id == sensor.tenant_id,
            DigitalTwinDevice.device_id == sensor.name,
            DigitalTwinDevice.kind == "sensor",
        ).first()
        if candidate and (candidate.state or {}).get("legacy_sensor_id") in (None, sensor.id):
            device = candidate

    zone = None
    if sensor.zone_id is not None:
        zone = db.query(Zone).filter(
            Zone.id == sensor.zone_id,
            Zone.tenant_id == sensor.tenant_id,
        ).first()
        if zone is None:
            raise HTTPException(status_code=409, detail="Sensor zone is missing or outside its tenant")

    device_type = _digital_twin_sensor_type(sensor.type)
    if device is None:
        device_id = legacy_device_id
        collision = db.query(DigitalTwinDevice.id).filter(
            DigitalTwinDevice.tenant_id == sensor.tenant_id,
            DigitalTwinDevice.device_id == device_id,
        ).first()
        if collision:
            device_id = f"legacy-sensor-{sensor.id}-{sensor.tenant_id}"
        position = dict(zone.spatial_position or {}) if zone else {}
        if not all(axis in position for axis in ("x", "y", "z")):
            position = {"x": 0.0, "y": 0.0, "z": 0.0}
        device = DigitalTwinDevice(
            tenant_id=sensor.tenant_id,
            zone_id=sensor.zone_id,
            device_id=device_id,
            name=sensor.name or device_id,
            kind="sensor",
            device_type=device_type,
            status="online" if sensor.last_reading else "offline",
            position=position,
            state={"legacy_sensor_id": sensor.id},
            simulation_enabled=False,
            control_mode="manual",
        )
        db.add(device)
        db.flush()
    else:
        device.name = sensor.name or device.name
        device.device_type = device_type
        device.zone_id = sensor.zone_id
        state = dict(device.state or {})
        state["legacy_sensor_id"] = sensor.id
        device.state = state
        device.simulation_enabled = False
    return device


def _parse_telemetry_time(timestamp: str | None) -> datetime:
    if timestamp:
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            try:
                return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
    return datetime.utcnow()


class SensorDataIngest(BaseModel):
    """Sensor data ingestion payload."""
    sensor_id: int
    value: float
    unit: str = ""
    timestamp: str = ""

class SensorDataResponse(BaseModel):
    """Sensor data response."""
    id: int
    sensor_id: int
    tenant_id: int | None = None
    zone_id: int | None = None
    name: str | None = None
    type: str | None = None
    location: str | None = None
    value: float | None = None
    unit: str | None = None
    timestamp: str | None = None
    status: str = 'offline'

@router.post("/sensors", response_model=schemas.Sensor)
async def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    if sensor.zone_id is not None and not db.query(Zone.id).filter(
        Zone.id == sensor.zone_id,
        Zone.tenant_id == tenant_id,
    ).first():
        raise HTTPException(status_code=404, detail="Zone not found")
    db_sensor = crud.create_sensor(db, sensor, tenant_id=tenant_id)
    _ensure_twin_sensor(db, db_sensor)
    db.commit()
    _record_sensor_audit(db, current_user, "sensor_created", db_sensor, {"location": db_sensor.location})
    return db_sensor

@router.post("/sensors/data", response_model=SensorDataResponse)
async def ingest_sensor_data(data: SensorDataIngest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == data.sensor_id).first()
    if not sensor or sensor.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Tenant mismatch or sensor not found")
    
    sensor.last_reading = {
        "value": float(data.value),
        "unit": str(data.unit),
        "timestamp": str(data.timestamp),
    }
    
    # Crucial for SQLAlchemy to detect changes in JSON columns
    flag_modified(sensor, "last_reading")
    
    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    telemetry_time = _parse_telemetry_time(data.timestamp)

    db.add(models.SensorData(
        sensor_id=sensor.id,
        timestamp=telemetry_time,
        value=str(data.value),
        unit=str(data.unit),
    ))
    db.commit()

    twin_sensor = _ensure_twin_sensor(db, sensor)
    snapshots = digital_twin.ingest_sensor_sample(
        db,
        twin_sensor,
        data.value,
        data.unit,
        telemetry_time,
    )
    for snapshot in snapshots:
        await realtime.emit_tenant_event(
            "digital_twin:device_update",
            snapshot,
            sensor.tenant_id,
        )
        if snapshot.get("alert"):
            await realtime.emit_tenant_event("digital_twin:alert", snapshot["alert"], sensor.tenant_id)
        if snapshot.get("alert_cleared"):
            await realtime.emit_tenant_event("digital_twin:alert_cleared", snapshot["alert_cleared"], sensor.tenant_id)

    # If this is an environmental or weather-oriented sensor, create a weather observation
    sensor_type = (sensor.type or "").lower()
    if any(key in sensor_type for key in ("temp", "temperature", "weather", "env", "humidity")):
        obs_time = telemetry_time

        weather_kwargs = {
            "tenant_id": sensor.tenant_id,
            "zone_id": sensor.zone_id,
            "sensor_id": sensor.id,
            "timestamp": obs_time,
            "temp_c": None,
            "humidity_percent": None,
            "wind_m_s": None,
            "precip_mm": None,
            "pressure_hpa": None,
        }

        if "temp" in sensor_type or data.unit.lower() in ("c", "°c", "degc", "celsius"):
            weather_kwargs["temp_c"] = float(data.value)
        elif "humidity" in sensor_type or data.unit.lower() in ("%", "percent", "humidity"):
            weather_kwargs["humidity_percent"] = float(data.value)

        db.add(models.WeatherObservation(**weather_kwargs))
        db.commit()

    return SensorDataResponse(
        id=sensor.id,
        sensor_id=sensor.id,
        tenant_id=sensor.tenant_id,
        zone_id=sensor.zone_id,
        name=sensor.name,
        type=sensor.type,
        location=sensor.location,
        value=sensor.last_reading["value"],
        unit=sensor.last_reading["unit"],
        timestamp=sensor.last_reading["timestamp"],
        status='online' if sensor.last_reading else 'offline',
    )

@router.get("/sensors/{sensor_id}/data", response_model=SensorDataResponse)
async def get_sensor_data(sensor_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor or sensor.tenant_id != current_user["tenant_id"] or sensor.last_reading is None:
        raise HTTPException(status_code=404, detail="Sensor data not found or tenant mismatch")
    sid = getattr(sensor, "id", None)
    last_reading = getattr(sensor, "last_reading", None)
    return SensorDataResponse(
        id=int(sid) if sid is not None else 0,
        sensor_id=int(sid) if sid is not None else 0,
        tenant_id=sensor.tenant_id,
        zone_id=sensor.zone_id,
        name=sensor.name,
        type=sensor.type,
        location=sensor.location,
        value=last_reading.get("value") if last_reading is not None else None,
        unit=last_reading.get("unit") if last_reading is not None else None,
        timestamp=last_reading.get("timestamp") if last_reading is not None else None,
        status='online' if last_reading else 'offline',
    )

@router.get("/sensors", response_model=list[SensorDataResponse])
async def list_sensors(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sensors = db.query(models.Sensor).filter(models.Sensor.tenant_id == current_user["tenant_id"]).all()
    result = []
    for s in sensors:
        sid = getattr(s, "id", None)
        last_reading = getattr(s, "last_reading", None)
        result.append(SensorDataResponse(
            id=int(sid) if sid is not None else 0,
            sensor_id=int(sid) if sid is not None else 0,
            tenant_id=s.tenant_id,
            zone_id=s.zone_id,
            name=s.name,
            type=s.type,
            location=s.location,
            value=last_reading.get("value") if last_reading is not None else None,
            unit=last_reading.get("unit") if last_reading is not None else None,
            timestamp=last_reading.get("timestamp") if last_reading is not None else None,
            status='online' if last_reading else 'offline',
        ))
    return result


@router.put("/sensors/{sensor_id}", response_model=schemas.Sensor)
async def update_sensor(sensor_id: int, update: schemas.SensorUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Update sensor metadata or last reading (tenant protected)."""
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor or sensor.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="Sensor not found or tenant mismatch")

    update_data = update.dict(exclude_unset=True)
    if update_data.get("zone_id") is not None and not db.query(Zone.id).filter(
        Zone.id == update_data["zone_id"],
        Zone.tenant_id == sensor.tenant_id,
    ).first():
        raise HTTPException(status_code=404, detail="Zone not found")
    # allow last_reading and other fields to be set via update
    if "last_reading" in update_data:
        sensor.last_reading = update_data.get("last_reading")
    if "name" in update_data:
        sensor.name = update_data.get("name")
    if "type" in update_data:
        sensor.type = update_data.get("type")
    if "location" in update_data:
        sensor.location = update_data.get("location")
    if "zone_id" in update_data:
        sensor.zone_id = update_data.get("zone_id")

    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    twin_sensor = _ensure_twin_sensor(db, sensor)
    twin_sensor.name = sensor.name or twin_sensor.name
    twin_sensor.device_type = _digital_twin_sensor_type(sensor.type)
    twin_sensor.zone_id = sensor.zone_id
    if sensor.last_reading and sensor.last_reading.get("value") is not None:
        digital_twin.ingest_sensor_sample(
            db,
            twin_sensor,
            float(sensor.last_reading["value"]),
            str(sensor.last_reading.get("unit") or ""),
            _parse_telemetry_time(sensor.last_reading.get("timestamp")),
        )
    else:
        db.commit()
    db.refresh(sensor)
    _record_sensor_audit(db, current_user, "sensor_updated", sensor, {"changed_fields": list(update_data.keys()), "changes": update_data})
    return sensor


@router.delete("/sensors/{sensor_id}")
async def delete_sensor(sensor_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    """Delete a sensor (admin only)."""
    tenant_id = current_admin.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current admin")

    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id, models.Sensor.tenant_id == tenant_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found or tenant mismatch")

    twin_sensor = _ensure_twin_sensor(db, sensor)
    sensor_snapshot = {
        "sensor_name": sensor.name,
        "sensor_type": sensor.type,
        "zone_id": sensor.zone_id,
    }
    db.delete(twin_sensor)
    db.delete(sensor)
    _record_sensor_audit(
        db,
        current_admin,
        "sensor_deleted",
        sensor,
        sensor_snapshot,
    )
    return {"detail": "Sensor deleted"}















