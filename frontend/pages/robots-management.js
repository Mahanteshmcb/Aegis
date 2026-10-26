import React, { useCallback, useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, Trash2, Edit2 } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import RobotForm from '../components/forms/RobotForm';
import Layout3D from '../components/Layout3D';
import Button3D from '../components/Button3D';
import Card3D from '../components/Card3D';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function RobotsManagement() {
  const { user, loading, token } = useCurrentUser();
  const estateState = useEstateState();
  const { setLoading: setEstateLoading, setRobots: setEstateRobots } = estateState;
  const [zones, setZones] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [commandingId, setCommandingId] = useState(null);
  const [integrationStatus, setIntegrationStatus] = useState(null);
  const canOperate = ['admin', 'superadmin', 'manager', 'operator'].includes(String(user?.role || '').toLowerCase());
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'field_rover',
    zone_id: '',
    status: 'stationary',
    battery: '',
  });
  const [search, setSearch] = useState('');

  const fetchRobots = useCallback(async () => {
    if (!token) return;
    try {
      setEstateLoading(true);
      const headers = { Authorization: `Bearer ${token}` };
      const [res, zonesRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }),
        fetch(`${API_URL}/api/v1/zones`, { headers }).catch(() => null),
      ]);
      if (!res.ok) throw new Error('Unable to load the robot fleet.');
      const [devices, zoneData] = await Promise.all([
        res.json(),
        zonesRes?.ok ? zonesRes.json().catch(() => []) : Promise.resolve([]),
      ]);
      const safeZones = Array.isArray(zoneData) ? zoneData : [];
      setZones(safeZones);
      const zoneNames = new Map(safeZones.map((zone) => [String(zone.id), zone.name]));
      const robots = (Array.isArray(devices) ? devices : []).filter((device) => device.kind === 'robot').map((device) => ({
        ...device,
        id: device.id ?? device.device_id,
        robot_id: device.device_id,
        type: device.device_type,
        battery: device.state?.battery ?? null,
        status: device.status || 'unknown',
        activity: device.state?.activity,
        zoneName: zoneNames.get(String(device.zone_id)) || (device.zone_id == null ? 'Unassigned' : `Zone ${device.zone_id}`),
      }));
      setEstateRobots(robots);
      setError('');
      setEstateLoading(false);
    } catch (err) {
      console.error('Error fetching robots:', err);
      setError(err.message || 'Unable to load the robot fleet.');
      setEstateLoading(false);
    }
  }, [setEstateLoading, setEstateRobots, token]);

  const fetchIntegrationStatus = useCallback(async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/api/v1/robotics/integrations`, {
        headers: { Authorization: 'Bearer ' + token },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to check robotics integrations.');
      setIntegrationStatus(result);
    } catch (err) {
      setIntegrationStatus({ error: err.message || 'Unable to check robotics integrations.' });
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) {
      fetchRobots();
      fetchIntegrationStatus();
    }
  }, [user, loading, fetchRobots, fetchIntegrationStatus]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (!token) throw new Error('Session expired. Please sign in again.');
      const method = editingId ? 'PUT' : 'POST';
      const endpoint = editingId ? `/api/v1/digital-twin/devices/${editingId}` : '/api/v1/digital-twin/devices';
      const selectedRobot = estateState.robots.find((robot) => String(robot.id) === String(editingId));
      const state = { ...(selectedRobot?.state || {}) };
      if (formData.battery !== '') state.battery = Number(formData.battery);
      state.activity = formData.status;
      const payload = editingId
        ? { name: formData.name.trim(), device_type: formData.type, zone_id: formData.zone_id === '' ? null : Number(formData.zone_id), state }
        : { device_id: `robot-${Date.now()}`, name: formData.name.trim(), kind: 'robot', device_type: formData.type || 'field_rover', zone_id: formData.zone_id === '' ? null : Number(formData.zone_id), position: { x: 0, y: 1, z: 0 }, status: 'online', state, control_mode: 'automation', automation_policy: {} };

      setSubmitting(true);
      setError('');
      const res = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const result = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(result.detail || 'Unable to save robot.');
      setSuccess(editingId ? 'Robot updated.' : 'Robot registered.');
      setFormData({ name: '', type: 'field_rover', zone_id: '', status: 'stationary', battery: '' });
      setEditingId(null);
      setShowForm(false);
      await fetchRobots();
    } catch (err) {
      console.error('Error saving robot:', err);
      setError(err.message || 'Unable to save robot.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this robot?')) return;

    try {
      if (!token) throw new Error('Session expired. Please sign in again.');
      const res = await fetch(`${API_URL}/api/v1/digital-twin/devices/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        setSuccess('Robot removed from the estate registry.');
        await fetchRobots();
      } else {
        const result = await res.json().catch(() => ({}));
        throw new Error(result.detail || 'Unable to delete robot.');
      }
    } catch (err) {
      console.error('Error deleting robot:', err);
      setError(err.message || 'Unable to delete robot.');
    }
  };

  const dispatchInspection = async (robot) => {
    if (!token) return setError('Session expired. Please sign in again.');
    setCommandingId(robot.id);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/v1/robotics/tasks`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: `inspect-${robot.robot_id}-${Date.now()}`,
          robot_id: robot.robot_id,
          operation_type: 'INSPECT',
          priority: 5,
          task_detail: { zone_id: robot.zone_id, robot_name: robot.name },
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Inspection mission could not be dispatched.');
      setSuccess(`Inspection mission queued for ${robot.name}.`);
    } catch (err) {
      setError(err.message || 'Inspection mission could not be dispatched.');
    } finally {
      setCommandingId(null);
    }
  };

  const stopRobot = async (robot) => {
    if (!token) {
      setError('Session expired. Please sign in again.');
      return;
    }
    if (!window.confirm(`Issue emergency stop to ${robot.name}?`)) return;
    setCommandingId(robot.id);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/v1/robotics/emergency-stop`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ robot_id: robot.robot_id, robot_type: robot.type }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Emergency stop was rejected.');
      setSuccess(`Emergency stop issued to ${robot.name}.`);
      await fetchRobots();
    } catch (err) {
      setError(err.message || 'Emergency stop failed.');
    } finally {
      setCommandingId(null);
    }
  };

  const handleEdit = (robot) => {
    setFormData({
      name: robot.name || '',
      type: robot.type || 'wheeled',
      zone_id: robot.zone_id ?? '',
      status: robot.activity || 'stationary',
      battery: robot.battery ?? '',
    });
    setEditingId(robot.id);
    setShowForm(true);
  };

  const filteredRobots = estateState.robots.filter((r) =>
    r.name?.toLowerCase().includes(search.toLowerCase()) ||
    r.type?.toLowerCase().includes(search.toLowerCase()) ||
    r.robot_id?.toLowerCase().includes(search.toLowerCase()) ||
    r.zoneName?.toLowerCase().includes(search.toLowerCase())
  );

  const typeIcons = {
    field_rover: '🤖',
    inspection_drone: '🚁',
    agri_swarm_bot: '🤖',
  };

  const statusColors = {
    active: 'from-green-600 to-emerald-600',
    charging: 'from-yellow-600 to-amber-600',
    idle: 'from-slate-600 to-slate-700',
    online: 'from-green-600 to-emerald-600',
    offline: 'from-slate-600 to-slate-700',
    error: 'from-red-600 to-orange-600',
  };

  if (loading) {
    return (
      <Layout3D title="ROBOT MANAGEMENT" icon="🤖" subtitle="Loading fleet data...">
        <div className="flex items-center justify-center h-96">
          <div className="text-aegis-muted animate-pulse text-lg">Scanning robot network...</div>
        </div>
      </Layout3D>
    );
  }

  return (
    <Layout3D
      title="ROBOT MANAGEMENT"
      icon="🤖"
      subtitle="Manage, monitor, and control your autonomous robot fleet"
    >
      <div className="space-y-8">
        {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>}
        {success && <div role="status" className="rounded border border-emerald-700 bg-emerald-900/20 p-3 text-sm text-emerald-200">{success}</div>}
        <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4" aria-label="Robotics integrations">
          <h2 className="text-lg font-semibold text-white">Robotics integrations</h2>
          {!integrationStatus ? <p className="mt-2 text-sm text-slate-400">Checking configured transports...</p> : integrationStatus.error ? (
            <p role="status" className="mt-2 text-sm text-amber-200">{integrationStatus.error}</p>
          ) : (
            <div className="mt-3 grid gap-3 text-sm md:grid-cols-3">
              <div><p className="text-slate-400">Aegis fleet gRPC</p><p className="text-white">{integrationStatus.fleet_grpc?.connected ? 'Connected · software simulator' : 'Offline'}</p><p className="text-xs text-slate-500">{integrationStatus.fleet_grpc?.address}</p></div>
              <div><p className="text-slate-400">Vryndara gRPC</p><p className="text-white">{integrationStatus.vryndara_grpc?.connected ? 'Connected' : 'Offline · configure/start kernel'}</p><p className="text-xs text-slate-500">{integrationStatus.vryndara_grpc?.address}</p></div>
              <div><p className="text-slate-400">ROS 2 hardware</p><p className="text-white">{integrationStatus.ros2?.hardware_control_enabled ? 'Enabled' : 'Disabled · hardware profile pending'}</p><p className="text-xs text-slate-500">{integrationStatus.ros2?.runtime_available ? 'ROS 2 runtime detected' : 'ROS 2 runtime not installed in this backend environment'}</p></div>
            </div>
          )}
          <p className="mt-3 text-xs text-amber-300">Robot commands in this environment are simulated. No ROS 2 command is sent to physical hardware.</p>
        </section>
        {/* Controls Bar */}
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-3 text-aegis-muted" size={20} />
            <input
              type="text"
              placeholder="Search robots by name or type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-black/50 border border-cyan-500/30 hover:border-cyan-500/60 rounded-lg text-white placeholder-aegis-muted text-sm focus:border-cyan-400 focus:outline-none transition-all"
            />
          </div>
          <Button3D
            variant="primary"
            size="md"
            icon={showForm ? undefined : Plus}
            onClick={() => {
              setShowForm(!showForm);
              setEditingId(null);
              setFormData({ name: '', type: 'field_rover', zone_id: '', status: 'stationary', battery: '' });
            }}
          >
            {showForm ? '✕ CANCEL' : '+ ADD ROBOT'}
          </Button3D>
        </div>

        {/* Add/Edit Form */}
        {showForm && (
          <Card3D variant="primary" glowing glowColor="#00f2ff">
            <RobotForm
              formData={formData}
              setFormData={setFormData}
              zones={zones}
              submitting={submitting}
              editingId={editingId}
              onSubmit={handleSubmit}
              onCancel={() => {
                setShowForm(false);
                setEditingId(null);
                setFormData({ name: '', type: 'field_rover', zone_id: '', status: 'stationary', battery: '' });
              }}
            />
          </Card3D>
        )}

        {/* Stats Bar */}
        <div className="grid grid-cols-3 gap-4">
          <Card3D variant="primary">
            <div className="text-center">
              <p className="text-3xl font-bold text-cyan-300">{estateState.robots.length}</p>
              <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Total Robots</p>
            </div>
          </Card3D>
          <Card3D variant="success">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-300">
                {estateState.robots.filter((robot) => ['patrolling', 'executing', 'active'].includes(String(robot.activity || '').toLowerCase())).length}
              </p>
              <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Active</p>
            </div>
          </Card3D>
          <Card3D variant="warning">
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-300">
                {(() => {
                  const reportedBatteries = estateState.robots
                    .filter((robot) => robot.battery !== null && robot.battery !== undefined && robot.battery !== '')
                    .map((robot) => Number(robot.battery))
                    .filter(Number.isFinite);
                  return reportedBatteries.length
                    ? `${Math.round(reportedBatteries.reduce((total, battery) => total + battery, 0) / reportedBatteries.length)}%`
                    : '—';
                })()}
              </p>
              <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Avg Battery</p>
            </div>
          </Card3D>
        </div>

        {/* Robots Grid */}
        <div>
          {filteredRobots.length === 0 ? (
            <Card3D variant="default" className="text-center py-12">
              <p className="text-aegis-muted text-lg">No robots found</p>
              <p className="text-xs text-aegis-muted mt-2">Create a new robot to get started</p>
            </Card3D>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRobots.map((robot) => (
                <Card3D
                  key={robot.id}
                  variant={
                    robot.activity === 'patrolling'
                      ? 'success'
                      : robot.status === 'charging'
                      ? 'warning'
                      : robot.status === 'error'
                      ? 'danger'
                      : 'default'
                  }
                  glowing
                  glowColor={
                    robot.activity === 'patrolling'
                      ? '#00FF00'
                      : robot.status === 'charging'
                      ? '#FFD700'
                      : robot.status === 'error'
                      ? '#FF0000'
                      : '#666666'
                  }
                >
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-2xl">{typeIcons[robot.type] || '🤖'}</p>
                        <h3 className="text-lg font-bold text-white mt-2">
                          {robot.name || `Robot ${robot.id}`}
                        </h3>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold text-white br-linear-to-r ${statusColors[robot.status] || statusColors.idle}`}
                      >
                        {(robot.status || 'unknown').toUpperCase()}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Type:</span>
                        <span className="text-white">{robot.type || 'Unknown type'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Zone:</span>
                        <span className="text-white">{robot.zoneName || 'Unassigned'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Activity:</span>
                        <span className="text-white">{robot.activity || 'Unknown'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Battery:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all ${
                                robot.battery >= 75
                                  ? 'bg-green-500'
                                  : robot.battery >= 50
                                  ? 'bg-yellow-500'
                                  : robot.battery >= 25
                                  ? 'bg-orange-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(0, Number(robot.battery) || 0))}%` }}
                            />
                          </div>
                          <span className="text-white font-mono">{robot.battery !== null && robot.battery !== undefined && robot.battery !== '' && Number.isFinite(Number(robot.battery)) ? `${robot.battery}%` : 'Unknown'}</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-4">
                      <Button3D
                        variant="primary"
                        size="sm"
                        disabled={!canOperate || commandingId === robot.id}
                        onClick={() => dispatchInspection(robot)}
                      >
                        {commandingId === robot.id ? 'SENDING...' : 'INSPECT'}
                      </Button3D>
                      <Button3D
                        variant="danger"
                        size="sm"
                        disabled={!canOperate || commandingId === robot.id}
                        onClick={() => stopRobot(robot)}
                      >
                        EMERGENCY STOP
                      </Button3D>
                      <Button3D
                        variant="secondary"
                        size="sm"
                        icon={Edit2}
                        disabled={submitting}
                        onClick={() => handleEdit(robot)}
                      >
                        EDIT
                      </Button3D>
                      <Button3D
                        variant="danger"
                        size="sm"
                        icon={Trash2}
                        disabled={submitting}
                        onClick={() => handleDelete(robot.id)}
                      >
                        DELETE
                      </Button3D>
                    </div>
                  </div>
                </Card3D>
              ))}
            </div>
          )}
        </div>

        {/* Back Button */}
        <div className="flex gap-4 pt-8">
          <Link href="/estate-dashboard">
            <Button3D variant="ghost">← BACK TO DASHBOARD</Button3D>
          </Link>
          <Link href="/3d-scene">
            <Button3D variant="primary">🌐 VIEW IN 3D</Button3D>
          </Link>
        </div>
      </div>
    </Layout3D>
  );
}
