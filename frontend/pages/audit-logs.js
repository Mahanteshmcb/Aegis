import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Card from '../components/Card';
import { getAuditLogs } from '../utils/api';
import { getAuthToken } from '../utils/auth';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.push('/login');
      return;
    }

    const loadLogs = async () => {
      setLoading(true);
      try {
        const data = await getAuditLogs(token);
        setLogs(data || []);
        setError(null);
      } catch (err) {
        if (err.message?.includes('401')) {
          localStorage.removeItem('aegis_token');
          router.push('/login');
        } else {
          setError(err.message || 'Unable to load audit logs');
        }
      } finally {
        setLoading(false);
      }
    };

    loadLogs();
  }, [router]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-white">Audit Logs</h1>
        <p className="mt-2 text-sm text-aegis-muted">Browse event history for compliance, security, and sensor activity.</p>
      </div>

      <Card title="Recent Audit Events">
        {loading ? (
          <p className="text-sm text-aegis-muted">Loading audit data...</p>
        ) : error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : logs.length ? (
          <div className="space-y-3">
            {logs.slice(0, 10).map((log) => (
              <div key={log.id} className="glass-card border border-slate-800 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-aegis-muted">Event</p>
                    <p className="font-medium text-white">{log.event_type}</p>
                  </div>
                  <span className="text-xs uppercase tracking-widest text-aegis-primary">ID {log.id}</span>
                </div>
                <p className="mt-3 text-sm text-aegis-muted">Sensor: {log.sensor_id ?? 'N/A'}</p>
                <p className="mt-2 text-xs text-slate-400 break-all">Hash: {log.data_hash}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-aegis-muted">No audit log entries are available yet.</p>
        )}
      </Card>
    </div>
  );
}
