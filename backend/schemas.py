from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TenantBase(BaseModel):
    name: str


class TenantCreate(TenantBase):
    pass


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
    last_reading: Optional[Dict[str, Any]] = None


class Sensor(SensorBase):
    id: int
    tenant_id: int
    last_reading: Optional[Dict[str, Any]]
    updated_at: datetime

    class Config:
        orm_mode = True


class AuditLogBase(BaseModel):
    sensor_id: int
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
