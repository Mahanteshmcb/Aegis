import { useCallback, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import { getAuthToken, getRefreshToken, setAuthToken, setRefreshToken } from '../utils/auth';
import { refreshAuthToken } from '../utils/api';
import { initializeSocket } from '../utils/socketClient';

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
  const source = entity?.position;
  const position = Array.isArray(source)
    ? { x: source[0], y: source[1], z: source[2] }
    : source && typeof source === 'object'
      ? source
      : {};
  const x = finiteNumber(entity?.x ?? position.x, 0);
  const y = finiteNumber(entity?.y ?? position.y, 1);
  const z = finiteNumber(entity?.z ?? position.z, 0);
  return [x, y, z];
};

const normalizeSize = (size, index = 0) => {
  const fallback = [6 + (index % 3), 2, 6 + (index % 2)];
  const values = Array.isArray(size) ? size : fallback;
  return [0, 1, 2].map((dimension) => finiteNumber(values[dimension], fallback[dimension]));
};

const hasSpatialPosition = (entity) => {
  const position = entity?.position;
  if (entity?.spatial_status === 'surveyed' && (Array.isArray(position) || (position && typeof position === 'object'))) return true;
  if (Array.isArray(position)) return [position[0], position[2]].some((value) => finiteNumber(value, 0) !== 0);
  return Boolean(position && ['x', 'z'].some((axis) => finiteNumber(position[axis], 0) !== 0));
};

const gridPosition = (index, count, spacingX = 120, spacingZ = 70) => {
  const columns = Math.ceil(Math.sqrt(count));
  const rows = Math.ceil(count / columns);
  return [
    (index % columns - (columns - 1) / 2) * spacingX,
    0,
    (Math.floor(index / columns) - (rows - 1) / 2) * spacingZ,
  ];
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
    status: entity?.status || 'unknown',
    position,
    x: position[0],
    y: position[1],
    z: position[2],
    rotation: entity?.rotation ?? 0,
    location: entity?.location || 'Main Estate',
  };
};

const buildUnifiedEstate = (robots = [], sensors = [], zones = [], actuators = []) => {
  const normalizedZones = zones.map((zone, idx) => normalizeEntity({
    ...zone,
    type: 'zone',
    name: zone.name || `Zone ${idx + 1}`,
    size: normalizeSize(zone.size || [100, 12, 50], idx),
    color: zone.color || ['#00a8ff', '#10b981', '#f59e0b', '#a78bfa'][idx % 4],
    position: hasSpatialPosition(zone) ? zone.position : gridPosition(idx, zones.length),
    position_inferred: zone.spatial_status !== 'surveyed',
  }, 'zone'));

  const entries = [
    ...robots.map((asset) => ({ asset, kind: 'robot' })),
    ...sensors.map((asset) => ({ asset, kind: 'sensor' })),
    ...actuators.map((asset) => ({ asset, kind: 'actuator' })),
  ];
  const resolveZone = (asset, index) => normalizedZones.find((candidate) => (
    String(candidate.id) === String(asset.zone_id) || String(candidate.zone_id) === String(asset.zone_id)
  )) || (normalizedZones.length ? normalizedZones[index % normalizedZones.length] : null);
  const layoutCounts = new Map();
  entries.forEach(({ asset }, index) => {
    const zone = resolveZone(asset, index);
    const layoutKey = zone ? String(zone.id) : 'estate';
    layoutCounts.set(layoutKey, (layoutCounts.get(layoutKey) || 0) + 1);
  });
  const layoutOffsets = new Map();
  const placedByKind = { robot: [], sensor: [], actuator: [] };

  entries.forEach(({ asset, kind }, index) => {
    const actualZone = normalizedZones.find((candidate) => (
      String(candidate.id) === String(asset.zone_id) || String(candidate.zone_id) === String(asset.zone_id)
    ));
    const layoutZone = actualZone || resolveZone(asset, index);
    const layoutKey = layoutZone ? String(layoutZone.id) : 'estate';
    const slot = layoutOffsets.get(layoutKey) || 0;
    layoutOffsets.set(layoutKey, slot + 1);
    const positionIsInferred = !hasSpatialPosition(asset);
    let position = asset.position;

    if (positionIsInferred && layoutZone) {
      const count = layoutCounts.get(layoutKey) || 1;
      const zoneWidth = Math.max(Number(layoutZone.size?.[0]) || 100, 12);
      const zoneDepth = Math.max(Number(layoutZone.size?.[2]) || 50, 12);
      const columns = Math.max(1, Math.ceil(Math.sqrt(count * zoneWidth / zoneDepth)));
      const rows = Math.max(1, Math.ceil(count / columns));
      const usableWidth = zoneWidth * 0.84;
      const usableDepth = zoneDepth * 0.78;
      const column = slot % columns;
      const row = Math.floor(slot / columns);
      position = [
        layoutZone.position[0] - usableWidth / 2 + (column + 0.5) * usableWidth / columns,
        kind === 'sensor' ? 2 : 1,
        layoutZone.position[2] - usableDepth / 2 + (row + 0.5) * usableDepth / rows,
      ];
    } else if (positionIsInferred) {
      position = gridPosition(slot, layoutCounts.get(layoutKey) || 1, 18, 12);
    }

    placedByKind[kind].push(normalizeEntity({
      ...asset,
      position,
      position_inferred: positionIsInferred,
      layout_zone_name: !actualZone && layoutZone ? layoutZone.name : undefined,
    }, kind));
  });

  return {
    robots: placedByKind.robot,
    sensors: placedByKind.sensor,
    actuators: placedByKind.actuator,
    zones: normalizedZones,
  };
};

const mapTwinDevice = (device) => {
  const position = normalizePosition(device.position);
  return normalizeEntity({
    ...device,
    id: device.id ?? device.device_id,
    device_id: device.device_id,
    type: device.kind,
    robot_id: device.kind === 'robot' ? device.device_id : undefined,
    sensor_id: device.kind === 'sensor' ? device.device_id : undefined,
    sensor_type: device.kind === 'sensor' ? device.device_type : undefined,
    value: device.state?.value,
    position,
    status: device.status || 'online',
  }, device.kind);
};

const mergeTwinDeviceSnapshot = (devices, snapshot) => {
  const updated = mapTwinDevice(snapshot);
  const existingIndex = devices.findIndex((item) => (
    String(item.id) === String(updated.id) || String(item.device_id) === String(updated.device_id)
  ));
  if (existingIndex < 0) return [...devices, updated];

  return devices.map((existing, index) => {
    if (index !== existingIndex) return existing;
    if (!existing.position_inferred || hasSpatialPosition(snapshot)) {
      return { ...existing, ...updated };
    }

    const position = existing.position;
    return {
      ...existing,
      ...updated,
      position,
      x: position[0],
      y: position[1],
      z: position[2],
      position_inferred: true,
    };
  });
};

export default function ScenePage() {
  const { user, token } = useCurrentUser();
  const [sceneToken, setSceneToken] = useState(token);
  const [robots, setRobots] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [actuators, setActuators] = useState([]);
  const [zones, setZones] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [assetHistory, setAssetHistory] = useState({});
  const [historyLoading, setHistoryLoading] = useState(false);
  const [cameraMedia, setCameraMedia] = useState([]);
  const [cameraMediaFile, setCameraMediaFile] = useState(null);
  const [mediaUploading, setMediaUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [sceneViewMode, setSceneViewMode] = useState('drone');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createKind, setCreateKind] = useState('sensor');
  const [deviceForm, setDeviceForm] = useState({ device_id: '', name: '', device_type: '', zone_id: '', adapter_type: 'simulation' });
  const [zoneForm, setZoneForm] = useState({
    name: '', description: '', location: '', x: '', y: '', z: '',
    width: '', height: '', depth: '', spatial_status: 'inferred', coordinate_system: '',
  });
  const [editingSelected, setEditingSelected] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', device_type: '', zone_id: '' });
  const [saving, setSaving] = useState(false);
  const [commandPending, setCommandPending] = useState(false);
  const [commandFeedback, setCommandFeedback] = useState('');
  const [liveConnected, setLiveConnected] = useState(false);
  const [lastSceneUpdateAt, setLastSceneUpdateAt] = useState(null);
  const [assetSearch, setAssetSearch] = useState('');
  const canManageDevices = user?.permissions?.includes('devices.manage') || ['admin', 'superadmin', 'operator'].includes(String(user?.role || '').toLowerCase());
  const canManageZones = user?.permissions?.includes('zones.manage') || ['admin', 'superadmin'].includes(String(user?.role || '').toLowerCase());

  useEffect(() => {
    if (token) setSceneToken(token);
  }, [token]);

  const refreshSceneData = useCallback(async () => {
    let activeToken = sceneToken || token || getAuthToken();
    if (!activeToken) {
      setMessage('Sign in to load the tenant digital twin.');
      return;
    }
    const fetchSnapshot = (bearerToken) => Promise.all([
      fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers: { Authorization: `Bearer ${bearerToken}` } }),
      fetch(`${API_URL}/api/v1/zones`, { headers: { Authorization: `Bearer ${bearerToken}` } }),
    ]);

    try {
      let [twinRes, zonesRes] = await fetchSnapshot(activeToken);
      if (twinRes.status === 401 || zonesRes.status === 401) {
        const refreshToken = getRefreshToken();
        if (!refreshToken) throw new Error('Session expired. Sign in again to refresh estate data.');
        const refreshed = await refreshAuthToken(refreshToken);
        activeToken = refreshed.access_token;
        setAuthToken(refreshed.access_token);
        setRefreshToken(refreshed.refresh_token);
        setSceneToken(refreshed.access_token);
        [twinRes, zonesRes] = await fetchSnapshot(activeToken);
      }
      if (!twinRes.ok || !zonesRes.ok) throw new Error('Unable to load the tenant digital twin.');
      const [twinDevices, nextZones] = await Promise.all([twinRes.json(), zonesRes.json()]);
      const devices = Array.isArray(twinDevices) ? twinDevices : [];
      const nextRobots = devices.filter((device) => device.kind === 'robot').map(mapTwinDevice);
      const nextSensors = devices.filter((device) => device.kind === 'sensor').map(mapTwinDevice);
      const nextActuators = devices.filter((device) => device.kind === 'actuator').map(mapTwinDevice);
      const normalized = buildUnifiedEstate(nextRobots, nextSensors, Array.isArray(nextZones) ? nextZones : [], nextActuators);

      setRobots(normalized.robots);
      setSensors(normalized.sensors);
      setActuators(normalized.actuators);
      setZones(normalized.zones);
      const observationTime = new Date();
      setLastSceneUpdateAt(observationTime);
      setAssetHistory((previous) => {
        const next = { ...previous };
        [...normalized.robots, ...normalized.sensors, ...normalized.actuators].forEach((asset) => {
          const key = `${asset.type}:${asset.id}`;
          const value = asset.value ?? asset.state?.value ?? asset.state?.output ?? asset.state?.activity ?? asset.status;
          next[key] = [{ time: observationTime, value, unit: asset.state?.unit || '' }, ...(previous[key] || [])].slice(0, 24);
        });
        return next;
      });
      const inferredPositionCount = (Array.isArray(nextZones) ? nextZones : []).filter((zone) => !hasSpatialPosition(zone)).length;
      setMessage(normalized.zones.length === 0
        ? 'No live zones are available for this tenant yet.'
        : inferredPositionCount
          ? `${inferredPositionCount} zone positions are inferred for planning; surveyed coordinates are not available from the zone service.`
          : '');
    } catch (error) {
      console.error('Failed to fetch estate scene data', error);
      setMessage(`Live refresh failed; showing the last successful scene. ${error.message || 'Unable to reach the live estate API.'}`);
    }
  }, [sceneToken, token]);

  useEffect(() => {
    refreshSceneData();
    const interval = window.setInterval(refreshSceneData, liveConnected ? 30000 : 5000);
    return () => window.clearInterval(interval);
  }, [liveConnected, refreshSceneData]);

  useEffect(() => {
    if (!sceneToken) return undefined;
    const socket = initializeSocket(sceneToken);
    const handleConnect = () => setLiveConnected(true);
    const handleDisconnect = () => setLiveConnected(false);
    const handleDeviceUpdate = (snapshot) => {
      if (!snapshot?.device_id && snapshot?.id === undefined) return;
      const device = mapTwinDevice(snapshot);
      const updateCollection = (setter) => setter((previous) => mergeTwinDeviceSnapshot(previous, snapshot));
      if (device.type === 'robot') updateCollection(setRobots);
      else if (device.type === 'sensor') updateCollection(setSensors);
      else if (device.type === 'actuator') updateCollection(setActuators);
      const receivedAt = new Date(snapshot.last_updated || Date.now());
      const historyKey = `${device.type}:${device.id}`;
      const value = device.state?.value ?? device.state?.output ?? device.state?.activity ?? device.status;
      setAssetHistory((previous) => {
        const samples = previous[historyKey] || [];
        if (samples[0] && receivedAt.getTime() - samples[0].time.getTime() < 5000) return previous;
        return {
          ...previous,
          [historyKey]: [{ time: receivedAt, value, unit: device.state?.unit || '' }, ...samples].slice(0, 60),
        };
      });
      setLastSceneUpdateAt(receivedAt);
    };
    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('digital_twin:device_update', handleDeviceUpdate);
    if (socket.connected) setLiveConnected(true);
    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('digital_twin:device_update', handleDeviceUpdate);
    };
  }, [sceneToken]);

  async function submitCreate(event) {
    event.preventDefault();
    if (!sceneToken) return;
    setSaving(true);
    setMessage('');
    try {
      const isZone = createKind === 'zone';
      const geometryValues = [zoneForm.x, zoneForm.y, zoneForm.z, zoneForm.width, zoneForm.height, zoneForm.depth];
      const hasGeometry = geometryValues.some((value) => value !== '');
      if (isZone && hasGeometry && geometryValues.some((value) => value === '' || !Number.isFinite(Number(value)))) {
        throw new Error('Enter all three position coordinates and all three dimensions as numbers.');
      }
      const zonePayload = {
        name: zoneForm.name,
        description: zoneForm.description,
        location: zoneForm.location,
        spatial_status: zoneForm.spatial_status,
        coordinate_system: zoneForm.coordinate_system || null,
        ...(hasGeometry ? {
          spatial_position: { x: Number(zoneForm.x), y: Number(zoneForm.y), z: Number(zoneForm.z) },
          dimensions: { width: Number(zoneForm.width), height: Number(zoneForm.height), depth: Number(zoneForm.depth) },
        } : {}),
      };
      const response = await fetch(`${API_URL}/api/v1/${isZone ? 'zones' : 'digital-twin/devices'}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${sceneToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(isZone ? zonePayload : {
          ...deviceForm,
          kind: createKind,
          zone_id: deviceForm.zone_id ? Number(deviceForm.zone_id) : null,
          control_mode: deviceForm.adapter_type === 'serial' ? 'manual' : 'automation',
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || `Unable to create ${isZone ? 'zone' : 'asset'}.`);
      setDeviceForm({ device_id: '', name: '', device_type: '', zone_id: '', adapter_type: 'simulation' });
      setZoneForm({ name: '', description: '', location: '', x: '', y: '', z: '', width: '', height: '', depth: '', spatial_status: 'inferred', coordinate_system: '' });
      setShowCreateForm(false);
      await refreshSceneData();
      setMessage(`${isZone ? 'Zone' : 'Asset'} created.`);
    } catch (error) {
      setMessage(error.message || 'Unable to create record.');
    } finally {
      setSaving(false);
    }
  }

  function beginEditSelected() {
    if (!liveSelectedEntity) return;
    setEditForm({
      name: liveSelectedEntity.name || '',
      device_type: liveSelectedEntity.device_type || liveSelectedEntity.sensor_type || '',
      zone_id: liveSelectedEntity.zone_id ?? '',
      x: liveSelectedEntity.spatial_position?.x ?? '',
      y: liveSelectedEntity.spatial_position?.y ?? '',
      z: liveSelectedEntity.spatial_position?.z ?? '',
      width: liveSelectedEntity.dimensions?.width ?? '',
      height: liveSelectedEntity.dimensions?.height ?? '',
      depth: liveSelectedEntity.dimensions?.depth ?? '',
      spatial_status: liveSelectedEntity.spatial_status || 'inferred',
      coordinate_system: liveSelectedEntity.coordinate_system || '',
      length_unit: liveSelectedEntity.length_unit || 'm',
    });
    setEditingSelected(true);
  }

  async function saveSelected() {
    if (!sceneToken || !liveSelectedEntity) return;
    const isZone = liveSelectedEntity.type === 'zone';
    const geometryValues = [editForm.x, editForm.y, editForm.z, editForm.width, editForm.height, editForm.depth];
    const hasGeometry = geometryValues.some((value) => value !== '');
    if (isZone && hasGeometry && geometryValues.some((value) => value === '' || !Number.isFinite(Number(value)))) {
      setMessage('Enter all three position coordinates and all three dimensions as numbers.');
      return;
    }
    setSaving(true);
    setMessage('');
    try {
      const response = await fetch(`${API_URL}/api/v1/${isZone ? 'zones' : 'digital-twin/devices'}/${liveSelectedEntity.id}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${sceneToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(isZone ? {
          name: editForm.name,
          location: editForm.name,
          spatial_status: editForm.spatial_status,
          coordinate_system: editForm.coordinate_system || null,
          length_unit: editForm.length_unit || 'm',
          ...(hasGeometry ? {
            spatial_position: { x: Number(editForm.x), y: Number(editForm.y), z: Number(editForm.z) },
            dimensions: { width: Number(editForm.width), height: Number(editForm.height), depth: Number(editForm.depth) },
          } : {}),
        } : {
          name: editForm.name,
          device_type: editForm.device_type,
          zone_id: editForm.zone_id === '' ? null : Number(editForm.zone_id),
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to update selected record.');
      setEditingSelected(false);
      await refreshSceneData();
      setMessage('Selected record updated.');
    } catch (error) {
      setMessage(error.message || 'Unable to update selected record.');
    } finally {
      setSaving(false);
    }
  }

  async function deleteSelected() {
    if (!sceneToken || !liveSelectedEntity) return;
    const isZone = liveSelectedEntity.type === 'zone';
    if (!window.confirm(`Delete ${isZone ? 'zone' : 'asset'} "${liveSelectedEntity.name}"?`)) return;
    setSaving(true);
    setMessage('');
    try {
      const response = await fetch(`${API_URL}/api/v1/${isZone ? 'zones' : 'digital-twin/devices'}/${liveSelectedEntity.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${sceneToken}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to delete selected record.');
      setSelectedEntity(null);
      await refreshSceneData();
      setMessage(`${isZone ? 'Zone' : 'Asset'} deleted.`);
    } catch (error) {
      setMessage(error.message || 'Unable to delete selected record.');
    } finally {
      setSaving(false);
    }
  }

  async function sendSelectedCommand(command) {
    if (!sceneToken || !liveSelectedEntity || !['robot', 'actuator'].includes(liveSelectedEntity.type)) return;
    setCommandPending(true);
    setCommandFeedback('');
    try {
      const response = await fetch(`${API_URL}/api/v1/digital-twin/devices/${liveSelectedEntity.id}/control`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${sceneToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Command was rejected.');
      const updated = mapTwinDevice(result);
      const setter = updated.type === 'robot' ? setRobots : setActuators;
      setter((previous) => mergeTwinDeviceSnapshot(previous, result));
      const delivery = result.state?.last_command_delivery;
      const outcome = delivery?.confirmed ? 'Confirmed' : 'Accepted';
      const confirmation = delivery?.message ? ` ${delivery.message}.` : '';
      setCommandFeedback(`${outcome}: ${command}.${confirmation} Device state updated at ${new Date(result.last_updated || Date.now()).toLocaleTimeString()}.`);
    } catch (error) {
      setCommandFeedback(error.message || 'Command failed.');
    } finally {
      setCommandPending(false);
    }
  }

  const selectedEntityKey = selectedEntity ? `${selectedEntity.type}:${selectedEntity.id}` : '';
  const selectedCollection = selectedEntity?.type === 'zone'
    ? zones
    : selectedEntity?.type === 'robot'
      ? robots
      : selectedEntity?.type === 'actuator'
        ? actuators
        : sensors;
  const liveSelectedEntity = selectedCollection.find((entity) => String(entity.id) === String(selectedEntity?.id)) || selectedEntity;
  const selectedHistory = assetHistory[selectedEntityKey] || [];
  const cameraMediaSelected = liveSelectedEntity && /camera|video|imaging/i.test(`${liveSelectedEntity.name || ''} ${liveSelectedEntity.device_type || ''} ${liveSelectedEntity.sensor_type || ''}`);
  const selectedDeviceId = selectedEntity?.id;
  const selectedDeviceType = selectedEntity?.type;

  useEffect(() => {
    if (!sceneToken || !selectedDeviceId || selectedDeviceType === 'zone') {
      setCameraMedia([]);
      return undefined;
    }
    let cancelled = false;
    const loadHistoryAndMedia = async () => {
      setHistoryLoading(true);
      try {
        const historyResponse = await fetch(`${API_URL}/api/v1/digital-twin/devices/${selectedDeviceId}/history?limit=120`, {
          headers: { Authorization: `Bearer ${sceneToken}` },
        });
        const historyResult = await historyResponse.json().catch(() => ({}));
        if (!historyResponse.ok) throw new Error(historyResult.detail || 'Unable to load persisted telemetry history.');
        if (!cancelled) {
          const historyKey = `${selectedDeviceType}:${selectedDeviceId}`;
          const persisted = (Array.isArray(historyResult.data) ? historyResult.data : []).map((entry) => {
            const snapshot = entry.snapshot || {};
            const state = snapshot.state || {};
            return {
              time: new Date(entry.recorded_at),
              value: state.value ?? state.output ?? state.activity ?? snapshot.status,
              unit: state.unit || '',
            };
          }).reverse();
          setAssetHistory((previous) => {
            const combined = [...persisted, ...(previous[historyKey] || [])];
            const unique = new Map(combined.map((sample) => [sample.time.getTime(), sample]));
            return {
              ...previous,
              [historyKey]: [...unique.values()].sort((a, b) => b.time.getTime() - a.time.getTime()).slice(0, 120),
            };
          });
        }
        if (cameraMediaSelected) {
          const mediaResponse = await fetch(`${API_URL}/api/v1/digital-twin/devices/${selectedDeviceId}/media`, {
            headers: { Authorization: `Bearer ${sceneToken}` },
          });
          const mediaResult = await mediaResponse.json().catch(() => ({}));
          if (!mediaResponse.ok) throw new Error(mediaResult.detail || 'Unable to load camera media.');
          if (!cancelled) setCameraMedia(Array.isArray(mediaResult.data) ? mediaResult.data : []);
        } else if (!cancelled) {
          setCameraMedia([]);
        }
      } catch (historyError) {
        if (!cancelled) setMessage(historyError.message || 'Unable to load persisted asset history.');
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    };
    loadHistoryAndMedia();
    return () => { cancelled = true; };
  }, [cameraMediaSelected, sceneToken, selectedDeviceId, selectedDeviceType]);

  async function uploadCameraMedia(event) {
    event.preventDefault();
    if (!cameraMediaFile || !liveSelectedEntity || !sceneToken) return;
    setMediaUploading(true);
    setMessage('');
    try {
      const body = new FormData();
      body.append('file', cameraMediaFile);
      const response = await fetch(`${API_URL}/api/v1/digital-twin/devices/${liveSelectedEntity.id}/media`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${sceneToken}` },
        body,
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to upload camera media.');
      setCameraMedia((previous) => [result, ...previous]);
      setCameraMediaFile(null);
      event.target.reset();
      setMessage('Camera media uploaded and retained according to the configured policy.');
    } catch (uploadError) {
      setMessage(uploadError.message || 'Unable to upload camera media.');
    } finally {
      setMediaUploading(false);
    }
  }

  async function downloadCameraMedia(media) {
    try {
      const response = await fetch(`${API_URL}${media.content_url}`, {
        headers: { Authorization: `Bearer ${sceneToken}` },
      });
      if (!response.ok) throw new Error('Unable to download camera media.');
      const objectUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = media.name;
      link.click();
      URL.revokeObjectURL(objectUrl);
    } catch (downloadError) {
      setMessage(downloadError.message || 'Unable to download camera media.');
    }
  }
  const allAssets = [...robots, ...sensors, ...actuators];
  const visibleAssets = allAssets.filter((asset) => `${asset.name || ''} ${asset.device_id || ''} ${asset.device_type || ''} ${asset.kind || ''}`.toLowerCase().includes(assetSearch.toLowerCase()));

  async function updateSelectedDevice(patch, successMessage) {
    if (!sceneToken || !liveSelectedEntity || liveSelectedEntity.type === 'zone') return;
    setSaving(true);
    setMessage('');
    try {
      const response = await fetch(`${API_URL}/api/v1/digital-twin/devices/${liveSelectedEntity.id}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${sceneToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to update device settings.');
      const updated = mapTwinDevice(result);
      const setter = updated.type === 'robot' ? setRobots : updated.type === 'sensor' ? setSensors : setActuators;
      setter((previous) => mergeTwinDeviceSnapshot(previous, result));
      setMessage(successMessage);
    } catch (error) {
      setMessage(error.message || 'Unable to update device settings.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-3xl border border-cyan-500/20 bg-slate-900/80 p-5 shadow-[0_0_35px_rgba(34,211,238,0.08)] backdrop-blur-xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.45em] text-cyan-300">AEGIS DIGITAL TWIN</p>
              <h1 className="mt-2 text-3xl font-bold text-cyan-200">3D Estate Scene</h1>
              <p className="mt-1 text-sm text-slate-300">Unified view for zones, sensors, robotics, and estate devices in the same operating environment.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <div role="group" aria-label="Scene camera view" className="flex rounded border border-slate-700 p-1">
                <button type="button" onClick={() => setSceneViewMode('drone')} aria-pressed={sceneViewMode === 'drone'} className={`rounded px-3 py-1.5 text-xs ${sceneViewMode === 'drone' ? 'bg-cyan-800 text-white' : 'text-slate-300'}`}>Drone</button>
                <button type="button" onClick={() => setSceneViewMode('orbit')} aria-pressed={sceneViewMode === 'orbit'} className={`rounded px-3 py-1.5 text-xs ${sceneViewMode === 'orbit' ? 'bg-cyan-800 text-white' : 'text-slate-300'}`}>Orbit</button>
              </div>
              {canManageDevices && <button type="button" onClick={() => { setShowCreateForm(!showCreateForm); setCreateKind('sensor'); }} className="rounded border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-100 hover:bg-cyan-500/20">{showCreateForm ? 'Close form' : 'Add asset'}</button>}
              {canManageZones && <button type="button" onClick={() => { setCreateKind('zone'); setShowCreateForm(true); }} className="rounded border border-emerald-700 px-3 py-2 text-sm text-emerald-200 hover:bg-emerald-950/60">Add zone</button>}
              <button type="button" onClick={refreshSceneData} className="rounded border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-cyan-600">Refresh</button>
            </div>
          </div>
        </div>

        {message && (
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
            {message}
          </div>
        )}

        {showCreateForm && (
          <form onSubmit={submitCreate} className="grid gap-3 border-y border-slate-800 py-4 md:grid-cols-2">
            {createKind !== 'zone' ? <>
              <label className="text-xs text-slate-400">Asset kind
                <select value={createKind} onChange={(event) => { setCreateKind(event.target.value); if (event.target.value !== 'actuator') setDeviceForm((previous) => ({ ...previous, adapter_type: 'simulation' })); }} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"><option value="sensor">Sensor</option><option value="robot">Robot</option><option value="actuator">Actuator</option></select>
              </label>
              <label className="text-xs text-slate-400">Device ID<input required maxLength={100} value={deviceForm.device_id} onChange={(event) => setDeviceForm({ ...deviceForm, device_id: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
              <label className="text-xs text-slate-400">Name<input required maxLength={255} value={deviceForm.name} onChange={(event) => setDeviceForm({ ...deviceForm, name: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
              <label className="text-xs text-slate-400">Device type<input required maxLength={100} value={deviceForm.device_type} onChange={(event) => setDeviceForm({ ...deviceForm, device_type: event.target.value })} placeholder="soil_moisture, rover, pump" className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
              <label className="text-xs text-slate-400">Connection<select value={deviceForm.adapter_type} onChange={(event) => setDeviceForm({ ...deviceForm, adapter_type: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"><option value="simulation">Software simulation</option><option value="serial" disabled={createKind !== 'actuator'}>Arduino Mega onboard LED (USB gateway)</option></select></label>
              <label className="text-xs text-slate-400">Zone
                <select value={deviceForm.zone_id} onChange={(event) => setDeviceForm({ ...deviceForm, zone_id: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"><option value="">Unassigned</option>{zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}</select>
              </label>
              {deviceForm.adapter_type === 'serial' && <p className="text-xs text-amber-300 md:col-span-2">Pilot only: use device ID <code>mega-onboard-led-01</code> and kind Actuator. Commands require the local Arduino gateway to be running.</p>}
            </> : <>
              <label className="text-xs text-slate-400">Zone name<input required maxLength={255} value={zoneForm.name} onChange={(event) => setZoneForm({ ...zoneForm, name: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
              <label className="text-xs text-slate-400">Description<input maxLength={500} value={zoneForm.description} onChange={(event) => setZoneForm({ ...zoneForm, description: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
              <label className="text-xs text-slate-400">Location<input value={zoneForm.location} onChange={(event) => setZoneForm({ ...zoneForm, location: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
              <label className="text-xs text-slate-400">Spatial status<select value={zoneForm.spatial_status} onChange={(event) => setZoneForm({ ...zoneForm, spatial_status: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"><option value="inferred">Inferred planning geometry</option><option value="surveyed">Surveyed geometry</option></select></label>
              <label className="text-xs text-slate-400">Coordinate system<input value={zoneForm.coordinate_system} onChange={(event) => setZoneForm({ ...zoneForm, coordinate_system: event.target.value })} placeholder="e.g. local-estate-grid or EPSG:4326" className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
              {['x', 'y', 'z', 'width', 'height', 'depth'].map((field) => <label key={field} className="text-xs text-slate-400">{field === 'x' || field === 'y' || field === 'z' ? `Position ${field.toUpperCase()} (m)` : `${field[0].toUpperCase()}${field.slice(1)} (m)`}
                <input type="number" step="any" value={zoneForm[field]} onChange={(event) => setZoneForm({ ...zoneForm, [field]: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
              </label>)}
              <p className="text-xs text-amber-300">Only set “Surveyed” when the position, dimensions, and coordinate-system reference come from an actual site survey. Otherwise the scene will label geometry as inferred.</p>
            </>}
            <button type="submit" disabled={saving} className="w-fit rounded bg-cyan-800 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{saving ? 'Saving...' : `Create ${createKind === 'zone' ? 'zone' : 'asset'}`}</button>
          </form>
        )}

        <div className="grid gap-6 xl:grid-cols-[1.6fr_0.7fr]">
          <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/80 p-3 shadow-2xl shadow-slate-950/30">
            <div className="h-170 min-h-105">
              <EstateScene
                robots={robots}
                sensors={sensors}
                actuators={actuators}
                zones={zones}
                selectedEntity={selectedEntity}
                viewMode={sceneViewMode === 'drone' ? 'drone' : 'realworld'}
                lightIntensity={1.1}
                autoRotate={false}
                onEntitySelect={(entity) => setSelectedEntity(normalizeEntity(entity, entity?.type || 'sensor'))}
              />
            </div>
          </div>

          <aside className="space-y-6">
            <section className="space-y-3 border-b border-slate-800 pb-5">
              <h2 className="text-lg font-semibold text-cyan-200">Estate inventory</h2>
              {[
                ['Robots', robots.length, '/robots-management'],
                ['Sensors', sensors.length, '/sensors'],
                ['Actuators', actuators.length, '/actuators'],
                ['Zones', zones.length, '/zones'],
              ].map(([label, count, href]) => (
                <Link key={label} href={href} className="flex items-center justify-between border-b border-slate-800/70 py-2 text-sm text-slate-300 hover:text-cyan-200">
                  <span>{label}</span><span className="font-mono">{count}</span>
                </Link>
              ))}
            </section>

            <section className="space-y-3 border-b border-slate-800 pb-5">
              <div className="flex items-center justify-between"><h2 className="text-lg font-semibold text-cyan-200">Live assets</h2><span className={`text-[10px] uppercase ${liveConnected ? 'text-emerald-300' : 'text-amber-300'}`}>{liveConnected ? 'Stream connected' : 'Polling'}</span></div>
              <input value={assetSearch} onChange={(event) => setAssetSearch(event.target.value)} placeholder="Find asset by name, ID, type" aria-label="Search live assets" className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white" />
              <ul className="max-h-56 divide-y divide-slate-800 overflow-y-auto">
                {visibleAssets.map((asset) => <li key={`${asset.type}:${asset.id}`}>
                  <button type="button" onClick={() => { setSelectedEntity(asset); setEditingSelected(false); setCommandFeedback(''); }} className={`flex w-full items-center justify-between gap-2 py-2 text-left ${String(selectedEntity?.id) === String(asset.id) ? 'text-cyan-200' : 'text-slate-300 hover:text-white'}`}>
                    <span className="min-w-0"><span className="block truncate text-xs">{asset.name}</span><span className="block truncate text-[10px] text-slate-500">{asset.device_id} · {asset.kind}</span></span>
                    <span className={`shrink-0 text-[10px] uppercase ${String(asset.status).toLowerCase() === 'online' ? 'text-emerald-300' : 'text-amber-300'}`}>{asset.status || 'unknown'}</span>
                  </button>
                </li>)}
                {!visibleAssets.length && <li className="py-3 text-xs text-slate-500">No matching assets.</li>}
              </ul>
              <p className="text-[10px] text-slate-500">{lastSceneUpdateAt ? `Last scene snapshot ${lastSceneUpdateAt.toLocaleTimeString()}` : 'Waiting for the first scene snapshot.'}</p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-cyan-200">Selected asset</h2>
              {selectedEntity ? (
                <div className="space-y-3 text-sm">
                  <h3 className="font-semibold text-white">{liveSelectedEntity.name}</h3>
                  {editingSelected ? <div className="space-y-3">
                    <label className="block text-xs text-slate-400">Name<input value={editForm.name} onChange={(event) => setEditForm({ ...editForm, name: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
                    {liveSelectedEntity.type !== 'zone' && <>
                      <label className="block text-xs text-slate-400">Device type<input value={editForm.device_type} onChange={(event) => setEditForm({ ...editForm, device_type: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
                      <label className="block text-xs text-slate-400">Zone<select value={editForm.zone_id} onChange={(event) => setEditForm({ ...editForm, zone_id: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"><option value="">Unassigned</option>{zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}</select></label>
                    </>}
                    {liveSelectedEntity.type === 'zone' && <>
                      <label className="block text-xs text-slate-400">Spatial status<select value={editForm.spatial_status} onChange={(event) => setEditForm({ ...editForm, spatial_status: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"><option value="inferred">Inferred</option><option value="surveyed">Surveyed</option></select></label>
                      <label className="block text-xs text-slate-400">Coordinate system<input value={editForm.coordinate_system} onChange={(event) => setEditForm({ ...editForm, coordinate_system: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
                      <label className="block text-xs text-slate-400">Length unit<input value={editForm.length_unit} onChange={(event) => setEditForm({ ...editForm, length_unit: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>
                      {['x', 'y', 'z', 'width', 'height', 'depth'].map((field) => <label key={field} className="text-xs text-slate-400">{field} (m)<input type="number" step="any" value={editForm[field]} onChange={(event) => setEditForm({ ...editForm, [field]: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" /></label>)}
                    </>}
                    <div className="flex gap-2"><button type="button" onClick={saveSelected} disabled={saving} className="rounded bg-cyan-800 px-3 py-1.5 text-xs text-white disabled:opacity-50">Save</button><button type="button" onClick={() => setEditingSelected(false)} className="rounded border border-slate-700 px-3 py-1.5 text-xs text-slate-200">Cancel</button></div>
                  </div> : <>
                  <dl className="space-y-2 text-slate-400">
                    <div className="flex justify-between gap-3"><dt>Kind</dt><dd className="text-slate-200">{liveSelectedEntity.type}</dd></div>
                    <div className="flex justify-between gap-3"><dt>Status</dt><dd className="text-slate-200">{liveSelectedEntity.status || 'Unknown'}</dd></div>
                    <div className="flex justify-between gap-3"><dt>Zone</dt><dd className="text-slate-200">{liveSelectedEntity.zone_id ?? (liveSelectedEntity.layout_zone_name ? `Unassigned · displayed in ${liveSelectedEntity.layout_zone_name}` : 'Unassigned')}</dd></div>
                    <div className="flex justify-between gap-3"><dt>Position</dt><dd className="text-right text-slate-200"><span className="block font-mono">{liveSelectedEntity.position?.map((value) => Number(value).toFixed(1)).join(', ') || 'Unknown'}</span><span className={`text-[10px] ${liveSelectedEntity.position_inferred ? 'text-amber-300' : 'text-emerald-300'}`}>{liveSelectedEntity.position_inferred ? 'Inferred planning position' : 'Reported position'}</span></dd></div>
                    {liveSelectedEntity.type === 'zone' && <div className="flex justify-between gap-3"><dt>Geometry</dt><dd className="text-right text-slate-200">{liveSelectedEntity.spatial_status === 'surveyed' ? `Surveyed · ${liveSelectedEntity.coordinate_system} · ${liveSelectedEntity.length_unit}` : 'Inferred planning layout'}<span className="block font-mono text-[10px]">{liveSelectedEntity.size?.join(' × ') || 'Dimensions unavailable'}</span></dd></div>}
                    <div className="flex justify-between gap-3"><dt>Reading / output</dt><dd className="text-slate-200">{liveSelectedEntity.value ?? liveSelectedEntity.state?.value ?? liveSelectedEntity.state?.output ?? liveSelectedEntity.state?.activity ?? 'No live value'}</dd></div>
                    {liveSelectedEntity.type !== 'zone' && <>
                      <div className="flex justify-between gap-3"><dt>Control source</dt><dd className="text-slate-200">{liveSelectedEntity.control_mode || 'unknown'}</dd></div>
                      <div className="flex justify-between gap-3"><dt>Simulation</dt><dd className="text-slate-200">{liveSelectedEntity.simulation_enabled ? 'enabled' : 'paused'}</dd></div>
                      <div className="flex justify-between gap-3"><dt>Last device update</dt><dd className="text-slate-200">{liveSelectedEntity.last_updated ? new Date(liveSelectedEntity.last_updated).toLocaleString() : 'Unknown'}</dd></div>
                    </>}
                  </dl>
                  {liveSelectedEntity.type !== 'zone' && <details className="rounded border border-slate-800 px-3 py-2">
                    <summary className="cursor-pointer text-xs text-cyan-200">Full telemetry and state</summary>
                    <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-all text-[10px] text-slate-300">{JSON.stringify({ state: liveSelectedEntity.state || {}, automation_policy: liveSelectedEntity.automation_policy || {} }, null, 2)}</pre>
                  </details>}
                  {cameraMediaSelected && <section className="space-y-3 rounded border border-slate-800 p-3">
                    <div>
                      <h4 className="text-xs font-semibold uppercase text-slate-300">Camera media</h4>
                      <p className="mt-1 text-[10px] text-slate-500">Files are stored on the configured local media volume and expire according to backend retention settings.</p>
                    </div>
                    {canManageDevices && <form onSubmit={uploadCameraMedia} className="space-y-2">
                      <input type="file" required accept="image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime" onChange={(event) => setCameraMediaFile(event.target.files?.[0] || null)} className="block w-full text-[10px] text-slate-300" />
                      <button type="submit" disabled={!cameraMediaFile || mediaUploading} className="rounded border border-cyan-800 px-3 py-1.5 text-xs text-cyan-200 disabled:opacity-50">{mediaUploading ? 'Uploading...' : 'Upload recording'}</button>
                    </form>}
                    {cameraMedia.length ? <ul className="space-y-2">
                      {cameraMedia.map((media) => <li key={media.id} className="flex items-center justify-between gap-3 text-xs">
                        <span className="min-w-0 truncate text-slate-300">{media.name} · {Math.ceil(media.size_bytes / 1024)} KB</span>
                        <button type="button" onClick={() => downloadCameraMedia(media)} className="shrink-0 text-cyan-200 hover:text-white">Download</button>
                      </li>)}
                    </ul> : <p className="text-xs text-slate-500">No retained recordings for this camera.</p>}
                  </section>}
                  {liveSelectedEntity.type !== 'zone' && <div className="border-t border-slate-800 pt-3">
                    <div className="flex items-baseline justify-between gap-2"><h4 className="text-xs font-semibold uppercase text-slate-300">Persisted telemetry</h4><span className="text-[10px] text-slate-500">{historyLoading ? 'Loading history...' : 'up to 120 retained samples'}</span></div>
                    {selectedHistory.length ? <ol className="mt-2 max-h-36 space-y-1 overflow-y-auto">
                      {selectedHistory.map((sample, index) => <li key={`${sample.time.getTime()}-${index}`} className="flex justify-between gap-3 text-xs"><time className="text-slate-500">{sample.time.toLocaleString()}</time><span className="font-mono text-slate-200">{sample.value ?? 'No value'} {sample.unit}</span></li>)}
                    </ol> : <p className="mt-2 text-xs text-slate-500">{historyLoading ? 'Loading durable snapshots...' : 'No telemetry snapshots have been retained for this asset yet.'}</p>}
                  </div>}
                  <Link href={selectedEntity.type === 'zone' ? '/zones' : selectedEntity.type === 'robot' ? '/robots-management' : selectedEntity.type === 'actuator' ? '/actuators' : '/sensors'} className="inline-flex text-sm text-cyan-300 hover:text-cyan-100">Open owning page</Link>
                  </>}
                  {selectedEntity.type !== 'zone' && canManageDevices && !editingSelected && <div className="flex gap-3 border-t border-slate-800 pt-3"><button type="button" onClick={beginEditSelected} className="text-xs text-cyan-200 hover:text-white">Edit asset</button><button type="button" onClick={deleteSelected} disabled={saving} className="text-xs text-red-300 hover:text-red-100 disabled:opacity-50">Delete asset</button></div>}
                  {selectedEntity.type === 'zone' && canManageZones && !editingSelected && <div className="flex gap-3 border-t border-slate-800 pt-3"><button type="button" onClick={beginEditSelected} className="text-xs text-cyan-200 hover:text-white">Edit zone</button><button type="button" onClick={deleteSelected} disabled={saving} className="text-xs text-red-300 hover:text-red-100 disabled:opacity-50">Delete zone</button></div>}
                  {selectedEntity.type !== 'zone' && canManageDevices && !editingSelected && <section className="space-y-3 border-t border-slate-800 pt-3">
                    <div className="grid grid-cols-2 gap-2">
                      <label className="text-[10px] uppercase text-slate-500">Control mode<select disabled={saving} value={liveSelectedEntity.control_mode || 'automation'} onChange={(event) => updateSelectedDevice({ control_mode: event.target.value }, `Control mode set to ${event.target.value}.`)} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-white"><option value="manual">Manual</option><option value="automation">Automation</option><option value="ai">AI</option></select></label>
                      <label className="text-[10px] uppercase text-slate-500">Simulation<select disabled={saving} value={liveSelectedEntity.simulation_enabled ? 'enabled' : 'paused'} onChange={(event) => updateSelectedDevice({ simulation_enabled: event.target.value === 'enabled' }, `Simulation ${event.target.value}.`)} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-white"><option value="enabled">Enabled</option><option value="paused">Paused</option></select></label>
                    </div>
                    {(liveSelectedEntity.type === 'robot' || liveSelectedEntity.type === 'actuator') && <div className="flex flex-wrap gap-2">
                      {(liveSelectedEntity.type === 'robot' ? ['start', 'stop', 'reset'] : ['on', 'off', 'open', 'close']).map((command) => <button key={command} type="button" disabled={commandPending} onClick={() => sendSelectedCommand(command)} className="rounded border border-cyan-700/70 px-3 py-1.5 text-xs text-cyan-100 hover:bg-cyan-950 disabled:opacity-50">{commandPending ? 'Sending…' : command}</button>)}
                    </div>}
                    {commandFeedback && <p role="status" className="text-xs text-slate-300">{commandFeedback}</p>}
                  </section>}
                </div>
              ) : <p className="text-sm text-slate-400">Select an asset in the scene to inspect its current state.</p>}
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
