from unittest.mock import MagicMock

from backend.blockchain_connector import BlockchainConnector


def test_connector_loads_address_from_local_deployment(monkeypatch):
    monkeypatch.delenv("CONTRACT_ADDRESS", raising=False)
    connector = BlockchainConnector()

    assert connector.contract_address == "0x5FbDB2315678afecb367f032d93F642f64180aa3"


def test_get_blockchain_logs_reads_tenant_records_and_formats_contract_fields():
    log_id = b"\x01" * 32
    log_entry = (
        3,
        1_750_000_000,
        "0xactor",
        "EMERGENCY",
        b"\x02" * 32,
        '{"severity":"emergency"}',
        7,
        3,
        True,
        False,
    )
    connector = BlockchainConnector.__new__(BlockchainConnector)
    connector.contract_load_error = None
    connector.contract = MagicMock()
    connector.contract.functions.getTenantLogs.return_value.call.return_value = [log_id]
    connector.contract.functions.getLog.return_value.call.return_value = log_entry

    result = connector.get_blockchain_logs(tenant_id=7)

    assert result == [{
        "id": "0x" + "01" * 32,
        "log_index": 3,
        "timestamp": 1_750_000_000,
        "actor": "0xactor",
        "event_type": "EMERGENCY",
        "data_hash": "0x" + "02" * 32,
        "metadata": '{"severity":"emergency"}',
        "tenant_id": 7,
        "severity": 3,
        "verified": True,
        "archived": False,
    }]
    connector.contract.functions.getTenantLogs.assert_called_once_with(7)


def test_send_transaction_uses_unlocked_account_only_for_local_development():
    connector = BlockchainConnector.__new__(BlockchainConnector)
    connector.private_key = None
    connector.use_unlocked_account = True
    connector.account = "0xlocal-account"
    connector.w3 = MagicMock()
    transaction = MagicMock()
    tx_hash = MagicMock()
    tx_hash.hex.return_value = "0xtransaction"
    receipt = MagicMock(status=1)
    transaction.transact.return_value = tx_hash
    connector.w3.eth.wait_for_transaction_receipt.return_value = receipt

    submitted_hash, submitted_receipt = connector._send_transaction(transaction)

    transaction.transact.assert_called_once_with({"from": "0xlocal-account"})
    assert submitted_hash is tx_hash
    assert submitted_receipt is receipt
