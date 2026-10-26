def test_password_change_verifies_current_password_and_updates_credentials(client):
    tenant = client.post("/api/v1/tenants", json={"name": "Password Tenant"})
    assert tenant.status_code == 200

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@aegis.com",
            "password": "old-password-123",
            "tenant_id": tenant.json()["id"],
            "role": "admin",
        },
    )
    assert registration.status_code == 200

    headers = {"Authorization": "Bearer test-token"}
    invalid_change = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "wrong-password", "new_password": "new-password-123"},
    )
    assert invalid_change.status_code == 400

    changed = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "old-password-123", "new_password": "new-password-123"},
    )
    assert changed.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aegis.com", "password": "new-password-123"},
    )
    assert login.status_code == 200