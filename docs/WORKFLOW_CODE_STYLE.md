# Aegis Development Workflow & Code Style Guide

## Solo Developer Workflow

### Git Branching Strategy
```
main (production-ready code)
├── develop (integration branch for current phase)
└── feature/FEATURE_NAME (individual features)
    ├── feature/backend-fastapi-scaffold
    ├── feature/database-schema
    ├── feature/ai-vryndara-integration
    └── feature/blockchain-audit
```

**Rules:**
- Never commit directly to `main`
- Create feature branches from `develop`
- Use self-review before merging to `develop`
- Merge to `main` after phase completion and testing

### Commit Convention
```
Format: [TYPE] SCOPE: Description

Types:
- [FEAT] — New feature
- [FIX] — Bug fix
- [DOCS] — Documentation
- [REFACTOR] — Code restructuring
- [TEST] — Testing
- [CHORE] — Setup, deps, config

Examples:
[FEAT] backend: Add user authentication endpoints
[DOCS] architecture: Update system diagram
[TEST] ai: Add unit tests for analyzer agent
[FIX] frontend: Correct dashboard layout
```

### Self-Review Process
1. Create feature branch with clear name
2. Commit with meaningful messages
3. Before merging to develop:
   - [ ] Run all tests (`pytest` + `npm test`)
   - [ ] Check code style (`flake8` for Python)
   - [ ] Verify no breaking API changes
   - [ ] Update related documentation
   - [ ] Peer-review your own code (ask: "Would I understand this in 6 months?")
4. Create a self-review note with changes and rationale
5. Merge to develop
6. Update progress tracker

---

## Code Style Guides

### Python (FastAPI Backend & AI)

**Naming Conventions:**
- Classes: `PascalCase` → `UserModel`, `AegisAudit`
- Functions: `snake_case` → `get_user_data()`, `analyze_sensor_data()`
- Constants: `UPPER_SNAKE_CASE` → `DEFAULT_TIMEOUT`, `MQTT_BROKER_HOST`
- Private members: Prefix with `_` → `_internal_state`

**Style Rules:**
- Use type hints on all functions:
  ```python
  def get_zone_sensors(zone_id: str) -> List[SensorData]:
      """Retrieve all sensors for a zone."""
      pass
  ```
- Docstrings for all public functions/classes (Google style):
  ```python
  def analyze_zone_data(zone_id: str, sensor_data: Dict) -> AnalysisResult:
      """
      Analyze sensor data for anomalies.

      Args:
          zone_id: The zone identifier
          sensor_data: Dictionary of sensor readings

      Returns:
          AnalysisResult with anomalies and recommendations
      """
      pass
  ```
- Max line length: 100 characters
- Use `black` for formatting: `black backend/`

**Linting:**
```bash
# Check style
flake8 backend/ ai/

# Auto-format
black backend/ ai/

# Type checking
mypy backend/
```

### JavaScript/TypeScript (Next.js Frontend)

**Naming Conventions:**
- Components: `PascalCase` → `Dashboard.js`, `SensorCard.js`
- Functions/variables: `camelCase` → `getUserData()`, `sensorList`
- Constants: `UPPER_SNAKE_CASE` → `API_BASE_URL`, `REFRESH_INTERVAL`

**Style Rules:**
- Use functional components with hooks
- Props typed with PropTypes or TypeScript
- Meaningful component names reflecting their purpose:
  ```jsx
  // Good
  function ZoneStatusCard({ zone }) { }
  
  // Avoid
  function Card({ data }) { }
  ```
- JSDoc for non-obvious functions:
  ```javascript
  /**
   * Fetch latest sensor readings for a zone.
   * @param {string} zoneId - Zone identifier
   * @returns {Promise<Array>} Array of sensor readings
   */
  async function fetchZoneSensors(zoneId) { }
  ```

**Linting:**
```bash
# Check style
npm run lint

# Auto-fix
npm run lint:fix
```

### Solidity (Blockchain Smart Contracts)

**Naming Conventions:**
- Contracts: `PascalCase` → `AegisAudit`, `TenantFactory`
- Functions: `camelCase` → `recordEvent()`, `getEventProof()`
- Events: `PascalCase` → `EventRecorded`, `ActionExecuted`
- Constants: `UPPER_SNAKE_CASE` → `MAX_ZONE_COUNT`

**Style Rules:**
- Natspec comments for all public functions:
  ```solidity
  /// @notice Records an action to the audit trail
  /// @param zoneId The identifier of the zone
  /// @param actionHash SHA-256 hash of the action
  function recordEvent(bytes32 zoneId, bytes32 actionHash) public {
  ```
- Clear access modifiers (`public`, `internal`, `private`)
- Validate inputs before storage

---

## Testing Strategy

### Python (Backend & AI)
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=backend tests/

# Run specific test file
pytest tests/test_user_auth.py
```

**Test Structure:**
```
tests/
├── test_auth.py          — Authentication & RBAC
├── test_zones.py         — Zone management
├── test_sensors.py       — Sensor data ingestion
├── test_ai_integration.py — AI orchestrator integration
└── test_blockchain.py    — Blockchain anchoring
```

### JavaScript (Frontend)
```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- SensorCard.test.js
```

### Solidity (Smart Contracts)
```bash
cd blockchain

# Run contract tests
npx hardhat test

# Check coverage
npx hardhat coverage
```

---

## Documentation Standards

### Docstring Examples

**Python:**
```python
def get_zone_state(tenant_id: str, zone_id: str) -> ZoneState:
    """
    Retrieve the current state of a zone.

    Includes sensor readings, actuator positions, and last update timestamp.
    If offline, returns cached state with 'is_stale' flag.

    Args:
        tenant_id: Tenant identifier for access control
        zone_id: Zone identifier

    Returns:
        ZoneState object with current readings and metadata

    Raises:
        PermissionError: If user lacks access to this zone
        ValueError: If zone_id not found
    """
```

**JavaScript:**
```javascript
/**
 * Dispatch control action to a zone actuator.
 * 
 * Sends command to backend, which validates safety constraints
 * before executing. Returns immediate response with action status.
 *
 * @async
 * @param {string} zoneId - Target zone
 * @param {string} actuatorId - Target actuator
 * @param {object} commandData - Command payload (e.g., { mode: 'cool', setpoint: 22 })
 * @returns {Promise<ActionResponse>} - { actionId, status, timestamp }
 * @throws {APIError} - On validation or execution failure
 */
async function executeZoneAction(zoneId, actuatorId, commandData) {
```

---

## Weekly Standup Template

**File:** `STANDUP_WEEK_XX.md`

```markdown
# Week X Standup

## Completed
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## In Progress
- [ ] Task 4
- [ ] Task 5

## Blockers
- None (or list them)

## Notes
- Any insights, decisions, or lessons learned

## Next Week Preview
- Planned tasks
- Dependencies to watch

## Metrics
- Lines of code written: XXX
- Tests added: XX
- Bugs fixed: X
- Documentation pages: X
```

---

## Continuous Integration / Continuous Deployment (CI/CD)

### GitHub Actions (Future Setup)
```yaml
name: Tests & Lint

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Lint
        run: flake8 backend/
      - name: Run tests
        run: pytest tests/
```

---

## Dependency Management

### Python
```bash
# Create requirements
pip freeze > backend/requirements.txt

# Install from requirements
pip install -r backend/requirements.txt

# Update a package
pip install --upgrade fastapi
pip freeze > backend/requirements.txt
```

### JavaScript
```bash
# Add new dependency
npm install package-name

# Update dependencies
npm update

# Check for vulnerabilities
npm audit
```

---

## Local Development Setup

**Prerequisites:**
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+ (or use SQLite locally)
- Git

**Initial Setup:**
```bash
# Clone repo
git clone <repo_url>
cd Aegis

# Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
pip install -r ai/requirements.txt

# Node environment
cd frontend
npm install

cd ../blockchain
npm install
```

**Running Locally:**
```bash
# Terminal 1: Backend
python -m uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Blockchain (optional)
cd blockchain && npx hardhat node
```

---

## Common Commands Reference

```bash
# Testing
pytest tests/ -v
npm test

# Formatting
black backend/
npm run lint:fix

# Git workflow
git checkout -b feature/new-feature
git commit -m "[FEAT] scope: description"
git push origin feature/new-feature
# Create PR / merge to develop

# Database
sqlite3 aegis.db < database/schema.sql

# Hardhat
npx hardhat compile
npx hardhat test
npx hardhat node
```

