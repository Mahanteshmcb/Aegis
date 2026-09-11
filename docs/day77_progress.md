# Day 77: Digital-Twin Automation Triggers

## Status: COMPLETE

Day 77 adds deterministic sensor-driven automation to the persisted digital-twin tick engine.

### Implemented

- Automation policies can reference a source sensor by `source_device_id`.
- Rules support below, above, and inclusive threshold comparisons.
- Actuators receive configured on/off commands and optional parameters.
- Actuator output is derived from the final automation command (`on`, `start`, `open`, and `enable` are active commands).
- Warning and critical sensor readings carry alert metadata with severity, message, and source device ID.
- Existing manual and AI control modes are not overridden by automation rules.

### Example policy

```json
{
  "source_device_id": "soil-automation",
  "direction": "below",
  "threshold": 20,
  "on_command": "on",
  "off_command": "off",
  "parameters": {"flow": 24}
}
```

### Validation

- Digital-twin regression suite: `7 passed`.
- Python syntax and editor diagnostics remain clean for the changed service and tests.

### Acceptance criteria

- [x] Low soil moisture can start irrigation.
- [x] High battery or solar readings can switch a power actuator off.
- [x] Abnormal sensor values expose alert metadata.
- [x] Manual and AI control modes remain protected.
- [x] Automation decisions are deterministic and tenant-scoped through the existing tick query.
