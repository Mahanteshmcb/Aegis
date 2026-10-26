import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from backend.device_adapters import (
    AdapterCommandError,
    ArduinoGatewayAdapter,
    DeviceCommand,
    DeviceContext,
)
from hardware.arduino_mega_led.gateway import create_gateway_app


TOKEN = "local-test-gateway-token-at-least-32-characters"
DEVICE_ID = "mega-onboard-led-01"


class FakeMega:
    def __init__(self):
        self.state = "OFF"
        self.last_response = b""
        self.writes = []

    def write(self, frame):
        self.writes.append(frame)
        protocol, command_id, device_id, command = frame.decode("ascii").strip().split(",")
        assert protocol == "AEGIS/1"
        assert device_id == DEVICE_ID
        if command == "LED_ON":
            self.state = "ON"
        elif command == "LED_OFF":
            self.state = "OFF"
        self.last_response = f"AEGIS/1,{command_id},OK,{self.state}\r\n".encode("ascii")
        return len(frame)

    def flush(self):
        return None

    def readline(self):
        return self.last_response


def make_command(name):
    device = DeviceContext(
        device_id=DEVICE_ID,
        tenant_id=1,
        zone_id=None,
        kind="actuator",
        device_type="onboard_led",
        status="online",
    )
    return DeviceCommand.create(device, name, {})


def test_gateway_adapter_translates_and_confirms_led_commands():
    mega = FakeMega()
    app = create_gateway_app(mega, TOKEN)
    client = TestClient(app)

    def post_json(url, payload, token, timeout):
        assert url == "http://127.0.0.1:8765/commands"
        assert token == TOKEN
        response = client.post("/commands", json=payload, headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            raise AdapterCommandError(f"gateway returned HTTP {response.status_code}")
        return response.json()

    adapter = ArduinoGatewayAdapter(
        "http://127.0.0.1:8765",
        TOKEN,
        DEVICE_ID,
        post_json=post_json,
    )

    on_command = make_command("on")
    on_ack = adapter.execute(on_command)
    off_command = make_command("off")
    off_ack = adapter.execute(off_command)

    assert mega.writes[0] == f"AEGIS/1,{on_command.command_id},{DEVICE_ID},LED_ON\n".encode()
    assert mega.writes[1] == f"AEGIS/1,{off_command.command_id},{DEVICE_ID},LED_OFF\n".encode()
    assert (on_ack.confirmed, on_ack.state) == (True, "ON")
    assert (off_ack.confirmed, off_ack.state) == (True, "OFF")


def test_gateway_rejects_invalid_token_without_touching_serial():
    mega = FakeMega()
    app = create_gateway_app(mega, TOKEN)
    client = TestClient(app)
    payload = make_command("on").to_payload()

    response = client.post("/commands", json=payload, headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401
    assert mega.writes == []


def test_gateway_rejects_wrong_device_and_unsupported_commands():
    mega = FakeMega()
    client = TestClient(create_gateway_app(mega, TOKEN))
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = make_command("on").to_payload()

    wrong_device = {**payload, "device_id": "another-device"}
    unsupported = {**payload, "command": "reset"}

    assert client.post("/commands", json=wrong_device, headers=headers).status_code == 404
    assert client.post("/commands", json=unsupported, headers=headers).status_code == 422
    assert mega.writes == []


def test_gateway_does_not_claim_success_when_board_does_not_acknowledge():
    class SilentMega:
        def write(self, frame):
            return len(frame)

        def flush(self):
            return None

        def readline(self):
            return b""

    client = TestClient(create_gateway_app(SilentMega(), TOKEN))
    response = client.post(
        "/commands",
        json=make_command("on").to_payload(),
        headers={"Authorization": f"Bearer {TOKEN}"},
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "Arduino did not acknowledge the command"


def test_gateway_reconnects_after_serial_disconnect():
    class DisconnectedMega(FakeMega):
        is_open = True

        def write(self, frame):
            raise OSError("device was unplugged")

        def close(self):
            self.is_open = False

    disconnected = DisconnectedMega()
    reconnected = FakeMega()
    app = create_gateway_app(
        disconnected,
        TOKEN,
        serial_port_factory=lambda: reconnected,
    )
    client = TestClient(app)

    response = client.post(
        "/commands",
        json=make_command("on").to_payload(),
        headers={"Authorization": f"Bearer {TOKEN}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["confirmed"] is True
    assert disconnected.is_open is False
    assert reconnected.state == "ON"


def test_gateway_can_start_without_board_and_connect_when_it_returns():
    reconnected = FakeMega()
    app = create_gateway_app(None, TOKEN, serial_port_factory=lambda: reconnected)
    client = TestClient(app)

    assert client.get("/health").json()["serial_open"] is False
    response = client.post(
        "/commands",
        json=make_command("off").to_payload(),
        headers={"Authorization": f"Bearer {TOKEN}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["confirmed"] is True
    assert client.get("/health").json()["serial_open"] is True


def test_gateway_health_reports_missing_serial_port_as_unavailable():
    client = TestClient(
        create_gateway_app(None, TOKEN, serial_port_factory=lambda: pytest.fail("no command was sent"))
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["serial_open"] is False


def test_serial_port_resolution_finds_reassigned_mega_port():
    from hardware.arduino_mega_led.gateway import resolve_serial_port

    available_ports = [
        SimpleNamespace(device="COM12", vid=0x2341, pid=0x0042, description="Arduino Mega 2560")
    ]

    assert resolve_serial_port("COM9", available_ports) == "COM12"
    assert resolve_serial_port("auto", available_ports) == "COM12"


def test_serial_port_resolution_rejects_ambiguous_mega_boards():
    from hardware.arduino_mega_led.gateway import resolve_serial_port

    available_ports = [
        SimpleNamespace(device="COM9", vid=0x2341, pid=0x0042, description="Arduino Mega 2560"),
        SimpleNamespace(device="COM12", vid=0x2A03, pid=0x0042, description="Arduino Mega 2560"),
    ]

    with pytest.raises(RuntimeError, match="Multiple Arduino Mega boards"):
        resolve_serial_port("auto", available_ports)


def test_gateway_adapter_rejects_unconfirmed_or_wrong_state_response():
    command = make_command("on")
    adapter = ArduinoGatewayAdapter(
        "http://localhost:8765",
        TOKEN,
        DEVICE_ID,
        post_json=lambda *_: {
            "accepted": True,
            "confirmed": True,
            "command_id": command.command_id,
            "device_id": DEVICE_ID,
            "state": "OFF",
        },
    )

    with pytest.raises(AdapterCommandError, match="did not confirm"):
        adapter.execute(command)


def test_gateway_adapter_includes_actionable_gateway_error_detail(monkeypatch):
    from io import BytesIO
    from urllib.error import HTTPError
    import backend.device_adapters as device_adapters

    def unavailable_gateway(*_args, **_kwargs):
        raise HTTPError(
            "http://127.0.0.1:8765/commands",
            503,
            "Service Unavailable",
            {},
            BytesIO(b'{"detail":"Arduino serial transport is unavailable; check the USB connection"}'),
        )

    monkeypatch.setattr(device_adapters, "urlopen", unavailable_gateway)
    with pytest.raises(
        AdapterCommandError,
        match="HTTP 503.*check the USB connection",
    ):
        ArduinoGatewayAdapter._http_post_json(
            "http://127.0.0.1:8765/commands",
            {},
            TOKEN,
            1,
        )


def test_gateway_adapter_restricts_device_and_command():
    adapter = ArduinoGatewayAdapter(
        "http://127.0.0.1:8765",
        TOKEN,
        DEVICE_ID,
        post_json=lambda *_: pytest.fail("invalid commands must not reach the gateway"),
    )
    wrong_device = DeviceCommand.create(
        DeviceContext("another-device", 1, None, "actuator", "led", "online"),
        "on",
        {},
    )
    unsupported = make_command("reset")

    with pytest.raises(AdapterCommandError, match="different physical device"):
        adapter.execute(wrong_device)
    with pytest.raises(AdapterCommandError, match="only on and off"):
        adapter.execute(unsupported)


def test_gateway_requires_loopback_http_and_strong_token():
    with pytest.raises(ValueError, match="loopback"):
        ArduinoGatewayAdapter("http://192.0.2.1:8765", TOKEN, DEVICE_ID)
    with pytest.raises(ValueError, match="32 characters"):
        ArduinoGatewayAdapter("http://127.0.0.1:8765", "short", DEVICE_ID)


def test_twin_rejects_unmapped_serial_device_ids(client, test_db, monkeypatch):
    monkeypatch.setattr("backend.routers.digital_twin.SessionLocal", test_db)
    response = client.post("/api/v1/digital-twin/devices", headers={
        "Authorization": "Bearer test-token",
    }, json={
        "device_id": "another-mega",
        "name": "Unmapped Mega",
        "kind": "actuator",
        "device_type": "onboard_led",
        "adapter_type": "serial",
    })

    assert response.status_code == 422
    assert "mega-onboard-led-01" in response.json()["detail"]


def test_gateway_settings_load_from_aegis_environment_names(monkeypatch):
    from backend.config import Settings

    monkeypatch.setenv("AEGIS_ARDUINO_GATEWAY_TOKEN", TOKEN)
    monkeypatch.setenv("AEGIS_ARDUINO_GATEWAY_URL", "http://localhost:8765")
    settings = Settings(_env_file=None)

    assert settings.arduino_gateway_token is not None
    assert settings.arduino_gateway_token.get_secret_value() == TOKEN
    assert settings.arduino_gateway_url == "http://localhost:8765"


def test_aegis_control_route_persists_only_confirmed_gateway_state(
    client, test_db, monkeypatch
):
    from backend.device_adapters import AdapterRegistry

    from_backend = FakeMega()
    gateway_client = TestClient(create_gateway_app(from_backend, TOKEN))

    def post_json(url, payload, token, timeout):
        response = gateway_client.post(
            "/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            raise AdapterCommandError(f"gateway returned HTTP {response.status_code}")
        return response.json()

    registry = AdapterRegistry()
    registry.register(ArduinoGatewayAdapter(
        "http://127.0.0.1:8765",
        TOKEN,
        DEVICE_ID,
        post_json=post_json,
    ))
    monkeypatch.setattr("backend.routers.digital_twin.SessionLocal", test_db)
    monkeypatch.setattr("backend.routers.digital_twin.adapter_registry", registry)
    monkeypatch.setattr("backend.device_adapters.adapter_registry", registry)
    headers = {"Authorization": "Bearer test-token"}
    created = client.post("/api/v1/digital-twin/devices", headers=headers, json={
        "device_id": DEVICE_ID,
        "name": "Mega onboard LED",
        "kind": "actuator",
        "device_type": "onboard_led",
        "adapter_type": "serial",
        "control_mode": "manual",
        "state": {"output": "idle"},
    })
    assert created.status_code == 200, created.text

    on_response = client.post(
        f"/api/v1/digital-twin/devices/{created.json()['id']}/control",
        headers=headers,
        json={"command": "on"},
    )
    assert on_response.status_code == 200, on_response.text
    assert on_response.json()["state"]["output"] == "active"
    assert on_response.json()["state"]["last_command_delivery"]["confirmed"] is True

    off_response = client.post(
        f"/api/v1/digital-twin/devices/{created.json()['id']}/control",
        headers=headers,
        json={"command": "off"},
    )
    assert off_response.status_code == 200, off_response.text
    assert off_response.json()["state"]["output"] == "idle"
    assert from_backend.state == "OFF"
