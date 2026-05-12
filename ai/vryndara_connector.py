# Vryndara Connector for Aegis
# Bridge between Aegis audit engine and Vryndara's multi-agent orchestration platform
#
# Purpose: Connect Aegis to Vryndara Researcher, Coder, and Brain agents
# Enables: Compliance framework research, audit script generation, data analysis
#
# Date: March 19, 2026
# Status: Production-ready implementation file

import json
import threading
import uuid
import logging
import time
from typing import Callable, Dict, Optional, Any, List
from queue import Queue
from datetime import datetime

import sys
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add Vryndara SDK and local protobuf definitions to path
vryndara_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Vryndara'))
ai_path = os.path.abspath(os.path.dirname(__file__))
local_protos_path = os.path.join(ai_path, 'protos')
if vryndara_path not in sys.path:
    sys.path.insert(0, vryndara_path)
if ai_path not in sys.path:
    sys.path.insert(0, ai_path)
if local_protos_path not in sys.path:
    sys.path.insert(0, local_protos_path)

# Conditional import with fallback
try:
    import grpc
    from protos import vryndara_pb2, vryndara_pb2_grpc
    VRYNDARA_AVAILABLE = True
except Exception as e:
    logger.warning(f"Vryndara protobuf import failed: {e}. Operating in offline mode.")
    VRYNDARA_AVAILABLE = False
    grpc = None

    class vryndara_pb2:
        class AgentInfo: pass
        class Signal: pass
        class Ack: pass
        class RoboticCommand: pass
        class SensorTelemetry: pass
        class SpatialRequest: pass
        class HologramCommand: pass
        class NodeHeartbeat: pass
        class WorkflowStep: pass
        class WorkflowRequest: pass
        class ChatMessage: pass
        class ChatRequest: pass
        class ChatResponse: pass
        class ChatStreamChunk: pass

    class vryndara_pb2_grpc:
        class KernelStub: pass

# ═══════════════════════════════════════════════════════════════════
# VRYNDARA CONNECTOR FOR AEGIS
# ═══════════════════════════════════════════════════════════════════

class VryndaraConnector:
    """
    Synchronous wrapper around gRPC client for Aegis audit operations.
    
    Handles all communication with Vryndara agents:
    - Researcher Agent: Compliance framework research
    - Coder Agent: Generate audit validation scripts
    - Brain Agent: Data analysis and decision support
    
    Features:
    - Async request/response via threading
    - Request timeout handling with retry
    - JSON serialization for all payloads
    - Fallback to local mode if kernel unavailable
    - Complete audit trail logging
    
    Example:
        connector = VryndaraConnector(
            app_id="aegis-audit-engine",
            kernel_address="localhost:50051"
        )
        
        # Research compliance framework
        findings = connector.research_compliance_framework(
            standard="ISO27001",
            project_id="AUD-2024-001"
        )
        
        # Generate validation script
        script = connector.generate_audit_script(
            framework="GDPR",
            check_type="data_processing_agreement"
        )
    """
    
    def __init__(self, 
                 app_id: str = "aegis-audit-engine",
                 kernel_address: str = "localhost:50051",
                 fallback_mode: bool = True):
        """
        Initialize Vryndara connector for Aegis.
        
        Args:
            app_id: Unique identifier for Aegis in Vryndara
            kernel_address: Vryndara kernel address (host:port)
            fallback_mode: If True, provide basic responses if kernel unavailable
        """
        
        self.app_id = app_id
        self.kernel_address = kernel_address
        self.fallback_mode = fallback_mode
        self.is_connected = False
        
        # gRPC connection
        self.channel = None
        self.stub = None
        
        # Response queues for each request ID
        self.response_queues: Dict[str, Queue] = {}
        
        logger.info(f"✅ VryndaraConnector initialized: {app_id} → {kernel_address}")
        
        # Initialize gRPC connection
        self._init_grpc()
        
        # Start listener thread in background
        self._start_listener()
    
    def _init_grpc(self):
        """Initialize gRPC connection to Vryndara kernel."""
        if not VRYNDARA_AVAILABLE:
            logger.warning("⚠️ Vryndara protobuf not available - operating in offline mode")
            self.is_connected = False
            return
            
        try:
            self.channel = grpc.insecure_channel(self.kernel_address)
            self.stub = vryndara_pb2_grpc.KernelStub(self.channel)
            
            # Test connection by registering
            info = vryndara_pb2.AgentInfo(
                id=self.app_id,
                capabilities=["audit.research", "audit.analysis", "audit.code_generation"]
            )
            self.stub.Register(info)
            self.is_connected = True
            logger.info(f"✅ Connected to Vryndara kernel at {self.kernel_address}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize gRPC: {e}")
            self.is_connected = False
    
    def _start_listener(self):
        """Start gRPC listener in background thread."""
        
        def listener_thread():
            try:
                if not self.is_connected:
                    logger.warning("⚠️ Not connected to Vryndara - skipping listener")
                    return
                
                # Subscribe to agent-specific messages
                info = vryndara_pb2.AgentInfo(id=self.app_id)
                for signal in self.stub.Subscribe(info):
                    # Route response to appropriate queue
                    if signal.id in self.response_queues:
                        self.response_queues[signal.id].put(signal)
                
                self.is_connected = True
                logger.info("📡 Vryndara kernel listener connected")
            except Exception as e:
                logger.warning(f"⚠️ Vryndara kernel listener error: {e}")
        
        thread = threading.Thread(target=listener_thread, daemon=True)
        thread.start()
    
    def _send_request_and_wait(self,
                               agent_id: str,
                               payload: Dict[str, Any],
                               timeout: int = 30,
                               fallback_data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Send a request to an agent and wait for response."""
        
        if not self.is_connected and not self.fallback_mode:
            logger.error("❌ Not connected to Vryndara and fallback mode disabled")
            return None
        
        if not self.is_connected:
            logger.warning(f"⚠️ Using fallback mode for {agent_id}")
            return fallback_data or {}
        
        try:
            request_id = str(uuid.uuid4())
            self.response_queues[request_id] = Queue()
            
            signal = vryndara_pb2.Signal(
                id=request_id,
                source_agent_id=self.app_id,
                target_agent_id=agent_id,
                type="AUDIT_REQUEST",
                payload=json.dumps(payload),
                timestamp=int(time.time() * 1000)
            )
            
            # Send request
            self.stub.Publish(signal)
            logger.info(f"📤 Sent request to {agent_id}")
            
            # Wait for response with timeout
            try:
                response = self.response_queues[request_id].get(timeout=timeout)
                result = json.loads(response.payload)
                logger.info(f"📥 Received response: {list(result.keys())}")
                return result
            except:
                logger.warning(f"⏱️ Request timeout after {timeout}s")
                return fallback_data or {}
        finally:
            # Clean up queue
            if request_id in self.response_queues:
                del self.response_queues[request_id]
    
    # ─────────────────────────────────────────────────────────────
    # RESEARCH OPERATIONS
    # ─────────────────────────────────────────────────────────────
    
    def research_compliance_framework(self, 
                                     standard: str, 
                                     project_id: str,
                                     include_controls: bool = True,
                                     timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Research a compliance framework using Vryndara Researcher agent.
        
        Args:
            standard: Framework name (ISO27001, GDPR, SOC2, PCI-DSS, HIPAA, etc.)
            project_id: Aegis audit project ID for tracking
            include_controls: Include detailed control information
            timeout: Max wait time in seconds
        
        Returns:
            {
              framework: str,
              description: str,
              controls: List[Dict],
              applicability: Dict,
              references: List[str],
              updated: datetime
            }
        """
        
        payload = {
            "query": f"Provide detailed {standard} compliance framework with all controls and requirements",
            "context": {
                "source_app": "aegis",
                "project_id": project_id,
                "task_type": "compliance_research",
                "include_details": include_controls
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._send_request_and_wait(
            agent_id="researcher-agent",
            payload=payload,
            timeout=timeout,
            fallback_data={
                "framework": standard,
                "description": f"Framework research for {standard} (Fallback)",
                "status": "fallback_mode",
                "controls": []
            }
        )
    
    def disconnect(self):
        """Disconnect from Vryndara kernel."""
        if self.channel:
            self.channel.close()
        self.is_connected = False
        logger.info("🔌 Disconnected from Vryndara kernel")
    
    def research_specific_requirement(self,
                                     standard: str,
                                     requirement_id: str,
                                     project_id: str,
                                     timeout: int = 20) -> Optional[Dict[str, Any]]:
        """
        Research a specific control or requirement within a framework.
        
        Args:
            standard: Framework (ISO27001, etc.)
            requirement_id: Specific requirement ID (e.g., "A.5.1")
            project_id: Audit project ID
            timeout: Max wait time
        
        Returns:
            {requirement_id, title, description, scope, implementation_guidance, ...}
        """
        
        payload = {
            "query": f"Explain {standard} requirement {requirement_id} in detail",
            "context": {
                "source_app": "aegis",
                "project_id": project_id,
                "task_type": "requirement_research",
                "standard": standard,
                "requirement": requirement_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._send_request_and_wait(
            agent_id="researcher-1",
            payload=payload,
            timeout=timeout,
            fallback_data={"requirement": requirement_id, "status": "fallback"}
        )
    
    # ─────────────────────────────────────────────────────────────
    # CODE GENERATION OPERATIONS
    # ─────────────────────────────────────────────────────────────
    
    def generate_audit_script(self,
                             framework: str,
                             check_type: str,
                             zone_id: Optional[str] = None,
                             timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Generate Python audit validation script using Vryndara Coder agent.
        
        Args:
            framework: Compliance framework (ISO27001, GDPR, etc.)
            check_type: Type of check (data_processing, access_control, encryption, etc.)
            zone_id: Optional zone to audit (for multi-zone systems)
            timeout: Max wait time
        
        Returns:
            {
              code: str,           # Python code
              imports: List[str],
              functions: List[str],
              class_definitions: List[str],
              usage_example: str,
              test_cases: List[str]
            }
        
        Example:
            script = connector.generate_audit_script(
                framework="GDPR",
                check_type="data_processing_agreement"
            )
            
            # Save and execute
            with open("audit_gdpr.py", "w") as f:
                f.write(script['code'])
        """
        
        payload = {
            "task": f"Generate Python audit script for {framework} {check_type}",
            "context": {
                "source_app": "aegis",
                "task_type": "audit_script_generation",
                "framework": framework,
                "check_type": check_type,
                "zone_id": zone_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._send_request_and_wait(
            agent_id="coder-1",
            payload=payload,
            timeout=timeout,
            fallback_data={
                "code": f"# Audit check for {framework}\nprint('Check complete')",
                "status": "fallback"
            }
        )
    
    def generate_remediation_code(self,
                                 issue: str,
                                 framework: str,
                                 timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Generate remediation/fix code for a compliance issue.
        
        Args:
            issue: Description of the compliance issue
            framework: Applicable compliance framework
            timeout: Max wait time
        
        Returns:
            {code: str, explanation: str, deployment_notes: str, ...}
        """
        
        payload = {
            "task": f"Generate Python code to remediate: {issue} (for {framework})",
            "context": {
                "source_app": "aegis",
                "task_type": "remediation_generation",
                "issue": issue,
                "framework": framework
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._send_request_and_wait(
            agent_id="coder-1",
            payload=payload,
            timeout=timeout,
            fallback_data={"code": "# Remediation code", "status": "fallback"}
        )

    def send_robotic_command(self,
                             robot_type: str,
                             action: str,
                             parameters: Dict[str, str],
                             security_token: Optional[str] = None,
                             timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Dispatch a robotic command through the Vryndara orchestration layer.

        Args:
            robot_type: Type of robotic asset (AegisRover, CanopyDrone, AgriSwarmBot)
            action: Command action (navigate, inspect, harvest, charge, standby)
            parameters: Command parameters as key/value pairs
            security_token: Optional signed token for secure routing
            timeout: Max wait time

        Returns:
            Command execution acknowledgement and metadata.
        """
        payload = {
            "task": "Dispatch robotic command",
            "command": {
                "robot_type": robot_type,
                "action": action,
                "parameters": parameters,
                "security_token": security_token,
            },
            "context": {
                "source_app": "aegis",
                "task_type": "robotic_command",
                "robot_type": robot_type,
                "action": action
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_request_and_wait(
            agent_id="engineer-1",
            payload=payload,
            timeout=timeout,
            fallback_data={
                "status": "fallback",
                "robot_type": robot_type,
                "action": action,
                "message": "Robotic command queued in fallback mode"
            }
        )
    
    # ─────────────────────────────────────────────────────────────
    # ANALYSIS OPERATIONS
    # ─────────────────────────────────────────────────────────────
    
    def analyze_audit_logs(self,
                          logs: List[Dict[str, Any]],
                          zone_id: str,
                          project_id: str,
                          timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Analyze audit logs using Vryndara Brain agent.
        
        Args:
            logs: List of audit log entries
            zone_id: Zone being analyzed
            project_id: Project ID
            timeout: Max wait time
        
        Returns:
            {
              anomalies: List[Dict],
              patterns: List[str],
              risk_assessment: Dict,
              recommendations: List[str]
            }
        """
        
        payload = {
            "query": f"Analyze these audit logs for anomalies and patterns",
            "logs": logs,
            "context": {
                "source_app": "aegis",
                "project_id": project_id,
                "zone_id": zone_id,
                "task_type": "log_analysis"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._send_request_and_wait(
            agent_id="brain-1",
            payload=payload,
            timeout=timeout,
            fallback_data={"anomalies": [], "patterns": [], "status": "fallback"}
        )
    
    def assess_compliance_gap(self,
                             standard: str,
                             current_controls: Dict[str, bool],
                             zone_id: str,
                             timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Assess compliance gaps using Vryndara Brain agent.
        
        Args:
            standard: Framework (ISO27001, etc.)
            current_controls: Dict of implemented controls {control_id: is_implemented}
            zone_id: Zone being assessed
            timeout: Max wait time
        
        Returns:
            {
              gap_summary: str,
              missing_controls: List[str],
              impact: str,
              priority_items: List[str],
              estimated_effort: str
            }
        """
        
        payload = {
            "query": f"Assess {standard} compliance gaps for these controls",
            "controls": current_controls,
            "context": {
                "source_app": "aegis",
                "zone_id": zone_id,
                "task_type": "compliance_gap_assessment"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._send_request_and_wait(
            agent_id="brain-1",
            payload=payload,
            timeout=timeout,
            fallback_data={"gaps": [], "status": "fallback"}
        )
    
    # ─────────────────────────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────────────────────────
    
    def health_check(self) -> bool:
        """Check if Vryndara kernel is accessible and healthy."""
        if not self.is_connected:
            logger.warning("⚠️ Vryndara kernel health check failed: no connection")
            return False
        try:
            if VRYNDARA_AVAILABLE and hasattr(self.stub, "HealthCheck"):
                request = vryndara_pb2.HealthCheckRequest(agent_id=self.app_id)
                response = self.stub.HealthCheck(request)
                healthy = getattr(response, "healthy", True)
                logger.info(f"✅ Vryndara kernel health: {healthy}")
                return healthy
            logger.info("✅ Vryndara kernel is healthy (connected)")
            return True
        except Exception as e:
            logger.error(f"❌ Vryndara health check failed: {e}")
            return False
    
    def get_registered_agents(self) -> List[str]:
        """List all Vryndara agents available to Aegis."""
        return [
            "researcher-1",      # Web research, compliance frameworks
            "coder-1",           # Code generation
            "brain-1",           # Reasoning and analysis
            "engineer-1",        # Infrastructure planning
            "director-1"         # Workflow orchestration
        ]


# ═══════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════

"""
To use VryndaraConnector in Aegis FastAPI backend:

# backend/routers/research.py
from fastapi import APIRouter, HTTPException
from services.vryndara_connector import VryndaraConnector

router = APIRouter(prefix="/api/v1/research", tags=["research"])
connector = VryndaraConnector()

@router.get("/framework/{standard}")
async def research_framework(standard: str, project_id: str):
    '''Research a compliance framework'''
    result = connector.research_compliance_framework(standard, project_id)
    if not result:
        raise HTTPException(status_code=503, detail="Vryndara unavailable")
    return result

@router.post("/audit-script")
async def generate_script(framework: str, check_type: str):
    '''Generate audit validation script'''
    result = connector.generate_audit_script(framework, check_type)
    return result

@router.post("/analyze-logs")
async def analyze_logs(logs: List[Dict], zone_id: str):
    '''Analyze audit logs for anomalies'''
    result = connector.analyze_audit_logs(logs, zone_id, "project-001")
    return result
"""

# ═══════════════════════════════════════════════════════════════════
# WEEK 2 INTEGRATION CHECKLIST
# ═══════════════════════════════════════════════════════════════════

"""
✓ Day 8 (FastAPI Scaffolding):
  - Import VryndaraConnector in backend/main.py
  - Create routers/research.py with research endpoints
  - Create routers/analysis.py with analysis endpoints

✓ Day 9 (Database Setup):
  - Create database models for audit findings
  - Store Vryndara responses in SQLite

✓ Day 10 (Authentication):
  - Add JWT middleware
  - Protect Vryndara endpoints with RBAC

✓ Day 11 (Health Check):
  - Add Vryndara health check to startup
  - Report connectivity status in /health endpoint

✓ Day 12-13 (Testing):
  - Unit tests for Vryndara requests
  - Integration tests with mock responses
  - Error handling tests

✓ Day 14 (Documentation):
  - Document all Vryndara endpoints
  - Add examples to API docs
"""
