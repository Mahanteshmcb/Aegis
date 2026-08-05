# Day 65 — Proposed Scope and Plan

Goal: Begin Day 65 by defining a small, test-driven feature set to deliver within the day. Keep scope narrow so we can implement, test, and land quickly.

Proposed feature focus (pick one):
- Option A: Audit export & filters
  - Add endpoint to export audit logs as CSV for a tenant
  - Add query filters: date range, event_type
  - Add unit/integration tests for export and filters
- Option B: User session listing & revoke
  - Add endpoint to list active sessions/tokens for a tenant
  - Add endpoint to revoke a session/token (admin)
  - Add tests for listing and revoke flows
- Option C: Sensor bulk import
  - Add endpoint to accept CSV of sensors and create entries
  - Validate input, dedupe by sensor ID, return created/updated counts
  - Tests for CSV parsing and DB side effects

Recommended next steps (for today):
1. Confirm which option to implement (A, B, or C).
2. Create tests scaffold under `tests/` for the chosen feature.
3. Implement minimal endpoint(s) in `backend/routers/` and helper functions in `backend/crud.py`.
4. Run tests, iterate until green.
5. Add small README notes and update `Roadmap.md`.

Deliverables for Day 65:
- Passing tests for the chosen feature
- `backend/routers/<new>.py` endpoint(s)
- `backend/crud.py` helpers
- `tests/test_day65_<feature>.py` with coverage for main flows

Notes:
- I will avoid large DB migrations; prefer additive columns or temporary in-memory handling for tests.
- If you prefer a different scope, tell me which feature to pick or propose an alternative.
