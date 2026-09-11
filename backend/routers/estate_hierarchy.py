"""Customer estate hierarchy APIs used by the 3D editor."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.dependencies import get_current_user, get_db
from backend.models.estate_hierarchy import Estate, EstateNode

router = APIRouter(prefix="/api/v1/estate-layout", tags=["estate-layout"])
NODE_TYPES = {"zone", "building", "room", "section"}
THREE_ACRE_LAYOUT = {
    "width_m": 135.0,
    "depth_m": 90.0,
    "area_m2": 12150.0,
    "area_acres": 3.0023,
    "origin": "southwest_corner",
}

THREE_ACRE_TEMPLATE = [
    ("zone", "Vegetable Garden", None, {"x": -35, "y": 0, "z": -30}, {"x": 40, "y": 0.3, "z": 25}),
    ("zone", "Fruit Orchard", None, {"x": 15, "y": 0, "z": -30}, {"x": 50, "y": 0.3, "z": 20}),
    ("zone", "Research and Workshop", None, {"x": -35, "y": 0, "z": 5}, {"x": 58, "y": 8, "z": 25}),
    ("zone", "Grains and Rice", None, {"x": 28, "y": 0, "z": 5}, {"x": 42, "y": 0.3, "z": 35}),
    ("zone", "Residential Estate", None, {"x": 25, "y": 0, "z": 30}, {"x": 45, "y": 5, "z": 18}),
]


class EstateCreate(BaseModel):
    name: str
    description: str | None = None
    layout: Dict[str, Any] = {}


class NodeCreate(BaseModel):
    node_type: str
    name: str
    parent_id: int | None = None
    description: str | None = None
    position: Dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
    dimensions: Dict[str, float] = {"x": 10.0, "y": 3.0, "z": 10.0}
    metadata: Dict[str, Any] = {}


def tenant_id_for(user) -> int:
    return int(user.tenant_id if hasattr(user, "tenant_id") else user["tenant_id"])


def estate_dict(estate: Estate) -> dict:
    return {"id": estate.id, "tenant_id": estate.tenant_id, "name": estate.name, "description": estate.description, "layout": estate.layout or {}}


def node_dict(node: EstateNode) -> dict:
    return {
        "id": node.id, "estate_id": node.estate_id, "parent_id": node.parent_id,
        "node_type": node.node_type, "name": node.name, "description": node.description,
        "position": node.position or {}, "dimensions": node.dimensions or {}, "metadata": node.node_metadata or {},
    }


@router.get("")
def list_estates(current_user=Depends(get_current_user), db=Depends(get_db)) -> List[dict]:
    return [estate_dict(row) for row in db.query(Estate).filter(Estate.tenant_id == tenant_id_for(current_user)).all()]


@router.post("")
def create_estate(schema: EstateCreate, current_user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    estate = Estate(tenant_id=tenant_id_for(current_user), **schema.dict())
    db.add(estate)
    db.commit()
    db.refresh(estate)
    return estate_dict(estate)


@router.post("/template/three-acre")
def create_three_acre_template(current_user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    """Create the measured demonstration estate once for the current tenant."""
    tenant_id = tenant_id_for(current_user)
    existing = db.query(Estate).filter(Estate.tenant_id == tenant_id).first()
    if existing:
        return get_estate_tree(existing.id, current_user, db)

    estate = Estate(
        tenant_id=tenant_id,
        name="Aegis 3-Acre Innovation Estate",
        description="135 m x 90 m software-first estate digital twin",
        layout=THREE_ACRE_LAYOUT,
    )
    db.add(estate)
    db.flush()
    nodes = []
    for node_type, name, parent_id, position, dimensions in THREE_ACRE_TEMPLATE:
        node = EstateNode(
            estate_id=estate.id, node_type=node_type, name=name,
            parent_id=parent_id, position=position, dimensions=dimensions,
        )
        db.add(node)
        db.flush()
        nodes.append(node)

    research_zone = nodes[2]
    building = EstateNode(
        estate_id=estate.id, parent_id=research_zone.id, node_type="building",
        name="R&D Laboratory and Workshop", position={"x": -35, "y": 4, "z": 5},
        dimensions={"x": 33, "y": 8, "z": 21},
    )
    db.add(building)
    db.flush()
    for name, position, dimensions in [
        ("Software Development Lab", {"x": -43, "y": 4, "z": 7}, {"x": 14, "y": 4, "z": 10}),
        ("Additive Manufacturing Room", {"x": -28, "y": 4, "z": 7}, {"x": 14, "y": 4, "z": 10}),
        ("Server and Control Room", {"x": -35, "y": 4, "z": 15}, {"x": 25, "y": 4, "z": 6}),
    ]:
        db.add(EstateNode(
            estate_id=estate.id, parent_id=building.id, node_type="room",
            name=name, position=position, dimensions=dimensions,
        ))
    db.commit()
    return get_estate_tree(estate.id, current_user, db)


@router.get("/{estate_id}/tree")
def get_estate_tree(estate_id: int, current_user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    estate = db.query(Estate).filter(Estate.id == estate_id, Estate.tenant_id == tenant_id_for(current_user)).first()
    if not estate:
        raise HTTPException(status_code=404, detail="Estate not found")
    nodes = db.query(EstateNode).filter(EstateNode.estate_id == estate.id).order_by(EstateNode.id).all()
    return {"estate": estate_dict(estate), "nodes": [node_dict(node) for node in nodes]}


@router.post("/{estate_id}/nodes")
def create_estate_node(estate_id: int, schema: NodeCreate, current_user=Depends(get_current_user), db=Depends(get_db)) -> dict:
    if schema.node_type not in NODE_TYPES:
        raise HTTPException(status_code=422, detail="node_type must be zone, building, room, or section")
    estate = db.query(Estate).filter(Estate.id == estate_id, Estate.tenant_id == tenant_id_for(current_user)).first()
    if not estate:
        raise HTTPException(status_code=404, detail="Estate not found")
    if schema.parent_id:
        parent = db.query(EstateNode).filter(EstateNode.id == schema.parent_id, EstateNode.estate_id == estate.id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent node does not belong to this estate")
        allowed_parent = {"building": "zone", "room": "building", "section": "room"}.get(schema.node_type)
        if allowed_parent and parent.node_type != allowed_parent:
            raise HTTPException(status_code=400, detail=f"{schema.node_type} must be inside a {allowed_parent}")
    elif schema.node_type != "zone":
        raise HTTPException(status_code=400, detail=f"{schema.node_type} requires a parent node")
    node = EstateNode(
        estate_id=estate.id,
        node_type=schema.node_type,
        name=schema.name,
        parent_id=schema.parent_id,
        description=schema.description,
        position=schema.position,
        dimensions=schema.dimensions,
        node_metadata=schema.metadata,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node_dict(node)