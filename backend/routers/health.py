"""
Aegis Backend - Health Check Router
System status and real-time threat monitoring endpoints.
"""

from datetime import datetime
import time
import sys
import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from web3 import Web3

from backend.config import settings
from backend.dependencies import get_current_admin, get_db, get_current_user
from backend.models_db import Sensor

# Import VryndaraConnector
vryndara_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ai'))
if vryndara_path not in sys.path:
    sys.path.insert(0, vryndara_path)
from vryndara_connector import VryndaraConnector

router = APIRouter(prefix="/api/v1/health", tags=["health"])

# --- SCHEMAS ---

class HealthResponse(BaseModel):
    status: str
    backend: str
    database: str
    vryndara: str
    blockchain: str
    uptime_seconds: int
    timestamp: str

class DetailedHealthResponse(HealthResponse):
    database_latency_ms: float = 0.0
    vryndara_latency_ms: float = 0.0
    request_count: int = 0
    error_count: int = 0
    version: str

class SystemStatusResponse(BaseModel):
    """Day 19: Real-time Threat Status Schema"""
    status: str
    threat_count: int
    uptime: str
    vryndara_version: str

# Track uptime
start_time = time.time()

# --- ENDPOINTS ---

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """
    Day 19: Active Sector Monitoring.
    Scans live telemetry for threshold violations (Thermal Anomalies).
    """
    # Fetch all sensors for the user's tenant
    sensors = db.query(Sensor).filter(Sensor.tenant_id == current_user["tenant_id"]).all()
    
    overall_status = "HEALTHY"
    threats = 0
    
    for s in sensors:
        # Scan for thermal anomaly (threshold: 23.5°C)
        if s.last_reading and s.last_reading.get("value", 0) > 23.5:
            overall_status = "WARNING"
            threats += 1
            
    return SystemStatusResponse(
        status=overall_status,
        threat_count=threats,
        uptime=f"{int((time.time() - start_time) / 3600)}h {int(((time.time() - start_time) % 3600) / 60)}m",
        vryndara_version="3.1-Flash"
    )

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Standard connectivity check."""
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
        vryndara_ok = vryndara.health_check()
        vryndara_status = "connected" if vryndara_ok else ("fallback" if vryndara.fallback_mode else "disconnected")
    except Exception:
        vryndara_status = "disconnected"

    # Check blockchain
    try:
        # Note: Using a short timeout for health check
        w3 = Web3(Web3.HTTPProvider("http://localhost:8545", request_kwargs={'timeout': 1}))
        blockchain_status = "connected" if w3.is_connected() else "disconnected"
    except Exception:
        blockchain_status = "disconnected"

    overall_status = "healthy"
    if db_status != "connected" or vryndara_status == "disconnected" or blockchain_status != "connected":
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
    db: Session = Depends(get_db),
):
    """Detailed health check for Admin dashboard."""
    uptime_seconds = int(time.time() - start_time)
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Database latency
    t0 = time.time()
    try:
        db.execute("SELECT 1")
        db_latency = (time.time() - t0) * 1000
        db_status = "connected"
    except Exception:
        db_latency = 0.0
        db_status = "disconnected"

    # Vryndara latency
    vryndara = VryndaraConnector()
    t1 = time.time()
    try:
        vryndara_ok = vryndara.health_check()
        vryndara_latency = (time.time() - t1) * 1000
        vryndara_status = "connected" if vryndara_ok else ("fallback" if vryndara.fallback_mode else "disconnected")
    except Exception:
        vryndara_latency = 0.0
        vryndara_status = "disconnected"

    # Blockchain connectivity
    try:
        w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
        blockchain_status = "connected" if w3.is_connected() else "disconnected"
    except Exception:
        blockchain_status = "disconnected"

    return DetailedHealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
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