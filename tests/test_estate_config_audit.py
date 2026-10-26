def test_estate_device_lifecycle_is_audited(client):
    headers = {"Authorization": "Bearer test-token"}
    device_id = "phase4-audit-device"

    created = client.post(
        "/api/v1/estate-config/devices",
        headers=headers,
        json={"device_id": device_id, "type": "sensor", "status": "active"},
    )
    assert created.status_code == 200, created.text

    updated = client.put(
        f"/api/v1/estate-config/devices/{device_id}",
        headers=headers,
        json={"status": "offline"},
    )
    assert updated.status_code == 200, updated.text

    deleted = client.delete(
        f"/api/v1/estate-config/devices/{device_id}",
        headers=headers,
    )
    assert deleted.status_code == 200, deleted.text

    response = client.get("/api/v1/audit?limit=100", headers=headers)
    assert response.status_code == 200, response.text
    events = [
        event for event in response.json()
        if event["entity_type"] == "estate_device"
        and event["entity_id"] == device_id
    ]
    events.sort(key=lambda event: event["id"])
    assert [event["event_type"] for event in events] == [
        "estate_device_created",
        "estate_device_updated",
        "estate_device_deleted",
    ]
    assert all(event["actor_email"] == "admin@aegis.com" for event in events)
    assert all(event["outcome"] == "success" for event in events)
