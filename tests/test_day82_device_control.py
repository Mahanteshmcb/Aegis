from contextlib import nullcontext

import pytest
from fastapi import HTTPException

from backend.models.digital_twin import DigitalTwinDevice
from backend.routers import digital_twin


class User:
    def __init__(self, tenant_id, role):
        self.tenant_id = tenant_id
        self.role = role


def test_day82_operator_control_updates_device_state(db, monkeypatch):
    device = DigitalTwinDevice(
        tenant_id=1,
        device_id="control-pump-1",
        name="Control pump",
        kind="actuator",
        device_type="pump",
    )
    db.add(device)
    db.commit()
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))

    result = digital_twin.control_device(
        device.id,
        digital_twin.DeviceControl(command="start", parameters={"flow": 24}),
        User(tenant_id=1, role="operator"),
    )

    assert result["state"] == {"command": "start", "flow": 24}
    assert result["status"] == "online"


def test_day82_control_rejects_unsupported_command_and_role(db, monkeypatch):
    device = DigitalTwinDevice(
        tenant_id=1,
        device_id="control-pump-2",
        name="Protected pump",
        kind="actuator",
        device_type="pump",
    )
    db.add(device)
    db.commit()
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))

    with pytest.raises(HTTPException) as command_error:
        digital_twin.control_device(
            device.id,
            digital_twin.DeviceControl(command="format_disk"),
            User(tenant_id=1, role="operator"),
        )
    assert command_error.value.status_code == 422

    with pytest.raises(HTTPException) as role_error:
        digital_twin.control_device(
            device.id,
            digital_twin.DeviceControl(command="stop"),
            User(tenant_id=1, role="auditor"),
        )
    assert role_error.value.status_code == 403
