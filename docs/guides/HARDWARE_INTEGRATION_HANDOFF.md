# Hardware Integration Handoff

## Phase 6: low-cost Arduino pilot (in progress; not yet commissioned)

For the one-command Windows startup and the current limits of one-device
onboarding, see the [local demo startup guide](LOCAL_DEMO_STARTUP.md).

### Available pilot inventory

Confirmed by the owner: Arduino Mega, connector cable, male/female jumper
connectors, built-in LED, and a general-purpose 9 V battery. A Windows laptop
is available. Do not assume that a breadboard, external LED, resistor, sensor,
or regulated power supply is available. Recheck the physical kit before wiring.

### Safe first bring-up

1. **Power only by USB for this first test.** Leave the 9 V battery
   disconnected. Do not connect it to the Mega's 5 V pin, any GPIO pin, or the
   built-in LED. A rectangular 9 V battery is not needed for this USB-powered
   test and is a poor choice for powering later projects with motors or other
   substantial loads.
2. No jumper wires are needed for the built-in LED test. Keep relays, motors,
   pumps, mains-voltage equipment, and external power wiring disconnected.
3. The starter firmware is
   [arduino_mega_led.ino](../../hardware/arduino_mega_led/arduino_mega_led.ino).
   In Arduino IDE, select **Arduino Mega or Mega 2560**, select the port
   belonging to the board, upload the sketch, then open Serial Monitor at
   **115200 baud**. The sketch accepts Newline, CR, or CRLF line endings.
4. Send `AEGIS/1,test-001,mega-onboard-led-01,LED_ON`. Expect
   `AEGIS/1,test-001,OK,ON` and the board's built-in LED to turn on. The
   response reflects the firmware's GPIO output readback, not an independent
   optical sensor. Send
   `AEGIS/1,test-002,mega-onboard-led-01,LED_OFF`; expect
   `AEGIS/1,test-002,OK,OFF` and the LED to turn off.
5. Test safe rejection: `AEGIS/1,test-003,mega-onboard-led-01,RELAY_ON`
   must return `AEGIS/1,test-003,ERROR,unsupported_command` and must not
   switch on an output. This firmware accepts only `LED_ON` and `LED_OFF`.
6. Record the actual board port, firmware upload result, both LED command
   results, and rejection result in the Phase 6 progress log below. Do not
   record a pass unless observed on the physical board.
7. The local gateway is a one-device pilot and binds only to `127.0.0.1`; it
   is not a remote or multi-site gateway. Do not expose its HTTP port to a
   network. Stop Arduino IDE Serial Monitor before starting the gateway,
   because Windows allows only one process to own COM9 at a time.

### Connect this pilot gateway to Aegis

1. Install the Python serial dependency in the `aegis` environment:
   `python -m pip install pyserial==3.5`.
2. Generate a private shared secret from the repository root:
   `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
   Put the generated value in the root `.env` as
   `AEGIS_ARDUINO_GATEWAY_TOKEN=<your-generated-value>`. Do not commit or share
   the token. The backend and gateway read this same setting; the gateway
   rejects requests without it.
3. Restart the backend so it registers its opt-in serial adapter:
   `python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001`.
   The default gateway URL is `http://127.0.0.1:8765`.
4. Close Serial Monitor. In a second terminal, activate the `aegis` Conda
   environment and run [start_arduino_gateway.bat](../../start_arduino_gateway.bat) (or
   `python -m hardware.arduino_mega_led.gateway --port COM9`). Keep that
   terminal open. The gateway opens the selected port at 115200 baud and lets
   the Mega finish its reset/startup before accepting commands. If the cable is
   removed, reconnect it and retry the command; the gateway reopens the serial
   connection and retries once without restarting its process. If Windows
   assigns a different COM port, the gateway tries to find a single Mega by
   its USB identity; if it cannot identify it unambiguously, set
   `AEGIS_ARDUINO_SERIAL_PORT` to the new COM port and restart the gateway.
5. Check `http://127.0.0.1:8765/health`; it should report the gateway process
   running and whether its serial port is open. This health response is not
   proof that the board is still physically connected; a real command must
   receive a matching board acknowledgement.
6. In the 3D Scene, choose **Add asset** and create an **Actuator** with device
   ID `mega-onboard-led-01`, device type `onboard_led`, and connection
   **Arduino Mega onboard LED (USB gateway)**. The form sets it to manual
   control. This is a separate physical identity; do not change a simulated
   device into hardware or reuse a simulator ID.
7. Select the new actuator and use **on** and **off**. A successful response
   includes a matching board acknowledgement and updates the recorded output
   state. A timeout, rejected command, wrong identity, or stopped gateway must
   return an error rather than a success-shaped response.

The gateway and backend must run on the same computer for this pilot. A future
remote site needs its own local gateway and a deliberately secured gateway-to-
backend channel (for example TLS plus managed device identity); this local
loopback HTTP pilot must not be copied as a network-facing design. The gateway
is limited to this one registered Mega ID and LED on/off commands.

If the gateway stops while the Mega remains powered, the firmware keeps its
last LED output; this firmware does not have a heartbeat or automatic
disconnect fail-safe. Send **off** before stopping the gateway and verify the
LED is off. That limitation must be addressed before controlling anything
other than the built-in demo LED.

### Phase 6 progress log

Keep this table as the source of truth; change a status to **Verified** only
after recording direct evidence. Add a date and result in the evidence column
when a physical step is completed.

| Step                                                                   | Status                   | Evidence / next action                                                                                                                                                                  |
| ---------------------------------------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pilot kit inventoried                                                  | Recorded                 | Owner reports Mega, connector cable, male/female jumper connectors, onboard LED, 9 V battery.                                                                                           |
| Safe onboard-LED firmware drafted                                      | Ready for board test     | Starter sketch added; host C++ syntax check passed. Arduino board-specific build is not available in this development environment.                                                      |
| Firmware uploaded to physical board                                    | Owner-reported success   | Owner reports successful compile/upload on COM9; sketch initializes the onboard LED off.                                                                                                |
| USB serial link identified                                             | Owner-reported verified  | Board reported on COM9; Serial Monitor returned the expected protocol responses.                                                                                                        |
| LED ON/OFF and invalid-command rejection                               | Serial protocol verified | On 2026-10-26, owner reported `test-001,OK,ON`, `test-002,OK,OFF`, and `test-003,ERROR,unsupported_command` from the board. Physical LED appearance was not separately confirmed. |
| Serial gateway translates Aegis commands and waits for acknowledgement | Owner-reported working | Owner reports the Aegis/gateway/Mega control path is working. Record direct command and acknowledgement evidence before treating this as independently verified. |
| Backend serial adapter registered safely | Owner-reported configured | Owner reports gateway setup is working. Only loopback HTTP and the single pilot device are supported. |
| Physical device registered and mapped to twin | Owner-reported working | Owner reports the physical control workflow is working; retain `mega-onboard-led-01` as a distinct physical identity. |
| USB disconnect/reconnect and COM-port reassignment                    | Owner-reported success   | On 2026-10-26, owner reports unplugging/reconnecting the Mega worked, including after plugging it into a different USB port. The gateway reconnected without a process restart.        |
| Telemetry, audit, disconnect, and safe-off tests                       | In progress              | USB reconnect is owner-reported as working. Still verify audit events, command failure while unplugged, retry after reconnect, and safe output behavior. This LED-only pilot has no sensor. |

The owner reports the expected ON, OFF, and unsupported-command responses
from the standalone sketch and reports that the Aegis/gateway/Mega control
path works. These are owner-reported results, not independently observed
hardware validation in this environment. The board's RX indicator can flash
when serial bytes arrive; only the built-in LED marked `L` (or the LED at pin
13) is the output controlled by this sketch. Audit verification and
offline/safety testing remain open Phase 6 work. The owner also reports that
USB unplug/replug worked when reconnecting through a different port. This
reconnection result is not independently tested here. This LED-only pilot has
no sensor for physical telemetry. The 3D scene's inferred device positions
are planning placements, not surveyed coordinates.

## 1. API Endpoint Summary

### Auth

- `POST /api/v1/auth/login`

  - Request: `{ "email": "user@example.com", "password": "secret" }`
  - Response: `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer" }`
- `POST /api/v1/auth/refresh`

  - Request: `{ "refresh_token": "..." }`
  - Response: new access and refresh tokens
- `GET /api/v1/auth/me`

  - Header: `Authorization: Bearer <access_token>`
  - Response: user profile

### Estate / Dashboard

- `GET /api/v1/estate/status`
- `GET /api/v1/estate/timeline`

### Sessions

- `GET /api/v1/sessions`
- `POST /api/v1/sessions/{session_id}/revoke`

### Alerts

- `POST /api/v1/alerts`
- `GET /api/v1/alerts`
- `POST /api/v1/alerts/{alert_id}/acknowledge`
- `POST /api/v1/alerts/{alert_id}/resolve`

### Sensor Ingestion

- `POST /api/v1/sensors/ingest`
  - Payload: `sensor_id`, `timestamp`, `value`, `type`, `unit`, `tenant_id`
- `POST /api/v1/digital-twin/devices/{device_id}/telemetry`
  - Authenticated and tenant-scoped. Accepts `device_id`, `tenant_id`, `zone_id`, `value`, `unit`, `sensor_type`, and `sampled_at`.
  - The selected adapter validates device, tenant, and zone identity before the reading enters canonical digital-twin telemetry history.

### System Control

- `POST /api/v1/systems/{systemId}/control`
  - Body: `{ "command": "power_on" | "power_off" | "reset" | "override", "payload": {...} }`

## 2. Data Ingestion Format

### Standard Sensor Payload

```json
{
  "sensor_id": "sensor-123",
  "tenant_id": 1,
  "timestamp": "2026-07-19T12:34:56Z",
  "type": "temperature",
  "value": "22.7",
  "unit": "C"
}
```

### Telemetry Playback Input

- Playback engine reads from `sensor_data` and emits live socket events.
- Use the existing `backend/playback_engine.py` for replaying stored telemetry.

## 3. Command Response Flow

1. Hardware sends state update to backend via REST or gRPC.
2. Backend validates JWT and tenant scope.
3. The digital-twin API validates tenant ownership and persists the canonical device state and telemetry snapshot.
4. Frontend/clients receive tenant-scoped `digital_twin:device_update` events; alert episode transitions use `digital_twin:alert` and `digital_twin:alert_cleared`.
5. Operator commands are authorized and persisted through `POST /api/v1/digital-twin/devices/{device_id}/control`. A physical transport adapter must still deliver that command to hardware and acknowledge its result.

### Adapter selection and delivery

- Digital-twin device snapshots include `adapter_type`: `simulation` (the default), `mqtt`, `rest`, `serial`, or `grpc`.
- Set `adapter_type` when creating a device or update it through `PUT /api/v1/digital-twin/devices/{device_id}`. Switching to a hardware adapter disables software simulation for that device.
- All transports use the same command envelope (`aegis.device-command.v1`) and control route. A successful transport publish/write is reported as accepted, not device-confirmed, unless the adapter receives an explicit device acknowledgement.
- The backend registers only the simulation adapter by default. Hardware commands return HTTP `503` until an application startup integration registers the corresponding injected MQTT/REST/serial/gRPC client. Transport credentials and device endpoints are deliberately not stored on device rows.
- Hardware telemetry uses the authenticated, tenant-scoped twin telemetry route and the existing durable telemetry history/retention pipeline. Do not expose this user-session endpoint directly to an untrusted device network; production gateways need a properly managed service identity before deployment.
- Adapter transport tests use fake clients only. No broker, serial hardware, physical endpoint, or robot controller has been commissioned or validated in this environment.

## 3a. Software-only resource and robotics simulation

- New default-tenant setup seeds demo water collection/purification/irrigation/recycling, waste containers/compost/recycling, and warehouse facilities/inventory only when each domain is empty. Seeded rows are named `Demo ...` or tagged with a `SIM-DEMO-...` lot/pile ID.
- `POST /api/v1/water/simulation/advance`, `POST /api/v1/waste/simulation/advance`, and `POST /api/v1/storage/simulation/advance` accept `{ "step_hours": 24 }`. These are explicit, tenant-scoped simulation steps; they do not run automatically.
- Simulation results identify generic, uncalibrated assumptions. Water simulation never writes synthetic quality readings; the quality timeline remains reserved for sensor/manual readings. Waste simulation persists sorting and processing logs. Storage simulation changes only the seeded `SIM-DEMO-...` inventory lots.
- Robot control in the current environment uses the local Aegis gRPC fleet simulator. `GET /api/v1/robotics/integrations` reports the fleet gRPC connection, Vryndara kernel gRPC status, and ROS 2 readiness separately.
- The Vryndara kernel client is configured with `VRYNDARA_HOST`, `VRYNDARA_PORT`, and `VRYNDARA_TIMEOUT`; the Vryndara endpoint must be running for routed commands to leave fallback mode.
- ROS 2 physical control is intentionally disabled until the ROS 2 runtime, ordered robot model, topics/actions, coordinate frame, and safety limits are known. A successful simulator gRPC call is not evidence of physical actuation.

## 4. WebSocket Events

- `digital_twin:device_update`
  - Emitted from persisted `DigitalTwinDevice` state in the canonical simulation path.
  - Payload includes tenant, zone, position, status, current state, and update timestamp.
- `digital_twin:alert`
  - Emitted when a sensor alert episode begins or escalates.
- `digital_twin:alert_cleared`
  - Emitted when the sensor returns to normal.
- Historical playback is a separate workflow; its events are not live device telemetry.

## 5. Database Schema

### Relevant tables

- `users`
- `tenants`
- `sessions`
- `audit_logs`
- `sensor_data`
- `system_alerts`
- `energy_policies`
- `scheduled_robotic_tasks`

### Sensor data row

- `sensor_id` (FK)
- `timestamp`
- `value`
- `unit`
- `created_at`

## 6. Error Codes

- `200` OK
- `201` Created
- `400` Bad Request
- `401` Unauthorized
- `403` Forbidden
- `404` Not Found
- `422` Validation Error
- `500` Internal Server Error

## 7. Rate Limits

- No dedicated throttle middleware yet.
- Recommend enforcing per-tenant limits in fronting proxy.
- For hardware clients, keep calls below 5 req/sec per device.

## 8. Security

- JWT format: `Bearer <access_token>`
- Admin-only endpoints require role `admin` or `superadmin`.
- Use `tenant_id` to scope all data operations.

## 9. Testing

- Verify login and token refresh.
- Confirm admin can list sessions and revoke them.
- Send sample sensor payloads to ingestion endpoint.
- Open an authenticated WebSocket and verify tenant-scoped twin updates and alert start/clear transitions.

## 10. Support

- Backend contact: software owner / repository maintainer
- Hardware handoff assumes the next team can run `docker-compose up -d`
- Use the project docs in `docs/DEPLOYMENT_GUIDE.md` and `docs/INSTALLATION_GUIDE.md`
