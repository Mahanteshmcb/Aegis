from contextlib import nullcontext

import pytest
from fastapi import HTTPException

from backend.routers import digital_twin
from backend.services import digital_twin as digital_twin_service
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


def test_day86_predictive_maintenance_recommendations(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day86-sensor",
            name="Day 86 soil probe",
            kind="sensor",
            device_type="soil_moisture",
            state={"value": 14.0, "reading_status": "critical"},
        ),
        operator,
    )
    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day86-pump",
            name="Day 86 irrigation pump",
            kind="actuator",
            device_type="pump",
            state={"output": "active"},
        ),
        operator,
    )

    health = digital_twin.twin_health(operator)

    assert "recommendations" in health
    assert isinstance(health["recommendations"], list)
    assert health["recommendations"]
    assert any(item["focus"] == "soil_moisture" for item in health["recommendations"])
    assert any(item["type"] == "maintenance" for item in health["recommendations"])


def test_day87_optimization_recommendations(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day87-soil",
            name="Day 87 soil sensor",
            kind="sensor",
            device_type="soil_moisture",
            state={"value": 18.0, "reading_status": "warning"},
        ),
        operator,
    )
    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day87-energy",
            name="Day 87 inverter",
            kind="sensor",
            device_type="power",
            state={"value": 91.0, "reading_status": "warning"},
        ),
        operator,
    )

    health = digital_twin.twin_health(operator)

    assert "optimization" in health
    assert isinstance(health["optimization"], list)
    assert health["optimization"]
    assert any(item["domain"] == "soil" for item in health["optimization"])
    assert any(item["domain"] == "energy" for item in health["optimization"])


def test_day88_weather_resource_adaptation(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day88-temp",
            name="Day 88 thermal sensor",
            kind="sensor",
            device_type="temperature",
            state={"value": 7.0, "reading_status": "warning"},
        ),
        operator,
    )
    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day88-power",
            name="Day 88 battery monitor",
            kind="sensor",
            device_type="power",
            state={"value": 88.0, "reading_status": "warning"},
        ),
        operator,
    )

    health = digital_twin.twin_health(operator)

    assert "adaptation" in health
    assert isinstance(health["adaptation"], list)
    assert health["adaptation"]
    assert any(item["domain"] == "weather" for item in health["adaptation"])
    assert any(item["domain"] == "resource" for item in health["adaptation"])


def test_day89_recommendation_and_alert_summaries(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day89-soil",
            name="Day 89 soil sensor",
            kind="sensor",
            device_type="soil_moisture",
            state={"value": 16.0, "reading_status": "warning"},
        ),
        operator,
    )
    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day89-power",
            name="Day 89 battery monitor",
            kind="sensor",
            device_type="battery",
            state={"value": 87.0, "reading_status": "critical"},
        ),
        operator,
    )

    health = digital_twin.twin_health(operator)

    assert "recommendation_summary" in health
    assert "alert_summary" in health
    assert isinstance(health["recommendation_summary"], dict)
    assert isinstance(health["alert_summary"], dict)
    assert health["recommendation_summary"]["total"] >= 1
    assert health["alert_summary"]["total"] >= 1
    assert health["recommendation_summary"]["top_actions"]


def test_day90_multiple_live_updates_remain_stable(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    for idx in range(6):
        digital_twin.create_device(
            digital_twin.DeviceCreate(
                device_id=f"day90-sensor-{idx}",
                name=f"Day 90 sensor {idx}",
                kind="sensor",
                device_type="temperature" if idx % 2 == 0 else "humidity",
                state={"value": 22.0 + idx, "reading_status": "normal"},
            ),
            operator,
        )

    for _ in range(8):
        snapshots = tick_once(db, tenant_id=operator.tenant_id)
        assert isinstance(snapshots, list)
        assert snapshots

    health = digital_twin.twin_health(operator)

    assert "stability" in health
    assert isinstance(health["stability"], dict)
    assert health["stability"]["stable"] is True
    assert health["stability"]["updates_processed"] >= 8


def test_day91_integration_workflow_summary(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day91-soil",
            name="Day 91 soil sensor",
            kind="sensor",
            device_type="soil_moisture",
            state={"value": 18.0, "reading_status": "warning"},
        ),
        operator,
    )
    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day91-power",
            name="Day 91 power sensor",
            kind="sensor",
            device_type="power",
            state={"value": 86.0, "reading_status": "warning"},
        ),
        operator,
    )

    health = digital_twin.twin_health(operator)

    assert "workflow" in health
    assert isinstance(health["workflow"], dict)
    assert health["workflow"]["status"] in {"healthy", "degraded", "critical"}
    assert health["workflow"]["modules"]["predictive"]["count"] >= 1
    assert health["workflow"]["modules"]["optimization"]["count"] >= 1
    assert health["workflow"]["summary"]


def test_day92_api_session_and_error_state(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day92-sensor",
            name="Day 92 runtime sensor",
            kind="sensor",
            device_type="temperature",
            state={"value": 22.0, "reading_status": "normal"},
        ),
        operator,
    )

    health = digital_twin.twin_health(operator)

    assert "api_status" in health
    assert "session" in health
    assert isinstance(health["api_status"], dict)
    assert isinstance(health["session"], dict)
    assert health["api_status"]["status"] in {"ok", "degraded"}
    assert health["session"]["tenant_id"] == operator.tenant_id
    assert health["session"]["active"] is True
    assert isinstance(health["api_status"]["errors"], list)


def test_day94_multi_system_interactions(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day94-temp",
            name="Day 94 climate sensor",
            kind="sensor",
            device_type="temperature",
            state={"value": 23.0, "reading_status": "normal"},
        ),
        operator,
    )
    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day94-soil",
            name="Day 94 soil sensor",
            kind="sensor",
            device_type="soil_moisture",
            state={"value": 40.0, "reading_status": "normal"},
        ),
        operator,
    )
    digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="day94-power",
            name="Day 94 power sensor",
            kind="sensor",
            device_type="power",
            state={"value": 65.0, "reading_status": "warning"},
        ),
        operator,
    )

    health = digital_twin.twin_health(operator)

    assert "interaction_summary" in health
    assert isinstance(health["interaction_summary"], dict)
    assert health["interaction_summary"]["system_count"] >= 2
    assert health["interaction_summary"]["coordinated"] is True
    assert health["interaction_summary"]["status"] in {"coordinated", "stable", "degraded"}
    assert isinstance(health["interaction_summary"]["systems"], list)
    assert health["interaction_summary"]["systems"]


def test_day95_edge_case_resilience(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    operator = User(tenant_id=1, role="operator")

    empty_interaction = digital_twin_service.build_interaction_summary([])
    assert empty_interaction["coordinated"] is False
    assert empty_interaction["system_count"] == 0
    assert empty_interaction["status"] in {"idle", "stable", "watch"}

    critical_status = digital_twin_service.build_api_status(30, [], {"total": 3})
    assert critical_status["status"] == "critical"
    assert any("No digital-twin devices" in error for error in critical_status["errors"])

    health = digital_twin.twin_health(operator)
    assert "api_status" in health
    assert health["api_status"]["status"] in {"ok", "degraded", "critical"}
