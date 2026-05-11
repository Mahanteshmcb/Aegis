import { useState, useEffect } from 'react';
import Link from 'next/link';
import TacticalMap from '../components/TacticalMap';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function Dashboard() {
  const { user, loading } = useCurrentUser();
  const [metrics, setMetrics] = useState({ zones: 0, sensors: 0, users: 0, auditLogs: 0 });
  const [loadingMetrics, setLoadingMetrics] = useState(true);

  useEffect(() => {
    if (!loading && user) {
      fetchMetrics();
    }
  }, [user, loading]);

  async function fetchMetrics() {
    try {
      const token = localStorage.getItem('aegis_token');
      const [zonesRes, sensorsRes, auditRes, usersRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/zones`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/sensors`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/audit`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/auth/users`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ ok: false })),
      ]);

      const zones = zonesRes.ok ? await zonesRes.json() : [];
      const sensors = sensorsRes.ok ? await sensorsRes.json() : [];
      const auditLogs = auditRes.ok ? await auditRes.json() : [];
      const users = usersRes.ok ? await usersRes.json() : [];

      setMetrics({
        zones: Array.isArray(zones) ? zones.length : 0,
        sensors: Array.isArray(sensors) ? sensors.length : 0,
        users: Array.isArray(users) ? users.length : 1,
        auditLogs: Array.isArray(auditLogs) ? auditLogs.length : 0,
      });
    } catch (err) {
      console.error('Error fetching metrics:', err);
    } finally {
      setLoadingMetrics(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="text-aegis-muted animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <>
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Dashboard</h1>
        <p className="text-aegis-muted">Welcome back, {user?.email || 'Operator'}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-12">
        <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/50 rounded-lg p-6 hover:border-blue-600/80 transition-colors">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-aegis-muted text-sm font-semibold uppercase tracking-wider">Zones</p>
              <p className="text-4xl font-bold text-blue-400 mt-2">{loadingMetrics ? '—' : metrics.zones}</p>
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
              <p className="text-4xl font-bold text-green-400 mt-2">{loadingMetrics ? '—' : metrics.sensors}</p>
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
              <p className="text-4xl font-bold text-yellow-400 mt-2">{loadingMetrics ? '—' : metrics.auditLogs}</p>
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
              <p className="text-4xl font-bold text-red-400 mt-2">{loadingMetrics ? '—' : metrics.users}</p>
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
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                <p className="text-xl font-bold text-green-400">Online</p>
              </div>
            </div>
            <div className="text-3xl text-purple-500 opacity-50">⚡</div>
          </div>
          <p className="text-aegis-muted text-xs mt-4">All systems operational</p>
          <Link href="/system-control" className="text-purple-400 text-xs font-semibold mt-4 inline-block hover:text-purple-300">System Control →</Link>
        </div>
      </div>

      <div className="mb-12">
        <TacticalMap anomaly={false} />
      </div>

      <div className="mb-12">
        <h2 className="text-2xl font-bold text-aegis-primary mb-4 tracking-[0.1em]">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/zones" className="group block bg-slate-900/50 hover:bg-slate-800/70 border border-slate-800 hover:border-slate-700 rounded-lg p-6 transition-all">
            <h3 className="text-lg font-semibold text-aegis-primary">Create New Zone</h3>
            <p className="text-aegis-muted text-sm mt-2">Define a new security zone for asset monitoring.</p>
          </Link>
          <Link href="/sensors" className="group block bg-slate-900/50 hover:bg-slate-800/70 border border-slate-800 hover:border-slate-700 rounded-lg p-6 transition-all">
            <h3 className="text-lg font-semibold text-green-300">Register Sensor</h3>
            <p className="text-aegis-muted text-sm mt-2">Add a new IoT sensor to the network.</p>
          </Link>
          <Link href="/audit-logs" className="group block bg-slate-900/50 hover:bg-slate-800/70 border border-slate-800 hover:border-slate-700 rounded-lg p-6 transition-all">
            <h3 className="text-lg font-semibold text-yellow-300">View Audit Trail</h3>
            <p className="text-aegis-muted text-sm mt-2">Review compliance and security events.</p>
          </Link>
          <Link href="/system-control" className="group block bg-slate-900/50 hover:bg-slate-800/70 border border-slate-800 hover:border-slate-700 rounded-lg p-6 transition-all">
            <h3 className="text-lg font-semibold text-violet-300">System Control</h3>
            <p className="text-aegis-muted text-sm mt-2">Open the Day 50 control dashboard.</p>
          </Link>
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-aegis-primary mb-4">System Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6 text-sm">
          <div>
            <p className="text-aegis-muted font-semibold">Your Email</p>
            <p className="text-aegis-text font-mono mt-1">{user?.email}</p>
          </div>
          <div>
            <p className="text-aegis-muted font-semibold">Role</p>
            <p className="text-aegis-text capitalize mt-1">{user?.role}</p>
          </div>
          <div>
            <p className="text-aegis-muted font-semibold">Tenant ID</p>
            <p className="text-aegis-text font-mono mt-1">{user?.tenant_id}</p>
          </div>
          <div>
            <p className="text-aegis-muted font-semibold">Backend</p>
            <p className="text-aegis-text font-mono mt-1">FastAPI v1</p>
          </div>
          <div>
            <p className="text-aegis-muted font-semibold">Database</p>
            <p className="text-aegis-text font-mono mt-1">SQLite</p>
          </div>
          <div>
            <p className="text-aegis-muted font-semibold">Status</p>
            <p className="text-green-400 font-semibold mt-1">● Operational</p>
          </div>
        </div>
      </div>
    </>
  );
}
