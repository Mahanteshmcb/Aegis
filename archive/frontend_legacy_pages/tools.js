import { useState, useEffect } from 'react';
import RoleBasedRoute from '../../components/RoleBasedRoute';
import useCurrentUser from '../../hooks/useCurrentUser';
import { exportAuditCSV, listSessions, revokeSession, bulkImportSensors } from '../../utils/api';

export default function AdminTools() {
  const { user } = useCurrentUser();
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [auditDownloading, setAuditDownloading] = useState(false);
  const [importResult, setImportResult] = useState(null);

  useEffect(() => {
    if (user) fetchSessions();
  }, [user]);

  async function fetchSessions() {
    try {
      setLoadingSessions(true);
      const token = localStorage.getItem('aegis_token');
      const data = await listSessions(token);
      setSessions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSessions(false);
    }
  }

  async function handleRevoke(id) {
    try {
      const token = localStorage.getItem('aegis_token');
      await revokeSession(token, id);
      fetchSessions();
    } catch (e) {
      console.error(e);
    }
  }

  async function handleExport() {
    try {
      setAuditDownloading(true);
      const token = localStorage.getItem('aegis_token');
      const blob = await exportAuditCSV(token, {});
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_export_${new Date().toISOString()}.csv`;
      document.body.appendChild(a);
      a.click();
+      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
    } finally {
      setAuditDownloading(false);
    }
  }

  async function handleFileImport(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await bulkImportSensors(token, file);
      setImportResult(res.summary);
      fetchSessions();
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <RoleBasedRoute requiredRole="admin">
      <div className="space-y-6 p-6">
        <h1 className="text-2xl font-bold">Admin Tools</h1>

        <section className="rounded border p-4">
          <h2 className="font-semibold">Audit Export</h2>
          <p className="text-sm text-slate-400">Download tenant audit logs as CSV.</p>
          <div className="mt-3">
            <button onClick={handleExport} className="px-4 py-2 bg-cyan-600 text-white rounded">{auditDownloading ? 'Downloading...' : 'Export Audit CSV'}</button>
          </div>
        </section>

        <section className="rounded border p-4">
          <h2 className="font-semibold">Sessions</h2>
          <p className="text-sm text-slate-400">List and revoke active sessions.</p>
          <div className="mt-3">
            <button onClick={fetchSessions} className="px-3 py-2 bg-slate-700 text-white rounded mr-2">Refresh</button>
          </div>
          <div className="mt-3">
            {loadingSessions ? <div>Loading...</div> : (
              <ul>
                {sessions.map(s => (
                  <li key={s.id} className="flex items-center justify-between py-2 border-b">
                    <div>
                      <div className="text-sm font-mono">User: {s.user_id}</div>
                      <div className="text-xs text-slate-400">Expires: {s.expires_at || 'n/a'}</div>
                    </div>
                    <div>
                      {!s.revoked && <button onClick={() => handleRevoke(s.id)} className="px-3 py-1 bg-red-600 text-white rounded">Revoke</button>}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="rounded border p-4">
          <h2 className="font-semibold">Sensors Bulk Import</h2>
          <p className="text-sm text-slate-400">Upload CSV with headers: name,type,location,zone_id</p>
          <div className="mt-3">
            <input type="file" accept="text/csv" onChange={handleFileImport} />
            {importResult && <div className="mt-2 text-sm">Created: {importResult.created} Updated: {importResult.updated}</div>}
          </div>
        </section>
      </div>
    </RoleBasedRoute>
  );
}
