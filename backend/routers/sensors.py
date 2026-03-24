"""
Aegis Backend - Sensors Router
Sensor data ingestion and retrieval.
"""




from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

"""
Aegis Backend - Sensors Router
Sensor data ingestion and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user
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
    sensor_id: int
    value: float | None = None
    unit: str | None = None
    timestamp: str | None = None
    zone_id: int | None = None

@router.post("/sensors", response_model=schemas.Sensor)
async def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    import hashlib
    if sensor.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    db_sensor = crud.create_sensor(db, sensor)
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
        crud.create_audit_log(db, audit)
    except Exception:
        pass  # Do not block sensor creation if audit log fails
    return db_sensor

@router.post("/sensors/data", response_model=SensorDataResponse)
async def ingest_sensor_data(data: SensorDataIngest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == data.sensor_id).first()
    if not sensor or sensor.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Tenant mismatch or sensor not found")
    # Assign last_reading as a dict (JSON column)
    # SQLAlchemy JSON column assignment (should accept dict)
    setattr(sensor, "last_reading", dict(
        value=float(data.value),
        unit=str(data.unit),
        timestamp=str(data.timestamp),
    ))
    db.commit()
    db.refresh(sensor)
    sid = getattr(sensor, "id", None)
    return SensorDataResponse(
        sensor_id=int(sid) if sid is not None else 0,
        value=float(data.value),
        unit=str(data.unit),
        timestamp=str(data.timestamp),
        zone_id=None,
    )

@router.get("/sensors/{sensor_id}/data", response_model=SensorDataResponse)
async def get_sensor_data(sensor_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor or sensor.tenant_id != current_user["tenant_id"] or sensor.last_reading is None:
        raise HTTPException(status_code=404, detail="Sensor data not found or tenant mismatch")
    sid = getattr(sensor, "id", None)
    last_reading = getattr(sensor, "last_reading", None)
    return SensorDataResponse(
        sensor_id=int(sid) if sid is not None else 0,
        value=last_reading.get("value") if last_reading is not None else None,
        unit=last_reading.get("unit") if last_reading is not None else None,
        timestamp=last_reading.get("timestamp") if last_reading is not None else None,
        zone_id=None,
    )

@router.get("/sensors", response_model=list[SensorDataResponse])
async def list_sensors(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sensors = db.query(models.Sensor).filter(models.Sensor.tenant_id == current_user["tenant_id"]).all()
    result = []
    for s in sensors:
        sid = getattr(s, "id", None)
        last_reading = getattr(s, "last_reading", None)
        result.append(SensorDataResponse(
            sensor_id=int(sid) if sid is not None else 0,
            value=last_reading.get("value") if last_reading is not None else None,
            unit=last_reading.get("unit") if last_reading is not None else None,
            timestamp=last_reading.get("timestamp") if last_reading is not None else None,
            zone_id=None,
        ))
    return result



















