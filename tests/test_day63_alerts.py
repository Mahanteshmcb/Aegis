import requests
import json
import pytest

BASE = 'http://127.0.0.1:8001'


@pytest.fixture(scope="function")
def token():
    """Get auth token for testing"""
    resp = requests.post(f"{BASE}/api/v1/auth/login", json={"email":"admin@aegis.com","password":"admin1234"})
    resp.raise_for_status()
    return resp.json().get('access_token')


def test_create_alert(token):
    """Test: POST /api/v1/alerts"""
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        "alert_type": "fleet_efficiency",
        "severity": "warning",
        "title": "Test Alert",
        "message": "Integration test alert",
        "source": "system",
        "data": {"test": True}
    }
    r = requests.post(f"{BASE}/api/v1/alerts", json=payload, headers=headers)
    assert r.status_code == 200, f"Create alert failed: {r.text}"
    alert = r.json()
    assert alert.get('id') is not None
    assert alert.get('alert_type') == 'fleet_efficiency'
    print("✅ Alert created successfully")
    return alert


def test_list_alerts(token):
    """Test: GET /api/v1/alerts"""
    headers = {'Authorization': f'Bearer {token}'}
    
    r = requests.get(f"{BASE}/api/v1/alerts", headers=headers)
    assert r.status_code == 200, f"List alerts failed: {r.text}"
    alerts = r.json()
    assert isinstance(alerts, list)
    print("✅ Alerts listed successfully")


def test_acknowledge_alert(token):
    """Test: POST /api/v1/alerts/{alert_id}/ack"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # First create an alert
    payload = {
        "alert_type": "robot_health",
        "severity": "critical",
        "title": "Ack Test",
        "message": "Test acknowledgment",
        "source": "robot_1",
        "data": {}
    }
    r = requests.post(f"{BASE}/api/v1/alerts", json=payload, headers=headers)
    assert r.status_code == 200
    alert_id = r.json().get('id')
    
    # Now acknowledge it
    r2 = requests.post(f"{BASE}/api/v1/alerts/{alert_id}/ack", headers=headers)
    assert r2.status_code == 200, f"Acknowledge failed: {r2.text}"
    ack_alert = r2.json()
    assert ack_alert.get('acknowledged') == True
    print("✅ Alert acknowledged successfully")


def test_filter_alerts(token):
    """Test: GET /api/v1/alerts with filters"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Create alert with specific type and severity
    payload = {
        "alert_type": "safety_incident",
        "severity": "high",
        "title": "Filter Test",
        "message": "Test filtering",
        "source": "zone_1",
        "data": {}
    }
    r = requests.post(f"{BASE}/api/v1/alerts", json=payload, headers=headers)
    assert r.status_code == 200
    
    # List with filter
    r2 = requests.get(f"{BASE}/api/v1/alerts?alert_type=safety_incident&severity=high", headers=headers)
    assert r2.status_code == 200, f"Filter failed: {r2.text}"
    alerts = r2.json()
    assert isinstance(alerts, list)
    # At least our newly created alert should be in the results
    assert len(alerts) > 0
    print("✅ Alerts filtered successfully")


def run():
    token = login()
    headers = {'Authorization': f'Bearer {token}'}

    # Create an alert
    payload = {"system": "climate", "severity": "warning", "title": "Test Alert", "message": "Integration test"}
    r = requests.post(f"{BASE}/api/v1/alerts", json=payload, headers=headers)
    print('create status', r.status_code, r.text)
    r.raise_for_status()
    alert = r.json()
    alert_id = alert['id']

    # List alerts
    r2 = requests.get(f"{BASE}/api/v1/alerts?system=climate", headers=headers)
    print('list status', r2.status_code)
    print(r2.json())

    # Ack alert
    r3 = requests.post(f"{BASE}/api/v1/alerts/{alert_id}/ack", headers=headers)
    print('ack status', r3.status_code, r3.json())

    # Resolve alert
    r4 = requests.post(f"{BASE}/api/v1/alerts/{alert_id}/resolve", headers=headers)
    print('resolve status', r4.status_code, r4.json())
