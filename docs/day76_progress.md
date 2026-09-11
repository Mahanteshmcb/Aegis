# Day 76: Realistic Sensor Reading Generation

## Status: COMPLETE

Day 76 extends the Day 74 digital-twin tick engine with typed sensor profiles and threshold-aware readings.

### Implemented

- Added profiles for temperature, humidity, soil moisture, light, and pressure sensors.
- Generated readings stay within profile-specific physical ranges.
- Reading drift uses a sensor-specific step size instead of one generic random delta.
- Each sensor state now includes its unit, warning and critical threshold bands, and `reading_status` (`normal`, `warning`, or `critical`).
- Existing tenant filtering, manual control behavior, robot movement, and websocket snapshots remain unchanged.

### Validation

- Digital-twin suite: `5 passed`.
- Existing Day 74 behavior remains covered by the same suite.

### Acceptance criteria

- [x] Sensor values update on each simulation tick.
- [x] Values remain bounded by sensor type.
- [x] Threshold bands are included in emitted state.
- [x] Abnormal readings receive warning or critical status.
- [x] Existing simulation behavior remains compatible.
