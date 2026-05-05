import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Sidebar from '../components/Sidebar';
import ProtectedRoute from '../components/ProtectedRoute';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

function AuditLogsContent() {
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
      const resp = await fetch(`${API_URL}/api/v1/audit-logs`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
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

  const getEventColor = (eventType) => {
    if (!eventType) return 'text-slate-400';
    const lower = eventType.toLowerCase();
    if (lower.includes('auth') || lower.includes('login')) return 'text-blue-400';
    if (lower.includes('delete')) return 'text-red-400';
    if (lower.includes('create')) return 'text-green-400';
    if (lower.includes('update')) return 'text-yellow-400';
    if (lower.includes('error')) return 'text-red-500';
    return 'text-slate-400';
  };

  const filteredLogs = logs
    .filter(log => {
      const matchesType = filterType === 'all' || (log.event_type || '').includes(filterType);
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
    <div className="flex min-h-screen bg-[#0b1120]">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Audit Logs</h1>
            <p className="text-aegis-muted">Compliance and security event history</p>
          </div>
          <button
            onClick={() => { setLoadingLogs(true); fetchLogs(); }}
            className="px-4 py-2 bg-aegis-primary hover:bg-aegis-primary/80 text-white rounded-lg font-semibold transition-colors"
          >
            ↻ Refresh
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400 flex items-center justify-between">
            <span>✗ {error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">✕</button>
          </div>
        )}

        {/* Filters & Search */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm text-aegis-muted font-semibold mb-2">Search Events</label>
            <input
              type="text"
              placeholder="Search by event type or hash..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm text-aegis-muted font-semibold mb-2">Event Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:border-aegis-primary focus:outline-none transition-colors"
            >
              <option value="all">All Events</option>
              <option value="auth">Authentication</option>
              <option value="create">Created</option>
              <option value="update">Updated</option>
              <option value="delete">Deleted</option>
              <option value="error">Errors</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-aegis-muted font-semibold mb-2">Sort By</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:border-aegis-primary focus:outline-none transition-colors"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>
          </div>
        </div>

        {/* Logs Table */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
          {loadingLogs ? (
            <div className="p-8 text-center text-aegis-muted">Loading audit logs...</div>
          ) : filteredLogs.length === 0 ? (
            <div className="p-8 text-center text-aegis-muted">
              {logs.length === 0 ? 'No audit logs found.' : 'No logs match your filters.'}
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
                    <tr key={idx} className="border-b border-slate-800 hover:bg-slate-800/30">
                      <td className="px-6 py-3">
                        <span className={`font-semibold ${getEventColor(log.event_type)}`}>
                          {log.event_type || 'Unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-3 font-mono text-xs text-aegis-muted">
                        {log.data_hash ? log.data_hash.substring(0, 16) + '...' : 'N/A'}
                      </td>
                      <td className="px-6 py-3 font-mono text-xs text-aegis-muted">
                        {log.blockchain_tx ? log.blockchain_tx.substring(0, 12) + '...' : '—'}
                      </td>
                      <td className="px-6 py-3 text-xs text-aegis-muted">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Footer with count */}
          {!loadingLogs && logs.length > 0 && (
            <div className="px-6 py-3 bg-slate-800/30 border-t border-slate-800 text-xs text-aegis-muted">
              Showing {filteredLogs.length} of {logs.length} events
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="mt-8 p-6 bg-slate-900/50 border border-slate-800 rounded-lg">
          <h3 className="text-aegis-primary font-semibold mb-3">About Audit Logs</h3>
          <ul className="text-sm text-aegis-muted space-y-2">
            <li>• All events are logged for compliance and security purposes</li>
            <li>• Blockchain transaction hashes link to immutable records (when enabled)</li>
            <li>• Data hashes provide integrity verification</li>
            <li>• Events are retained according to your compliance requirements</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export default function AuditLogsPage() {
  return (
    <ProtectedRoute>
      <AuditLogsContent />
    </ProtectedRoute>
  );
}
