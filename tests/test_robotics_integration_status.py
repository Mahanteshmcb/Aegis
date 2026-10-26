from unittest.mock import MagicMock


def test_robotics_integrations_report_simulation_and_disabled_ros2(client, monkeypatch):
    fleet = MagicMock()
    fleet.address = "localhost:50053"
    fleet.is_connected = True
    monkeypatch.setattr("backend.routers.robotics.get_robotics_connector", lambda: fleet)

    vryndara = MagicMock()
    vryndara.health_check.return_value = False
    monkeypatch.setattr("backend.routers.research.get_vryndara_connector", lambda: vryndara)

    response = client.get(
        "/api/v1/robotics/integrations",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["execution_mode"] == "simulation"
    assert result["fleet_grpc"]["connected"] is True
    assert result["vryndara_grpc"]["connected"] is False
    assert result["ros2"]["hardware_control_enabled"] is False
    assert "safety limits" in result["ros2"]["reason"]
