from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


class TenantBase(BaseModel):
    name: str
    settings: Optional[Dict[str, Any]] = {}


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class Tenant(TenantBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class SensorBase(BaseModel):
    type: Optional[str] = None
    location: Optional[str] = None


class SensorCreate(SensorBase):
    tenant_id: int


class SensorUpdate(SensorBase):
    last_reading: Optional[Any] = None


class Sensor(SensorBase):
    id: int
    tenant_id: int
    last_reading: Optional[Any] = None
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class AuditLogBase(BaseModel):
    tenant_id: Optional[int] = None
    sensor_id: Optional[int] = None
    event_type: str
    data_hash: str
    blockchain_tx: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class AgriculturalSensorBase(BaseModel):
    tenant_id: int
    zone_id: Optional[int] = None
    sensor_type: str
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    location_z: Optional[float] = None
    measurement_unit: Optional[str] = None
    min_range: Optional[float] = None
    max_range: Optional[float] = None
    accuracy: Optional[float] = None
    sampling_rate_hz: Optional[float] = None
    is_active: Optional[bool] = True
    last_calibration: Optional[datetime] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    notes: Optional[str] = None


class AgriculturalSensorCreate(AgriculturalSensorBase):
    pass


class AgriculturalSensorResponse(AgriculturalSensorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class AgriculturalSensorReadingBase(BaseModel):
    sensor_id: int
    timestamp: datetime
    value: float
    unit: Optional[str] = None
    confidence: Optional[float] = None
    is_anomaly: Optional[bool] = False
    notes: Optional[str] = None


class AgriculturalSensorReadingCreate(AgriculturalSensorReadingBase):
    pass


class AgriculturalSensorReadingResponse(AgriculturalSensorReadingBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class CropLifecycleEventBase(BaseModel):
    event_type: str
    event_date: datetime
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    action_date: Optional[datetime] = None
    blockchain_tx: Optional[str] = None


class CropLifecycleEventCreate(CropLifecycleEventBase):
    pass


class CropLifecycleEventResponse(CropLifecycleEventBase):
    id: int
    crop_instance_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class BiologicalMetricBase(BaseModel):
    measurement_date: datetime
    health_score: Optional[float] = None
    health_status: Optional[str] = None
    ndvi: Optional[float] = None
    chlorophyll_content: Optional[float] = None
    canopy_coverage_percent: Optional[float] = None
    leaf_area_index: Optional[float] = None
    nitrogen_level: Optional[float] = None
    phosphorus_level: Optional[float] = None
    potassium_level: Optional[float] = None
    soil_health_status: Optional[str] = None
    pest_detected: Optional[bool] = False
    pest_types: Optional[List[str]] = None
    pest_severity: Optional[str] = None
    disease_detected: Optional[bool] = False
    disease_types: Optional[List[str]] = None
    disease_severity: Optional[str] = None
    height_cm: Optional[float] = None
    stem_diameter_cm: Optional[float] = None
    leaf_count: Optional[int] = None
    flower_count: Optional[int] = None
    fruit_count: Optional[int] = None
    temperature_avg_c: Optional[float] = None
    humidity_avg_percent: Optional[float] = None
    soil_moisture_percent: Optional[float] = None
    light_hours: Optional[float] = None
    recommendations: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    confidence_score: Optional[float] = None


class BiologicalMetricCreate(BiologicalMetricBase):
    pass


class BiologicalMetricResponse(BiologicalMetricBase):
    id: int
    crop_instance_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class CropInstanceBase(BaseModel):
    species_id: int
    spatial_zone_id: int
    position_x: float
    position_y: float
    position_z: float
    vertical_layer: str
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    actual_harvest_date: Optional[datetime] = None
    planting_soil_ph: Optional[float] = None
    planting_soil_moisture: Optional[float] = None
    planting_temperature_c: Optional[float] = None
    batch_id: Optional[str] = None
    notes: Optional[str] = None
    current_height_cm: Optional[float] = None
    health_status: Optional[str] = None
    growth_stage: Optional[str] = None
    last_watered: Optional[datetime] = None
    last_fertilized: Optional[datetime] = None
    last_pruned: Optional[datetime] = None
    pest_incidents: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = True
    harvest_yield_kg: Optional[float] = None


class CropInstanceCreate(CropInstanceBase):
    pass


class CropInstanceUpdate(BaseModel):
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    vertical_layer: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    actual_harvest_date: Optional[datetime] = None
    planting_soil_ph: Optional[float] = None
    planting_soil_moisture: Optional[float] = None
    planting_temperature_c: Optional[float] = None
    batch_id: Optional[str] = None
    notes: Optional[str] = None
    current_height_cm: Optional[float] = None
    health_status: Optional[str] = None
    growth_stage: Optional[str] = None
    last_watered: Optional[datetime] = None
    last_fertilized: Optional[datetime] = None
    last_pruned: Optional[datetime] = None
    pest_incidents: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    harvest_yield_kg: Optional[float] = None


class CropInstanceResponse(CropInstanceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


# --- User schemas for authentication and RBAC ---
class UserBase(BaseModel):
    email: EmailStr
    role: str = "viewer"

class UserCreate(UserBase):
    password: str
    tenant_id: int

class UserRead(UserBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
        from_attributes = True

class UserProfile(UserBase):
    id: int
    tenant_id: int

    class Config:
        orm_mode = True

class UserInDB(UserRead):
    hashed_password: str
