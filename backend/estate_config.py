"""
Aegis Backend - Universal Estate Configuration Parser + Spatial Graph

Parses estate_config.json (the universal layout file) into a NetworkX spatial
graph and persists zones/devices to SQLite so any physical space (3-acre farm,
office building, warehouse) can be loaded by swapping a single JSON file.

Zero-cost, local-first: no cloud dependency, runs on the dev laptop.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import models_db as models
from backend import crud
from backend.schemas import SensorCreate

logger = logging.getLogger(__name__)

# Optional NetworkX spatial graph (universal estate topology)
try:
    import networkx as nx  # type: ignore

    NETWORKX_AVAILABLE = True
except Exception as exc:  # pragma: no cover - fallback when networkx missing
    NETWORKX_AVAILABLE = False
    logger.info("networkx unavailable (%s); spatial graph features degraded", exc)


@dataclass
class BoundaryPoint:
    x: float
    y: float


@dataclass
class ZoneConfig:
    zone_id: str
    name: str
    zone_type: str
    boundary_coordinates: List[Dict[str, float]] = field(default_factory=list)
    target_metrics: Dict[str, float] = field(default_factory=dict)
    devices: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DeviceConfig:
    device_id: str
    zone_id: str
    type: str
    status: str = "ACTIVE"
    position: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EstateConfig:
    estate_id: str
    estate_type: str
    name: str
    zones: List[ZoneConfig] = field(default_factory=list)
    devices: List[DeviceConfig] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


class EstateGraph:
    """
    In-memory spatial graph of an estate.
    Nodes: zones and devices.
    Edges: zone->device (containment), zone->zone (adjacency by proximity).
    """

    def __init__(self, estate_config: EstateConfig):
        self.estate = estate_config
        self.graph: Optional["nx.Graph"] = None
        self._node_zone: Dict[str, str] = {}
        self._build()

    def _build(self) -> None:
        if not NETWORKX_AVAILABLE:
            self.graph = None
            return
        g = nx.Graph()
        g.graph["estate_id"] = self.estate.estate_id
        g.graph["estate_type"] = self.estate.estate_type
        g.graph["name"] = self.estate.name
        for zone in self.estate.zones:
            gid = f"zone:{zone.zone_id}"
            g.add_node(
                gid,
                node_type="zone",
                zone_id=zone.zone_id,
                name=zone.name,
                zone_type=zone.zone_type,
                boundary=zone.boundary_coordinates,
                target_metrics=zone.target_metrics,
                centroid=self._centroid(zone.boundary_coordinates),
            )
            self._node_zone[zone.zone_id] = gid
        for device in self.estate.devices:
            did = f"device:{device.device_id}"
            g.add_node(
                did,
                node_type="device",
                device_id=device.device_id,
                zone_id=device.zone_id,
                name=device.device_id,
                type=device.type,
                status=device.status,
                position=device.position,
            )
            self._node_zone[device.device_id] = device.zone_id
            if device.zone_id in self._node_zone:
                g.add_edge(self._node_zone[device.zone_id], did, relation="contains")
        zone_nodes = [
            n for n, d in g.nodes(data=True) if d.get("node_type") == "zone"
        ]
        for i, a in enumerate(zone_nodes):
            for b in zone_nodes[i + 1 :]:
                ca = g.nodes[a].get("centroid") or {}
                cb = g.nodes[b].get("centroid") or {}
                dist = self._dist(ca, cb)
                if dist is not None and dist < 50.0:
                    g.add_edge(a, b, relation="adjacent", distance=dist)
        self.graph = g

    @staticmethod
    def _centroid(boundary: List[Dict[str, float]]) -> Dict[str, float]:
        if not boundary:
            return {"x": 0.0, "y": 0.0}
        xs = [p.get("x", 0.0) for p in boundary]
        ys = [p.get("y", 0.0) for p in boundary]
        return {"x": sum(xs) / len(xs), "y": sum(ys) / len(ys)}

    @staticmethod
    def _dist(a: Dict[str, float], b: Dict[str, float]) -> Optional[float]:
        try:
            return ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5
        except Exception:
            return None

    def devices_in_zone(self, zone_id: str) -> List[Dict[str, Any]]:
        if self.graph is None:
            return [d for d in self.estate.devices if d.zone_id == zone_id]
        gid = f"zone:{zone_id}"
        out = []
        for nbr in self.graph.neighbors(gid):
            data = self.graph.nodes[nbr]
            if data.get("node_type") == "device":
                out.append(data)
        return out

    def as_dict(self) -> Dict[str, Any]:
        return {
            "estate_id": self.estate.estate_id,
            "estate_type": self.estate.estate_type,
            "name": self.estate.name,
            "node_count": len(self.graph.nodes) if self.graph else 0,
            "edge_count": len(self.graph.edges) if self.graph else 0,
            "zones": [
                {
                    "zone_id": z.zone_id,
                    "name": z.name,
                    "zone_type": z.zone_type,
                    "device_count": len(self.devices_in_zone(z.zone_id)),
                }
                for z in self.estate.zones
            ],
        }

def load_estate_config(path: str | os.PathLike[str]) -> EstateConfig:
    """
    Load and validate an estate_config.json file.
    Raises FileNotFoundError / ValueError on bad input.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Estate config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    estate_id = raw.get("estate_id") or raw.get("id") or f"estate-{uuid.uuid4().hex[:8]}"
    estate_type = raw.get("estate_type", "UNIVERSAL")
    name = raw.get("name", estate_id)
    zones: List[ZoneConfig] = []
    for z in raw.get("zones", []):
        zones.append(
            ZoneConfig(
                zone_id=z.get("zone_id", f"zone-{uuid.uuid4().hex[:6]}"),
                name=z.get("name", z.get("zone_id", "Zone")),
                zone_type=z.get("zone_type", "GENERIC"),
                boundary_coordinates=z.get("boundary_coordinates", []),
                target_metrics=z.get("target_metrics", {}),
                devices=z.get("devices", []),
            )
        )
    devices: List[DeviceConfig] = []
    for d in raw.get("devices", []):
        devices.append(
            DeviceConfig(
                device_id=d.get("device_id", f"dev-{uuid.uuid4().hex[:6]}"),
                zone_id=d.get("zone_id", ""),
                type=d.get("type", "UNKNOWN"),
                status=d.get("status", "ACTIVE"),
                position=d.get("position", {}),
                metadata=d.get("metadata", {}),
            )
        )
    # Lift device definitions nested inside zones into the top-level list too
    for zone in zones:
        for dev in zone.devices:
            devices.append(
                DeviceConfig(
                    device_id=dev.get("device_id", f"dev-{uuid.uuid4().hex[:6]}"),
                    zone_id=zone.zone_id,
                    type=dev.get("type", "UNKNOWN"),
                    status=dev.get("status", "ACTIVE"),
                    position=dev.get("position", {}),
                    metadata=dev.get("metadata", {}),
                )
            )
    return EstateConfig(
        estate_id=estate_id,
        estate_type=estate_type,
        name=name,
        zones=zones,
        devices=devices,
        raw=raw,
    )


def build_graph(estate_config: EstateConfig) -> EstateGraph:
    return EstateGraph(estate_config)

def _default_tenant_id(db: Session) -> int:
    row = db.execute(
        "SELECT id FROM tenants ORDER BY id LIMIT 1"
    ).fetchone()
    if row is None:
        now = datetime.utcnow().isoformat(sep=" ")
        result = db.execute(
            "INSERT INTO tenants (name, settings, created_at, updated_at) "
            "VALUES (:name, :settings, :created_at, :updated_at)",
            {"name": "Default Tenant", "settings": "{}", "created_at": now, "updated_at": now},
        )
        db.commit()
        new_id = result.lastrowid
        if new_id is None:
            new_id = db.execute("SELECT id FROM tenants ORDER BY id LIMIT 1").fetchone()[0]
        return int(new_id)
    return int(row[0])


def persist_estate_config(
    estate_config: EstateConfig,
    db: Session,
    tenant_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Persist an estate config into SQLite zones/sensors/digital_twin_devices.
    Returns a summary of created records.
    """
    if tenant_id is None:
        tenant_id = _default_tenant_id(db)

    zones_created: List[Dict[str, Any]] = []
    devices_created: List[Dict[str, Any]] = []

    from backend.models.digital_twin import DigitalTwinDevice

    # 1) Zones
    for zone in estate_config.zones:
        existing = (
            db.query(models.Zone)
            .filter(models.Zone.name == zone.name, models.Zone.tenant_id == tenant_id)
            .first()
        )
        if existing:
            zones_created.append({"zone_id": existing.id, "name": existing.name, "status": "existing"})
            continue
        db_zone = models.Zone(
            name=zone.name,
            description=f"{zone.zone_type} zone loaded from estate config",
            location=zone.zone_id,
            tenant_id=tenant_id,
        )
        db.add(db_zone)
        db.flush()
        zones_created.append(
            {
                "zone_id": db_zone.id,
                "name": db_zone.name,
                "config_zone_id": zone.zone_id,
                "status": "created",
            }
        )
    db.flush()

    # Map config zone_id -> db Zone.id by name/location for device linkage
    zone_lookup: Dict[str, int] = {}
    for db_zone in db.query(models.Zone).filter(models.Zone.tenant_id == tenant_id).all():
        zone_lookup[db_zone.location] = db_zone.id
        zone_lookup[db_zone.name] = db_zone.id

    # 2) Devices -> sensors + digital twin devices
    for device in estate_config.devices:
        zone_id = zone_lookup.get(device.zone_id)
        try:
            db_sensor = crud.create_sensor(
                db,
                SensorCreate(
                    name=device.device_id,
                    type=device.type,
                    location=device.zone_id,
                    zone_id=zone_id,
                ),
                tenant_id=tenant_id,
            )
            devices_created.append(
                {
                    "device_id": device.device_id,
                    "db_sensor_id": db_sensor.id,
                    "zone_id": zone_id,
                    "status": "created",
                }
            )
        except Exception as exc:
            logger.warning("Failed to create sensor %s: %s", device.device_id, exc)
        try:
            existing_twin = (
                db.query(DigitalTwinDevice)
                .filter(
                    DigitalTwinDevice.device_id == device.device_id,
                    DigitalTwinDevice.tenant_id == tenant_id,
                )
                .first()
            )
            if existing_twin is None:
                db_twin = DigitalTwinDevice(
                    tenant_id=tenant_id,
                    zone_id=zone_id,
                    device_id=device.device_id,
                    name=device.device_id,
                    kind="sensor" if device.type.upper().startswith("SENSOR") else "actuator",
                    device_type=device.type,
                    status="online",
                    position=device.position or {"x": 0, "y": 0, "z": 0},
                    state={"status": device.status, **device.metadata},
                    simulation_enabled=1,
                    control_mode="automation",
                    automation_policy={},
                    last_updated=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )
                db.add(db_twin)
                db.flush()
                if devices_created:
                    devices_created[-1]["db_twin_id"] = db_twin.id
        except Exception as exc:
            logger.warning("Failed to create digital twin %s: %s", device.device_id, exc)

    db.commit()
    return {
        "estate_id": estate_config.estate_id,
        "tenant_id": tenant_id,
        "zones": zones_created,
        "devices": devices_created,
        "zones_created": len(zones_created),
        "devices_created": len(devices_created),
    }


def export_estate_config(db: Session, tenant_id: int) -> Dict[str, Any]:
    """
    Read the current tenant's zones back out as an estate config dict
    (round-trip for hot-swap / export).
    """
    zones = db.query(models.Zone).filter(models.Zone.tenant_id == tenant_id).all()
    out_zones = [
        {
            "zone_id": z.location or str(z.id),
            "name": z.name,
            "zone_type": "GENERIC",
            "target_metrics": {},
            "boundary_coordinates": [],
        }
        for z in zones
    ]
    return {
        "estate_id": f"estate-tenant-{tenant_id}",
        "estate_type": "UNIVERSAL",
        "zones": out_zones,
    }


def load_and_persist(
    path: str | os.PathLike[str], tenant_id: Optional[int] = None
) -> Dict[str, Any]:
    cfg = load_estate_config(path)
    with SessionLocal() as db:
        summary = persist_estate_config(cfg, db, tenant_id=tenant_id)
    graph = build_graph(cfg)
    summary["graph"] = graph.as_dict()
    return summary
