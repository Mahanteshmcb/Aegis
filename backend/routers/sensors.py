"""
Aegis Backend - Sensors Router
Sensor data ingestion and retrieval.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.dependencies import get_db

router = APIRouter(prefix="/api/v1", tags=["sensors"])


class SensorDataIngest(BaseModel):
    """Sensor data ingestion payload."""
    sensor_id: str
    value: float
    unit: str = ""
    timestamp: str = ""


class SensorDataResponse(BaseModel):
    """Sensor data response."""
    sensor_id: str
    value: float
    unit: str
    timestamp: str
    zone_id: str


@router.post("/sensors/data")
async def ingest_sensor_data(data: SensorDataIngest, db=Depends(get_db)):
    """Ingest sensor data. Implemented in Day 9."""
    return {"message": "Sensor data ingestion not yet implemented"}


@router.get("/sensors/{sensor_id}/data")
async def get_sensor_data(sensor_id: str, db=Depends(get_db)):
    """Get latest sensor data. Implemented in Day 9."""
    return {"data": []}


@router.get("/sensors")
async def list_sensors(db=Depends(get_db)):
    """List all sensors. Implemented in Day 9."""
    return {"sensors": []}
