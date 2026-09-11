# Day 83: Live Digital-Twin Health Monitoring

## Status: COMPLETE

Day 83 adds tenant-scoped health monitoring for persisted twin devices and surfaces it in the estate dashboard.

### Implemented

- Added `GET /api/v1/digital-twin/health`.
- Health summaries include overall status, health score, total devices, online devices, sensors, actuators, active actuators, and alert count.
- Health calculations are tenant-scoped.
- Estate Dashboard displays the current twin health summary.
- Day 82 actuator controls are visible in the dashboard for selected digital-twin actuators.

### Validation

- Combined Day 81-83 and digital-twin suite: `12 passed`.
- Estate dashboard lint: clean.
- Editor diagnostics: no errors in changed files.

### Acceptance criteria

- [x] Online/offline device counts are available.
- [x] Sensor alert counts are visible.
- [x] Active actuator counts are visible.
- [x] Health status is tenant-scoped.
- [x] Dashboard exposes actionable actuator controls.
