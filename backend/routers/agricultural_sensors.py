"""
Aegis Backend - Agricultural Sensors Router
Handlers for specialized agricultural sensors and their time-series readings.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user, get_current_admin
from backend import schemas
from backend.models_db import AgriculturalSensor, AgriculturalSensorReading

router = APIRouter(prefix="/api/v1/agricultural", tags=["Agricultural Sensors"])


@router.post("/sensors", response_model=schemas.AgriculturalSensorResponse)
async def create_agricultural_sensor(
    sensor: schemas.AgriculturalSensorCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    if sensor.tenant_id != current_admin["tenant_id"]:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    db_sensor = AgriculturalSensor(**sensor.dict())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


@router.get("/sensors", response_model=List[schemas.AgriculturalSensorResponse])
async def list_agricultural_sensors(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    sensors = db.query(AgriculturalSensor).filter(
        AgriculturalSensor.tenant_id == current_user["tenant_id"]
    ).all()
    return sensors


@router.post("/sensors/{sensor_id}/readings", response_model=schemas.AgriculturalSensorReadingResponse)
async def add_agricultural_sensor_reading(
    sensor_id: int,
    reading: schemas.AgriculturalSensorReadingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    sensor = db.query(AgriculturalSensor).filter(AgriculturalSensor.id == sensor_id).first()
    if not sensor or sensor.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="Sensor not found or tenant mismatch")

    if reading.sensor_id != sensor_id:
        raise HTTPException(status_code=400, detail="Sensor ID mismatch")

    db_reading = AgriculturalSensorReading(**reading.dict())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading


@router.get("/sensors/{sensor_id}/readings", response_model=List[schemas.AgriculturalSensorReadingResponse])
async def get_agricultural_sensor_readings(
    sensor_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    sensor = db.query(AgriculturalSensor).filter(AgriculturalSensor.id == sensor_id).first()
    if not sensor or sensor.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="Sensor not found or tenant mismatch")

    readings = (
        db.query(AgriculturalSensorReading)
        .filter(AgriculturalSensorReading.sensor_id == sensor_id)
        .order_by(AgriculturalSensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )
    return readings
