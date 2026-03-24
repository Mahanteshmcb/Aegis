"""
Aegis Backend - Health Check Router
System status endpoints.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel


from backend.config import settings
from backend.dependencies import get_current_admin, get_db
import sys
import os
# Import VryndaraConnector
vryndara_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ai'))
if vryndara_path not in sys.path:
    sys.path.insert(0, vryndara_path)
from vryndara_connector import VryndaraConnector
from web3 import Web3

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    backend: str
    database: str
    vryndara: str
    blockchain: str
    uptime_seconds: int
    timestamp: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response."""
    database_latency_ms: float = 0.0
    vryndara_latency_ms: float = 0.0
    request_count: int = 0
    error_count: int = 0
    version: str


# Track uptime
import time
start_time = time.time()



@router.get("/health", response_model=HealthResponse)
async def health_check(db=Depends(get_db)):
    """
    Get system health status.
    Checks: backend, database, vryndara, blockchain.
    """
    uptime_seconds = int(time.time() - start_time)
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Check Vryndara
    vryndara = VryndaraConnector()
    try:
        vryndara_status = "connected" if vryndara.health_check() else ("fallback" if vryndara.fallback_mode else "disconnected")
    except Exception:
        vryndara_status = "disconnected"

    # Check blockchain (basic connectivity)
    try:
        w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
        blockchain_status = "connected" if w3.isConnected() else "disconnected"
    except Exception:
        blockchain_status = "disconnected"

    # Determine overall status
    overall_status = "healthy"
    if db_status != "connected" or vryndara_status in ("disconnected",) or blockchain_status != "connected":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        backend="running",
        database=db_status,
        vryndara=vryndara_status,
        blockchain=blockchain_status,
        uptime_seconds=uptime_seconds,
        timestamp=timestamp,
    )



@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def health_check_detailed(
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    """
    Get detailed system health status (admin only).
    Includes latency metrics and request counts.
    """
    uptime_seconds = int(time.time() - start_time)
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Check database with latency
    import time as time_module
    db_start = time_module.time()
    try:
        db.execute("SELECT 1")
        db_status = "connected"
        db_latency = (time_module.time() - db_start) * 1000
    except Exception:
        db_status = "disconnected"
        db_latency = 0.0

    # Vryndara latency
    vryndara = VryndaraConnector()
    vryndara_start = time_module.time()
    try:
        vryndara_ok = vryndara.health_check()
        vryndara_status = "connected" if vryndara_ok else ("fallback" if vryndara.fallback_mode else "disconnected")
        vryndara_latency = (time_module.time() - vryndara_start) * 1000
    except Exception:
        vryndara_status = "disconnected"
        vryndara_latency = 0.0

    # Blockchain latency
    blockchain_start = time_module.time()
    try:
        w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
        blockchain_status = "connected" if w3.isConnected() else "disconnected"
        blockchain_latency = (time_module.time() - blockchain_start) * 1000
    except Exception:
        blockchain_status = "disconnected"
        blockchain_latency = 0.0

    # Determine overall status
    overall_status = "healthy"
    if db_status != "connected" or vryndara_status in ("disconnected",) or blockchain_status != "connected":
        overall_status = "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        backend="running",
        database=db_status,
        vryndara=vryndara_status,
        blockchain=blockchain_status,
        uptime_seconds=uptime_seconds,
        timestamp=timestamp,
        database_latency_ms=db_latency,
        vryndara_latency_ms=vryndara_latency,
        request_count=0,
        error_count=0,
        version=settings.app_version,
    )
