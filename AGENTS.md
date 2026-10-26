# AGENTS.md

## Project overview
Aegis is a decentralized digital twin framework for sovereign asset management, anti-forensic security, and enterprise infrastructure orchestration. The implementation is split across several layers:

- `backend/` — FastAPI API, routers, SQLAlchemy models, services, and database wiring
- `ai/` — orchestration and intelligence helpers for energy, weather, optimization, robotics, and sensors
- `frontend/` — Next.js dashboard and UI for tenant operations
- `blockchain/` — Hardhat/solidity contracts and deployment scripts
- `tests/` — pytest regression and integration coverage
- `docs/` — architecture and milestone guidance

For the big picture, start with [README.md](README.md), [Roadmap.md](Roadmap.md), and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

## Core working conventions
- Prefer small, targeted changes that fit the existing module boundaries.
- Keep backend logic in FastAPI routers/services, not in ad hoc scripts.
- Use the existing test structure in `tests/` and add focused regression tests when changing behavior.
- Preserve tenant-aware and security-sensitive behavior; treat audit, auth, and zone operations as high trust.
- Use offline/demo defaults unless the feature explicitly requires live external integrations.

## Local development commands
### Backend
```powershell
cd c:\Users\Mahantesh\DevelopmentProjects\Aegis
conda activate aegis
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend
```powershell
cd c:\Users\Mahantesh\DevelopmentProjects\Aegis\frontend
npm run dev
```

### Tests
```powershell
cd c:\Users\Mahantesh\DevelopmentProjects\Aegis
python -m pytest tests/ -q
```

Common project assumptions from the docs:
- Backend API is on port `8001`
- Frontend runs on `3000` or the next available port
- Default login for local dev is `admin@aegis.com` / `admin1234`
- API docs are available at `http://localhost:8001/docs`

## Important repo-specific notes
- Python target is `3.10+` in the developer guide; use the `aegis` conda environment when available.
- FastAPI is the canonical backend stack; keep endpoints and schema changes aligned with existing router patterns.
- Blockchain work belongs under `blockchain/` and related docs; do not spread contract logic into unrelated Python modules.
- Vryndara/AI features are intentionally modular; changes in `ai/` should remain focused and testable.
- If a feature depends on live services, prefer graceful fallback behavior and document the dependency clearly.

## Documentation links
- [README.md](README.md) — project overview and architecture
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — local setup and day-by-day milestones
- [Roadmap.md](Roadmap.md) — product and delivery roadmap
- [docs/README.md](docs/README.md) — docs index
- [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) — system design details

## Review checklist before finishing work
- Verify the change matches the intended module boundary.
- Run the relevant targeted tests, or the smallest relevant subset of `pytest`.
- Check whether the feature affects backend, frontend, or blockchain and update linked docs only if necessary.
- Avoid speculative rewrites or broad refactors outside the immediate task.
