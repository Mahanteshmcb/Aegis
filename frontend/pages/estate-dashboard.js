import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, Bot, Cpu, Layers, RefreshCw, ShieldCheck, Thermometer, Trash2, Droplets, FlaskConical, Zap, Warehouse } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const navigation = [
  { name: 'Zones', href: '/zones', icon: Layers },
  { name: 'Sensors', href: '/sensors', icon: Thermometer },
  { name: 'Robots', href: '/robots-management', icon: Bot },
  { name: 'Devices', href: '/devices', icon: Cpu },
  { name: 'Safety', href: '/safety-dashboard', icon: ShieldCheck },
  { name: 'Water', href: '/water-dashboard', icon: Droplets },
  { name: 'Waste', href: '/waste-dashboard', icon: Trash2 },
  { name: 'System Control', href: '/system-control', icon: Activity },
];

const systemDefinitions = [
  { name: 'Climate', href: '/environmental', icon: Thermometer, match: /temperature|humidity|climate|air|hvac|co2/ },
  { name: 'Water', href: '/water-dashboard', icon: Droplets, match: /water|flow|pump|valve|irrigation/ },
  { name: 'Energy', href: '/system-analytics', icon: Zap, match: /energy|power|battery|solar|voltage/ },
  { name: 'Biosphere', href: '/robots-management', icon: Bot, match: /soil|crop|greenhouse|plant|robot|agri/ },
  { name: 'Security', href: '/safety-dashboard', icon: ShieldCheck, match: /security|access|motion|camera|gate|lock/ },
  { name: 'Laboratory', href: '/devices', icon: FlaskConical, match: /lab|sample|experiment|chemical|ph/ },
  { name: 'Storage', href: '/storage', icon: Warehouse, match: /storage|warehouse|inventory|cold/ },
  { name: 'Waste', href: '/waste-dashboard', icon: Trash2, match: /waste|compost|recycl/ },
];

export default function EstateDashboard() {
  const { user, token, loading: userLoading } = useCurrentUser();
  const [devices, setDevices] = useState([]);
  const [storageFacilities, setStorageFacilities] = useState([]);
  const [zoneCount, setZoneCount] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [updatedAt, setUpdatedAt] = useState(null);

  const refreshOverview = useCallback(async (background = false) => {
    if (!token) return;
    if (background) setRefreshing(true);
    else setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [deviceResponse, zoneResponse, healthResponse, storageResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }),
        fetch(`${API_URL}/api/v1/zones`, { headers }),
        fetch(`${API_URL}/api/v1/digital-twin/health`, { headers }),
        fetch(`${API_URL}/api/v1/storage/facilities`, { headers }),
      ]);
      const [deviceData, zoneData, healthData, storageData] = await Promise.all([
        deviceResponse.json().catch(() => []),
        zoneResponse.json().catch(() => []),
        healthResponse.json().catch(() => ({})),
        storageResponse.json().catch(() => []),
      ]);
      if (!deviceResponse.ok || !zoneResponse.ok || !healthResponse.ok || !storageResponse.ok) {
        throw new Error('Unable to load the complete tenant overview. Retry after checking the backend connection.');
      }
      setDevices(Array.isArray(deviceData) ? deviceData : []);
      setStorageFacilities(Array.isArray(storageData) ? storageData : []);
      setZoneCount(Array.isArray(zoneData) ? zoneData.length : 0);
      setHealth(healthData);
      setUpdatedAt(new Date());
      setError('');
    } catch (loadError) {
      setError(loadError.message || 'Unable to load tenant overview.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => {
    if (!userLoading && user) refreshOverview();
  }, [userLoading, user, refreshOverview]);

  useEffect(() => {
    if (!user || !token) return undefined;
    const interval = window.setInterval(() => refreshOverview(true), 30000);
    return () => window.clearInterval(interval);
  }, [user, token, refreshOverview]);

  const counts = devices.reduce((result, device) => {
    const kind = ['sensor', 'robot', 'actuator'].includes(device.kind) ? device.kind : 'other';
    result[kind] += 1;
    if (String(device.status || '').toLowerCase() === 'online') result.online += 1;
    return result;
  }, { sensor: 0, robot: 0, actuator: 0, other: 0, online: 0 });

  const alertSummary = health?.alert_summary;
  const alerts = Array.isArray(alertSummary?.top_alerts) ? alertSummary.top_alerts : [];
  const systemStatus = health?.status || 'unavailable';
  const systemPanels = systemDefinitions.map((system) => {
    const assets = devices.filter((device) => system.match.test(`${device.name || ''} ${device.kind || ''} ${device.device_type || ''}`));
    const facilities = system.name === 'Storage' ? storageFacilities : [];
    const online = assets.filter((device) => String(device.status || '').toLowerCase() === 'online').length;
    const attention = assets.filter((device) => ['warning', 'critical'].includes(String(device.state?.reading_status || '').toLowerCase())).length;
    const readings = assets.filter((device) => device.state?.value !== undefined && device.state?.value !== null);
    return { ...system, assets, facilities, online, attention, readings };
  });

  if (userLoading || loading) {
    return <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center text-slate-400">Loading estate overview...</main>;
  }

  if (!user) {
    return <main className="p-6 text-slate-300">Sign in to view your estate overview. <Link href="/login" className="text-cyan-300">Sign in</Link></main>;
  }

  return (
    <main className="mx-auto max-w-7xl space-y-8 p-6 text-slate-100">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-cyan-300">Tenant {user.tenant_id}</p>
          <h1 className="mt-2 text-3xl font-semibold">Estate Overview</h1>
          <p className="mt-2 text-sm text-slate-400">Zones, connected assets, and current system health.</p>
        </div>
        <div className="flex items-center gap-4">
          <p className="text-xs text-slate-500">{updatedAt ? `Updated ${updatedAt.toLocaleTimeString()}` : 'Not updated'}</p>
          <button onClick={() => refreshOverview(true)} disabled={refreshing} aria-label="Refresh estate overview" title="Refresh estate overview" className="rounded border border-slate-700 p-2 text-slate-200 hover:border-cyan-600 disabled:opacity-50">
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          </button>
        </div>
      </header>

      {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-4 text-sm text-red-200">{error}</div>}

      <section aria-label="Estate key metrics" className="grid grid-cols-2 gap-5 border-b border-slate-800 pb-6 sm:grid-cols-3 xl:grid-cols-6">
        {[
          ['Zones', zoneCount, '/zones'],
          ['Devices', devices.length, '/devices'],
          ['Online', counts.online, '/devices'],
          ['Sensors', counts.sensor, '/sensors'],
          ['Robots', counts.robot, '/robots-management'],
          ['Actuators', counts.actuator, '/actuators'],
        ].map(([label, value, href]) => (
          <Link key={label} href={href} className="border-l-2 border-cyan-700 pl-3 hover:border-cyan-300">
            <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-semibold text-white">{value ?? '—'}</p>
          </Link>
        ))}
      </section>

      <section className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_minmax(20rem,0.8fr)]">
        <div>
          <div className="flex items-baseline justify-between border-b border-slate-800 pb-2">
            <h2 className="text-lg font-semibold">System health</h2>
            <span className={`text-sm font-semibold uppercase ${systemStatus === 'healthy' ? 'text-emerald-300' : systemStatus === 'critical' ? 'text-red-300' : systemStatus === 'degraded' ? 'text-amber-300' : 'text-slate-400'}`}>{systemStatus}</span>
          </div>
          <div className="mt-4 flex flex-wrap gap-x-8 gap-y-3 text-sm">
            <p className="text-slate-400">Health score <span className="ml-2 font-mono text-white">{Number.isFinite(Number(health?.health_score)) ? `${health.health_score}%` : 'Unavailable'}</span></p>
            <p className="text-slate-400">Alerts <span className="ml-2 font-mono text-white">{health?.alerts ?? 'Unavailable'}</span></p>
            <p className="text-slate-400">Recommendations <span className="ml-2 font-mono text-white">{health?.recommendation_summary?.total ?? 'Unavailable'}</span></p>
          </div>
        </div>

        <div>
          <div className="flex items-baseline justify-between border-b border-slate-800 pb-2">
            <h2 className="text-lg font-semibold">Critical conditions</h2>
            <span className="text-xs text-slate-500">{alertSummary ? `${alertSummary.total ?? alerts.length} active` : 'Unavailable'}</span>
          </div>
          {alerts.length ? <ul className="divide-y divide-slate-800">{alerts.map((message, index) => <li key={`${index}-${message}`} className="py-3 text-sm text-amber-200">{message}</li>)}</ul> : <p className="py-4 text-sm text-slate-400">{alertSummary ? 'No current alert conditions.' : 'Alert conditions unavailable.'}</p>}
        </div>
      </section>

      <section aria-label="Estate operational systems" className="space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-slate-800 pb-2">
          <div><h2 className="text-lg font-semibold">Operational systems</h2><p className="mt-1 text-xs text-slate-500">Live inventory and condition counts from registered tenant devices.</p></div>
          <Link href="/3d-scene" className="text-xs text-cyan-300 hover:text-cyan-100">Open 3D estate view</Link>
        </div>
        <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2 xl:grid-cols-4">
          {systemPanels.map(({ name, href, icon: Icon, assets, facilities, online, attention, readings }) => (
            <Link key={name} href={href} className="group min-h-36 border-b border-slate-800 py-4 transition hover:border-cyan-700">
              <div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2"><Icon size={16} className="text-cyan-300" /><h3 className="text-sm font-semibold text-white">{name}</h3></div><span className="text-xs text-slate-500">{assets.length + facilities.length} assets</span></div>
              {assets.length || facilities.length ? <>
                {facilities.length > 0 && <div className="mt-4 flex items-baseline justify-between"><span className="text-xs text-slate-500">Registered facilities</span><span className="font-mono text-sm text-white">{facilities.length}</span></div>}
                {assets.length > 0 && <>
                <div className="mt-4 flex items-baseline justify-between"><span className="text-xs text-slate-500">Online</span><span className="font-mono text-sm text-emerald-300">{online} / {assets.length}</span></div>
                <div className="mt-1 flex items-baseline justify-between"><span className="text-xs text-slate-500">Needs attention</span><span className={`font-mono text-sm ${attention ? 'text-amber-300' : 'text-slate-300'}`}>{attention}</span></div>
                <p className="mt-2 truncate text-[11px] text-slate-500">{readings.length ? `${readings.length} current readings` : 'No current readings reported'}</p>
                </>}
              </> : <p className="mt-5 text-xs text-slate-500">No connected assets reported</p>}
            </Link>
          ))}
        </div>
      </section>

      <nav aria-label="Operational pages" className="grid grid-cols-2 gap-x-6 md:grid-cols-4">
        {navigation.map(({ name, href, icon: Icon }) => <Link key={href} href={href} className="flex items-center gap-3 border-b border-slate-800 py-4 text-sm text-slate-300 hover:text-cyan-200"><Icon size={17} className="text-cyan-400" />{name}</Link>)}
        <Link href="/audit-logs" className="flex items-center gap-3 border-b border-slate-800 py-4 text-sm text-slate-300 hover:text-cyan-200"><Activity size={17} className="text-cyan-400" />Audit Logs</Link>
      </nav>
    </main>
  );
}