import { useCallback, useEffect, useMemo, useState } from 'react';
import RoleBasedRoute from '../../components/RoleBasedRoute';
import Link from 'next/link';
import useCurrentUser from '../../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function AuditorReportsPage() {
  const { user, token, loading: userLoading } = useCurrentUser();
  const [logs, setLogs] = useState([]);
  const [chainSummary, setChainSummary] = useState(null);
  const [databaseSummary, setDatabaseSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [chainError, setChainError] = useState('');
  const [reportDays, setReportDays] = useState('7');
  const [updatedAt, setUpdatedAt] = useState(null);

  const fetchReports = useCallback(async (background = false) => {
    if (!token || !user?.tenant_id) return;
    if (!background) setLoading(true);
    setError('');
    try {
      const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
      const [auditResponse, complianceResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/audit?limit=100`, { headers }),
        fetch(`${API_URL}/api/v1/audit/compliance/${user.tenant_id}`, { headers }).catch(() => null),
      ]);
      const auditPayload = await auditResponse.json().catch(() => []);
      if (!auditResponse.ok) throw new Error(auditPayload.detail || 'Unable to load tenant audit records.');
      const compliancePayload = complianceResponse?.ok ? await complianceResponse.json().catch(() => null) : null;
      setLogs(Array.isArray(auditPayload) ? auditPayload : []);
      const summary = compliancePayload?.compliance_summary;
      const usableSummary = summary && typeof summary === 'object' && !summary.error ? summary : null;
      setChainSummary(usableSummary);
      setDatabaseSummary(compliancePayload?.database_summary || null);
      setChainError(
        usableSummary ? '' :
          compliancePayload?.blockchain_error || summary?.error ||
          (complianceResponse ? 'Blockchain compliance summary is unavailable.' : 'Could not reach the blockchain compliance endpoint.')
      );
      setUpdatedAt(new Date());
    } catch (loadError) {
      setError(loadError.message || 'Unable to load compliance data.');
      setChainSummary(null);
      setDatabaseSummary(null);
      setChainError('Compliance data could not be loaded.');
    } finally {
      if (!background) setLoading(false);
    }
  }, [token, user?.tenant_id]);

  useEffect(() => {
    if (!userLoading && user) fetchReports();
  }, [userLoading, user, fetchReports]);

  useEffect(() => {
    if (userLoading || !user || !token) return undefined;
    const interval = window.setInterval(() => fetchReports(true), 30000);
    return () => window.clearInterval(interval);
  }, [userLoading, user, token, fetchReports]);

  const periodLogs = useMemo(() => {
    const cutoff = Date.now() - Number(reportDays) * 86400000;
    return logs.filter((item) => new Date(item.created_at || 0).getTime() >= cutoff);
  }, [logs, reportDays]);

  const summary = useMemo(() => {
    const eventCounts = periodLogs.reduce((acc, item) => {
      const key = item.action || item.event_type || 'system';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    const countBy = (getKey) => periodLogs.reduce((acc, item) => {
      const key = getKey(item);
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    const entityCounts = countBy((item) => item.entity_type || 'Unspecified');
    const outcomeCounts = countBy((item) => item.outcome || 'Unspecified');

    return {
      topEvents: Object.entries(eventCounts).sort((a, b) => b[1] - a[1]).slice(0, 8),
      topEntities: Object.entries(entityCounts).sort((a, b) => b[1] - a[1]).slice(0, 6),
      outcomes: Object.entries(outcomeCounts).sort((a, b) => b[1] - a[1]),
      withTransaction: periodLogs.filter((item) => item.blockchain_tx).length,
      missingActor: periodLogs.filter((item) => !item.actor_email && !item.actor_user_id).length,
      missingEntity: periodLogs.filter((item) => !item.entity_type || !item.entity_id).length,
      missingOutcome: periodLogs.filter((item) => !item.outcome).length,
      failures: periodLogs.filter((item) => /fail|denied|error|reject/i.test(`${item.outcome || ''} ${item.event_type || ''}`)).length,
      latestEvent: periodLogs[0] || null,
    };
  }, [periodLogs]);

  const verifiedRate = chainSummary && Number(chainSummary.total_logs) > 0
    ? Math.round((Number(chainSummary.verified_logs || 0) / Number(chainSummary.total_logs)) * 100)
    : null;
  const allTimeMetrics = [
    {
      chainLabel: 'Blockchain records · all time',
      localLabel: 'Local audit records · all time',
      chainValue: chainSummary?.total_logs,
      localValue: databaseSummary?.total_logs,
    },
    {
      chainLabel: 'Verified records · all time',
      localLabel: 'Local records with TX reference',
      chainValue: chainSummary?.verified_logs,
      localValue: databaseSummary?.transaction_references,
    },
    {
      chainLabel: 'Critical records · all time',
      localLabel: 'Critical audit events · all time',
      chainValue: chainSummary?.critical_logs,
      localValue: databaseSummary?.critical_logs,
    },
    {
      chainLabel: 'Emergency records · all time',
      localLabel: 'Emergency audit events · all time',
      chainValue: chainSummary?.emergency_logs,
      localValue: databaseSummary?.emergency_logs,
    },
  ];

  return (
    <RoleBasedRoute requiredRole="auditor">
      <div className="min-h-[calc(100vh-4rem)] space-y-8">
        <div>
          <Link href="/estate-dashboard" className="mb-6 inline-flex items-center gap-2 text-sm text-aegis-primary hover:text-sky-300">← Back to Estate Dashboard</Link>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Compliance Reports</h1>
          <p className="text-aegis-muted">Tenant audit activity and blockchain verification coverage.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">{updatedAt ? `Updated ${updatedAt.toLocaleTimeString()}` : 'Waiting for data'}</span>
          <button type="button" onClick={() => fetchReports()} disabled={loading} className="rounded border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-cyan-600 disabled:opacity-50">{loading ? 'Refreshing...' : 'Refresh'}</button>
        </div>

        {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-4 text-sm text-red-200">{error}</div>}
        {loading ? (
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8 text-aegis-muted">Loading report summary…</div>
        ) : (
          <div className="space-y-8">
            <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-800 pb-4">
              <label className="text-xs text-slate-400">Report window
                <select value={reportDays} onChange={(event) => setReportDays(event.target.value)} className="ml-3 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
                  <option value="1">Last 24 hours</option><option value="7">Last 7 days</option><option value="30">Last 30 days</option>
                </select>
              </label>
              <span className="text-xs text-slate-500">Window metrics use the latest {logs.length} database records returned by the audit API. All-time totals use the blockchain when available, otherwise local audit records.</span>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
              {allTimeMetrics.map(({ chainLabel, localLabel, chainValue, localValue }) => {
                const hasChainValue = chainValue !== undefined && chainValue !== null;
                const value = hasChainValue ? chainValue : localValue;
                return (
                <div key={hasChainValue ? chainLabel : localLabel} className="border-b border-slate-800 pb-4">
                  <p className="text-xs uppercase tracking-wider text-slate-500">{hasChainValue ? chainLabel : localLabel}</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{value !== undefined && value !== null ? value : 'Unavailable'}</p>
                </div>
              );
              })}
            </div>
            {chainError && <p role="status" className="rounded border border-amber-700/60 bg-amber-950/20 p-3 text-sm text-amber-200">On-chain summary unavailable ({chainError}). All-time figures above use local audit records; transaction references are not proof of on-chain verification.</p>}
            <div className="grid gap-6 sm:grid-cols-3">
              <div className="border-b border-slate-800 pb-4"><p className="text-xs uppercase tracking-wider text-slate-500">Database TX references</p><p className="mt-2 text-2xl font-semibold text-white">{summary.withTransaction}</p></div>
              <div className="border-b border-slate-800 pb-4"><p className="text-xs uppercase tracking-wider text-slate-500">Chain verification rate</p><p className="mt-2 text-2xl font-semibold text-white">{verifiedRate === null ? 'Unavailable' : `${verifiedRate}%`}</p></div>
              <div className="border-b border-slate-800 pb-4"><p className="text-xs uppercase tracking-wider text-slate-500">Events in window</p><p className="mt-2 text-2xl font-semibold text-white">{periodLogs.length}</p></div>
            </div>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Audit record completeness">
              {[
                ['Actor missing', summary.missingActor],
                ['Entity context missing', summary.missingEntity],
                ['Outcome missing', summary.missingOutcome],
                ['Failure or denial events', summary.failures],
              ].map(([label, value]) => <div key={label} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
                <p className={`mt-2 text-xl font-semibold ${value ? 'text-amber-200' : 'text-emerald-200'}`}>{value}</p>
              </div>)}
            </section>
            <section className="space-y-3">
              <div className="flex items-baseline justify-between border-b border-slate-800 pb-2">
                <h2 className="text-lg font-semibold text-white">Activity by action</h2>
                <span className="text-xs text-slate-500">{periodLogs.length} in selected window</span>
              </div>
              {summary.topEvents.length ? summary.topEvents.map(([event, count]) => (
                <div key={event} className="flex justify-between gap-4 border-b border-slate-800/70 py-2 text-sm">
                  <span className="text-slate-300">{event}</span>
                  <span className="font-mono text-slate-400">{count}</span>
                </div>
              )) : <p className="py-3 text-sm text-slate-400">No audit events in the loaded records.</p>}
            </section>
            <section className="grid gap-6 lg:grid-cols-2">
              <div className="space-y-3">
                <h2 className="border-b border-slate-800 pb-2 text-lg font-semibold text-white">Activity by entity</h2>
                {summary.topEntities.length ? summary.topEntities.map(([entity, count]) => <div key={entity} className="flex justify-between border-b border-slate-800/70 py-2 text-sm"><span className="text-slate-300">{entity}</span><span className="font-mono text-slate-400">{count}</span></div>) : <p className="text-sm text-slate-400">No entity activity in the selected window.</p>}
              </div>
              <div className="space-y-3">
                <h2 className="border-b border-slate-800 pb-2 text-lg font-semibold text-white">Outcomes</h2>
                {summary.outcomes.map(([outcome, count]) => <div key={outcome} className="flex justify-between border-b border-slate-800/70 py-2 text-sm"><span className="text-slate-300">{outcome}</span><span className="font-mono text-slate-400">{count}</span></div>)}
              </div>
            </section>
            <section className="space-y-3">
              <div className="flex items-baseline justify-between border-b border-slate-800 pb-2"><h2 className="text-lg font-semibold text-white">Recent activity detail</h2><Link href="/audit-logs" className="text-xs text-cyan-300 hover:text-cyan-100">Open searchable audit log</Link></div>
              {periodLogs.slice(0, 20).map((entry) => <article key={entry.id} className="grid gap-3 border-b border-slate-800/70 py-3 text-sm md:grid-cols-[minmax(0,1fr)_12rem]">
                <div className="min-w-0">
                  <p className="font-medium text-white">{entry.action || entry.event_type || 'Audit event'} <span className="font-normal text-slate-400">· {entry.entity_type ? `${entry.entity_type}${entry.entity_id ? ` #${entry.entity_id}` : ''}` : 'Entity not recorded'}</span></p>
                  <p className="mt-1 text-xs text-slate-400">{entry.actor_email || (entry.actor_user_id ? `User #${entry.actor_user_id}` : 'Actor not recorded')} · {entry.outcome || 'Outcome not recorded'} · {entry.created_at ? new Date(entry.created_at).toLocaleString() : 'No timestamp'}</p>
                  <details className="mt-2"><summary className="cursor-pointer text-xs text-cyan-300">Audit context and integrity references</summary><div className="mt-2 space-y-1 break-all rounded bg-slate-950 p-3 font-mono text-[10px] text-slate-400"><p>Record #{entry.id}</p><p>SHA-256: {entry.data_hash || 'Not recorded'}</p><p>Blockchain transaction: {entry.blockchain_tx || 'Not recorded'}</p><pre className="whitespace-pre-wrap">{JSON.stringify(entry.details || {}, null, 2)}</pre></div></details>
                </div>
                <span className={`text-xs md:text-right ${entry.blockchain_tx ? 'text-emerald-300' : 'text-slate-500'}`}>{entry.blockchain_tx ? 'Transaction reference recorded' : 'No transaction reference'}</span>
              </article>)}
            </section>
            <section className="space-y-3 border-t border-slate-800 pt-5">
              <h2 className="text-lg font-semibold text-white">Most recent event</h2>
              {summary.latestEvent ? <article className="border-l-2 border-cyan-700 pl-4">
                <p className="font-semibold text-slate-200">{summary.latestEvent.event_type || 'Unknown event'}</p>
                <p className="mt-1 text-xs text-slate-500">{summary.latestEvent.created_at ? new Date(summary.latestEvent.created_at).toLocaleString() : 'No timestamp'} · Record #{summary.latestEvent.id}</p>
                <p className="mt-2 break-all font-mono text-xs text-slate-400">{summary.latestEvent.data_hash || 'No data hash'}</p>
                <p className="mt-1 break-all font-mono text-xs text-slate-400">{summary.latestEvent.blockchain_tx ? `TX ${summary.latestEvent.blockchain_tx}` : 'No blockchain transaction reference recorded'}</p>
              </article> : <p className="text-sm text-slate-400">No audit events in this report window.</p>}
            </section>
            <Link href="/auditor/evidence" className="inline-flex text-sm text-aegis-primary hover:text-sky-300">Review chain evidence</Link>
          </div>
        )}
      </div>
    </RoleBasedRoute>
  );
}
