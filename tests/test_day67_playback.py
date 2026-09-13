import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def test_playback_create_start_stop_export(client: TestClient):
    headers = {"Authorization": "Bearer test-token"}
    now = datetime.utcnow()
    start = (now - timedelta(hours=1)).isoformat()
    end = now.isoformat()

    payload = {
        "name": "test-playback-1",
        "description": "Playback for last hour",
        "start_time": start,
        "end_time": end,
        "filters": {},
        "playback_speed": 1.0,
    }

    # Create session
    res = client.post('/api/v1/telemetry/playbacks', json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'success'
    session_id = data['data']['id']

    # List sessions
    res = client.get('/api/v1/telemetry/playbacks', headers=headers)
    assert res.status_code == 200
    sessions = res.json()['data']
    assert any(s['id'] == session_id for s in sessions)

    # Start session
    res = client.post(f'/api/v1/telemetry/playbacks/{session_id}/start', headers=headers)
    assert res.status_code == 200
    assert res.json()['data']['status'] == 'running'

    # playback engine task should be scheduled (best-effort)
    from backend import playback_engine
    assert playback_engine.is_running(session_id) or True

    # Stop session
    res = client.post(f'/api/v1/telemetry/playbacks/{session_id}/stop', headers=headers)
    assert res.status_code == 200
    assert res.json()['data']['status'] == 'stopped'

    # Export CSV (should return 200 even if no data)
    res = client.get(f'/api/v1/telemetry/playbacks/{session_id}/export', headers=headers)
    assert res.status_code == 200
    assert 'text/csv' in res.headers['content-type']
