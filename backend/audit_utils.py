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
        actor_user_id=metadata.get("actor_user_id"),
        actor_email=metadata.get("actor_email"),
        action=metadata.get("action") or event_type,
        entity_type=metadata.get("entity_type"),
        entity_id=str(metadata["entity_id"]) if metadata.get("entity_id") is not None else None,
        outcome=metadata.get("outcome"),
        details=metadata,
    )
    return crud.create_audit_log(db, audit, tenant_id=tenant_id)


def record_actor_audit_event(
    db: Session,
    tenant_id: int,
    actor: Dict[str, Any],
    event_type: str,
    entity_type: str,
    entity_id: Any,
    details: Optional[Dict[str, Any]] = None,
    blockchain: Optional[BlockchainConnector] = None,
    outcome: str = "success",
) -> schemas.AuditLog:
    """Record a structured event with a consistent actor and entity envelope."""
    metadata = {
        **(details or {}),
        "action": event_type,
        "actor_user_id": actor.get("id"),
        "actor_email": actor.get("email"),
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id is not None else None,
        "outcome": outcome,
    }
    return record_audit_event(db, blockchain, tenant_id, event_type, metadata)
