# Aegis System Architecture

## High-Level Overview

Aegis is a decentralized digital twin framework comprising five integrated layers:
1. **IoT Edge Layer** — Sensors and actuators collecting/controlling physical assets
2. **Backend Layer** — FastAPI REST API for data ingestion, orchestration, and business logic
3. **Cognitive Layer** — Vryndara AI kernel for autonomous decision-making
4. **Blockchain Layer** — Ethereum smart contracts for anti-forensic audit trails
5. **Frontend Layer** — Next.js SaaS dashboard for real-time monitoring and control

All layers operate offline-first with eventual consistency via blockchain sync.

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                          │
│  ┌──────────────────┐  ┌────────────────┐  ┌──────────────────┐│
│  │  Dashboard       │  │  Real-time UI  │  │  RBAC Controls   ││
│  └──────────────────┘  └────────────────┘  └──────────────────┘│
└──────────────────────┬───────────────────┬──────────────────────┘
                       │                   │
         ┌─────────────┴─────────────┬─────┴────────────────┐
         │                           │                      │
    HTTP/REST                   WebSocket              User Actions
         │                           │                      │
┌────────▼──────────────────────────▼──────────────────────▼──────┐
│              Backend (FastAPI + SQLAlchemy)                      │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────────┤
│  │ Auth/RBAC    │  │  Tenant Manager │  │  Zone Management     │
│  │ (JWT, OAuth) │  │  (Multi-tenant) │  │  (Assets & Sensors)  │
│  └──────────────┘  └─────────────────┘  └──────────────────────┤
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────────┤
│  │ Data Ingest  │  │  Orchestrator   │  │  Control Dispatcher  │
│  │ (sensor data)│  │  (workflow mgmt)│  │  (actions to edge)   │
│  └──────────────┘  └─────────────────┘  └──────────────────────┤
└──┬─────────┬────────────┬──────────────────┬──────────────┬─────┘
   │         │            │                  │              │
   │         │            ▼                  │              │
   │         │    ┌─────────────────┐        │              │
   │         │    │ Vryndara AI     │        │              │
   │         │    │ Orchestrator    │        │              │
   │         │    │ (Multi-agent)   │        │              │
   │         │    └────────┬────────┘        │              │
   │         │             │                 │              │
   │    ┌────▼─────┐   ┌───▼──────┐    ┌────▼─────┐   ┌────▼─────┐
   │    │Local SQLite   │Blockchain │    │ MQTT     │   │ IoT Edge │
   │    │(SQLite 3.x)   │ Node      │    │ Broker   │   │ Devices  │
   │    └────┬─────┘    │(Hardhat)  │    └──┬───────┘   └────┬─────┘
   │         │          │           │       │                 │
   └─────────┴──────────┴───────────┴───────┴─────────────────┘
             │                      │              │
         Local DB              Blockchain      Sensor/Actuator
         (Offline)             (Audit Trail)   (Physical Assets)
```

---

## Layer Descriptions

### 1. IoT Edge Layer
**Technology Stack:** ESP32, MicroPython, MQTT
**Components:**
- Temperature/humidity sensors
- Motion detectors
- Relay/actuator controllers
- Local WiFi/mesh networking

**Responsibilities:**
- Sense physical state
- Publish data to local MQTT broker
- Subscribe to control commands
- Cache data locally if network unavailable

**Data Format:**
```json
{
  "device_id": "esp32_zone01_temp",
  "device_type": "temperature_sensor",
  "zone_id": "zone_001",
  "value": 23.5,
  "unit": "celsius",
  "timestamp": "2026-03-19T10:30:00Z",
  "battery_level": 85,
  "signal_strength": -65
}
```

---

### 2. Backend Layer (FastAPI)
**Technology Stack:** FastAPI, SQLAlchemy, SQLite (local) + PostgreSQL (cloud)
**Key Endpoints:**

#### Sensor Data Ingestion
- `POST /api/v1/sensors/{sensor_id}/data` — Ingest sensor readings
- `GET /api/v1/zones/{zone_id}/sensors` — List zone sensors

#### Tenant & RBAC
- `POST /api/v1/tenants` — Create tenant
- `GET /api/v1/tenants/{tenant_id}/users` — List tenant users
- `POST /api/v1/users/{user_id}/roles` — Assign RBAC role

#### Zone Management
- `POST /api/v1/zones` — Create zone (asset management)
- `GET /api/v1/zones/{zone_id}` — Get zone state
- `PUT /api/v1/zones/{zone_id}/state` — Update zone state

#### AI Orchestration
- `POST /api/v1/analyze` — Send data for AI analysis
- `GET /api/v1/analysis/{analysis_id}` — Get analysis result
- `POST /api/v1/execute` — Execute AI-recommended action

#### Control Dispatcher
- `POST /api/v1/actions/{action_id}/execute` — Execute control action
- `GET /api/v1/actions/{action_id}/status` — Get action status

#### Blockchain Integration
- `POST /api/v1/audit/anchor` — Anchor event to blockchain
- `GET /api/v1/audit/trail/{zone_id}` — Get audit trail

**Database Schema:**
- `tenants` — Multi-tenant isolation
- `zones` — Physical asset/operational zones
- `sensors` — Sensor metadata and mappings
- `actuators` — Actuator metadata and mappings
- `audit_logs` — Immutable action logs (before blockchain)
- `user_roles` — RBAC role assignments

---

### 3. Cognitive Layer (Vryndara AI)
**Technology Stack:** CrewAI, LangChain, OpenAI GPT
**Agents:**

#### Analyst Agent
- Input: Sensor data from zone
- Processing: Identify patterns, anomalies, trends
- Output: Analysis report with recommendations

#### Executor Agent
- Input: Analysis report + recommendations
- Processing: Safety validation, zone state checks
- Output: Approved/rejected action command

**Request-Response Contract:**
```
Backend → AI:
{
  "agent_action": "analyze_zone_data",
  "zone_id": "zone_001",
  "sensor_data": [...]
}

AI → Backend:
{
  "analysis_id": "...",
  "actions": [...],
  "confidence": 0.87
}
```

---

### 4. Blockchain Layer (Hardhat)
**Technology Stack:** Hardhat, Solidity, Web3.py
**Smart Contracts:**
- `AegisAudit.sol` — Immutable audit log contract
  - Function: `recordEvent(zone_id, action_hash, timestamp)`
  - Function: `getEventProof(event_id)`
  - Function: `verifyIntegrity(event_data, merkle_proof)`

**Anchor Strategy:**
- Every 15 minutes (or on critical action), hash all pending audit logs
- Submit merkle root to blockchain for proof
- Enables offline operation with eventual on-chain verification

**Offline Mode:**
- Local test network (`npx hardhat node`)
- Sync to live network when connectivity available
- Dual anchoring: local + on-chain

---

### 5. Frontend Layer (Next.js)
**Technology Stack:** Next.js, React, Tailwind CSS, Recharts
**Pages:**
- `/login` — User authentication
- `/dashboard` — Real-time zone status
- `/zones` — Zone/asset management
- `/analytics` — Historical data and trends
- `/audit` — Blockchain audit trail viewer
- `/settings` — User/tenant settings

**Components:**
- Real-time zone status cards (temp, humidity, alerts)
- Action history timeline
- AI decision explanations
- WebSocket connection for push updates

---

## Data Flow Scenarios

### Scenario 1: Normal Operation (Online)
```
Sensor publishes → MQTT → Backend receives → 
Stores in local SQLite → Vryndara analyzes → 
AI recommends action → Backend validates → 
Executor sends command → Sensor executes → 
Action logged locally → Blockchain anchor syncs
```

### Scenario 2: Offline Operation
```
Sensor publishes → Local MQTT queue → Backend (local) receives →
Stores in local SQLite → Vryndara analyzes (edge AI) →
Cached AI model recommends → Action logged locally →
Cache pending sync when network returns
```

### Scenario 3: Network Partition
```
Sensor operates locally ✓ → MQTT queue builds up → 
Backend queues data ✓ → AI decisions cached ✓ →
Actions stored in SQLite → Status shown as "pending sync" →
When network returns: bulk replay of queued data → 
Blockchain syncs pending audit entries
```

---

## Integration Procedures

### 1. Sensor to Backend
- MQTT over TLS on local broker
- Sensor publishes to `aegis/devices/{device_id}/telemetry`
- Backend subscribes; validates schema; stores in DB
- Metadata: sensor_id, device_type, zone_id, timestamp

### 2. Backend to Vryndara
- HTTP POST to local AI orchestrator
- Payload: sensor_data, zone_id, analysis_type
- Response: recommendations with confidence scores

### 3. Vryndara to Actuators
- Backend dispatcher receives AI decision
- Safety validation: check zone state, limits, conflicts
- MQTT publish to `/aegis/commands/{device_id}/action`
- Actuator executes; reports back via sensor data
- Audit log created immediately

### 4. Backend to Blockchain
- Event hashing: SHA-256(action_data + timestamp)
- Local storage: immutable audit log in SQLite
- Periodic anchor: merkle root → blockchain
- Verification: frontend can validate any action

---

## Security Layers

| Layer | Mechanism |
|-------|-----------|
| **Transport** | TLS 1.3 on all connections |
| **Authentication** | JWT tokens (short-lived) + Refresh tokens |
| **Authorization** | RBAC (roles: admin, operator, viewer, analyst) |
| **Data Integrity** | SHA-256 hashing on all audit events |
| **Audit Trail** | Immutable blockchain anchoring |
| **Offline Resilience** | Local-first with eventual consistency |

---

## Offline-First Design Principles

1. **All core operations work offline:**
   - Data ingestion ✓
   - AI analysis ✓
   - Actuation ✓
   - Audit logging ✓

2. **Blockchain as async backup:**
   - Not required for real-time operation
   - Syncs when network available
   - Provides forensic evidence

3. **Local-first database:**
   - SQLite for edge, PostgreSQL for cloud
   - Sync via standard replication
   - Conflict resolution via timestamps

4. **Queue-based integration:**
   - MQTT for sensor→backend
   - Redis/RabbitMQ for backend queuing (future)
   - Store-and-forward semantics

---

## Future Extensions

1. **Hardware Integration (Phase 2)**
   - Real ESP32 firmware deployment
   - Mesh networking (ZigBee/LoRaWAN)
   - Industrial sensor integration (Modbus, OPC-UA)

2. **Advanced AI (Phase 2)**
   - ML model fine-tuning on proprietary data
   - Predictive maintenance algorithms
   - Natural language command processing

3. **Cloud Sync (Phase 2)**
   - PostgreSQL cloud backend
   - API gateway for multi-region sync
   - CDN for frontend distribution

4. **Enterprise Features (Phase 2)**
   - Factory smart contracts for vendor onboarding
   - SLA monitoring and reporting
   - Advanced analytics and ML dashboards

