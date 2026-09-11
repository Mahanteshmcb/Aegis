import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import useEstateRealtime from '../hooks/useEstateRealtime';
import Inspector3D from '../components/3d/Inspector3D';
import Creator3D from '../components/3d/Creator3D';

const DigitalTwinScene = dynamic(
  () => import('../components/3d/DigitalTwinScene'),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        Loading digital twin visuals...
      </div>
    ),
  }
);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const buildSimulatedEstate = () => ({
  robots: [
    { id: 'sim-robot-1', name: 'Field Rover A', status: 'active', position: [-8, 0, 4] },
    { id: 'sim-robot-2', name: 'Inspection Bot', status: 'charging', position: [8, 0, 4] },
  ],
  sensors: [
    { id: 'sim-sensor-1', type: 'temperature', name: 'Thermal Node', status: 'active', position: [-6, 0, -4], value: 24.5 },
    { id: 'sim-sensor-2', type: 'humidity', name: 'Moisture Node', status: 'active', position: [6, 0, -4], value: 63 },
    { id: 'sim-sensor-3', type: 'motion', name: 'Security Beacon', status: 'idle', position: [0, 0, 8], value: 0 },
  ],
  zones: [
    { id: 'sim-zone-1', name: 'Crop Field A', position: [-10, 0, -8], size: [14, 1.5, 12], color: '#10b981', status: 'secure' },
    { id: 'sim-zone-2', name: 'Livestock Zone', position: [10, 0, -8], size: [12, 1.5, 12], color: '#f97316', status: 'warning' },
    { id: 'sim-zone-3', name: 'Drone Pad', position: [0, 0, 12], size: [10, 1.5, 10], color: '#38bdf8', status: 'secure' },
  ],
});

const tickEstateSimulation = (estateState) => {
  estateState.setRobots((prev) => prev.map((robot, index) => {
    const base = robot.position || [0, 0, 0];
    const phase = Date.now() / 800 + index;
    const nextX = base[0] + Math.sin(phase) * 0.22;
    const nextZ = base[2] + Math.cos(phase * 1.2) * 0.22;
    return {
      ...robot,
      position: [nextX, 1, nextZ],
      status: robot.status === 'active' ? 'active' : 'charging',
    };
  }));

  estateState.setSensors((prev) => prev.map((sensor, index) => {
    const baseValue = Number(sensor.value ?? 0);
    const drift = ((Math.sin(Date.now() / 1000 + index) + 1) / 2) * 2.4;
    const nextValue = sensor.type === 'motion'
      ? (Math.random() > 0.88 ? 1 : 0)
      : Math.min(100, Math.max(0, baseValue + (drift - 1.2) * (sensor.type === 'temperature' ? 0.7 : 0.9)));

    return {
      ...sensor,
      value: Number(nextValue.toFixed(sensor.type === 'temperature' ? 1 : 0)),
      status: nextValue > 80 || nextValue < 20 ? 'warning' : 'active',
    };
  }));

  estateState.setZones((prev) => prev.map((zone, index) => ({
    ...zone,
    status: index === 1 && Math.random() > 0.7 ? 'warning' : 'secure',
  })));
};

export default function Dashboard3D() {
  const { user, loading } = useCurrentUser();
  const estateState = useEstateState();
  const { socketConnected, realtimeError } = useEstateRealtime(estateState);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [creatorOpen, setCreatorOpen] = useState(true);

  useEffect(() => {
    if (!loading && user) {
      fetchInitialData();
    }
  }, [user, loading]);

  useEffect(() => {
    if (!user || loading) return undefined;

    if (!estateState.robots.length && !estateState.sensors.length && !estateState.zones.length) {
      const seeded = buildSimulatedEstate();
      estateState.setRobots(seeded.robots);
      estateState.setSensors(seeded.sensors);
      estateState.setZones(seeded.zones);
    }

    const interval = setInterval(() => {
      if (estateState.robots.length || estateState.sensors.length || estateState.zones.length) {
        tickEstateSimulation(estateState);
      }
    }, 2200);

    return () => clearInterval(interval);
  }, [user, loading, estateState]);

  const fetchInitialData = async () => {
    try {
      const token = localStorage.getItem('aegis_token');

      const [robotsRes, sensorsRes, zonesRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/robots`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/sensors`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/zones`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      const robots = robotsRes.ok ? await robotsRes.json() : [];
      const sensors = sensorsRes.ok ? await sensorsRes.json() : [];
      const zones = zonesRes.ok ? await zonesRes.json() : [];

      const robotsWithPositions = (Array.isArray(robots) ? robots : []).map((robot, idx) => ({
        ...robot,
        position: [-5 + (idx % 3) * 5, 1, 5 - Math.floor(idx / 3) * 5],
        status: robot.status || 'idle',
      }));

      const sensorsWithPositions = (Array.isArray(sensors) ? sensors : []).map((sensor, idx) => ({
        ...sensor,
        position: [-4 + (idx % 5) * 2, 0.5, 4 - Math.floor(idx / 5) * 4],
      }));

      const zonesWithPositions = (Array.isArray(zones) ? zones : []).map((zone, idx) => ({
        ...zone,
        position: [-5 + (idx % 2) * 10, 0, 5 - Math.floor(idx / 2) * 10],
        size: [3, 3, 3],
        color: ['#0088ff', '#00ffaa', '#88ff00', '#ff8800', '#ffaa00'][idx % 5],
      }));

      estateState.setRobots(robotsWithPositions);
      estateState.setSensors(sensorsWithPositions);
      estateState.setZones(zonesWithPositions);
    } catch (err) {
      console.error('Error fetching estate data:', err);
    }
  };

  const handleUpdateEntity = async (updatedData) => {
    try {
      const token = localStorage.getItem('aegis_token');
      const endpoint = `/api/v1/${selectedEntity.type}s/${selectedEntity.id}`;

      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updatedData),
      });

      if (res.ok) {
        const updated = await res.json();
        if (selectedEntity.type === 'robot') {
          estateState.updateRobot(selectedEntity.id, updated);
        } else if (selectedEntity.type === 'sensor') {
          estateState.updateSensor(selectedEntity.id, updated);
        } else if (selectedEntity.type === 'zone') {
          estateState.updateZone(selectedEntity.id, updated);
        }
        setSelectedEntity({ ...selectedEntity, ...updated });
      }
    } catch (err) {
      console.error('Error updating entity:', err);
    }
  };

  const handleDeleteEntity = async () => {
    if (!window.confirm(`Delete this ${selectedEntity.type}?`)) return;

    try {
      const token = localStorage.getItem('aegis_token');
      const endpoint = `/api/v1/${selectedEntity.type}s/${selectedEntity.id}`;

      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        if (selectedEntity.type === 'robot') {
          estateState.deleteRobot(selectedEntity.id);
        } else if (selectedEntity.type === 'sensor') {
          estateState.deleteSensor(selectedEntity.id);
        } else if (selectedEntity.type === 'zone') {
          estateState.deleteZone(selectedEntity.id);
        }
        setSelectedEntity(null);
      }
    } catch (err) {
      console.error('Error deleting entity:', err);
    }
  };

  const handleDuplicateEntity = async () => {
    try {
      const token = localStorage.getItem('aegis_token');
      const newEntity = {
        ...selectedEntity,
        id: undefined,
        name: `${selectedEntity.name} (Copy)`,
      };

      const endpoint = `/api/v1/${selectedEntity.type}s`;
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newEntity),
      });

      if (res.ok) {
        const created = await res.json();
        if (selectedEntity.type === 'robot') {
          estateState.addRobot(created);
        } else if (selectedEntity.type === 'sensor') {
          estateState.addSensor(created);
        } else if (selectedEntity.type === 'zone') {
          estateState.addZone(created);
        }
      }
    } catch (err) {
      console.error('Error duplicating entity:', err);
    }
  };

  const handleCreateRobot = async (data) => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/robots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        const robot = await res.json();
        estateState.addRobot({
          ...robot,
          position: [Math.random() * 10 - 5, 1, Math.random() * 10 - 5],
        });
      }
    } catch (err) {
      console.error('Error creating robot:', err);
    }
  };

  const handleCreateSensor = async (data) => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/sensors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        const sensor = await res.json();
        estateState.addSensor({
          ...sensor,
          position: [Math.random() * 10 - 5, 0.5, Math.random() * 10 - 5],
        });
      }
    } catch (err) {
      console.error('Error creating sensor:', err);
    }
  };

  const handleCreateZone = async (data) => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/zones`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        const zone = await res.json();
        estateState.addZone({
          ...zone,
          position: [Math.random() * 10 - 5, 0, Math.random() * 10 - 5],
          size: [3, 3, 3],
          color: '#00ffaa',
        });
      }
    } catch (err) {
      console.error('Error creating zone:', err);
    }
  };

  if (loading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-slate-950">
        <div className="text-aegis-muted animate-pulse text-center">
          <p className="text-lg">Loading 3D Estate Management...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="aegis-twin-page w-full h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <div className="aegis-twin-header px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-slate-900 to-slate-950">
        <h1 className="text-3xl font-bold text-aegis-primary tracking-[0.2em]">🌐 3D ESTATE MANAGEMENT</h1>
        <p className="text-xs text-aegis-muted mt-1 uppercase tracking-wider">
          Click entities to inspect • Use left panel to create • Right panel to edit
        </p>
      </div>

      {/* Main Content */}
      <div className="aegis-twin-layout flex-1 flex overflow-hidden">
        {/* 3D Scene */}
        <div className="aegis-twin-scene flex-1 min-w-0 relative">
          <DigitalTwinScene
            robots={estateState.robots}
            sensors={estateState.sensors}
            zones={estateState.zones}
            selectedEntity={selectedEntity}
            onEntitySelect={setSelectedEntity}
          />

          {/* Top Stats */}
          <div className="absolute top-6 right-6 z-10 bg-gradient-to-br from-black/60 to-black/40 border border-aegis-primary/30 rounded-lg p-4 font-mono text-xs text-white space-y-3">
            <div className="flex gap-4">
              <div>
                <p className="text-aegis-muted">Robots</p>
                <p className="text-lg font-bold text-cyan-400">{estateState.robots.length}</p>
              </div>
              <div>
                <p className="text-aegis-muted">Sensors</p>
                <p className="text-lg font-bold text-green-400">{estateState.sensors.length}</p>
              </div>
              <div>
                <p className="text-aegis-muted">Zones</p>
                <p className="text-lg font-bold text-purple-400">{estateState.zones.length}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <span className={`w-2 h-2 rounded-full ${socketConnected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
              <span>{socketConnected ? 'Realtime online' : 'Realtime offline'}</span>
            </div>
            {realtimeError && <div className="text-[10px] text-amber-300">{realtimeError}</div>}
          </div>
        </div>

        {/* Left Panel: Creator */}
        {creatorOpen && (
          <div className="aegis-twin-creator w-80 border-l border-slate-800 bg-slate-900/50 overflow-y-auto">
            <Creator3D
              onCreateRobot={handleCreateRobot}
              onCreateSensor={handleCreateSensor}
              onCreateZone={handleCreateZone}
              onClose={() => setCreatorOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Right Inspector */}
      {selectedEntity && (
        <Inspector3D
          selectedEntity={selectedEntity}
          onClose={() => setSelectedEntity(null)}
          onUpdate={handleUpdateEntity}
          onDelete={handleDeleteEntity}
          onDuplicate={handleDuplicateEntity}
        />
      )}

      {/* Back Button */}
      <div className="absolute top-6 left-6 z-20">
        <Link
          href="/estate-dashboard"
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded font-mono text-xs transition border border-slate-700"
        >
          ← Back
        </Link>
      </div>
    </div>
  );
}
