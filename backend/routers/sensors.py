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

router = APIRouter(prefix="/api/v1", tags=["sensors"])

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
    import hashlib
    tenant_id = current_user.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    db_sensor = crud.create_sensor(db, sensor, tenant_id=tenant_id)
    # Audit log for sensor creation
    sensor_data = f"type={db_sensor.type}|tenant_id={db_sensor.tenant_id}|location={db_sensor.location}"
    data_hash = hashlib.sha256(sensor_data.encode()).hexdigest()
    audit = schemas.AuditLogCreate(
        sensor_id=db_sensor.id,
        event_type="sensor_created",
        data_hash=data_hash,
        blockchain_tx=None,
    )
    try:
        crud.create_audit_log(db, audit, tenant_id=current_user["tenant_id"])
    except Exception:
        pass  # Do not block sensor creation if audit log fails
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

    # Persist raw telemetry for history and energy analysis
    telemetry_time = datetime.utcnow()
    if data.timestamp:
        try:
            telemetry_time = datetime.fromisoformat(data.timestamp)
        except ValueError:
            try:
                telemetry_time = datetime.strptime(data.timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                telemetry_time = datetime.utcnow()

    db.add(models.SensorData(
        sensor_id=sensor.id,
        timestamp=telemetry_time,
        value=str(data.value),
        unit=str(data.unit),
    ))
    db.commit()

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

    db.delete(sensor)
    db.commit()
    return {"detail": "Sensor deleted"}



















