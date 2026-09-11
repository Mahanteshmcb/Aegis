# Aegis Finalized Demo Build

**Build date:** 2026-08-28  
**Project phase:** Phase 2, software-first realtime digital twin  
**Demo status:** Ready for guided demonstration

## 1. Demo Purpose

Aegis demonstrates a customizable smart-estate digital twin for monitoring, simulation, automation, and future hardware integration. The demo represents an estate that can contain homes, farms, gardens, laboratories, workshops, server rooms, infrastructure, sensors, devices, and autonomous robots.

The same platform can be configured for different customer estate organizations. Estate data is tenant-scoped, while the 3D environment provides the visual operating layer.

## 2. Start The Demo

### Backend

From the repository root:

```powershell
conda activate aegis
$env:SERVER_PORT=8001
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Backend URLs:

- API: http://localhost:8001
- API documentation: http://localhost:8001/docs
- Health check: http://localhost:8001/api/v1/health

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend normally runs at http://localhost:3000. Next.js selects the next available port if that port is busy.

### Demo account

- Email: `admin@aegis.com`
- Password: `admin1234`

The local database is `aegis.db`. The database initializer creates the default tenant and demo account when required.

## 3. Demonstration Route

Recommended sequence:

1. Open the main dashboard and sign in.
2. Open `/estate-dashboard` to show estate health, zones, sensors, alerts, and operational controls.
3. Select a zone, sensor, or robot to inspect its status and available actions.
4. Dispatch a robot task or emergency stop from the permitted control panel.
5. Open `/3d-scene` to use the environment workspace.
6. Place a scene entity by selecting a point on the ground.
7. Select an entity from the scene or hierarchy and edit its name, type, model, position, or rotation.
8. Save the entity and confirm that the change is persisted.
9. Open `/dashboard-3d` for the realtime digital-twin view.
10. Open `/system-control` for health, backup, synchronization, and fleet controls.

## 4. 3D Environment

The current visual environment uses downloaded CC0 assets from Kenney Nature Kit. Assets are stored in:

`frontend/public/assets/kenney/nature-kit`

The environment includes:

- Trees and perimeter vegetation
- Bushes, flowers, and rocks
- Crop rows and garden areas
- Fences and paths
- Bridges and landscape details
- Daylight sky, sunlight, ambient fill, shadows, and open-world ground

The shared asset layer is implemented in:

`frontend/components/3d/EstateEnvironmentAssets.js`

It is used by the estate visualization, digital-twin scene, and 3D editor.

The first realistic architectural layer is the Poly Haven Modular Factory Facade, a CC0 glTF asset used for the R&D/workshop area. Its geometry, textures, and license record are stored under `frontend/public/assets/polyhaven/modular_factory_facade`. The loader is isolated in `frontend/components/3d/RealisticArchitectureAsset.js`; replace its `FACTORY_URL` and scale with a customer-owned Blender `.glb` without changing the Aegis data or automation layers.

## 5. 3D Editor Capabilities

The `/3d-scene` route is the environment workspace for administrator-led configuration.

Current capabilities:

- Full-height responsive 3D workspace
- Scene hierarchy listing
- Ground-point placement
- Entity selection and hover state
- Entity property editing
- Position and rotation editing
- Model filename selection and persistence
- Entity deletion
- Center and follow camera controls
- Realtime scene entity updates through Socket.IO
- Customer-specific scene data through tenant-aware APIs

Scene entities are persisted in the `scene_entities` table. The selected model is persisted by the `model` field added in migration `0009_scene_entity_model.py`.

The customer layout foundation is available through:

- `GET /api/v1/estate-layout`
- `POST /api/v1/estate-layout`
- `GET /api/v1/estate-layout/{estate_id}/tree`
- `POST /api/v1/estate-layout/{estate_id}/nodes`

Layout nodes support `zone`, `building`, `room`, and `section` types. Parent validation prevents invalid nesting, and the 3D editor displays the configured estate tree for the current tenant.

## 6. Estate Dashboard Capabilities

The `/estate-dashboard` route is the operational view for authorized users.

Current capabilities:

- Estate system health summary
- Zone and sensor counts
- Live sensor readings
- Robot fleet status
- Alert and notification display
- Predictive maintenance presentation
- System-specific dashboard cards
- Robot task dispatch
- Robot emergency stop
- Zone operation scheduling
- Realtime Socket.IO connection status
- Auto-refresh and manual refresh
- 3D estate visualization with entity selection

Role intent:

- **Admin:** configure estate objects, manage users, and perform administrative controls.
- **Operator:** monitor systems and operate permitted robots, sensors, and workflows.
- **Auditor:** inspect estate state, telemetry, and audit information.
- **Viewer:** read-only monitoring where enforced by the endpoint.

## 7. Simulation And Realtime Backend

The Day 74 simulation foundation is implemented with:

- `backend/models/digital_twin.py`
- `backend/services/digital_twin.py`
- `backend/routers/digital_twin.py`
- `backend/alembic/versions/0008_digital_twin_devices.py`

Available endpoints:

- `GET /api/v1/digital-twin/devices`
- `POST /api/v1/digital-twin/devices`
- `POST /api/v1/digital-twin/tick`

Supported virtual device kinds:

- `sensor`
- `robot`
- `actuator`

The realtime service advances enabled digital-twin devices and publishes `digital_twin:device_update` events. Sensors receive bounded changing values, robots move within bounded coordinates, and actuators expose simulated output state.

Each digital-twin device has a persisted `control_mode`: `manual`, `automation`, or `ai`. Manual commands are sent through `POST /api/v1/digital-twin/devices/{device_id}/control`; automation and AI policy data are retained in `automation_policy` for future rule and agent decisions. This separates the visual GLB from project behavior and allows each customer estate to use different control policies.

## 8. Estate Organization Model

The default demonstration estate uses the reference plan measurement of **135 m x 90 m = 12,150 m²**, which is approximately **3.0023 acres**. The 3D editor uses metres for placement coordinates and provides a measured template through `POST /api/v1/estate-layout/template/three-acre`.

The template includes vegetable garden, fruit orchard, research/workshop, grains/rice, and residential zones. The research/workshop zone includes an R&D laboratory building with software development, additive manufacturing, and server/control rooms.

The target customer-customizable structure is:

```text
Customer Tenant
  Estate
    Zones
      Buildings
        Rooms / Sections
          Sensors
          Devices
          Servers
      Farms
      Gardens
      Laboratories
      Workshops
      Infrastructure
      Robots and automated tools
```

The current implementation provides the estate, zone, building, room, section, scene entity, sensor, robot, and device foundations. Full server inventory and richer room-level placement are planned extensions of the same tenant-scoped model.

## 9. Systems View

Use `/system-control` for operational controls and `/system-analytics` for performance metrics.

The system layer covers:

- Backend health
- Database connectivity
- Realtime services
- Robot fleet controls
- Backup and synchronization operations
- Estate system status
- Audit and compliance services
- Energy, water, climate, security, laboratory, storage, and waste modules

## 10. Asset Licensing Policy

Only use assets whose license permits commercial modification and distribution.

Approved current source:

- Kenney Nature Kit: Creative Commons Zero (CC0)

For future assets, retain a manifest containing:

- Asset name
- Source URL
- Creator
- License
- Download date
- Local file path
- Modification notes

Do not add Unreal Engine Marketplace, Quixel, MetaHuman, or other UE-only assets to the web build unless the individual license explicitly permits standalone web distribution and company use.

## 11. Validation

Frontend production build:

```powershell
cd frontend
npm run build
```

Backend focused digital-twin test:

```powershell
python -m pytest tests/test_day74_digital_twin.py -q
```

Backend syntax/import check:

```powershell
python -m py_compile backend/models/digital_twin.py backend/services/digital_twin.py backend/routers/digital_twin.py
```

The current frontend build compiles all 43 pages successfully. The focused Day 74 test passes. Existing repository-wide test failures from older Day 65-68 areas should be resolved separately before production release.

## 12. Known Demo Limitations

- The current estate environment combines a realistic CC0 architecture asset with modular landscape and procedural infrastructure; it is not yet one single photorealistic Blender estate file.
- Room and section hierarchy is not yet represented as a dedicated backend model.
- Some dashboard system cards still use demonstration values where live subsystem data is unavailable.
- Full admin authorization for every scene edit should be hardened at the API boundary before external deployment.
- The local SQLite demo database is suitable for demonstration, not multi-customer production scale.
- Production deployment should use PostgreSQL, HTTPS, managed secrets, backups, and a reviewed asset license manifest.

## 13. Next Build Priorities

1. Add device and server management screens to the 3D editor.
2. Add transform and property editing for hierarchy nodes.
3. Add explicit admin/operator permissions to scene and digital-twin mutation endpoints.
4. Bind every visible 3D object to a persistent entity ID and live telemetry state.
5. Add customer estate templates and import/export of scene layouts.
6. Replace remaining mock dashboard values with subsystem APIs.
7. Add browser-based smoke tests for login, 3D editing, robot control, and realtime updates.
8. Optimize downloaded GLBs with compression, level of detail, and lazy loading.
