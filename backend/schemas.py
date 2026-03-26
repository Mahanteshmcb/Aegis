from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


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

class UserInDB(UserRead):
    hashed_password: str
