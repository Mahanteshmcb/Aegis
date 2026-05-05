"""
Aegis Backend - Audit Logs Router
Endpoints for viewing system and sensor audit trails from both database and blockchain.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.dependencies import get_db, get_current_user
from backend import crud, schemas
from backend.models_db import Sensor, AuditLog
from backend.blockchain_connector import get_blockchain_connector, BlockchainConnector

router = APIRouter(prefix="/api/v1", tags=["audit"])

# FIXED: Path changed from "/audit/logs" to "/audit" to match frontend api.js
@router.get("/audit", response_model=list[schemas.AuditLog])
async def list_audit_logs(
    sensor_id: int = Query(None, description="Filter by sensor ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List audit logs from database. Tenant-isolated via Sensor join.
    """
    if sensor_id is not None:
        return crud.list_audit_logs(
            db,
            tenant_id=current_user["tenant_id"],
            sensor_id=sensor_id,
            skip=skip,
            limit=limit,
        )

    return crud.list_audit_logs(
        db,
        tenant_id=current_user["tenant_id"],
        skip=skip,
        limit=limit,
    )

@router.get("/audit/blockchain", response_model=List[dict])
async def list_blockchain_audit_logs(
    tenant_id: Optional[int] = Query(None, description="Filter by tenant ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, description="Maximum number of logs to return"),
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    List audit logs directly from the blockchain.
    Requires blockchain connection to be configured.
    """
    try:
        # Use current user's tenant if not specified
        target_tenant = tenant_id or current_user["tenant_id"]
        if tenant_id and tenant_id != current_user["tenant_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        logs = blockchain.get_blockchain_logs(
            tenant_id=target_tenant,
            event_type=event_type,
            limit=limit
        )

        return logs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain query failed: {str(e)}")

@router.post("/audit/requirement/request")
async def submit_requirement_request(
    event_type: str = Query(..., description="Type of requirement event"),
    data_hash: str = Query(..., description="Hash of the requirement data"),
    metadata: str = Query(..., description="Human-readable requirement details"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID (defaults to current user's tenant)"),
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    Submit a requirement request to the blockchain.
    """
    try:
        target_tenant = tenant_id or current_user["tenant_id"]
        if tenant_id and tenant_id != current_user["tenant_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        tx_hash = blockchain.submit_requirement_request(
            event_type=event_type,
            data_hash=data_hash,
            metadata=metadata,
            tenant_id=target_tenant
        )

        if tx_hash:
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "message": "Requirement request submitted to blockchain"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to submit requirement request")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit requirement: {str(e)}")

@router.post("/audit/requirement/{log_id}/approve")
async def approve_requirement(
    log_id: str,
    approval_metadata: str = Query(..., description="Approval details and reasoning"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID"),
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    Approve a requirement on the blockchain.
    """
    try:
        target_tenant = tenant_id or current_user["tenant_id"]
        if tenant_id and tenant_id != current_user["tenant_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        tx_hash = blockchain.approve_requirement(
            log_id=log_id,
            approval_metadata=approval_metadata,
            tenant_id=target_tenant
        )

        if tx_hash:
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "message": "Requirement approved on blockchain"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to approve requirement")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve requirement: {str(e)}")

@router.post("/audit/requirement/{log_id}/reject")
async def reject_requirement(
    log_id: str,
    rejection_metadata: str = Query(..., description="Rejection details and reasoning"),
    tenant_id: Optional[int] = Query(None, description="Tenant ID"),
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    Reject a requirement on the blockchain.
    """
    try:
        target_tenant = tenant_id or current_user["tenant_id"]
        if tenant_id and tenant_id != current_user["tenant_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        tx_hash = blockchain.reject_requirement(
            log_id=log_id,
            rejection_metadata=rejection_metadata,
            tenant_id=target_tenant
        )

        if tx_hash:
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "message": "Requirement rejected on blockchain"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reject requirement")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject requirement: {str(e)}")

@router.get("/audit/compliance/{tenant_id}")
async def get_tenant_compliance_summary(
    tenant_id: int,
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    Get compliance summary for a specific tenant from blockchain.
    """
    try:
        # Users can only view their own tenant's compliance (unless admin)
        if current_user["tenant_id"] != tenant_id and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        summary = blockchain.get_compliance_summary(tenant_id)

        return {
            "tenant_id": tenant_id,
            "compliance_summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance summary: {str(e)}")

@router.get("/audit/statistics")
async def get_system_audit_statistics(
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    Get system-wide audit statistics from blockchain.
    """
    try:
        stats = blockchain.get_audit_statistics()

        return {
            "system_statistics": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit statistics: {str(e)}")

@router.get("/blockchain/status")
async def get_blockchain_status(
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
):
    """
    Get blockchain network status and connection information.
    """
    try:
        network_info = blockchain.get_network_info()

        return {
            "connected": blockchain.is_connected,
            "network_info": network_info
        }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }

@router.get("/blockchain/health")
async def get_blockchain_health(
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
):
    """
    Get comprehensive blockchain health status and monitoring metrics.
    """
    from backend.blockchain_monitor import get_blockchain_monitor

    try:
        monitor = get_blockchain_monitor(blockchain)
        health_status = await monitor.get_health_status()

        return health_status

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/blockchain/metrics")
async def get_blockchain_metrics(
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    Get detailed blockchain performance metrics.
    """
    from backend.blockchain_monitor import get_blockchain_monitor

    try:
        monitor = get_blockchain_monitor(blockchain)
        metrics = await monitor.get_performance_metrics()

        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/blockchain/transactions")
async def get_transaction_history(
    tenant_id: Optional[int] = Query(None, description="Filter by tenant ID"),
    limit: int = Query(50, description="Maximum transactions to return"),
    blockchain: BlockchainConnector = Depends(get_blockchain_connector),
    current_user=Depends(get_current_user),
):
    """
    Get transaction history from blockchain monitoring.
    """
    from backend.blockchain_monitor import get_blockchain_monitor

    try:
        monitor = get_blockchain_monitor(blockchain)

        # Users can only see their own tenant's transactions (unless admin)
        target_tenant = tenant_id or current_user["tenant_id"]
        if current_user["tenant_id"] != target_tenant and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        transactions = monitor.get_transaction_history(
            tenant_id=target_tenant,
            limit=limit
        )

        return {
            "transactions": transactions,
            "count": len(transactions)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transaction history: {str(e)}")