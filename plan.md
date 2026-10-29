# Aegis Hardware-Ready Execution Plan

## Current status and execution order — 2026-10-27

This plan records work completed to date and the remaining path to a coherent,
operational Aegis system. "Implemented" describes code or test coverage;
hardware results labeled owner-reported have not been independently verified
in this development environment. Simulated data, demo gRPC services, and
recommendations must never be represented as physical measurements or
autonomous hardware control.

### Priority order

1. **Phase 6 — 3D scene editor and operational visibility/control** is the
   highest-priority active software milestone. The current scene is a useful
   tenant-scoped viewer with selection, inspector, CRUD, history, media
   review, and camera/orbit navigation; it is not yet a full editor.
2. **Phase 7 — Protocol, protobuf/gRPC, and service integration** connects
   the existing contracts and service implementations into one observable,
   versioned, authenticated system without claiming unavailable hardware.
3. **Phase 8 — Rules, safety, Vryndara AI, and governed decisions** connects
   verified input data to explainable recommendations and explicitly
   authorized, safety-checked actions.
4. **Phase 9 — End-to-end simulation, verification, and operational
   readiness** validates the complete software path before expanding to
   physical devices.
5. **Phase 10 — Asset-by-asset hardware onboarding** adds one measured,
   supported physical asset at a time. The current Arduino LED remains a
   narrowly scoped pilot.
6. **Phase 11 — Deployment and final acceptance** is last; do not declare
   production or estate-wide readiness before earlier acceptance criteria
   and per-asset commissioning are complete.

Phases 6–11 are ordered work, not claims that the entire project is complete.
Subtasks may be implemented in small increments, but deployment remains the
final milestone.

## Goal
Build a clean, realistic, hardware-ready digital twin for the estate with a single authoritative data model, clear page roles, and a validated path from simulated assets to real devices.

## Core rules
- One source of truth for estate, zones, assets, telemetry, commands, and audit records.
- One page = one primary purpose.
- No duplicate state across frontend, backend, and database.
- Simulation exists as a software model of the real world, not as a disconnected mock system.
- Every asset must be able to map to a physical hardware adapter later without redesigning the platform.

---

## Phase 0 — Project cleanup and architecture stabilization

### Checklist
- [x] Remove duplicate root and scratch files from active project flow
- [x] Keep only active app folders and active project documents in the root structure
- [x] Archive legacy experimental pages and scripts that are not part of the main estate workflow
- [x] Confirm all active routes represent real product use cases
- [x] Verify the sidebar only contains operational pages and admin/audit pages with clear purpose
- [x] Confirm there is one canonical estate model and one canonical device schema
- [x] Ensure developer documentation points to the real working roadmap

### Deliverable
A clean project structure where only the real estate and operations workflow remains active.

### Status
Phase 0 and Phase 1 are complete and verified.

---

## Phase 1 — Single-source estate simulation model

### Checklist
- [x] Define the canonical estate layout: greenhouse, water vault, waste zone, robotics bay, security perimeter, swimming pool, multi level agriculture, hydroponic plantation, garden, office, server room, warehouse
- [x] Link each zone to its applicable sensors, robots, devices and actuators dynamically
- [x] Define robots, devices, and actuator types for each operational zone
- [x] Create realistic telemetry profiles for each asset category
- [x] Introduce automation rules tied to actual estate operations
- [x] Ensure all simulation state is stored through database-backed device models
- [x] Validate cross-zone consistency, no duplicate asset definitions
- [x] Validate all telemetry flows from backend to dashboard through same source

### Example asset mapping
- Greenhouse: temperature, humidity, soil, irrigation, lighting, vent actuators
- Water Vault: water level, flow, quality, pump and valve actuators
- Waste Zone: waste level, sorting efficiency, compactor and conveyor control
- Robotics Bay: robot health, battery, charging, route tasks
- Security Perimeter: motion, camera, access gate, lock actuator

### Deliverable
A realistic estate model where each zone contains meaningful equipment and operational logic.

### Status
Phase 1 is complete and verified. Phase 2 is complete. Phase 3 software-demo validation is complete; field calibration and hardware validation remain outstanding. Phase 4 audit, governance, and traceability is complete. Phase 5 adapter abstraction is software-complete; physical commissioning remains outstanding.

---

## Phase 2 — Frontend page structure and unique responsibilities

### Checklist
- [x] Review and improve each existing page route below; do not add pages.
- [x] `/` — home/entry
- [x] `/3d-scene` — 3D estate view
- [x] `/actuators` — actuator controls
- [x] `/admin/roles` — role governance
- [x] `/admin/settings` — removed on user request; tenant API settings are retained for backend compatibility
- [x] `/admin/users` — user administration
- [x] `/ai` — AI recommendations
- [x] `/alerts-configuration` — alert rules
- [x] `/audit-logs` — audit history
- [x] `/auditor/evidence` — evidence review
- [x] `/auditor/reports` — compliance reports
- [x] `/communication-channels` — communications health
- [x] `/devices` — device registry
- [x] `/environmental` — environmental monitoring
- [x] `/estate-dashboard` — estate overview
- [x] `/login` — authentication
- [x] `/profile` — personal account
- [x] `/reset-password` — password recovery
- [x] `/robots-management` — robot fleet
- [x] `/safety-dashboard` — security and incidents
- [x] `/schedules` — operational schedules
- [x] `/sensors` — telemetry inventory
- [x] `/signup` — account registration
- [x] `/storage` — storage and inventory
- [x] `/system-analytics` — system analytics
- [x] `/system-control` — system orchestration
- [x] `/task-scheduler` — robot task scheduling
- [x] `/user-management` — user directory
- [x] `/waste-dashboard` — waste operations
- [x] `/water-dashboard` — water operations
- [x] `/zones` — zone ownership and resources
- [x] Estate Dashboard = overview, KPI summary, critical alerts, system health only
- [x] Zones = operational zone ownership, layout, zone-specific resources
- [x] Sensors = telemetry inventory, readings, health, thresholds, filters
- [x] Robots = fleet status, missions, availability, task states, robot control and automation
- [x] Devices = registry of connected devices and lifecycle status
- [x] Actuators = commands, outputs, control state, automation actions
- [x] Environmental = climate, temperature, humidity, air quality, weather context
- [x] Safety = access, security perimeter, alerts, incident state
- [x] Water = water flow, storage, leak and irrigation management
- [x] Waste = handling, sorting, processing, disposal state
- [x] System Control = orchestration and command execution
- [x] AI = Vryndara decisions, optimization, recommendations
- [x] Admin / Users / Audit = governance, traceability, evidence, compliance
- [x] Remove duplicate panels and repeated widgets across pages
- [x] Make each page consistent with the same estate model and system schema

### Deliverable
A clean operational frontend where no page duplicates another page’s purpose.

### Status
Phase 2 is complete and verified. Phase 3 software-demo validation is complete; field calibration and hardware validation remain outstanding. Phase 4 audit, governance, and traceability is complete. Phase 5 adapter abstraction is software-complete; physical commissioning remains outstanding.

### Progress
- Estate Dashboard: complete. Uses tenant-scoped device/zone/health counts, current alert conditions, and links to owning pages; removed fabricated metrics and duplicate CRUD/control surfaces. Production build passes.
- Zones: complete. Admin-only CRUD now matches backend RBAC; the page uses the canonical digital-twin device inventory for zone resources and reports actual resource assignment counts. Frontend production build passes.
- Sensors: complete. Uses the shared auth token, edits persisted sensor fields including zone assignment without discarding state metadata, searches names and device IDs, and distinguishes unknown/offline connectivity. Frontend production build passes.
- Devices: complete. Uses shared auth, human-readable zone ownership, name/type/ID/zone filters, and separate online/offline/unknown counts with lifecycle metadata. Frontend production build passes.
- Actuators: complete. Uses shared auth, role-gates controls to backend-supported roles, shows command progress, zone/control mode and unknown output distinctly. Frontend production build passes.
- Robots: complete. Reads/writes canonical digital-twin robots, persists real zone/activity/type, avoids fabricated battery/position values, and adds role-gated inspection/emergency-stop actions with request feedback. Frontend production build passes; the route's hook warning is cleared.
- Environmental: complete. Passes the shared authenticated token into the dashboard, preserves zone choice, loads current metrics independently of optional trend history, validates setpoint changes, supports HVAC mode/scenes, and removes unsupported purifier/VOC safety claims. Frontend production build passes; live backend/browser verification remains part of final route QA.
- Water: complete. Displays persisted collection/purification/irrigation/recycling/quality state, derives real volume and system counts, and creates collection systems via the tenant API. Frontend production build passes.
- Waste: complete. Displays persisted metrics, container fill, compost/recycling processes and sorting history; creates containers and records sorting events through the API. Removed the non-persistent local-only delete control because no delete endpoint exists. Frontend production build passes.
- Safety: complete. Uses the shared token, removes the unscoped unauthenticated SSE stream, directs commands to the API origin, binds patrols and evacuation to registered robots/zones, and renders unknown states fail-closed with inline errors. Frontend production build passes.
- System Control: complete. Uses the real estate snapshot endpoint, role-gates operational controls, exposes the fleet emergency stop, and removes unsupported pause/resume and fabricated anomaly actions. Frontend production build passes.
- Role Management: complete. Removed browser-only custom role/permission creation that the API did not persist; the admin-only page documents the backend-supported fixed roles and links to actual user assignments. Frontend production build passes.
- Tenant Settings: retired on request. The page and sidebar entry are removed; backend settings remain for existing soil-moisture automation compatibility.
- User Administration: complete. Uses the shared session token for tenant-scoped create/list/role/delete operations, removes unsupported permission claims, and prevents self-role changes in the UI. Frontend production build passes.
- AI: complete. Replaced timed fabricated audit output with tenant-authenticated predictive, optimization, and adaptation recommendations from the digital-twin health API. Frontend production build passes.
- Alerts Configuration: complete. Replaced fake local rules with tenant-authenticated notification-rule list/create/delete operations and explicit condition/status display. Frontend production build passes.
- Audit Logs: complete. Shows structured actor, action, target, outcome, details, blockchain transaction, and timestamp fields; successful login/logout and asset lifecycle events persist this metadata.
- Evidence Review: complete. Reconciles database audit hashes against recent blockchain entries and distinguishes verified, unmatched, and unavailable states instead of marking every row verified. Frontend production build passes.
- Compliance Reports: complete. Displays the backend blockchain compliance counters and tenant audit-event distribution; missing chain data remains unavailable instead of implying low risk. Frontend production build passes.
- Communication Channels: complete. Maps real tenant channel schema and status/latency/signal fields, creates channels using supported fields, and invokes the backend sync operation. Frontend production build passes.
- 3D Scene foundation: implemented. Loads authenticated tenant devices/zones, positions object-shaped device coordinates correctly, offers drone/orbit views and role-gated device/zone CRUD, and uses roofless zone footprints to avoid covering assets. The full scene-editor, visibility, interaction, and operational-control scope is still open in Phase 6; camera streaming and archived footage are not available without configured capture hardware.
- Home: complete. Reduced `/` to authenticated dashboard/login routing with a direct continuation link; removed unreachable promotional UI and fabricated system metrics. Frontend production build passes.
- Login: complete. Removed hard-coded emergency override credentials and fabricated token issuance, routes authenticated sessions directly to the estate dashboard, and links to password recovery. Frontend production build passes.
- Signup: complete. Requires an explicit tenant ID, creates viewer-only accounts in dev/test, and rejects public self-registration in production. Security regressions and frontend production build pass.
- Profile: complete. Implements the previously missing authenticated password-change endpoint, verifies current credentials, updates bcrypt hash, revokes sessions, audits the change, and routes the user to sign in again. Regression test and frontend production build pass.
- Reset Password: complete. The page now accurately states that requests are audited but no email/reset link is sent, and directs users to their tenant administrator. Frontend build and auth regressions pass.
- Schedules: complete. Restricted the page to authenticated tenant HVAC schedule CRUD, removed overlapping lab-job/E-stop workflows and unauthenticated SSE, and added accurate form feedback/validation. Frontend production build passes.
- Storage: complete. Uses tenant-scoped facility/inventory create, read, update, and delete operations; protects non-empty facility deletion; audits changes; and provides search, expiry filtering, and refreshed-at status. Focused API tests and frontend production build pass.
- System Analytics: complete. Uses canonical tenant digital-twin health/device data as its required source and treats monitoring history as optional enrichment; offers selectable persisted metric history and refresh status.
- Task Scheduler: complete. Replaced nonexistent generic task CRUD with authenticated enqueue/queue/assign/cancel operations and uses registered tenant robots. Frontend production build passes; the loader hook warning is cleared.
- User Directory: complete. Replaced a duplicate page calling nonexistent CRUD endpoints with a compatibility redirect to the canonical `/admin/users` route and removed the duplicate sidebar entry. Frontend production build passes.
- Estate Dashboard: complete. Uses tenant-scoped device/zone/health counts, active alert conditions, recent asset readings, and eight live system panels instead of an audit feed. Periodically refreshes the live tenant snapshot. Frontend production build passes.
- Remaining routes: none. All active routes are checked; `/admin/settings` was subsequently retired on request.
- Phase 3: operational integration and generic demo-simulation validation are complete. Field calibration and hardware validation remain outstanding. Phase 4 audit, governance, and traceability is complete; Phase 5 adapter abstraction is software-complete, with physical commissioning outstanding.

---

## Phase 2 follow-up review

### Completed in this follow-up
- [x] Alerts: build threshold rules from registered sensor state and manually evaluate them against current tenant-scoped readings.
- [x] Analytics: display persisted metric history with metric and time-window selection and automatic refresh.
- [x] System Control: replace the synthetic map and hard-coded statistics with a live tenant asset status board.
- [x] Storage: add inventory search, facility selection, expiry filters, lot attention counts, and refreshed-at status.
- [x] Audit logs: persist the actual blockchain transaction hash for new audit submissions, add a transaction-reference filter, and clarify missing references.
- [x] Compliance: add report windows, live refresh, verification coverage, database transaction-reference counts, and the latest audit record.
- [x] Evidence: show matched chain actor, severity, timestamp, log index, metadata, and verification state.
- [x] Audit lifecycle: persist actor, action, entity, outcome, and details for login/logout, sensor/zone/storage/device CRUD, and device commands; return the blockchain transaction hash where the connector succeeds.
- [x] Role visibility: the existing role page is restricted to administrators; backend roles remain fixed and permission checks remain endpoint-enforced.
- [x] Tenant Settings: remove the page and sidebar link on request; retain the backend settings API for soil-moisture automation compatibility.
- [x] 3D scene: replace giant cone roofs and overlapping static props with estate-scale zone footprints, transparent walls, labels, an oblique drone/orbit view, corrected object-shaped device coordinates, asset positioning, and selected-asset CRUD.
- [x] Estate dashboard: organize current tenant assets into eight operational system panels with status, attention, reading, and detail links.

### Backend follow-ups still required
- [x] Persist tenant-scoped custom role/permission definitions, enforce resolved permissions in protected APIs, and support role management in the UI.
- [x] Persist surveyed zone positions, dimensions, coordinate-system labels, and units; the 3D planning layout remains explicitly inferred for zones without surveyed geometry.
- [x] Persist per-device simulation snapshots and camera media, expose tenant-scoped history/media APIs, connect the 3D inspector, and apply configurable retention.
- [x] Integrate alert delivery-provider configuration into the alert configuration page, with sensitive configuration values redacted from list responses.
- [x] Add migration revisions `0013_tenant_roles_spatial_twin_history` and `0014_zone_geometry_defaults` after structured audit revision `0012_structured_audit_events`; apply `python -m alembic -c backend\alembic.ini upgrade head` to new or existing deployments before starting the backend.

## Phase 3 — Data flow, automation, and live twin behavior

### Checklist
- [x] Connect dashboard to canonical estate backend data
- [x] Keep telemetry updates in a single data path
- [x] Ensure alert generation is triggered by system conditions only once per event
- [x] Make automation rules operate on underlying device health and thresholds
- [x] Attach zone, sensor, and actuator state to their owning estate objects
- [x] Keep robot task execution consistent with digital twin state
- [x] Validate controls are role-aware and tenant-scoped
- [x] Validate audit logs capture create, update, delete, view, and command activity
- [x] Ensure no inconsistent duplication across database, frontend, and API responses
- [x] Validate the generic demo simulator against deterministic water/soil, climate, structural-response, and robot-motion scenarios; keep all uncalibrated assumptions visible.
- [x] Seed tenant water, waste, and storage demo records; expose explicit, bounded simulation steps that only modify demo-scoped state.
- [x] Wire the local robot control simulator through gRPC and show Vryndara gRPC / ROS 2 readiness without claiming physical connectivity.

### Progress
- Dashboard and 3D consumers use the tenant-scoped digital-twin device, zone, and health APIs.
- Legacy sensor ingestion now updates the matching canonical twin device, persists digital-twin history, evaluates tenant-scoped automation, and emits the same tenant-room twin events.
- Random sensor/status/scene emitters were removed from the live stream; playback remains a separate historical workflow.
- Alert notifications represent episode start/escalation and recovery transitions; offline sources cannot trigger automation.
- Soil moisture now uses a configurable discrete water-balance model, and robots no longer drift randomly. Task execution updates persisted tenant-owned robot state and surveyed zone position when available.
- The demo simulator now advances configurable soil and tank water balances, first-order temperature/humidity response, a single-degree-of-freedom structural response, and bounded robot point kinematics with battery energy accounting. Unsupported or invalid model parameters fail explicitly; each simulated snapshot identifies its model and generic/un-calibrated assumptions.
- The seeded demo estate now includes explicit simulated solar generation, battery state-of-charge, and estate-load telemetry. The estate overview reads storage facilities from the tenant-scoped storage API instead of misreporting them as missing digital-twin devices.
- Estate configuration now persists spatial positions and state as JSON objects (not JSON-encoded strings), preserving the API/3D coordinate shape.
- Final Phase 3 regression validation: `python -m pytest tests/test_canonical_sensor_ingestion.py tests/test_day66_robotics_tasks.py tests/test_day72_automation.py tests/test_day74_digital_twin.py tests/test_day85_validation.py tests/test_roles_and_zone_geometry.py tests/test_estate_seed.py tests/test_digital_twin_history.py tests/test_robotics.py tests/test_domain_simulation.py tests/test_robotics_grpc_simulation.py tests/test_robotics_integration_status.py -q -p no:cacheprovider --disable-warnings` passed (69 tests).
- Final frontend validation: `npm run lint` and `npm run build` passed; the build reports existing non-blocking React hook dependency warnings in unrelated metric/weather cards.
- Live backend validation: login, digital-twin devices, storage facilities, zones, and twin health returned HTTP 200; health remained connected across repeated requests, with 3 demo energy assets and 2 registered storage facilities.
- The requested scope is a 3-acre estate spanning soil/irrigation, climate, energy, robotics, water, and structures. A site location, surveyed as-built geometry, soil characterization, measured actuator rates, and reference telemetry have not been provided, so model calibration remains outstanding.
- The user accepted generic demo climate/soil/irrigation defaults and inferred planning geometry for now. Phase 3's software demo simulation is complete against its generic acceptance scenarios, not field calibration or hardware validation. The single-degree-of-freedom model is not a finite-element or structural safety analysis, and robot scene units are not surveyed meters. Phase 5 adapters are contract-tested with fake clients, not field-tested; calibrate models and validate adapters against surveyed measurements and purchased hardware before operational use.
- Resource follow-up: existing default-tenant setup now idempotently seeds generic water collection/purification/irrigation/recycling, waste collection/compost/recycling, and storage facilities/lots when those domains are empty. Each dashboard has an explicit one-day advance action; water quality stays real-reading-only, waste simulation updates its demo streams/processes and writes sorting/processing history, and storage simulation only consumes `SIM-DEMO-...` lots. No simulation runs automatically.
- Robotics follow-up: the robot page reports the local fleet gRPC, configured Vryndara gRPC health, and ROS 2 runtime/control boundary. A navigation bug that treated the zone ID as a robot ID was fixed. The ROS 2 runtime is not installed here, and hardware control remains disabled pending the ordered robot model, ROS distribution, topic/action mapping, coordinate frame, and safety limits.
- Resource/robotics regressions: `python -m pytest tests/test_domain_simulation.py tests/test_robotics_grpc_simulation.py tests/test_robotics_integration_status.py tests/test_vryndara.py tests/test_day66_water.py tests/test_day67_waste.py tests/test_day64_storage_and_safety.py -q -p no:cacheprovider` passed (28 tests; 425 warnings). Targeted frontend lint passed for water, waste, storage, and robot management pages.

### Deliverable
A live digital twin that behaves like an operational, simulated estate instead of a disconnected mock UI.

---

## Phase 4 — Audit, governance, and traceability

### Checklist
- [x] Review all CRUD actions and capture audit records
- [x] Log device creation, deletion, move, activation, and control changes
- [x] Log zone changes and ownership modifications
- [x] Log user actions, role changes, and admin actions
- [x] Log automation triggers and alert actions
- [x] Ensure audit event timestamp, actor, entity, and action are stored consistently
- [x] Provide evidence pages and compliance view from the same canonical log set
- [x] Verify no asset action is silent or untracked

### Deliverable
A trustworthy estate system where every meaningful action is auditable.

### Progress
- Added a consistent structured audit envelope for actor, tenant, action, entity, outcome, timestamp, and details; local persistence remains authoritative when blockchain submission is unavailable.
- Audited device, zone, user/role, alert, automation/actuator, safety, water/waste/storage, spatial/crop, estate-layout, tenant, scene, IoT sensor control, orchestration, HVAC, communications, and telemetry-playback mutations.
- Secured legacy scene APIs with authentication and tenant scoping; global simulation controls require superadmin access. IoT sensor registration and controls now require the corresponding device permissions.
- Tightened tenant administration and succession operations to prevent cross-tenant mutation; scene and spatial APIs now scope assets to the authenticated tenant.
- The evidence review and compliance pages consume the canonical audit set and distinguish local-only, verified, unmatched, and unavailable blockchain evidence.
- Routine weather observation samples and ordinary telemetry ticks are intentionally not emitted as individual audit records to avoid high-volume audit noise; they remain in their telemetry/history stores. State transitions and operator-initiated controls are audited.
- Focused regression validation passed: 107 tests across audit, compliance, device, spatial, estate, sensor, playback, succession, orchestration, tenant, and robotics flows. Python compile checks and `git diff --check` passed.
- Phase 4 is complete for the software environment. Phase 5 software adapter contracts and common API routing are complete; physical hardware commissioning is not.

---

## Phase 5 — Hardware-ready adapter abstraction

### Checklist
- [x] Define a device abstraction interface for all assets
- [x] Create a common persisted device model with id, name, kind, zone, status, adapter selection, state, and command/telemetry contracts
- [x] Separate business logic from transport protocol
- [x] Define injectable adapter implementations for MQTT, REST, serial, and gRPC
- [x] Standardize device command and telemetry formats with tenant/zone identity validation
- [x] Map every digital-twin device to a simulation-default or explicitly selected hardware adapter contract
- [x] Keep simulation and hardware behind the same command API; do not update physical state from an unconfirmed hardware command
- [x] Validate adapter plug-in behavior through fake transport clients and the common API; no physical device was available for field validation

### Deliverable
A platform where the same software layer can control simulated devices or real hardware via adapters.

### Status
Phase 5's common device/command/telemetry abstractions and injectable adapter contracts are implemented and covered by software tests; this does not mean every protocol or physical device is connected. The Arduino Mega LED adapter is opt-in through gateway configuration and is restricted to one loopback-only pilot identity. The owner reports the physical command/acknowledgment and USB reconnect/port-change tests working. Additional sensors, robot hardware, protocol services, and safety commissioning remain open in Phases 7–10.

---

## Phase 6 — 3D scene editor, visibility, and operational control

**Priority: highest.** The existing 3D scene is an initial viewer/editor
foundation, not a finished spatial authoring or complete estate-control
workspace. Work here first, preserving tenant scope, permissions, surveyed vs.
inferred geometry, audit events, and the existing source of truth.

### Scene navigation and visibility
- [x] Add a clear scene toolbar with select, pan/orbit, zoom, reset view, home,
  top/front/side/isometric presets, and a visible camera/view indicator.
- [x] Add search and filters for zone, asset type, status, connectivity,
  control mode, adapter, active alerts, and surveyed/inferred position.
- [x] Add a scene layer/visibility panel for zones, buildings, labels, sensors,
  actuators, robots, camera feeds, routes, alert overlays, and telemetry
  overlays; unavailable camera/route sources are visibly disabled.
- [x] Add a text-labeled status legend and source summary for normal, warning,
  critical, offline, simulated, configured physical-adapter, and unknown
  states. State precedence is explicit and colors are paired with labels.
- [x] Make zone labels readable at estate scale with selected-zone default,
  optional all-zone density, hide/show, and selection highlighting; keep
  unknown or stale readings explicit.
- [x] Show scene load/error/empty states, data freshness, configured source
  counts, current tenant, coordinate units, and surveyed/inferred provenance.
- [ ] Test scene interaction and usability on common desktop resolutions and
  keyboard navigation; document touch/tablet limitations if not supported.

### Real scene editing and spatial data
- [x] Implement an explicit edit-mode boundary from read-only operation;
  creation, edit, deletion, and transform affordances are hidden until an
  authorized user enables edit mode.
- [x] Support placing a new scene asset directly in the viewport before save;
  show an inferred placement preview and coordinates before the create request.
- [x] Add selected-object move/rotate gizmos, zone resize controls, constrained
  axis handles, and configurable grid/rotation snapping. Drag release stages a
  draft; explicit Save edits, Discard, Undo, and Redo actions control persistence.
  Numeric inspector editing remains available for exact values.
- [x] Add undo/redo for unsaved scene transforms and viewport placement drafts.
- [x] Add numeric position/orientation/dimension inputs and persist zone/device
  position, orientation (degrees), units, coordinate frame, and
  surveyed/inferred provenance through tenant-scoped APIs. Migration
  `0016_spatial_orientation` and `0017_device_position_provenance` add durable
  fields; inferred placements remain explicitly labeled and no coordinate
  conversion is implied.
- [x] Validate tenant-scoped permissions, finite/bounded values, surveyed
  coordinate-frame requirements, and audit edits through the backend APIs.
- [x] Resolve concurrent edits without overwriting newer saved state using
  expected update timestamps, conditional writes, and HTTP 409 conflict handling.
- [x] Support create/edit/delete for zones and assets from the scene with
  permission gating, delete confirmation, API error display, no success-shaped
  optimistic state, and links to owning operational pages.
- [ ] Add configurable, metadata-backed model selection and asset orientation;
  handle missing models with a clear fallback and never break the scene.
- [ ] Provide selection/inspector details for identity, zone, live/simulated/
  physical source, adapter/protocol, state, health, freshness, recent telemetry,
  alert/safety status, command history, and audit links.
- [ ] Add scene bookmarks/views and persist them only if tenant/user ownership
  and schema are explicit; avoid browser-only configuration that appears saved.

### Scene operations and controls
- [ ] Add explicit simulation-vs-live indication and a user-controlled
  simulation overlay; simulated state must not overwrite or masquerade as
  physical observations.
- [x] Add selected-device controls only for supported commands and authorized
  users, with pending/accepted/confirmed/failed state and acknowledgment
  timestamps; do not present a requested state as a confirmed physical state.
- [ ] Surface interlocks, safety-rule blocks, stale/offline state, manual/
  automation/AI authority, and the reason a command is unavailable.
- [x] Add scoped scene actions for real underlying APIs, including opening the
  owning operational page; do not add cosmetic buttons or duplicate business
  logic in the frontend.
- [ ] Overlay current telemetry, historical trails, sensor coverage, robot
  route/tasks, zone bounds, and alerts only when backed by data; include time
  range, units, legend, and source.
- [x] Connect camera/media controls only to camera/media devices; display an
  unavailable state when no camera source exists and expose media retention and
  permission-gated upload behavior.
- [ ] Validate render performance with a documented representative estate;
  use instancing/LOD or incremental loading only when measurements justify it.
- [ ] Add component and browser-level regression tests for selection, edit,
  save/cancel, tenant scoping, permissions, scene filters, and loading/errors.

### Exit criteria
- [ ] A permitted user can create/select/move/rotate/resize a supported object,
  see exact coordinate units/provenance, save it, reload, and observe the same
  persisted layout.
- [ ] Every visible layer and filter has a defined effect; no invisible
  selected controls or misleading physical/live indicators.
- [ ] A selected device's information and controls agree with backend state,
  permission results, and acknowledged command/audit history.
- [ ] Focused frontend build/lint/tests and role/tenant API tests pass; no
  unsaved or failed edit is reported as saved.

### Phase 6 progress — 2026-10-30
- [x] Added camera presets and explicit select/pan/orbit interaction modes,
  bounded zoom controls, and a reset-to-home action.
- [x] Added live scene search and filters for zone, asset type, state,
  connectivity, adapter, control mode, active sensor alerts, and inferred vs.
  reported spatial placement. Filters now affect both the rendered scene and
  the live-asset list, with a reset action and a visible zone/asset count.
- [x] Added visibility toggles for zone footprints, labels, robots, sensors,
  actuators, the coordinate grid, illustrative proximity guides, alert/status
  overlays, and backed current sensor readings. Camera feeds and measured
  routes are visibly unavailable until configured sources exist. Sensor alert
  labels and per-asset stale/unknown statuses keep source state explicit.
- [x] Tightened inferred zone spacing and footprint defaults so planning
  geometry stays legible at the estate-wide camera view without claiming
  surveyed dimensions.
- [x] Added tenant-scoped persisted zone/device position and orientation,
  spatial provenance, coordinate-frame and unit fields, numeric inspector
  editing, and scene rotation rendering. Added retry-safe Alembic migration
  `0016_spatial_orientation` plus focused API/migration regressions.
- [x] Added selected-object Move/Rotate transform gizmos, zone resizing,
  configurable translation snapping, and 15-degree rotation snapping.
  Transform changes are permission-gated and staged until an explicit save.
- [x] Persisted an explicit device-position-configured flag so a deliberate
  origin position remains distinct from an unset/default position; migration
  `0017_device_position_provenance` covers existing databases.
- [x] Added a scene condition legend and per-tenant configured-source counts;
  the inspector identifies adapter/source while clearly separating adapter
  configuration from evidence of connectivity or live telemetry.
- [x] Promoted the 3D viewport ahead of filters and the inspector at full
  content width; fitted camera framing to visible zone dimensions and device
  positions, kept the ground/grid centered, and added fit-all, focus-selected,
  orientation-gizmo, and keyboard view controls. The canvas reports when
  WebGL is unavailable instead of leaving a blank viewport.
- [x] Added compact selected-zone label density by default, with an explicit
  all-zone option and a global labels toggle to reduce overlap while preserving
  selection highlighting and provenance.
- [x] Added an explicit permission-gated scene edit mode; spatial gizmos,
  create controls, and asset/zone edit-delete actions are unavailable in
  read-only mode. Exiting edit mode asks before discarding an open unsaved
  scene form.
- [x] Browser-checked the 3D viewport with a 1195 × 478 canvas: the complete
  estate loads, camera presets and keyboard preset shortcuts respond, Fit
  scene restores the whole-estate view, and Focus selection is enabled after
  selecting an asset. Edit mode reveals and hides authoring controls as
  expected. This is a focused smoke check, not desktop-resolution or keyboard
  acceptance coverage.
- [x] Added direct viewport placement previews for device and zone creation;
  inferred coordinates remain editable before submit and Undo restores the
  previous placement draft.
- [x] Added shared draft Undo/Redo, explicit save/discard actions, and
  timestamp-based compare-and-swap conflict handling for spatial writes.
- [x] Added explicit commits to digital-twin device create/update/delete/control
  operations so successful responses persist beyond the request session.
- [x] Focused backend tests pass for tenant-scoped zone edits, stale zone/device
  writes, and device CRUD. Scene ESLint passes. A final production-build rerun
  was inconclusive because the persistent Next dev process continued writing to
  the shared `.next` directory (ENOENT); the live page was restored and smoke
  checked instead of stopping the user's server.
- [x] Browser-smoke-checked the live scene on port 3000 with 14 zones and 26
  assets: viewport placement created an inferred draft; Undo/Redo restored it;
  Cancel removed it without submitting. Orientation-gizmo interaction no longer
  triggers the controls error after registering OrbitControls as the default.
- [x] Added a tenant-scoped scene safety-status endpoint and enforced the same
  emergency-stop/rule check before digital-twin commands are dispatched. The
  scene fails closed when safety status cannot be verified and shows the latest
  recorded command acknowledgment in the selected-asset inspector.
- [ ] Remaining model/inspector/control requirements, desktop/accessibility
  acceptance, persistent scene bookmarks, and automated browser tests remain
  open; Phase 6 is not complete.

---

## Phase 7 — Canonical protocols, protobuf/gRPC, and service connectivity

**Dependency:** Phase 6 establishes how operators inspect and edit assets;
this phase makes the underlying service and edge contracts consistent and
observable. Existing `.proto` contracts, generated clients, gRPC connectors,
simulated services, and common device adapters are starting points, not proof
that all services or physical endpoints are connected.

- [ ] Inventory each `.proto`, generated stub, gRPC client/server, REST route,
  adapter, and actual runtime entry point; label each as production,
  simulation/demo, test-only, or unconnected.
- [ ] Choose and document a canonical device identity, tenant/zone context,
  timestamp/clock convention, units, status/freshness, telemetry envelope,
  command envelope, acknowledgment, error, and correlation/trace ID.
- [ ] Version protobuf schemas and establish reproducible stub generation;
  check generated code in or regenerate consistently from source `.proto`
  files. Add compatibility tests for schema evolution and unknown fields.
- [ ] Align sensor, robot, Vryndara, and digital-twin message fields with the
  canonical schema; define conversions in adapters, not duplicated UI logic.
- [ ] Run gRPC service processes through documented entry points with health
  checks, startup/shutdown, timeouts, cancellation, bounded retry/backoff, and
  clear disconnected status. Never fall back to fabricated success.
- [ ] Add service identity and authentication; use TLS/mTLS and managed
  credentials for networked deployments. Keep insecure loopback-only demos
  explicitly local.
- [ ] Define protocol responsibilities: serial for local microcontroller
  links; MQTT for suitable event/telemetry brokers; Modbus for supported
  industrial equipment; REST for explicit HTTP integrations; gRPC/protobuf
  for service/gateway RPC and streaming. Select per device capability and
  verified adapter, not by branding.
- [ ] Implement and test real gateway/adapter drivers only for protocols and
  hardware on hand; include discovery, reconnect, heartbeat, bounded queues,
  deduplication, stale-data handling, and acknowledged results where supported.
- [ ] Route inbound telemetry through validation, tenant/device authorization,
  canonical persistence/history, alert evaluation, and realtime publication.
- [ ] Route commands through authorization, safety checks, selected adapter,
  acknowledgment tracking, state reconciliation, audit, and user-visible
  status.
- [ ] Make Vryndara gRPC connectivity explicit in health/status and evidence;
  show demo, disconnected, configured, or verified states distinctly.
- [ ] Add integration tests with local gRPC servers/fakes for telemetry
  streams, RPC failure, deadlines, service restart, malformed messages, and
  unauthorized tenant/device access.

### Exit criteria
- [ ] Every supported live path has a contract, owner, health indicator,
  authenticated identity, timeout/error behavior, and focused integration test.
- [ ] No demo or fallback service is reported as a live sensor, physical robot,
  successful command, or trained model.

---

## Phase 8 — Rules, safe control, Vryndara AI, and learning governance

**Dependency:** consumes canonical and freshness-aware Phase 7 data. AI is
advisory until safety, traceability, and explicit authorization are proven.

### Deterministic rules and safety
- [ ] Define persisted, tenant-scoped rule schemas: event/source, condition,
  comparison, threshold/window/hysteresis, action, enabled state, owner,
  version, cooldown, and effective time.
- [ ] Evaluate rules deterministically on canonical telemetry/state
  transitions; deduplicate events and prevent loops, repeat firing, and
  stale/offline sources from triggering actions.
- [ ] Add rule simulation/dry-run and explain output showing the input sample,
  evaluated condition, threshold, decision, and proposed action.
- [ ] Apply a shared safety/interlock layer to manual, scheduled, automated,
  and AI-originated commands: role/tenant scope, device online/freshness,
  command allowlist, operating bounds, rate limits, emergency stop, and
  fail-safe state.
- [ ] Require explicit operator confirmation for uncommissioned or
  high-consequence actions. Keep the pilot LED command allowlist separate
  from future relays, pumps, gates, or motors.
- [ ] Record rule version, input references, decision, block reason, command
  ID, acknowledgment, actor/system identity, and outcome in audit history.

### Vryndara recommendations and AI
- [ ] Map each existing Vryndara/orchestrator/prediction capability to a
  verified input dataset, output schema, service/protobuf method, endpoint,
  model/version, operational status, and test; mark unavailable dependencies.
- [ ] Connect recommendations to canonical twin telemetry/history with
  explicit units, data windows, provenance, missing-data warnings, confidence,
  and model limitations.
- [ ] Display recommendations in the AI UI and relevant scene/asset inspector
  with evidence, expected effect, uncertainty, timestamp, model version, and
  accept/reject/defer workflow.
- [ ] Separate prediction/recommendation from command execution; require a
  human approval or explicitly configured, bounded automation policy before
  any AI proposal reaches a device.
- [ ] Keep AI actions inside the same authorization, rule, safety, adapter,
  acknowledgement, and audit pipeline as manual commands; fail closed when
  the AI service or required evidence is unavailable.

### Learning and evaluation
- [ ] Define what "learning" means for each feature: model training,
  calibration, feedback capture, or online adaptation; do not imply a model
  learns from chat or telemetry without an implemented data pipeline.
- [ ] Capture operator outcomes and labeled observations with consent,
  tenant isolation, retention, provenance, and correction/deletion policy.
- [ ] Establish offline training/evaluation datasets, baseline metrics,
  validation splits, acceptance thresholds, model registry/versioning,
  rollback, drift monitoring, and reproducible evaluation.
- [ ] Prohibit uncontrolled online model updates and autonomous high-impact
  actions; require reviewed model promotion and an emergency disable switch.
- [ ] Test missing/out-of-range/stale inputs, uncertain predictions, failed
  Vryndara service, conflicting rules, denied permission, and interlock
  activation.

### Exit criteria
- [ ] A recommendation is reproducible from recorded evidence and never
  bypasses deterministic permissions or safety controls.
- [ ] Rules can be simulated, versioned, audited, disabled, and tested without
  connecting physical outputs.
- [ ] No claim of autonomous learning is made until measured model/data
  acceptance criteria pass.

---

## Phase 9 — Integrated simulation and system verification

**Dependency:** validates the complete software flow before expanding physical
commissioning. Demo assumptions remain labeled and must not be called
field-calibrated.

### Existing local-development foundations
- [x] Add a Windows `start_aegis.bat` workflow with separate service windows,
  backend migration invocation, optional gateway startup, and individual
  service launchers for troubleshooting.
- [x] Add Alembic to the backend dependency list and make migration
  `0015_device_adapter_type` tolerate an already-present adapter column;
  this was needed because the local SQLite schema had the column while its
  recorded Alembic revision was still `0014`.
- [x] Update the local Arduino gateway to reconnect after serial loss and
  identify a single Mega when Windows assigns a different COM port; focused
  reconnect and adapter tests pass.
- [ ] Verify a complete fresh `start_aegis.bat` run from a clean terminal
  through blockchain, migrations, backend, frontend, and optional gateway;
  distinguish Hardhat's temporary chain from a persistent Anvil setup.

- [ ] Define repeatable scenarios for estate startup, normal telemetry,
  threshold/alert, rule evaluation, recommendation, approved action, denied
  action, adapter acknowledgment, audit evidence, and recovery.
- [ ] Verify simulated and physical identity/state separation throughout
  APIs, 3D scene, analytics, alerts, and audit.
- [ ] Verify sensor → canonical ingestion → durable history → realtime scene
  and dashboard → alert/rule → optional approved command → acknowledgment →
  audit end to end.
- [ ] Verify robot task lifecycle from request to gRPC/service response,
  persisted twin state, scene/inspector visibility, cancellation, timeout,
  and emergency-stop handling; simulation is clearly labeled.
- [ ] Test restart persistence for database, audit history, migration state,
  chain configuration, and service health; distinguish Hardhat ephemeral
  history from persistent-chain operation.
- [ ] Exercise service/USB/network outages, reconnect, duplicate messages,
  delayed acknowledgments, invalid data, stale telemetry, and partial
  failure; confirm no false success or unsafe retry.
- [ ] Validate tenant/RBAC boundaries, secrets handling, upload/retention
  limits, migration from a representative existing database, and backup
  restore.
- [ ] Validate all active pages and core flows with focused automated tests
  and a browser walkthrough; keep failures and known gaps visible.
- [ ] Calibrate simulation only when surveyed geometry, site location,
  physical parameters, and reference telemetry exist; otherwise keep generic
  assumptions and uncertainty labeled.

### Exit criteria
- [ ] Measurable end-to-end tests pass for happy path, negative path,
  restart, permission denial, stale/offline state, and recovery.
- [ ] Audit/evidence distinguishes simulated, owner-reported physical, and
  independently verified outcomes.

---

## Phase 10 — Asset-by-asset hardware onboarding

**Must precede deployment.** Onboard only hardware the project actually has
or can safely validate. Each asset follows the same commissioning record;
never bulk-mark assets physical based on a template or simulation.

### Per-asset onboarding record
- [ ] Record manufacturer/model, unique physical ID, site/zone, interface,
  protocol, wiring/power needs, documented operating limits, supported
  telemetry/commands, safe state, firmware/adapter version, and evidence owner.
- [ ] Verify the correct driver/protobuf/adapter and local gateway; identify
  hardware by stable identity rather than an assumed USB port.
- [ ] Bench-test power and wiring safely, then validate sensor units/range or
  actuator command/acknowledgment and unsupported-command rejection.
- [ ] Register a distinct physical device in the tenant-scoped twin, associate
  it with surveyed location where known, and preserve simulator records as
  simulated.
- [ ] Verify telemetry freshness/history/alerts or command authorization,
  interlocks, acknowledgment, audit, offline behavior, reconnect, and safe
  output behavior for that specific asset.
- [ ] Record dated observed results and mark owner-reported vs independently
  witnessed. Keep unresolved limitations and fail-safe gaps visible.

### Hardware sequence by asset category (after the software gates)
1. **Current Arduino Mega onboard LED:** retain as the low-voltage command
   pilot. On 2026-10-26, the owner reported command/acknowledgment,
   unplug/reconnect, and operation after plugging into a different USB port
   working. Complete audit, disconnect/retry, and safe-state evidence; it is
   not a sensor and does not prove general Arduino support.
2. **Sensors:** onboard one affordable sensor at a time (for example soil
   moisture or temperature/humidity), document calibration and units, and
   verify real telemetry through the canonical ingestion path before using it
   for rules or AI.
3. **Low-voltage actuators:** only after bench tests, correctly rated driver
   hardware, isolation/protection, and hardware-specific interlocks; never
   connect a 9 V battery, mains load, pump, motor, or relay directly to a
   microcontroller GPIO.
4. **Water and waste equipment:** onboard level/flow sensors before pumps,
   valves, compactors, or conveyors; validate mechanical limits, fail-safe
   state, local emergency stop, and commissioning with the equipment owner.
5. **Robots:** select and document the exact robot/controller/ROS 2
   distribution, coordinate frame, topics/actions, obstacle and speed limits,
   emergency stop, and recovery procedure before enabling gRPC-to-robot
   commands. Verify status/telemetry before motion.
6. **Security, camera, and access equipment:** complete privacy, retention,
   access-control, physical safety, audit, and local fail-safe reviews before
   installation or control.
7. **Gateways and multiple locations:** use a separately identified local
   gateway per site; specify managed identities, authenticated encrypted
   gateway-to-backend communication, network segmentation, update strategy,
   monitoring, and outage behavior. Do not expose the current loopback-only
   Arduino pilot to a LAN/WAN.

### Exit criteria
- [ ] Every commissioned asset has its own completed record and tested
  telemetry/command/safety path appropriate to its capabilities.
- [ ] Unavailable sensors, robots, camera feeds, and physical outputs remain
  explicitly unavailable rather than being represented by simulated values.

---

## Phase 11 — Deployment and final acceptance (last)

**Do not start production/estate deployment until Phases 6–10 exit criteria
are met for the features and devices in the deployment scope.**

- [ ] Choose deployment topology and service ownership; document supported
  OS/runtime versions, local vs. remote gateways, network dependencies, and
  recovery responsibilities.
- [ ] Provision secrets, TLS/service identities, least-privilege users,
  firewall rules, database/media storage, backups, and retention before
  exposing any service beyond loopback.
- [ ] Create a reproducible installation/update/rollback procedure with
  migrations, health checks, logs, and versioned firmware/protobuf/client
  artifacts.
- [ ] Validate backup restore and disaster recovery, persistent blockchain
  configuration if used, database migration from the supported baseline,
  monitoring/alerts, and data-retention jobs.
- [ ] Run production build, targeted and full tests, dependency/security
  checks, browser acceptance, access-control review, and all deployment
  runbooks against a clean environment.
- [ ] Commission each in-scope physical asset on site using Phase 10 records;
  obtain operator acceptance and document limitations before enabling
  automation.
- [ ] Sign off operator training, manual override, emergency stop, offline
  procedure, change ownership, maintenance plan, and rollback.
- [ ] Publish final architecture, inventory, verified capability matrix,
  deployment configuration, known gaps, and incident/recovery instructions.

### Final acceptance
- [ ] The scene, twin, telemetry, rules, AI recommendations, device commands,
  audit, and evidence present consistent and traceable state.
- [ ] Every claim is labeled as simulated, configured, owner-reported, or
  independently verified with evidence.
- [ ] Only individually commissioned hardware is enabled for real control.
- [ ] Deployment scope passes its documented operational and safety
  acceptance criteria.
