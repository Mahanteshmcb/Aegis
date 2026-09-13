import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function AuditLogsPage() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState('newest');

  useEffect(() => {
    if (!loading && user) {
      fetchLogs();
    }
  }, [user, loading]);

  async function fetchLogs() {
    try {
      setLoadingLogs(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/audit`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      });

      if (resp.status === 401) {
        router.push('/login');
        return;
      }

      if (!resp.ok) {
        throw new Error('Failed to load audit logs');
      }

      const data = await resp.json();
      setLogs(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Fetch logs error:', err);
    } finally {
      setLoadingLogs(false);
    }
  }

  const filteredLogs = logs
    .filter((log) => {
      const matchesType = filterType === 'all' || (log.event_type || '').toLowerCase().includes(filterType.toLowerCase());
      const matchesSearch = !searchQuery ||
        (log.event_type || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (log.data_hash || '').toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesSearch;
    })
    .sort((a, b) => {
      const timeA = new Date(a.created_at || 0).getTime();
      const timeB = new Date(b.created_at || 0).getTime();
      return sortOrder === 'newest' ? timeB - timeA : timeA - timeB;
    });

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Audit Logs</h1>
          <p className="text-aegis-muted">Compliance and security event history.</p>
        </div>
        <button onClick={fetchLogs} className="px-5 py-3 rounded-2xl bg-aegis-primary text-white font-semibold hover:bg-sky-400 transition-all">
          Refresh
        </button>
      </div>

      {error && <div className="rounded-3xl border border-red-700 bg-red-900/20 p-4 text-red-300">{error}</div>}

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <div>
          <label className="block text-sm text-aegis-muted font-semibold mb-2">Search Events</label>
          <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search by event type or hash..." className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary" />
        </div>
        <div>
          <label className="block text-sm text-aegis-muted font-semibold mb-2">Event Type</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary">
            <option value="all">All Events</option>
            <option value="auth">Authentication</option>
            <option value="create">Created</option>
            <option value="update">Updated</option>
            <option value="delete">Deleted</option>
            <option value="error">Errors</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-aegis-muted font-semibold mb-2">Sort Order</label>
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary">
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-700 bg-slate-900/80 overflow-hidden">
        {loadingLogs ? (
          <div className="p-8 text-center text-aegis-muted">Loading audit logs...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-8 text-center">
            <div className="mb-2 text-xl font-semibold text-white">
              {logs.length === 0 ? 'No audit events recorded yet.' : 'No audit events match the current filters.'}
            </div>
            <p className="text-aegis-muted">
              {logs.length === 0
                ? 'This tenant has not generated any audit records yet. Successful logins, sensor changes, and admin actions will appear here.'
                : 'Try clearing the event-type filter or searching for a different keyword.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-700 bg-slate-800/50">
                <tr>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Event Type</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Hash</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Blockchain TX</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log, idx) => (
                  <tr key={idx} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-3 font-semibold text-white">{log.event_type || 'Unknown'}</td>
                    <td className="px-6 py-3 font-mono text-xs text-aegis-muted">{log.data_hash ? `${log.data_hash.slice(0, 16)}...` : 'N/A'}</td>
                    <td className="px-6 py-3 font-mono text-xs text-aegis-muted">{log.blockchain_tx ? `${log.blockchain_tx.slice(0, 12)}...` : '—'}</td>
                    <td className="px-6 py-3 text-xs text-aegis-muted">{log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {!loadingLogs && logs.length > 0 && (
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-4 text-xs text-aegis-muted">Showing {filteredLogs.length} of {logs.length} events.</div>
      )}
    </div>
  );
}

