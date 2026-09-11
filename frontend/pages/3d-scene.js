import React, { useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { getAuthToken } from '../utils/auth';

const EstateScene = dynamic(() => import('../components/3d/EstateScene'), {
  ssr: false,
  loading: () => <div className="flex h-full items-center justify-center text-sm text-slate-400">Loading estate scene...</div>,
});

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

const finiteNumber = (value, fallback) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
};

const normalizePosition = (entity) => {
  const fallback = Array.isArray(entity?.position) ? entity.position : [0, 1, 0];
  const x = finiteNumber(entity?.x ?? fallback[0], 0);
  const y = finiteNumber(entity?.y ?? fallback[1], 1);
  const z = finiteNumber(entity?.z ?? fallback[2], 0);
  return [x, y, z];
};

const normalizeSize = (size, index = 0) => {
  const fallback = [6 + (index % 3), 2, 6 + (index % 2)];
  const values = Array.isArray(size) ? size : fallback;
  return [0, 1, 2].map((dimension) => finiteNumber(values[dimension], fallback[dimension]));
};

const normalizeEntity = (entity, fallbackType) => {
  const rawType = typeof entity?.type === 'string' ? entity.type.toLowerCase() : '';
  const sensorTypeSet = new Set(['sensor', 'temperature', 'humidity', 'pressure', 'light', 'motion', 'air_quality', 'soil_moisture', 'flow', 'vibration', 'proximity']);
  const zoneTypeSet = new Set(['zone', 'greenhouse', 'warehouse', 'facility', 'building', 'lab', 'room']);

  let type = entity?.type || fallbackType;
  if (sensorTypeSet.has(rawType)) type = 'sensor';
  else if (zoneTypeSet.has(rawType)) type = 'zone';
  else if (entity?.robot_id || rawType === 'robot') type = 'robot';

  const position = normalizePosition(entity);
  const id = entity?.id ?? entity?.robot_id ?? entity?.sensor_id ?? entity?.zone_id ?? `${type}-${Math.random().toString(16).slice(2)}`;

  return {
    ...entity,
    id,
    type,
    name: entity?.name || `${type.charAt(0).toUpperCase()}${type.slice(1)} ${String(id).slice(-4)}`,
    status: entity?.status || 'active',
    position,
    x: position[0],
    y: position[1],
    z: position[2],
    rotation: entity?.rotation ?? 0,
    location: entity?.location || 'Main Estate',
  };
};

const buildUnifiedEstate = (robots = [], sensors = [], zones = []) => ({
  robots: robots.map((robot, idx) => normalizeEntity({
    ...robot,
    position: robot.position || [-(6 - (idx % 4)) + (idx % 4) * 4, 1, 6 - Math.floor(idx / 4) * 4],
  }, 'robot')),
  sensors: sensors.map((sensor, idx) => normalizeEntity({
    ...sensor,
    position: sensor.position || [-(7 - (idx % 5)) + (idx % 5) * 3, 2, 7 - Math.floor(idx / 5) * 3],
  }, 'sensor')),
  zones: zones.map((zone, idx) => normalizeEntity({
    ...zone,
    type: 'zone',
    name: zone.name || `Zone ${idx + 1}`,
    size: normalizeSize(zone.size, idx),
    color: zone.color || ['#00a8ff', '#10b981', '#f59e0b', '#a78bfa'][idx % 4],
    position: normalizePosition(zone),
  }, 'zone')),
});

const entityTypeMap = {
  robot: 'robots',
  sensor: 'sensors',
  zone: 'zones',
};

const fallbackRobots = [
  { id: 'sim-robot-1', type: 'robot', name: 'Field Rover A', status: 'active', position: [-8, 1, 4], x: -8, y: 1, z: 4 },
  { id: 'sim-robot-2', type: 'robot', name: 'Inspection Bot', status: 'charging', position: [8, 1, 4], x: 8, y: 1, z: 4 },
];

const fallbackSensors = [
  { id: 'sim-sensor-1', type: 'sensor', name: 'Thermal Node', status: 'active', position: [-6, 1, -4], x: -6, y: 1, z: -4, sensor_type: 'temperature', value: 24.5 },
  { id: 'sim-sensor-2', type: 'sensor', name: 'Moisture Node', status: 'active', position: [6, 1, -4], x: 6, y: 1, z: -4, sensor_type: 'humidity', value: 63 },
  { id: 'sim-sensor-3', type: 'sensor', name: 'Security Beacon', status: 'idle', position: [0, 1, 8], x: 0, y: 1, z: 8, sensor_type: 'motion', value: 0 },
];

const fallbackZones = [
  { id: 'sim-zone-1', type: 'zone', name: 'Crop Field A', status: 'secure', position: [-10, 0, -8], x: -10, y: 0, z: -8, size: [14, 2, 12], color: '#10b981' },
  { id: 'sim-zone-2', type: 'zone', name: 'Livestock Zone', status: 'warning', position: [10, 0, -8], x: 10, y: 0, z: -8, size: [12, 2, 12], color: '#f97316' },
  { id: 'sim-zone-3', type: 'zone', name: 'Drone Pad', status: 'secure', position: [0, 0, 12], x: 0, y: 0, z: 12, size: [10, 2, 10], color: '#38bdf8' },
];

export default function ScenePage() {
  const [robots, setRobots] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [zones, setZones] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState({ name: '', type: 'sensor', location: 'Main Estate', sensorType: 'temperature' });

  const refreshSceneData = async () => {
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      const [robotsRes, sensorsRes, zonesRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/robotics/active`, { headers }).then((response) => (response.ok ? response.json() : [])).catch(() => []),
        fetch(`${API_URL}/api/v1/sensors`, { headers }).then((response) => (response.ok ? response.json() : [])).catch(() => []),
        fetch(`${API_URL}/api/v1/zones`, { headers }).then((response) => (response.ok ? response.json() : [])).catch(() => []),
      ]);

      const hasLiveData = (robotsRes?.length || sensorsRes?.length || zonesRes?.length);
      const normalized = buildUnifiedEstate(
        hasLiveData ? robotsRes : fallbackRobots,
        hasLiveData ? sensorsRes : fallbackSensors,
        hasLiveData ? zonesRes : fallbackZones,
      );

      setRobots(normalized.robots);
      setSensors(normalized.sensors);
      setZones(normalized.zones);
      setMessage('');
    } catch (error) {
      console.error('Failed to fetch estate scene data', error);
      setRobots(fallbackRobots.map((item) => normalizeEntity(item, 'robot')));
      setSensors(fallbackSensors.map((item) => normalizeEntity(item, 'sensor')));
      setZones(fallbackZones.map((item) => normalizeEntity(item, 'zone')));
      setMessage('Unable to reach the live estate API. Showing a synchronized simulated estate view.');
    }
  };

  useEffect(() => {
    refreshSceneData();
  }, []);

  const entityList = useMemo(() => [...robots, ...sensors, ...zones], [robots, sensors, zones]);

  const handleCreateEntity = async (event) => {
    event.preventDefault();
    const token = getAuthToken();
    const type = draft.type;
    const endpoint = entityTypeMap[type] || 'sensors';

    const payload = {
      name: draft.name || `${type.charAt(0).toUpperCase()}${type.slice(1)} Instance`,
      type: type === 'sensor' ? (draft.sensorType || 'temperature') : type,
      location: draft.location || 'Main Estate',
      status: 'active',
      position: [0, 1, 0],
      x: 0,
      y: 1,
      z: 0,
    };

    try {
      const response = await fetch(`${API_URL}/api/v1/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || `Failed to create ${type}`);
      }

      setDraft({ name: '', type: 'sensor', location: 'Main Estate', sensorType: 'temperature' });
      setMessage(`${type.charAt(0).toUpperCase()}${type.slice(1)} created successfully.`);
      await refreshSceneData();
    } catch (error) {
      console.error('Failed to create entity', error);
      setMessage(error.message || 'Failed to create entity.');
    }
  };

  const handleSaveEntity = async (event) => {
    event.preventDefault();
    if (!selectedEntity) return;

    const type = selectedEntity.type;
    const endpoint = entityTypeMap[type];
    if (!endpoint) return;

    const token = getAuthToken();
    const payload = {
      ...selectedEntity,
      name: selectedEntity.name,
      status: selectedEntity.status || 'active',
      location: selectedEntity.location || 'Main Estate',
      x: Number(selectedEntity.x),
      y: Number(selectedEntity.y),
      z: Number(selectedEntity.z),
      position: [Number(selectedEntity.x), Number(selectedEntity.y), Number(selectedEntity.z)],
    };

    try {
      setSaving(true);
      const response = await fetch(`${API_URL}/api/v1/${endpoint}/${selectedEntity.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || `Failed to update ${type}`);
      }

      setMessage(`${type.charAt(0).toUpperCase()}${type.slice(1)} updated.`);
      await refreshSceneData();
    } catch (error) {
      console.error('Failed to update entity', error);
      setMessage(error.message || 'Failed to update entity.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteEntity = async () => {
    if (!selectedEntity) return;

    const type = selectedEntity.type;
    const endpoint = entityTypeMap[type];
    if (!endpoint) return;

    const confirmed = window.confirm(`Delete ${selectedEntity.name}?`);
    if (!confirmed) return;

    const token = getAuthToken();

    try {
      const response = await fetch(`${API_URL}/api/v1/${endpoint}/${selectedEntity.id}`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || `Failed to delete ${type}`);
      }

      setSelectedEntity(null);
      setMessage(`${type.charAt(0).toUpperCase()}${type.slice(1)} deleted.`);
      await refreshSceneData();
    } catch (error) {
      console.error('Failed to delete entity', error);
      setMessage(error.message || 'Failed to delete entity.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-3xl border border-cyan-500/20 bg-slate-900/80 p-5 shadow-[0_0_35px_rgba(34,211,238,0.08)] backdrop-blur-xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.45em] text-cyan-300">AEGIS ESTATE BUILDER</p>
              <h1 className="mt-2 text-3xl font-bold text-cyan-200">3D Estate Scene</h1>
              <p className="mt-1 text-sm text-slate-300">Unified view for zones, sensors, robotics, and estate devices in the same operating environment.</p>
            </div>
            <button
              onClick={refreshSceneData}
              className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-200 transition hover:bg-cyan-500/20"
            >
              Refresh Scene
            </button>
          </div>
        </div>

        {message && (
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
            {message}
          </div>
        )}

        <div className="grid gap-6 xl:grid-cols-[1.6fr_0.7fr]">
          <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/80 p-3 shadow-2xl shadow-slate-950/30">
            <div className="h-[680px] min-h-[420px]">
              <EstateScene
                robots={robots}
                sensors={sensors}
                zones={zones}
                selectedEntity={selectedEntity}
                viewMode="realworld"
                lightIntensity={1.1}
                autoRotate={false}
                onEntitySelect={(entity) => setSelectedEntity(normalizeEntity(entity, entity?.type || 'sensor'))}
              />
            </div>
          </div>

          <aside className="space-y-6">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-4">
              <h2 className="mb-3 text-lg font-semibold text-cyan-200">Create Asset</h2>
              <form onSubmit={handleCreateEntity} className="space-y-3 text-sm">
                <label className="block">
                  <span className="mb-1 block text-slate-300">Type</span>
                  <select
                    value={draft.type}
                    onChange={(event) => setDraft((prev) => ({ ...prev, type: event.target.value }))}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                  >
                    <option value="sensor">Sensor</option>
                    <option value="robot">Robot</option>
                    <option value="zone">Zone</option>
                  </select>
                </label>

                {draft.type === 'sensor' && (
                  <label className="block">
                    <span className="mb-1 block text-slate-300">Sensor Type</span>
                    <select
                      value={draft.sensorType}
                      onChange={(event) => setDraft((prev) => ({ ...prev, sensorType: event.target.value }))}
                      className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                    >
                      <option value="temperature">Temperature</option>
                      <option value="humidity">Humidity</option>
                      <option value="motion">Motion</option>
                      <option value="pressure">Pressure</option>
                      <option value="light">Light</option>
                    </select>
                  </label>
                )}

                <label className="block">
                  <span className="mb-1 block text-slate-300">Name</span>
                  <input
                    value={draft.name}
                    onChange={(event) => setDraft((prev) => ({ ...prev, name: event.target.value }))}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                    placeholder="Main sensor / rover / zone"
                  />
                </label>

                <label className="block">
                  <span className="mb-1 block text-slate-300">Location</span>
                  <input
                    value={draft.location}
                    onChange={(event) => setDraft((prev) => ({ ...prev, location: event.target.value }))}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                    placeholder="Main Estate"
                  />
                </label>

                <button type="submit" className="w-full rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-cyan-400">
                  Create {draft.type}
                </button>
              </form>
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-4">
              <h2 className="mb-3 text-lg font-semibold text-cyan-200">Selected Asset</h2>
              {selectedEntity ? (
                <form onSubmit={handleSaveEntity} className="space-y-3 text-sm">
                  <label className="block">
                    <span className="mb-1 block text-slate-300">Name</span>
                    <input
                      value={selectedEntity.name || ''}
                      onChange={(event) => setSelectedEntity((prev) => ({ ...prev, name: event.target.value }))}
                      className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                    />
                  </label>

                  <div className="grid grid-cols-3 gap-2">
                    <label className="block">
                      <span className="mb-1 block text-slate-300">X</span>
                      <input type="number" value={selectedEntity.x ?? 0} onChange={(event) => setSelectedEntity((prev) => ({ ...prev, x: Number(event.target.value) }))} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-slate-100" />
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-slate-300">Y</span>
                      <input type="number" value={selectedEntity.y ?? 0} onChange={(event) => setSelectedEntity((prev) => ({ ...prev, y: Number(event.target.value) }))} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-slate-100" />
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-slate-300">Z</span>
                      <input type="number" value={selectedEntity.z ?? 0} onChange={(event) => setSelectedEntity((prev) => ({ ...prev, z: Number(event.target.value) }))} className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-slate-100" />
                    </label>
                  </div>

                  <label className="block">
                    <span className="mb-1 block text-slate-300">Status</span>
                    <input
                      value={selectedEntity.status || ''}
                      onChange={(event) => setSelectedEntity((prev) => ({ ...prev, status: event.target.value }))}
                      className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1 block text-slate-300">Location</span>
                    <input
                      value={selectedEntity.location || ''}
                      onChange={(event) => setSelectedEntity((prev) => ({ ...prev, location: event.target.value }))}
                      className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                    />
                  </label>

                  <div className="flex gap-2">
                    <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-60">
                      {saving ? 'Saving...' : 'Save'}
                    </button>
                    <button type="button" onClick={handleDeleteEntity} className="flex-1 rounded-lg bg-red-500 px-4 py-2 font-semibold text-white transition hover:bg-red-400">
                      Delete
                    </button>
                  </div>
                </form>
              ) : (
                <p className="text-sm text-slate-400">Select a robot, sensor, or zone in the scene to edit or remove it.</p>
              )}
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-4">
              <h3 className="mb-3 text-sm uppercase tracking-[0.25em] text-slate-400">Estate Inventory</h3>
              <div className="space-y-2 text-sm text-slate-300">
                <div className="flex items-center justify-between rounded-xl bg-slate-950/70 px-3 py-2">
                  <span>Robots</span>
                  <span className="font-semibold text-cyan-300">{robots.length}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-950/70 px-3 py-2">
                  <span>Sensors</span>
                  <span className="font-semibold text-emerald-300">{sensors.length}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-950/70 px-3 py-2">
                  <span>Zones</span>
                  <span className="font-semibold text-violet-300">{zones.length}</span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

