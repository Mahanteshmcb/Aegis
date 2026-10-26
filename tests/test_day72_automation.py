import pytest

from backend import models_db
from backend.models.digital_twin import DigitalTwinDevice
from backend.services import automation, robot_worker


@pytest.mark.asyncio
async def test_process_sensor_reading_creates_alert(monkeypatch):
    calls = {}

    class DummyAlert:
        def __init__(self, id):
            self.id = id

    def dummy_create_system_alert(db, alert_payload):
        calls["created"] = True
        return DummyAlert(1)

    def dummy_get_sensor(db, sensor_id):
        class Sensor:
            id = sensor_id
            tenant_id = 1
            type = "soil_moisture"
        return Sensor()

    def dummy_get_tenant(db, tenant_id):
        class Tenant:
            settings = {}
        return Tenant()

    monkeypatch.setattr("backend.crud.create_system_alert", dummy_create_system_alert)
    monkeypatch.setattr("backend.crud.get_sensor", dummy_get_sensor)
    monkeypatch.setattr("backend.crud.get_tenant", dummy_get_tenant)

    await automation.process_sensor_reading({
        "sensor_id": 123,
        "value": 10.5,
        "type": "soil_moisture",
    })

    assert calls.get("created") is True


def test_robot_task_updates_persisted_tenant_robot(test_db):
    session = test_db()
    try:
        robot = DigitalTwinDevice(
            tenant_id=1,
            device_id="rover-main",
            name="Estate rover",
            kind="robot",
            device_type="rover",
            state={"activity": "stationary"},
        )
        task = models_db.ScheduledRoboticTask(
            tenant_id=1,
            task_id="inspect-north-zone",
            operation_type="inspect",
            requested_robot_id="rover-main",
            status="pending",
        )
        session.add_all([robot, task])
        session.commit()
        task_id = task.id

        assigned, assigned_robot = robot_worker._transition_task(session, task_id, "pending", "assigned")
        assert assigned.status == "assigned"
        assert assigned.assigned_robot_id == "rover-main"
        assert assigned_robot.state["active_task_id"] == "inspect-north-zone"

        running, running_robot = robot_worker._transition_task(session, task_id, "assigned", "in_progress")
        assert running.status == "in_progress"
        assert running_robot.state["activity"] == "working"

        completed, completed_robot = robot_worker._transition_task(session, task_id, "in_progress", "completed")
        assert completed.status == "completed"
        assert completed_robot.state["activity"] == "stationary"
        assert "active_task_id" not in completed_robot.state
        assert completed_robot.state["last_task"]["task_id"] == "inspect-north-zone"
    finally:
        session.close()


def test_robot_task_does_not_fall_back_to_another_tenant(test_db):
    session = test_db()
    try:
        session.add(DigitalTwinDevice(
            tenant_id=2,
            device_id="other-tenant-rover",
            name="Other tenant rover",
            kind="robot",
            device_type="rover",
        ))
        task = models_db.ScheduledRoboticTask(
            tenant_id=1,
            task_id="isolated-task",
            operation_type="inspect",
            status="pending",
        )
        session.add(task)
        session.commit()

        result = robot_worker._transition_task(session, task.id, "pending", "assigned")

        assert result[0].status == "conflicted"
        assert result[0].assigned_robot_id is None
        assert "No available tenant-owned" in result[0].conflict_reason
    finally:
        session.close()


def test_robot_stop_prevents_task_from_reporting_success(test_db):
    session = test_db()
    try:
        robot = DigitalTwinDevice(
            tenant_id=1,
            device_id="stoppable-rover",
            name="Stoppable rover",
            kind="robot",
            device_type="rover",
            state={"activity": "stationary"},
        )
        task = models_db.ScheduledRoboticTask(
            tenant_id=1,
            task_id="stop-during-task",
            operation_type="inspect",
            requested_robot_id="stoppable-rover",
            status="pending",
        )
        session.add_all([robot, task])
        session.commit()

        assigned, assigned_robot = robot_worker._transition_task(session, task.id, "pending", "assigned")
        assigned_robot.state = {"command": "stop", "activity": "stopped"}
        session.commit()

        conflicted, updated_robot = robot_worker._transition_task(
            session,
            task.id,
            "assigned",
            "in_progress",
        )

        assert conflicted.status == "conflicted"
        assert "no longer owns" in conflicted.conflict_reason
        assert updated_robot is None
    finally:
        session.close()
