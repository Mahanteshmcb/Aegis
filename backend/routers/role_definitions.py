"""Tenant-scoped custom role and permission definitions."""
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.dependencies import (
    BUILTIN_ROLE_PERMISSIONS,
    CUSTOM_ROLE_PERMISSIONS,
    get_current_admin,
    get_db,
)
from backend.audit_utils import record_actor_audit_event
from backend.blockchain_connector import get_blockchain_connector
from backend.models_db import RoleDefinition, User

router = APIRouter(prefix="/api/v1/roles", tags=["roles"])


class RoleDefinitionInput(BaseModel):
    key: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str]

    def validate_custom_permissions(self):
        if not re.fullmatch(r"[a-z][a-z0-9_-]{1,49}", self.key):
            raise HTTPException(status_code=422, detail="Role key must be a lowercase identifier")
        if self.key in BUILTIN_ROLE_PERMISSIONS:
            raise HTTPException(status_code=409, detail="Role key is reserved")
        unknown = sorted(set(self.permissions) - CUSTOM_ROLE_PERMISSIONS)
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unsupported permissions: {', '.join(unknown)}")


class RoleDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    description: str | None
    permissions: list[str]
    created_at: datetime
    updated_at: datetime


def _role_data(role):
    return {
        "id": role.id,
        "key": role.key,
        "name": role.name,
        "description": role.description,
        "permissions": role.permissions or [],
        "created_at": role.created_at,
        "updated_at": role.updated_at,
    }


def _record_role_action(db, actor, event_type, role, details=None):
    return record_actor_audit_event(
        db,
        actor["tenant_id"],
        actor,
        event_type,
        "role_definition",
        role.id,
        {"role_key": role.key, "role_name": role.name, **(details or {})},
        blockchain=get_blockchain_connector(),
    )


@router.get("")
def list_roles(current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    builtins = [
        {"id": None, "key": key, "name": key.replace("_", " ").title(), "description": "Built-in role", "permissions": sorted(permissions), "built_in": True}
        for key, permissions in BUILTIN_ROLE_PERMISSIONS.items()
        if key != "superadmin" or current_admin.get("role") == "superadmin"
    ]
    custom = db.query(RoleDefinition).filter(
        RoleDefinition.tenant_id == current_admin["tenant_id"]
    ).order_by(RoleDefinition.name).all()
    return {"data": builtins + [{**_role_data(role), "built_in": False} for role in custom]}


@router.post("", response_model=RoleDefinitionResponse, status_code=201)
def create_role(payload: RoleDefinitionInput, current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    payload.validate_custom_permissions()
    role = RoleDefinition(
        tenant_id=current_admin["tenant_id"],
        key=payload.key,
        name=payload.name.strip(),
        description=payload.description,
        permissions=sorted(set(payload.permissions)),
    )
    if not role.name:
        raise HTTPException(status_code=422, detail="Role name cannot be blank")
    if db.query(RoleDefinition.id).filter_by(tenant_id=role.tenant_id, key=role.key).first():
        raise HTTPException(status_code=409, detail="Role key already exists")
    db.add(role)
    db.flush()
    _record_role_action(
        db,
        current_admin,
        "role_created",
        role,
        {"permissions": role.permissions},
    )
    db.refresh(role)
    return _role_data(role)


@router.put("/{role_id}", response_model=RoleDefinitionResponse)
def update_role(role_id: int, payload: RoleDefinitionInput, current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    payload.validate_custom_permissions()
    role = db.query(RoleDefinition).filter_by(
        id=role_id, tenant_id=current_admin["tenant_id"]
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    duplicate = db.query(RoleDefinition.id).filter(
        RoleDefinition.tenant_id == current_admin["tenant_id"],
        RoleDefinition.key == payload.key,
        RoleDefinition.id != role_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Role key already exists")
    old_key = role.key
    role.key = payload.key
    role.name = payload.name.strip()
    if not role.name:
        raise HTTPException(status_code=422, detail="Role name cannot be blank")
    role.description = payload.description
    role.permissions = sorted(set(payload.permissions))
    if old_key != payload.key:
        db.query(User).filter(
            User.tenant_id == current_admin["tenant_id"],
            User.role == old_key,
        ).update({User.role: payload.key}, synchronize_session=False)
    _record_role_action(
        db,
        current_admin,
        "role_updated",
        role,
        {
            "previous_key": old_key,
            "permissions": role.permissions,
            "assigned_users_updated": old_key != payload.key,
        },
    )
    db.refresh(role)
    return _role_data(role)


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: int, current_admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    role = db.query(RoleDefinition).filter_by(
        id=role_id, tenant_id=current_admin["tenant_id"]
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    assigned = db.query(User.id).filter(
        User.tenant_id == current_admin["tenant_id"],
        User.role == role.key,
    ).first()
    if assigned:
        raise HTTPException(status_code=409, detail="Reassign users before deleting this role")
    role_snapshot = {"role_key": role.key, "role_name": role.name, "permissions": role.permissions or []}
    db.delete(role)
    record_actor_audit_event(
        db,
        current_admin["tenant_id"],
        current_admin,
        "role_deleted",
        "role_definition",
        role_id,
        role_snapshot,
        blockchain=get_blockchain_connector(),
    )
