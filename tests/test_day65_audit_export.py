from unittest.mock import MagicMock

from backend import crud, schemas
from backend.crud import create_audit_log_with_transaction
from backend.blockchain_connector import BlockchainConnector
from backend.audit_utils import record_actor_audit_event
BASE = "/api/v1"


def setup_tenant_and_admin(test_db):
    SessionLocal = test_db
    db = SessionLocal()
    tenant = crud.create_tenant(db, schemas.TenantCreate(name="Audit Tenant"))
    admin = crud.create_user(
        db,
        schemas.UserCreate(email="admin@audit.com", password="admin1234", tenant_id=tenant.id, role="admin")
    )
    return db, tenant, admin


def test_audit_export(client, test_db):
    db, tenant, admin = setup_tenant_and_admin(test_db)
    headers = {"Authorization": "Bearer test-token"}

    # create a few audit logs
    for i in range(3):
        create_audit_log_with_transaction(db, event_type="user_created", data_hash=f"h{i}", tenant_id=tenant.id)
    record_actor_audit_event(
        db,
        tenant.id,
        {"id": admin.id, "email": admin.email},
        "zone_updated",
        "zone",
        "zone-12",
        {"changed_fields": ["location"]},
    )

    r = client.get(f"{BASE}/audit/export", headers=headers)
    assert r.status_code == 200
    text = r.text
    assert "actor_email" in text
    assert "entity_type" in text
    assert "details" in text
    assert "admin@audit.com" in text
    assert "zone-12" in text

    db.close()


def test_audit_submission_returns_transaction_hash_not_event_id(monkeypatch):
    transaction_hash = MagicMock()
    transaction_hash.hex.return_value = "0xactual-transaction-hash"
    signed_transaction = MagicMock(raw_transaction=b"signed")
    contract = MagicMock()
    transaction = contract.functions.createLog.return_value
    transaction.estimate_gas.return_value = 21000
    connector = BlockchainConnector.__new__(BlockchainConnector)
    connector.contract = contract
    connector.account = "0xaccount"
    connector.private_key = "test-key"
    connector.w3 = MagicMock()
    connector.w3.eth.account.sign_transaction.return_value = signed_transaction
    connector.w3.eth.send_raw_transaction.return_value = transaction_hash
    connector.w3.eth.wait_for_transaction_receipt.return_value = MagicMock(status=1)
    connector.w3.eth.gas_price = 1
    connector.w3.eth.get_transaction_count.return_value = 1
    monkeypatch.setattr("backend.blockchain_monitor.get_blockchain_monitor", lambda _connector: MagicMock())

    result = connector.submit_audit_log("asset_updated", "data-hash", "{}", 1)

    assert result == "0xactual-transaction-hash"
