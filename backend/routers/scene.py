"""Router for scene entity CRUD endpoints (Day 73 starter)."""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db, require_permission
from backend.audit_utils import record_actor_audit_event
from backend.blockchain_connector import get_blockchain_connector
from backend import models_scene as models
from backend.services import scene as scene_service

router = APIRouter(prefix="/api/v1/scene", tags=["scene"])


class SceneEntityIn(BaseModel):
    name: str
    type: str | None = None
    model: str | None = None
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rotation: float = 0.0
    state: dict | None = None


class SceneEntityOut(SceneEntityIn):
    id: int

def _record_scene_action(db: Session, actor, event_type: str, entity_id: int, details: dict):
    tenant_id = actor.tenant_id if hasattr(actor, "tenant_id") else actor["tenant_id"]
    return record_actor_audit_event(
        db, tenant_id, actor, event_type, "scene_entity", entity_id, details,
        blockchain=get_blockchain_connector(),
    )


@router.get("/entities", response_model=List[SceneEntityOut])
def list_entities(db=Depends(get_db), current_user=Depends(get_current_user)):
    tenant_id = current_user.tenant_id if hasattr(current_user, "tenant_id") else current_user["tenant_id"]
    rows = db.query(models.SceneEntity).filter(models.SceneEntity.tenant_id == tenant_id).all()
    return [
        SceneEntityOut(
            id=r.id,
            name=r.name,
            type=r.type,
            model=r.model,
            x=r.x,
            y=r.y,
            z=r.z,
            rotation=r.rotation,
            state=r.state or {},
        )
        for r in rows
    ]


@router.post("/entities", response_model=SceneEntityOut)
async def create_entity(
    schema: SceneEntityIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("devices.manage")),
):
    tenant_id = current_user.tenant_id if hasattr(current_user, "tenant_id") else current_user["tenant_id"]
    existing = db.query(models.SceneEntity).filter(
        models.SceneEntity.name == schema.name,
        models.SceneEntity.tenant_id == tenant_id,
    ).first()
    if existing:
        existing.type = schema.type
        existing.model = schema.model
        existing.x = schema.x
        existing.y = schema.y
        existing.z = schema.z
        existing.rotation = schema.rotation
        existing.state = schema.state or {}
        db.add(existing)
        db.flush()
        _record_scene_action(
            db, current_user, "scene_entity_updated", existing.id,
            {"name": existing.name, "type": existing.type, "model": existing.model,
             "position": {"x": existing.x, "y": existing.y, "z": existing.z},
             "rotation": existing.rotation, "state": existing.state or {}},
        )
        db.refresh(existing)
        ent = existing
    else:
        ent = models.SceneEntity(
            name=schema.name,
            type=schema.type,
            model=schema.model,
            x=schema.x,
            y=schema.y,
            z=schema.z,
            rotation=schema.rotation,
            state=schema.state or {},
            tenant_id=tenant_id,
        )
        db.add(ent)
        db.flush()
        _record_scene_action(
            db, current_user, "scene_entity_created", ent.id,
            {"name": ent.name, "type": ent.type, "model": ent.model,
             "position": {"x": ent.x, "y": ent.y, "z": ent.z},
             "rotation": ent.rotation, "state": ent.state or {}},
        )
        db.refresh(ent)
    # Broadcast to realtime clients (best-effort)
    try:
        await scene_service.broadcast_entity_update({
            "id": ent.id,
            "name": ent.name,
            "type": ent.type,
            "model": ent.model,
            "x": ent.x,
            "y": ent.y,
            "z": ent.z,
            "rotation": ent.rotation,
            "state": ent.state or {},
        })
    except Exception:
        pass
    return SceneEntityOut(
        id=ent.id,
        name=ent.name,
        type=ent.type,
        model=ent.model,
        x=ent.x,
        y=ent.y,
        z=ent.z,
        rotation=ent.rotation,
        state=ent.state or {},
    )


@router.put("/entities/{entity_id}", response_model=SceneEntityOut)
async def update_entity(
    entity_id: int,
    schema: SceneEntityIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("devices.manage")),
):
    tenant_id = current_user.tenant_id if hasattr(current_user, "tenant_id") else current_user["tenant_id"]
    ent = db.query(models.SceneEntity).filter(
        models.SceneEntity.id == entity_id, models.SceneEntity.tenant_id == tenant_id
    ).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
    ent.name = schema.name
    ent.type = schema.type
    ent.model = schema.model
    ent.x = schema.x
    ent.y = schema.y
    ent.z = schema.z
    ent.rotation = schema.rotation
    ent.state = schema.state or {}
    db.add(ent)
    db.flush()
    _record_scene_action(
        db, current_user, "scene_entity_updated", ent.id,
        {"name": ent.name, "type": ent.type, "model": ent.model,
         "position": {"x": ent.x, "y": ent.y, "z": ent.z},
         "rotation": ent.rotation, "state": ent.state or {}},
    )
    db.refresh(ent)
    try:
        await scene_service.broadcast_entity_update({
            "id": ent.id,
            "name": ent.name,
            "type": ent.type,
            "model": ent.model,
            "x": ent.x,
            "y": ent.y,
            "z": ent.z,
            "rotation": ent.rotation,
            "state": ent.state or {},
        })
    except Exception:
        pass
    return SceneEntityOut(
        id=ent.id,
        name=ent.name,
        type=ent.type,
        model=ent.model,
        x=ent.x,
        y=ent.y,
        z=ent.z,
        rotation=ent.rotation,
        state=ent.state or {},
    )


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("devices.manage")),
):
    tenant_id = current_user.tenant_id if hasattr(current_user, "tenant_id") else current_user["tenant_id"]
    ent = db.query(models.SceneEntity).filter(
        models.SceneEntity.id == entity_id, models.SceneEntity.tenant_id == tenant_id
    ).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
    details = {
        "name": ent.name, "type": ent.type, "model": ent.model,
        "position": {"x": ent.x, "y": ent.y, "z": ent.z},
    }
    db.delete(ent)
    _record_scene_action(db, current_user, "scene_entity_deleted", entity_id, details)
    try:
        await scene_service.broadcast_entity_update({"id": entity_id, "deleted": True})
    except Exception:
        pass
    return {"deleted": True}
