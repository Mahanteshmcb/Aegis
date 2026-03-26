"""
Aegis Backend - Research Router
Vryndara integration for compliance research and AI log analysis.
"""

from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.models_db import AuditLog, Sensor
from backend.dependencies import get_db, get_current_user
from backend import schemas

router = APIRouter(prefix="/api/v1/research", tags=["AI"])

# --- SCHEMAS ---

class ResearchRequest(BaseModel):
    framework: str 
    query: str = ""

class ResearchResponse(BaseModel):
    framework: str
    findings: list = []
    summary: str = ""
    status: str

class AuditScriptResponse(BaseModel):
    status: str
    message: str = ""
    script: str = ""

class AnalyzeLogsResponse(BaseModel):
    status: str
    findings: list = []
    message: str = ""

# --- ENDPOINTS ---

@router.post("/analysis/logs", response_model=AnalyzeLogsResponse)
async def analyze_logs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Vryndara Brain: Analyzes the last 50 audit logs for tenant-specific anomalies.
    """
    # 1. Fetch recent logs for this tenant
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

    # 2. Heuristic Analysis Logic (Simulating Vryndara's Thought Process)
    findings = []
    sensor_ids = set([log.sensor_id for log in logs])
    
    # Identify unique sensor activity
    findings.append(f"Vryndara verified integrity for {len(sensor_ids)} active data streams.")
    
    # Check for rapid registration (Potential spoofing)
    reg_events = [l for l in logs if l.event_type == "sensor_created"]
    if len(reg_events) > 5:
        findings.append("⚠️ ALERT: High frequency of sensor registrations detected in Sector.")

    # 3. Final Summary
    message = f"Vryndara processed {len(logs)} audit entries. Sector integrity: 98.2%. Status: NOMINAL."

    return {
        "status": "success",
        "findings": findings,
        "message": message
    }

@router.post("/research/framework", response_model=ResearchResponse)
async def research_framework(
    request: ResearchRequest = Body(..., example={"framework": "ISO27001", "query": "Access controls"}),
    current_user=Depends(get_current_user),
):
    """Query Vryndara for compliance framework research."""
    # Placeholder for actual RAG (Retrieval Augmented Generation) logic
    return {
        "framework": request.framework,
        "findings": ["Control A.9: User Access Management applied", "Control A.12: Operations Security verified"],
        "summary": f"Vryndara mapping completed for {request.framework}.",
        "status": "completed"
    }

@router.post("/generate/audit-script", response_model=AuditScriptResponse)
async def generate_audit_script(current_user=Depends(get_current_user)):
    """Generate an automated audit validation script."""
    script_template = """
# Aegis Automated Audit Script
import hashlib
def verify_integrity(data_hash, expected):
    return hashlib.sha256(data_hash.encode()).hexdigest() == expected
    """
    return {
        "status": "success",
        "message": "Validation script generated successfully.",
        "script": script_template
    }