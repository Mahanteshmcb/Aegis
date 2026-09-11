# Aegis Developer Guide

## Quick Start (5 Minutes)

### 1. Prerequisites
- **Conda environment:** Must have `aegis` environment with Python 3.10
- **Backend port:** 8001 (FastAPI)
- **Frontend port:** 3000+ (Next.js, auto-increments if in use)

### 2. Terminal 1: Start Backend
```powershell
cd c:\Users\Mahantesh\DevelopmentProjects\Aegis
conda activate aegis
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

✅ **Expected output:** `Application startup complete.`  
📚 **API Docs:** http://localhost:8001/docs

### 3. Terminal 2: Start Frontend
```powershell
cd frontend
npm run dev
```

✅ **Frontend runs on:** http://localhost:3000 or http://127.0.0.1:3000 (or 3001, 3002, etc.)  
📝 **`.env.local` already configured** to point to backend at port 8001

### 4. Login
- **URL:** http://localhost:3000 (or the port shown in terminal)
- **Email:** `admin@aegis.com`
- **Password:** `admin1234`

### 5. Access Points
| Component | URL |
|-----------|-----|
| **Dashboard** | http://localhost:3000 |
| **API Docs** | http://localhost:8001/docs |
| **Health Check** | http://localhost:8001/api/v1/health |

---

## Day 54 — Energy policy persistence & Biodiversity optimizer (Reference)

- Energy charging policies are persisted in the database via the `energy_policies` table.
- Backend model: `backend.models_db.EnergyPolicy` — fields: `tenant_id`, `charge_threshold`, `discharge_threshold`, `max_charge_rate_kw`.
- API endpoints:
  - `GET /api/v1/energy/policy` — returns latest policy for `tenant_id` (optional query param).
  - `POST /api/v1/energy/policy` — saves a new policy row for the tenant.
- If Alembic isn't available or fails in dev, create tables with SQLAlchemy at runtime:
  ```powershell
  $env:PYTHONPATH='.'; python -c "from backend.database import init_db; init_db(); print('DB initialized')"
  ```

- Biodiversity optimizer helper: `ai/biodiversity_optimization.py` with `optimize_diversity()`.
- API endpoint: `GET /api/v1/biodiversity/optimize?slots=10` — returns suggested species mix (demo logic).

## Day 55 — Weather integration (scaffold)

Goal: integrate weather forecasts to inform scheduling, energy management, and crop decisions.

Scaffold added (Day 55):
- AI helper: `ai/weather_integration.py` — `get_forecast(lat, lon)` returns demo forecast if no `OPENWEATHER_API_KEY` is set.
- Router: `backend/routers/weather.py` — `GET /api/v1/weather/forecast?lat=&lon=` returns forecast JSON.
- Test: `tests/test_weather.py` — simple unit check for forecast structure.

How to run quick local checks:
```powershell
cd C:\Users\Mahantesh\DevelopmentProjects\Aegis
$env:PYTHONPATH='.'; python -c "from ai.weather_integration import get_forecast; print(get_forecast(51.5, -0.12)[:2])"
```

To enable a real provider, set `OPENWEATHER_API_KEY` in your environment (the helper will attempt a fetch).

Next steps I can take for Day 55 on request:
- Wire weather signals into the energy scheduler to account for expected cloud/rain.
- Add frontend dashboard widgets (forecast card, rain warnings, adaptive scheduling toggles).
- Add historical weather caching and DB model for forecasts.

## Day 56 — Compliance and regulatory reporting
This milestone implements tenant-aware compliance tracking and certification reporting for agricultural and organic production.
- Added `POST /api/v1/audit/compliance/organic-certification/request` to record certification requests on blockchain and in DB audit logs.
- Added `GET /api/v1/audit/compliance/organic-certification/{tenant_id}` to retrieve certification request counts and compliance summary.
- Extended frontend API utilities with `requestOrganicCertification()` and `getOrganicCertificationStatus()`.

### Day 56 validation
- Submit a certification request through `/api/v1/audit/compliance/organic-certification/request`.
- Query `/api/v1/audit/compliance/organic-certification/{tenant_id}` to confirm request counts and compliance summary.
- Verify audit log records exist for `organic_certification_request` events.

## Day 57 — Live telemetry and local adaptation
This milestone connects live on-site sensor telemetry directly into the weather and energy planning pipeline.
- Sensor readings are ingested through `/api/v1/sensors/data` and environmental sensors automatically create local `WeatherObservation` entries.
- The dashboard now includes a `Live Sensor Telemetry` card with the latest device readings and a direct button to ingest environmental telemetry into the local weather model.
- Weather forecast cache and energy status calculations now reflect local observations, closing the loop between sensor feed, forecast, and charge scheduling.
- WeatherObservationCard displays recent local observations with timestamp, temperature, humidity, wind, and precipitation.
- Frontend uses `useCurrentUser()` hook for tenant-aware queries across all weather/energy endpoints.

### Day 57 validation
- Verify sensor telemetry ingestion with `/api/v1/sensors` and `/api/v1/sensors/data`.
- Query `/api/v1/weather/observations` for recent local weather data.
- Confirm `/api/v1/weather/local_forecast` and `/api/v1/energy/status` respond with forecast-driven values.
- Check dashboard displays "Recent Observations" panel with weather data.
- Verify SensorTelemetryCard shows live sensor readings with ingest buttons.

## Day 58 — Adaptive energy scheduling
This milestone implements an intelligent charge/discharge scheduler that uses weather forecasts to optimize battery management and recommend load-shifting strategies.
- Smart scheduler evaluates solar confidence based on precipitation, cloud cover, and temperature.
- Analyzes 24-hour forecast to prioritize charging during high-solar windows.
- Defers non-critical loads when battery is low; recommends manual load shifting.
- Endpoint: `GET /api/v1/energy/smart_schedule?tenant_id=&zone_id=` returns adaptive schedule with recommendations.
- EnergyCard dashboard widget includes "Smart Schedule" button to view weather-aware plan.
- Returns detailed metrics: peak load, min/max SOC, generation/consumption balance, and actionable recommendations.

### Day 58 validation
- Call `/api/v1/energy/smart_schedule` to see adaptive schedule with weather signals.
- Click "Smart Schedule" button in EnergyCard to view hourly plan and recommendations.
- Verify schedule adjusts solar confidence based on forecast (rain → reduced confidence).
- Check recommendations for capacity warnings and low battery alerts.
- Run `pytest tests/test_day58_adaptive_energy.py -q` to validate all 6 scheduling scenarios.

### References
- **Adaptive Scheduler:** `ai/energy_management.py::smart_adaptive_schedule()`
- **API Endpoint:** `/api/v1/energy/smart_schedule`
- **Frontend Component:** `frontend/components/EnergyCard.js` with getSmartEnergySchedule()
- **Tests:** `tests/test_day58_adaptive_energy.py`

## Day 59 — Software completion milestone
This milestone conducts final integration testing, performance benchmarking, and security audits to validate all components work together and meet quality standards before Phase 2 hardware development.
- **E2E Integration Tests:** Complete pipeline validation (tenant → sensor → telemetry → weather → energy → schedule)
- **Performance Benchmarking:** Establishes baseline metrics for key endpoints (health <5ms, queries <100ms, adaptive schedule <150ms)
- **Security Audit:** Validates JWT authentication, multi-tenant isolation, SQL injection prevention, audit immutability
- All tests located in `tests/test_day59_*.py` (3 test files, 32 total test cases)
- Comprehensive milestone report: `DAY59_MILESTONE_REPORT.md`

### Day 59 validation
Run full quality assurance suite:
```bash
# E2E Integration Tests (6 tests)
pytest tests/test_day59_e2e_integration.py -v

# Performance Benchmarking (12 tests) - includes baseline metrics report
pytest tests/test_day59_performance.py -v -s

# Security Audit (14 tests)
pytest tests/test_day59_security.py -v

# All Day 59 Tests (32 tests)
pytest tests/test_day59_*.py -v
```

**Expected Results:** 32/32 PASS ✅

### Quality Gates
✅ Full pipeline integration verified  
✅ Performance within acceptable baselines  
✅ Multi-tenant isolation enforced  
✅ Security vulnerabilities prevented  
✅ Audit trails immutable  

### References
- **E2E Tests:** `tests/test_day59_e2e_integration.py` (6 scenarios)
- **Performance Tests:** `tests/test_day59_performance.py` (12 benchmarks)
- **Security Tests:** `tests/test_day59_security.py` (14 validations)
- **Milestone Report:** `DAY59_MILESTONE_REPORT.md`


## Overview
Aegis is a decentralized digital twin framework for sovereign asset management, anti-forensic security, and enterprise infrastructure orchestration. The system is modular, with components for backend (FastAPI), AI orchestration, frontend (Next.js), blockchain (Hardhat), IoT (ESP32), and database (SQLite/PostgreSQL).

---

## 1. Environment Setup

- **Python:** 3.10+ (via conda)
  ```sh
  conda create -y -n aegis python=3.10
  conda activate aegis
  ```
- **Node.js:** v18+ (for frontend/blockchain)
- **Database:** SQLite (default, no setup needed) or PostgreSQL v13+ (for production)

---

## 2. Backend (FastAPI)

- **Location:** `backend/`
- **Entry Point:** `main.py`
- **Dependencies:** `backend/requirements.txt`
- **Run with Auto-Reload:**
  ```sh
  conda activate aegis
  $env:SERVER_PORT=8001
  python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
  ```
- **Endpoints:**
  - `GET /` — API info
  - `GET /api/v1/health` — Health check
  - `POST /api/v1/tenants` — Tenant management
  - `POST /api/v1/auth/register` — User registration
  - `POST /api/v1/auth/login` — User login
  - `POST /api/v1/zones` — Zone management
  - `POST /api/v1/sensors` — Sensor management
  - `GET /api/v1/audit-logs` — Audit trail
- **Testing:**
  ```sh
  conda activate aegis
  python -m pytest tests/ -q
  ```
- **Notes:**
  - All models are in `backend/models_db.py`
  - Use tenants API to create tenants before zones/sensors
  - CORS configured for ports: 3000, 3001, 3002, 8080
  - Vryndara integration operates in offline mode by default
  - All tests must pass before merging changes

---

## 3. AI Orchestrator

- **Location:** `ai/`
- **Entry Point:** `orchestrator.py`
- **Dependencies:** `ai/requirements.txt`
- **Run:**
  ```sh
  conda activate aegis
  python ai/orchestrator.py
  ```
- **Notes:**
  - Uses LangChain and CrewAI for multi-agent orchestration
  - Vryndara connector: Gracefully handles offline mode
  - Operates without OpenAI API key (local/offline mode)
  - Extend by adding new agents/tasks in `orchestrator.py`

---

## 4. Frontend (Next.js)

- **Location:** `frontend/`
- **Entry Point:** `pages/index.js`
- **Dependencies:** `frontend/package.json`
- **Environment File:** `frontend/.env.local`
  ```env
  NEXT_PUBLIC_API_URL=http://localhost:8001
  ```
- **Run:**
  ```sh
  cd frontend
  npm install
  npm run dev
  ```
- **Expected Output:**
  ```
  ▲ Next.js 14.0.0
  - Local: http://localhost:3000
  ✓ Ready in XXXms
  ```
- **Notes:**
  - Port auto-increments if 3000 is in use (3001, 3002, etc.)
  - `.env.local` already configured with correct backend URL
  - CORS configured on backend for all frontend ports
  - Add new pages/components in `pages/` and `components/`
  - Uses Tailwind CSS for styling

---

## 5. Blockchain (Hardhat - Optional)

- **Location:** `blockchain/`
- **Entry Point:** `contracts/AegisAudit.sol`
- **Dependencies:** `blockchain/package.json`
- **Run Local Network:**
  ```sh
  cd blockchain
  npm install
  npx hardhat node --config hardhat.config.js
  ```
- **Expected Output:**
  ```
  Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/
  ```
- **Run Tests:**
  ```sh
  npx hardhat test
  ```
- **Notes:**
  - Write/test contracts in `contracts/`
  - Hardhat network runs at http://localhost:8545
  - Use Hardhat scripts for deployment

---

## 6. IoT (ESP32)

- **Location:** `iot/esp32_sensor.py`
- **Notes:**
  - MicroPython code for ESP32 sensor node
  - Update WiFi and MQTT settings as needed
  - Publishes sensor data to backend via API

---

## 7. Database

### SQLite (Development - Default)
- **File:** `aegis.db` (auto-created)
- **No setup required** - database initializes on first backend startup

### PostgreSQL (Production)
- **Location:** `database/schema.sql`
- **Setup:**
  ```sql
  psql -U postgres -d aegis -f database/schema.sql
  ```
- **Connection String:**
  ```env
  DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/aegis
  ```

---

## 8. Testing

- **Location:** `tests/`
- **Run All Tests:**
  ```sh
  conda activate aegis
  python -m pytest tests/ -q
  ```
- **Run Specific Test:**
  ```sh
  conda activate aegis
  python -m pytest tests/test_basic.py -v
  ```
- **Run with Coverage:**
  ```sh
  conda activate aegis
  pytest --cov=backend --cov=ai --cov-report=term-missing
  ```
- **Generate HTML Coverage Report:**
  ```sh
  conda activate aegis
  pytest --cov=backend --cov=ai --cov-report=html
  ```
  Open `htmlcov/index.html` to view

- **Notes:**
  - 20 tests currently passing
  - Uses pytest-asyncio==0.21.1 for async support
  - No `__init__.py` in `tests/` directory (important)
  - All tests must pass before PR approval

---

## 9. Common Issues & Troubleshooting

### Frontend Shows "Failed to Fetch"
- **Cause:** Backend not running or API URL mismatch
- **Solution:**
  ```
  1. Verify backend is running on port 8001
  2. Check frontend/.env.local has: NEXT_PUBLIC_API_URL=http://localhost:8001
  3. Hard refresh frontend: Ctrl+F5 (or Cmd+Shift+R on Mac)
  4. Clear browser cache
  ```

### Backend Won't Start on Port 8001
- **Cause:** Port already in use or permission denied
- **Solution:**
  ```powershell
  # Try different port
  $env:SERVER_PORT=8002
  python -m backend.main
  
  # Or kill the process using the port
  netstat -ano | findstr :8001
  taskkill /PID <PID> /F
  ```

### CORS Errors on Login
- **Cause:** Frontend running on port not in CORS whitelist
- **Solution:** Backend CORS allows ports: 3000, 3001, 3002, 8080
  - If using different port, update `backend/middleware.py`
  - Add new port to `allow_origins` list

### Tests Fail with Import Errors
- **Cause:** Missing dependencies or wrong Python environment
- **Solution:**
  ```powershell
  conda activate aegis
  pip install -r backend/requirements.txt
  pip install -r ai/requirements.txt
  ```

### Vryndara Connector Warnings
- **Cause:** Protobuf version incompatibility (expected in offline mode)
- **Solution:** This is normal! System runs in offline fallback mode
  - No OpenAI API key needed
  - No Vryndara kernel required
  - All features work locally

### Port 3000 Already in Use
- **Solution:** Next.js auto-increments to 3001, 3002, etc.
  - Check the terminal output for actual port
  - Update `NEXT_PUBLIC_API_URL` if needed

---

## 10. Development Workflow

### Adding a New Endpoint
```python
# In backend/routers/example.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["example"])

@router.get("/example")
async def get_example():
    return {"message": "Hello"}

# In backend/main.py
app.include_router(example.router)
```

### Adding a New Frontend Page
```bash
# Create new file: frontend/pages/newpage.js
# Access at: http://localhost:3000/newpage
```

### Running Backend in Production
```powershell
$env:ENVIRONMENT=prod
$env:DEBUG=false
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

---

## 11. Contribution

- Follow modular structure for new features
- Document new endpoints, agents, or contracts
- Keep dependencies updated in `requirements.txt` or `package.json`
- All code must be tested and pass CI before merging
- Ensure all tests pass: `pytest tests/ -q`

---

## 12. API Documentation & Usage

### Interactive API Docs (Swagger UI)

Aegis provides interactive API documentation using FastAPI's built-in Swagger UI.

- **Access the docs:**
  - Backend running: http://localhost:8001/docs
  - Try endpoints directly from the UI
  - See request/response schemas
  - Authorize with JWT tokens

- **Features:**
  - Browse all endpoints grouped by tags
  - View request/response schemas
  - Test endpoints interactively
  - Copy curl commands for API testing

---

## 13. Environment Variables

### Backend (`.env` or CLI)
```bash
ENVIRONMENT=dev              # dev, test, prod
DEBUG=true                  # Enable debug mode
SERVER_HOST=127.0.0.1       # Server host
SERVER_PORT=8001            # Server port
DATABASE_URL=sqlite:///./aegis.db  # Database connection
JWT_SECRET_KEY=your-secret  # JWT signing key
VRYNDARA_HOST=localhost     # Vryndara kernel host
VRYNDARA_PORT=50051         # Vryndara kernel port
```

### Frontend (`.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## 14. Quick Reference

| Task | Command |
|------|---------|
| Start Backend | `conda activate aegis && $env:SERVER_PORT=8001 && python -m backend.main` |
| Start Frontend | `cd frontend && npm run dev` |
| Start Blockchain | `cd blockchain && npx hardhat node` |
| Run Tests | `conda activate aegis && pytest tests/ -q` |
| View API Docs | http://localhost:8001/docs |
| Login Credentials | Email: `admin@aegis.com` / Password: `aegis2026` |
| Dashboard | http://localhost:3000 (or auto-incremented port) |
| Database File | `aegis.db` (auto-created in project root) |

---

**Last Updated:** April 21, 2026  
**Status:** ✅ Production Ready (Offline Mode)
  - View request/response models, descriptions, and example payloads.
  - Try out endpoints interactively (requires authentication for protected endpoints).

### API Usage Examples

- **Register a user:**
  - `POST /api/v1/auth/register` with JSON body `{ "email": ..., "password": ..., "tenant_id": ..., "role": ... }`
- **Login:**
  - `POST /api/v1/auth/login` with credentials to receive JWT tokens.
- **Health check:**
  - `GET /api/v1/health` for system status.
- **Research compliance framework:**
  - `POST /api/v1/research/framework` with body `{ "framework": "ISO27001", "query": "Describe controls" }`

### Improving API Docs

- All endpoints should have descriptive docstrings, response models, and tags.
- Use the `summary`, `description`, and `response_model` parameters in FastAPI routes for best docs.
- Add example payloads using `Body(..., example={...})` for clear API usage.

**Note:**
- If you add new endpoints, always check the docs at `/docs` to ensure they are discoverable and well-described.
- For OpenAPI JSON, visit `/openapi.json`.

---

## API Security Hardening (Day 14)

### Security Middleware
- **CORS:** Configured via `CORSMiddleware` using trusted origins from settings. In production, restrict `cors_origins` to trusted domains only.
- **Security Headers:** Automatically added to all responses:
  - `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `X-XSS-Protection`
- **Request ID, Logging, Error Handling:** All requests are traced, logged, and errors are returned in a consistent format.
- **Trusted Host & HTTPS Redirect:**
  - In production (`settings.debug == False`), only requests to allowed hosts are accepted and HTTP is redirected to HTTPS.
  - Adjust `allowed_hosts` in `setup_production_security_middleware` as needed for your deployment.

### Rate Limiting
- Not enabled by default. For production, consider adding a rate limiting middleware (e.g., `slowapi` or `starlette-limiter`).

### Best Practices
- Always run with `debug=False` in production for full security.
- Review and restrict CORS origins and allowed hosts.
- Use HTTPS in production (with a valid certificate).
- Monitor logs for suspicious activity and errors.

---
