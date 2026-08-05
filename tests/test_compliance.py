import pytest


def register_and_login_admin(client):
    user_data = {
        "email": "compliance-admin@example.com",
        "password": "testpass",
        "tenant_id": 1,
        "role": "admin",
    }
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"],
        "tenant_id": user_data["tenant_id"],
        "role": user_data["role"],
    }
    resp = client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class MockBlockchain:
    def __init__(self):
        self.submitted = []

    def submit_requirement_request(self, event_type, data_hash, metadata, tenant_id):
        self.submitted.append({
            "event_type": event_type,
            "data_hash": data_hash,
            "metadata": metadata,
            "tenant_id": tenant_id,
        })
        return "0xdeadbeef" + "0" * 56

    def get_compliance_summary(self, tenant_id):
        return {
            "total_logs": 1,
            "verified_logs": 0,
            "critical_logs": 0,
            "emergency_logs": 0,
        }


def test_organic_certification_request_and_status(client, monkeypatch):
    headers = register_and_login_admin(client)
    mock_blockchain = MockBlockchain()
    import backend.routers.audit as audit_router
    from backend.main import app

    app.dependency_overrides[audit_router.get_blockchain_connector] = lambda: mock_blockchain

    try:
        request_payload = {
        "details": "Organic certification requested for greenhouse crop cycle 4.",
        "certification_level": "organic",
    }

        response = client.post(
            "/api/v1/audit/compliance/organic-certification/request",
            json=request_payload,
            headers=headers,
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["success"] is True
        assert result["transaction_hash"].startswith("0x")
        assert isinstance(result["audit_log_id"], int)

        status_response = client.get(
            "/api/v1/audit/compliance/organic-certification/1",
            headers=headers,
        )
        assert status_response.status_code == 200, status_response.text
        status_data = status_response.json()
        assert status_data["tenant_id"] == 1
        assert status_data["organic_certification_requests"] == 1
        assert status_data["compliance_summary"]["total_logs"] == 1
    finally:
        app.dependency_overrides.clear()
