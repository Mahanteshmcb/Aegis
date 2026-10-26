def test_current_tenant_settings_are_tenant_scoped_and_admin_writable(client):
    tenant_response = client.post("/api/v1/tenants", json={"name": "Settings Tenant"})
    assert tenant_response.status_code == 200

    headers = {"Authorization": "Bearer test-token"}
    read_response = client.get("/api/v1/tenants/me", headers=headers)
    assert read_response.status_code == 200
    assert read_response.json()["name"] == "Settings Tenant"

    update_response = client.put(
        "/api/v1/tenants/me",
        headers=headers,
        json={
            "name": "Updated Settings Tenant",
            "settings": {"automation": {"soil_moisture_threshold": 27.5}},
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Updated Settings Tenant"
    assert updated["settings"]["automation"]["soil_moisture_threshold"] == 27.5

    audit_response = client.get("/api/v1/audit?limit=100", headers=headers)
    assert audit_response.status_code == 200, audit_response.text
    tenant_events = [
        event for event in audit_response.json()
        if event["entity_type"] == "tenant"
        and event["entity_id"] == str(tenant_response.json()["id"])
    ]
    assert {event["event_type"] for event in tenant_events} >= {
        "tenant_created", "tenant_updated"
    }
    updated_event = next(event for event in tenant_events if event["event_type"] == "tenant_updated")
    assert updated_event["actor_email"] == "admin@aegis.com"


def test_current_tenant_settings_require_authentication(client):
    assert client.get("/api/v1/tenants/me").status_code == 401
    assert client.put("/api/v1/tenants/me", json={"name": "Unauthenticated"}).status_code == 401