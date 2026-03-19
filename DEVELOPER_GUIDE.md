# Aegis Developer Guide

## Overview
Aegis is a decentralized digital twin framework for sovereign asset management, anti-forensic security, and enterprise infrastructure orchestration. The system is modular, with components for backend (FastAPI), AI orchestration, frontend (Next.js), blockchain (Hardhat), IoT (ESP32), and database (PostgreSQL).

---

## 1. Backend (FastAPI)
- **Location:** `backend/`
- **Entry Point:** `main.py`
- **Dependencies:** See `backend/requirements.txt`
- **Run:**
  ```sh
  pip install -r backend/requirements.txt
  uvicorn backend.main:app --reload
  ```
- **Endpoints:**
  - `/` — Welcome message
  - `/health` — Health check
- **Notes:**
  - Extend with new endpoints as needed for your application logic.

---

## 2. AI Orchestrator
- **Location:** `ai/`
- **Entry Point:** `orchestrator.py`
- **Dependencies:** See `ai/requirements.txt`
- **Run:**
  ```sh
  pip install -r ai/requirements.txt
  python ai/orchestrator.py
  ```
- **Notes:**
  - Uses LangChain and CrewAI for multi-agent orchestration.
  - Extend by adding new agents or tasks in `orchestrator.py`.

---

## 3. Frontend (Next.js)
- **Location:** `frontend/`
- **Entry Point:** `pages/index.js`
- **Dependencies:** See `frontend/package.json`
- **Run:**
  ```sh
  npm install
  npm run dev
  ```
- **Notes:**
  - Add new pages/components in `pages/` and `components/`.
  - Uses Tailwind CSS for styling.

---

## 4. Blockchain (Hardhat)
- **Location:** `blockchain/`
- **Entry Point:** `contracts/AegisAudit.sol`
- **Dependencies:** See `blockchain/package.json`
- **Run:**
  ```sh
  cd blockchain
  npm install
  npx hardhat node --config hardhat.config.js
  ```
- **Notes:**
  - Write and test smart contracts in `contracts/`.
  - Use Hardhat scripts for deployment/testing.

---

## 5. IoT (ESP32)
- **Location:** `iot/esp32_sensor.py`
- **Notes:**
  - MicroPython code for ESP32 sensor node.
  - Update WiFi and MQTT settings as needed.
  - Publishes sensor data to MQTT broker.

---

## 6. Database (PostgreSQL)
- **Location:** `database/schema.sql`
- **Notes:**
  - Schema includes tenants, sensors, and audit logs.
  - Uses PostGIS for geospatial data.
  - Apply schema to your PostgreSQL instance as needed.

---

## 7. Testing
- **Location:** `tests/`
- **Run:**
  ```sh
  pytest tests/
  ```
- **Notes:**
  - Add new tests for backend and AI modules as you develop features.

---

## 8. Troubleshooting
- **Backend Socket Error:** Try running as administrator or check firewall settings.
- **Frontend CSS Error:** Ensure `frontend/styles/Home.module.css` exists.
- **Hardhat Error:** Ensure Hardhat is installed locally in the `blockchain/` directory.

---

## 9. Contribution
- Follow modular structure for new features.
- Document new endpoints, agents, or contracts.
- Keep dependencies updated in respective `requirements.txt` or `package.json` files.

---

For further details, see the `README.md` or ask the project maintainer.
