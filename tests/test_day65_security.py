from datetime import datetime
from backend.models_db import Tenant


def create_tenant(session):
    tenant = Tenant(name=f"Security Tenant {datetime.utcnow().timestamp()}")
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


def test_perimeter_lockdown_flow(client, test_db):
    db = test_db()
    tenant = create_tenant(db)

    response = client.post('/api/v1/safety/perimeter/lockdown', json={'reason': 'Test lockdown'})
    assert response.status_code == 200
    data = response.json()
    assert data['active'] is True
    assert data['reason'] == 'Test lockdown'

    status_response = client.get('/api/v1/safety/perimeter')
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data['active'] is True

    release_response = client.post('/api/v1/safety/perimeter/release')
    assert release_response.status_code == 200
    released = release_response.json()
    assert released['active'] is False


def test_biometric_access_logs(client, test_db):
    db = test_db()
    tenant = create_tenant(db)

    payload = {
        'user_name': 'operator@aegis.com',
        'scan_id': 'BIO-ACCESS-123',
        'biometric_type': 'fingerprint',
        'location': 'Main Gate',
    }
    response = client.post('/api/v1/safety/access/biometric', json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert result['status'] == 'granted'
    assert 'event_id' in result

    logs_response = client.get('/api/v1/safety/access/logs')
    assert logs_response.status_code == 200
    logs = logs_response.json()
    assert any(log['status'] == 'granted' for log in logs)
    assert any('Biometric access granted' in log['message'] for log in logs)


def test_robotic_patrol_and_evacuation_protocol(client, test_db):
    db = test_db()
    tenant = create_tenant(db)

    start_response = client.post('/api/v1/safety/patrols/start', json={
        'route_name': 'Perimeter Sweep Bravo',
        'assigned_robot': 'Patrol Rover 001',
        'zone_sequence': ['Gate House', 'Northeast Watch', 'South Gate'],
    })
    assert start_response.status_code == 200
    patrol_data = start_response.json()
    assert patrol_data['active'] is True
    assert patrol_data['status'] == 'patrolling'

    status_response = client.get('/api/v1/safety/patrols/status')
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data['active'] is True
    assert status_data['route_name'] == 'Perimeter Sweep Bravo'

    stop_response = client.post('/api/v1/safety/patrols/stop')
    assert stop_response.status_code == 200
    stopped_data = stop_response.json()
    assert stopped_data['active'] is False
    assert stopped_data['status'] == 'completed'

    trigger_response = client.post('/api/v1/safety/evacuation/trigger', json={
        'incident_type': 'security breach',
        'affected_zones': ['Gate House', 'Control Center'],
        'reason': 'Automated test evacuation',
    })
    assert trigger_response.status_code == 200
    evac_data = trigger_response.json()
    assert evac_data['active'] is True
    assert evac_data['stage'] == 'initiated'
    assert 'Activate perimeter lockdown' in evac_data['instructions']

    evac_status_response = client.get('/api/v1/safety/evacuation')
    assert evac_status_response.status_code == 200
    evac_status = evac_status_response.json()
    assert evac_status['active'] is True
    assert evac_status['incident_type'] == 'security breach'

    complete_response = client.post('/api/v1/safety/evacuation/complete')
    assert complete_response.status_code == 200
    complete_data = complete_response.json()
    assert complete_data['active'] is False
    assert complete_data['stage'] == 'completed'
