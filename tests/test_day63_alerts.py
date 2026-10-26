"""Day 63: Alert API tests."""

import pytest


@pytest.fixture
def token(client):
    return "test-token"


def test_create_alert(client, token):
    response = client.post(
        "/api/v1/alerts",
        json={
            "alert_type": "fleet_efficiency",
            "severity": "warning",
            "title": "Test Alert",
            "message": "Integration test alert",
            "source": "system",
            "data": {"test": True},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    alert = response.json()
    assert alert.get("id") is not None
    assert alert.get("alert_type") == "fleet_efficiency"


def test_list_alerts(client, token):
    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_acknowledge_alert(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/alerts",
        json={
            "alert_type": "robot_health",
            "severity": "critical",
            "title": "Ack Test",
            "message": "Test acknowledgment",
            "source": "robot_1",
            "data": {},
        },
        headers=headers,
    )
    assert created.status_code == 200, created.text

    acknowledged = client.post(
        f"/api/v1/alerts/{created.json()['id']}/ack",
        headers=headers,
    )
    assert acknowledged.status_code == 200, acknowledged.text
    assert acknowledged.json().get("acknowledged") is True


def test_filter_alerts(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/alerts",
        json={
            "alert_type": "safety_incident",
            "severity": "high",
            "title": "Filter Test",
            "message": "Test filtering",
            "source": "zone_1",
            "data": {},
        },
        headers=headers,
    )
    assert created.status_code == 200, created.text

    response = client.get(
        "/api/v1/alerts",
        params={"alert_type": "safety_incident", "severity": "high"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    alerts = response.json()
    assert any(alert["id"] == created.json()["id"] for alert in alerts)
