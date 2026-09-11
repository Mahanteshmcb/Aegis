from contextlib import nullcontext

import pytest
from fastapi import HTTPException

from backend.routers import digital_twin
from backend.services.digital_twin import tick_once


class User:
    def __init__(self, tenant_id, role):
        self.tenant_id = tenant_id
        self.role = role


def test_day85_operator_workflow_is_tenant_scoped(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")
    other_tenant = User(tenant_id=2, role="operator")

    created = digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day85-pump",
            name="Day 85 irrigation pump",
            kind="actuator",
            device_type="pump",
            state={"output": "idle"},
        ),
        operator,
    )

    health_before = digital_twin.twin_health(operator)
    assert health_before["devices"] == 1
    assert health_before["active_actuators"] == 0

    controlled = digital_twin.control_device(
        created["id"],
        digital_twin.DeviceControl(command="start", parameters={"flow": 18}),
        operator,
    )
    assert controlled["state"] == {"output": "idle", "command": "start", "flow": 18}

    with pytest.raises(HTTPException) as error:
        digital_twin.control_device(
            created["id"],
            digital_twin.DeviceControl(command="stop"),
            other_tenant,
        )
    assert error.value.status_code == 404

    snapshots = tick_once(db, tenant_id=operator.tenant_id)
    assert snapshots[0]["device_id"] == "day85-pump"
