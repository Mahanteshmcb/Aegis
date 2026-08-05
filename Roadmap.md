**Days 1-70 (COMPLETED):** Phase 1 software finished; estate dashboard and core API delivery are complete.
**Days 71-110 (PHASE 2 ACTIVE):** Begin joint hardware/software execution: IoT sensor deployment, robotic fleet integration, and estate-wide system commissioning.

---

# Aegis Biosphere Protocol: Complete Implementation Roadmap

## Overview
**Vision:** Engineer and deploy highly secure, offline, self-sustaining "Private Biospheres" for UHNIs and the Defense sector. This system utilizes a multi-tiered robotic fleet and a dense IoT sensor mesh, all orchestrated locally via the high-performance **Vryndara gRPC kernel platform**, to autonomously manage 3,000+ unique biological crops within a decentralized, privacy-first network.

**Implementation Strategy:** 
- **This Semester (Phase 1):** Complete all software development (Days 1-70) - gRPC communication, ML models, robotic orchestration, spatial mapping
- **Next Semester (Phase 2):** Complete all hardware development (Days 71-150) - IoT sensors, robotic fleet, 3-acre prototype, final integration


**Key Technologies:** FastAPI, gRPC, TensorFlow/PyTorch, PostgreSQL, React/Next.js, Vryndara kernel, robotic fleet coordination, 3D spatial mapping

---

# Phase 1: Biosphere Protocol Software Development (Days 1-70)
*This Semester - Core Software Development*

| Day | Task | Details |
|-----|------|---------|
| 1   | ✅ Project vision, objectives, and architecture planning | - Define Aegis as Digital Twin/IoT Audit Platform for industrial compliance<br>- Identify key objectives: multi-tenant zones, blockchain audit trails, AI-driven compliance<br>- Map user personas: facility managers, auditors, compliance officers<br>- Create project charter with success metrics and KPIs |
| 2   | ✅ GitHub repo, initial docs, folder structure, .gitignore, license | - Initialize GitHub repository with MIT license<br>- Set up folder structure: backend/, frontend/, blockchain/, docs/, ai/<br>- Create README.md with project overview and setup instructions<br>- Configure .gitignore for Python, Node.js, and blockchain artifacts |
| 3   | ✅ Research digital twin frameworks, IEEE paper, presentation | - Study existing digital twin frameworks (Azure DT, AWS IoT TwinMaker)<br>- Review IEEE papers on IoT security and compliance automation<br>- Create comparative analysis document<br>- Prepare internal presentation on chosen approach |
| 4   | ✅ Vryndara AI kernel architecture study, integration plan | - Analyze Vryndara gRPC API and available agents (Researcher, Brain, etc.)<br>- Design VryndaraConnector class for async communication<br>- Plan integration points: compliance research, AI analysis, predictive maintenance<br>- Document gRPC connection setup (localhost:50051) |
| 5   | ✅ System architecture (5 layers), data flow diagrams | - Design 5-layer architecture: Presentation, Application, Domain, Infrastructure, Hardware<br>- Create data flow diagrams for sensor data → AI processing → actuator control<br>- Define zone-based partitioning for scalability<br>- Document API boundaries and service contracts |
| 6   | ✅ Dev workflow, code style, testing standards | - Set up development environment with Python 3.11, Node.js 18, Hardhat<br>- Configure pre-commit hooks, black formatter, ESLint<br>- Establish testing standards: pytest for backend, Jest for frontend<br>- Create contribution guidelines and code review process |
| 7   | ✅ Week 1 review, planning for backend | - Review deliverables Days 1-6, identify gaps<br>- Plan backend development: FastAPI setup, database models<br>- Estimate timelines and resource needs<br>- Update roadmap with any adjustments |
| 8   | ✅ FastAPI backend scaffolding, CORS, error handling, routers | - Initialize FastAPI application with main.py<br>- Configure CORS for frontend integration<br>- Implement global error handlers and custom exceptions<br>- Set up modular router structure (auth, tenants, zones, devices) |
| 9   | ✅ PostgreSQL/SQLite setup, SQLAlchemy models, Alembic migrations | - Choose SQLite for development, PostgreSQL for production<br>- Define SQLAlchemy models: User, Tenant, Zone, Asset, SensorData<br>- Set up Alembic for database migrations<br>- Create initial migration scripts |
| 10  | ✅ User & tenant models, JWT auth, RBAC, middleware | - Implement User and Tenant models with relationships<br>- Set up JWT authentication with refresh tokens<br>- Create RBAC system with roles (admin, manager, auditor, operator)<br>- Add authentication middleware for protected endpoints |
| 11  | ✅ Health check endpoint, Vryndara & blockchain connectivity | - Create /health endpoint with dependency checks<br>- Implement VryndaraConnector basic connectivity test<br>- Add blockchain network health monitoring<br>- Set up connection retry logic and error reporting |
| 12  | ✅ Pytest setup, unit/integration tests, coverage | - Configure pytest with fixtures and async support<br>- Write unit tests for models, auth, and core services<br>- Create integration tests for API endpoints<br>- Set up coverage reporting (>80% target) |
| 13  | ✅ API docs, endpoint cleanup, Postman collection | - Generate OpenAPI/Swagger documentation<br>- Clean up endpoint responses and error codes<br>- Create Postman collection with authentication flows<br>- Document API versioning strategy |
| 14  | ✅ Week 2 review, backend test pass, planning | - Review backend completion, run full test suite<br>- Identify any security or performance issues<br>- Plan frontend development integration<br>- Update integration status with Vryndara team |
| 15  | ✅ Next.js frontend scaffolding, TypeScript config | - Initialize Next.js 14 with TypeScript<br>- Configure Tailwind CSS and PostCSS<br>- Set up ESLint, Prettier, and Husky<br>- Create basic folder structure: components/, pages/, hooks/, utils/ |
| 16  | ✅ Tailwind CSS, reusable components, base layout | - Implement design system with Tailwind utilities<br>- Create reusable components: Button, Input, Card, Modal<br>- Build base layout with navigation and sidebar<br>- Set up responsive design patterns |
| 17  | ✅ Authentication UI: login, signup, password reset | - Create login/signup forms with validation<br>- Implement password reset flow with email<br>- Add form error handling and loading states<br>- Integrate with backend JWT endpoints |
| 18  | ✅ Frontend-backend integration, JWT storage, API abstraction | - Set up Axios instance with interceptors for JWT<br>- Implement secure token storage (httpOnly cookies)<br>- Create API abstraction layer with error handling<br>- Test authentication flow end-to-end |
| 19  | ✅ RBAC UI, role-based menus, endpoint protection | - Implement role-based navigation menus<br>- Create user management interface for admins<br>- Add frontend route protection based on roles<br>- Test RBAC scenarios with different user types |
| 20  | ✅ Frontend documentation, storybook, integration guide | - Set up Storybook for component documentation<br>- Create integration guide for frontend-backend<br>- Document component API and usage examples<br>- Add automated visual regression testing |
| 21  | ✅ Week 3 review, frontend test pass, planning | - Review frontend completion and integration<br>- Run end-to-end tests with Cypress<br>- Plan blockchain integration and hardware stubs<br>- Coordinate with backend team for API finalization |
| 22  | ✅ Hardhat blockchain scaffolding, network config | - Initialize Hardhat project with TypeScript<br>- Configure local network and test networks<br>- Set up contract deployment scripts<br>- Create basic test framework for contracts |
| 23  | ✅ Solidity contract for audit logs, event functions | - Design AuditLog contract with event emission<br>- Implement functions for logging device actions<br>- Add access control and validation<br>- Write comprehensive contract documentation |
| 24  | ✅ Local contract testing, deploy, verify flows | - Write unit tests for contract functions<br>- Set up local deployment and verification<br>- Create deployment scripts for different networks<br>- Test contract interactions and gas optimization |
| 25  | ✅ Backend-blockchain integration, Web3.py, event recording | - Integrate Web3.py for blockchain communication<br>- Implement event listening for audit logs<br>- Create database models for blockchain data<br>- Test full audit trail from device to blockchain |
| 26  | ✅ Blockchain docs, ABI, integration guide | - Generate contract ABI and deployment artifacts<br>- Create integration guide for backend-blockchain<br>- Document security considerations and best practices<br>- Set up monitoring for blockchain transactions |
| 27  | ✅ Code cleanup, refactoring, error handling | - Refactor code for consistency and maintainability<br>- Improve error handling across all layers<br>- Optimize database queries and API responses<br>- Add comprehensive logging and monitoring |
| 28  | ✅ Month 1 review, milestone checkpoint | - Review all Phase 1 Week 1-4 deliverables<br>- Conduct security audit and performance testing<br>- Prepare demo for stakeholders<br>- Plan Phase 1 completion and Phase 2 transition |
| 29  | ✅ Multi-tenant schema, SQLAlchemy filters | - Implement tenant isolation in database schema<br>- Add SQLAlchemy filters for tenant-scoped queries<br>- Create tenant context middleware<br>- Test tenant data separation |
| 30  | ✅ Tenant CRUD endpoints, management UI | - Build REST endpoints for tenant management<br>- Create admin UI for tenant creation/configuration<br>- Implement tenant switching for super admins<br>- Add tenant-specific settings storage |
| 31  | ✅ Extend Vryndara connector for gRPC | - Add gRPC client support to existing VryndaraConnector class<br>- Define Protocol Buffer schemas for robotic commands and sensor data<br>- Implement secure, air-gapped communication channels |
| 32  | ✅ Robotics fleet API and backend wiring | - Add RoboticFleetService gRPC connector and fallback support<br>- Expose robotics control endpoints under /api/v1/robotics<br>- Add test coverage for robotics routing and fallback behavior |
| 32  | ✅ Design robotic fleet communication contracts | - Create protobuf definitions for Aegis Rover, Agri-Swarm Micro-Bots, and Canopy Drones<br>- Define command/response patterns for navigation, harvesting, and maintenance<br>- Implement authentication and authorization for robotic units |
| 33  | ✅ Implement 3D spatial mapping models | - Extend backend models for 3D crop positioning and zone management<br>- Add spatial algorithms for vertical crop layers (ground, mid-canopy, upper)<br>- Create database schemas for 3,000+ biological species tracking |
| 34  | ✅ Backend integration for spatial data | - Add new routers for spatial queries and crop management<br>- Implement CRUD operations for biological species database<br>- Test spatial data processing with mock coordinates |
| 35  | ✅ Vryndara kernel orchestration engine | - Design the "Succession & Orchestration" engine logic<br>- Implement decision-making algorithms for crop planting and maintenance<br>- Create event-driven triggers for robotic actions |
| 36  | ✅ gRPC service definitions for IoT sensors | - Define protobuf schemas for Sub-Surface Mycelial Probes, Acoustic Pest Monitors<br>- Implement real-time data streaming protocols<br>- Add sensor health monitoring and calibration endpoints |
| 37  | ✅ Integration testing for gRPC contracts | - Set up mock robotic clients and sensor simulators<br>- Test end-to-end communication flows<br>- Validate security and performance of gRPC channels |
| 38  | ✅ Acoustic pest recognition ML model | - Collect training data for insect acoustic signatures<br>- Implement ML pipeline for pest detection using PyTorch<br>- Integrate model with Vryndara kernel for real-time analysis |
| 39  | ✅ Soil health prediction models | - Develop ML models for N-P-K level prediction from mycelial sensor data<br>- Create predictive algorithms for soil rehabilitation with priority-based recommendations<br>- Add model training and validation pipelines with heuristic fallback mode |
| 40  | ✅ Visual crop health assessment | - Implement computer vision models for plant health monitoring from drone imagery<br>- Create heuristic and neural network inference modes for 6 health status classifications<br>- Integrate with orchestration engine for autonomous health-based decision making |
| 41  | ✅ Aegis backend extensions for agricultural data | - Extend sensor models to include specialized agricultural probes<br>- Add new endpoints for crop lifecycle management<br>- Implement data aggregation for biological metrics |
| 42  | ✅ Robotic fleet control interfaces | - Create backend APIs for robotic command dispatching<br>- Implement fleet coordination algorithms<br>- Add safety protocols and emergency stop mechanisms |
| 43  | ✅ Integration with blockchain audit | - Extend audit logging for robotic actions and biological transactions<br>- Implement traceability for seed movements and crop yields<br>- Add compliance reporting for agricultural operations |
| 44  | ✅ Performance optimization and testing | - Optimize gRPC communication for low latency<br>- Conduct load testing for concurrent robotic operations<br>- Validate ML model accuracy with test datasets |
| 45  | ✅ Succession planning algorithms | - Implement crop succession logic for syntropic agriculture<br>- Create algorithms for companion planting optimization<br>- Add seasonal planning and rotation schedules |
| 46  | ✅ Robotic task scheduling system | - Develop task queue management for robotic fleet<br>- Implement priority-based task assignment<br>- Add conflict resolution for overlapping operations |
| 47  | ✅ Real-time monitoring dashboard | - Create backend APIs for real-time system status<br>- Implement health monitoring for all robotic units<br>- Add alerting system for system anomalies |
| 48  | ✅ Emergency response protocols | - Design automated emergency response for system failures<br>- Implement backup power management and recovery procedures<br>- Add manual override capabilities for critical situations |
| 49  | ✅ Data synchronization and backup | - Implement offline data synchronization strategies<br>- Create backup procedures for biological databases<br>- Add data integrity verification mechanisms |
| 50  | ✅ User interface for system control | - Extend frontend for biosphere management<br>- Add control panels for robotic fleet operations<br>- Implement visualization for 3D crop mapping |
| 51  | ✅ End-to-end integration testing | - Conduct comprehensive system integration tests<br>- Validate all communication protocols and data flows<br>- Perform security audits and penetration testing<br>- Verified with `python -m pytest tests/test_grpc_integration.py --tb=no -q` |
| 52  | ✅ Predictive maintenance for robotics | - Implement ML models for robotic health prediction<br>- Add maintenance scheduling algorithms<br>- Create automated diagnostics and repair protocols |
| 53  | ✅ Energy management system | - Design power distribution for robotic fleet and sensors<br>- Implement energy optimization algorithms<br>- Add solar and backup power integration<br>- Verified with `scripts/run_energy_checks.py` (naive scheduler & balance) |
| 54  | ✅ Biological diversity optimization | - Implemented naive biodiversity optimizer and `/api/v1/biodiversity/optimize` endpoint<br> - Persisted energy charging policies to DB (`energy_policies` table) and wired frontend controls to use persisted policies |
| 55  | ✅ Weather integration and adaptation | - Integrate weather data sources for predictive planning<br>- Implement adaptive algorithms for weather events<br>- Add climate change adaptation strategies |
| 56  | ✅ Compliance and regulatory integration | - Implement agricultural compliance tracking with blockchain-backed audit requests<br>- Add regulatory reporting and certification status endpoints<br>- Create audit trails for organic certification requests |
| 57  | ✅ Live sensor telemetry weather/energy bridge | - Connect live sensor telemetry into local weather observations<br>- Update energy forecasts and charge scheduling using on-site sensor data<br>- Add dashboard telemetry widgets that ingest and surface environmental readings |
| 58  | ✅ Adaptive energy scheduling with weather signals | - Implement smart_adaptive_schedule() using weather forecasts<br>- Prioritize battery charging during high-solar windows<br>- Add load-shifting recommendations when battery is low |
| 59  | ✅ Software completion milestone | - Final integration testing of all software components (**E2E pipeline: 6 tests**)<br>- Performance benchmarking and optimization (**baseline metrics: 12 tests**)<br>- Security audit and compliance verification (**multi-tenant isolation: 14 tests**)<br>- **Result: 32/32 test cases PASS** |
| 60  | ✅ Phase 1 software delivery | - All software components complete and tested<br>- Backend: 30+ routers with full CRUD operations<br>- Frontend: 39 pages compiling with 0 errors<br>- Ready for hardware integration handoff |
| 61  | ✅ Complete Estate Dashboard Backend APIs | - Implemented `/api/v1/estate/status` returning aggregated system health<br>- Created `/api/v1/systems/{systemId}/data` for individual system telemetry<br>- Implemented mocked sensor data (realistic ranges for climate, energy, water, biosphere)<br>- Added `/api/v1/estate/timeline` for activity history with filtering<br>- **All 7/7 endpoints tested: 200 OK responses, proper error handling, Pydantic validation** |
| 62  | ✅ Real-Time WebSocket Streaming (Socket.IO) | - Implemented Socket.IO v5.9.0 server with dual emitter architecture<br>- Emits 'systemStatus:update' events every 5 seconds with aggregated system health<br>- Streams 'sensor:reading' events with realistic intervals (1-5 sec random)<br>- Supports concurrent client connections with proper cleanup on disconnect<br>- **Code complete and tested: standalone Socket.IO server validated (5 concurrent clients received events). Applied Windows SSL workaround; recommend adding `certifi` to `backend/requirements.txt` and keeping the SSL monkeypatch in `backend/main.py` for Windows dev environments.** |
| 63  | ✅ Complete Alert & Notification System | - Implemented `/api/v1/alerts` POST/GET/acknowledge/resolve endpoints<br>- Added alert types: robot_health, fleet_efficiency, safety_incident, system_error<br>- Created SystemAlert model with severity levels: low, medium, high, critical<br>- Implemented alert acknowledgment with tracking (acknowledged_by, acknowledged_at)<br>- **4/4 alert CRUD tests passing; alerts persist in database and isolated by tenant** |
| 64  | ✅ Finalize Admin User & Role Management | - Completed user PUT/DELETE endpoints and role assignment endpoint (`/api/v1/users/{id}/role`)<br>- Added tests for create/list/update/delete and self-demotion protection<br>- Permission matrix documented in `backend/day64_plan.md`<br>- Frontend admin panel integration pending (connect to `/admin/users`). |
| 65  | ✅ Predictive Maintenance Mock System | - Implement `/api/v1/maintenance/predictions` endpoint<br>- Return realistic failure risk scores (0-100) for major systems<br>- Add recommended actions and days-until-maintenance estimates<br>- Create database model for maintenance history<br>- Wire to frontend maintenance alerts |
| 66  | ✅ System Control Command Handlers | - Implement `/api/v1/systems/{systemId}/control` POST endpoint<br>- Support basic commands: power on/off, reset, manual override<br>- Validate command permissions per user role<br>- Add command logging to audit trail<br>- Return immediate acknowledgment + eventual status updates |
| 67  | ✅ Complete 3D Dashboard Visualization | - Ensure real-time data feeds into 3D estate renderer<br>- Add color-coded health indicators (green/yellow/red)<br>- Implement interactive system selection on 3D model<br>- Add drill-down from 3D view to detailed system data<br>- Test performance with all systems updating simultaneously |
| 68  | ✅ Final Integration Testing & Bug Fixes | - Run full E2E test suite (authentication → dashboard → system control)<br>- Validate 100% of user workflows on production build<br>- Performance test: dashboard load <2sec, updates <500ms latency<br>- Security audit: verify RBAC on all endpoints, JWT validation, XSS/CSRF protection<br>- Document all known limitations and workarounds |
| 69  | ✅ Production Deployment & Documentation Complete | - Backend packaged for production with Docker containerization and runtime configuration documentation<br>- Deployment runbook created for Days 71+ team, including setup, build, deploy, and rollback procedures<br>- API reference generated from FastAPI OpenAPI and linked in project documentation<br>- Frontend production build optimized with Next.js and asset minification<br>- CI/CD scaffolding created for backend and frontend with lint/test/build gates<br>- Day 67/68 playback and notification systems fully validated with pause/resume, scheduling, rule evaluation, delivery configuration, and status tracking<br>- Acceptance: playback and notification endpoint tests passing, production deployment checklist completed |
| 70  | ✅ Hardware Integration Handoff & Readiness Review Complete | - Verified backend API readiness for real sensor data injection and telemetry storage<br>- Confirmed database schema supports IoT telemetry, alerts, playback sessions, and delivery state<br>- Reviewed gRPC/Vryndara robotic control integration and hardware command readiness<br>- Delivered integration guide and knowledge transfer materials to the hardware team<br>- Completed final readiness checklist and established software freeze for Phase 2 hardware development |s, CI/CD & Verification (Other)** — finalize production readiness:<br>- Add production Dockerfiles, multi-stage builds, and small `docker-compose.prod.yml` for quick staging deploys.<br>- Add GitHub Actions pipelines for PR lint/test/build and a deploy pipeline to staging (container image publish, DB migration job).<br>- Run full test suite and fix collection issues (`pytest_asyncio`); add CI job that runs `pytest -q` and fails on collection errors.<br>- Create smoke tests and health-check endpoints; add synthetic monitoring scripts for uptime checks.<br>- Acceptance: successful staging deploy, CI runs all tests and migration job, smoke tests report green for 48h in staging.<br><br>Notes: break Day 69 into smaller tickets (69.1..69.9) for implementation; prioritize CI + migrations + alert delivery in first sprint. |

---

# Phase 2: Student-Scale Hardware Prototype (Days 71-110)
*Final semester: build a low-cost Phase 2 prototype using your existing Arduino Mega, soldering tools, and affordable sensors.*

**TARGET BUDGET:** under ₹8,000

**GOAL:** deliver a working hardware/software prototype that demonstrates telemetry, backend integration, alerts, and a small mobile platform.

---

## Day-by-day student plan (71–110)

### Days 71–75: Sensor node setup
| Day | Task | Required components | Skills | Outcome |
|-----|------|---------------------|--------|---------|
| 71 | Confirm hardware and order parts | DHT11 module, capacitive soil moisture sensor, LDR, jumper wires, breadboard kit | procurement, planning | All required parts ordered and workspace prepared |
| 72 | Setup Arduino and PC | Arduino Mega, USB cable, Arduino IDE | Arduino setup, serial communication | Arduino development environment working |
| 73 | Assemble sensor node | DHT11, soil moisture, LDR, breadboard, jumper wires | wiring, soldering, sensor interfacing | Sensor node reads temperature, humidity, moisture, light |
| 74 | Calibrate sensors | same sensors, small resistors if needed | calibration, analog smoothing | Sensor readings stable and correct ranges confirmed |
| 75 | Add serial telemetry | USB cable, Python/PC | Python serial, data parsing | Sensor values available on PC via Arduino serial |

### Days 76–80: Backend ingestion and dashboard
| Day | Task | Required components | Skills | Outcome |
|-----|------|---------------------|--------|---------|
| 76 | Build backend endpoint | existing FastAPI app | FastAPI route creation | `/api/v1/student-sensor` endpoint ready |
| 77 | Send serial data to backend | Python script, Arduino serial | HTTP POST, JSON | Sensor data uploads to backend successfully |
| 78 | Store telemetry in DB | backend DB, schemas | SQLAlchemy/ORM | Telemetry persisted with timestamp and sensor type |
| 79 | Display live data | backend + simple page | HTML/JavaScript or template | Dashboard shows current sensor values |
| 80 | Validate end-to-end flow | sensor node + backend | integration testing | Sensor → backend → dashboard flow works |

### Days 81–85: Mobile carrier and simple control
| Day | Task | Required components | Skills | Outcome |
|-----|------|---------------------|--------|---------|
| 81 | Build robot chassis | small 2-wheeled chassis kit, caster wheel | mechanical assembly | Small mobile platform built |
| 82 | Add motion control | 2 DC motors, L298N motor driver, battery holder | motor wiring, Arduino control | Robot can move forward/backward via Arduino |
| 83 | Add remote commands | Arduino serial command parser | control logic, serial handling | PC can send start/stop/move commands to robot |
| 84 | Mount sensor node on carrier | sensor node, chassis mounting | assembly, fastening | Sensor node mounted on mobile platform |
| 85 | Test movement while sensing | complete prototype | system testing | Robot moves and streams sensor data together |

### Days 86–90: Alerts, actuators, and emergency response
| Day | Task | Required components | Skills | Outcome |
|-----|------|---------------------|--------|---------|
| 86 | Add threshold alerts and pump control | backend rule logic, relay module, water pump | rule creation, actuator control | Alerts trigger for dry soil and pump activation works |
| 87 | Add emergency stop, RFID operator auth and alarm | Arduino stop command, RC522 RFID module, cards/tags, buzzer | safety logic, RFID integration | Backend can stop robot, require operator RFID auth, and sound alarm immediately |
| 88 | Add fire/smoke detection | flame sensor, MQ-2/MQ-135 gas sensor | fire detection, sensor integration | Fire/smoke alert triggers and emergency path validates |
| 89 | Harden hardware with actuators | tape, glue, extra wiring, relay wiring | hardware robustness, actuator wiring | Pump and alarm wiring are stable for repeated use |
| 90 | Prepare demo script with actuators | documentation, notes | demo planning | Repeatable demo checklist includes pump and emergency flow |

### Days 91–96: Integration testing and reliability
| Day | Task | Required components | Skills | Outcome |
|-----|------|---------------------|--------|---------|
| 91 | Continuous run test | prototype, PC | reliability testing | 2-hour continuous run validated |
| 92 | Connectivity test | USB serial or nRF24L01 | comm debugging | Communication stable |
| 93 | Record sample dataset | backend storage | logging, data capture | Sample dataset saved for review |
| 94 | Test alert flow | backend rules, sensor node | scenario testing | Alert conditions verified |
| 95 | Troubleshoot issues | spare wires, parts | debugging | Remaining issues fixed |
| 96 | Code cleanup | source code | refactoring | Clean and maintainable codebase |

### Days 97–100: Packaging and documentation
| Day | Task | Required components | Skills | Outcome |
|-----|------|---------------------|--------|---------|
| 97 | Build enclosure | cardboard, hot glue | prototyping | Prototype housed neatly |
| 98 | Write README | text editor | documentation | Implementation documented step-by-step |
| 99 | Prepare operation notes | printed checklist | process planning | Operation checklist ready |
| 100 | Final demo practice & staff training with RFID | prototype, PC, RC522 module, cards/tags | presentation, RFID onboarding | Running demo completed and operators trained on RFID login and emergency procedures |

### Days 101–110: Final review and handoff readiness
| Day | Task | Required components | Skills | Outcome |
|-----|------|---------------------|--------|---------|
| 101 | Demo the prototype | prototype, PC | presentation | Prototype demonstrated successfully |
| 102 | Capture evidence | photos, notes | reporting | Results documented |
| 103 | Collect feedback | mentor/peer review | communication | Feedback noted for improvements |
| 104 | Plan future scaling | notes | planning | Clear next-step plan created |
| 105 | Repeat demo run | prototype | verification | System repeats reliably |
| 106 | Finalize documentation | docs | documentation | Final notes complete |
| 107 | Backup project files | Git/zip | source control | Code and data backed up |
| 108 | Optional extension | optional extra sensor | prototyping | Bonus feature added if budget remains |
| 109 | Final checklist | notes | closure planning | Handoff checklist prepared |
| 110 | Completion review | review sheet | project closure | Final semester deliverable complete |

---

## Required components and approximate cost
| Component | Estimate (Rs) |
|---|---|
| DHT11 temperature/humidity sensor | 120 |
| Capacitive soil moisture sensor | 200 |
| LDR light sensor + resistors | 50 |
| ESP32-WROOM-32 DevKit (1x) | 400 |
| USB cable (micro-USB) | 150 |
| Flame sensor module | 120 |
| MQ-2 / MQ-135 gas/smoke sensor | 180 |
| Jumper wires + breadboard kit | 250 |
| Protoboard / headers | 150 |
| Small robot chassis kit | 420 |
| L298N motor driver board | 150 |
| Battery holder / 18650 holder | 200 |
| Submersible water pump | 300 |
| 1-channel relay module | 120 |
| Buzzer / alarm module | 50 |
| Mounting parts / glue / tape | 150 |
| Optional wireless module (nRF24L01) | 250 |
| Extra sensor or spare parts | 300 |
| RC522 RFID reader/writer (SPI) | 350 |
| RFID cards (5) + keyfobs (5) | 120 |
| **Total** | **4,280–4,540** |

> With the actuator and emergency components included, the project remains under ₹4,000 and still well within the ₹8,000 student budget.

> With room to add one extra sensor or better connectivity while staying well below ₹8,000.

---

## What this prototype will do
- Read temperature, humidity, soil moisture, light, and fire/smoke signals
- Send the data from Arduino to the backend
- Store sensor telemetry in the database
- Display live values in a dashboard or simple page
- Trigger alerts when thresholds are crossed or emergency conditions happen
- Automatically run a water pump when soil is dry
- Sound an alarm and stop the robot on fire/smoke detection
- Control a small mobile platform from the backend
- Show a complete hardware/software integration flow

---

## Core skills required
- Arduino programming and sensor interfacing
- Basic electronics and wiring
- Python scripting and serial communication
- FastAPI endpoint and DB integration
- Simple frontend/dashboard display
- Hardware testing and debugging
- Documentation and demo preparation

---

## Notes
- This plan is intentionally reduced for a student budget and still retains core Phase 2 functionality.
- It does not include a full estate-scale network or professional-grade robotics fleet.
- It requires careful wiring, stable power, and good documentation to prevent stoppage.

---

## Implementation Notes
- **Full Estate Scope:** Biosphere Protocol covers entire private estate including living quarters, laboratories, farms, storage facilities, security systems, and infrastructure
- **Software-First Approach:** All software development (Days 1-70) completed THIS SEMESTER before hardware begins
- **gRPC Priority:** Vryndara kernel integration is critical for robotic orchestration and estate management
- **ML Integration:** Acoustic pest recognition, soil health prediction, and environmental monitoring models are core
- **3D Spatial Mapping:** Essential for managing entire estate layout and operations
- **Security Focus:** All components must support air-gapped, offline operation for UHNIs
- **Estate Integration:** Unified system for agriculture, residential, laboratory, and infrastructure management
- **Realistic Hardware Timeline:** Days 71-110 focuses on actual physical IoT deployment, robotics assembly, and system integration
- **Reserved Days 111-150:** Future expansion, research integration, and system enhancements based on Phase 1+2 operational data
