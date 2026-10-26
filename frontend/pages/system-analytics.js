import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function SystemAnalytics() {
  const { user, token, loading } = useCurrentUser();
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [dataSource, setDataSource] = useState('');
  const [selectedMetric, setSelectedMetric] = useState('');
  const [historyWindow, setHistoryWindow] = useState('24');
  const [updatedAt, setUpdatedAt] = useState(null);

  const fetchAnalytics = useCallback(async (background = false) => {
    if (!token) return;
    if (!background) setIsLoading(true);
    setError('');
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [healthResponse, devicesResponse, monitoringResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/digital-twin/health`, { headers }),
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }),
        fetch(`${API_URL}/api/v1/robotics/monitoring/dashboard`, { headers }).catch(() => null),
      ]);
      const [health, devices, monitoring] = await Promise.all([
        healthResponse.json().catch(() => ({})),
        devicesResponse.json().catch(() => []),
        monitoringResponse?.ok ? monitoringResponse.json().catch(() => null) : Promise.resolve(null),
      ]);
      if (!healthResponse.ok || !devicesResponse.ok) {
        throw new Error(health.detail || devices.detail || 'Unable to load canonical tenant digital-twin analytics.');
      }
      const tenantDevices = Array.isArray(devices) ? devices : [];
      const robots = tenantDevices.filter((device) => device.kind === 'robot');
      const activeAlerts = (health.alert_summary?.top_alerts || []).map((message, index) => ({
        id: `twin-alert-${index}`,
        title: 'Sensor condition',
        severity: health.alert_summary?.highest_severity || 'warning',
        message,
      }));
      setDashboard({
        real_time_status: {
          system_health: health.status,
          fleet_status: {
            total_robots: robots.length,
            active_robots: robots.filter((robot) => ['active', 'online'].includes(String(robot.status).toLowerCase())).length,
          },
          active_alerts: activeAlerts,
          performance_metrics: monitoring?.real_time_status?.performance_metrics || {},
          last_updated: new Date().toISOString(),
        },
        historical_data: monitoring?.historical_data || { metrics_last_7_days: 0, performance_metrics: [] },
        recommendations: health.recommendations || monitoring?.recommendations || [],
      });
      setDataSource(monitoring ? 'Digital twin + monitoring history' : 'Digital twin; monitoring history unavailable');
      setUpdatedAt(new Date());
    } catch (loadError) {
      setError(loadError.message || 'Unable to load tenant analytics.');
    } finally {
      if (!background) setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) fetchAnalytics();
  }, [loading, user, fetchAnalytics]);

  useEffect(() => {
    if (loading || !user || !token) return undefined;
    const interval = window.setInterval(() => fetchAnalytics(true), 30000);
    return () => window.clearInterval(interval);
  }, [loading, user, token, fetchAnalytics]);

  const metricRows = useMemo(() => Object.entries(dashboard?.real_time_status?.performance_metrics || {})
    .map(([name, metric]) => ({
      name: name.replace('.', ' / '),
      value: Number(metric.value),
      unit: metric.unit || '',
      timestamp: metric.timestamp,
    }))
    .filter((metric) => Number.isFinite(metric.value)), [dashboard]);

  const metricHistory = useMemo(() => {
    const cutoff = Date.now() - Number(historyWindow) * 60 * 60 * 1000;
    return (dashboard?.historical_data?.performance_metrics || [])
      .filter((metric) => Number.isFinite(Number(metric.value)) && new Date(metric.timestamp).getTime() >= cutoff)
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  }, [dashboard, historyWindow]);

  const metricOptions = [...new Set(metricHistory.map((metric) => `${metric.category}.${metric.name}`))];
  const activeMetric = metricOptions.includes(selectedMetric) ? selectedMetric : metricOptions[0] || '';
  const selectedHistory = metricHistory
    .filter((metric) => `${metric.category}.${metric.name}` === activeMetric)
    .map((metric) => ({
      time: new Date(metric.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      value: Number(metric.value),
      unit: metric.unit || '',
      timestamp: metric.timestamp,
    }));

  if (loading) {
    return <div className="text-aegis-muted animate-pulse">Loading...</div>;
  }

  const status = dashboard?.real_time_status;
  const fleet = status?.fleet_status;
  const alerts = status?.active_alerts || [];
  const history = dashboard?.historical_data || {};

  return (
    <div className="w-full">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
        <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">
          System Analytics
        </h1>
        <p className="text-aegis-muted">Tenant health, fleet state, active alerts, and recorded performance metrics.</p>
        </div>
        <div className="flex items-center gap-3">
          {dataSource && <span className="text-xs text-slate-500">{dataSource}</span>}
          <span className="text-xs text-slate-500">{updatedAt ? `Updated ${updatedAt.toLocaleTimeString()}` : 'Waiting for data'}</span>
          <button onClick={() => fetchAnalytics()} disabled={isLoading} className="rounded border border-cyan-700 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-950 disabled:opacity-50">{isLoading ? 'Refreshing...' : 'Refresh'}</button>
        </div>
      </div>

      {error && <div role="alert" className="mb-5 rounded border border-red-700 bg-red-900/20 p-4 text-sm text-red-200">{error}</div>}

      <div className="grid grid-cols-2 gap-5 border-y border-slate-800 py-5 md:grid-cols-4">
        {[
          ['System health', status?.system_health],
          ['Robots active', fleet ? `${fleet.active_robots}/${fleet.total_robots}` : null],
          ['Active alerts', alerts.length],
          ['Metrics, last 7 days', history.metrics_last_7_days],
        ].map(([label, value]) => (
          <div key={label}><p className="text-xs uppercase tracking-wider text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-white">{value ?? 'Unavailable'}</p></div>
        ))}
      </div>

      <div className="mt-8 grid gap-8 xl:grid-cols-[1.2fr_1fr]">
        <section className="min-w-0 border-b border-slate-800 pb-6 xl:border-b-0">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">Recorded performance history</h2>
            <div className="flex gap-2">
              <select aria-label="Metric history window" value={historyWindow} onChange={(event) => setHistoryWindow(event.target.value)} className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200">
                <option value="24">Last 24 hours</option>
                <option value="168">Last 7 days</option>
              </select>
              <select aria-label="Performance metric" value={activeMetric} onChange={(event) => setSelectedMetric(event.target.value)} className="max-w-52 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200">
                {metricOptions.map((metric) => <option key={metric} value={metric}>{metric.replace('.', ' / ')}</option>)}
              </select>
            </div>
          </div>
          {selectedHistory.length ? <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={selectedHistory} margin={{ bottom: 8, left: 8, right: 12, top: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#263244" />
                <XAxis dataKey="time" stroke="#94a3b8" minTickGap={24} />
                <YAxis stroke="#94a3b8" />
                <Tooltip labelFormatter={(_label, items) => items?.[0]?.payload?.timestamp ? new Date(items[0].payload.timestamp).toLocaleString() : ''} formatter={(value, _name, item) => [`${value} ${item.payload.unit}`, activeMetric]} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="value" stroke="#38bdf8" strokeWidth={2} dot={selectedHistory.length < 30} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div> : <p className="py-8 text-sm text-slate-400">No persisted metric samples in this time window.</p>}
          <h3 className="mb-3 mt-6 text-sm font-semibold text-slate-300">Latest values</h3>
          {metricRows.length ? <>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metricRows} margin={{ bottom: 48, left: 8, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263244" />
                  <XAxis dataKey="name" angle={-25} textAnchor="end" interval={0} height={60} stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip formatter={(value, _name, item) => [`${value} ${item.payload.unit}`, 'Value']} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }} />
                  <Bar dataKey="value" fill="#38bdf8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="divide-y divide-slate-800">
              {metricRows.map((metric) => <div key={metric.name} className="flex justify-between gap-4 py-2 text-sm"><span className="text-slate-300">{metric.name}</span><span className="font-mono text-cyan-200">{metric.value} {metric.unit}</span></div>)}
            </div>
          </> : <p className="py-8 text-sm text-slate-400">No performance metrics have been recorded for this tenant yet.</p>}
        </section>

        <section className="min-w-0">
          <h2 className="mb-4 text-lg font-semibold text-white">Active alerts</h2>
          {alerts.length ? <div className="divide-y divide-slate-800 border-y border-slate-800">{alerts.map((alert) => <article key={alert.id} className="py-3"><div className="flex justify-between gap-3"><strong className="text-slate-200">{alert.title}</strong><span className="text-xs uppercase text-amber-300">{alert.severity}</span></div><p className="mt-1 text-sm text-slate-400">{alert.message}</p><p className="mt-1 text-xs text-slate-500">{alert.created_at ? new Date(alert.created_at).toLocaleString() : 'No timestamp'}</p></article>)}</div> : <p className="py-8 text-sm text-slate-400">No active alerts reported.</p>}
          {dashboard?.recommendations?.length > 0 && <div className="mt-6"><h3 className="mb-2 text-sm font-semibold text-white">Monitoring recommendations</h3><ul className="space-y-2 text-sm text-slate-400">{dashboard.recommendations.map((item, index) => {
            const message = typeof item === 'string' ? item : item?.message || item?.title || JSON.stringify(item);
            const key = typeof item === 'string' ? `${index}-${item}` : `${index}-${item?.type || item?.focus || 'recommendation'}`;
            return <li key={key}>{message}</li>;
          })}</ul></div>}
        </section>
      </div>

      <div className="mt-8 border-t border-slate-800 pt-4">
        <Link href="/estate-dashboard" className="text-aegis-primary hover:text-aegis-primary/80 transition-colors">
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
