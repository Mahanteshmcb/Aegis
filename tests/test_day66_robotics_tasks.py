import pytest
from fastapi.testclient import TestClient
from backend import crud


def test_enqueue_list_assign_and_cancel(client: TestClient):
    headers = {"Authorization": "Bearer test-token"}

    # Enqueue a pending task
    payload = {
        "task_id": "task-66-1",
        "operation_type": "patrol",
        "robot_id": None,
        "zone_id": None,
        "priority": 5,
        "task_detail": {},
        "timeout_seconds": 60,
        "metadata": {},
    }

    res = client.post('/api/v1/robotics/schedule/enqueue', json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'success'
    assert data['data']['task_id'] == 'task-66-1'

    # Verify queue contains the task
    res = client.get('/api/v1/robotics/schedule/queue', headers=headers)
    assert res.status_code == 200
    q = res.json()
    tasks = q['data']['tasks']
    assert any(t['task_id'] == 'task-66-1' for t in tasks)

    # Assign pending tasks (should process without error)
    res = client.post('/api/v1/robotics/schedule/assign', headers=headers)
    assert res.status_code == 200
    assigned = res.json()
    assert assigned['status'] == 'success'

    # Enqueue another task and cancel it while pending
    payload['task_id'] = 'task-66-2'
    res = client.post('/api/v1/robotics/schedule/enqueue', json=payload, headers=headers)
    assert res.status_code == 200

    # Cancel pending task
    res = client.delete('/api/v1/robotics/schedule/cancel/task-66-2', headers=headers)
    assert res.status_code == 200
    cancelled = res.json()
    assert cancelled['status'] == 'success'
    assert cancelled['data']['task_id'] == 'task-66-2'
