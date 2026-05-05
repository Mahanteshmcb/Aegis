# Vryndara Multi-Agent AI Orchestration Platform - Integration Guide for Aegis

**Date:** March 19, 2026  
**Version:** 1.0  
**Audience:** Aegis Development Team  
**Purpose:** Comprehensive technical reference for integrating Aegis with the Vryndara platform

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Overall Architecture](#overall-architecture)
3. [Core Components & Modules](#core-components--modules)
4. [Multi-Agent Framework](#multi-agent-framework)
5. [Available Agent Types](#available-agent-types)
6. [Integration/API Reference](#integrationapi-reference)
7. [Project & Application Management](#project--application-management)
8. [Configuration Reference](#configuration-reference)
9. [Current Status & Limitations](#current-status--limitations)
10. [Key Integration Points for Aegis](#key-integration-points-for-aegis)
11. [Data Flow Architecture](#data-flow-architecture)
12. [Deployment & Infrastructure](#deployment--infrastructure)

---

## Executive Summary

**Vryndara** is a sophisticated multi-agent AI orchestration platform that serves as a bridge between discrete AI services (code generation, research, media production, 3D rendering) and external applications. 

### Key Characteristics:

- **gRPC-based distributed architecture** for real-time agent communication
- **Three-tier service model:** Kernel (orchestrator) → Agents (specialized workers) → Gateway (external interface)
- **Memory management** via ChromaDB for semantic recall and context persistence
- **Multi-sensory I/O:** Voice (Whisper speech recognition, Piper TTS), Vision (MediaPipe hand gestures), Text
- **3D Content Generation:** SDF-based computational geometry → Blender rendering
- **Workflow execution** with sequential agent chaining
- **Event logging** via PostgreSQL for audit trails and state recovery
- **Distributed storage** via MinIO S3-compatible object storage

### Core Purpose:

Vryndara acts as a **central hub** that receives requests from external applications (like Aegis), routes them through specialized agents, orchestrates complex multi-step workflows, and returns results through standardized APIs.

---

## Overall Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL APPLICATIONS                        │
│  (Aegis, Historabook, VrindaAI, etc.)                          │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP/REST (FastAPI Gateway)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GATEWAY LAYER (FastAPI)                      │
│  - WebSocket connections to UI/Browser clients                  │
│  - REST endpoints for app integration                           │
│  - Bridge to gRPC Kernel                                        │
│  Port: 8081 (HTTP) / 8888 (WebSocket)                          │
└────────────┬──────────────────────────────────────────────────┘
             │ gRPC (Port 50051)
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KERNEL (gRPC Server)                         │
│  - Agent registry & message routing                             │
│  - Workflow orchestration                                       │
│  - Memory management (ChromaDB)                                 │
│  - Event persistence (PostgreSQL)                               │
│  - Service initialization (Brain, Engineer, Coder)              │
│  Port: 50051 (gRPC)                                             │
└────┬──────────────┬─────────────────┬──────────────────────────┘
     │              │                 │
     ▼              ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Coder      │ │ Researcher   │ │  Media       │
│   Agent      │ │   Agent      │ │  Director    │
│ (Code Gen)   │ │ (Web Search) │ │  (Rendering) │
└──────────────┘ └──────────────┘ └──────────────┘
     │              │                 │
     └──────────────┴─────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUPPORT SERVICES                             │
│  - ChromaDB (Vector Memory)       Port: Local                   │
│  - PostgreSQL (Event Log)         Port: 5433                    │
│  - MinIO (Object Storage)         Port: 9000 (API), 9001 (Web)  │
│  - Llama.cpp (LLM Inference)      Port: 8080                    │
│  - Blender (3D Rendering)         Desktop App                   │
└─────────────────────────────────────────────────────────────────┘
```

### Architectural Layers

1. **Presentation Layer (UI/External Apps)**
   - Browser-based React dashboard
   - External applications (Aegis, Historabook)
   - Command-line interfaces

2. **API Gateway Layer (FastAPI)**
   - HTTP REST endpoints for external integration
   - WebSocket connections for real-time UI updates
   - Bridges external apps to internal gRPC kernel

3. **Orchestration Layer (gRPC Kernel)**
   - Central message broker for all agents
   - Agent registration and discovery
   - Workflow execution engine
   - Memory and context management
   - Event logging and audit trails

4. **Agent Layer**
   - Specialized workers performing discrete tasks
   - Communication via gRPC messages (Signal protocol)
   - Can be distributed across network

5. **Service Layer**
   - Core AI services (BrainService, EngineeringService, etc.)
   - External tools integration (Blender, LLMs, web search)
   - Data persistence (databases, object storage)

---

## Core Components & Modules

### Directory Structure

```
Vryndara/
├── Vryndara_Core/           # Core kernel and services
│   ├── main.py              # Entry point (JARVIS voice interface)
│   └── services/
│       ├── brain_service.py         # LLM interface + ChromaDB memory
│       ├── engineering_service.py   # SDF geometry compilation
│       ├── director_skill.py        # 3D rendering orchestration
│       ├── vision_service.py        # MediaPipe hand gesture detection
│       └── voice_engine.py          # Whisper speech recognition + Piper TTS
│
├── kernel/                  # gRPC kernel & database
│   ├── main.py              # Kernel server (gRPC)
│   ├── database.py          # PostgreSQL async setup
│   └── memory/              # ChromaDB storage
│
├── gateway/                 # FastAPI REST gateway
│   ├── main.py              # WebSocket + REST endpoints
│   └── bridge/              # UI connectivity layer
│
├── agents/                  # Specialized agent implementations
│   ├── coder/               # Code generation agent
│   │   ├── code_generator.py    # LLM-based code generation
│   │   └── main.py              # Agent registration & listening
│   ├── researcher/          # Web research agent
│   │   └── main.py              # DuckDuckGo integration, web scraping
│   └── media/               # Media generation agent
│       └── main.py              # Screenplay generation, rendering
│
├── sdk/                     # Client SDKs for external integration
│   ├── python/
│   │   ├── vryndara/
│   │   │   ├── client.py        # AgentClient for gRPC communication
│   │   │   ├── storage.py       # StorageManager for S3/MinIO
│   │   │   └── __init__.py
│   │   └── examples/            # Integration examples
│   └── wasm/                # Future WebAssembly SDK
│
├── protos/                  # Protocol Buffer definitions
│   ├── vryndara.proto           # Service & message definitions
│   ├── vryndara_pb2.py          # Generated Python message classes
│   └── vryndara_pb2_grpc.py     # Generated gRPC stubs
│
├── Director_Jobs/           # Job output artifacts
│   ├── JOB_*.json              # Manifest files
│   ├── JOB_*_script.py         # Generated Blender/render scripts
│   └── JOB_*_render.{png,mp4}  # Output media
│
├── models/                  # ML model storage
│   ├── faster-whisper-small/
│   ├── piper-voice-ryan/
│   └── mistral.gguf         # (Symlinked to VrindaAI)
│
├── piper/                   # Text-to-speech binary & models
│   ├── piper.exe
│   ├── libtashkeel_model.ort
│   └── espeak-ng-data/
│
├── docker-compose.yml       # Infrastructure setup
├── Requirements.txt         # Python dependencies
├── setup.py                 # Package configuration
└── .env                     # Environment variables
```

### Key Files & Their Responsibilities

| File | Purpose | Key Functions |
|------|---------|---------------|
| `kernel/main.py` | gRPC kernel server | `Register()`, `Publish()`, `Subscribe()`, `ExecuteWorkflow()` |
| `gateway/main.py` | REST/WebSocket API | FastAPI endpoints, WebSocket bridge to kernel |
| `sdk/python/vryndara/client.py` | External app client | `AgentClient.register()`, `.send()`, `.listen()` |
| `Vryndara_Core/services/brain_service.py` | LLM interface | `think()`, `store_memory()`, `retrieve_context()` |
| `agents/coder/code_generator.py` | Code generation | `generate_sdf_code()`, `_llm_inference()` |
| `agents/researcher/main.py` | Web research | `search_web()`, message callback |
| `Vryndara_Core/services/director_skill.py` | 3D rendering pipeline | `create_manifest()`, `launch_blender_directly()` |
| `protos/vryndara.proto` | Contract definitions | Service RPC methods, message schemas |

---

## Multi-Agent Framework

### Agent Lifecycle & Communication Model

#### 1. **Agent Registration**

When an agent starts, it registers with the kernel:

```python
# Agent-side code
from sdk.python.vryndara.client import AgentClient

client = AgentClient(
    agent_id="coder-alpha",
    kernel_address="localhost:50051"  # Kernel gRPC server
)

client.register(capabilities=["python.generation", "ai.local"])
```

**Kernel-side handling:**
```python
# kernel/main.py - VryndaraKernel class
async def Register(self, request, context):
    logging.info(f"Registering Agent: {request.id}")
    self.registry[request.id] = request  # Add to agent registry
    self.message_queues[request.id] = asyncio.Queue()  # Create message queue
    return vryndara_pb2.Ack(success=True)
```

#### 2. **Message Protocol (Signal)**

All agent communication uses the **Signal** protobuf message:

```protobuf
message Signal {
    string id = 1;                  // Unique message ID (UUID)
    string source_agent_id = 2;     // Sender agent ID
    string target_agent_id = 3;     // Recipient agent ID
    string type = 4;                // Message type (TASK_REQUEST, TASK_RESULT, etc.)
    string payload = 5;             // JSON-encoded data
    int64 timestamp = 6;            // Unix timestamp
}
```

**Example Message Flow:**

```
1. External App (Aegis) → Kernel
   Signal {
       id: "abc-123",
       source_agent_id: "aegis-audit",
       target_agent_id: "researcher-1",
       type: "TASK_REQUEST",
       payload: "{\"query\": \"Find audit frameworks\"}",
       timestamp: 1710868800
   }

2. Kernel → Researcher Agent
   (Same signal routed to researcher's message queue)

3. Researcher Agent processes & responds
   Signal {
       id: "def-456",
       source_agent_id: "researcher-1",
       target_agent_id: "aegis-audit",
       type: "TASK_RESULT",
       payload: "{\"results\": \"...research data...\"}",
       timestamp: 1710868850
   }
```

#### 3. **Agent Message Loop**

Standard agent pattern:

```python
def on_message(signal):
    """Callback when message arrives for this agent"""
    print(f">>> [RECEIVED] {signal.type} from {signal.source_agent_id}")
    
    if signal.type == "TASK_REQUEST":
        # 1. Extract payload
        task_data = signal.payload
        
        # 2. Do work
        result = do_work(task_data)
        
        # 3. Send response back to requester
        client.send(
            target_id=signal.source_agent_id,
            msg_type="TASK_RESULT",
            payload=result
        )

if __name__ == "__main__":
    client = AgentClient("my-agent", kernel_address="localhost:50051")
    client.register(["my.capability"])
    client.listen(on_message)  # Block and listen for incoming signals
```

#### 4. **Broadcast & Publishing**

The kernel broadcasts signals to all subscribed agents:

```python
# kernel/main.py - Publish method
async def Publish(self, request, context):
    target = request.target_agent_id
    
    # 1. BROADCAST: Send to all subscribers except sender
    for agent_id, queue in self.message_queues.items():
        if agent_id != request.source_agent_id:
            await queue.put(request)  # Enqueue for agent to receive
    
    # 2. PERSISTENCE: Log to database
    event = EventLog(
        id=request.id,
        source=request.source_agent_id,
        target=request.target_agent_id,
        type=request.type,
        payload=request.payload,
        timestamp=request.timestamp
    )
    session.add(event)
    await session.commit()
    
    # 3. INTERCEPT: Special handling for specific agents
    if target == "ComputationalEngineer":
        generated_code = await self.coder.generate_sdf_code(request.payload)
        result = await self.engineer.generate_sdf_from_code(generated_code)
        return vryndara_pb2.Ack(success=True, error=json.dumps(result))
```

#### 5. **Workflow Execution**

Multi-step workflows chain agents:

```python
# Execute a workflow with multiple steps
workflow = WorkflowRequest(
    workflow_id="audit-flow-001",
    steps=[
        WorkflowStep(agent_id="researcher-1", task_payload="Find frameworks", step_order=1),
        WorkflowStep(agent_id="analyzer-1", task_payload="Analyze results", step_order=2),
        WorkflowStep(agent_id="reporter-1", task_payload="Generate report", step_order=3),
    ]
)

kernel_stub.ExecuteWorkflow(workflow)
```

---

## Available Agent Types

### 1. **Coder Agent** (`agents/coder/`)

**Purpose:** Generate Python code, especially SDF (Signed Distance Field) computational geometry scripts

**Capabilities:**
- Code generation using local LLM (Mistral via llama.cpp)
- SDF geometry code synthesis
- API documentation parsing
- Code validation

**Entry Point:** `agents/coder/main.py`

**Message Protocol:**
```
Incoming: TASK_REQUEST with {prompt: "Create a cylinder with radius 10"}
Outgoing: TASK_RESULT with {code: "f = cylinder(10)"}
```

**Example:**
```python
client.send(
    target_id="coder-alpha",
    msg_type="TASK_REQUEST",
    payload="Create a coffee mug with a handle"
)
```

**Configuration:**
- Model: `mistral.gguf` (llama-cpp-python compatible)
- LLM Params: `n_ctx=4096`, `n_gpu_layers=0` (CPU), `temperature=0.4`
- Ollama Alternative: Can use `ollama.chat()` with `llama3.1:8b`

### 2. **Researcher Agent** (`agents/researcher/`)

**Purpose:** Perform web research and information retrieval

**Capabilities:**
- Web scraping via DuckDuckGo API
- Fact extraction
- Knowledge synthesis
- Topic summarization

**Entry Point:** `agents/researcher/main.py`

**Message Protocol:**
```
Incoming: TASK_REQUEST with {topic: "Great Wall of China"}
Outgoing: TASK_RESULT with {findings: "...research summary..."}
```

**Example:**
```python
client.send(
    target_id="researcher-1",
    msg_type="TASK_REQUEST",
    payload="Find interesting facts about blockchain consensus mechanisms"
)
```

**Configuration:**
- Search Engine: DuckDuckGo (free, no API key required)
- Results per Query: 3 (configurable)
- Gateway URL: `http://localhost:8081/api/v1/progress` (optional UI updates)

### 3. **Media Director Agent** (`agents/media/`)

**Purpose:** Generate screenplays and orchestrate media rendering

**Capabilities:**
- Screenplay generation from research data
- Scene-by-scene narrative creation
- Video production orchestration
- Asset management

**Entry Point:** `agents/media/main.py`

**Message Protocol:**
```
Incoming: TASK_REQUEST with {research_data: "..."}
Outgoing: TASK_RESULT with {video_url: "http://..."}
```

**Configuration:**
- LLM: Ollama (`llama3.1:8b`)
- Storage Bucket: `historabook-output`
- Render Engine: Blender 4.3

### 4. **Brain Service** (Built-in Kernel Service)

**Purpose:** Central LLM interface and memory management

**Capabilities:**
- Query the local LLM (llama.cpp server on port 8080)
- Store & retrieve conversation context via ChromaDB
- Semantic search using vector embeddings
- System personality/persona definition

**Key Methods:**
```python
# Think/inference
response = brain.think("What is machine learning?", system_prompt=None)

# Store episodic memory
brain.store_memory(
    text="User asked about ML, received explanation about algorithms",
    metadata={"type": "chat_history", "timestamp": "..."}
)

# Retrieve context
past_context = brain.retrieve_context("machine learning")  # Returns up to 3 similar memories
```

**Configuration:**
- LLM API: `http://127.0.0.1:8080/completion`
- Memory: ChromaDB PersistentClient at `./kernel/memory/chroma_db`
- Vector Space: Cosine similarity (HNSW)

### 5. **Engineering Service** (Built-in Kernel Service)

**Purpose:** Compile and validate computational geometry code

**Capabilities:**
- SDF code compilation and validation
- 3D geometry generation (STL export)
- Blender script generation
- Error handling for hallucinated code

**Key Methods:**
```python
# Generate 3D model from Python code
result = engineer.generate_sdf_from_code(python_code_str)
# Returns: {success: bool, output_file: str, error: str}
```

### 6. **Director Skill** (Built-in Kernel Service)

**Purpose:** Orchestrate 3D rendering pipeline

**Capabilities:**
- Intent extraction from natural language
- Manifest generation (job definition)
- Blender automation
- Image rendering and export

**Key Methods:**
```python
response = director.create_manifest(user_request)
# Returns: Rendered image path or error message
```

### 7. **Voice Engine** (Built-in Kernel Service)

**Purpose:** Speech recognition and synthesis

**Capabilities:**
- Audio input via microphone (Whisper)
- Voice activity detection (VAD)
- Text-to-speech output (Piper)
- Silence trimming

**Methods:**
```python
# Speech recognition
text = voice.listen(duration=5)  # Listen for up to 5 seconds

# Text-to-speech
voice.speak("Hello, this is Vryndara speaking")
```

### 8. **Vision Service** (Built-in Kernel Service)

**Purpose:** Gesture recognition and spatial awareness

**Capabilities:**
- Hand gesture detection (MediaPipe)
- Pinch detection
- Real-time video processing
- UDP broadcast to kernel

**Configuration:**
- Detection confidence: 0.7 minimum
- Max hands tracked: 2
- UDP Target: `127.0.0.1:50052`

---

## Integration/API Reference

### Method 1: Direct gRPC Communication (Agents)

**Use Case:** Creating new agents or low-level control

**Steps:**

1. **Initialize client:**
```python
from sdk.python.vryndara.client import AgentClient

client = AgentClient(
    agent_id="my-custom-agent",
    kernel_address="localhost:50051"
)
```

2. **Register with capabilities:**
```python
client.register(capabilities=[
    "custom.capability1",
    "custom.capability2"
])
```

3. **Send messages:**
```python
client.send(
    target_id="coder-alpha",
    msg_type="TASK_REQUEST",
    payload=json.dumps({"instruction": "Create a sphere"})
)
```

4. **Listen for responses:**
```python
def handle_message(signal):
    if signal.type == "TASK_RESULT":
        print(f"Result: {signal.payload}")
    if signal.type == "ERROR":
        print(f"Error: {signal.payload}")

client.listen(handle_message)
```

### Method 2: HTTP REST via FastAPI Gateway

**Use Case:** External applications (like Aegis) integrating without gRPC

**Endpoints:** (To be implemented - currently under development)

```
POST /api/v1/task          - Submit task to agent
GET  /api/v1/status/{id}   - Check task status
GET  /api/v1/results/{id}  - Retrieve results
WS   /ws                   - WebSocket for real-time updates
```

**Example (Future):**
```bash
# Submit research task
curl -X POST http://localhost:8081/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "researcher-1",
    "task_type": "web_search",
    "payload": {"topic": "Vryndara architecture"}
  }'

# Get status
curl http://localhost:8081/api/v1/status/task-123

# Get results
curl http://localhost:8081/api/v1/results/task-123
```

### Method 3: WebSocket Connection (Real-time Updates)

**Use Case:** Browser-based UIs needing real-time status updates

**URL:** `ws://localhost:8888/ws`

**Protocol:**
```javascript
// Client-side JavaScript
const socket = new WebSocket('ws://localhost:8888/ws');

socket.addEventListener('message', (event) => {
    const payload = JSON.parse(event.data);
    console.log(`Agent ${payload.type}: ${payload.data}`);
    // Update UI in real-time
});
```

**Message Format:**
```json
{
    "type": "TASK_REQUEST",
    "data": {...},
    "timestamp": 1710868800,
    "status": "THINKING"
}
```

### Method 4: Internal Kernel Direct Access

**Use Case:** Kernel-level operations (within Vryndara itself)

```python
# In kernel/main.py or related services
from kernel.database import AsyncSessionLocal, EventLog
from Vryndara_Core.services.brain_service import BrainService

brain = BrainService()
result = brain.think("Ask the brain something")
```

### Storage Integration

**Using StorageManager for file uploads:**

```python
from sdk.python.vryndara.storage import StorageManager

storage = StorageManager(bucket_name="my-assets")

# Upload file
url = storage.upload_file("local_file.mp4", object_name="video.mp4")
# Returns: "http://localhost:9000/my-assets/video.mp4"

# Download file
storage.download_file("remote_file.mp4", "local_path.mp4")
```

**Storage Buckets (configured in docker-compose.yml):**
- `vryndara-assets` - General assets
- `historabook-output` - Video/media output
- Custom buckets can be created as needed

**MinIO Web Console:** http://localhost:9001
- Username: `admin`
- Password: `password123`

---

## Project & Application Management

### Central Platform Concept

Vryndara manages multiple external applications through standardized interfaces:

```
Vryndara Kernel
├── Aegis (Audit & Risk Management)
│   ├── Research requirements
│   ├── Generate audit frameworks
│   ├── Analyze policies
│   └── Generate reports
│
├── Historabook (Video Production)
│   ├── Research topics
│   ├── Generate screenplays
│   └── Produce videos
│
└── VrindaAI (General Purpose)
    ├── Creative workflows
    ├── 3D design
    └── Code generation
```

### App Registration Pattern

**Where:** External app's initialization code

**What:** Each app registers as an "agent" in Vryndara:

```python
# In Aegis bootstrap code
sys.path.append("path/to/vryndara/sdk/python")
from vryndara.client import AgentClient

class AegisConnector:
    def __init__(self):
        self.client = AgentClient(
            agent_id="aegis-audit-system",
            kernel_address="localhost:50051"
        )
        
        # Register what Aegis can request
        self.client.register([
            "audit.research",
            "audit.analysis",
            "audit.reporting"
        ])
    
    def get_audit_framework(self, standard_name):
        """Request Vryndara to find audit frameworks"""
        self.client.send(
            target_id="researcher-1",
            msg_type="TASK_REQUEST",
            payload=json.dumps({
                "query": f"Find audit frameworks for {standard_name}",
                "source_app": "aegis"
            })
        )
```

### Multi-Project Context

**Usage Pattern:**

Each request should include context:

```python
payload = {
    "query": "...",
    "context": {
        "source_app": "aegis",
        "project_id": "AUDIT-2024-001",
        "session_id": "sess-abc123",
        "user_id": "analyst-john"
    }
}

client.send(target_id="...", msg_type="TASK_REQUEST", payload=json.dumps(payload))
```

**Benefits:**
- Kernel can track requests by originating app
- Memory can be compartmentalized per project
- Audit logs show which app made which request
- Results can be routed back to correct app

### Workflow Templates

Pre-defined multi-step workflows can be created:

```python
# Define a workflow in your app
workflow = {
    "name": "Regulatory Compliance Check",
    "steps": [
        {
            "agent_id": "researcher-1",
            "task": "research_compliance_laws",
            "payload": {"region": "EU", "standard": "GDPR"}
        },
        {
            "agent_id": "analyzer-1",  # (Future agent)
            "task": "analyze_compliance",
            "payload": {"previous_result": "${step_1.result}"}
        },
        {
            "agent_id": "reporter-1",  # (Future agent)
            "task": "generate_report",
            "payload": {"analysis": "${step_2.result}"}
        }
    ]
}

# Execute via kernel
kernel_stub.ExecuteWorkflow(WorkflowRequest(
    workflow_id="compliance-check-001",
    steps=[...convert to WorkflowStep messages...]
))
```

---

## Configuration Reference

### Environment Variables (`.env`)

```bash
PYTHONPATH=sdk/python
```

### Kernel Configuration

**Database Connection** (`kernel/database.py`):
```python
DATABASE_URL = "postgresql+asyncpg://vryndara:devpassword@localhost:5433/vryndara_core"
```

**gRPC Server** (`kernel/main.py`):
```python
server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
vryndara_pb2_grpc.add_KernelServicer_to_server(VryndaraKernel(), server)
await server.start()
// Listens on [::]:50051
```

### Gateway Configuration

**FastAPI** (`gateway/main.py`):
```python
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow local Aegis
    allow_methods=["*"],
    allow_headers=["*"],
)
# Runs on http://127.0.0.1:8081
```

**WebSocket Bridge** (`bridge/main.py`):
```python
# Provides WebSocket server at http://127.0.0.1:8888/ws
# Streams signals from kernel to connected browsers in real-time
```

### Agent Configuration

**Coder Agent:**
```python
MODEL_PATH = r"C:\...\mistral.gguf"  # Or symlink to VrindaAI
GATEWAY_URL = "http://localhost:8081/api/v1/progress"
```

**Researcher Agent:**
```python
AGENT_ID = "researcher-1"
GATEWAY_URL = "http://localhost:8081/api/v1/progress"
```

### LLM Configuration

**Llama.cpp Server:**
```bash
# Run this separately to provide local LLM inference
cd C:\...\llama.cpp\build\bin\Release
.\llama-server.exe -m mistral.gguf --port 8080 -c 4096
```

**Ollama** (Alternative):
```bash
# ollama pull llama3.1:8b
# ollama serve  # Listens on http://localhost:11434
```

### Storage Configuration

**MinIO** (via docker-compose.yml):
```yaml
environment:
  MINIO_ROOT_USER: admin
  MINIO_ROOT_PASSWORD: password123
ports:
  - "9000:9000"  # S3 API
  - "9001:9001"  # Web UI
```

### Database Configuration

**PostgreSQL** (via docker-compose.yml):
```yaml
environment:
  POSTGRES_USER: vryndara
  POSTGRES_PASSWORD: devpassword
  POSTGRES_DB: vryndara_core
ports:
  - "5433:5432"
```

---

## Current Status & Limitations

### Fully Implemented ✅

1. **Core gRPC Kernel**
   - Agent registration and discovery
   - Message routing and broadcasting
   - Event persistence to PostgreSQL
   - Memory management via ChromaDB

2. **Available Agents**
   - Coder Agent (Python code generation via LLM)
   - Researcher Agent (Web search via DuckDuckGo)
   - Media Director (Screenplay generation, Blender rendering)

3. **Core Services**
   - BrainService (LLM interface + semantic memory)
   - EngineeringService (SDF geometry compilation)
   - DirectorSkill (3D rendering orchestration)
   - VoiceEngine (Speech recognition + TTS)
   - VisionService (Gesture detection)

4. **Storage & Infrastructure**
   - PostgreSQL event logging
   - ChromaDB semantic memory
   - MinIO object storage
   - Docker Compose deployment

### Partially Implemented ⚠️

1. **FastAPI Gateway**
   - REST endpoints for external app integration (framework ready, full API endpoints need development)
   - WebSocket bridge to kernel (working for browser UI, needs testing for Aegis)
   - Progress tracking endpoints (minimal implementation)

2. **Workflow Execution**
   - Proto definitions exist
   - Kernel method semi-implemented (needs comprehensive testing)
   - Error handling for failed workflow steps (incomplete)

3. **Hardware Node Management**
   - Proto definitions prepared (NodeHeartbeat, distributed nodes)
   - Not yet implemented in kernel
   - Future: Support multiple Vryndara instances, load balancing

### Not Yet Implemented ❌

1. **Advanced Agent Types**
   - Analyzer Agent (data analysis, decision making)
   - Reporter Agent (report generation, formatting)
   - Executor Agent (system command execution, installations)
   - Scheduler Agent (periodic task execution)

2. **Enterprise Features**
   - Authentication & Authorization (no user/role management)
   - API rate limiting
   - Request quotas per app
   - Multi-tenancy support
   - Data encryption at rest

3. **Observability**
   - Distributed tracing (OpenTelemetry)
   - Metrics collection (Prometheus)
   - Centralized logging (ELK stack)
   - Performance profiling

4. **High Availability**
   - Kernel clustering
   - State replication
   - Failover mechanisms
   - Load balancing

### Known Issues & Workarounds

1. **Model Path Hardcoded**
   - Issue: Mistral model paths hardcoded to `VrindaAI` folder
   - Workaround: Create symlink or set env variable
   ```bash
   mklink /J ".\llama.cpp" "C:\...\VrindaAI\llama.cpp"
   ```

2. **LLM Inference Slow on CPU**
   - Issue: Mistral running on CPU is slow
   - Workaround: Switch to `ollama` (abstract inference interface), use smaller models
   - Future: CUDA support for faster inference

3. **Voice/Vision Services Not in Agent Pipeline**
   - Issue: Voice and Vision run as standalone services, not integrated into agent messaging
   - Workaround: Call directly from Vryndara_Core/main.py
   - Future: Wrap as agents with standard message protocol

4. **Blender Rendering Timeout**
   - Issue: Long-running renders may timeout in browser
   - Workaround: Polling-based status checks with fallback to local rendering
   - Future: Queue-based render job system with pub/sub updates

---

## Key Integration Points for Aegis

### 1. **Primary Entry Point: SDK Client**

**Location:** `sdk/python/vryndara/client.py`

**In Aegis:** Create a connector module

```python
# aegis/vryndara_connector.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../Vryndara'))

from sdk.python.vryndara.client import AgentClient
import json

class VryndaraConnector:
    def __init__(self):
        self.client = AgentClient(
            agent_id="aegis-audit-engine",
            kernel_address="localhost:50051"
        )
        self.client.register([
            "audit.research",
            "audit.analysis",
            "audit.code_generation"
        ])
    
    def research_topic(self, topic: str, project_id: str) -> str:
        """Request Vryndara to research a topic"""
        self.client.send(
            target_id="researcher-1",
            msg_type="TASK_REQUEST",
            payload=json.dumps({
                "query": topic,
                "context": {"source_app": "aegis", "project_id": project_id}
            })
        )
        # Note: Client.listen() is blocking; use threading or async for responses
    
    def generate_code(self, prompt: str, project_id: str) -> str:
        """Request code generation"""
        self.client.send(
            target_id="coder-alpha",
            msg_type="TASK_REQUEST",
            payload=json.dumps({
                "instruction": prompt,
                "context": {"source_app": "aegis", "project_id": project_id}
            })
        )
```

### 2. **Asynchronous Response Handling**

Since `client.listen()` blocks, Aegis should use threading:

```python
import threading

class VryndaraConnector:
    def __init__(self):
        self.client = AgentClient(...)
        self.client.register([...])
        self.response_callbacks = {}  # Map request_id -> callback
        
        # Start listener in background thread
        listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listener_thread.start()
    
    def _listen_loop(self):
        """Background listener"""
        def handle_message(signal):
            if signal.source_agent_id in self.response_callbacks:
                callback = self.response_callbacks[signal.source_agent_id]
                callback(signal.payload)
        
        self.client.listen(handle_message)
    
    def research_topic_async(self, topic: str, callback):
        """Non-blocking research request"""
        self.response_callbacks["researcher-1"] = callback
        self.client.send(
            target_id="researcher-1",
            msg_type="TASK_REQUEST",
            payload=json.dumps({"query": topic})
        )

# In Aegis audit workflow:
def on_research_complete(result):
    print(f"Research complete: {result}")
    # Update Aegis UI, continue audit workflow

connector = VryndaraConnector()
connector.research_topic_async("GDPR compliance requirements", on_research_complete)
```

### 3. **REST Integration (Future)**

Once FastAPI REST endpoints are fully implemented:

```python
# aegis/vryndara_rest_connector.py
import requests
import json

class VryndaraRESTConnector:
    def __init__(self, gateway_url="http://localhost:8081"):
        self.gateway_url = gateway_url
    
    def research_topic(self, topic: str, project_id: str) -> dict:
        """Submit research task via HTTP"""
        response = requests.post(
            f"{self.gateway_url}/api/v1/task",
            json={
                "agent_id": "researcher-1",
                "task_type": "web_search",
                "payload": {
                    "topic": topic,
                    "context": {"source_app": "aegis", "project_id": project_id}
                }
            }
        )
        return response.json()
    
    def get_task_status(self, task_id: str) -> dict:
        """Check task status"""
        response = requests.get(f"{self.gateway_url}/api/v1/status/{task_id}")
        return response.json()
    
    def get_results(self, task_id: str) -> str:
        """Retrieve task results"""
        response = requests.get(f"{self.gateway_url}/api/v1/results/{task_id}")
        return response.text
```

### 4. **Create Custom Aegis Agent**

For specialized audit tasks, create an Aegis agent:

```python
# aegis/audit_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Vryndara')))

from sdk.python.vryndara.client import AgentClient
import json

class AegisAuditAgent:
    def __init__(self):
        self.client = AgentClient("aegis-audit-agent", kernel_address="localhost:50051")
        self.client.register(["audit.analysis", "audit.compliance"])
    
    def on_message(self, signal):
        if signal.type == "TASK_REQUEST":
            task = json.loads(signal.payload)
            
            if task.get("task_type") == "compliance_check":
                # Request researcher to gather regulations
                self.client.send(
                    target_id="researcher-1",
                    msg_type="TASK_REQUEST",
                    payload=json.dumps({
                        "query": f"Find {task['standard']} compliance requirements"
                    })
                )
            
            elif task.get("task_type") == "generate_audit_code":
                # Request coder to generate audit scripts
                self.client.send(
                    target_id="coder-alpha",
                    msg_type="TASK_REQUEST",
                    payload=json.dumps({
                        "instruction": task.get("code_prompt")
                    })
                )
    
    def run(self):
        self.client.listen(self.on_message)

if __name__ == "__main__":
    agent = AegisAuditAgent()
    agent.run()
```

**Run the agent:**
```bash
# Terminal 1: Start Vryndara kernel
python kernel/main.py

# Terminal 2: Start Aegis audit agent
cd aegis
python audit_agent.py

# Terminal 3: Aegis main app sends requests
# from vryndara_connector import AegisAuditAgent
# agent_client.send(target_id="aegis-audit-agent", ...)
```

### 5. **Data Flow Pattern: Aegis Request → Vryndara Processing**

```
┌──────────────────────────────────────────────────────────────┐
│ AEGIS APPLICATION                                            │
│                                                              │
│  AuditWorkflow:                                              │
│  1. User initiates "Generate GDPR Audit"                    │
│  2. Calls vryndara_connector.research_topic(...)             │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ gRPC Signal (TASK_REQUEST)
                 │ target: "researcher-1"
                 │ payload: "{query: "GDPR requirements"}"
                 ▼
┌──────────────────────────────────────────────────────────────┐
│ VRYNDARA KERNEL (localhost:50051)                            │
│                                                              │
│  1. Receives Signal from "aegis-audit-engine"               │
│  2. Broadcasts to "researcher-1"'s message queue             │
│  3. Logs event to PostgreSQL                                 │
│  4. Injects context into brain memory                        │
└─────────────────┬────────────────────────────────────────────┘
                  │
                  │ Enqueue to researcher's queue
                  ▼
┌──────────────────────────────────────────────────────────────┐
│ RESEARCHER AGENT (agents/researcher/main.py)                │
│                                                              │
│  1. Receives Signal with query                               │
│  2. Executes search_web("GDPR requirements")                 │
│  3. Scrapes results from DuckDuckGo                          │
│  4. Formats findings                                         │
│  5. Sends Signal back (TASK_RESULT) to "aegis-audit-engine" │
└─────────────────┬────────────────────────────────────────────┘
                  │
                  │ gRPC Signal (TASK_RESULT)
                  │ source: "researcher-1"
                  │ target: "aegis-audit-engine"
                  │ payload: "{findings: "...research data..."}"
                  ▼
┌──────────────────────────────────────────────────────────────┐
│ VRYNDARA KERNEL                                              │
│                                                              │
│  1. Receives TASK_RESULT from researcher                     │
│  2. Routes to "aegis-audit-engine"'s queue                   │
│  3. Logs to event history                                    │
│  4. Stores findings in ChromaDB memory                       │
└─────────────────┬────────────────────────────────────────────┘
                  │
                  │ Enqueue to Aegis message queue
                  ▼
┌──────────────────────────────────────────────────────────────┐
│ AEGIS APPLICATION                                            │
│                                                              │
│  on_research_complete() callback fired:                      │
│  1. Receives TASK_RESULT signal                              │
│  2. Extracts findings from payload                           │
│  3. Processes/analyzes for audit relevance                   │
│  4. Updates audit document with findings                     │
│  5. Continues audit workflow                                 │
└──────────────────────────────────────────────────────────────┘
```

### 6. **Storage Integration for Audit Files**

```python
from sdk.python.vryndara.storage import StorageManager

storage = StorageManager(bucket_name="aegis-audits")

# Audit workflow generates a document
audit_report = "findings: ...\n recommendations: ..."

# Save to Vryndara storage
local_path = "audit_report_2024.pdf"
with open(local_path, 'w') as f:
    f.write(audit_report)

# Upload to MinIO
url = storage.upload_file(local_path, object_name="AUDIT-2024-001.pdf")
print(f"Report accessible at: {url}")

# Download report in another session
storage.download_file("AUDIT-2024-001.pdf", "local_audit.pdf")
```

### 7. **Memory Injection for Audit Context**

Vryndara can remember audit context across requests:

```python
# In audit workflow — store audit context
from Vryndara_Core.services.brain_service import BrainService

brain = BrainService()

# Store audit facts
brain.store_memory(
    text="ISO 27001 Information Security Management: Controls A.5-A.18 cover organizational, personnel, asset, access, cryptography, physical, and operational controls.",
    metadata={
        "type": "audit_knowledge",
        "standard": "ISO27001",
        "audit_id": "AUDIT-2024-001"
    }
)

# Later, when processing similar audit
context = brain.retrieve_context("What are ISO 27001 requirements?")
# Returns stored memory about ISO 27001
```

---

## Data Flow Architecture

### Message Flow Layers

#### 1. Application Layer (Aegis)
```python
# User clicks "Generate Audit"
audit_service.create_audit(standard="ISO27001", scope="IT Department")
  ├─ vryndara_connector.research_topic(standard)
  │   └─ Signal: TASK_REQUEST → researcher-1
  │
  ├─ wait for response (blocking or callback)
  │   └─ Signal: TASK_RESULT ← researcher-1
  │
  └─ update audit with findings
```

#### 2. Transport Layer (gRPC)
```protobuf
Signal {
  id: "uuid",
  source_agent_id: "aegis-audit-engine",
  target_agent_id: "researcher-1",
  type: "TASK_REQUEST",
  payload: "{...json...}",
  timestamp: 1710868800
}
```

#### 3. Routing Layer (Kernel)
```
Kernel.Publish(signal)
├─ Enqueue to target agent's message queue
├─ Broadcast to subscribed agents
├─ Log to PostgreSQL event_log table
├─ Inject into ChromaDB memory
└─ Trigger special handlers (e.g., ComputationalEngineer)
```

#### 4. Processing Layer (Agent)
```python
def on_message(signal):
    parse_payload()
    do_work()
    send_result_back()
```

#### 5. Storage Layer (Database)
```sql
-- PostgreSQL Event Log
INSERT INTO event_log 
  (id, source, target, type, payload, timestamp)
VALUES ('abc', 'aegis-audit', 'researcher-1', 'TASK_REQUEST', '...', 1710868800);

-- ChromaDB Memory (Vector Database)
INSERT INTO vryndara_core_memory 
  (document: "ISO27001 controls...", metadata: {audit_id: "..."}, embedding: [...])
```

### Concurrent Request Handling

Vryndara handles multiple concurrent Aegis requests:

```
Time  Aegis Request 1        Aegis Request 2        Kernel               Researcher
────────────────────────────────────────────────────────────────────────────────
T0    send("research GDPR")                         
                             send("research CCPA")
T1                                                  receive both
                                                    enqueue both
T2                                                                        process GDPR
T3                                                                        process CCPA
T4                                                                        complete GDPR
                                                    send GDPR result
T5    receive GDPR result
                                                    send CCPA result
T6                             receive CCPA result
```

### Memory & Context Persistence

```
Vryndara Session 1:
├─ Aegis asks: "Find GDPR requirements"
├─ Researcher searches and returns findings
├─ Brain stores in ChromaDB with metadata: {audit_id: "AUD-001", type: "compliance_fact"}
└─ Audit workflow processes findings

Later Session 2:
├─ Aegis asks: "What were the GDPR requirements we found?"
├─ Brain queries ChromaDB: retrieve_context("GDPR")
├─ Returns stored facts from previous session
└─ Audit workflow builds on previous findings
```

---

## Deployment & Infrastructure

### Development Setup

**Prerequisites:**
- Python 3.10+
- PostgreSQL 15 (or Docker)
- Node.js 18+ (for UI)
- Blender 4.3
- Llama.cpp (for inference)

**Installation:**

```bash
# 1. Clone/navigate to Vryndara
cd Vryndara

# 2. Create Python environment
conda create -n vryndara python=3.10 -y
conda activate vryndara

# 3. Install dependencies
pip install -r Requirements.txt

# 4. Compile protobuf
python -m grpc_tools.protoc -I protos --python_out=. --grpc_python_out=. protos/vryndara.proto

# 5. Install as editable package
pip install -e .

# 6. Start PostgreSQL + MinIO
docker-compose up -d

# 7. Start LLM server (separate terminal)
cd C:\...\llama.cpp\build\bin\Release
.\llama-server.exe -m mistral.gguf --port 8080 -c 4096

# 8. Start Vryndara Kernel (separate terminal)
python kernel/main.py

# 9. Start Agents (separate terminals)
python agents/coder/main.py
python agents/researcher/main.py
python agents/media/main.py

# 10. Start Gateway/Bridge (separate terminal)
uvicorn gateway.main:socket_app --reload --port 8081

# 11. Start UI (separate terminal, if using React)
cd ui
npm run dev
```

### Production Deployment

**Using Docker:**

```yaml
# docker-compose.yml (already provided)
# Add services for each agent, kernel

version: '3.8'
services:
  vryndara-kernel:
    build:
      context: .
      dockerfile: kernel.Dockerfile
    ports:
      - "50051:50051"
    depends_on:
      - db
      - minio
      - llama-server
    environment:
      DATABASE_URL: postgresql://vryndara:password@db:5432/vryndara_core
      LLAMA_API: http://llama-server:8080
  
  coder-agent:
    build:
      context: .
      dockerfile: agents/coder/Dockerfile
    depends_on:
      - vryndara-kernel
    environment:
      KERNEL_ADDRESS: vryndara-kernel:50051
  
  researcher-agent:
    build:
      context: .
      dockerfile: agents/researcher/Dockerfile
    depends_on:
      - vryndara-kernel
  
  gateway:
    build:
      context: .
      dockerfile: gateway.Dockerfile
    ports:
      - "8081:8081"
      - "8888:8888"
    depends_on:
      - vryndara-kernel
  
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: vryndara_core
      POSTGRES_USER: vryndara
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
  
  llama-server:
    image: llama-cpp-python:latest
    ports:
      - "8080:8080"
    volumes:
      - ./models:/models
    command: python -m llama_cpp.server --model /models/mistral.gguf --port 8080

volumes:
  postgres_data:
  minio_data:
```

### Monitoring & Logging

**Current State:**
- Event logging to PostgreSQL (all inter-agent messages)
- File-based logs from each agent (print statements)
- Browser UI shows real-time agent status via WebSocket

**Recommended Additions:**
- ELK Stack (Elasticsearch, Logstash, Kibana) for centralized logging
- Prometheus for metrics (request counts, latency, errors)
- Grafana dashboards for visualization
- OpenTelemetry for distributed tracing

### Network Architecture

```
Production Network:
┌─ Load Balancer (nginx)
│  ├─ :80 → gateway:8081  (HTTP API)
│  ├─ :443 → gateway:8888 (HTTPS WebSocket)
│  └─ :8888 → UI:3000 (React frontend)
│
├─ Vryndara Service Network (internal)
│  ├─ Kernel :50051 (gRPC)
│  ├─ Agents (gRPC clients)
│  ├─ PostgreSQL :5432 (internal only)
│  └─ MinIO :9000 (internal S3 API)
│
└─ External Services
   └─ Llama.cpp Server :8080
```

---

## Recommendations for Aegis Integration

### Phase 1: Basic Integration (Immediate)

1. **Create VryndaraConnector module** in Aegis
   - Use SDK Python client
   - Implement async request/response handling
   - Map Aegis audit workflows to Vryndara agents

2. **Implement Aegis Agent** (optional but recommended)
   - Specialized agent for audit-specific tasks
   - Can orchestrate complex audit workflows internally

3. **Add Research Capability**
   - Audit workflows request compliance research from Vryndara Researcher
   - Store findings in local Aegis database + Vryndara memory

4. **Storage Integration**
   - Upload audit reports to MinIO
   - Retrieve historical reports from MinIO

### Phase 2: Advanced Features (Next Quarter)

1. **Create Custom Analyzer Agent**
   - Analyze research findings for audit relevance
   - Generate risk assessments
   - Extract key compliance gaps

2. **Implement Workflow Templates**
   - Pre-defined audit workflows (ISO27001, SOC2, etc.)
   - Multi-step orchestration through Vryndara

3. **Memory Injection**
   - Store audit knowledge in Vryndara's ChromaDB
   - Leverage cross-audit learning
   - Contextual recommendations from past audits

4. **Report Generation**
   - Future Reporter Agent generates professional audit reports
   - Integration with Aegis report formatting

### Phase 3: Enterprise Features (Long-term)

1. **Multi-Tenant Support**
   - Segregate Aegis data per client organization
   - Isolated audit knowledge bases per tenant

2. **API-Based Integration**
   - REST endpoints instead of gRPC client
   - Decouples from Vryndara Python client library

3. **Scheduling & Automation**
   - Future Scheduler Agent for periodic compliance checks
   - Automated report generation on schedules

4. **Advanced Observability**
   - Distributed tracing of audit requests
   - Performance metrics and SLAs
   - Compliance audit trail of Vryndara interactions

---

## Summary: Key Takeaways

| Aspect | Details |
|--------|---------|
| **Primary Integration** | SDK `AgentClient` in `sdk/python/vryndara/client.py` |
| **Kinnel Entry Point** | `localhost:50051` (gRPC) |
| **Key Agents** | researcher-1, coder-alpha, media-director (extensible) |
| **Request Pattern** | Send gRPC Signal → Kernel → Agent → Process → Response Signal |
| **Memory System** | ChromaDB (semantic, persistent across sessions) |
| **Storage** | MinIO S3-compatible (bucket: vryndara-assets) |
| **Databases** | PostgreSQL (event log), ChromaDB (memory) |
| **Authentication** | Currently none; planned for Phase 2+ |
| **Async Handling** | Use threading for non-blocking listen loops |
| **Future REST API** | Gateway endpoints being developed (currently WebSocket-only) |

---

## Contact & Support

For issues, questions, or feature requests regarding Vryndara integration:

1. Check `docs/` folder in Vryndara root
2. Review agent implementations in `agents/` folder
3. Consult proto definitions in `protos/vryndara.proto`
4. Test with provided example: `test_historabook_mock.py`

---

**Document Version:** 1.0  
**Last Updated:** March 19, 2026  
**Status:** Complete & Production-Ready (with noted limitations)
