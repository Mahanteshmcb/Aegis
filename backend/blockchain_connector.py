"""
AEGIS Backend - Blockchain Integration Module
Handles communication with the AegisAudit smart contract on the private blockchain network.
"""

import os
import json
import logging
import ssl
import ipaddress
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

# Optional imports for blockchain functionality
try:
    from web3 import Web3
    from web3.contract import Contract
    from web3.exceptions import ContractLogicError
    from eth_account import Account
    WEB3_AVAILABLE = True
except Exception as e:
    if isinstance(e, ssl.SSLError) and os.name == "nt":
        original_create_default_context = ssl.create_default_context
        try:
            import certifi

            def create_default_context_with_certifi(*args, **kwargs):
                if not kwargs.get("cafile") and not kwargs.get("capath") and not kwargs.get("cadata"):
                    kwargs["cafile"] = certifi.where()
                return original_create_default_context(*args, **kwargs)

            ssl.create_default_context = create_default_context_with_certifi
            from web3 import Web3
            from web3.contract import Contract
            from web3.exceptions import ContractLogicError
            from eth_account import Account
            WEB3_AVAILABLE = True
            logging.warning(
                "Web3 loaded using certifi roots because the Windows certificate store "
                "could not initialize cleanly"
            )
        except Exception as retry_error:
            logging.warning("Web3 import failed after TLS certificate fallback: %s", retry_error)
            WEB3_AVAILABLE = False
            Web3 = None
            Contract = None
            ContractLogicError = Exception
            Account = None
        finally:
            ssl.create_default_context = original_create_default_context
    else:
        logging.info(f"Web3 import failed: {e}. Blockchain features will be disabled.")
        WEB3_AVAILABLE = False
        Web3 = None
        Contract = None
        ContractLogicError = Exception
        Account = None

logger = logging.getLogger(__name__)

class BlockchainConnector:
    """
    Manages connection to the private Aegis blockchain network and contract interactions.
    """

    def __init__(self):
        self.w3: Optional[Web3] = None
        self.contract: Optional[Contract] = None
        self.account: Optional[str] = None
        self.is_connected = False
        self.use_unlocked_account = False

        # Load configuration
        self.rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.contract_address = os.getenv("CONTRACT_ADDRESS") or self._load_local_deployment_address()
        self.private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
        self.contract_load_error: Optional[str] = None

        # Load contract ABI from the project root so it resolves correctly in this repo layout.
        self.abi_path = str(BASE_DIR / "blockchain" / "artifacts" / "contracts" / "AegisAudit.sol" / "AegisAudit.json")

    @staticmethod
    def _load_local_deployment_address() -> Optional[str]:
        deployment_path = BASE_DIR / "blockchain" / "deployments" / "localhost-deployment.json"
        try:
            with deployment_path.open(encoding="utf-8") as deployment_file:
                deployment = json.load(deployment_file)
            address = deployment.get("AegisAudit")
            return address if isinstance(address, str) and address else None
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read local blockchain deployment file %s: %s", deployment_path, exc)
            return None

    def connect(self) -> bool:
        """
        Establish connection to the blockchain network.
        """
        if not WEB3_AVAILABLE:
            logger.info("Web3 is not installed; blockchain features are disabled for this environment.")
            self.is_connected = False
            return False

        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

            if not self.w3.is_connected():
                logger.error(f"Failed to connect to blockchain at {self.rpc_url}")
                return False

            # A node can be reachable even when its local chain has been reset and
            # the previously deployed contract is no longer present.
            if self.contract_address:
                self._load_contract()
            else:
                self.contract_load_error = "No contract address is configured or recorded for the localhost network"
                logger.warning(self.contract_load_error)

            # Only use unlocked RPC accounts for the local Hardhat development chain.
            if self.private_key:
                self.account = Account.from_key(self.private_key).address
            elif self._is_local_hardhat_chain():
                accounts = self.w3.eth.accounts
                if accounts:
                    self.account = accounts[0]
                    self.use_unlocked_account = True

            self.is_connected = True
            logger.info(f"✅ Connected to blockchain network at {self.rpc_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to blockchain: {e}")
            return False

    def _is_local_hardhat_chain(self) -> bool:
        if not self.w3 or self.w3.eth.chain_id != 31337:
            return False
        hostname = urlparse(self.rpc_url).hostname
        if hostname == "localhost":
            return True
        try:
            return bool(hostname and ipaddress.ip_address(hostname).is_loopback)
        except ValueError:
            return False

    def _send_transaction(self, transaction):
        if self.private_key:
            estimated_gas = transaction.estimate_gas({"from": self.account})
            built_transaction = transaction.build_transaction({
                "from": self.account,
                "gas": int(estimated_gas * 1.2),
                "gasPrice": self.w3.eth.gas_price,
                "nonce": self.w3.eth.get_transaction_count(self.account),
            })
            signed_transaction = self.w3.eth.account.sign_transaction(
                built_transaction, self.private_key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.raw_transaction)
        elif self.use_unlocked_account and self.account:
            tx_hash = transaction.transact({"from": self.account})
        else:
            raise RuntimeError(
                "No signing account configured; local unlocked accounts are only enabled "
                "for the loopback Hardhat chain (chain ID 31337)"
            )

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise RuntimeError(f"Blockchain transaction {self._format_transaction_hash(tx_hash)} failed")
        return tx_hash, receipt

    @staticmethod
    def _format_transaction_hash(tx_hash) -> str:
        value = tx_hash.hex()
        return value if value.startswith("0x") else f"0x{value}"

    @staticmethod
    def _normalize_data_hash(data_hash: str):
        value = data_hash[2:] if data_hash.startswith("0x") else data_hash
        if len(value) == 64:
            try:
                return bytes.fromhex(value)
            except ValueError:
                pass
        return data_hash

    def _load_contract(self):
        """
        Load the AegisAudit contract ABI and create contract instance.
        """
        try:
            if not self.contract_address:
                self.contract_load_error = "No contract address is configured"
                return

            contract_address = Web3.to_checksum_address(self.contract_address)
            code = self.w3.eth.get_code(contract_address)
            if not code or code == b"" or code == b"\x00":
                self.contract = None
                self.contract_load_error = (
                    f"No contract code found at {contract_address} on RPC {self.rpc_url}; "
                    "the node may be using a reset or different chain"
                )
                logger.warning(self.contract_load_error)
                return

            with open(self.abi_path, 'r') as f:
                contract_data = json.load(f)

            self.contract = self.w3.eth.contract(
                address=contract_address,
                abi=contract_data['abi']
            )
            self.contract_address = contract_address
            self.contract_load_error = None

            logger.info("Contract loaded at %s", self.contract_address)

        except FileNotFoundError:
            self.contract = None
            self.contract_load_error = f"Contract ABI not found at {self.abi_path}"
            logger.warning(self.contract_load_error)
        except Exception as e:
            self.contract = None
            self.contract_load_error = f"Failed to load contract: {e}"
            logger.error(self.contract_load_error)

    def get_network_info(self) -> Dict[str, Any]:
        """
        Get basic network information.
        """
        if not self.is_connected:
            return {"error": "Not connected to blockchain"}

        try:
            return {
                "network_id": self.w3.eth.chain_id,
                "block_number": self.w3.eth.block_number,
                "gas_price": self.w3.eth.gas_price,
                "is_syncing": self.w3.eth.syncing,
                "contract_address": self.contract_address,
                "account": self.account
            }
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return {"error": str(e)}

    def submit_requirement_request(self, event_type: str, data_hash: str,
                                       metadata: str, tenant_id: int) -> Optional[str]:
        """
        Submit a requirement request to the blockchain.
        """
        if not self.contract or not self.account:
            logger.error("Contract not loaded or account not configured")
            return None

        try:
            txn = self.contract.functions.createLog(
                event_type,
                self._normalize_data_hash(data_hash),
                metadata,
                tenant_id
            )
            tx_hash, receipt = self._send_transaction(txn)

            # Record transaction for monitoring
            from backend.blockchain_monitor import get_blockchain_monitor
            monitor = get_blockchain_monitor(self)
            tx_hash_value = self._format_transaction_hash(tx_hash)
            monitor.record_transaction(tx_hash_value, "submit_requirement_request", tenant_id)

            logger.info(f"✅ Requirement request submitted: {tx_hash_value}")

            # Extract log ID from events
            log_created_event = None
            for log in receipt.logs:
                try:
                    event = self.contract.events.LogCreated().process_log(log)
                    log_created_event = event
                    break
                except:
                    continue

            return tx_hash_value

        except Exception as e:
            logger.error(f"Failed to submit requirement request: {e}")
            return None

    def submit_audit_log(self, event_type: str, data_hash: str,
                         metadata: str, tenant_id: int) -> Optional[str]:
        """
        Submit a generic audit log to the blockchain.
        """
        if not self.contract or not self.account:
            logger.error("Contract not loaded or account not configured")
            return None

        try:
            txn = self.contract.functions.createLog(
                event_type,
                self._normalize_data_hash(data_hash),
                metadata,
                tenant_id
            )
            tx_hash, _receipt = self._send_transaction(txn)

            from backend.blockchain_monitor import get_blockchain_monitor
            monitor = get_blockchain_monitor(self)
            tx_hash_value = self._format_transaction_hash(tx_hash)
            monitor.record_transaction(tx_hash_value, "submit_audit_log", tenant_id)

            logger.info(f"✅ Audit log submitted: {tx_hash_value}")
            return tx_hash_value

        except Exception as e:
            logger.error(f"Failed to submit audit log: {e}")
            return None

    def approve_requirement(self, log_id: str, approval_metadata: str,
                                tenant_id: int) -> Optional[str]:
        """
        Approve a requirement on the blockchain.
        """
        if not self.contract or not self.account:
            logger.error("Contract not loaded or account not configured")
            return None

        try:
            txn = self.contract.functions.createLog(
                "REQUIREMENT_APPROVAL",
                self.w3.keccak(text=approval_metadata),
                approval_metadata,
                tenant_id
            )
            tx_hash, _receipt = self._send_transaction(txn)

            # Record transaction for monitoring
            from backend.blockchain_monitor import get_blockchain_monitor
            monitor = get_blockchain_monitor(self)
            tx_hash_value = self._format_transaction_hash(tx_hash)
            monitor.record_transaction(tx_hash_value, "approve_requirement", tenant_id)

            logger.info(f"✅ Requirement approved: {tx_hash_value}")
            return tx_hash_value

        except Exception as e:
            logger.error(f"Failed to approve requirement: {e}")
            return None

    def reject_requirement(self, log_id: str, rejection_metadata: str,
                               tenant_id: int) -> Optional[str]:
        """
        Reject a requirement on the blockchain.
        """
        if not self.contract or not self.account:
            logger.error("Contract not loaded or account not configured")
            return None

        try:
            txn = self.contract.functions.createLog(
                "REQUIREMENT_REJECTION",
                self.w3.keccak(text=rejection_metadata),
                rejection_metadata,
                tenant_id
            )
            tx_hash, _receipt = self._send_transaction(txn)

            # Record transaction for monitoring
            from backend.blockchain_monitor import get_blockchain_monitor
            monitor = get_blockchain_monitor(self)
            tx_hash_value = self._format_transaction_hash(tx_hash)
            monitor.record_transaction(tx_hash_value, "reject_requirement", tenant_id)

            logger.info(f"✅ Requirement rejected: {tx_hash_value}")
            return tx_hash_value

        except Exception as e:
            logger.error(f"Failed to reject requirement: {e}")
            return None

    def get_blockchain_logs(self, tenant_id: Optional[int] = None,
                                event_type: Optional[str] = None,
                                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve logs from the blockchain.
        """
        if not self.contract:
            error = self.contract_load_error or "Contract not loaded"
            raise RuntimeError(error)

        try:
            if tenant_id is not None:
                log_ids = self.contract.functions.getTenantLogs(tenant_id).call()
                if event_type:
                    event_log_ids = set(self.contract.functions.getLogsByEventType(event_type).call())
                    log_ids = [log_id for log_id in log_ids if log_id in event_log_ids]
            elif event_type:
                log_ids = self.contract.functions.getLogsByEventType(event_type).call()
            else:
                log_ids = self.contract.functions.getAllLogs().call()

            return [
                self._format_log_data(log_id, self.contract.functions.getLog(log_id).call())
                for log_id in log_ids[-limit:]
            ]

        except Exception as e:
            logger.error("Failed to get blockchain logs: %s", e)
            raise RuntimeError(f"Failed to get blockchain logs: {e}") from e

    def _format_log_data(self, log_id: str, log_data: tuple) -> Dict[str, Any]:
        """
        Format raw log data into a structured dictionary.
        """
        formatted_log_id = log_id.hex() if hasattr(log_id, "hex") else str(log_id)
        if not formatted_log_id.startswith("0x"):
            formatted_log_id = f"0x{formatted_log_id}"
        data_hash = log_data[4].hex() if hasattr(log_data[4], "hex") else str(log_data[4])
        if not data_hash.startswith("0x"):
            data_hash = f"0x{data_hash}"
        return {
            "id": formatted_log_id,
            "log_index": log_data[0],
            "timestamp": log_data[1],
            "actor": log_data[2],
            "event_type": log_data[3],
            "data_hash": data_hash,
            "metadata": log_data[5],
            "tenant_id": log_data[6],
            "severity": log_data[7],
            "verified": log_data[8],
            "archived": log_data[9]
        }

    def get_compliance_summary(self, tenant_id: int) -> Dict[str, Any]:
        """
        Get compliance summary for a tenant from blockchain.
        """
        if not self.contract:
            return {"error": self.contract_load_error or "Contract not loaded"}

        try:
            summary = self.contract.functions.getComplianceSummary(tenant_id).call()
            return {
                "total_logs": summary[0],
                "verified_logs": summary[1],
                "critical_logs": summary[2],
                "emergency_logs": summary[3]
            }
        except Exception as e:
            logger.error(f"Failed to get compliance summary: {e}")
            return {"error": str(e)}

    def get_audit_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide audit statistics from blockchain.
        """
        if not self.contract:
            return {"error": "Contract not loaded"}

        try:
            stats = self.contract.functions.getAuditStatistics().call()
            return {
                "total_logs": stats[0],
                "total_tenants": stats[1],
                "emergency_count": stats[2],
                "average_severity": stats[3]
            }
        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            return {"error": str(e)}

# Global blockchain connector instance
blockchain_connector = BlockchainConnector()

def get_blockchain_connector() -> BlockchainConnector:
    """
    Dependency injection for blockchain connector.
    """
    if not blockchain_connector.is_connected or (
        blockchain_connector.contract_address and not blockchain_connector.contract
    ):
        blockchain_connector.connect()
    return blockchain_connector