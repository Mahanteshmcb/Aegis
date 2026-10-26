import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Activity, ArrowLeft, Cpu } from 'lucide-react';
import Layout3D from '../components/Layout3D';
import Card3D from '../components/Card3D';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const kindMeta = {
  sensor: { label: 'Sensor', icon: Activity, color: 'text-cyan-300' },
  robot: { label: 'Robot', icon: Cpu, color: 'text-emerald-300' },
  actuator: { label: 'Actuator', icon: Cpu, color: 'text-amber-300' },
};

export default function DevicesPage() {
  const { user, loading, token } = useCurrentUser();
  const [devices, setDevices] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [kindFilter, setKindFilter] = useState('all');

  const fetchDevices = useCallback(async () => {
    if (!token) return;
    try {
      setLoadingData(true);
      const headers = { Authorization: `Bearer ${token}` };
      const [response, zonesResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }),
        fetch(`${API_URL}/api/v1/zones`, { headers }).catch(() => null),
      ]);

      if (!response.ok) {
        throw new Error('Unable to load estate devices.');
      }

      const payload = await response.json().catch(() => []);
      const rows = Array.isArray(payload) ? payload : [];
      const zonePayload = zonesResponse?.ok ? await zonesResponse.json().catch(() => []) : [];
      const zoneNames = new Map((Array.isArray(zonePayload) ? zonePayload : []).map((zone) => [String(zone.id), zone.name]));
      setDevices(
        rows
          .filter((device) => ['sensor', 'robot', 'actuator'].includes(device.kind))
          .map((device) => ({
            ...device,
            status: device.status || 'unknown',
            zoneName: zoneNames.get(String(device.zone_id)) || (device.zone_id == null ? 'Unassigned' : `Zone ${device.zone_id}`),
            kindLabel: kindMeta[device.kind]?.label || 'Device',
          }))
      );
      setError('');
    } catch (fetchError) {
      setError(fetchError.message || 'Unable to load estate devices.');
      setDevices([]);
    } finally {
      setLoadingData(false);
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) {
      fetchDevices();
    }
  }, [user, loading, fetchDevices]);

  const visibleDevices = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    return devices.filter((device) => {
      const matchesKind = kindFilter === 'all' || device.kind === kindFilter;
      const matchesQuery = !query || [device.name, device.device_id, device.device_type, device.zoneName]
        .some((value) => String(value || '').toLowerCase().includes(query));
      return matchesKind && matchesQuery;
    });
  }, [devices, kindFilter, searchTerm]);

  const stats = useMemo(() => {
    const total = devices.length;
    const robotCount = devices.filter((device) => device.kind === 'robot').length;
    const sensorCount = devices.filter((device) => device.kind === 'sensor').length;
    const actuatorCount = devices.filter((device) => device.kind === 'actuator').length;
    const online = devices.filter((device) => ['online', 'active', 'connected'].includes(String(device.status).toLowerCase())).length;
    const offline = devices.filter((device) => String(device.status).toLowerCase() === 'offline').length;

    return { total, robotCount, sensorCount, actuatorCount, online, offline, unknown: total - online - offline };
  }, [devices]);

  return (
    <Layout3D
      title="ESTATE DEVICES"
      icon="📟"
      subtitle="Unified operational view for sensors, robots, and actuators"
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-3">
          <Link href="/estate-dashboard" className="inline-flex items-center gap-2 text-sm text-cyan-300 hover:text-cyan-200">
            <ArrowLeft size={16} /> Back to Estate Dashboard
          </Link>
          <button
            onClick={fetchDevices}
            disabled={loadingData}
            className="rounded border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200 disabled:opacity-50"
          >
            {loadingData ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-5">
          <Card3D variant="primary">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Total</p>
            <p className="mt-3 text-3xl font-bold text-white">{stats.total}</p>
          </Card3D>
          <Card3D variant="success">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Online</p>
            <p className="mt-3 text-3xl font-bold text-emerald-300">{stats.online}</p>
          </Card3D>
          <Card3D variant="secondary">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Robots</p>
            <p className="mt-3 text-3xl font-bold text-cyan-300">{stats.robotCount}</p>
          </Card3D>
          <Card3D variant="primary">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Sensors</p>
            <p className="mt-3 text-3xl font-bold text-sky-300">{stats.sensorCount}</p>
          </Card3D>
          <Card3D variant="warning">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Actuators</p>
            <p className="mt-3 text-3xl font-bold text-amber-300">{stats.actuatorCount}</p>
          </Card3D>
          <Card3D variant="warning">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Offline</p>
            <p className="mt-3 text-3xl font-bold text-rose-300">{stats.offline}</p>
          </Card3D>
          <Card3D variant="secondary">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Unknown</p>
            <p className="mt-3 text-3xl font-bold text-slate-300">{stats.unknown}</p>
          </Card3D>
        </div>

        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_14rem]">
          <input aria-label="Search devices" type="search" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Search name, device ID, type, or zone" className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
          <select aria-label="Filter device kind" value={kindFilter} onChange={(event) => setKindFilter(event.target.value)} className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
            <option value="all">All kinds</option>
            {Object.entries(kindMeta).map(([kind, metadata]) => <option key={kind} value={kind}>{metadata.label}</option>)}
          </select>
        </div>

        {error && (
          <div className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>
        )}

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          {loadingData ? (
            <div className="p-10 text-center text-slate-400">Loading devices...</div>
          ) : devices.length === 0 ? (
            <div className="p-10 text-center text-slate-400">No estate devices are registered yet.</div>
          ) : visibleDevices.length === 0 ? (
            <div className="p-10 text-center text-slate-400">No devices match the selected filters.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-800 text-slate-300">
                  <tr>
                    <th className="px-4 py-3">Device</th>
                    <th className="px-4 py-3">Kind</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Zone</th>
                    <th className="px-4 py-3">Control</th>
                    <th className="px-4 py-3">Last Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200">
                  {visibleDevices.map((device) => {
                    const meta = kindMeta[device.kind] || { label: 'Device', icon: MonitorSmartphone, color: 'text-slate-300' };
                    const Icon = meta.icon;
                    return (
                      <tr key={device.id} className="hover:bg-slate-800/50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <span className={`rounded bg-slate-800 p-2 ${meta.color}`}><Icon size={16} /></span>
                            <div>
                              <div className="font-semibold text-white">{device.name || `Device ${device.id}`}</div>
                              <div className="text-xs text-slate-400">{device.device_id || device.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-slate-300">{meta.label}</td>
                        <td className="px-4 py-3 text-slate-300">{device.device_type || 'general'}</td>
                        <td className="px-4 py-3">
                          <span className={`rounded-full px-2 py-1 text-xs font-medium ${device.status === 'online' || device.status === 'active' ? 'bg-emerald-500/20 text-emerald-200' : device.status === 'offline' ? 'bg-red-500/20 text-red-200' : 'bg-slate-500/20 text-slate-200'}`}>
                            {device.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-300">{device.zoneName}</td>
                        <td className="px-4 py-3 text-slate-300">{device.control_mode || 'unknown'} · {device.simulation_enabled ? 'simulation on' : 'simulation off'}</td>
                        <td className="px-4 py-3 text-slate-400">{device.last_updated ? new Date(device.last_updated).toLocaleString() : 'Unknown'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout3D>
  );
}
