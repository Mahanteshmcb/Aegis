"""
Aegis Backend - Research Router
Vryndara integration for compliance research and AI log analysis.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.models_db import AuditLog, Sensor
from backend.dependencies import get_db, get_current_user
from backend.config import settings

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.vryndara_connector import VryndaraConnector

router = APIRouter(prefix="/api/v1/research", tags=["AI"])

# Lazy connector initialization to avoid multiple reconnections on hot-reload
_vryndara_connector = None

def get_vryndara_connector():
    """Get or create VryndaraConnector (lazy initialization)."""
    global _vryndara_connector
    if _vryndara_connector is None:
        _vryndara_connector = VryndaraConnector(
            kernel_address=f"{settings.vryndara_host}:{settings.vryndara_port}",
            fallback_mode=settings.vryndara_fallback_enabled,
        )
    return _vryndara_connector


# --- SCHEMAS ---

class ResearchRequest(BaseModel):
    framework: str 
    query: str = ""

class ResearchResponse(BaseModel):
    framework: str
    findings: List[Dict[str, Any]] = []
    summary: str = ""
    status: str

class GenerateScriptRequest(BaseModel):
    framework: str
    check_type: str
    zone_id: Optional[str] = None

class RobotCommandRequest(BaseModel):
    robot_type: str
    action: str
    parameters: Dict[str, str] = {}
    security_token: Optional[str] = None

class AuditScriptResponse(BaseModel):
    status: str
    message: str = ""
    script: str = ""

class AnalyzeLogsResponse(BaseModel):
    status: str
    findings: List[str] = []
    message: str = ""

class VryndaraHealthResponse(BaseModel):
    status: str
    connected: bool

class RobotCommandResponse(BaseModel):
    status: str
    message: str = ""
    result: Dict[str, Any] = {}

# --- ENDPOINTS ---

@router.get("/health", response_model=VryndaraHealthResponse)
async def vryndara_health(current_user=Depends(get_current_user)):
    """Return the current Vryndara connection status."""
    connector = get_vryndara_connector()
    healthy = connector.health_check()
    return {
        "status": "connected" if healthy else "fallback",
        "connected": healthy,
    }

@router.post("/analysis/logs", response_model=AnalyzeLogsResponse)
async def analyze_logs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Vryndara Brain: Analyzes the last 50 audit logs for tenant-specific anomalies.
    """
    logs = (
        db.query(AuditLog)
        .join(Sensor, AuditLog.sensor_id == Sensor.id)
        .filter(Sensor.tenant_id == current_user["tenant_id"])
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )

    if not logs:
        return {"status": "idle", "message": "No telemetry data found to analyze.", "findings": []}

    payload_logs = [
        {
            "event_type": log.event_type,
            "sensor_id": log.sensor_id,
            "timestamp": log.created_at.isoformat(),
            "data_hash": log.data_hash,
        }
        for log in logs
    ]

    connector = get_vryndara_connector()
    result = connector.analyze_audit_logs(
        logs=payload_logs,
        zone_id=str(current_user["tenant_id"]),
        project_id=f"tenant-{current_user['tenant_id']}-{int(time.time())}",
    )

    findings = result.get("anomalies", []) if result else []
    if not isinstance(findings, list):
        findings = [str(findings)]

    return {
        "status": result.get("status", "success") if result else "fallback",
        "findings": findings,
        "message": result.get("risk_assessment", {}).get("summary", "Vryndara processed logs.") if result else "Fallback analysis completed.",
    }

@router.post("/research/framework", response_model=ResearchResponse)
async def research_framework(
    request: ResearchRequest = Body(..., example={"framework": "ISO27001", "query": "Access controls"}),
    current_user=Depends(get_current_user),
):
    """Query Vryndara for compliance framework research."""
    project_id = f"tenant-{current_user['tenant_id']}-{int(time.time())}"
    connector = get_vryndara_connector()
    result = connector.research_compliance_framework(request.framework, project_id)
    return {
        "framework": result.get("framework", request.framework),
        "findings": result.get("controls", []),
        "summary": result.get("description", result.get("status", "")),
        "status": result.get("status", "completed"),
    }

@router.post("/generate/audit-script", response_model=AuditScriptResponse)
async def generate_audit_script(
    request: GenerateScriptRequest,
    current_user=Depends(get_current_user),
):
    """Generate an automated audit validation script."""
    connector = get_vryndara_connector()
    result = connector.generate_audit_script(
        framework=request.framework,
        check_type=request.check_type,
        zone_id=request.zone_id,
    )
    return {
        "status": result.get("status", "success"),
        "message": result.get("message", "Audit script generated successfully."),
        "script": result.get("code", ""),
    }

@router.post("/robotic/command", response_model=RobotCommandResponse)
async def robotic_command(
    request: RobotCommandRequest,
    current_user=Depends(get_current_user),
):
    """Dispatch a robotic command through Vryndara."""
    connector = get_vryndara_connector()
    result = connector.send_robotic_command(
        robot_type=request.robot_type,
        action=request.action,
        parameters=request.parameters,
        security_token=request.security_token,
    )
    return {
        "status": result.get("status", "completed"),
        "message": result.get("message", "Robotic command dispatched."),
        "result": result,
    }

# Day 31 Test Endpoint (no auth required)
@router.get("/test/connector", response_model=ResearchResponse)
async def test_connector():
    """Test Vryndara connector in fallback mode (Day 31)."""
    connector = get_vryndara_connector()
    result = connector.research_compliance_framework(
        standard="ISO27001",
        project_id="test-day31-001"
    )
    return {
        "framework": "ISO27001",
        "findings": result.get("controls", []) if result else [],
        "summary": result.get("description", "Test fallback mode") if result else "Test fallback mode",
        "status": "fallback" if not connector.is_connected else "connected",
    }
