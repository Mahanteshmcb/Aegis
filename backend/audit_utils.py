"""
AEGIS Backend - Audit Utilities
Shared helpers for creating database and blockchain-backed audit records.
"""

import hashlib
import json
import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend import crud, schemas
from backend.blockchain_connector import BlockchainConnector

logger = logging.getLogger(__name__)


def _serialize_metadata(metadata: Dict[str, Any]) -> str:
    return json.dumps(metadata, sort_keys=True, default=str)


def _compute_data_hash(metadata: Dict[str, Any]) -> str:
    serialized = _serialize_metadata(metadata)
    return hashlib.sha256(serialized.encode()).hexdigest()


def record_audit_event(
    db: Session,
    blockchain: Optional[BlockchainConnector],
    tenant_id: int,
    event_type: str,
    metadata: Dict[str, Any],
) -> schemas.AuditLog:
    """Create an audit log record and optionally persist a blockchain transaction."""
    metadata_json = _serialize_metadata(metadata)
    data_hash = hashlib.sha256(metadata_json.encode()).hexdigest()
    blockchain_tx = None

    if blockchain is not None:
        try:
            blockchain_tx = blockchain.submit_audit_log(
                event_type=event_type,
                data_hash=data_hash,
                metadata=metadata_json,
                tenant_id=tenant_id,
            )
        except Exception as e:
            logger.warning(f"Failed to submit blockchain audit log: {e}")

    audit = schemas.AuditLogCreate(
        event_type=event_type,
        data_hash=data_hash,
        blockchain_tx=blockchain_tx,
    )
    return crud.create_audit_log(db, audit, tenant_id=tenant_id)
