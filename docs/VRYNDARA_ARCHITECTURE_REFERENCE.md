# Vryndara Architecture Diagrams & Decision Matrix

**Purpose:** Visual reference for Vryndara architecture and integration decision-making  
**Last Updated:** March 19, 2026

---

## System Architecture Diagrams

### Diagram 1: Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL APPLICATIONS                           │
├─────────────────────────────────────────────────────────────────────────┤
│  Aegis               │  Historabook           │  VrindaAI               │
│  (Audit Platform)    │  (Video Production)    │  (General AI)           │
│  ────────────────    │  ──────────────────    │ ─────────────           │
│  ├─ audit_service    │  ├─ research_req      │  ├─ creative_ai         │
│  ├─ finding_gen      │  ├─ screenplay_gen    │  ├─ 3d_design           │
│  └─ report_gen       │  └─ video_render      │  └─ code_gen            │
└────────┬─────────────┴────────┬──────────────┴────────────┬─────────────┘
         │                      │                           │
         │                      │  gRPC (Port 50051)       │
         │                      │                           │
         └──────────────────────┼───────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────┐
        │     VRYNDARA KERNEL (gRPC Server)                 │
        ├───────────────────────────────────────────────────┤
        │  Core Services:                                   │
        │  ├─ Message Router (Pub/Sub)                      │
        │  ├─ Agent Registry                                │
        │  ├─ BrainService (LLM Interface)                  │
        │  ├─ EngineeringService (3D Geometry)              │
        │  └─ DirectorSkill (Rendering Orchestration)       │
        │                                                   │
        │  Storage:                                         │
        │  ├─ Message Queues (per agent)                    │
        │  └─ Event Log Index                               │
        └────────┬──────────────────────────────────────────┘
                 │
        ┌────────┴───────────────────────────────┐
        │                                        │
        ▼                                        ▼
    ┌─────────────────┐             ┌──────────────────────┐
    │   AGENTS        │             │  SERVICES & DATA     │
    ├─────────────────┤             ├──────────────────────┤
    │ ┌─────────────┐ │             │ ┌──────────────────┐ │
    │ │ Coder Agent │ │             │ │ PostgreSQL       │ │
    │ │ (Code Gen)  │ │             │ │ (Event Log)      │ │
    │ └─────────────┘ │             │ └──────────────────┘ │
    │                 │             │                      │
    │ ┌─────────────┐ │             │ ┌──────────────────┐ │
    │ │ Researcher  │ │             │ │ ChromaDB         │ │
    │ │ (Web Search)│ │             │ │ (Vector Memory)  │ │
    │ └─────────────┘ │             │ └──────────────────┘ │
    │                 │             │                      │
    │ ┌─────────────┐ │             │ ┌──────────────────┐ │
    │ │ Media Dir   │ │             │ │ MinIO (S3)       │ │
    │ │ (Rendering) │ │             │ │ (Object Storage) │ │
    │ └─────────────┘ │             │ └──────────────────┘ │
    │                 │             │                      │
    │ ┌─────────────┐ │             │ ┌──────────────────┐ │
    │ │ VoiceEngine │ │             │ │ Llama.cpp Server │ │
    │ │ (Speech)    │ │             │ │ (LLM Inference)  │ │
    │ └─────────────┘ │             │ └──────────────────┘ │
    └─────────────────┘             │                      │
                                    │ ┌──────────────────┐ │
                                    │ │ Blender          │ │
                                    │ │ (3D Rendering)   │ │
                                    │ └──────────────────┘ │
                                    └──────────────────────┘
                                           ▲
                                           │
                                    HTTP   │
                                  REST     │
                                  Port 8081│
                                           │
        ┌──────────────────────────────────┴────────────────────┐
        │          FASTAPI GATEWAY                              │
        ├───────────────────────────────────────────────────────┤
        │  ├─ REST Endpoints (partial)                          │
        │  ├─ WebSocket Server (Real-time UI updates)           │
        │  ├─ gRPC Bridge (to kernel)                           │
        │  │                                                    │
        │  Ports:                                               │
        │  ├─ HTTP:       127.0.0.1:8081                        │
        │  └─ WebSocket:  127.0.0.1:8888                        │
        └─────────────────────────────────────────────────────┘
                           ▲
                           │
                  Browser UI / External App
                  (React Dashboard, Aegis)
```

### Diagram 2: Message Flow Architecture

```
SEQUENCE: External App → Agent → Processing → Response

Timeline:
─────────────────────────────────────────────────────────

T0  Aegis                  Kernel              Researcher Agent    Services
    │                      │                   │                   │
    │ Send Signal          │                   │                   │
    │ (TASK_REQUEST)       │                   │                   │
    ├─────────────────────>│                   │                   │
    │ id: msg-123          │                   │                   │
    │ type: TASK_REQUEST   │                   │                   │
    │ payload: "query:..." │                   │                   │
    │                      │                   │                   │
T1  │                      │ Log to DB         │                   │
    │                      ├──────────────────────────────────────>│
    │                      │                                        │ INSERT event_log
    │                      │                   │                   │
    │                      │ Enqueue to        │                   │
    │                      │ researcher queue  │                   │
    │                      ├──────────────────>│                   │
    │                      │                   │ Receive Signal   │
    │                      │                   │ Process          │
T2  │                      │                   ├─────────────────>│ Search Web
    │                      │                   │                  │ (DuckDuckGo)
    │  (waiting...)        │                   │                  │
    │                      │                   │  Get Results     │
T3  │                      │                   │<─────────────────┤
    │                      │                   │ Format Response  │
    │                      │                   │                  │
    │                      │ Send Response     │                  │
    │<─────────────────────┼───────────────────│                  │
    │ Signal               │                   │                  │
    │ type: TASK_RESULT    │                   │                  │
    │                      │                   │                  │
T4  │ Process Result       │ Log to DB         │                  │
    │ Update Audit         │<─────────────────────────────────────┤
    │                      │                                        │
```

### Diagram 3: Data Flow for Aegis Audit Workflow

```
User initiates "Create ISO27001 Audit"
│
├─ Aegis Backend
│  ├─ Create Audit Record
│  ├─ Call VryndaraConnector.research_compliance_framework()
│  │  └─ SIGNAL: {query: "Find ISO27001 requirements"}
│  │     → Kernel → Researcher Queue
│  │
│  ├─ WAIT for response (blocking with timeout)
│  │
│  ├─ RECEIVE: {findings: "ISO27001 Section A.5..."}
│  │  ├─ Parse findings
│  │  ├─ Store in Aegis database
│  │  └─ Trigger local scanning
│  │
│  ├─ Scan Current State (local)
│  │  ├─ Check configurations
│  │  ├─ Review access logs
│  │  └─ Collect evidence
│  │
│  ├─ Compare vs Framework
│  │  └─ Identify gaps: [control A.5.1 missing implementation, ...]
│  │
│  ├─ Generate Audit Code (optional)
│  │  └─ SIGNAL: {instruction: "Generate access review code"}
│  │     → Kernel → Coder Queue
│  │
│  ├─ RECEIVE: {code: "for user in users..."}
│  │  └─ Save in database for automation
│  │
│  ├─ Create Findings
│  │  └─ For each gap: Finding(control_id, description, severity)
│  │
│  ├─ Upload Report (if generated)
│  │  └─ Using StorageManager → MinIO
│  │     Returns: http://localhost:9000/aegis-audits/...
│  │
│  └─ Return Results
│     {
│       audit_id: "AUD-2024-001",
│       status: "COMPLETED",
│       findings_count: 12,
│       framework_url: "http://...",
│       report_url: "http://..."
│     }
│
└─ Aegis Frontend
   ├─ Display results
   ├─ Show findings
   ├─ Allow remediation planning
   └─ Track audit history
```

### Diagram 4: Deployment Architecture (Production)

```
┌───────────────────────────────────────────────────────────────┐
│                    LOAD BALANCER (nginx)                      │
│  ├─ :80    → Gateway:8081 (HTTP REST)                         │
│  ├─ :443   → Gateway:8888 (HTTPS WebSocket)                   │
│  └─ HTTP2 Push for real-time updates                          │
└────┬─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│         VRYNDARA SERVICE TIER (Kubernetes Pod)                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Container: vryndara-kernel                             │   │
│  │ ├─ Process: python kernel/main.py                      │   │
│  │ ├─ Port (internal):50051 (gRPC)                        │   │
│  │ ├─ CPU: 2 cores min                                    │   │
│  │ ├─ Memory: 4GB (for ChromaDB + queues)                 │   │
│  │ └─ Health Check: gRPC health probe                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Sidecar: gateway service                               │   │
│  │ ├─ Process: uvicorn gateway.main:socket_app             │   │
│  │ ├─ Port (internal): 8081, 8888                          │   │
│  │ └─ Proxies to kernel via localhost:50051               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Agent Containers (separate pods):                       │   │
│  │ ├─ researcher-agent-pod                                │   │
│  │ ├─ coder-agent-pod                                     │   │
│  │ ├─ media-director-pod                                  │   │
│  │ └─ voice-service-pod (future)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
     │       │       │       │
     ▼       ▼       ▼       ▼
┌─────────────────────────────────────────────────────────────────┐
│               DATA & SERVICE TIER (Managed Services)            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │  PostgreSQL 15  │  │  ChromaDB       │  │  MinIO/S3     │  │
│  │  (RDS/Cloud)    │  │  (Container)    │  │  (Cloud Stor) │  │
│  │  ┌──────────────┤  │  ┌─────────────┤  │  ┌───────────┤  │
│  │  │ event_log    │  │  │ vryndara_   │  │  │ Buckets:  │  │
│  │  │ audit_trail  │  │  │ core_memory │  │  │ ├─ aegis- │  │
│  │  │ workflow_log │  │  │ (vector db) │  │  │ │  audits  │  │
│  │  └──────────────┤  │  └─────────────┤  │  │ ├─ history│  │
│  └─────────────────┘  └─────────────────┘  │  │-  book    │  │
│                                             │  └───────────┤  │
│                                             └───────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LLM Inference Service                                   │   │
│  │ ├─ Llama.cpp Server (or Ollama)                         │   │
│  │ ├─ Model: mistral.gguf or equivalent                    │   │
│  │ ├─ Port: 8080                                           │   │
│  │ └─ Auto-scaling by queue depth                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Rendering Service (for Media Agent)                     │   │
│  │ ├─ Blender (batch mode)                                 │   │
│  │ ├─ Render jobs queue                                    │   │
│  │ └─ Output → MinIO                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Diagram 5: Integration Points - Aegis ↔ Vryndara

```
Aegis Module               Integration Pattern        Vryndara Component
─────────────────────────────────────────────────────────────────────────

audit_service.py    
├─ create_audit()   ──gRPC Signal──>  research_compliance_framework()
│  └─ VryndaraConnector.send()                     │
│                                                   ├─ Kernel.Publish()
│                                                   └─ researcher-1.on_message()

finding_generator.py
├─ generate_code()  ──gRPC Signal──>  generate_audit_code()
│  └─ VryndaraConnector.send()                     │
│                                                   ├─ Kernel.Publish()
│                                                   └─ coder-alpha.on_message()

audit_analyzer.py
├─ analyze_gaps()   ──(Future)──>  analyzer-agent
│                                  (To be implemented)

report_generator.py
├─ export_report()  ──HTTP PUT──>   gateway.main:upload_endpoint()
│  └─ StorageManager()               (Via MinIO backend)

memory_cache.py
├─ store_context()  ──Direct──>  Kernel.BrainService
│  │                             └─ ChromaDB.add()
│  └─ retrieve_context()            └─ ChromaDB.query()

audit_model.py
├─ save()           ──SQL──────>  PostgreSQL
│  └─ event logging               (Via Vryndara event_log table)
```

---

## Decision Matrix: Integration Approach

### When to Use Which Integration Method

| Scenario | Method | Client Type | Pros | Cons | Example |
|----------|--------|-------------|------|------|---------|
| **Within same Python process** (local dev) | Direct SDK | `AgentClient` | Simple, low latency | Must run kernel locally | Testing audit_service |
| **Separate Python service** | SDK + Threading | `AgentClient` w/ threads | Clean separation | More complex async | Aegis backend service |
| **Web application** (Aegis frontend) | REST API | HTTP Client | No gRPC needed, familiar | Endpoints under dev | Browser audit dashboard |
| **Long-running async task** | Task Queue | Celery/RQ | Non-blocking, scalable | Additional infra | Scheduled audits |
| **Real-time UI updates** | WebSocket | Browser JS | Instant feedback | Requires browser | Live audit progress |
| **Microservice** (future) | HTTP REST | REST Client | Language agnostic | Latency from network | External audit tool |

### Choosing Your Integration Path

**Question 1: Where is Aegis code running?**
- Same server as Vryndara? → Use **SDK + Threading**
- Different server? → Use **REST API** (when ready) or **SDK over network**
- Browser? → Use **WebSocket** or **REST**

**Question 2: Is the request blocking (user waits) or async (background)?**
- User waiting (interactive) → **SDK + Timeout** (30 sec max)
- Background processing → **Queue-based** (Celery/RQ)
- Both → **SDK for quick queries**, **Queue for long tasks**

**Question 3: Do you need real-time updates during processing?**
- Yes → **WebSocket** or **Server-Sent Events (SSE)**
- No → **SDK** (request/response only)

**Question 4: Multiple instances of Aegis (scaling)?**
- Single instance → **SDK** is fine
- Multiple instances → **REST API** + **Load balancer**

---

## Quick Decision Tree

```
Start: "I want to integrate Aegis with Vryndara"
│
├─ Is this for Aegis Backend (Python)?
│  ├─ YES
│  │  ├─ Need real-time status updates?
│  │  │  ├─ YES → Use WebSocket (via gateway) + SDK for requests
│  │  │  └─ NO → Use SDK client directly with threading
│  │  │
│  │  λ Go to: Implementation Pattern 1 (Threaded SDK Client)
│  │
│  └─ NO
│     └─ Is this for Aegis Frontend (React/Browser)?
│        ├─ YES → Use REST API (when available) or WebSocket
│        │
│        λ Go to: REST/WebSocket Integration Guide
│        │
│        └─ NO → Other language/system?
│           └─ Use REST API (when available) or gRPC (if supporting)

         λ Go to: Multi-language Integration Guide
```

---

## Performance Characteristics

### Response Time Expectations

```
Operation                          Min      Typical    Max        Notes
──────────────────────────────────────────────────────────────────────

gRPC Message Routing               <1ms     1-2ms      5ms        Local network
Web Search (Researcher)            2s       5-8s       20s        DuckDuckGo API
Code Generation (Coder)            1s       3-5s       15s        LLM inference on CPU
LLM Inference (no code)            0.5s     2-3s       10s        Depending on prompt
3D Rendering (Blender)             5s       20-60s     5m+        Depends on complexity
Database Write (PostgreSQL)        1ms      2-5ms      20ms       Per event
Vector Search (ChromaDB)           5ms      10-20ms    100ms      Semantic similarity

Full Audit Workflow:
- Research framework              5s
- Local scanning                  2s
- Gap analysis                    3s
- Code generation                 5s
─────────────────────────────────────────
- Total (sequential)              15s
- Total (cached framework)        10s
```

### Throughput

```
Concurrent Requests              Recommended    Max Safe    Notes
─────────────────────────────────────────────────────────────────

Agents responding to requests    1-3            5          CPU-bound (LLM)
Parallel framework research      3              10         I/O-bound (web)
Event log writes/sec             100            500        PostgreSQL
Vector search/sec                20             100        ChromaDB
Storage uploads/sec              5              20         MinIO

Vryndara Kernel Capacity:
- Single kernel instance: ~10 concurrent workflows
- With clustering: Scales linearly
```

---

## Failure Scenarios & Resilience

### Common Failure Modes

```
Failure Mode              Impact              Recovery Strategy
─────────────────────────────────────────────────────────────────────

Kernel Crash            Cannot process         Restart kernel
                        any requests            Auto-restart via supervisor

Researcher Timeout      Audit blocked           Retry with longer timeout
                        20s+                    Use cached results

Coder LLM Slow          Code generation        Use fallback templates
                        delayed                 Reduce complexity

PostgreSQL Down         Event log loss          Reconnect when available
                        (in-memory recovery)    Replay from Kafka (future)

MinIO Unavailable       Can't store files       Local temp storage
                        Reports not uploaded    Retry when available

Aegis Network Issue     Cannot reach Kernel    Local database fallback
                                              Retry with backoff

Researcher (Website)    Cannot fetch findings  Use cached knowledge
  Blocked/Down          Blank research         Manual input prompt

LLM Model Missing       Code generation fails  Pre-download models
                                              Use alternative models
```

### Monitoring Recommendations

```
Metric                      Alert Threshold    Action
────────────────────────────────────────────────────────────────

Kernel Response Time        > 5s              Check CPU/memory
Researcher Timeout Rate     > 10%             Investigate web connectivity
Database Query Time         > 100ms           Check PostgreSQL logs
Memory Usage (Kernel)       > 80%             Restart kernel
Message Queue Depth         > 50 messages     Investigate slow agent
Error Rate                  > 5%              Check logs, restart affected service
Disk Space                  < 10%             Archive old job artifacts
```

---

## Implementation Roadmap

### Phase 1: Basic Integration (NOW)
- [x] VryndaraConnector SDK client
- [x] Threading for async handling
- [x] Research capability integration
- [ ] Error handling & retries
- [ ] Local caching

### Phase 2: Enhanced Features (Next 4 weeks)
- [ ] REST API finalization
- [ ] WebSocket real-time updates
- [ ] Custom analyzer agent
- [ ] Scheduled audits (Scheduler agent)
- [ ] Advanced memory management

### Phase 3: Enterprise (Next quarter)
- [ ] Multi-tenancy
- [ ] Authentication/authorization
- [ ] Distributed kernel (HA)
- [ ] Advanced observability
- [ ] Custom agent framework (for audit-specific logic)

---

## Compatibility & Version Matrix

```
Component              Version      Python Version      Notes
──────────────────────────────────────────────────────────────────

Vryndara Core          0.1.0        3.10+              Alpha release
Kernel gRPC            50051        N/A                Stable
SDK Python             0.1.0        3.10+              Compatible
PostgreSQL             15+          N/A                Tested on 15
ChromaDB               0.3.21+      3.10+              Pinned version
MinIO                  Latest       N/A                Via docker-compose
FastAPI                0.104.1      3.10+              For gateway
Mistral GGUF           7B           N/A                Optional alternative

Aegis Compatibility:
- Django 4.2+          Yes
- FastAPI             Yes
- Flask               Yes (requires REST API)
- Async (asyncio)     Yes (with custom wrapper)
```

---

**End of Architecture Reference**  
For implementation details, see `VRYNDARA_QUICK_START.md`
