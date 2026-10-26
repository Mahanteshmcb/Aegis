import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const normalizeHash = (hash) => String(hash || '').replace(/^0x/i, '').toLowerCase();

const getChainDetails = (metadata) => {
  if (metadata && typeof metadata === 'object' && !Array.isArray(metadata)) return metadata;
  if (typeof metadata === 'string') {
    try {
      const parsed = JSON.parse(metadata);
      return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
        ? parsed
        : { metadata: parsed };
    } catch {
      return metadata ? { metadata } : {};
    }
  }
  return {};
};

const formatChainLog = (entry) => {
  const details = getChainDetails(entry.metadata);
  const diagnostic = details.source === 'local-connection-check'
    || details.source === 'backend-python-runtime';
  const timestamp = Number(entry.timestamp);
  return {
    ...entry,
    id: `chain:${entry.id}`,
    source: 'blockchain',
    is_diagnostic: diagnostic,
    actor_email: details.actor_email || details.email || details.actor || entry.actor,
    actor_user_id: details.actor_user_id,
    action: details.action || entry.event_type,
    entity_type: details.entity_type || (diagnostic ? 'Blockchain connectivity check' : 'On-chain audit record'),
    entity_id: details.entity_id == null ? null : String(details.entity_id),
    outcome: details.outcome || (entry.verified ? 'Verified on-chain' : 'Not verified on-chain'),
    details,
    created_at: Number.isFinite(timestamp) && timestamp > 0
      ? new Date(timestamp * 1000).toISOString()
      : null,
    blockchain_tx: null,
  };
};

export default function AuditLogsPage() {
  const router = useRouter();
  const { user, loading, token } = useCurrentUser();
  const [logs, setLogs] = useState([]);
  const [blockchainStatus, setBlockchainStatus] = useState({ available: null, message: '' });
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState('newest');
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [updatedAt, setUpdatedAt] = useState(null);

  const nextOffsetRef = useRef(0);
  const fetchLogs = useCallback(async (reset = true) => {
    if (!token) {
      router.push('/login');
      return;
    }
    const offset = reset ? 0 : nextOffsetRef.current;
    try {
      if (reset) setLoadingLogs(true);
      else setLoadingMore(true);
      const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
      const [resp, chainResp] = await Promise.all([
        fetch(`${API_URL}/api/v1/audit?skip=${offset}&limit=100`, { headers }),
        fetch(`${API_URL}/api/v1/audit/blockchain?limit=100`, { headers }).catch(() => null),
      ]);

      if (resp.status === 401) {
        router.push('/login');
        return;
      }

      if (!resp.ok) {
        throw new Error('Failed to load audit logs');
      }

      const data = await resp.json();
      const databasePage = Array.isArray(data) ? data : [];
      let chainLogs = [];
      if (chainResp?.ok) {
        const chainPayload = await chainResp.json().catch(() => []);
        chainLogs = Array.isArray(chainPayload) ? chainPayload : [];
        setBlockchainStatus({ available: true, message: '' });
      } else {
        const chainPayload = await chainResp?.json().catch(() => null);
        setBlockchainStatus({
          available: false,
          message: chainPayload?.detail || (chainResp
            ? `Blockchain audit query failed (${chainResp.status}).`
            : 'Blockchain audit query could not be reached.'),
        });
      }

      const chainByHash = new Map(chainLogs.map((entry) => [normalizeHash(entry.data_hash), entry]));
      const databaseHashes = new Set(databasePage.map((entry) => normalizeHash(entry.data_hash)).filter(Boolean));
      const page = [
        ...databasePage.map((entry) => ({
          ...entry,
          source: chainByHash.has(normalizeHash(entry.data_hash)) ? 'local_and_chain' : 'local',
          chain_record: chainByHash.get(normalizeHash(entry.data_hash)) || null,
        })),
        ...chainLogs
          .filter((entry) => !databaseHashes.has(normalizeHash(entry.data_hash)))
          .map(formatChainLog),
      ];
      setLogs((previous) => {
        if (reset) return page;
        const existingIds = new Set(previous.map((entry) => entry.id));
        return [...previous, ...page.filter((entry) => !existingIds.has(entry.id))];
      });
      nextOffsetRef.current = offset + databasePage.length;
      setHasMore(databasePage.length === 100);
      setUpdatedAt(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Fetch logs error:', err);
    } finally {
      setLoadingLogs(false);
      setLoadingMore(false);
    }
  }, [router, token]);

  useEffect(() => {
    if (!loading && user) fetchLogs();
  }, [user, loading, fetchLogs]);

  const filteredLogs = logs
    .filter((log) => {
      const type = (log.event_type || '').toLowerCase();
      const matchesType = filterType === 'all' || (
        filterType === 'auth' ? /auth|login|logout|session/.test(type) :
          filterType === 'create' ? /creat|add|register/.test(type) :
            filterType === 'update' ? /updat|edit|modif/.test(type) :
              filterType === 'delete' ? /delet|remov/.test(type) :
                filterType === 'error' ? /error|fail|denied|reject/.test(type) :
                  filterType === 'blockchain' ? log.source !== 'local' || Boolean(log.blockchain_tx) : type.includes(filterType)
      );
      const matchesSearch = !searchQuery ||
        [log.event_type, log.actor_email, log.actor_user_id, log.action, log.entity_type, log.entity_id, log.outcome, JSON.stringify(log.details || {}), log.data_hash, log.blockchain_tx, log.sensor_id, log.id, log.chain_record?.id]
          .some((value) => String(value ?? '').toLowerCase().includes(searchQuery.toLowerCase()));
      return (showDiagnostics || !log.is_diagnostic) && matchesType && matchesSearch;
    })
    .sort((a, b) => {
      const timeA = new Date(a.created_at || 0).getTime();
      const timeB = new Date(b.created_at || 0).getTime();
      return sortOrder === 'newest' ? timeB - timeA : timeA - timeB;
    });
  const diagnosticCount = logs.filter((log) => log.is_diagnostic).length;

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-aegis-primary mb-2">Audit Logs</h1>
          <p className="text-aegis-muted">Local audit events and their matching on-chain records. Diagnostic entries are labeled separately.</p>
        </div>
        <div className="flex items-center gap-3"><span className="text-xs text-slate-500">{updatedAt ? `Updated ${updatedAt.toLocaleTimeString()}` : 'Waiting for data'}</span><button onClick={() => fetchLogs()} disabled={loadingLogs} className="rounded border border-cyan-700 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-950 disabled:opacity-50">{loadingLogs ? 'Refreshing...' : 'Refresh'}</button></div>
      </div>

      {error && <div className="rounded-3xl border border-red-700 bg-red-900/20 p-4 text-red-300">{error}</div>}
      {blockchainStatus.available === false && (
        <div role="status" className="rounded-2xl border border-amber-700 bg-amber-950/20 p-4 text-sm text-amber-200">
          On-chain audit records could not be loaded: {blockchainStatus.message} Local audit records are still shown.
        </div>
      )}
      {blockchainStatus.available === true && (
        <div role="status" className="rounded-2xl border border-emerald-800 bg-emerald-950/20 p-4 text-sm text-emerald-200">
          Blockchain query connected · {logs.filter((entry) => entry.source === 'blockchain' || entry.source === 'local_and_chain').length} on-chain record(s) matched or loaded.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <div>
          <label className="block text-sm text-aegis-muted font-semibold mb-2">Search Events</label>
          <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search actor, action, target, response, or hash" className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary" />
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
            <option value="blockchain">On-chain or TX-linked</option>
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
      {diagnosticCount > 0 && (
        <label className="flex items-center gap-2 text-sm text-slate-400">
          <input
            type="checkbox"
            checked={showDiagnostics}
            onChange={(event) => setShowDiagnostics(event.target.checked)}
            className="rounded border-slate-600 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
          />
          Show blockchain connectivity diagnostics ({diagnosticCount})
        </label>
      )}

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
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Source</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Event Type</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Actor / Activity</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Target / Result</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Hash</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Transaction / Chain ID</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                    <tr key={log.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-3 text-xs">
                      <span className={log.source === 'blockchain' ? 'text-cyan-300' : log.source === 'local_and_chain' ? 'text-emerald-300' : 'text-slate-400'}>
                        {log.source === 'blockchain' ? 'On-chain' : log.source === 'local_and_chain' ? 'Local + on-chain' : 'Local'}
                      </span>
                    </td>
                    <td className="px-6 py-3 font-semibold text-white">
                      <p>{log.event_type || 'Unknown'}</p>
                      {log.is_diagnostic && <span className="mt-1 inline-block rounded border border-amber-700/70 px-2 py-0.5 text-[10px] font-normal uppercase text-amber-300">Diagnostic test record</span>}
                    </td>
                      <td className="px-6 py-3 text-xs text-slate-300">
                        <p>{log.actor_email || (log.actor_user_id ? `User #${log.actor_user_id}` : 'Actor not recorded')}</p>
                        <p className="mt-1 text-slate-500">{log.action || log.event_type || 'Activity not recorded'}</p>
                        {(log.details?.client_ip || log.details?.user_agent) && (
                          <p className="mt-2 text-slate-400">
                            {log.details.client_ip && <span>IP {log.details.client_ip}</span>}
                            {log.details.client_ip && log.details.user_agent && <span> · </span>}
                            {log.details.user_agent && <span title={log.details.user_agent}>{log.details.user_agent}</span>}
                          </p>
                        )}
                      </td>
                      <td className="px-6 py-3 text-xs text-slate-300">
                        <p>{log.entity_type ? `${log.entity_type}${log.entity_id ? ` #${log.entity_id}` : ''}` : log.sensor_id ? `sensor #${log.sensor_id}` : 'Target not recorded'}</p>
                        <p className="mt-1 text-slate-500">{log.outcome || 'Outcome not recorded'}</p>
                        {log.details?.session_duration_seconds != null && (
                          <p className="mt-1 text-slate-400">Session duration: {log.details.session_duration_seconds}s</p>
                        )}
                        {log.source === 'blockchain' && log.actor && (
                          <p className="mt-1 text-slate-500">Chain signer: {log.actor}</p>
                        )}
                        {log.details && <details className="mt-2 max-w-xs"><summary className="cursor-pointer text-cyan-300">Response and context</summary><pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-all rounded bg-slate-950 p-2 text-[10px] text-slate-300">{JSON.stringify(log.details, null, 2)}</pre></details>}
                      </td>
                      <td className="max-w-xs break-all px-6 py-3 font-mono text-xs text-aegis-muted" title={log.data_hash || ''}>{log.data_hash || 'N/A'}</td>
                      <td className="max-w-xs break-all px-6 py-3 font-mono text-xs text-aegis-muted">
                        {log.blockchain_tx && <div title={log.blockchain_tx}><span className="mb-1 block font-sans text-[10px] uppercase text-emerald-300">Transaction hash</span>{log.blockchain_tx}</div>}
                        {(log.chain_record?.id || log.source === 'blockchain') && (
                          <div className={log.blockchain_tx ? 'mt-2' : ''} title={log.chain_record?.id || log.id.replace(/^chain:/, '')}>
                            <span className="mb-1 block font-sans text-[10px] uppercase text-cyan-300">
                              Contract log ID · {(log.chain_record || log).verified ? 'verified' : 'unverified'}
                            </span>
                            {log.chain_record?.id || log.id.replace(/^chain:/, '')}
                          </div>
                        )}
                        {!log.blockchain_tx && !log.chain_record?.id && log.source !== 'blockchain' && (
                          <span className="font-sans text-slate-500">No transaction reference recorded</span>
                        )}
                        {log.source === 'blockchain' && !log.blockchain_tx && (
                          <p className="mt-1 font-sans text-[10px] text-slate-500">Transaction hash is not stored in the contract record.</p>
                        )}
                      </td>
                    <td className="px-6 py-3 text-xs text-aegis-muted">{log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {!loadingLogs && logs.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4 text-xs text-aegis-muted">
          <span>Showing {filteredLogs.length} matching events from {logs.length} loaded.</span>
          {hasMore && <button onClick={() => fetchLogs(false)} disabled={loadingMore} className="rounded border border-slate-700 px-3 py-2 text-slate-200 hover:border-cyan-600 disabled:opacity-50">{loadingMore ? 'Loading...' : 'Load more'}</button>}
        </div>
      )}
    </div>
  );
}
