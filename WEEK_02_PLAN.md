# Week 2: Backend Infrastructure
## Theme: Production-Grade FastAPI Foundation

**Week Dates:** March 20-26, 2026  
**Status:** 🟢 IN PROGRESS  
**Target Completion:** Day 14 (March 26)  
**Success Metric:** All tests passing, health endpoint working, Vryndara integration confirmed

---

## Daily Breakdown

### Day 8: FastAPI Project Scaffolding ✅ TODAY
**Objective:** Establish production-grade backend structure with best practices

**Deliverables:**
- [ ] FastAPI app initialization with CORS & error handling
- [ ] Router structure: `/api/v1/auth`, `/api/v1/zones`, `/api/v1/sensors`, `/api/v1/research`
- [ ] Comprehensive middleware (logging, error handling, request ID tracing)
- [ ] Configuration management (dev/test/prod)
- [ ] Dependency injection for database and services
- [ ] Startup events (DB initialization, Vryndara health check)
- [ ] Basic error response schema + exception handlers

**Code Structure to Create:**
```
backend/
├── main.py                 # App entry point
├── config.py              # Settings (Pydantic BaseSettings)
├── dependencies.py        # FastAPI dependencies
├── exceptions.py          # Custom exceptions
├── middleware.py          # Logging, tracing, CORS
├── routers/
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── zones.py          # Zone management
│   ├── sensors.py        # Sensor data ingestion
│   ├── research.py       # Vryndara research endpoints
│   └── health.py         # Health and status
├── services/
│   ├── __init__.py
│   ├── vryndara_connector.py  # Vryndara integration
│   ├── auth_service.py        # JWT/RBAC logic
│   └── zone_service.py        # Zone business logic
├── models/
│   ├── __init__.py
│   ├── schemas.py         # Pydantic models (API)
│   └── db.py             # SQLAlchemy models
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # pytest fixtures
│   ├── test_auth.py
│   ├── test_zones.py
│   └── test_vryndara.py
└── requirements.txt
```

**Key Endpoints to Stub:**
```
POST   /api/v1/auth/login           → Get JWT token
GET    /api/v1/health              → System health
GET    /api/v1/health/detailed     → Detailed status (admin only)
POST   /api/v1/zones               → Create zone
GET    /api/v1/zones/{zone_id}     → Get zone state
POST   /api/v1/research/framework  → Vryndara research
GET    /docs                       → Swagger/OpenAPI docs
```

**Acceptance Criteria:**
- FastAPI app starts without errors: `uvicorn backend.main:app --reload`
- All routers imported and mounted correctly
- `/health` returns 200 with basic status
- Swagger docs accessible at `http://localhost:8000/docs`
- All imports organized and no circular dependencies
- Code follows PEP 8 + style guide

---

### Day 9: PostgreSQL Setup & SQLAlchemy Models
**Objective:** Establish data persistence layer with ORM

**Deliverables:**
- [ ] PostgreSQL local setup OR SQLite for dev (decision: use SQLite for Week 2)
- [ ] SQLAlchemy core configuration (engine, session factory)
- [ ] ORM models:
  - `Tenant` — Multi-tenant isolation
  - `User` — Authentication + RBAC
  - `Zone` — Operational zones (asset groups)
  - `Sensor` — Sensor metadata
  - `SensorData` — Time-series readings
  - `AuditLog` — All state changes (pre-blockchain)
  - `VryndaraRequest` — Track Vryndara queries
- [ ] Alembic migration setup
- [ ] Database initialization script

**Database Schema Highlights:**
- Timestamps: `created_at`, `updated_at` on all models
- Soft deletes: `deleted_at` for compliance
- Tenant isolation: `tenant_id` as foreign key (will be enforced in middleware)
- Indexes on: `tenant_id`, `user_id`, `zone_id`, `created_at`

**Acceptance Criteria:**
- `sqlite:///aegis.db` created on app startup
- All models pass SQLAlchemy validation
- Alembic migration: `alembic revision --autogenerate`
- No migration errors on fresh DB

---

### Day 10: User & Tenant Models + Authentication
**Objective:** Establish multi-tenant isolation + user auth

**Deliverables:**
- [ ] User model: id, email, hashed_password, role, tenant_id, is_active, created_at
- [ ] Tenant model: id, name, created_at, settings (JSON)
- [ ] RBAC roles: `admin`, `operator`, `viewer`, `analyst`
- [ ] Password hashing: bcrypt with salt
- [ ] JWT token generation (access + refresh)
- [ ] Login endpoint: POST `/api/v1/auth/login`
- [ ] Token validation middleware
- [ ] Tenant ID enforcement in all queries (via dependency injection)

**Security Features:**
- Bcrypt password hashing (cost: 12)
- JWT access tokens: 15-minute TTL
- JWT refresh tokens: 7-day TTL
- Secure password reset flow (stub for Phase 2)

**Acceptance Criteria:**
- `POST /api/v1/auth/login` with email/password returns JWT token
- Invalid credentials return 401
- Expired tokens return 401
- Refresh token endpoint works
- All queries filtered by tenant_id

---

### Day 11: Health Check Endpoint & Vryndara Integration
**Objective:** Verify system connectivity across all components

**Deliverables:**
- [ ] GET `/health` endpoint returning:
  - `status`: "healthy" | "degraded" | "unhealthy"
  - `backend`: "running"
  - `database`: "connected" | "disconnected"
  - `vryndara`: "connected" | "disconnected" | "fallback"
  - `blockchain`: "connected" | "simulated"
  - `uptime_seconds`: integer
  - `timestamp`: ISO 8601
- [ ] GET `/health/detailed` (admin only) with:
  - Database connection time (ms)
  - Vryndara gRPC latency
  - Request count, error count
  - Memory usage
  - Version info
- [ ] Vryndara health check on startup
- [ ] Graceful fallback if Vryndara unavailable
- [ ] BlockchainStub mock for Phase 1

**Vryndara Integration:**
- gRPC client connection attempt (port 50051)
- Retry logic with backoff
- Fallback mode: continue if Vryndara unavailable
- Log all connection attempts

**Acceptance Criteria:**
- `/health` returns 200 within 500ms
- Shows accurate component status
- Vryndara unavailability doesn't crash app
- Detailed endpoint requires admin token

---

### Day 12: Testing Framework Setup (pytest)
**Objective:** Establish comprehensive testing infrastructure

**Deliverables:**
- [ ] pytest configuration in `pyproject.toml` or `pytest.ini`
- [ ] Fixtures:
  - `client` — TestClient for FastAPI
  - `db_session` — In-memory SQLite
  - `test_user` — Pre-created user
  - `test_tenant` — Pre-created tenant
  - `mock_vryndara` — Mocked Vryndara responses
- [ ] Unit tests for models and services:
  - `test_auth.py` — Password hashing, JWT generation
  - `test_models.py` — Tenant/User/Zone creation
  - `test_vryndara_connector.py` — Fallback mode
- [ ] Integration tests:
  - Login flow
  - Tenant isolation verification
  - Health check status
- [ ] Coverage reporting (pytest-cov)
- [ ] CI/CD ready (GitHub Actions stub)

**Test Organization:**
```
tests/
├── conftest.py                    # Global fixtures
├── test_auth.py                   # Auth unit tests
├── test_models.py                 # ORM tests
├── test_vryndara_connector.py    # Vryndara tests
└── integration/
    └── test_full_workflow.py      # End-to-end
```

**Coverage Targets:**
- Target: 75%+ (aim for 80%+)
- Ignore: migrations, config defaults
- Report: html + console

**Acceptance Criteria:**
- `pytest` runs without errors
- All fixtures work correctly
- Coverage ≥75% for core modules
- Mocked Vryndara doesn't require real kernel

---

### Day 13: API Documentation & Route Cleanup
**Objective:** Document all endpoints for developer reference

**Deliverables:**
- [ ] Swagger/OpenAPI docs (auto-generated by FastAPI)
- [ ] README with curl/Python examples
- [ ] Endpoint documentation including:
  - Request/response schemas (Pydantic)
  - HTTP status codes
  - Authentication requirements
  - Example payloads
- [ ] Postman collection (optional, for testing UI)
- [ ] Route organization review

**Documentation to Create:**
- `API_REFERENCE.md` — All endpoints with examples
- Update main `README.md` — Quick-start for backend
- Swagger accessible at `http://localhost:8000/docs`
- ReDoc at `http://localhost:8000/redoc`

**Example Endpoint Doc Format:**
```
### POST /api/v1/auth/login
**Description:** Authenticate user with email/password  
**Authentication:** None  
**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```
**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```
**Errors:** 401 (invalid credentials), 422 (validation error)
```

**Acceptance Criteria:**
- All endpoints documented
- Examples are copy-paste ready
- Swagger renders without errors
- No broken links in docs

---

### Day 14: Week 2 Review & Planning for Week 3
**Objective:** Assess progress, document blockers, plan next week

**Deliverable:** WEEK_02_REVIEW.md

**Review Checklist:**
- [ ] FastAPI app starts cleanly: `uvicorn backend.main:app --reload`
- [ ] Health check passes: `GET http://localhost:8000/health` returns 200
- [ ] Database schema loads: `sqlite:///aegis.db` exists with all tables
- [ ] All tests pass: `pytest -v` shows ≥20 passing tests
- [ ] Authentication endpoint works: `POST /api/v1/auth/login`
- [ ] Vryndara connector initializes (fallback mode if kernel unavailable)
- [ ] Swagger docs accessible: `http://localhost:8000/docs`
- [ ] No circular imports or linting errors

**Metrics to Track:**
- Lines of code: Target 2,000-2,500
- Tests added: ≥20
- Code coverage: ≥75%
- Documentation pages: 3+ (API_REFERENCE, README updates, dev guide)
- Bugs found/fixed: count
- Time spent: per task

**Success Criteria (Go/NoGo for Week 3):**
- ✅ All 6 deliverables (Days 8-13) substantially complete
- ✅ No critical blockers
- ✅ Confidence in architecture: ≥85%

**If Blocked:**
- Document issue in blockers list
- Propose mitigation
- Continue with non-blocking tasks
- Recap in next daily standup

---

## Week 2 Success Profile

### What "Done" Looks Like
```bash
# Terminal 1: Start backend
$ uvicorn backend.main:app --reload
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
INFO:     Database initialized
INFO:     Vryndara connector: fallback mode (kernel unavailable)

# Terminal 2: Run tests
$ pytest -v
collected 25 items
test_auth.py::test_login_success PASSED                              [ 4%]
test_auth.py::test_login_invalid_credentials PASSED                  [ 8%]
...
========================== 25 passed in 2.34s ==========================

# Browser: Check API docs
Open http://localhost:8000/docs
→ All endpoints documented + executable

# Health check
$ curl http://localhost:8000/health
{
  "status": "healthy",
  "backend": "running",
  "database": "connected",
  "vryndara": "fallback",
  "uptime_seconds": 1234,
  "timestamp": "2026-03-26T18:00:00Z"
}
```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Vryndara kernel not installed | High | Medium | Use mock/fallback mode in Week 2 |
| Database migration complexity | Low | Medium | Use SQLite fixtures for tests |
| JWT token refresh logic error | Low | Medium | Comprehensive auth tests |
| Import circular dependencies | Medium | Low | Clean architecture from day 1 |
| Pytest fixtures not flexible | Low | Low | Use conftest.py best practices |

---

## Blockers & Notes
- [ ] None identified yet (create as needed)

---

## Next Week Preview (Week 3: Frontend Scaffolding)
- Next.js project setup with TypeScript
- Tailwind CSS + component library
- Login UI connected to backend
- Real-time health check display
- RBAC role-based UI variations

---

**Week 2 Start Date:** March 20, 2026  
**Week 2 End Date:** March 26, 2026  
**Status:** 🟢 IN PROGRESS (Day 8 Starting)
