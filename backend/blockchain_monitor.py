"""
AEGIS Backend - Blockchain Monitoring Module
Provides monitoring and health checks for blockchain operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from backend.blockchain_connector import BlockchainConnector

logger = logging.getLogger(__name__)

class BlockchainMonitor:
    """
    Monitors blockchain network health, transaction status, and performance metrics.
    """

    def __init__(self, blockchain_connector: BlockchainConnector):
        self.blockchain = blockchain_connector
        self.metrics = {
            "transactions_submitted": 0,
            "transactions_successful": 0,
            "transactions_failed": 0,
            "last_block_check": None,
            "network_latency": 0,
            "gas_price_avg": 0,
            "errors": []
        }
        self.transaction_history: List[Dict[str, Any]] = []
        self.monitoring_active = False

    async def start_monitoring(self, interval_seconds: int = 30):
        """
        Start background monitoring of blockchain health.
        """
        self.monitoring_active = True
        logger.info("🚀 Starting blockchain monitoring...")

        while self.monitoring_active:
            try:
                await self._check_network_health()
                await self._check_pending_transactions()
                await self._update_metrics()

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                self.metrics["errors"].append({
                    "timestamp": datetime.utcnow(),
                    "error": str(e)
                })

            await asyncio.sleep(interval_seconds)

    def stop_monitoring(self):
        """
        Stop background monitoring.
        """
        self.monitoring_active = False
        logger.info("⏹️ Stopped blockchain monitoring")

    async def _check_network_health(self):
        """
        Check blockchain network connectivity and performance.
        """
        if not self.blockchain.is_connected:
            return

        try:
            start_time = datetime.utcnow()
            network_info = await asyncio.to_thread(self.blockchain.get_network_info)
            end_time = datetime.utcnow()

            self.metrics["network_latency"] = (end_time - start_time).total_seconds() * 1000  # ms
            self.metrics["last_block_check"] = datetime.utcnow()

            if network_info.get("gas_price"):
                # Update rolling average gas price
                current_avg = self.metrics["gas_price_avg"]
                self.metrics["gas_price_avg"] = (current_avg + network_info["gas_price"]) / 2

            # Check if network is syncing
            if network_info.get("is_syncing"):
                logger.warning("⚠️ Blockchain network is syncing")

        except Exception as e:
            logger.error(f"Network health check failed: {e}")

    async def _check_pending_transactions(self):
        """
        Check status of recent transactions.
        """
        # Clean old transactions (older than 1 hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.transaction_history = [
            tx for tx in self.transaction_history
            if tx["timestamp"] > cutoff_time
        ]

        # Check pending transactions
        for tx in self.transaction_history:
            if tx["status"] == "pending":
                await self._check_transaction_status(tx)

    async def _check_transaction_status(self, tx_record: Dict[str, Any]):
        """
        Check the status of a specific transaction.
        """
        if not self.blockchain.w3:
            return

        try:
            tx_hash = tx_record["hash"]
            receipt = await asyncio.to_thread(self.blockchain.w3.eth.get_transaction_receipt, tx_hash)

            if receipt:
                if receipt.status == 1:
                    tx_record["status"] = "confirmed"
                    tx_record["block_number"] = receipt.blockNumber
                    tx_record["gas_used"] = receipt.gasUsed
                    self.metrics["transactions_successful"] += 1
                    logger.info(f"✅ Transaction confirmed: {tx_hash}")
                else:
                    tx_record["status"] = "failed"
                    tx_record["error"] = "Transaction reverted"
                    self.metrics["transactions_failed"] += 1
                    logger.warning(f"❌ Transaction failed: {tx_hash}")

        except Exception as e:
            # Transaction might still be pending
            pass

    async def _update_metrics(self):
        """
        Update monitoring metrics.
        """
        # Clean old errors (keep last 100)
        self.metrics["errors"] = self.metrics["errors"][-100:]

        # Calculate success rate
        total_tx = self.metrics["transactions_submitted"]
        if total_tx > 0:
            success_rate = self.metrics["transactions_successful"] / total_tx
            self.metrics["transaction_success_rate"] = success_rate

    def record_transaction(self, tx_hash: str, operation: str, tenant_id: int):
        """
        Record a new transaction for monitoring.
        """
        tx_record = {
            "hash": tx_hash,
            "operation": operation,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow(),
            "status": "pending"
        }

        self.transaction_history.append(tx_record)
        self.metrics["transactions_submitted"] += 1

        logger.info(f"📝 Recorded transaction: {tx_hash} ({operation})")

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of blockchain integration.
        """
        health = {
            "timestamp": datetime.utcnow(),
            "blockchain_connected": self.blockchain.is_connected,
            "monitoring_active": self.monitoring_active,
            "metrics": self.metrics.copy(),
            "recent_transactions": self.transaction_history[-10:],  # Last 10 transactions
        }

        if self.blockchain.is_connected:
            try:
                network_info = await self.blockchain.get_network_info()
                health["network_info"] = network_info

                # Calculate health score
                health_score = 100

                # Deduct points for connection issues
                if not network_info.get("is_syncing", True):
                    health_score -= 20

                # Deduct points for high latency (>5 seconds)
                if self.metrics["network_latency"] > 5000:
                    health_score -= 30

                # Deduct points for recent errors
                recent_errors = len([e for e in self.metrics["errors"]
                                   if e["timestamp"] > datetime.utcnow() - timedelta(minutes=5)])
                health_score -= min(recent_errors * 10, 40)

                # Deduct points for low transaction success rate
                success_rate = self.metrics.get("transaction_success_rate", 1.0)
                if success_rate < 0.95:
                    health_score -= 10

                health["health_score"] = max(0, health_score)
                health["status"] = "healthy" if health_score >= 70 else "degraded" if health_score >= 40 else "unhealthy"

            except Exception as e:
                health["network_error"] = str(e)
                health["status"] = "error"
                health["health_score"] = 0

        else:
            health["status"] = "disconnected"
            health["health_score"] = 0

        return health

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics.
        """
        return {
            "network_latency_ms": self.metrics["network_latency"],
            "gas_price_avg": self.metrics["gas_price_avg"],
            "transaction_success_rate": self.metrics.get("transaction_success_rate", 0),
            "transactions_per_hour": len([
                tx for tx in self.transaction_history
                if tx["timestamp"] > datetime.utcnow() - timedelta(hours=1)
            ]),
            "error_rate": len(self.metrics["errors"]) / max(1, self.metrics["transactions_submitted"]),
            "last_block_check": self.metrics["last_block_check"]
        }

    def get_transaction_history(self, tenant_id: Optional[int] = None,
                              limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get transaction history, optionally filtered by tenant.
        """
        transactions = self.transaction_history

        if tenant_id is not None:
            transactions = [tx for tx in transactions if tx["tenant_id"] == tenant_id]

        return transactions[-limit:]

# Global monitor instance
blockchain_monitor = None

def get_blockchain_monitor(blockchain_connector: BlockchainConnector) -> BlockchainMonitor:
    """
    Get or create the global blockchain monitor instance.
    """
    global blockchain_monitor
    if blockchain_monitor is None:
        blockchain_monitor = BlockchainMonitor(blockchain_connector)
    return blockchain_monitor