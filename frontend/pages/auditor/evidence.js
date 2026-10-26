import { useCallback, useEffect, useState } from 'react';
import RoleBasedRoute from '../../components/RoleBasedRoute';
import Link from 'next/link';
import useCurrentUser from '../../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function EvidenceReviewPage() {
  const { user, token, loading: userLoading } = useCurrentUser();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [blockchainAvailable, setBlockchainAvailable] = useState(false);
  const [blockchainError, setBlockchainError] = useState('');
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [verificationFilter, setVerificationFilter] = useState('all');

  const fetchEvidence = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError('');
    try {
      const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
      const [auditResponse, chainResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/audit?limit=100`, { headers }),
        fetch(`${API_URL}/api/v1/audit/blockchain?limit=100`, { headers }).catch(() => null),
      ]);
      const auditPayload = await auditResponse.json().catch(() => []);
      if (!auditResponse.ok) throw new Error(auditPayload.detail || 'Unable to load audit evidence.');
      const chainPayload = chainResponse?.ok ? await chainResponse.json().catch(() => null) : null;
      const chainQueryAvailable = Boolean(chainResponse?.ok && Array.isArray(chainPayload));
      setBlockchainAvailable(chainQueryAvailable);
      const chainFailure = chainQueryAvailable
        ? ''
        : !chainResponse
          ? 'Blockchain query could not be reached; chain verification cannot be confirmed.'
          : !chainResponse.ok
          ? `Blockchain query failed (${chainResponse.status}); chain verification cannot be confirmed.`
          : 'Blockchain query returned an invalid response; chain verification cannot be confirmed.';
      setBlockchainError(chainFailure);
      const chainByHash = new Map((chainQueryAvailable ? chainPayload : []).map((item) => [String(item.data_hash || '').toLowerCase(), item]));
      setEntries((Array.isArray(auditPayload) ? auditPayload : []).map((entry) => {
        const chainEntry = chainByHash.get(String(entry.data_hash || '').toLowerCase());
        const hasHash = Boolean(entry.data_hash);
        const chainMatched = Boolean(hasHash && chainEntry);
        const verificationState = chainMatched
          ? chainEntry.verified ? 'verified' : 'matched_unverified'
          : !hasHash ? 'missing_hash'
            : entry.blockchain_tx
              ? chainQueryAvailable ? 'not_in_query_results' : 'verification_unavailable'
              : 'not_anchored';
        return {
          ...entry,
          chain_entry: chainEntry || null,
          chain_verified: Boolean(chainEntry?.verified),
          chain_matched: chainMatched,
          verification_state: verificationState,
        };
      }));
    } catch (loadError) {
      setError(loadError.message || 'Unable to load audit evidence.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!userLoading && user) fetchEvidence();
  }, [userLoading, user, fetchEvidence]);

  const verifiedCount = entries.filter((entry) => entry.verification_state === 'verified').length;
  const filteredEntries = entries.filter((entry) => {
    const matchesFilter = verificationFilter === 'all' || entry.verification_state === verificationFilter;
    const searchable = [
      entry.event_type, entry.actor_email, entry.actor_user_id, entry.action,
      entry.entity_type, entry.entity_id, entry.outcome, entry.details,
      entry.data_hash, entry.blockchain_tx,
    ].map((value) => typeof value === 'object' ? JSON.stringify(value) : String(value ?? '')).join(' ').toLowerCase();
    return matchesFilter && (!query || searchable.includes(query.toLowerCase()));
  });
  const verificationLabels = {
    verified: 'Hash matched · chain marks verified',
    matched_unverified: 'Hash matched · not verified on chain',
    not_in_query_results: 'No hash match in returned results · inconclusive',
    verification_unavailable: 'Chain query unavailable · verification inconclusive',
    not_anchored: 'No transaction reference recorded',
    missing_hash: 'No audit hash recorded',
  };

  return (
    <RoleBasedRoute requiredRole="auditor">
      <div className="min-h-[calc(100vh-4rem)] space-y-8">
        <div>
          <Link href="/auditor/reports" className="mb-6 inline-flex items-center gap-2 text-sm text-aegis-primary hover:text-sky-300">← Back to Reports</Link>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Evidence Review</h1>
          <p className="text-aegis-muted">Review each structured audit record, its integrity hash, and whether the corresponding event appears in the chain query.</p>
        </div>

        {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-4 text-sm text-red-200">{error}</div>}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {[
            ['Loaded audit records', entries.length],
            ['Hash matched', entries.filter((entry) => entry.chain_matched).length],
            ['Marked verified', verifiedCount],
            ['Not found in query results', entries.filter((entry) => entry.verification_state === 'not_in_query_results').length],
            ['Missing hash or transaction', entries.filter((entry) => ['missing_hash', 'not_anchored'].includes(entry.verification_state)).length],
          ].map(([label, count]) => <div key={label} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-white">{count}</p>
          </div>)}
        </div>
        {!blockchainAvailable && blockchainError && <p role="status" className="rounded border border-amber-700/60 bg-amber-950/20 p-3 text-sm text-amber-200">{blockchainError} Chain-backed verification is unavailable; records with stored transaction references are marked inconclusive, not unmatched.</p>}
        {blockchainAvailable && <p role="status" className="rounded border border-amber-700/60 bg-amber-950/20 p-3 text-sm text-amber-200">This endpoint returns a limited set of recent chain records. A missing hash match means only that the record was not present in this response; it is inconclusive and is not evidence of tampering.</p>}
        <div className="flex flex-wrap items-end gap-3 border-b border-slate-800 pb-4">
          <label className="min-w-64 flex-1 text-xs text-slate-400">Search records
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Actor, action, entity, outcome, hash, transaction" className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
          </label>
          <label className="text-xs text-slate-400">Evidence status
            <select value={verificationFilter} onChange={(event) => setVerificationFilter(event.target.value)} className="mt-1 block rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
              <option value="all">All statuses</option>
              <option value="verified">Hash matched · verified</option>
              <option value="matched_unverified">Hash matched · unverified</option>
              <option value="not_in_query_results">Not found in returned results · inconclusive</option>
              <option value="verification_unavailable">Chain query unavailable</option>
              <option value="not_anchored">No transaction reference</option>
              <option value="missing_hash">Missing hash</option>
            </select>
          </label>
          <button type="button" onClick={fetchEvidence} disabled={loading} className="rounded border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-cyan-600 disabled:opacity-50">{loading ? 'Refreshing...' : 'Refresh evidence'}</button>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4 text-sm">
          <span className="text-slate-300">{filteredEntries.length} shown · {entries.length} latest database records loaded</span>
          <span className={blockchainAvailable ? 'text-emerald-300' : 'text-amber-300'}>{blockchainAvailable ? 'Blockchain query available · results may be partial' : 'Blockchain verification unavailable'}</span>
        </div>
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Audit evidence</h2>
          {loading ? (
            <p className="py-6 text-aegis-muted text-sm">Loading evidence records...</p>
          ) : filteredEntries.length > 0 ? (
            <ul className="divide-y divide-slate-800 border-y border-slate-800 text-sm text-aegis-muted">
              {filteredEntries.map((entry) => (
                <li key={entry.id} className="grid gap-2 py-4 sm:grid-cols-[12rem_minmax(0,1fr)_12rem]">
                  <div>
                    <p className="font-semibold text-white">{entry.action || entry.event_type || 'audit_event'}</p>
                    <p className="mt-1 text-xs text-cyan-200">{entry.entity_type ? `${entry.entity_type}${entry.entity_id ? ` #${entry.entity_id}` : ''}` : 'Entity not recorded'}</p>
                    <p className="mt-1 text-xs text-slate-500">{entry.created_at ? new Date(entry.created_at).toLocaleString() : 'No timestamp'}</p>
                    <p className="mt-1 text-xs text-slate-500">Record #{entry.id} · {entry.actor_email || (entry.actor_user_id ? `User #${entry.actor_user_id}` : 'Actor not recorded')}</p>
                  </div>
                  <div className="min-w-0 space-y-2">
                    <p><span className="text-slate-500">Outcome: </span><span className={/fail|denied|error|reject/i.test(entry.outcome || '') ? 'text-red-200' : 'text-slate-200'}>{entry.outcome || 'Not recorded'}</span></p>
                    <details className="rounded border border-slate-800 px-3 py-2">
                      <summary className="cursor-pointer text-xs text-cyan-200">Database audit context and hash</summary>
                      <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                        <div><dt className="text-slate-500">Actor</dt><dd className="mt-1 break-all text-slate-200">{entry.actor_email || (entry.actor_user_id ? `User #${entry.actor_user_id}` : 'Not recorded')}</dd></div>
                        <div><dt className="text-slate-500">Action</dt><dd className="mt-1 text-slate-200">{entry.action || entry.event_type || 'Not recorded'}</dd></div>
                        <div><dt className="text-slate-500">Entity</dt><dd className="mt-1 text-slate-200">{entry.entity_type ? `${entry.entity_type}${entry.entity_id ? ` #${entry.entity_id}` : ''}` : 'Not recorded'}</dd></div>
                        <div><dt className="text-slate-500">Outcome</dt><dd className="mt-1 text-slate-200">{entry.outcome || 'Not recorded'}</dd></div>
                        <div className="sm:col-span-2"><dt className="text-slate-500">SHA-256 data hash</dt><dd className="mt-1 break-all font-mono text-slate-300">{entry.data_hash || 'Not recorded'}</dd></div>
                        <div className="sm:col-span-2"><dt className="text-slate-500">Recorded database details</dt><dd className="mt-1 whitespace-pre-wrap break-all font-mono text-slate-300">{JSON.stringify(entry.details || {}, null, 2)}</dd></div>
                      </dl>
                    </details>
                    {entry.chain_entry && <details className="rounded border border-slate-800 px-3 py-2">
                      <summary className="cursor-pointer text-xs text-cyan-200">Matched blockchain event</summary>
                      <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                        <div><dt className="text-slate-500">Actor</dt><dd className="mt-1 break-all text-slate-200">{entry.chain_entry.actor || 'Not recorded'}</dd></div>
                        <div><dt className="text-slate-500">Severity</dt><dd className="mt-1 text-slate-200">{entry.chain_entry.severity ?? 'Not recorded'}</dd></div>
                        <div><dt className="text-slate-500">Chain timestamp</dt><dd className="mt-1 text-slate-200">{entry.chain_entry.timestamp ? new Date(Number(entry.chain_entry.timestamp) * 1000).toLocaleString() : 'Not recorded'}</dd></div>
                        <div><dt className="text-slate-500">Chain log index</dt><dd className="mt-1 break-all text-slate-200">{entry.chain_entry.log_index ?? entry.chain_entry.id ?? 'Not recorded'}</dd></div>
                        <div><dt className="text-slate-500">Chain event type</dt><dd className="mt-1 text-slate-200">{entry.chain_entry.event_type || 'Not recorded'}</dd></div>
                        <div><dt className="text-slate-500">Chain verification flag</dt><dd className="mt-1 text-slate-200">{entry.chain_entry.verified ? 'Verified' : 'Not verified'}</dd></div>
                        <div className="sm:col-span-2"><dt className="text-slate-500">Recorded metadata</dt><dd className="mt-1 whitespace-pre-wrap break-all font-mono text-slate-300">{typeof entry.chain_entry.metadata === 'string' ? entry.chain_entry.metadata : JSON.stringify(entry.chain_entry.metadata, null, 2)}</dd></div>
                      </dl>
                    </details>}
                    {entry.blockchain_tx && <p className="break-all font-mono text-[11px] text-slate-500">Transaction: {entry.blockchain_tx}</p>}
                  </div>
                  <div className="text-xs sm:text-right">
                    <p className={entry.verification_state === 'verified' ? 'text-emerald-300' : entry.chain_matched || ['not_in_query_results', 'verification_unavailable'].includes(entry.verification_state) ? 'text-amber-300' : 'text-slate-400'}>
                      {verificationLabels[entry.verification_state]}
                    </p>
                    {entry.blockchain_tx && <p className="mt-1 break-all text-slate-500">TX {entry.blockchain_tx}</p>}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-sm text-slate-400">{entries.length ? 'No evidence records match the current search and status filters.' : 'No audit evidence records are available for this tenant.'}</p>
          )}
        </section>
        <Link href="/audit-logs" className="inline-flex text-sm text-aegis-primary hover:text-sky-300">Open full audit history</Link>
      </div>
    </RoleBasedRoute>
  );
}
