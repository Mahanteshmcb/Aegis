import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  Zap,
  Droplets,
  Thermometer,
  Leaf,
  Lock,
  Beaker,
  Package,
  Trash2,
  TrendingUp,
  Bell,
  Settings,
  Eye,
  EyeOff,
  Plus,
  Trash,
  Edit2,
  Check,
  X,
} from 'lucide-react';
import dynamic from 'next/dynamic';
import Layout3D from '../components/Layout3D';
import Card3D from '../components/Card3D';
import Button3D from '../components/Button3D';
const EstateScene = dynamic(() => import('../components/3d/EstateScene'), { ssr: false });
const Monitor3D = dynamic(() => import('../components/Monitor3D'), { ssr: false });
import { LiveFeedsGrid } from '../components/LiveFeeds';
import RealTimeMetrics from '../components/RealTimeMetrics';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import useEstateRealtime from '../hooks/useEstateRealtime';
import { getAuthToken } from '../utils/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const ESTATE_SYSTEMS = [
  { id: 'climate', name: 'Climate Control', icon: Thermometer, color: '#ff6b35' },
  { id: 'water', name: 'Water Management', icon: Droplets, color: '#004e89' },
  { id: 'energy', name: 'Energy Systems', icon: Zap, color: '#f1b233' },
  { id: 'biosphere', name: 'Biosphere Ops', icon: Leaf, color: '#06a77d' },
  { id: 'security', name: 'Security', icon: Lock, color: '#d62828' },
  { id: 'lab', name: 'Laboratory', icon: Beaker, color: '#9d4edd' },
  { id: 'storage', name: 'Storage', icon: Package, color: '#7209b7' },
  { id: 'waste', name: 'Waste Mgmt', icon: Trash2, color: '#8ecae6' },
];

const MOCK_ALERTS = [
  { id: 1, type: 'critical', system: 'climate', message: 'CO2 levels exceeding threshold', timestamp: new Date(), status: 'active' },
  { id: 2, type: 'warning', system: 'energy', message: 'Solar panels detected anomaly', timestamp: new Date(Date.now() - 300000), status: 'active' },
  { id: 3, type: 'info', system: 'water', message: 'Recycling system maintenance scheduled', timestamp: new Date(Date.now() - 600000), status: 'resolved' },
];

const getMockSystemData = (systemId) => {
  const mockData = {
    climate: { temperature: 22.5, humidity: 65, co2: 520, vocs: 0.8, status: 'healthy', hvacStatus: 'cooling', lastUpdate: new Date() },
    water: { level: 85, flowRate: 2.3, recycleStatus: 92, quality: 'excellent', status: 'healthy', nextMaintenance: '2 days' },
    energy: { solarGeneration: 4.2, batterySOC: 78, batteryHealth: 96, powerDraw: 2.1, status: 'healthy', forecast: 'excellent' },
    biosphere: { robotsActive: 12, cropHealth: 94, soilQuality: 'optimal', pestsDetected: 0, status: 'healthy', nextHarvest: '3 days' },
    security: { perimetersSecure: 'yes', accessGranted: 0, accessDenied: 0, status: 'secure', lastIncident: 'none' },
    lab: { activeExperiments: 5, equipmentStatus: 'operational', sampleCount: 142, status: 'operational' },
    storage: { capacity: 85, temperature: 18, humidity: 45, status: 'optimal' },
    waste: { processingRate: 65, sortingEfficiency: 94, status: 'processing' },
  };
  return mockData[systemId] || {};
};

const getHealthColor = (status) => {
  switch (status) {
    case 'healthy':
    case 'excellent':
    case 'operational':
    case 'optimal':
    case 'secure':
      return '#06a77d';
    case 'warning':
    case 'degraded':
      return '#f1b233';
    case 'critical':
    case 'alert':
      return '#d62828';
    default:
      return '#757575';
  }
};

const normalizeSelectedEntity = (entity) => {
  if (!entity) return null;
  const type = entity.type || (entity.status ? 'robot' : entity.zone_id || entity.zone ? 'zone' : 'sensor');
  return {
    ...entity,
    id: entity.id ?? entity.robot_id ?? entity.sensor_id,
    robot_id: entity.robot_id ?? entity.id,
    sensor_id: entity.sensor_id ?? entity.id,
    type,
  };
};

function SystemStatusCard({ system, data }) {
  const Icon = system.icon;
  return (
    <Card3D variant="primary" glowing className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon size={20} style={{ color: system.color }} />
          <div>
            <p className="text-xs font-bold text-cyan-300">{system.name}</p>
            <p className="text-[11px] text-slate-400 mt-1">Monitoring</p>
          </div>
        </div>
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getHealthColor(data.status || 'unknown') }} />
      </div>
      <div className="mt-3 text-[10px] text-slate-300 space-y-1">
        {Object.entries(data)
          .slice(0, 3)
          .map(([key, value]) => key !== 'status' && <div key={key} className="flex justify-between"><span>{key}:</span><span className="text-cyan-200 font-mono">{typeof value === 'number' ? value.toFixed(1) : String(value).substring(0, 20)}</span></div>)}
      </div>
    </Card3D>
  );
}

function AlertPanel({ alerts }) {
  const criticalCount = alerts.filter((a) => a.type === 'critical').length;
  const warningCount = alerts.filter((a) => a.type === 'warning').length;
  return (
    <Card3D variant="default" glowing glowColor="#ff6b35" className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <Bell size={16} className="text-red-400" />
        <h3 className="text-sm font-bold text-red-300">System Alerts</h3>
        <span className="text-xs bg-red-900/30 text-red-200 px-2 py-1 rounded">{criticalCount + warningCount} Active</span>
      </div>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {alerts.filter((a) => a.status === 'active').map((alert) => (
          <div key={alert.id} className="p-2 rounded bg-slate-900/50 border-l-2" style={{ borderColor: alert.type === 'critical' ? '#d62828' : '#f1b233' }}>
            <p className="text-xs font-semibold text-slate-200">{alert.message}</p>
            <p className="text-[10px] text-slate-400 mt-1">{alert.system} • {alert.timestamp.toLocaleTimeString()}</p>
          </div>
        ))}
      </div>
    </Card3D>
  );
}

function PredictiveMaintenancePanel() {
  const predictions = [
    { system: 'Climate HVAC', daysUntil: 5, confidence: 92, action: 'Filter replacement' },
    { system: 'Solar Inverter', daysUntil: 12, confidence: 87, action: 'Firmware update' },
    { system: 'Battery Pack', daysUntil: 45, confidence: 79, action: 'Capacity test' },
  ];
  return (
    <Card3D variant="success" glowing className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp size={16} className="text-green-400" />
        <h3 className="text-sm font-bold text-green-300">Predictive Maintenance</h3>
      </div>
      <div className="space-y-2">
        {predictions.map((pred, idx) => (
          <div key={idx} className="p-2 rounded bg-slate-900/50 border-l-2 border-green-600">
            <div className="flex justify-between items-start">
              <p className="text-xs font-semibold text-slate-200">{pred.system}</p>
              <span className="text-[10px] bg-green-900/30 text-green-200 px-1.5 py-0.5 rounded">{pred.daysUntil} days</span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">{pred.action}</p>
            <div className="mt-2 h-1 bg-slate-700 rounded overflow-hidden">
              <div className="h-full bg-green-500" style={{ width: `${pred.confidence}%` }} />
            </div>
          </div>
        ))}
      </div>
    </Card3D>
  );
}

export default function EstateDashboard() {
  const { user, loading } = useCurrentUser();
  const estateState = useEstateState();
  const [viewMode, setViewMode] = useState('realworld');
  const [lightIntensity, setLightIntensity] = useState(1);
  const [autoRotate, setAutoRotate] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [entityType, setEntityType] = useState('sensor');
  const [createData, setCreateData] = useState({ name: '', type: '', location: '' });
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [systemDataCache, setSystemDataCache] = useState({});
  const [alerts, setAlerts] = useState(MOCK_ALERTS);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Metrics from dashboard
  const [metrics, setMetrics] = useState({ zones: 0, sensors: 0, users: 0, auditLogs: 0 });
  const [systemHealth, setSystemHealth] = useState({ status: 'healthy', latency: 0 });
  const [commandLoading, setCommandLoading] = useState(false);
  const [commandResult, setCommandResult] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const { socketConnected, realtimeError, liveSystemStatus, liveSensorReadings } = useEstateRealtime(estateState);

  useEffect(() => {
    if (!loading && user) {
      fetchInitialData();
    }
  }, [user, loading]);

  useEffect(() => {
    if (!liveSystemStatus?.systems?.length) return;

    setSystemHealth((prev) => ({
      ...prev,
      status: liveSystemStatus.systems.some((s) => s.status === 'degraded') ? 'degraded' : 'healthy',
      latency: 0,
    }));

    setSystemDataCache((prevCache) => {
      const updated = { ...prevCache };
      liveSystemStatus.systems.forEach((system) => {
        const id = system.id === 'comms' ? 'communications' : system.id;
        updated[id] = {
          ...updated[id],
          status: system.status,
          health_score: system.health_score || 0,
          last_update: system.last_update,
          data: updated[id]?.data || {},
        };
      });
      return updated;
    });
  }, [liveSystemStatus]);

  useEffect(() => {
    if (!user || !autoRefresh) return undefined;

    const timer = window.setInterval(() => {
      fetchInitialData();
    }, refreshInterval);

    return () => {
      window.clearInterval(timer);
    };
  }, [user, autoRefresh, refreshInterval]);

  const fetchInitialData = async () => {
    try {
      setIsRefreshing(true);
      setError(null);
      estateState.setLoading(true);
      const token = getAuthToken();
      const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

      // Fetch entities and metrics in parallel
      const [estateStatusRes, robotsRes, sensorsRes, zonesRes, auditRes, usersRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/estate/status`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/robotics/active`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/sensors`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/zones`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/audit`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/auth/users`, { headers: authHeaders }).catch(() => ({ ok: false })),
      ]);

      const estateStatus = estateStatusRes?.ok ? await estateStatusRes.json().catch(() => null) : null;
      const robots = robotsRes?.ok ? await robotsRes.json().catch(() => []) : [];
      const sensors = sensorsRes?.ok ? await sensorsRes.json().catch(() => []) : [];
      const zones = zonesRes?.ok ? await zonesRes.json().catch(() => []) : [];
      const auditLogs = auditRes?.ok ? await auditRes.json().catch(() => []) : [];
      const users = usersRes?.ok ? await usersRes.json().catch(() => []) : [];
      const userCount = Array.isArray(users) && users.length > 0 ? users.length : 1;

      const robotsWithPositions = (Array.isArray(robots) ? robots : []).map((robot, idx) => ({
        ...robot,
        id: robot.id ?? robot.robot_id ?? `robot_${idx}`,
        robot_id: robot.robot_id ?? robot.id ?? `robot_${idx}`,
        type: 'robot',
        position: [-(6 - (idx % 4)) + (idx % 4) * 4, 1, 6 - Math.floor(idx / 4) * 4],
        status: robot.status || (idx % 2 === 0 ? 'active' : 'charging'),
      }));

      const sensorsWithPositions = (Array.isArray(sensors) ? sensors : []).map((sensor, idx) => ({
        ...sensor,
        id: sensor.id ?? sensor.sensor_id ?? `sensor_${idx}`,
        sensor_id: sensor.sensor_id ?? sensor.id ?? `sensor_${idx}`,
        type: 'sensor',
        position: [-(7 - (idx % 5)) + (idx % 5) * 3, 2, 7 - Math.floor(idx / 5) * 3],
        sensor_type: sensor.type || ['temperature', 'humidity', 'light', 'pressure', 'motion'][idx % 5],
        value: sensor.value ?? `${Math.floor(20 + idx * 2)}${idx % 2 === 0 ? '°C' : '%'}`,
      }));

      const zonesWithPositions = (Array.isArray(zones) ? zones : []).map((zone, idx) => ({
        ...zone,
        id: zone.id ?? `zone_${idx}`,
        type: 'zone',
        position: [-(6 - (idx % 2)) + (idx % 2) * 12, 0, 6 - Math.floor(idx / 2) * 10],
        size: [3 + (idx % 2), 3 + (idx % 3), 3 + ((idx + 1) % 2)],
        color: ['#0088ff', '#00ffaa', '#88ff00', '#ff8800', '#ffaa00'][idx % 5],
      }));

      // Update entity state
      estateState.setRobots(robotsWithPositions);
      estateState.setSensors(sensorsWithPositions);
      estateState.setZones(zonesWithPositions);
      
      // Update metrics
      setMetrics({
        zones: Array.isArray(zones) ? zones.length : 0,
        sensors: Array.isArray(sensors) ? sensors.length : 0,
        users: userCount,
        auditLogs: Array.isArray(auditLogs) ? auditLogs.length : 0,
      });

      estateState.updateMetrics({
        activeRobots: robotsWithPositions.filter((robot) => robot.status === 'active').length,
        sensorsOnline: sensorsWithPositions.length,
        systemHealth: estateStatus?.overall_health ?? 96,
        cpuUsage: 42,
        memoryUsage: 58,
        networkLatency: 14,
      });
      setSystemHealth((prev) => ({
        ...prev,
        status: estateStatus?.overall_health >= 80 ? 'healthy' : estateStatus?.overall_health >= 60 ? 'degraded' : 'critical',
      }));

      if (estateStatus) {
        setSystemDataCache((prev) => ({
          ...prev,
          climate: {
            ...prev.climate,
            status: estateStatus.climate?.status || prev.climate?.status,
            health_score: estateStatus.climate?.health_score || prev.climate?.health_score,
            last_update: estateStatus.climate?.last_update || prev.climate?.last_update,
          },
          energy: {
            ...prev.energy,
            status: estateStatus.energy?.status || prev.energy?.status,
            health_score: estateStatus.energy?.health_score || prev.energy?.health_score,
            last_update: estateStatus.energy?.last_update || prev.energy?.last_update,
          },
          security: {
            ...prev.security,
            status: estateStatus.security?.status || prev.security?.status,
            health_score: estateStatus.security?.health_score || prev.security?.health_score,
            last_update: estateStatus.security?.last_update || prev.security?.last_update,
          },
          water: {
            ...prev.water,
            status: estateStatus.water?.status || prev.water?.status,
            health_score: estateStatus.water?.health_score || prev.water?.health_score,
            last_update: estateStatus.water?.last_update || prev.water?.last_update,
          },
          communications: {
            ...prev.communications,
            status: estateStatus.communications?.status || prev.communications?.status,
            health_score: estateStatus.communications?.health_score || prev.communications?.health_score,
            last_update: estateStatus.communications?.last_update || prev.communications?.last_update,
          },
        }));
      }

      const promises = ESTATE_SYSTEMS.map((sys) => Promise.resolve().then(() => setSystemDataCache((prev) => ({ ...prev, [sys.id]: getMockSystemData(sys.id) }))));
      await Promise.all(promises);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Dashboard data fetch failed:', error);
      setError(error.message || 'Unable to load estate data.');
      estateState.setError(error.message || 'Unable to load estate data.');
    } finally {
      estateState.setLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleEntityDelete = useCallback(async (type, id) => {
    const token = getAuthToken();
    try {
      setError(null);
      setIsRefreshing(true);
      if (type === 'robot') {
        throw new Error('Robot deletion is not available from this dashboard. Use fleet management tools instead.');
      }
      const endpoint = type === 'sensor' ? 'sensors' : 'zones';
      
      const response = await fetch(`${API_URL}/api/v1/${endpoint}/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      }).catch((err) => ({ ok: false, statusText: err.message }));
      
      if (!response.ok) {
        const errorData = await response.json?.().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete ${type}. Please try again.`);
      }
      
      // Show success message
      const successMsg = `${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully`;
      setError(null);
      setSelectedEntity(null);
      
      // Give UI time to update before refreshing
      setTimeout(() => fetchInitialData(), 300);
    } catch (error) {
      console.error('Error deleting entity:', error);
      setError(error.message || `Failed to delete ${type}. Please check the connection and try again.`);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  const handleEntityCreate = useCallback(async (type, data) => {
    try {
      // Validation
      if (!data.name?.trim()) {
        setError('⚠ Please enter a name for the entity');
        return;
      }
      if (data.name.length > 100) {
        setError('⚠ Entity name cannot exceed 100 characters');
        return;
      }
      if (!data.type?.trim()) {
        setError('⚠ Please select or enter a type for the entity');
        return;
      }
      if (data.type.length > 50) {
        setError('⚠ Entity type cannot exceed 50 characters');
        return;
      }
      
      const token = getAuthToken();
      if (!token) {
        setError('Session expired. Please log in again.');
        return;
      }
      
      setIsRefreshing(true);
      setError(null);
      
      const endpoint = type === 'robot' ? 'robots' : type === 'sensor' ? 'sensors' : 'zones';
      const response = await fetch(`${API_URL}/api/v1/${endpoint}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: data.name.trim(),
          type: data.type.trim(),
          location: data.location?.trim() || '',
        }),
      }).catch((err) => ({ ok: false, statusText: err.message }));
      
      if (!response.ok) {
        const errorData = await response.json?.().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create ${type}. ${response.status === 400 ? 'Check your input and try again.' : 'Please contact support if the problem persists.'}`);
      }
      
      // Success
      setShowCreateForm(false);
      setCreateData({ name: '', type: '', location: '' });
      setEntityType('sensor'); // Reset to default
      setStatusMessage('Entity created successfully.');
      
      // Give UI time to update before refreshing
      setTimeout(() => fetchInitialData(), 300);
    } catch (error) {
      console.error('Error creating entity:', error);
      setError(error.message || `Failed to create entity. Please check the connection and try again.`);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  const dispatchRobotTask = useCallback(async (operationType) => {
    if (!selectedEntity || selectedEntity.type !== 'robot') return;
    const token = getAuthToken();
    if (!token) {
      setError('Session expired. Please log in again.');
      return;
    }

    setCommandLoading(true);
    setError(null);

    try {
      const payload = {
        task_id: `task-${Date.now()}`,
        robot_id: selectedEntity.robot_id ?? selectedEntity.id,
        operation_type: operationType,
        priority: 5,
        task_detail: {
          robot_name: selectedEntity.name,
          target_zone: selectedEntity.zone_id || selectedEntity.zone || null,
        },
      };

      const response = await fetch(`${API_URL}/api/v1/robotics/tasks`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(result?.detail || result?.message || 'Robot task failed');
      }

      setCommandResult(result);
      setStatusMessage('Robot task dispatched successfully.');
      setSystemHealth((prev) => ({ ...prev, latency: prev.latency }));
    } catch (err) {
      setError(err.message || 'Failed to dispatch robot task');
    } finally {
      setCommandLoading(false);
    }
  }, [selectedEntity]);

  const dispatchRobotStop = useCallback(async () => {
    if (!selectedEntity || selectedEntity.type !== 'robot') return;
    const token = getAuthToken();
    if (!token) {
      setError('Session expired. Please log in again.');
      return;
    }

    setCommandLoading(true);
    setError(null);

    try {
      const payload = {
        robot_id: selectedEntity.robot_id ?? selectedEntity.id,
        robot_type: selectedEntity.type || 'AEGIS_ROVER',
      };

      const response = await fetch(`${API_URL}/api/v1/robotics/emergency-stop`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(result?.detail || result?.message || 'Emergency stop failed');
      }

      setCommandResult(result);
    } catch (err) {
      setError(err.message || 'Failed to send stop command');
    } finally {
      setCommandLoading(false);
    }
  }, [selectedEntity]);

  const scheduleZoneTask = useCallback(async (operationType) => {
    if (!selectedEntity || selectedEntity.type !== 'zone') return;
    const token = getAuthToken();
    if (!token) {
      setError('Session expired. Please log in again.');
      return;
    }

    setCommandLoading(true);
    setError(null);

    try {
      const payload = {
        task_id: `schedule-${Date.now()}`,
        operation_type: operationType,
        zone_id: selectedEntity.id,
        priority: 5,
        task_detail: {
          zone_name: selectedEntity.name,
        },
      };

      const response = await fetch(`${API_URL}/api/v1/robotics/schedule/enqueue`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(result?.detail || result?.message || 'Zone task failed');
      }

      setCommandResult(result);
    } catch (err) {
      setError(err.message || 'Failed to schedule zone task');
    } finally {
      setCommandLoading(false);
    }
  }, [selectedEntity]);

  if (loading || estateState.loading) {
    return (
      <Layout3D title="Estate Dashboard" icon="🏢" subtitle="Loading...">
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-cyan-900/30 animate-spin mb-4">
              <div className="w-8 h-8 rounded-full border-2 border-transparent border-t-cyan-400 border-r-cyan-400"></div>
            </div>
            <p className="text-slate-300 font-semibold">Initializing Estate Command Center...</p>
            <p className="text-slate-400 text-sm mt-2">Fetching zones, sensors, and system data</p>
          </div>
        </div>
      </Layout3D>
    );
  }

  return (
    <Layout3D title="Estate Dashboard" icon="🏢" subtitle="Unified command center for all estate systems">
      {error && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-700/50 rounded-lg text-red-300 text-sm flex items-center justify-between animate-pulse">
          <span className="flex items-center gap-2">
            <AlertCircle size={18} />
            {error}
          </span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300 font-bold text-lg">✕</button>
        </div>
      )}
      
      <div className="space-y-6">
        {/* Welcome Header with Refresh */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-4xl font-bold text-cyan-300 tracking-[0.2em] mb-2">Estate Command Center</h1>
            <p className="text-slate-300 text-sm">Welcome, {user?.email}. Monitor & manage all zones, sensors, systems and data in one unified interface</p>
            <p className="text-xs text-slate-500 mt-1">
              Realtime connection: <span className={`font-semibold ${socketConnected ? 'text-green-300' : 'text-red-300'}`}>{socketConnected ? 'Online' : 'Offline'}</span>
              {liveSystemStatus?.timestamp ? ` • Last status ${new Date(liveSystemStatus.timestamp).toLocaleTimeString()}` : ''}
              {realtimeError ? ` • ${realtimeError}` : ''}
            </p>
          </div>
          <div className="flex gap-3 items-center flex-wrap">
            <button onClick={() => fetchInitialData()} className="px-4 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 rounded-lg text-blue-300 text-sm transition-all disabled:opacity-50" disabled={isRefreshing}>
              {isRefreshing ? '⟳ Syncing...' : '⟳ Refresh'}
            </button>
            <label className="flex items-center gap-2 text-sm text-slate-300 hover:text-slate-200 cursor-pointer transition-colors">
              <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} className="w-4 h-4 accent-blue-500" />
              Auto
            </label>
          </div>
        </div>

        {error && <div className="mb-6 p-4 bg-red-900/20 border border-red-700/50 rounded-lg text-red-300 text-sm flex items-center justify-between"><span>⚠️ {error}</span><button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">✕</button></div>}
        
        {lastRefresh && <div className="mb-4 text-xs text-slate-400 text-right">Last updated: {lastRefresh.toLocaleTimeString()}</div>}

        {/* Quick Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-purple-900/20 to-violet-900/20 border border-purple-700/30 rounded-lg p-6 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase text-purple-400 font-semibold">System Status</p>
              <p className="text-2xl font-bold text-purple-300 mt-2">Operational</p>
            </div>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          </div>
        </div>

        {/* Key Metrics Cards - from Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-6">
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/50 rounded-lg p-6 hover:border-blue-600/80 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-aegis-muted text-sm font-semibold uppercase tracking-wider">Zones</p>
                <p className="text-4xl font-bold text-blue-400 mt-2">{isRefreshing ? '—' : metrics.zones}</p>
              </div>
              <div className="text-3xl text-blue-500 opacity-50">📍</div>
            </div>
            <p className="text-aegis-muted text-xs mt-4">Active security zones</p>
            <Link href="/zones" className="text-blue-400 text-xs font-semibold mt-4 inline-block hover:text-blue-300">Manage Zones →</Link>
          </div>

          <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/50 rounded-lg p-6 hover:border-green-600/80 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-aegis-muted text-sm font-semibold uppercase tracking-wider">Sensors</p>
                <p className="text-4xl font-bold text-green-400 mt-2">{isRefreshing ? '—' : metrics.sensors}</p>
              </div>
              <div className="text-3xl text-green-500 opacity-50">📊</div>
            </div>
            <p className="text-aegis-muted text-xs mt-4">IoT devices online</p>
            <Link href="/sensors" className="text-green-400 text-xs font-semibold mt-4 inline-block hover:text-green-300">View Sensors →</Link>
          </div>

          <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/10 border border-yellow-700/50 rounded-lg p-6 hover:border-yellow-600/80 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-aegis-muted text-sm font-semibold uppercase tracking-wider">Audit Logs</p>
                <p className="text-4xl font-bold text-yellow-400 mt-2">{isRefreshing ? '—' : metrics.auditLogs}</p>
              </div>
              <div className="text-3xl text-yellow-500 opacity-50">📋</div>
            </div>
            <p className="text-aegis-muted text-xs mt-4">Compliance events recorded</p>
            <Link href="/audit-logs" className="text-yellow-400 text-xs font-semibold mt-4 inline-block hover:text-yellow-300">View Logs →</Link>
          </div>

          <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-700/50 rounded-lg p-6 hover:border-red-600/80 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-aegis-muted text-sm font-semibold uppercase tracking-wider">Users</p>
                <p className="text-4xl font-bold text-red-400 mt-2">{isRefreshing ? '—' : metrics.users}</p>
              </div>
              <div className="text-3xl text-red-500 opacity-50">👥</div>
            </div>
            <p className="text-aegis-muted text-xs mt-4">Active tenant users</p>
            {user?.role === 'admin' && (
              <Link href="/admin/users" className="text-red-400 text-xs font-semibold mt-4 inline-block hover:text-red-300">Manage Users →</Link>
            )}
          </div>

          <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/50 rounded-lg p-6 hover:border-purple-600/80 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-aegis-muted text-sm font-semibold uppercase tracking-wider">Status</p>
                <div className="flex items-center gap-2 mt-2">
                  <div className={`w-3 h-3 rounded-full animate-pulse ${systemHealth.status === 'healthy' ? 'bg-green-400' : systemHealth.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'}`}></div>
                  <p className={`text-xl font-bold ${systemHealth.status === 'healthy' ? 'text-green-400' : systemHealth.status === 'degraded' ? 'text-yellow-400' : 'text-red-400'}`}>{systemHealth.status === 'healthy' ? 'Healthy' : systemHealth.status === 'degraded' ? 'Degraded' : 'Critical'}</p>
                </div>
              </div>
              <div className="text-3xl text-purple-500 opacity-50">⚡</div>
            </div>
            <div className="text-aegis-muted text-xs mt-4 space-y-1">
              <p>Latency: {systemHealth.latency}ms</p>
            </div>
            <Link href="/system-control" className="text-purple-400 text-xs font-semibold mt-4 inline-block hover:text-purple-300">System Control →</Link>
          </div>
        </div>
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Zones Section */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-blue-300">📍 Monitored Zones ({estateState.zones.length})</h2>
              <Button3D size="sm" variant="primary" onClick={() => setShowCreateForm(!showCreateForm)} className="flex items-center gap-1">
                <Plus size={14} /> Add
              </Button3D>
            </div>
            {estateState.zones.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800">
                {estateState.zones.map((zone) => (
                  <div
                    key={zone.id}
                    onClick={() => setSelectedEntity(normalizeSelectedEntity(zone))}
                    className={`p-3 rounded-lg cursor-pointer transition-all border-l-4 ${
                      selectedEntity?.id === zone.id
                        ? 'bg-blue-900/40 border-l-blue-500 border border-blue-500/50 ring-1 ring-blue-400/20'
                        : 'bg-slate-800/50 border-l-blue-400 border border-slate-700 hover:bg-slate-800 hover:border-blue-500/30'
                    }`}
                  >
                    <p className="font-semibold text-blue-200">{zone.name || `Zone ${zone.id}`}</p>
                    <p className="text-xs text-slate-400 mt-1">Type: {zone.type || 'Unknown'}</p>
                    {zone.position && (
                      <div className="text-xs text-slate-500 mt-2">Pos: [{Math.round(zone.position[0])}, {Math.round(zone.position[1])}, {Math.round(zone.position[2])}]</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center border border-dashed border-slate-700 rounded-lg">
                <p className="text-slate-400 text-sm mb-3">📍 No zones configured yet</p>
                <button 
                  onClick={() => setShowCreateForm(true)} 
                  className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
                >
                  Create your first zone →
                </button>
              </div>
            )}
          </div>

          {/* Sensors Section */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-green-300">📊 Active Sensors ({estateState.sensors.length})</h2>
              <Button3D size="sm" variant="success" onClick={() => setShowCreateForm(!showCreateForm)} className="flex items-center gap-1">
                <Plus size={14} /> Add
              </Button3D>
            </div>
            {estateState.sensors.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800">
                {estateState.sensors.map((sensor) => (
                  <div
                    key={sensor.id}
                    onClick={() => setSelectedEntity(normalizeSelectedEntity(sensor))}
                    className={`p-3 rounded-lg cursor-pointer transition-all border-l-4 ${
                      selectedEntity?.id === sensor.id
                        ? 'bg-green-900/40 border-l-green-500 border border-green-500/50 ring-1 ring-green-400/20'
                        : 'bg-slate-800/50 border-l-green-400 border border-slate-700 hover:bg-slate-800 hover:border-green-500/30'
                    }`}
                  >
                    <p className="font-semibold text-green-200">{sensor.name || `Sensor ${sensor.id}`}</p>
                    <div className="flex gap-3 text-xs text-slate-400 mt-1">
                      <span>Type: {sensor.type || 'Unknown'}</span>
                      {sensor.value && <span>Value: {sensor.value}</span>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center border border-dashed border-slate-700 rounded-lg">
                <p className="text-slate-400 text-sm mb-3">📊 No sensors connected yet</p>
                <button 
                  onClick={() => setShowCreateForm(true)} 
                  className="text-xs text-green-400 hover:text-green-300 font-semibold"
                >
                  Add your first sensor →
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Quick Access Systems */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-bold text-slate-300 mb-4">🔗 Quick Access Systems</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            <Link href="/zones" className="group block bg-gradient-to-br from-blue-900/20 to-blue-800/10 hover:from-blue-900/40 hover:to-blue-800/20 border border-blue-700/30 hover:border-blue-600/50 rounded-lg p-4 transition-all">
              <h3 className="text-sm font-semibold text-blue-300 group-hover:text-blue-200">📍 Zones</h3>
              <p className="text-xs text-slate-400 mt-1">Define security zones</p>
            </Link>
            <Link href="/sensors" className="group block bg-gradient-to-br from-green-900/20 to-green-800/10 hover:from-green-900/40 hover:to-green-800/20 border border-green-700/30 hover:border-green-600/50 rounded-lg p-4 transition-all">
              <h3 className="text-sm font-semibold text-green-300 group-hover:text-green-200">📊 Sensors</h3>
              <p className="text-xs text-slate-400 mt-1">Manage IoT devices</p>
            </Link>
            <Link href="/environmental" className="group block bg-gradient-to-br from-cyan-900/20 to-cyan-800/10 hover:from-cyan-900/40 hover:to-cyan-800/20 border border-cyan-700/30 hover:border-cyan-600/50 rounded-lg p-4 transition-all">
              <h3 className="text-sm font-semibold text-cyan-300 group-hover:text-cyan-200">🌡️ Climate</h3>
              <p className="text-xs text-slate-400 mt-1">Temperature & humidity</p>
            </Link>
            <Link href="/water-dashboard" className="group block bg-gradient-to-br from-sky-900/20 to-sky-800/10 hover:from-sky-900/40 hover:to-sky-800/20 border border-sky-700/30 hover:border-sky-600/50 rounded-lg p-4 transition-all">
              <h3 className="text-sm font-semibold text-sky-300 group-hover:text-sky-200">💧 Water</h3>
              <p className="text-xs text-slate-400 mt-1">Water management</p>
            </Link>
            <Link href="/waste-dashboard" className="group block bg-gradient-to-br from-amber-900/20 to-amber-800/10 hover:from-amber-900/40 hover:to-amber-800/20 border border-amber-700/30 hover:border-amber-600/50 rounded-lg p-4 transition-all">
              <h3 className="text-sm font-semibold text-amber-300 group-hover:text-amber-200">♻️ Waste</h3>
              <p className="text-xs text-slate-400 mt-1">Waste management</p>
            </Link>
          </div>
        </div>
        {/* Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <Card3D variant="primary" glowing className="p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-400">Active Robots</p>
            <p className="text-3xl font-bold text-white mt-3">{estateState.robots.filter((r) => r.status === 'active').length}</p>
            <p className="text-xs text-slate-400 mt-3">Fleet ready for mission</p>
          </Card3D>
          <Card3D variant="success" glowing className="p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-green-400">Sensors Online</p>
            <p className="text-3xl font-bold text-white mt-3">{estateState.sensors.length}</p>
            <p className="text-xs text-slate-400 mt-3">Environmental nodes</p>
          </Card3D>
          <Card3D variant="warning" glowing className="p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-yellow-400">System Health</p>
            <p className="text-3xl font-bold text-white mt-3">{estateState.metrics.systemHealth || 96}%</p>
            <p className="text-xs text-slate-400 mt-3">Nominal performance</p>
          </Card3D>
          <Card3D variant="secondary" glowing className="p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-purple-400">Zones Monitored</p>
            <p className="text-3xl font-bold text-white mt-3">{estateState.zones.length}</p>
            <p className="text-xs text-slate-400 mt-3">Security coverage</p>
          </Card3D>
        </div>

        {/* 3D View Controls */}
        <div className="space-y-3">
          <div className="flex gap-2 flex-wrap items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-900/50">
            <div className="flex gap-2">
              <Button3D size="sm" variant={viewMode === 'realworld' ? 'primary' : 'ghost'} onClick={() => setViewMode('realworld')}>
                Real World
              </Button3D>
              <Button3D size="sm" variant={viewMode === 'schematic' ? 'primary' : 'ghost'} onClick={() => setViewMode('schematic')}>
                Schematic
              </Button3D>
              <Button3D size="sm" variant={viewMode === 'heat' ? 'primary' : 'ghost'} onClick={() => setViewMode('heat')}>
                Heat Map
              </Button3D>
              <Button3D size="sm" variant="ghost" onClick={() => setAutoRotate(!autoRotate)} className="flex items-center gap-2">
                {autoRotate ? <Eye size={16} /> : <EyeOff size={16} />}
              </Button3D>
            </div>
            <div className="flex gap-3 items-center flex-wrap">
              <button onClick={() => fetchInitialData()} className="px-3 py-1 text-xs bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 rounded text-blue-300 transition-all disabled:opacity-50" disabled={isRefreshing}>
                {isRefreshing ? '⟳ Syncing...' : '⟳ Refresh'}
              </button>
              <label className="text-xs text-slate-300 hover:text-slate-200 cursor-pointer transition-colors flex items-center gap-2">
                <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} className="w-3 h-3 accent-blue-500" />
                Auto
              </label>
              <select value={refreshInterval} onChange={(e) => setRefreshInterval(Number(e.target.value))} className="text-xs px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-200">
                <option value={2000}>2s</option>
                <option value={5000}>5s</option>
                <option value={10000}>10s</option>
              </select>
              {lastRefresh && <span className="text-xs text-slate-400">Last: {lastRefresh.toLocaleTimeString()}</span>}
            </div>
          </div>
          
          <div className="flex gap-2 flex-wrap">
            <span className="text-xs text-slate-400 flex items-center">Filter:</span>
            {['all', 'healthy', 'warning', 'critical'].map(status => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 text-xs rounded transition-colors capitalize ${
                  statusFilter === status
                    ? 'bg-cyan-600/30 border border-cyan-500/50 text-cyan-300'
                    : 'bg-slate-800/50 border border-slate-700 text-slate-300 hover:text-slate-200'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {/* Main Grid: 3D View + CRUD */}
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-black/40 p-4 shadow-2xl shadow-cyan-500/5 relative" style={{ minHeight: '480px' }}>
            {isRefreshing && <div className="absolute top-4 right-4 z-10 text-xs text-blue-300 flex items-center gap-2"><div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />Syncing...</div>}
            <EstateScene robots={estateState.robots} sensors={estateState.sensors} zones={estateState.zones} viewMode={viewMode} onEntitySelect={(entity) => setSelectedEntity(normalizeSelectedEntity(entity))} lightIntensity={lightIntensity} autoRotate={autoRotate} />
          </div>

          {/* CRUD Panel */}
          <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/50 p-6 max-h-[600px] overflow-y-auto">
            <h3 className="text-sm font-bold text-cyan-300">Entity Management</h3>
            <Button3D variant="primary" size="sm" className="w-full flex items-center justify-center gap-2" onClick={() => setShowCreateForm(!showCreateForm)}>
              <Plus size={16} />
              Add Entity
            </Button3D>

            {showCreateForm && (
              <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 space-y-2">
                <select 
                  value={entityType} 
                  onChange={(e) => setEntityType(e.target.value)} 
                  className="w-full text-xs px-3 py-2 bg-slate-900 border border-slate-600 rounded text-slate-200 focus:border-cyan-500 focus:outline-none"
                >
                  <option value="sensor">📊 Sensor</option>
                  <option value="robot">🤖 Robot</option>
                  <option value="zone">📍 Zone</option>
                </select>
                
                <input 
                  type="text" 
                  placeholder="Name (required)" 
                  value={createData.name} 
                  onChange={(e) => setCreateData({ ...createData, name: e.target.value.slice(0, 100) })} 
                  className={`w-full text-xs px-3 py-2 bg-slate-900 border rounded text-slate-200 placeholder-slate-500 focus:outline-none transition-colors ${
                    !createData.name && showCreateForm ? 'border-red-600 focus:border-red-500' : 'border-slate-600 focus:border-cyan-500'
                  }`}
                  maxLength={100}
                />
                <p className="text-[10px] text-slate-400">{createData.name.length}/100 characters</p>
                
                <input 
                  type="text" 
                  placeholder="Type (required)" 
                  value={createData.type} 
                  onChange={(e) => setCreateData({ ...createData, type: e.target.value.slice(0, 50) })} 
                  className={`w-full text-xs px-3 py-2 bg-slate-900 border rounded text-slate-200 placeholder-slate-500 focus:outline-none transition-colors ${
                    !createData.type && showCreateForm ? 'border-red-600 focus:border-red-500' : 'border-slate-600 focus:border-cyan-500'
                  }`}
                  maxLength={50}
                />
                <p className="text-[10px] text-slate-400">{createData.type.length}/50 characters</p>
                
                <input 
                  type="text" 
                  placeholder="Location (optional)" 
                  value={createData.location} 
                  onChange={(e) => setCreateData({ ...createData, location: e.target.value.slice(0, 100) })} 
                  className="w-full text-xs px-3 py-2 bg-slate-900 border border-slate-600 rounded text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                  maxLength={100}
                />
                
                <div className="flex gap-2 pt-2">
                  <button 
                    onClick={() => handleEntityCreate(entityType, createData)} 
                    disabled={isRefreshing || !createData.name.trim() || !createData.type.trim()} 
                    className="flex-1 text-xs px-3 py-2 rounded bg-green-600 hover:bg-green-700 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-1"
                  >
                    <Check size={14} />
                    {isRefreshing ? 'Creating...' : 'Save'}
                  </button>
                  <button 
                    onClick={() => { 
                      setShowCreateForm(false); 
                      setError(null);
                      setCreateData({ name: '', type: '', location: '' });
                    }} 
                    className="flex-1 text-xs px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-white font-semibold transition-colors flex items-center justify-center gap-1"
                  >
                    <X size={14} />
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {estateState.sensors.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-300">Sensors ({estateState.sensors.length})</p>
                {estateState.sensors.map((sensor) => (
                  <div
                    key={sensor.id}
                    onClick={() => setSelectedEntity(normalizeSelectedEntity(sensor))}
                    className={`p-2 rounded text-xs cursor-pointer transition-colors ${selectedEntity?.id === sensor.id ? 'bg-cyan-900/40 border border-cyan-500' : 'bg-slate-800/50 border border-slate-700 hover:bg-slate-800'}`}
                  >
                    <p className="font-semibold text-cyan-200">{sensor.name || `Sensor ${sensor.id}`}</p>
                    <p className="text-slate-400">{sensor.type || 'Unknown'}</p>
                  </div>
                ))}
              </div>
            )}

            {estateState.robots.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-300">Robots ({estateState.robots.length})</p>
                {estateState.robots.map((robot) => (
                  <div
                    key={robot.id}
                    onClick={() => setSelectedEntity(normalizeSelectedEntity(robot))}
                    className={`p-2 rounded text-xs cursor-pointer transition-colors ${selectedEntity?.id === robot.id ? 'bg-cyan-900/40 border border-cyan-500' : 'bg-slate-800/50 border border-slate-700 hover:bg-slate-800'}`}
                  >
                    <p className="font-semibold text-green-200">{robot.name || `Robot ${robot.id}`}</p>
                    <p className="text-slate-400">{robot.status || 'Unknown'}</p>
                  </div>
                ))}
              </div>
            )}

            {estateState.zones.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-300">Zones ({estateState.zones.length})</p>
                {estateState.zones.map((zone) => (
                  <div
                    key={zone.id}
                    onClick={() => setSelectedEntity(normalizeSelectedEntity(zone))}
                    className={`p-2 rounded text-xs cursor-pointer transition-colors ${selectedEntity?.id === zone.id ? 'bg-cyan-900/40 border border-cyan-500' : 'bg-slate-800/50 border border-slate-700 hover:bg-slate-800'}`}
                  >
                    <p className="font-semibold text-amber-200">{zone.name || `Zone ${zone.id}`}</p>
                    <p className="text-slate-400">{zone.type || 'Unknown'}</p>
                  </div>
                ))}
              </div>
            )}

            {selectedEntity && (
              <div className="pt-4 border-t border-slate-700 space-y-3">
                <div className="rounded-lg bg-slate-800/50 border border-slate-700 p-4">
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Selected Entity</p>
                  <p className="text-lg font-semibold text-white mt-2">{selectedEntity.name || selectedEntity.id}</p>
                  <p className="text-xs text-slate-400 mt-1">Type: {selectedEntity.type || 'unknown'}</p>
                  {selectedEntity.status && <p className="text-xs text-slate-400">Status: {selectedEntity.status}</p>}
                  {selectedEntity.value !== undefined && <p className="text-xs text-slate-400">Value: {selectedEntity.value}</p>}
                </div>

                {selectedEntity.type === 'robot' && (
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-slate-300">Robot Commands</p>
                    <div className="grid grid-cols-2 gap-2">
                      <Button3D
                        variant="success"
                        size="sm"
                        className="w-full flex items-center justify-center gap-2"
                        onClick={() => dispatchRobotTask('inspect')}
                        disabled={commandLoading}
                      >
                        Dispatch Task
                      </Button3D>
                      <Button3D
                        variant="danger"
                        size="sm"
                        className="w-full flex items-center justify-center gap-2"
                        onClick={dispatchRobotStop}
                        disabled={commandLoading}
                      >
                        Emergency Stop
                      </Button3D>
                    </div>
                  </div>
                )}

                {selectedEntity.type === 'zone' && (
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-slate-300">Zone Automation</p>
                    <Button3D
                      variant="primary"
                      size="sm"
                      className="w-full flex items-center justify-center gap-2"
                      onClick={() => scheduleZoneTask('irrigate')}
                      disabled={commandLoading}
                    >
                      Schedule Irrigation
                    </Button3D>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2">
                  <Button3D 
                    variant="warning" 
                    size="sm" 
                    className="w-full flex items-center justify-center gap-2"
                    onClick={() => {
                      alert(`Edit ${selectedEntity.name || 'entity'} - Coming soon`);
                    }}
                  >
                    <Edit2 size={14} />
                    Edit
                  </Button3D>
                  <Button3D
                    variant="danger"
                    size="sm"
                    className="w-full flex items-center justify-center gap-2"
                    onClick={() => {
                      if (window.confirm(`Delete ${selectedEntity.name || 'this entity'}?`)) {
                        const type = selectedEntity.type || (selectedEntity?.status ? 'robot' : selectedEntity?.zone_id || selectedEntity?.zone ? 'zone' : 'sensor');
                        handleEntityDelete(type, selectedEntity.id);
                      }
                    }}
                    disabled={isRefreshing}
                  >
                    <Trash size={14} />
                    Delete
                  </Button3D>
                </div>

                {statusMessage && (
                  <div className="rounded-lg border border-cyan-500/30 bg-cyan-900/20 p-3 text-xs text-cyan-100">
                    {statusMessage}
                  </div>
                )}
                {commandResult && (
                  <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-xs text-slate-200">
                    <p className="font-semibold text-slate-100">Last command response</p>
                    <pre className="mt-2 text-[10px] whitespace-pre-wrap break-words">{JSON.stringify(commandResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* System Health Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-sm font-bold text-cyan-300 px-2">System Health</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800/50 pr-2">
              {ESTATE_SYSTEMS.map((system) => (
                <button key={system.id} onClick={() => setSelectedSystem(system.id)} className={`transition-all ${selectedSystem === system.id ? 'ring-2 ring-cyan-500' : ''}`}>
                  <SystemStatusCard system={system} data={systemDataCache[system.id] || { status: 'loading' }} />
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <AlertPanel alerts={alerts} />
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <div />
          <PredictiveMaintenancePanel />
        </div>

        {selectedSystem && (
          <Card3D variant="primary" className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-cyan-300">{ESTATE_SYSTEMS.find((s) => s.id === selectedSystem)?.name} Details</h3>
              <button onClick={() => setSelectedSystem(null)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(systemDataCache[selectedSystem] || {}).map(([key, value]) => (
                <div key={key} className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
                  <p className="text-xs uppercase text-slate-400">{key}</p>
                  <p className="text-sm font-bold text-cyan-200 mt-1">{typeof value === 'number' ? value.toFixed(2) : String(value)}</p>
                </div>
              ))}
            </div>
          </Card3D>
        )}

        {/* Quick Links */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="text-sm font-bold text-slate-300 mb-4">Quick Navigation</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Link href="/zones" className="p-3 rounded-lg border border-slate-700 bg-slate-800/50 hover:bg-slate-800 text-sm text-slate-300 hover:text-white transition-colors">
              Zones
            </Link>
            <Link href="/sensors-management" className="p-3 rounded-lg border border-slate-700 bg-slate-800/50 hover:bg-slate-800 text-sm text-slate-300 hover:text-white transition-colors">
              Sensors
            </Link>
            <Link href="/robots-management" className="p-3 rounded-lg border border-slate-700 bg-slate-800/50 hover:bg-slate-800 text-sm text-slate-300 hover:text-white transition-colors">
              Robots
            </Link>
            <Link href="/system-analytics" className="p-3 rounded-lg border border-slate-700 bg-slate-800/50 hover:bg-slate-800 text-sm text-slate-300 hover:text-white transition-colors">
              Analytics
            </Link>
          </div>
        </div>
      </div>
    </Layout3D>
  );
}
