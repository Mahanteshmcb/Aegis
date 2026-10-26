"""Transport-neutral contracts and adapters for simulated and physical devices."""
from __future__ import annotations

import json
import math
from ipaddress import ip_address
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4


SUPPORTED_ADAPTER_TYPES = frozenset({"simulation", "mqtt", "rest", "serial", "grpc"})


class AdapterError(RuntimeError):
    """Base error for adapter dispatch and protocol failures."""


class AdapterUnavailableError(AdapterError):
    """Raised when a device selects a transport with no configured driver."""


class AdapterCommandError(AdapterError):
    """Raised when a configured transport cannot deliver a command."""


class TelemetryValidationError(ValueError):
    """Raised when a transport message does not match the canonical schema."""


@dataclass(frozen=True)
class DeviceContext:
    device_id: str
    tenant_id: int
    zone_id: int | None
    kind: str
    device_type: str
    status: str


@dataclass(frozen=True)
class DeviceCommand:
    command_id: str
    device_id: str
    tenant_id: int
    zone_id: int | None
    name: str
    parameters: Mapping[str, Any]
    issued_at: str

    @classmethod
    def create(
        cls, device: DeviceContext, name: str, parameters: Mapping[str, Any]
    ) -> "DeviceCommand":
        return cls(
            command_id=str(uuid4()),
            device_id=device.device_id,
            tenant_id=device.tenant_id,
            zone_id=device.zone_id,
            name=name,
            parameters=dict(parameters),
            issued_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": "aegis.device-command.v1",
            "command_id": self.command_id,
            "device_id": self.device_id,
            "tenant_id": self.tenant_id,
            "zone_id": self.zone_id,
            "command": self.name,
            "parameters": dict(self.parameters),
            "issued_at": self.issued_at,
        }


@dataclass(frozen=True)
class DeviceTelemetry:
    device_id: str
    tenant_id: int
    zone_id: int | None
    sensor_type: str
    value: float
    unit: str
    sampled_at: datetime

    @classmethod
    def from_message(
        cls, device: DeviceContext, payload: Mapping[str, Any]
    ) -> "DeviceTelemetry":
        message_device_id = payload.get("device_id", device.device_id)
        if str(message_device_id) != device.device_id:
            raise TelemetryValidationError("Telemetry device_id does not match its registered device")

        message_tenant_id = payload.get("tenant_id", device.tenant_id)
        try:
            tenant_id = int(message_tenant_id)
        except (TypeError, ValueError) as exc:
            raise TelemetryValidationError("Telemetry tenant_id must be an integer") from exc
        if tenant_id != device.tenant_id:
            raise TelemetryValidationError("Telemetry tenant_id does not match its registered device")

        try:
            value = float(payload["value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TelemetryValidationError("Telemetry value must be numeric") from exc
        if not math.isfinite(value):
            raise TelemetryValidationError("Telemetry value must be finite")

        raw_timestamp = payload.get("sampled_at", payload.get("timestamp"))
        if raw_timestamp is None:
            sampled_at = datetime.now(timezone.utc)
        elif isinstance(raw_timestamp, datetime):
            sampled_at = raw_timestamp
        elif isinstance(raw_timestamp, str):
            try:
                sampled_at = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            except ValueError as exc:
                raise TelemetryValidationError("Telemetry timestamp must be ISO-8601") from exc
        else:
            raise TelemetryValidationError("Telemetry timestamp must be ISO-8601")
        if sampled_at.tzinfo is None:
            sampled_at = sampled_at.replace(tzinfo=timezone.utc)

        sensor_type = str(payload.get("sensor_type") or device.device_type).strip()
        unit = str(payload.get("unit") or "raw").strip()
        if not sensor_type or not unit:
            raise TelemetryValidationError("Telemetry sensor_type and unit must not be empty")

        raw_zone_id = payload.get("zone_id", device.zone_id)
        try:
            zone_id = int(raw_zone_id) if raw_zone_id is not None else None
        except (TypeError, ValueError) as exc:
            raise TelemetryValidationError("Telemetry zone_id must be an integer") from exc
        if zone_id != device.zone_id:
            raise TelemetryValidationError("Telemetry zone_id does not match its registered device")

        return cls(
            device_id=device.device_id,
            tenant_id=device.tenant_id,
            zone_id=device.zone_id,
            sensor_type=sensor_type,
            value=value,
            unit=unit,
            sampled_at=sampled_at,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": "aegis.device-telemetry.v1",
            "device_id": self.device_id,
            "tenant_id": self.tenant_id,
            "zone_id": self.zone_id,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "sampled_at": self.sampled_at.isoformat(),
        }


@dataclass(frozen=True)
class CommandAcknowledgement:
    command_id: str
    device_id: str
    adapter_type: str
    accepted: bool
    confirmed: bool
    message: str
    acknowledged_at: str
    state: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "command_id": self.command_id,
            "device_id": self.device_id,
            "adapter_type": self.adapter_type,
            "accepted": self.accepted,
            "confirmed": self.confirmed,
            "message": self.message,
            "acknowledged_at": self.acknowledged_at,
        }
        if self.state is not None:
            payload["state"] = self.state
        return payload


class DeviceAdapter(Protocol):
    adapter_type: str

    def execute(self, command: DeviceCommand) -> CommandAcknowledgement: ...

    def normalize_telemetry(
        self, device: DeviceContext, payload: Mapping[str, Any]
    ) -> DeviceTelemetry: ...


class _AdapterBase:
    adapter_type: str

    def normalize_telemetry(
        self, device: DeviceContext, payload: Mapping[str, Any]
    ) -> DeviceTelemetry:
        return DeviceTelemetry.from_message(device, payload)

    def _acknowledgement(
        self, command: DeviceCommand, accepted: bool, confirmed: bool, message: str
    ) -> CommandAcknowledgement:
        return CommandAcknowledgement(
            command_id=command.command_id,
            device_id=command.device_id,
            adapter_type=self.adapter_type,
            accepted=accepted,
            confirmed=confirmed,
            message=message,
            acknowledged_at=datetime.now(timezone.utc).isoformat(),
        )


class SimulationAdapter(_AdapterBase):
    adapter_type = "simulation"

    def execute(self, command: DeviceCommand) -> CommandAcknowledgement:
        return self._acknowledgement(
            command, accepted=True, confirmed=True, message="Applied by the Aegis software simulator"
        )


class MqttAdapter(_AdapterBase):
    """MQTT publisher adapter; the injected client owns TLS and broker credentials."""

    adapter_type = "mqtt"

    def __init__(
        self,
        publish: Callable[..., Any],
        topic_for_device: Callable[[str], str],
        qos: int = 1,
    ) -> None:
        self._publish = publish
        self._topic_for_device = topic_for_device
        self._qos = qos

    def execute(self, command: DeviceCommand) -> CommandAcknowledgement:
        payload = json.dumps(command.to_payload(), sort_keys=True)
        try:
            result = self._publish(self._topic_for_device(command.device_id), payload, qos=self._qos)
        except Exception as exc:
            raise AdapterCommandError("MQTT command publish failed") from exc
        return self._acknowledgement(
            command,
            accepted=True,
            confirmed=bool(getattr(result, "device_acknowledged", False)),
            message="Published to MQTT broker; device acknowledgement is not implied",
        )


class RestAdapter(_AdapterBase):
    """REST command adapter; endpoint lookup and authentication stay outside the model."""

    adapter_type = "rest"

    def __init__(
        self,
        post: Callable[..., Any],
        endpoint_for_device: Callable[[str], str],
        timeout_seconds: float = 5.0,
    ) -> None:
        self._post = post
        self._endpoint_for_device = endpoint_for_device
        self._timeout_seconds = timeout_seconds

    def execute(self, command: DeviceCommand) -> CommandAcknowledgement:
        try:
            response = self._post(
                self._endpoint_for_device(command.device_id),
                json=command.to_payload(),
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            response_body = response.json() if callable(getattr(response, "json", None)) else {}
        except Exception as exc:
            raise AdapterCommandError("REST command request failed") from exc
        if not isinstance(response_body, Mapping):
            response_body = {}
        accepted = response_body.get("accepted", True) is True
        confirmed = response_body.get("confirmed", response_body.get("acknowledged", False)) is True
        return self._acknowledgement(
            command, accepted, confirmed,
            str(response_body.get("message") or "REST endpoint accepted the command request"),
        )


class SerialAdapter(_AdapterBase):
    """Serial command adapter; port ownership and operating-system setup are injected."""

    adapter_type = "serial"

    def __init__(self, writer_for_device: Callable[[str], Any]) -> None:
        self._writer_for_device = writer_for_device

    def execute(self, command: DeviceCommand) -> CommandAcknowledgement:
        writer = self._writer_for_device(command.device_id)
        frame = (json.dumps(command.to_payload(), sort_keys=True) + "\n").encode("utf-8")
        try:
            written = writer.write(frame)
            flush = getattr(writer, "flush", None)
            if callable(flush):
                flush()
        except Exception as exc:
            raise AdapterCommandError("Serial command write failed") from exc
        if written is not None and written != len(frame):
            raise AdapterCommandError("Serial transport wrote an incomplete command frame")
        return self._acknowledgement(
            command, True, False, "Written to serial transport; device acknowledgement is not implied"
        )


class ArduinoGatewayAdapter(_AdapterBase):
    """Deliver the single-device LED pilot command through its loopback gateway."""

    adapter_type = "serial"

    def __init__(
        self,
        gateway_url: str,
        token: str,
        expected_device_id: str,
        timeout_seconds: float = 4.0,
        post_json: Callable[[str, dict[str, Any], str, float], Mapping[str, Any]] | None = None,
    ) -> None:
        parsed_url = urlparse(gateway_url)
        hostname = parsed_url.hostname or ""
        try:
            is_loopback = ip_address(hostname).is_loopback
        except ValueError:
            is_loopback = hostname.lower() == "localhost"
        if parsed_url.scheme != "http" or not is_loopback:
            raise ValueError("Arduino pilot gateway must use HTTP on this computer's loopback interface")
        if not token or len(token) < 32:
            raise ValueError("Arduino pilot gateway token must contain at least 32 characters")
        if not expected_device_id:
            raise ValueError("Arduino pilot device ID must not be empty")
        self._gateway_url = gateway_url.rstrip("/") + "/commands"
        self._token = token
        self._expected_device_id = expected_device_id
        self._timeout_seconds = timeout_seconds
        self._post_json = post_json or self._http_post_json

    @staticmethod
    def _http_post_json(
        url: str, payload: dict[str, Any], token: str, timeout_seconds: float
    ) -> Mapping[str, Any]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                error_body = json.loads(exc.read().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                error_body = {}
            detail = error_body.get("detail") if isinstance(error_body, Mapping) else None
            if isinstance(detail, str) and detail:
                raise AdapterCommandError(
                    f"Arduino gateway rejected the command (HTTP {exc.code}): {detail}"
                ) from exc
            raise AdapterCommandError(
                f"Arduino gateway rejected the command (HTTP {exc.code})"
            ) from exc
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AdapterCommandError("Arduino gateway could not deliver the command") from exc
        if not isinstance(result, Mapping):
            raise AdapterCommandError("Arduino gateway returned an invalid response")
        return result

    def execute(self, command: DeviceCommand) -> CommandAcknowledgement:
        if command.device_id != self._expected_device_id:
            raise AdapterCommandError("This gateway is configured for a different physical device")
        command_name = command.name.lower()
        if command_name not in {"on", "off"}:
            raise AdapterCommandError("Arduino LED gateway accepts only on and off commands")
        if command.parameters:
            raise AdapterCommandError("Arduino LED gateway does not accept command parameters")

        result = self._post_json(
            self._gateway_url,
            command.to_payload(),
            self._token,
            self._timeout_seconds,
        )
        expected_state = "ON" if command_name == "on" else "OFF"
        if (
            result.get("accepted") is not True
            or result.get("confirmed") is not True
            or result.get("command_id") != command.command_id
            or result.get("device_id") != command.device_id
            or result.get("state") != expected_state
        ):
            raise AdapterCommandError("Arduino gateway did not confirm the requested LED state")
        return CommandAcknowledgement(
            command_id=command.command_id,
            device_id=command.device_id,
            adapter_type=self.adapter_type,
            accepted=True,
            confirmed=True,
            message=f"Arduino confirmed LED_{expected_state}",
            acknowledged_at=datetime.now(timezone.utc).isoformat(),
            state=expected_state,
        )


class GrpcAdapter(_AdapterBase):
    """gRPC command adapter; generated stubs and request construction are injected."""

    adapter_type = "grpc"

    def __init__(
        self,
        call_for_device: Callable[[str], Callable[[Any], Any]],
        request_factory: Callable[[dict[str, Any]], Any] = lambda payload: payload,
    ) -> None:
        self._call_for_device = call_for_device
        self._request_factory = request_factory

    def execute(self, command: DeviceCommand) -> CommandAcknowledgement:
        try:
            response = self._call_for_device(command.device_id)(
                self._request_factory(command.to_payload())
            )
        except Exception as exc:
            raise AdapterCommandError("gRPC command call failed") from exc
        accepted = getattr(response, "accepted", True) is True
        confirmed = getattr(response, "confirmed", getattr(response, "acknowledged", False)) is True
        message = getattr(response, "message", "gRPC endpoint accepted the command request")
        return self._acknowledgement(command, accepted, confirmed, str(message))


class AdapterRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._adapters: dict[str, DeviceAdapter] = {}
        self.register(SimulationAdapter())

    def register(self, adapter: DeviceAdapter) -> None:
        adapter_type = getattr(adapter, "adapter_type", None)
        if adapter_type not in SUPPORTED_ADAPTER_TYPES:
            raise ValueError(f"Unsupported adapter type: {adapter_type!r}")
        if not callable(getattr(adapter, "execute", None)) or not callable(
            getattr(adapter, "normalize_telemetry", None)
        ):
            raise TypeError("Device adapters must implement execute and normalize_telemetry")
        with self._lock:
            self._adapters[adapter_type] = adapter

    def get(self, adapter_type: str) -> DeviceAdapter:
        with self._lock:
            adapter = self._adapters.get(adapter_type)
        if adapter is None:
            raise AdapterUnavailableError(
                f"The {adapter_type!r} adapter is not configured in this backend process"
            )
        return adapter

    def available_adapter_types(self) -> list[str]:
        with self._lock:
            return sorted(self._adapters)


adapter_registry = AdapterRegistry()


def device_context(device: Any) -> DeviceContext:
    return DeviceContext(
        device_id=str(device.device_id),
        tenant_id=int(device.tenant_id),
        zone_id=int(device.zone_id) if device.zone_id is not None else None,
        kind=str(device.kind),
        device_type=str(device.device_type),
        status=str(device.status),
    )


def dispatch_command(
    device: Any, command_name: str, parameters: Mapping[str, Any]
) -> tuple[DeviceCommand, CommandAcknowledgement]:
    command = DeviceCommand.create(device_context(device), command_name, parameters)
    adapter = adapter_registry.get(str(device.adapter_type))
    acknowledgement = adapter.execute(command)
    if not acknowledgement.accepted:
        raise AdapterCommandError(acknowledgement.message or "Device rejected the command")
    return command, acknowledgement
