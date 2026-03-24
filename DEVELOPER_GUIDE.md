# Aegis Developer Guide

## Overview
Aegis is a decentralized digital twin framework for sovereign asset management, anti-forensic security, and enterprise infrastructure orchestration. The system is modular, with components for backend (FastAPI), AI orchestration, frontend (Next.js), blockchain (Hardhat), IoT (ESP32), and database (PostgreSQL).

---

## conda create -y -n aegis python=3.10

# To activate this environment, use
#
#     $ conda activate aegis
#
# To deactivate an active environment, use
#
#     $ conda deactivate


# Aegis Developer Guide

## Overview
Aegis is a decentralized digital twin platform for asset management, anti-forensic security, and enterprise orchestration. It is modular, with backend (FastAPI), AI orchestration, frontend (Next.js), blockchain (Hardhat), IoT (ESP32), and PostgreSQL database.

---

## 1. Environment Setup

- **Python:** 3.10 (recommended via conda)
  ```sh
  conda create -y -n aegis python=3.10
  conda activate aegis
  ```
- **Node.js:** v18+ (for frontend/blockchain)
- **PostgreSQL:** v13+ (for production DB)

---

## 2. Backend (FastAPI)

- **Location:** `backend/`
- **Entry Point:** `main.py`
- **Dependencies:** `backend/requirements.txt`
- **Run:**
  ```sh
  pip install -r backend/requirements.txt
  uvicorn backend.main:app --reload --port 8080
  ```
- **Endpoints:**
  - `/` — API info
  - `/api/v1/health` — Health check
  - `/api/v1/tenants` — Tenant management
  - `/api/v1/zones` — Zone management
  - `/api/v1/sensors` — Sensor management
- **Testing:**
  ```sh
  pytest tests/
  ```
- **Notes:**
  - All models are in `backend/models_db.py`.
  - Use the tenants API to create tenants before zones/sensors in tests.
  - All tests must pass before merging changes.

---

## 3. AI Orchestrator

- **Location:** `ai/`
- **Entry Point:** `orchestrator.py`
- **Dependencies:** `ai/requirements.txt`
- **Run:**
  ```sh
  pip install -r ai/requirements.txt
  python ai/orchestrator.py
  ```
- **Notes:**
  - Uses LangChain and CrewAI for multi-agent orchestration.
  - Extend by adding new agents/tasks in `orchestrator.py`.

---

## 4. Frontend (Next.js)

- **Location:** `frontend/`
- **Entry Point:** `pages/index.js`
- **Dependencies:** `frontend/package.json`
- **Run:**
  ```sh
  cd frontend
  npm install
  npm run dev
  ```
- **Notes:**
  - Add new pages/components in `pages/` and `components/`.
  - Uses Tailwind CSS for styling.

---

## 5. Blockchain (Hardhat)

- **Location:** `blockchain/`
- **Entry Point:** `contracts/AegisAudit.sol`
- **Dependencies:** `blockchain/package.json`
- **Run:**
  ```sh
  cd blockchain
  npm install
  npx hardhat node --config hardhat.config.js
  ```
- **Notes:**
  - Write/test contracts in `contracts/`.
  - Use Hardhat scripts for deployment/testing.

---

## 6. IoT (ESP32)

- **Location:** `iot/esp32_sensor.py`
- **Notes:**
  - MicroPython code for ESP32 sensor node.
  - Update WiFi and MQTT settings as needed.
  - Publishes sensor data to MQTT broker.

---

## 7. Database (PostgreSQL)

- **Location:** `database/schema.sql`
- **Notes:**
  - Schema includes tenants, sensors, and audit logs.
  - Uses PostGIS for geospatial data.
  - Apply schema to your PostgreSQL instance as needed.

---

## 8. Testing

- **Location:** `tests/`
- **Run:**
  ```sh
  pytest tests/
  ```
- **Notes:**
  - Add new tests for backend and AI modules as you develop features.
  - All backend tests must pass before PR approval.

---

## 9. Troubleshooting

- **Backend Socket Error:** Run as administrator or check firewall.
- **Frontend CSS Error:** Ensure `frontend/styles/Home.module.css` exists.
- **Hardhat Error:** Ensure Hardhat is installed locally in `blockchain/`.

---

## 10. Contribution

- Follow modular structure for new features.
- Document new endpoints, agents, or contracts.
- Keep dependencies updated in `requirements.txt` or `package.json`.
- All code must be tested and pass CI before merging.

---

## Running Tests and Coverage

To run all tests and generate a coverage report for the backend and AI modules:

```powershell
$env:PYTHONPATH="."; pytest --cov=backend --cov=ai --cov-report=term-missing
```
- This will show which lines are not covered in each file.

To run a single test file:

```powershell
$env:PYTHONPATH="."; pytest tests/test_basic.py
```

To suppress warnings for cleaner output:

```powershell
$env:PYTHONPATH="."; pytest --cov=backend --cov=ai --cov-report=term-missing -p no:warnings
```

To generate an HTML coverage report:

```powershell
$env:PYTHONPATH="."; pytest --cov=backend --cov=ai --cov-report=html
```
- Open `htmlcov/index.html` in your browser to view coverage visually.

**Note:**
- Always set `PYTHONPATH` to the project root (`.`) to ensure all modules are found.
- If you see import errors, ensure all dependencies are installed in your active environment.
- If you see test discovery errors, ensure there is no `__init__.py` in the `tests/` directory.
- For best compatibility, use `pytest-asyncio==0.21.1` with recent pytest versions.

---

## API Documentation & Usage (Day 13)

### Interactive API Docs (Swagger UI)

Aegis provides interactive API documentation using FastAPI's built-in Swagger UI.

- **Access the docs:**
  - Start the backend server:
    ```powershell
    $env:PYTHONPATH="."; uvicorn backend.main:app --reload
    ```
  - Open your browser and go to: [http://localhost:8000/docs](http://localhost:8000/docs)

- **Features:**
  - Browse all available endpoints, grouped by tags (e.g., auth, zones, sensors, research, health).
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
