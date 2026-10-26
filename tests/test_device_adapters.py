import io
from datetime import datetime, timezone

import pytest

from backend.device_adapters import (
    AdapterCommandError,
    AdapterUnavailableError,
    AdapterRegistry,
    DeviceCommand,
    DeviceContext,
    GrpcAdapter,
    MqttAdapter,
    RestAdapter,
    SerialAdapter,
    SimulationAdapter,
    TelemetryValidationError,
)


@pytest.fixture
def command():
    device = DeviceContext(
        device_id="pump-01",
        tenant_id=7,
        zone_id=3,
        kind="actuator",
        device_type="pump",
        status="online",
    )
    return DeviceCommand.create(device, "start", {"flow": 24})


def test_simulation_adapter_acknowledges_software_execution(command):
    acknowledgement = SimulationAdapter().execute(command)

    assert acknowledgement.adapter_type == "simulation"
    assert acknowledgement.accepted is True
    assert acknowledgement.confirmed is True


def test_mqtt_adapter_does_not_claim_device_confirmation(command):
    published = []
    adapter = MqttAdapter(
        lambda topic, payload, qos: published.append((topic, payload, qos)),
        lambda device_id: f"devices/{device_id}/commands",
    )

    acknowledgement = adapter.execute(command)

    assert published[0][0] == "devices/pump-01/commands"
    assert published[0][2] == 1
    assert acknowledgement.accepted is True
    assert acknowledgement.confirmed is False


def test_rest_adapter_uses_explicit_endpoint_acknowledgement(command):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"accepted": True, "confirmed": True, "message": "relay confirmed"}

    calls = []
    adapter = RestAdapter(
        lambda url, **kwargs: calls.append((url, kwargs)) or Response(),
        lambda device_id: f"https://devices.example/{device_id}",
    )

    acknowledgement = adapter.execute(command)

    assert calls[0][0] == "https://devices.example/pump-01"
    assert acknowledgement.confirmed is True
    assert acknowledgement.message == "relay confirmed"


def test_serial_adapter_writes_standard_command_without_claiming_confirmation(command):
    writer = io.BytesIO()
    acknowledgement = SerialAdapter(lambda device_id: writer).execute(command)

    assert b'"schema": "aegis.device-command.v1"' in writer.getvalue()
    assert acknowledgement.accepted is True
    assert acknowledgement.confirmed is False


def test_grpc_adapter_maps_response_confirmation(command):
    class Response:
        accepted = True
        confirmed = True
        message = "robot accepted command"

    adapter = GrpcAdapter(lambda device_id: lambda request: Response())

    acknowledgement = adapter.execute(command)

    assert acknowledgement.confirmed is True
    assert acknowledgement.message == "robot accepted command"


def test_adapter_registry_requires_explicit_hardware_configuration():
    registry = AdapterRegistry()

    assert registry.available_adapter_types() == ["simulation"]
    with pytest.raises(AdapterUnavailableError, match="not configured"):
        registry.get("grpc")


@pytest.mark.parametrize(
    "payload",
    [
        {"device_id": "other", "value": 10},
        {"tenant_id": 8, "value": 10},
        {"zone_id": 4, "value": 10},
        {"value": float("inf")},
        {"value": 10, "timestamp": "not-a-timestamp"},
    ],
)
def test_telemetry_normalization_rejects_invalid_identity_and_values(payload):
    device = DeviceContext(
        device_id="sensor-01",
        tenant_id=7,
        zone_id=3,
        kind="sensor",
        device_type="temperature",
        status="online",
    )

    with pytest.raises(TelemetryValidationError):
        SimulationAdapter().normalize_telemetry(device, payload)


def test_telemetry_normalization_returns_canonical_tenant_scoped_sample():
    device = DeviceContext(
        device_id="sensor-01",
        tenant_id=7,
        zone_id=3,
        kind="sensor",
        device_type="temperature",
        status="online",
    )
    sample_time = datetime(2026, 1, 2, tzinfo=timezone.utc)

    telemetry = SimulationAdapter().normalize_telemetry(
        device,
        {
            "device_id": "sensor-01",
            "tenant_id": 7,
            "zone_id": 3,
            "value": 21.5,
            "unit": "C",
            "timestamp": sample_time.isoformat(),
        },
    )

    assert telemetry.value == 21.5
    assert telemetry.tenant_id == 7
    assert telemetry.zone_id == 3
    assert telemetry.sampled_at == sample_time


def test_rest_adapter_wraps_transport_failures(command):
    adapter = RestAdapter(
        lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError()),
        lambda device_id: "https://devices.example/command",
    )

    with pytest.raises(AdapterCommandError, match="REST command request failed"):
        adapter.execute(command)
