"""Router for scene entity CRUD endpoints (Day 73 starter)."""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.database import SessionLocal
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/entities", response_model=List[SceneEntityOut])
def list_entities(db=Depends(get_db)):
    rows = db.query(models.SceneEntity).all()
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
async def create_entity(schema: SceneEntityIn, db=Depends(get_db)):
    # If an entity with this name exists, update it instead of creating duplicates
    existing = db.query(models.SceneEntity).filter(models.SceneEntity.name == schema.name).first()
    if existing:
        existing.type = schema.type
        existing.model = schema.model
        existing.x = schema.x
        existing.y = schema.y
        existing.z = schema.z
        existing.rotation = schema.rotation
        existing.state = schema.state or {}
        db.add(existing)
        db.commit()
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
        )
        db.add(ent)
        db.commit()
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
async def update_entity(entity_id: int, schema: SceneEntityIn, db=Depends(get_db)):
    ent = db.query(models.SceneEntity).filter(models.SceneEntity.id == entity_id).first()
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
    db.commit()
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
async def delete_entity(entity_id: int, db=Depends(get_db)):
    ent = db.query(models.SceneEntity).filter(models.SceneEntity.id == entity_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.delete(ent)
    db.commit()
    try:
        await scene_service.broadcast_entity_update({"id": entity_id, "deleted": True})
    except Exception:
        pass
    return {"deleted": True}
