import pytest

from backend.models_db import AuditLog
from fastapi import HTTPException

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
        audit = client.get("/api/v1/audit?limit=10", headers=headers)
        assert audit.status_code == 200, audit.text
        certification = next(
            event for event in audit.json()
            if event["event_type"] == "organic_certification_request"
        )
        assert certification["actor_email"] == "compliance-admin@example.com"
        assert certification["entity_type"] == "compliance_requirement"
        assert certification["blockchain_tx"].startswith("0x")
    finally:
        app.dependency_overrides.clear()


def test_audit_tenant_access_only_allows_same_tenant_or_superadmin():
    import backend.routers.audit as audit_router

    audit_router._ensure_audit_tenant_access(
        {"tenant_id": 1, "role": "admin"}, 1
    )
    audit_router._ensure_audit_tenant_access(
        {"tenant_id": 1, "role": "superadmin"}, 2
    )
    with pytest.raises(HTTPException) as error:
        audit_router._ensure_audit_tenant_access(
            {"tenant_id": 1, "role": "admin"}, 2
        )
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_blockchain_audit_query_reports_unavailable_without_leaking_provider_error():
    import backend.routers.audit as audit_router

    class UnavailableBlockchain:
        def get_blockchain_logs(self, **kwargs):
            raise RuntimeError("provider internals")

    with pytest.raises(HTTPException) as error:
        await audit_router.list_blockchain_audit_logs(
            tenant_id=None,
            event_type=None,
            limit=50,
            blockchain=UnavailableBlockchain(),
            current_user={"tenant_id": 1, "role": "auditor"},
        )

    assert error.value.status_code == 503
    assert error.value.detail == "Blockchain audit query is unavailable"
    assert "provider internals" not in error.value.detail


@pytest.mark.asyncio
async def test_compliance_summary_falls_back_to_all_time_local_audit_metrics(test_db):
    db = test_db()
    db.add_all([
        AuditLog(
            tenant_id=1,
            event_type="device_commanded",
            action="device_commanded",
            outcome="success",
            details={"severity": "critical"},
            blockchain_tx="0xabc",
        ),
        AuditLog(
            tenant_id=1,
            event_type="emergency_stop",
            action="emergency_stop",
            outcome="success",
            details={},
        ),
        AuditLog(
            tenant_id=2,
            event_type="emergency_stop",
            action="emergency_stop",
            outcome="success",
            details={"severity": "emergency"},
        ),
    ])
    db.commit()
    db.close()

    class UnavailableBlockchain:
        def get_compliance_summary(self, tenant_id):
            return {"error": "Contract not loaded"}

    import backend.routers.audit as audit_router
    payload = await audit_router.get_tenant_compliance_summary(
        tenant_id=1,
        db=db,
        blockchain=UnavailableBlockchain(),
        current_user={"tenant_id": 1, "role": "auditor"},
    )
    db.close()

    assert payload["blockchain_error"] == "Contract not loaded"
    assert payload["database_summary"] == {
        "total_logs": 2,
        "transaction_references": 1,
        "critical_logs": 1,
        "emergency_logs": 1,
    }
    assert payload["compliance_summary"]["error"] == "Contract not loaded"
