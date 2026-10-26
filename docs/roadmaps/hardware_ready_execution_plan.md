# Hardware-Ready Execution Plan

## 1. Project goal

Build a complete Aegis estate digital twin that is realistic, tenant-aware, operationally coherent, and easy to connect to real hardware without redesigning the platform.

The system must behave as a single-source smart estate:
- one canonical database for devices, zones, sensors, robots, actuators, alerts, telemetry, and audit
- one clear asset taxonomy
- one operational workflow from monitoring to control to escalation
- one clean interface model that can later map to MQTT, serial, REST, and gRPC hardware adapters

---

## 2. Design principles

1. Single source of truth
   - No duplicate mock datasets or parallel storage layers.
   - Every asset, event, and state change flows through the canonical backend and database.

2. Realistic estate modeling
   - Each zone owns the assets required for its purpose.
   - Sensors, robots, and actuators are not random examples; they reflect actual estate functions.

3. Hardware-ready abstraction
   - The software layer must separate business logic from transport protocols.
   - Devices are represented as logical assets that can map to physical interfaces later.

4. Clean page architecture
   - Each page has a unique purpose.
   - Duplicate control panels and repeated telemetry cards are removed.
   - Navigation reflects operational flow rather than exploratory experiments.

5. Auditability and traceability
   - Every created, changed, removed, or viewed asset must be traceable through logs and audit records.

---

## 3. Canonical asset model

### Estate layer
- Estate overview
- Zones
- Areas and operational subzones
- Safety perimeter and environmental regions

### Asset layer
- Sensors
- Actuators
- Robots
- Devices
- Communication gateways
- Integration adapters

### Operational layer
- Telemetry streams
- Alert engine
- Automation rules
- Task scheduling
- Role-based controls

### Governance layer
- Audit trails
- Compliance reviews
- User and role management
- Tenant configuration

---

## 4. Required page structure

### Primary estate pages
- Estate Dashboard
- 3D Scene
- Zones
- Sensors
- Robots
- Devices
- Actuators
- Environmental Monitoring
- Safety Dashboard
- Water Dashboard
- Waste Dashboard
- System Control
- AI / Vryndara
- Profile

### Operational control pages
- Task Scheduler
- Task Board
- Schedules
- Communication Channels
- System Analytics
- Alerts Configuration
- Storage

### Governance and audit pages
- Audit Logs
- User Directory
- Compliance Reports
- Evidence Review
- Admin Users
- Admin Roles
- Tenant Settings
- Notifications
- Playback

### Advanced/maintenance pages
- Scene Admin
- Sensor Management
- Zone Management
- Lab Automation
- Optional diagnostic pages that are clearly marked as advanced operational tools

Any page that duplicates another page’s function must be merged or moved under a proper operational label.

---

## 5. Execution roadmap to hardware-ready design

### Phase 1 — Repository and system cleanup
- Archive legacy one-off scripts and temporary debug files.
- Remove duplicate root clutter and keep only active project files.
- Normalize the docs structure and route inventory.
- Establish a canonical asset schema and zone structure.

### Phase 2 — Single-source estate simulation
- Seed a realistic estate layout with zone-based services.
- Create an authoritative device catalog for each zone.
- Link sensors, actuators, and robots to the correct operational function.
- Ensure telemetry, state, and automation derive from the same backend source.

### Phase 3 — Frontend architecture cleanup
- Consolidate all pages into a clear navigation hierarchy.
- Remove noisy or duplicate control surfaces.
- Keep one estate representation and one detailed asset workflow per domain.
- Deliver a stable dashboard and 3D scene experience backed by one source of truth.

### Phase 4 — Automation and digital twin behavior
- Add realistic simulation of thresholds, actions, and event triggers.
- Link environmental conditions to automated control decisions.
- Connect robot and actuator behaviors to zone operations.
- Surface alerts and recommendations from the same data flow.

### Phase 5 — Audit, security, and traceability
- Every asset lifecycle action records who changed or viewed it.
- Keep audit logs synchronized with frontend and backend events.
- Enforce tenant scope and role-based access control.
- Validate that no duplicate or inconsistent state remains across layers.

### Phase 6 — Hardware-ready integration layer
- Define asset adapters for MQTT, serial, REST, and gRPC.
- Standardize message formats for telemetry and commands.
- Create an adapter layer that maps logical Aegis devices to physical hardware channels.
- Ensure simulated devices can be swapped for real devices without rewriting core workflows.

### Phase 7 — Real hardware onboarding
- Connect a physical sensor node or actuator cluster in a controlled environment.
- Verify protocol translation and device registration.
- Validate telemetry ingestion and actuation command execution.
- Confirm the audit trail records hardware-triggered events correctly.

### Phase 8 — Field validation and hardening
- Run stability checks, fault handling, and recovery tests.
- Validate resilience under offline conditions and device disconnects.
- Finalize operator dashboards, alerts, and command health views.
- Prepare the platform for pilot deployment.

---

## 6. Acceptance criteria for completion

The project is ready for realistic hardware integration only when all of the following are true:

- there is one canonical database and no split legacy state
- every zone has realistic asset inventory and purpose
- every sensor, robot, actuator, and device is traceable by zone and tenant
- each page has a unique operational role with no duplicate purpose
- telemetry, control actions, and audit records are consistent across frontend, backend, and database
- the digital twin can be driven by software simulation and later replaced with hardware devices without major redesign
- the system supports CRUD operations for estate assets, zones, and controls
- the operator can view collected data, logs, visualizations, and decisions in one coherent workflow

---

## 7. Immediate next tasks

1. complete the page taxonomy cleanup and remove duplicate navigation clutter
2. validate a realistic estate seed for all major zones and systems
3. standardize telemetry + alert flow from backend to dashboard
4. finalize hardware adapter contracts for device connectivity
5. run the full regression set after each refactor

---

## 8. Working principle for future implementation

Aegis must be designed as a software-first digital twin that remains physically extensible. The simulation layer is not an end in itself; it is the training ground for the real world. The goal is to connect a digital twin to physical hardware later without breaking the platform’s model, controls, or audit traceability.
