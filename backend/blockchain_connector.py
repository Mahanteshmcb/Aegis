"""
AEGIS Backend - Blockchain Integration Module
Handles communication with the AegisAudit smart contract on the private blockchain network.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from eth_account import Account
from datetime import datetime

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

        # Load configuration
        self.rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.contract_address = os.getenv("CONTRACT_ADDRESS")
        self.private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")

        # Load contract ABI
        self.abi_path = os.path.join(os.path.dirname(__file__), "../../blockchain/artifacts/contracts/AegisAudit.sol/AegisAudit.json")

    def connect(self) -> bool:
        """
        Establish connection to the blockchain network.
        """
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

            if not self.w3.is_connected():
                logger.error(f"Failed to connect to blockchain at {self.rpc_url}")
                return False

            # Load contract if address is available
            if self.contract_address:
                self._load_contract()

            # Set up account if private key is available
            if self.private_key:
                self.account = Account.from_key(self.private_key).address

            self.is_connected = True
            logger.info(f"✅ Connected to blockchain network at {self.rpc_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to blockchain: {e}")
            return False

    def _load_contract(self):
        """
        Load the AegisAudit contract ABI and create contract instance.
        """
        try:
            with open(self.abi_path, 'r') as f:
                contract_data = json.load(f)

            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=contract_data['abi']
            )

            logger.info(f"✅ Contract loaded at {self.contract_address}")

        except FileNotFoundError:
            logger.warning(f"Contract ABI not found at {self.abi_path}")
        except Exception as e:
            logger.error(f"Failed to load contract: {e}")

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
        if not self.contract or not self.account or not self.private_key:
            logger.error("Contract not loaded or account not configured")
            return None

        try:
            # Build transaction
            tx = self.contract.functions.createLog(
                event_type,
                data_hash,
                metadata,
                tenant_id
            ).build_transaction({
                'from': self.account,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })

            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Record transaction for monitoring
            from backend.blockchain_monitor import get_blockchain_monitor
            monitor = get_blockchain_monitor(self)
            monitor.record_transaction(str(tx_hash.hex()), "submit_requirement_request", tenant_id)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"✅ Requirement request submitted: {tx_hash.hex()}")

            # Extract log ID from events
            log_created_event = None
            for log in receipt.logs:
                try:
                    event = self.contract.events.LogCreated().process_log(log)
                    log_created_event = event
                    break
                except:
                    continue

            if log_created_event:
                return log_created_event.args.logId.hex()

            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Failed to submit requirement request: {e}")
            return None

    def approve_requirement(self, log_id: str, approval_metadata: str,
                                tenant_id: int) -> Optional[str]:
        """
        Approve a requirement on the blockchain.
        """
        if not self.contract or not self.account or not self.private_key:
            logger.error("Contract not loaded or account not configured")
            return None

        try:
            tx = self.contract.functions.createLog(
                "REQUIREMENT_APPROVAL",
                self.w3.keccak(text=approval_metadata),
                approval_metadata,
                tenant_id
            ).build_transaction({
                'from': self.account,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Record transaction for monitoring
            from backend.blockchain_monitor import get_blockchain_monitor
            monitor = get_blockchain_monitor(self)
            monitor.record_transaction(str(tx_hash.hex()), "approve_requirement", tenant_id)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"✅ Requirement approved: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Failed to approve requirement: {e}")
            return None

    def reject_requirement(self, log_id: str, rejection_metadata: str,
                               tenant_id: int) -> Optional[str]:
        """
        Reject a requirement on the blockchain.
        """
        if not self.contract or not self.account or not self.private_key:
            logger.error("Contract not loaded or account not configured")
            return None

        try:
            tx = self.contract.functions.createLog(
                "REQUIREMENT_REJECTION",
                self.w3.keccak(text=rejection_metadata),
                rejection_metadata,
                tenant_id
            ).build_transaction({
                'from': self.account,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Record transaction for monitoring
            from backend.blockchain_monitor import get_blockchain_monitor
            monitor = get_blockchain_monitor(self)
            monitor.record_transaction(str(tx_hash.hex()), "reject_requirement", tenant_id)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"✅ Requirement rejected: {tx_hash.hex()}")
            return tx_hash.hex()

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
            logger.error("Contract not loaded")
            return []

        try:
            logs = []

            if event_type:
                # Get logs by event type
                log_ids = self.contract.functions.getLogsByEventType(event_type).call()
                for log_id in log_ids[-limit:]:  # Get last 'limit' logs
                    log_data = self.contract.functions.getLog(log_id).call()
                    if not tenant_id or log_data[4] == tenant_id:  # tenantId is at index 4
                        logs.append(self._format_log_data(log_id, log_data))
            else:
                # Get recent logs
                recent_logs = self.contract.functions.getRecentLogs(limit).call()
                for log_id in recent_logs:
                    log_data = self.contract.functions.getLog(log_id).call()
                    if not tenant_id or log_data[4] == tenant_id:
                        logs.append(self._format_log_data(log_id, log_data))

            return logs

        except Exception as e:
            logger.error(f"Failed to get blockchain logs: {e}")
            return []

    def _format_log_data(self, log_id: str, log_data: tuple) -> Dict[str, Any]:
        """
        Format raw log data into a structured dictionary.
        """
        return {
            "id": log_id,
            "log_index": log_data[0],
            "timestamp": log_data[1],
            "actor": log_data[2],
            "event_type": log_data[3],
            "tenant_id": log_data[4],
            "severity": log_data[5],
            "data_hash": log_data[6],
            "metadata": log_data[7],
            "verified": log_data[8],
            "archived": log_data[9]
        }

    def get_compliance_summary(self, tenant_id: int) -> Dict[str, Any]:
        """
        Get compliance summary for a tenant from blockchain.
        """
        if not self.contract:
            return {"error": "Contract not loaded"}

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
    if not blockchain_connector.is_connected:
        blockchain_connector.connect()
    return blockchain_connector