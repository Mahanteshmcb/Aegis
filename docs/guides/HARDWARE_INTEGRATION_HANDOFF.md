# Hardware Integration Handoff

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
3. Backend stores telemetry in `sensor_data` and emits realtime events.
4. Frontend/clients receive `systemStatus:update` and `sensor:reading` events.
5. Hardware receives commands from `/api/v1/systems/{systemId}/control`.

## 4. WebSocket Events

- `systemStatus:update`
  - Emitted by `backend/realtime.py`
  - Payload includes aggregated system health snapshot

- `sensor:reading`
  - Emitted by `backend/realtime.py` and `backend/playback_engine.py`
  - Payload includes `sensor_id`, `timestamp`, `value`, `unit`

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
- Open WebSocket and verify `systemStatus:update` and `sensor:reading` events.

## 10. Support

- Backend contact: software owner / repository maintainer
- Hardware handoff assumes the next team can run `docker-compose up -d`
- Use the project docs in `docs/DEPLOYMENT_GUIDE.md` and `docs/INSTALLATION_GUIDE.md`
