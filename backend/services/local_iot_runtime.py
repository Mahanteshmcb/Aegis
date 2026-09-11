"""Local-first IOT runtime for device registry, command queue, telemetry, and twin sync."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional


class LocalIotRuntime:
    """In-memory runtime used to keep a tenant-local twin synchronized."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.zone_index: Dict[int, List[str]] = defaultdict(list)
        self.command_queue: List[Dict[str, Any]] = []
        self.event_log: List[Dict[str, Any]] = []

    def _stamp(self) -> str:
        return datetime.utcnow().isoformat()

    def _log_event(self, event_type: str, device_id: Optional[str] = None, zone_id: Optional[int] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        record = {
            "id": len(self.event_log) + 1,
            "event_type": event_type,
            "device_id": device_id,
            "zone_id": zone_id,
            "payload": payload or {},
            "timestamp": self._stamp(),
        }
        self.event_log.append(record)
        return record

    def register_device(
        self,
        *,
        tenant_id: int,
        zone_id: Optional[int],
        device_id: str,
        name: str,
        kind: str,
        device_type: str,
        status: str = "online",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        with self._lock:
            current = self.registry.get(device_id, {})
            device = {
                "tenant_id": tenant_id,
                "device_id": device_id,
                "zone_id": zone_id,
                "name": name,
                "kind": kind,
                "device_type": device_type,
                "status": status,
                "position": current.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}),
                "state": current.get("state", {}),
                "metadata": {**current.get("metadata", {}), **metadata},
                "last_updated": self._stamp(),
            }
            self.registry[device_id] = device
            if zone_id is not None:
                ids = [item for item in self.zone_index.get(zone_id, []) if item != device_id]
                ids.append(device_id)
                self.zone_index[zone_id] = ids
            self._log_event("device_registered", device_id=device_id, zone_id=zone_id, payload={"name": name, "kind": kind})
            return device

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.registry.get(device_id)

    def list_devices(self, tenant_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self.registry.values())
            if tenant_id is not None:
                items = [item for item in items if item.get("tenant_id") == tenant_id]
            return items

    def list_zone_devices(self, zone_id: int, tenant_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            matches = [self.registry[item] for item in self.zone_index.get(zone_id, []) if item in self.registry]
            if tenant_id is not None:
                matches = [item for item in matches if item.get("tenant_id") == tenant_id]
            return matches

    def queue_command(
        self,
        *,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
        zone_id: Optional[int] = None,
        created_by: str = "system",
    ) -> Dict[str, Any]:
        with self._lock:
            record = {
                "id": len(self.command_queue) + 1,
                "device_id": device_id,
                "zone_id": zone_id,
                "command": command,
                "parameters": parameters or {},
                "status": "queued",
                "created_by": created_by,
                "created_at": self._stamp(),
            }
            self.command_queue.append(record)
            if device_id in self.registry:
                self.registry[device_id]["state"] = {
                    **self.registry[device_id].get("state", {}),
                    "last_command": command,
                    "last_command_parameters": parameters or {},
                    "last_command_at": record["created_at"],
                }
                self.registry[device_id]["last_updated"] = record["created_at"]
            self._log_event("command_queued", device_id=device_id, zone_id=zone_id, payload={"command": command, "parameters": parameters or {}})
            return record

    def execute_command(self, *, device_id: str, command: str, parameters: Optional[Dict[str, Any]] = None, actor: str = "operator") -> Dict[str, Any]:
        with self._lock:
            if device_id not in self.registry:
                raise KeyError(f"Device {device_id} is not registered locally")
            device = self.registry[device_id]
            device["state"] = {
                **device.get("state", {}),
                "last_command": command,
                "last_command_parameters": parameters or {},
                "last_command_at": self._stamp(),
                "last_actor": actor,
            }
            device["status"] = "online"
            device["last_updated"] = self._stamp()
            for item in reversed(self.command_queue):
                if item["device_id"] == device_id and item["status"] == "queued":
                    item["status"] = "executed"
                    item["executed_at"] = device["last_updated"]
                    break
            self._log_event("command_executed", device_id=device_id, zone_id=device.get("zone_id"), payload={"command": command, "parameters": parameters or {}})
            return device

    def record_telemetry(
        self,
        *,
        device_id: str,
        value: float,
        unit: str = "raw",
        sensor_type: Optional[str] = None,
        zone_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            if device_id not in self.registry:
                raise KeyError(f"Device {device_id} is not registered locally")
            device = self.registry[device_id]
            if zone_id is not None:
                device["zone_id"] = zone_id
            telemetry = {
                "value": value,
                "unit": unit,
                "sensor_type": sensor_type,
                "timestamp": self._stamp(),
            }
            device["telemetry"] = telemetry
            state = device.get("state", {})
            state.update({
                "last_value": value,
                "last_unit": unit,
                "last_sensor_type": sensor_type,
                "last_reading_at": telemetry["timestamp"],
            })
            device["state"] = state
            device["status"] = "online"
            device["last_updated"] = telemetry["timestamp"]
            self._log_event("telemetry_recorded", device_id=device_id, zone_id=device.get("zone_id"), payload={"value": value, "unit": unit, "sensor_type": sensor_type})
            return device

    def get_twin_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            zones = []
            for zone_id, device_ids in self.zone_index.items():
                if zone_id is None:
                    continue
                zones.append({
                    "id": zone_id,
                    "device_count": len([item for item in device_ids if item in self.registry]),
                    "device_ids": [item for item in device_ids if item in self.registry],
                })
            return {
                "devices": list(self.registry.values()),
                "zones": zones,
                "command_queue": self.command_queue,
                "events": self.event_log[-25:],
                "updated_at": self._stamp(),
            }


runtime = LocalIotRuntime()
