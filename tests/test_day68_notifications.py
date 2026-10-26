import pytest
from fastapi.testclient import TestClient
from backend.models.digital_twin import DigitalTwinDevice


def test_notifications_create_list_evaluate_delete(client: TestClient):
    headers = {"Authorization": "Bearer test-token"}

    # Create a rule that always triggers
    payload = {"name": "rule-always", "condition": "always", "enabled": True}
    res = client.post('/api/v1/notifications/rules', json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()['data']
    rule_id = data['id']

    # List rules
    res = client.get('/api/v1/notifications/rules', headers=headers)
    assert res.status_code == 200
    rules = res.json()['data']
    assert any(r['id'] == rule_id for r in rules)

    # Evaluate rule
    res = client.post(f'/api/v1/notifications/rules/{rule_id}/evaluate', headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body['triggered'] is True
    alert_id = body.get('alert_id')
    assert alert_id is not None

    # Confirm alert exists via alerts list
    res = client.get('/api/v1/alerts', headers=headers)
    assert res.status_code == 200
    alerts = res.json()
    assert any(a['id'] == alert_id for a in alerts)

    # Delete rule
    res = client.delete(f'/api/v1/notifications/rules/{rule_id}', headers=headers)
    assert res.status_code == 200


def test_notification_rule_evaluates_tenant_sensor_state(client: TestClient, test_db):
    headers = {"Authorization": "Bearer test-token"}
    db = test_db()
    db.add(DigitalTwinDevice(
        tenant_id=1,
        device_id="soil-alert-test",
        name="Soil moisture test sensor",
        kind="sensor",
        device_type="soil_moisture",
        state={"value": 18.0, "unit": "%"},
    ))
    db.commit()
    db.close()

    create_response = client.post(
        "/api/v1/notifications/rules",
        json={
            "name": "low-soil-moisture",
            "condition": 'sensors["soil-alert-test"].value < 30',
            "enabled": True,
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    rule_id = create_response.json()["data"]["id"]

    evaluation = client.post(f"/api/v1/notifications/rules/{rule_id}/evaluate", headers=headers)

    assert evaluation.status_code == 200
    assert evaluation.json()["triggered"] is True


def test_delivery_provider_configuration_is_listed_without_secrets(client: TestClient):
    headers = {"Authorization": "Bearer test-token"}
    created = client.post(
        "/api/v1/notifications/delivery-configs",
        headers=headers,
        json={
            "provider": "webhook",
            "enabled": True,
            "config": {"endpoint": "https://alerts.example.invalid", "api_key": "private-value"},
        },
    )
    assert created.status_code == 200

    listed = client.get("/api/v1/notifications/delivery-configs", headers=headers)

    assert listed.status_code == 200
    config = next(row for row in listed.json()["data"] if row["id"] == created.json()["data"]["id"])
    assert config["config"]["api_key"] == "********"
    assert config["config"]["endpoint"] == "https://alerts.example.invalid"
