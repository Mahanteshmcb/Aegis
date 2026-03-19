# Aegis-Vryndara Integration: Developer Quick Start

**Target Audience:** Aegis backend developers implementing Vryndara connectivity  
**Duration to Read:** 15 minutes  
**Last Updated:** March 19, 2026

---

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [Integration Patterns](#integration-patterns)
3. [Code Examples](#code-examples)
4. [Common Workflows](#common-workflows)
5. [Debugging & Troubleshooting](#debugging--troubleshooting)

---

## Quick Setup

### Step 1: Add Vryndara to Python Path

In your Aegis backend initialization:

```python
# aegis/config.py or aegis/__init__.py
import sys
import os

# Add Vryndara SDK to path
vryndara_path = os.path.join(os.path.dirname(__file__), '../../Vryndara')
if vryndara_path not in sys.path:
    sys.path.insert(0, vryndara_path)
```

### Step 2: Create VryndaraConnector Module

```python
# aegis/services/vryndara_connector.py
"""
Bridge between Aegis audit engine and Vryndara orchestration platform.
Handles all communication with Vryndara agents.
"""

import json
import threading
import uuid
from typing import Callable, Dict, Optional, Any
from queue import Queue
import logging

from sdk.python.vryndara.client import AgentClient
from sdk.python.vryndara.storage import StorageManager

logger = logging.getLogger(__name__)

class VryndaraConnector:
    """
    Synchronous wrapper around gRPC client for Aegis audit workflows.
    Handles async request/response via threading.
    """
    
    def __init__(self, 
                 aegis_app_id: str = "aegis-audit-engine",
                 kernel_address: str = "localhost:50051"):
        """Initialize Vryndara connector."""
        
        self.app_id = aegis_app_id
        self.kernel_address = kernel_address
        self.client = AgentClient(aegis_app_id, kernel_address=kernel_address)
        
        # Response queues for each agent
        self.response_queues: Dict[str, Queue] = {}
        
        # Start listener in background
        self._start_listener()
        
        logger.info(f"✅ VryndaraConnector initialized: {aegis_app_id}")
    
    def _start_listener(self):
        """Start gRPC listener in background thread."""
        
        def listener_thread():
            try:
                self.client.register([
                    "audit.research",
                    "audit.analysis",
                    "audit.code_generation",
                    "audit.framework"
                ])
                
                def on_message(signal):
                    # Route responses to appropriate queues
                    if signal.source_agent_id not in self.response_queues:
                        self.response_queues[signal.source_agent_id] = Queue()
                    
                    self.response_queues[signal.source_agent_id].put(signal)
                
                self.client.listen(on_message)
            except Exception as e:
                logger.error(f"❌ Listener error: {e}")
        
        thread = threading.Thread(target=listener_thread, daemon=True)
        thread.start()
        logger.info("📡 Background listener started")
    
    # ─────────────────────────────────────────────────────────────
    # PUBLIC API: Audit-Specific Operations
    # ─────────────────────────────────────────────────────────────
    
    def research_compliance_framework(self, 
                                     standard: str, 
                                     project_id: str,
                                     timeout: int = 30) -> Optional[str]:
        """
        Research a compliance framework (ISO27001, SOC2, GDPR, etc).
        
        Args:
            standard: Framework name (e.g., "ISO27001", "GDPR")
            project_id: Aegis audit project ID
            timeout: Max wait time in seconds
        
        Returns:
            Research findings as JSON string, or None if timeout
        
        Example:
            findings = connector.research_compliance_framework("GDPR", "AUD-2024-001")
            print(findings)  # "GDPR Article 5 covers data principles..."
        """
        
        payload = {
            "query": f"Find {standard} compliance requirements and controls",
            "context": {
                "source_app": "aegis",
                "project_id": project_id,
                "task_type": "compliance_research"
            }
        }
        
        return self._send_request_and_wait(
            agent_id="researcher-1",
            payload=payload,
            timeout=timeout
        )
    
    def analyze_audit_gaps(self,
                          current_state: Dict[str, Any],
                          framework_data: str,
                          project_id: str,
                          timeout: int = 30) -> Optional[str]:
        """
        Analyze gaps between current state and framework requirements.
        
        Args:
            current_state: Current audit findings
            framework_data: Framework requirements from research
            project_id: Audit project ID
            timeout: Max wait time
        
        Returns:
            Gap analysis results
        """
        
        payload = {
            "task": "analyze_gaps",
            "current_state": current_state,
            "framework": framework_data,
            "context": {
                "source_app": "aegis",
                "project_id": project_id
            }
        }
        
        # Future: Will route to analyzer agent once implemented
        # For now, use researcher for gap analysis via LLM
        payload["query"] = f"Analyze gaps: current {current_state} vs required {framework_data[:200]}"
        
        return self._send_request_and_wait(
            agent_id="researcher-1",
            payload=payload,
            timeout=timeout
        )
    
    def generate_audit_code(self,
                           audit_type: str,
                           requirements: str,
                           project_id: str,
                           timeout: int = 30) -> Optional[str]:
        """
        Generate Python code for audit automation.
        
        Args:
            audit_type: Type of audit (e.g., "access_review", "config_check")
            requirements: Specific requirements to check
            project_id: Audit project ID
            timeout: Max wait time
        
        Returns:
            Generated Python code
        
        Example:
            code = connector.generate_audit_code(
                "access_review",
                "Check that all user accounts have MFA enabled",
                "AUD-2024-001"
            )
            # Returns Python code that performs the check
        """
        
        payload = {
            "instruction": f"Generate {audit_type} code to {requirements}",
            "context": {
                "source_app": "aegis",
                "project_id": project_id,
                "audit_type": audit_type
            },
            "language": "python"
        }
        
        return self._send_request_and_wait(
            agent_id="coder-alpha",
            payload=payload,
            timeout=timeout
        )
    
    # ─────────────────────────────────────────────────────────────
    # INTERNAL: Request/Response Handling
    # ─────────────────────────────────────────────────────────────
    
    def _send_request_and_wait(self,
                              agent_id: str,
                              payload: Dict[str, Any],
                              timeout: int = 30) -> Optional[str]:
        """
        Send request to agent and wait for response (blocking).
        
        Args:
            agent_id: Target agent ID
            payload: Request payload (will be JSON-encoded)
            timeout: Max wait time in seconds
        
        Returns:
            Agent response payload, or None if timeout
        """
        
        # Create response queue for this agent if needed
        if agent_id not in self.response_queues:
            self.response_queues[agent_id] = Queue()
        
        # Send request
        self.client.send(
            target_id=agent_id,
            msg_type="TASK_REQUEST",
            payload=json.dumps(payload)
        )
        
        logger.info(f"📤 Sent request to {agent_id}")
        
        # Wait for response
        try:
            signal = self.response_queues[agent_id].get(timeout=timeout)
            
            if signal.type == "TASK_RESULT":
                logger.info(f"📥 Received result from {agent_id}")
                return signal.payload
            else:
                logger.warning(f"⚠️ Unexpected signal type: {signal.type}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Timeout waiting for {agent_id}: {e}")
            return None
    
    # ─────────────────────────────────────────────────────────────
    # STORAGE: File Management
    # ─────────────────────────────────────────────────────────────
    
    def upload_audit_report(self,
                           local_path: str,
                           audit_id: str,
                           report_type: str = "report") -> Optional[str]:
        """
        Upload audit report to Vryndara storage.
        
        Args:
            local_path: Local file path
            audit_id: Audit identifier
            report_type: Type of report (report, evidence, etc)
        
        Returns:
            Accessible URL, or None if failed
        """
        
        storage = StorageManager(bucket_name="aegis-audits")
        
        # Generate object name
        object_name = f"{audit_id}/{report_type}_{uuid.uuid4().hex[:8]}.pdf"
        
        try:
            url = storage.upload_file(local_path, object_name=object_name)
            logger.info(f"✅ Uploaded to {url}")
            return url
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return None
    
    def download_audit_report(self,
                             audit_id: str,
                             object_name: str,
                             local_path: str) -> bool:
        """
        Download audit report from storage.
        
        Args:
            audit_id: Audit identifier
            object_name: Object name in storage
            local_path: Where to save locally
        
        Returns:
            True if successful, False otherwise
        """
        
        storage = StorageManager(bucket_name="aegis-audits")
        
        try:
            success = storage.download_file(object_name, local_path)
            if success:
                logger.info(f"✅ Downloaded to {local_path}")
            return success
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return False


# ─────────────────────────────────────────────────────────────
# SINGLETON: Global instance
# ─────────────────────────────────────────────────────────────

_vryndara_connector = None

def get_vryndara_connector() -> VryndaraConnector:
    """Get or create global Vryndara connector instance."""
    global _vryndara_connector
    
    if _vryndara_connector is None:
        _vryndara_connector = VryndaraConnector()
    
    return _vryndara_connector
```

### Step 3: Use in Aegis Services

```python
# aegis/services/audit_service.py
from aegis.services.vryndara_connector import get_vryndara_connector
import json

class AuditService:
    def __init__(self):
        self.vryndara = get_vryndara_connector()
    
    def create_iso27001_audit(self, project_id: str, scope: str):
        """Create ISO27001 audit using Vryndara for research."""
        
        # Step 1: Research ISO 27001 requirements
        framework_data = self.vryndara.research_compliance_framework(
            standard="ISO27001",
            project_id=project_id
        )
        
        if not framework_data:
            raise Exception("Failed to retrieve ISO27001 framework")
        
        # Step 2: Analyze gaps
        gap_analysis = self.vryndara.analyze_audit_gaps(
            current_state={"scope": scope},
            framework_data=framework_data,
            project_id=project_id
        )
        
        # Step 3: Generate audit scripts
        audit_code = self.vryndara.generate_audit_code(
            audit_type="iso27001_assessment",
            requirements=gap_analysis or framework_data,
            project_id=project_id
        )
        
        # Step 4: Create audit record
        audit = {
            "project_id": project_id,
            "standard": "ISO27001",
            "framework": json.loads(framework_data) if framework_data else {},
            "gaps": gap_analysis,
            "automation_code": audit_code,
            "status": "IN_PROGRESS"
        }
        
        # Save to Aegis database
        return self.save_audit(audit)
```

---

## Integration Patterns

### Pattern 1: Sequential Research → Analysis → Reporting

```
User Request
    ↓
Research Framework (Vryndara Researcher)
    ↓
Analyze Gaps (Vryndara Researcher or future Analyzer)
    ↓
Generate Report (Future Reporter Agent)
    ↓
Upload to Storage (MinIO)
    ↓
Return to User
```

**Code:**
```python
def full_audit_workflow(self, standard: str, project_id: str):
    # 1. Research
    framework = self.vryndara.research_compliance_framework(standard, project_id)
    
    # 2. Analyze current state
    findings = self.scan_current_state()  # Local Aegis scan
    gaps = self.analyze_gaps(findings, framework)
    
    # 3. Generate report (when reporter agent available)
    # report = self.vryndara.generate_report(gaps, standard)
    
    # 4. Save report
    report_path = self.generate_local_report(gaps, standard)
    url = self.vryndara.upload_audit_report(report_path, project_id)
    
    return {"url": url, "gaps": gaps}
```

### Pattern 2: Parallel Agent Requests

```
For Multiple Frameworks:
  ├─ Research GDPR (Researcher)
  ├─ Research ISO27001 (Researcher)
  └─ Research SOC2 (Researcher)
      ↓
All complete → Synthesize → Return
```

**Code:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def multi_framework_audit(self, frameworks: List[str], project_id: str):
    results = {}
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(
                self.vryndara.research_compliance_framework,
                standard,
                project_id
            ): standard
            for standard in frameworks
        }
        
        for future in as_completed(futures):
            standard = futures[future]
            try:
                results[standard] = future.result(timeout=60)
            except Exception as e:
                results[standard] = f"Error: {e}"
    
    return results
```

### Pattern 3: Context Retention Across Sessions

```
Session 1:
  ├─ Research framework
  ├─ Store in Vryndara memory
  └─ Store in Aegis database

Session 2 (Later):
  ├─ Retrieve from Vryndara memory (faster, semantic)
  ├─ Retrieve from Aegis database (persistent)
  └─ Use for follow-up audit
```

**Code:**
```python
def get_framework_with_cache(self, standard: str, project_id: str):
    # Try Aegis database first
    cached = self.database.get_framework(standard, project_id)
    if cached:
        return cached
    
    # Fetch from Vryndara (triggers research agent)
    framework = self.vryndara.research_compliance_framework(standard, project_id)
    
    # Cache in Aegis
    self.database.save_framework(standard, project_id, framework)
    
    return framework
```

---

## Code Examples

### Example 1: Complete Audit Workflow

```python
# aegis/workflows/iso27001_audit.py
from aegis.services.vryndara_connector import get_vryndara_connector
from aegis.models import Audit, Finding
import json

class ISO27001AuditWorkflow:
    """End-to-end ISO27001 audit using Vryndara."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.vryndara = get_vryndara_connector()
        self.audit = None
    
    def execute(self):
        """Run the full audit workflow."""
        
        print("🔍 Starting ISO27001 Audit...")
        
        # Phase 1: Research
        print("📚 Phase 1: Researching ISO27001...")
        framework = self.vryndara.research_compliance_framework(
            standard="ISO27001",
            project_id=self.project_id
        )
        
        if not framework:
            raise Exception("Failed to retrieve ISO27001 framework")
        
        framework_dict = json.loads(framework)
        
        # Phase 2: Create audit record
        print("📋 Phase 2: Creating audit record...")
        self.audit = Audit.objects.create(
            project_id=self.project_id,
            standard="ISO27001",
            framework_reference=framework_dict,
            status="IN_PROGRESS"
        )
        
        # Phase 3: Generate audit code
        print("⚙️ Phase 3: Generating audit code...")
        code = self.vryndara.generate_audit_code(
            audit_type="iso27001_assessment",
            requirements=framework,
            project_id=self.project_id
        )
        
        if code:
            self.audit.automation_code = code
            self.audit.save()
        
        # Phase 4: Scan current state (local implementation)
        print("🔎 Phase 4: Scanning current state...")
        current_findings = self._perform_local_scan()
        
        # Phase 5: Analyze gaps
        print("📊 Phase 5: Analyzing gaps...")
        gaps = self._analyze_gaps(current_findings, framework_dict)
        
        # Phase 6: Create findings
        print("✏️ Phase 6: Documenting findings...")
        for gap in gaps:
            Finding.objects.create(
                audit=self.audit,
                category=gap.get("control_id"),
                description=gap.get("description"),
                severity=gap.get("severity", "MEDIUM"),
                remediation=gap.get("remediation")
            )
        
        # Phase 7: Mark complete
        print("✅ Phase 7: Finalizing audit...")
        self.audit.status = "COMPLETED"
        self.audit.save()
        
        return self.audit
    
    def _perform_local_scan(self):
        """Local scanning (Aegis-specific)."""
        # Implement your local scan logic
        return []
    
    def _analyze_gaps(self, findings, framework):
        """Analyze gaps between current and required state."""
        # Implement analysis logic
        return []

# Usage:
def start_audit(project_id: str):
    workflow = ISO27001AuditWorkflow(project_id)
    audit = workflow.execute()
    return audit
```

### Example 2: Handling Async Responses

```python
# aegis/services/async_audit_service.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from aegis.services.vryndara_connector import get_vryndara_connector

class AsyncAuditService:
    """Handle long-running Vryndara requests without blocking."""
    
    def __init__(self):
        self.vryndara = get_vryndara_connector()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def research_framework_async(self, standard: str, project_id: str, callback):
        """
        Request framework research without blocking.
        
        Args:
            standard: Framework name
            project_id: Project ID
            callback: Function to call with results
        """
        
        def worker():
            result = self.vryndara.research_compliance_framework(
                standard=standard,
                project_id=project_id
            )
            callback(standard, result)
        
        self.executor.submit(worker)
    
    def on_framework_ready(self, standard: str, framework: str):
        """Callback when framework research completes."""
        
        if framework:
            # Update database
            from aegis.models import FrameworkReference
            FrameworkReference.objects.update_or_create(
                standard=standard,
                defaults={"content": framework}
            )
            
            # Trigger analysis
            print(f"✅ {standard} framework ready. Starting analysis...")
        else:
            print(f"❌ Failed to research {standard}")

# Usage:
service = AsyncAuditService()
service.research_framework_async(
    "GDPR",
    "AUD-2024-001",
    callback=service.on_framework_ready
)
# Function returns immediately; result processed in callback
```

### Example 3: Error Handling & Resilience

```python
# aegis/services/resilient_vryndara_connector.py
from aegis.services.vryndara_connector import VryndaraConnector
import time
import random

class ResilientVryndaraConnector(VryndaraConnector):
    """Enhanced connector with retry logic and fallbacks."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def _send_request_and_wait(self, agent_id, payload, timeout=30):
        """Override with retry logic."""
        
        for attempt in range(1, self.max_retries + 1):
            try:
                result = super()._send_request_and_wait(
                    agent_id=agent_id,
                    payload=payload,
                    timeout=timeout
                )
                
                if result:
                    return result
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(f"⚠️ Attempt {attempt} failed. Retrying in {wait_time}s...")
                    time.sleep(wait_time + random.uniform(0, 1))  # Add jitter
            
            except Exception as e:
                logger.error(f"❌ Attempt {attempt} error: {e}")
                
                if attempt == self.max_retries:
                    logger.error(f"❌ All {self.max_retries} retries failed")
                    return self._fallback_response(payload)
        
        return None
    
    def _fallback_response(self, payload):
        """Provide fallback response when Vryndara unavailable."""
        
        # This could be:
        # 1. Locally cached response from database
        # 2. Generic template response
        # 3. Error state that triggers manual review
        
        logger.warning("⚠️ Using fallback response (Vryndara unavailable)")
        
        query = payload.get("query", "unknown")
        return json.dumps({
            "status": "FALLBACK_MODE",
            "message": f"Vryndara unavailable. Manual review needed for: {query}",
            "timestamp": time.time()
        })

# Usage:
vryndara = ResilientVryndaraConnector()
result = vryndara.research_compliance_framework("ISO27001", "AUD-001")
# Automatically retries with exponential backoff if Vryndara unavailable
```

---

## Common Workflows

### Workflow 1: Create and Run Audit

```python
# aegis/views/audit_views.py (Django example)
from django.http import JsonResponse
from aegis.workflows.iso27001_audit import ISO27001AuditWorkflow

def create_audit(request):
    project_id = request.POST.get("project_id")
    
    # Create and execute workflow
    workflow = ISO27001AuditWorkflow(project_id)
    audit = workflow.execute()
    
    return JsonResponse({
        "audit_id": audit.id,
        "status": audit.status,
        "findings_count": audit.findings.count()
    })
```

### Workflow 2: Compare Audits Over Time

```python
# aegis/services/audit_comparison.py
class AuditComparisonService:
    def __init__(self, vryndara_connector):
        self.vryndara = vryndara_connector
    
    def compare_audits(self, audit_1_id: str, audit_2_id: str):
        """Compare findings across two audits."""
        
        audit_1 = Audit.objects.get(id=audit_1_id)
        audit_2 = Audit.objects.get(id=audit_2_id)
        
        # Analyze improvement
        findings_1 = set(audit_1.findings.values_list("category"))
        findings_2 = set(audit_2.findings.values_list("category"))
        
        resolved = findings_1 - findings_2
        new_issues = findings_2 - findings_1
        persistent = findings_1 & findings_2
        
        return {
            "resolved": len(resolved),
            "new_issues": len(new_issues),
            "persistent": len(persistent),
            "improvement": len(resolved) / max(len(findings_1), 1)
        }
```

### Workflow 3: Scheduled Compliance Checks

```
# Future: When Vryndara Scheduler Agent is ready

# aegis/tasks/scheduled_audits.py (Celery task example)
from celery import shared_task
from aegis.workflows.iso27001_audit import ISO27001AuditWorkflow

@shared_task
def run_scheduled_audit(project_id: str, standard: str):
    """Run audit on schedule (e.g., weekly)."""
    
    if standard == "ISO27001":
        workflow = ISO27001AuditWorkflow(project_id)
    else:
        # Add more workflows for other standards
        pass
    
    audit = workflow.execute()
    
    # Notify stakeholders if issues found
    if audit.findings.filter(severity="HIGH").exists():
        send_alert(f"High-severity findings in {standard} audit")
    
    return audit.id

# Schedule via celery beat:
# Every Monday at 9 AM:
# run_scheduled_audit.apply_async(
#     args=["PROJECT-001", "ISO27001"],
#     countdown=3600 * 24 * 7
# )
```

---

## Debugging & Troubleshooting

### Issue 1: "Connection refused" when connecting to Vryndara

**Symptoms:**
```
❌ Error: [Errno 111] Connection refused (localhost:50051)
```

**Solutions:**
1. Verify Vryndara kernel is running:
   ```bash
   ps aux | grep kernel/main.py
   # Should see: python kernel/main.py
   ```

2. Check if port 50051 is listening:
   ```bash
   # Windows PowerShell
   netstat -ano | findstr :50051
   
   # Linux/Mac
   lsof -i :50051
   ```

3. Restart kernel:
   ```bash
   # Terminal 1
   python kernel/main.py
   ```

### Issue 2: Agent doesn't respond (timeout)

**Symptoms:**
```
❌ Timeout waiting for researcher-1: ...
```

**Causes & Solutions:**
1. Agent not registered - Start the agent:
   ```bash
   python agents/researcher/main.py
   ```

2. Agent crashed - Check logs and restart

3. LLM unavailable - Ensure llama.cpp server running:
   ```bash
   # Terminal
   cd ...llama.cpp/build/bin/Release
   .\llama-server.exe -m mistral.gguf --port 8080
   ```

4. Slow inference - Check CPU usage, reduce timeout, or use faster model

### Issue 3: Import errors

**Error:**
```
ModuleNotFoundError: No module named 'vryndara'
```

**Solution:**
```python
# In your Aegis code
import sys
import os
vryndara_path = os.path.abspath("../../Vryndara")
sys.path.insert(0, vryndara_path)

from sdk.python.vryndara.client import AgentClient
```

### Issue 4: Storage upload fails

**Error:**
```
❌ Upload failed: Cannot connect to MinIO
```

**Solutions:**
1. Start MinIO:
   ```bash
   docker-compose up -d minio
   ```

2. Check credentials in `storage.py`:
   ```python
   # Should be:
   aws_access_key_id='admin'
   aws_secret_access_key='password123'
   endpoint_url='http://localhost:9000'
   ```

3. Create bucket via MinIO console:
   - http://localhost:9001
   - Login: admin / password123
   - Create bucket "aegis-audits"

### Debug Logging

Enable detailed logging in your Aegis code:

```python
import logging

# Enable all logging
logging.basicConfig(level=logging.DEBUG)

# Enable Vryndara logging
logging.getLogger('sdk.python.vryndara').setLevel(logging.DEBUG)
logging.getLogger('VryndaraConnector').setLevel(logging.DEBUG)

# Now all connector calls will log details
vryndara = VryndaraConnector()
vryndara.research_compliance_framework("ISO27001", "AUD-001")
# Output: 📤 Sent request to researcher-1
#         📥 Received result from researcher-1
```

### Testing Connectivity

Before integrating, test the connection:

```python
# aegis/tests/test_vryndara_connection.py
import unittest
from aegis.services.vryndara_connector import VryndaraConnector

class TestVryndaraConnection(unittest.TestCase):
    
    def setUp(self):
        self.connector = VryndaraConnector()
    
    def test_kernel_connection(self):
        """Test gRPC kernel connection."""
        # If this passes, kernel is running
        self.assertIsNotNone(self.connector.client)
    
    def test_researcher_response(self):
        """Test researcher agent responds."""
        result = self.connector.research_compliance_framework(
            "Test",
            "TEST-PROJECT"
        )
        self.assertIsNotNone(result, "Researcher agent did not respond")
    
    def test_coder_response(self):
        """Test coder agent responds."""
        result = self.connector.generate_audit_code(
            "test_audit",
            "test requirements",
            "TEST-PROJECT"
        )
        self.assertIsNotNone(result, "Coder agent did not respond")

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python -m unittest aegis/tests/test_vryndara_connection.py -v
```

---

## Checklist: Before Going Live

- [ ] Vryndara kernel running and stable (test 1 hour runtime)
- [ ] All required agents running (researcher, coder, media if needed)
- [ ] PostgreSQL and MinIO running via docker-compose
- [ ] LLM server online (llama.cpp) 
- [ ] VryndaraConnector tested with sample requests
- [ ] Async response handling implemented and tested
- [ ] Error logging configured
- [ ] Storage buckets created (aegis-audits)
- [ ] Database schema for audit findings verified
- [ ] Load testing (multiple concurrent audits)
- [ ] UI integration tested end-to-end

---

## Next Steps

1. **Copy `VryndaraConnector` code** into Aegis backend
2. **Implement audit workflows** using provided patterns
3. **Test end-to-end** with sample audit
4. **Monitor performance** (response times, error rates)
5. **Plan Phase 2 features** (custom analyzer agent, scheduling)

---

**Questions?** Refer to [VRYNDARA_INTEGRATION_GUIDE.md](./VRYNDARA_INTEGRATION_GUIDE.md) for detailed architecture documentation.
