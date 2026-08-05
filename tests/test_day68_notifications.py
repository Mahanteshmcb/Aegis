import pytest
from fastapi.testclient import TestClient


def test_notifications_create_list_evaluate_delete(client: TestClient):
    # Create a rule that always triggers
    payload = {"name": "rule-always", "condition": "always", "enabled": True}
    res = client.post('/api/v1/notifications/rules', json=payload)
    assert res.status_code == 200
    data = res.json()['data']
    rule_id = data['id']

    # List rules
    res = client.get('/api/v1/notifications/rules')
    assert res.status_code == 200
    rules = res.json()['data']
    assert any(r['id'] == rule_id for r in rules)

    # Evaluate rule
    res = client.post(f'/api/v1/notifications/rules/{rule_id}/evaluate')
    assert res.status_code == 200
    body = res.json()
    assert body['triggered'] is True
    alert_id = body.get('alert_id')
    assert alert_id is not None

    # Confirm alert exists via alerts list
    res = client.get('/api/v1/alerts')
    assert res.status_code == 200
    alerts = res.json()
    assert any(a['id'] == alert_id for a in alerts)

    # Delete rule
    res = client.delete(f'/api/v1/notifications/rules/{rule_id}')
    assert res.status_code == 200
