import React, { useState, useEffect, useCallback, useRef } from 'react';
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

  const rawType = typeof entity.type === 'string' ? entity.type.toLowerCase() : '';
  const sensorTypeSet = new Set(['sensor', 'temperature', 'humidity', 'pressure', 'light', 'motion', 'air_quality', 'soil_moisture', 'flow', 'vibration', 'proximity']);
  const zoneTypeSet = new Set(['zone', 'greenhouse', 'warehouse', 'facility', 'building', 'lab', 'room']);

  let inferredType = entity.type || entity.kind || entity.device_type || 'sensor';
  if (sensorTypeSet.has(rawType)) inferredType = 'sensor';
  else if (zoneTypeSet.has(rawType)) inferredType = 'zone';
  else if (entity.robot_id || entity.robot_name || rawType === 'robot') inferredType = 'robot';
  else if (entity.zone_id || entity.zone || rawType === 'zone') inferredType = 'zone';
  else if (entity.sensor_id || rawType === 'sensor') inferredType = 'sensor';

  const type = inferredType === 'device' && entity.kind === 'sensor' ? 'sensor' : inferredType;

  return {
    ...entity,
    id: entity.id ?? entity.robot_id ?? entity.sensor_id ?? entity.device_id,
    robot_id: entity.robot_id ?? entity.id,
    sensor_id: entity.sensor_id ?? entity.id,
    device_id: entity.device_id ?? entity.id,
    type,
  };
};

const getEntityDataEntries = (entity) => {
  if (!entity) return [];
  const values = {
    name: entity.name,
    id: entity.id,
    type: entity.type,
    status: entity.status,
    location: entity.location || entity.zone || entity.zone_id,
    zone: entity.zone_id ?? entity.zone ?? null,
    sensor_type: entity.sensor_type || entity.type,
    value: entity.value,
    battery: entity.battery_percent ?? entity.battery,
    cpu_temp_celsius: entity.cpu_temp_celsius,
    motor_health_percent: entity.motor_health_percent,
    device_type: entity.device_type || entity.kind,
    last_updated: entity.last_updated || entity.updated_at,
    position: entity.position,
  };

  return Object.entries(values).filter(([, value]) => value !== undefined && value !== null && value !== '' && !(Array.isArray(value) && value.length === 0));
};

function TrendSparkline({ values, color }) {
  const width = 120;
  const height = 36;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const step = values.length > 1 ? (width - 8) / (values.length - 1) : 1;

  const linePoints = values
    .map((value, index) => {
      const x = 4 + index * step;
      const y = height - 6 - ((value - min) / Math.max(max - min, 1)) * (height - 12);
      return `${x},${y}`;
    })
    .join(' ');

  const areaPoints = `${linePoints} ${width - 4},${height - 4} 4,${height - 4}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-10 w-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id={`trend-gradient-${color.replace('#', '')}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.5" />
          <stop offset="100%" stopColor={color} stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#trend-gradient-${color.replace('#', '')})`} opacity="0.9" />
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={linePoints}
        style={{ filter: `drop-shadow(0 0 8px ${color})` }}
      >
        <animate attributeName="stroke-dasharray" values="0 200;120 80;0 200" dur="3s" repeatCount="indefinite" />
      </polyline>
    </svg>
  );
}

function LiveTelemetryPanel({ readings }) {
  const grouped = readings.reduce((result, reading) => {
    const key = reading.sensor_id ?? reading.id ?? reading.sensor_name ?? 'unknown';
    if (!result[key]) result[key] = [];
    const value = Number(reading.value);
    if (Number.isFinite(value)) result[key].push({ ...reading, value });
    return result;
  }, {});

  const sensors = Object.values(grouped).slice(0, 4);

  return (
    <Card3D variant="primary" className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-cyan-300">Live Telemetry</h3>
          <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Recent sensor readings</p>
        </div>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[10px] font-mono text-emerald-300">
          {readings.length ? 'STREAMING' : 'WAITING'}
        </span>
      </div>
      {sensors.length ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {sensors.map((sensorReadings) => {
            const latest = sensorReadings[0];
            const values = sensorReadings.slice().reverse().map((reading) => reading.value);
            const status = latest.reading_status || 'normal';
            const color = status === 'critical' ? '#f87171' : status === 'warning' ? '#fbbf24' : '#34d399';
            return (
              <div key={latest.sensor_id || latest.sensor_name} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate text-xs font-semibold text-slate-200">{latest.sensor_name || `Sensor ${latest.sensor_id}`}</p>
                    <p className="text-[10px] text-slate-500">{latest.type || 'sensor'}</p>
                  </div>
                  <span className="text-xs font-mono" style={{ color }}>{latest.value} {latest.unit || ''}</span>
                </div>
                <TrendSparkline values={values} color={color} />
                <p className="text-[10px] uppercase tracking-wider" style={{ color }}>{status}</p>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="py-6 text-center text-xs text-slate-500">Waiting for sensor telemetry...</p>
      )}
    </Card3D>
  );
}

function LiveActivityPanel({ events, historyEvents, mode, onModeChange }) {
  const displayedEvents = mode === 'history' ? historyEvents : events.slice(0, 30);
  return (
    <Card3D variant="secondary" className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-cyan-300">Live Activity</h3>
          <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Realtime event feed</p>
        </div>
        <div className="flex gap-1 rounded border border-slate-800 p-1 text-[10px]">
          <button className={`rounded px-2 py-1 ${mode === 'live' ? 'bg-cyan-900/60 text-cyan-200' : 'text-slate-500'}`} onClick={() => onModeChange('live')}>Latest 30</button>
          <button className={`rounded px-2 py-1 ${mode === 'history' ? 'bg-cyan-900/60 text-cyan-200' : 'text-slate-500'}`} onClick={() => onModeChange('history')}>Audit history</button>
        </div>
      </div>
      <p className="mb-2 text-[10px] text-slate-500">{mode === 'history' ? 'Persisted tenant audit records' : 'In-memory realtime buffer; older live events are not deleted from audit storage'}</p>
      {displayedEvents.length ? (
        <div className="max-h-48 space-y-2 overflow-y-auto pr-1">
          {displayedEvents.slice(0, 30).map((event) => {
            const severity = ['critical', 'warning'].includes(event.type);
            return (
              <div key={event.id} className="flex items-start gap-2 rounded border border-slate-800 bg-slate-950/60 p-2">
                <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${severity ? (event.type === 'critical' ? 'bg-red-400' : 'bg-amber-400') : 'bg-cyan-400'}`} />
                <div className="min-w-0">
                  <p className="truncate text-xs text-slate-200">{event.message}</p>
                  <p className="text-[10px] uppercase tracking-wider text-slate-500">{event.type} · {new Date(event.timestamp).toLocaleTimeString()}</p>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="py-6 text-center text-xs text-slate-500">{mode === 'history' ? 'No persisted audit records found.' : 'Waiting for realtime events...'}</p>
      )}
    </Card3D>
  );
}

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
  const activeAlerts = alerts.filter((a) => a.status === 'active');
  const criticalCount = activeAlerts.filter((a) => a.type === 'critical').length;
  const warningCount = activeAlerts.filter((a) => a.type === 'warning').length;

  return (
    <Card3D variant="default" glowing glowColor="#ff6b35" className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <Bell size={16} className="text-red-400" />
        <h3 className="text-sm font-bold text-red-300">System Alerts</h3>
        <span className="text-xs bg-red-900/30 text-red-200 px-2 py-1 rounded">{criticalCount + warningCount} Active</span>
      </div>
      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
        {activeAlerts.map((alert) => {
          const trendValues = alert.trend || [22, 26, 28, 27, 35, 40, 38, 52, 60, 58, 66, 72];
          const accentColor = alert.type === 'critical' ? '#ef4444' : alert.type === 'warning' ? '#f59e0b' : '#38bdf8';
          return (
            <div
              key={alert.id}
              className="p-2 rounded bg-slate-900/50 border-l-2 transition-all duration-300 animate-pulse"
              style={{ borderColor: accentColor, boxShadow: `0 0 18px ${accentColor}33` }}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-semibold text-slate-200">{alert.message}</p>
                <span className="text-[9px] uppercase tracking-wide rounded-full px-1.5 py-0.5" style={{ backgroundColor: `${accentColor}22`, color: accentColor }}>
                  {alert.type}
                </span>
              </div>
              <div className="mt-2">
                <TrendSparkline values={trendValues} color={accentColor} />
              </div>
              <p className="text-[10px] text-slate-400 mt-1">{alert.system} • {alert.timestamp.toLocaleTimeString()}</p>
            </div>
          );
        })}
      </div>
    </Card3D>
  );
}

function PredictiveMaintenancePanel({ recommendations = [], optimization = [], adaptation = [] }) {
  const predictions = Array.isArray(recommendations) && recommendations.length > 0
    ? recommendations.map((item) => ({
        system: item.focus || 'System',
        daysUntil: item.days_until_action ?? item.daysUntil ?? 7,
        confidence: item.confidence ?? 80,
        action: item.message || 'Monitor and inspect',
        severity: item.severity || 'monitor',
        domain: item.type || 'maintenance',
      }))
    : [
        { system: 'System', daysUntil: 14, confidence: 88, action: 'Routine monitoring remains within target range', severity: 'normal', domain: 'maintenance' },
      ];

  const optimizationCards = Array.isArray(optimization) && optimization.length > 0
    ? optimization.map((item) => ({
        system: item.focus || 'Estate',
        confidence: item.confidence ?? 80,
        action: item.message || 'Optimize scheduling and load balancing',
        severity: item.severity || 'medium',
        domain: item.domain || 'system',
      }))
    : [];

  const adaptationCards = Array.isArray(adaptation) && adaptation.length > 0
    ? adaptation.map((item) => ({
        system: item.focus || 'Environment',
        confidence: item.confidence ?? 80,
        action: item.message || 'Adjust climate and resource response',
        severity: item.severity || 'medium',
        domain: item.domain || 'weather',
      }))
    : [];

  const combinedCards = [...predictions, ...optimizationCards, ...adaptationCards].slice(0, 6);

  return (
    <Card3D variant="success" glowing className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp size={16} className="text-green-400" />
        <h3 className="text-sm font-bold text-green-300">Predictive Maintenance & Optimization</h3>
      </div>
      <div className="space-y-2">
        {combinedCards.map((pred, idx) => (
          <div key={`${pred.domain}-${pred.system}-${idx}`} className="p-2 rounded bg-slate-900/50 border-l-2 border-green-600">
            <div className="flex justify-between items-start gap-2">
              <p className="text-xs font-semibold text-slate-200">{pred.system}</p>
              <span className="text-[10px] bg-green-900/30 text-green-200 px-1.5 py-0.5 rounded">{pred.domain === 'maintenance' ? `${pred.daysUntil || 7} days` : pred.domain}</span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">{pred.action}</p>
            <div className="mt-2 flex items-center justify-between text-[9px] uppercase tracking-wide text-slate-400">
              <span>{pred.severity}</span>
              <span>{pred.confidence}% confidence</span>
            </div>
            <div className="mt-2 h-1 bg-slate-700 rounded overflow-hidden">
              <div className="h-full bg-green-500" style={{ width: `${Math.min(100, Math.max(10, pred.confidence))}%` }} />
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
  const [autoRefresh, setAutoRefresh] = useState(false);
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
  const [twinHealth, setTwinHealth] = useState(null);
  const [activityMode, setActivityMode] = useState('live');
  const [auditEvents, setAuditEvents] = useState([]);
  const { socketConnected, realtimeError, liveSystemStatus, liveSensorReadings, liveAlerts, liveEvents } = useEstateRealtime(estateState);
  const fetchLockRef = useRef(false);
  const timerRef = useRef(null);
  const estateStateRef = useRef(estateState);

  const metricCards = React.useMemo(() => [
    {
      key: 'zones',
      label: 'Zones',
      value: metrics.zones,
      tone: 'blue',
      detail: 'Active security zones',
      href: '/zones',
      icon: '📍',
    },
    {
      key: 'sensors',
      label: 'Sensors',
      value: metrics.sensors,
      tone: 'green',
      detail: 'IoT devices online',
      href: '/sensors',
      icon: '📊',
    },
    {
      key: 'auditLogs',
      label: 'Audit Logs',
      value: metrics.auditLogs,
      tone: 'yellow',
      detail: 'Compliance events recorded',
      href: '/audit-logs',
      icon: '📋',
    },
    {
      key: 'users',
      label: 'Users',
      value: metrics.users,
      tone: 'red',
      detail: 'Active tenant users',
      href: user?.role === 'admin' ? '/admin/users' : undefined,
      icon: '👥',
    },
    {
      key: 'status',
      label: 'Status',
      value: systemHealth.status === 'healthy' ? 'Healthy' : systemHealth.status === 'degraded' ? 'Degraded' : 'Critical',
      tone: systemHealth.status === 'healthy' ? 'green' : systemHealth.status === 'degraded' ? 'yellow' : 'red',
      detail: `Latency: ${systemHealth.latency}ms`,
      href: '/system-control',
      icon: '⚡',
    },
  ], [metrics, systemHealth, user?.role]);

  useEffect(() => {
    estateStateRef.current = estateState;
  }, [estateState]);

  const fetchInitialData = useCallback(async () => {
    if (fetchLockRef.current) return;
    fetchLockRef.current = true;

    const currentEstateState = estateStateRef.current;

    try {
      setIsRefreshing(true);
      setError(null);
      currentEstateState.setLoading(true);
      const token = getAuthToken();
      const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

      const [estateStatusRes, robotsRes, sensorsRes, zonesRes, twinDevicesRes, twinHealthRes, auditRes, usersRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/estate/status`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/robotics/active`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/sensors`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/zones`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/digital-twin/health`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/audit`, { headers: authHeaders }).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/v1/auth/users`, { headers: authHeaders }).catch(() => ({ ok: false })),
      ]);

      const estateStatus = estateStatusRes?.ok ? await estateStatusRes.json().catch(() => null) : null;
      const robots = robotsRes?.ok ? await robotsRes.json().catch(() => []) : [];
      const sensors = sensorsRes?.ok ? await sensorsRes.json().catch(() => []) : [];
      const zones = zonesRes?.ok ? await zonesRes.json().catch(() => []) : [];
      const twinDevices = twinDevicesRes?.ok ? await twinDevicesRes.json().catch(() => []) : [];
      const twinHealthData = twinHealthRes?.ok ? await twinHealthRes.json().catch(() => null) : null;
      const auditLogs = auditRes?.ok ? await auditRes.json().catch(() => []) : [];
      setAuditEvents((Array.isArray(auditLogs) ? auditLogs : []).map((log) => ({
        id: `audit-${log.id}`,
        type: log.event_type || 'audit',
        message: log.event_type || 'Audit event recorded',
        timestamp: log.created_at,
      })));
      const users = usersRes?.ok ? await usersRes.json().catch(() => []) : [];
      const userCount = Array.isArray(users) && users.length > 0 ? users.length : 1;
      setTwinHealth(twinHealthData);

      const twinPosition = (position) => {
        if (Array.isArray(position)) return position;
        return [Number(position?.x) || 0, Number(position?.y) || 1, Number(position?.z) || 0];
      };
      const twinRobots = Array.isArray(twinDevices)
        ? twinDevices.filter((device) => device.kind === 'robot').map((device) => ({
          ...device,
          id: device.id ?? device.device_id,
          robot_id: device.device_id,
          type: 'robot',
          position: twinPosition(device.position),
          state: device.state || {},
        }))
        : [];
      const twinSensors = Array.isArray(twinDevices)
        ? twinDevices.filter((device) => device.kind === 'sensor').map((device) => ({
          ...device,
          id: device.id ?? device.device_id,
          sensor_id: device.device_id,
          type: 'sensor',
          sensor_type: device.device_type,
          value: device.state?.value,
          position: twinPosition(device.position),
        }))
        : [];

      const fallbackRobots = [
        { id: 'fallback-robot-1', robot_id: 'fallback-robot-1', type: 'robot', status: 'active', position: [-8, 1, 4] },
        { id: 'fallback-robot-2', robot_id: 'fallback-robot-2', type: 'robot', status: 'charging', position: [8, 1, 4] },
      ];
      const fallbackSensors = [
        { id: 'fallback-sensor-1', sensor_id: 'fallback-sensor-1', type: 'sensor', sensor_type: 'temperature', value: 24.5, status: 'active', position: [-6, 1, -4] },
        { id: 'fallback-sensor-2', sensor_id: 'fallback-sensor-2', type: 'sensor', sensor_type: 'humidity', value: 57, status: 'active', position: [6, 1, -4] },
      ];
      const fallbackZones = [
        { id: 'fallback-zone-1', type: 'zone', name: 'Operations Zone', status: 'secure', position: [-10, 0, -8], size: [10, 2, 10], color: '#10b981' },
        { id: 'fallback-zone-2', type: 'zone', name: 'Service Lane', status: 'warning', position: [12, 0, -8], size: [10, 2, 10], color: '#f59e0b' },
      ];

      const safeRobots = twinRobots.length > 0 ? twinRobots : (Array.isArray(robots) && robots.length > 0 ? robots : fallbackRobots);
      const safeSensors = twinSensors.length > 0 ? twinSensors : (Array.isArray(sensors) && sensors.length > 0 ? sensors : fallbackSensors);
      const safeZones = Array.isArray(zones) && zones.length > 0 ? zones : fallbackZones;

      const robotsWithPositions = safeRobots.map((robot, idx) => ({
        ...robot,
        id: robot.id ?? robot.robot_id ?? `robot_${idx}`,
        robot_id: robot.robot_id ?? robot.id ?? `robot_${idx}`,
        type: 'robot',
        position: robot.position || [-(6 - (idx % 4)) + (idx % 4) * 4, 1, 6 - Math.floor(idx / 4) * 4],
        status: robot.status || (idx % 2 === 0 ? 'active' : 'charging'),
      }));

      const sensorsWithPositions = safeSensors.map((sensor, idx) => ({
        ...sensor,
        id: sensor.id ?? sensor.sensor_id ?? `sensor_${idx}`,
        sensor_id: sensor.sensor_id ?? sensor.id ?? `sensor_${idx}`,
        type: 'sensor',
        position: sensor.position || [-(7 - (idx % 5)) + (idx % 5) * 3, 2, 7 - Math.floor(idx / 5) * 3],
        sensor_type: sensor.type || sensor.sensor_type || ['temperature', 'humidity', 'light', 'pressure', 'motion'][idx % 5],
        value: sensor.value ?? `${Math.floor(20 + idx * 2)}${idx % 2 === 0 ? '°C' : '%'}`,
        status: sensor.status || 'active',
      }));

      const zonesWithPositions = safeZones.map((zone, idx) => ({
        ...zone,
        id: zone.id ?? `zone_${idx}`,
        type: 'zone',
        position: zone.position || [-(6 - (idx % 2)) + (idx % 2) * 12, 0, 6 - Math.floor(idx / 2) * 10],
        size: zone.size || [3 + (idx % 2), 3 + (idx % 3), 3 + ((idx + 1) % 2)],
        color: zone.color || ['#0088ff', '#00ffaa', '#88ff00', '#ff8800', '#ffaa00'][idx % 5],
      }));

      currentEstateState.setRobots(robotsWithPositions);
      currentEstateState.setSensors(sensorsWithPositions);
      currentEstateState.setZones(zonesWithPositions);

      setMetrics({
        zones: safeZones.length,
        sensors: safeSensors.length,
        users: userCount,
        auditLogs: Array.isArray(auditLogs) ? auditLogs.length : 0,
      });

      currentEstateState.updateMetrics({
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
          climate: { ...prev.climate, status: estateStatus.climate?.status || prev.climate?.status, health_score: estateStatus.climate?.health_score || prev.climate?.health_score, last_update: estateStatus.climate?.last_update || prev.climate?.last_update },
          energy: { ...prev.energy, status: estateStatus.energy?.status || prev.energy?.status, health_score: estateStatus.energy?.health_score || prev.energy?.health_score, last_update: estateStatus.energy?.last_update || prev.energy?.last_update },
          security: { ...prev.security, status: estateStatus.security?.status || prev.security?.status, health_score: estateStatus.security?.health_score || prev.security?.health_score, last_update: estateStatus.security?.last_update || prev.security?.last_update },
          water: { ...prev.water, status: estateStatus.water?.status || prev.water?.status, health_score: estateStatus.water?.health_score || prev.water?.health_score, last_update: estateStatus.water?.last_update || prev.water?.last_update },
          communications: { ...prev.communications, status: estateStatus.communications?.status || prev.communications?.status, health_score: estateStatus.communications?.health_score || prev.communications?.health_score, last_update: estateStatus.communications?.last_update || prev.communications?.last_update },
        }));
      }

      const systemStateSnapshot = ESTATE_SYSTEMS.reduce((accumulator, system) => {
        accumulator[system.id] = getMockSystemData(system.id);
        return accumulator;
      }, {});
      setSystemDataCache((previous) => ({ ...previous, ...systemStateSnapshot }));
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Dashboard data fetch failed:', error);
      setError(error.message || 'Unable to load estate data.');
      currentEstateState.setError(error.message || 'Unable to load estate data.');
    } finally {
      currentEstateState.setLoading(false);
      setIsRefreshing(false);
      fetchLockRef.current = false;
    }
  }, []);

  useEffect(() => {
    if (!loading && user) {
      fetchInitialData();
    }
  }, [user, loading, fetchInitialData]);

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
          ...(system.status ? { status: system.status } : {}),
          ...(system.health_score !== undefined ? { health_score: system.health_score } : {}),
          ...(system.last_update ? { last_update: system.last_update } : {}),
          data: updated[id]?.data || {},
        };
      });
      return updated;
    });
  }, [liveSystemStatus]);

  useEffect(() => {
    if (!user || !autoRefresh) return undefined;

    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = window.setInterval(() => {
      fetchInitialData();
    }, refreshInterval);

    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [user, autoRefresh, refreshInterval, fetchInitialData]);

  useEffect(() => {
    if (!liveSensorReadings.length) return;

    const sensorSummary = liveSensorReadings.reduce((acc, reading) => {
      const sensorKey = reading.sensor_id ?? reading.id ?? 'unknown';
      acc[sensorKey] = reading.value ?? acc[sensorKey];
      return acc;
    }, {});

    estateState.setSensors((prevSensors) => prevSensors.map((sensor) => {
      const key = sensor.sensor_id ?? sensor.id;
      const nextValue = sensorSummary[key];
      return nextValue === undefined ? sensor : { ...sensor, value: nextValue };
    }));
  }, [liveSensorReadings, estateState]);

  useEffect(() => {
    if (!liveAlerts.length) return;

    const normalizedAlerts = liveAlerts.map((alert) => ({
      id: `twin-${alert.device_id}-${alert.timestamp}`,
      type: alert.severity || 'warning',
      system: 'biosphere',
      message: alert.message || `Sensor ${alert.device_id} requires attention`,
      timestamp: new Date(alert.timestamp || Date.now()),
      status: 'active',
    }));
    setAlerts((previous) => {
      const merged = [...normalizedAlerts, ...previous];
      return merged.filter((alert, index, all) => all.findIndex((candidate) => candidate.id === alert.id) === index).slice(0, 12);
    });
  }, [liveAlerts]);

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
  }, [fetchInitialData]);

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
  }, [fetchInitialData]);

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

  const controlTwinDevice = useCallback(async (command) => {
    if (!selectedEntity?.device_id) return;
    const token = getAuthToken();
    setCommandLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/v1/digital-twin/devices/${selectedEntity.id}/control`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok) throw new Error(result?.detail || 'Device command failed');
      setCommandResult(result);
      setStatusMessage(`${selectedEntity.name || 'Device'} command accepted: ${command}`);
      await fetchInitialData();
    } catch (err) {
      setError(err.message || 'Failed to control device');
    } finally {
      setCommandLoading(false);
    }
  }, [fetchInitialData, selectedEntity]);

  const createPanelTilt = useCallback((event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    const rotateY = (x - 0.5) * 12;
    const rotateX = (0.5 - y) * 12;

    event.currentTarget.style.transform = `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    event.currentTarget.style.transition = 'transform 0.18s ease-out';
    event.currentTarget.style.boxShadow = '0 20px 45px rgba(59, 130, 246, 0.18)';
  }, []);

  const resetPanelTilt = useCallback((event) => {
    event.currentTarget.style.transform = 'translate3d(0,0,0)';
    event.currentTarget.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
    event.currentTarget.style.boxShadow = '';
  }, []);

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
        <div
          className="rounded-3xl border border-white/10 bg-slate-900/40 backdrop-blur-xl shadow-[0_0_25px_rgba(34,211,238,0.08)] p-5 relative overflow-hidden"
          style={{ transform: 'translate3d(0,0,0)', perspective: '1200px' }}
        >
          <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_42%)]" />
          <div className="relative flex items-center justify-between flex-wrap gap-4">
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
        </div>

        {error && <div className="mb-6 p-4 bg-red-900/20 border border-red-700/50 rounded-lg text-red-300 text-sm flex items-center justify-between"><span>⚠️ {error}</span><button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">✕</button></div>}
        
        {lastRefresh && <div className="mb-4 text-xs text-slate-400 text-right">Last updated: {lastRefresh.toLocaleTimeString()}</div>}

        {/* Quick Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-white/10 bg-slate-900/35 backdrop-blur-xl shadow-[0_0_25px_rgba(168,85,247,0.12)] p-6 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase text-purple-400 font-semibold">System Status</p>
              <p className="text-2xl font-bold text-purple-300 mt-2">Operational</p>
            </div>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          </div>
        </div>

        {/* Key Metrics Cards - from Dashboard */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {metricCards.map((card) => {
            const toneClasses = {
              blue: 'border-blue-500/40 bg-gradient-to-br from-slate-900/80 via-blue-900/20 to-slate-900/90',
              green: 'border-green-500/40 bg-gradient-to-br from-slate-900/80 via-green-900/20 to-slate-900/90',
              yellow: 'border-yellow-500/40 bg-gradient-to-br from-slate-900/80 via-yellow-900/20 to-slate-900/90',
              red: 'border-red-500/40 bg-gradient-to-br from-slate-900/80 via-red-900/20 to-slate-900/90',
            };

            const textClasses = {
              blue: 'text-blue-400',
              green: 'text-green-400',
              yellow: 'text-yellow-400',
              red: 'text-red-400',
            };

            const cardBody = (
              <div
                key={card.key}
                className={`rounded-2xl border p-6 shadow-[0_0_24px_rgba(96,165,250,0.12)] transition-all duration-300 ease-out hover:border-slate-500/60 ${toneClasses[card.tone]}`}
                style={{ transform: 'translate3d(0,0,0)', perspective: '1200px' }}
                onMouseMove={createPanelTilt}
                onMouseLeave={resetPanelTilt}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-aegis-muted text-sm font-semibold uppercase tracking-wider">{card.label}</p>
                    <p className={`mt-2 text-3xl font-bold ${textClasses[card.tone]}`}>{isRefreshing && card.key !== 'status' ? '—' : card.value}</p>
                  </div>
                  <div className="text-3xl opacity-60">{card.icon}</div>
                </div>
                <p className="text-aegis-muted text-xs mt-4">{card.detail}</p>
                {card.href && (
                  <Link href={card.href} className={`${textClasses[card.tone]} text-xs font-semibold mt-4 inline-block hover:opacity-90`}>
                    {card.key === 'zones' ? 'Manage Zones' : card.key === 'sensors' ? 'View Sensors' : card.key === 'auditLogs' ? 'View Logs' : card.key === 'users' ? 'Manage Users' : 'System Control'} →
                  </Link>
                )}
              </div>
            );

            return card.href ? <Link key={card.key} href={card.href} className="block">{cardBody}</Link> : cardBody;
          })}
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

        {twinHealth && (
          <Card3D variant={twinHealth.status === 'healthy' ? 'success' : 'warning'} className="p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Digital Twin Health</p>
                <p className="mt-1 text-sm text-slate-300">{twinHealth.online}/{twinHealth.devices} devices online</p>
              </div>
              <div className="flex gap-4 text-xs font-mono text-slate-300">
                <span>Score {twinHealth.health_score}%</span>
                <span>Alerts {twinHealth.alerts}</span>
                <span>Actuators {twinHealth.active_actuators}/{twinHealth.actuators}</span>
              </div>
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="rounded border border-slate-800 bg-slate-950/50 p-3">
                <p className="text-[10px] uppercase tracking-[0.25em] text-slate-400">Recommendation summary</p>
                <p className="mt-2 text-sm font-semibold text-green-300">{twinHealth.recommendation_summary?.total ?? 0} active recommendations</p>
                <p className="mt-1 text-[11px] text-slate-300">{(twinHealth.recommendation_summary?.top_actions || []).slice(0, 2).join(' • ') || 'No immediate actions required'}</p>
              </div>
              <div className="rounded border border-slate-800 bg-slate-950/50 p-3">
                <p className="text-[10px] uppercase tracking-[0.25em] text-slate-400">Alert summary</p>
                <p className="mt-2 text-sm font-semibold text-amber-300">{twinHealth.alert_summary?.total ?? 0} active alerts</p>
                <p className="mt-1 text-[11px] text-slate-300">{(twinHealth.alert_summary?.top_alerts || []).slice(0, 2).join(' • ') || 'No active alert conditions detected'}</p>
              </div>
            </div>
            {twinHealth.workflow && (
              <div className="mt-3 rounded border border-cyan-700/50 bg-cyan-950/30 p-3">
                <p className="text-[10px] uppercase tracking-[0.25em] text-cyan-300">Workflow summary</p>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-cyan-100">
                  <span className="rounded border border-cyan-500/40 bg-cyan-900/40 px-2 py-1">{twinHealth.workflow.status}</span>
                  <span>Predictive {twinHealth.workflow.modules?.predictive?.count ?? 0}</span>
                  <span>Optimization {twinHealth.workflow.modules?.optimization?.count ?? 0}</span>
                  <span>Adaptation {twinHealth.workflow.modules?.adaptation?.count ?? 0}</span>
                </div>
                <p className="mt-2 text-[11px] text-slate-200">{twinHealth.workflow.summary}</p>
              </div>
            )}
          </Card3D>
        )}

        <LiveActivityPanel events={liveEvents} historyEvents={auditEvents} mode={activityMode} onModeChange={setActivityMode} />

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

                <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-3">
                  <p className="mb-2 text-[10px] uppercase tracking-[0.22em] text-slate-400">Entity data</p>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                    {getEntityDataEntries(selectedEntity).map(([key, value]) => (
                      <div key={key} className="rounded border border-slate-700 bg-slate-800/40 p-2">
                        <div className="text-[9px] uppercase tracking-[0.18em] text-slate-500">{String(key).replace(/_/g, ' ')}</div>
                        <div className="mt-1 truncate font-mono text-cyan-200">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-bold text-slate-300">Quick actions</p>
                  {selectedEntity.type === 'sensor' && (
                    <Button3D
                      variant="primary"
                      size="sm"
                      className="w-full flex items-center justify-center gap-2"
                      onClick={() => {
                        const reading = selectedEntity.value ?? selectedEntity.state?.value ?? 'No current reading';
                        setStatusMessage(`${selectedEntity.name || 'Sensor'} telemetry: ${String(reading)}`);
                        setCommandResult({ id: selectedEntity.id, type: 'sensor', value: reading, status: selectedEntity.status || 'active' });
                      }}
                    >
                      Read telemetry
                    </Button3D>
                  )}

                  {selectedEntity.type === 'device' && (
                    <Button3D
                      variant="primary"
                      size="sm"
                      className="w-full flex items-center justify-center gap-2"
                      onClick={() => {
                        setStatusMessage(`${selectedEntity.name || 'Device'} is ${selectedEntity.status || 'online'} and ready for inspection.`);
                        setCommandResult({ id: selectedEntity.id, type: 'device', status: selectedEntity.status || 'online', metadata: selectedEntity });
                      }}
                    >
                      Inspect device
                    </Button3D>
                  )}

                  {selectedEntity.device_id && selectedEntity.kind === 'actuator' && (
                    <div className="grid grid-cols-2 gap-2">
                      <Button3D variant="success" size="sm" onClick={() => controlTwinDevice('start')} disabled={commandLoading}>Start</Button3D>
                      <Button3D variant="danger" size="sm" onClick={() => controlTwinDevice('stop')} disabled={commandLoading}>Stop</Button3D>
                    </div>
                  )}

                  {selectedEntity.type === 'robot' && (
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
                  )}

                  {selectedEntity.type === 'zone' && (
                    <Button3D
                      variant="primary"
                      size="sm"
                      className="w-full flex items-center justify-center gap-2"
                      onClick={() => scheduleZoneTask('irrigate')}
                      disabled={commandLoading}
                    >
                      Schedule Irrigation
                    </Button3D>
                  )}
                </div>

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

        <LiveTelemetryPanel
          readings={[
            ...liveSensorReadings,
            ...estateState.sensors.map((sensor) => ({
              sensor_id: sensor.sensor_id ?? sensor.id,
              sensor_name: sensor.name,
              type: sensor.sensor_type ?? sensor.type,
              value: sensor.value,
              unit: sensor.unit,
              reading_status: sensor.reading_status ?? 'normal',
              timestamp: sensor.timestamp,
            })),
          ]}
        />

        <div className="grid lg:grid-cols-2 gap-6">
          <div />
          <PredictiveMaintenancePanel
            recommendations={twinHealth?.recommendations || []}
            optimization={twinHealth?.optimization || []}
            adaptation={twinHealth?.adaptation || []}
          />
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
