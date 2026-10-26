import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function AiPage() {
  const { user, token, loading } = useCurrentUser();
  const [recommendations, setRecommendations] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchRecommendations = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/v1/digital-twin/health`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to load digital-twin recommendations.');
      setRecommendations(result);
      setLastUpdated(new Date());
    } catch (loadError) {
      setError(loadError.message || 'Unable to load digital-twin recommendations.');
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) fetchRecommendations();
  }, [loading, user, fetchRecommendations]);

  if (loading) {
    return <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center text-aegis-muted">Loading AI workspace...</div>;
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Vryndara AI</h1>
        <p className="text-aegis-muted max-w-2xl">Recommendations derived from the tenant digital-twin device state.</p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <p className="text-sm text-slate-400">
          {recommendations ? `${recommendations.devices} devices · ${recommendations.online} online · ${recommendations.alerts} active alerts` : 'Waiting for digital-twin data'}
          {lastUpdated ? ` · Updated ${lastUpdated.toLocaleTimeString()}` : ''}
        </p>
        <button onClick={fetchRecommendations} disabled={isLoading || loading} className="rounded border border-cyan-700 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-950 disabled:opacity-50">
          {isLoading ? 'Refreshing...' : 'Refresh recommendations'}
        </button>
      </div>

      {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-4 text-sm text-red-200">{error}</div>}
      {isLoading && !recommendations && <p className="py-8 text-center text-slate-400">Loading current recommendations...</p>}

      {recommendations && (
        <>
          {recommendations.workflow?.summary && <p className="max-w-4xl text-slate-300">{recommendations.workflow.summary}</p>}
          <div className="space-y-8">
            {[
              ['Predictive maintenance', recommendations.recommendations],
              ['Optimization', recommendations.optimization],
              ['Adaptation', recommendations.adaptation],
            ].map(([title, items]) => (
              <section key={title} className="space-y-3">
                <div className="flex items-baseline justify-between border-b border-slate-800 pb-2">
                  <h2 className="text-lg font-semibold text-white">{title}</h2>
                  <span className="text-xs text-slate-500">{Array.isArray(items) ? items.length : 0} recommendations</span>
                </div>
                {Array.isArray(items) && items.length ? items.map((item, index) => (
                  <article key={`${item.focus || title}-${index}`} className="grid gap-2 border-b border-slate-800/70 py-3 sm:grid-cols-[10rem_minmax(0,1fr)_8rem]">
                    <div>
                      <p className="font-medium text-cyan-200">{item.focus || 'Estate'}</p>
                      <p className="text-xs text-slate-500">{item.domain || item.type || 'System'}</p>
                    </div>
                    <p className="text-sm text-slate-300">{item.message || 'No details provided.'}</p>
                    <div className="text-xs text-slate-400 sm:text-right">
                      <p className="uppercase">{item.severity || 'Unrated'}</p>
                      {Number.isFinite(Number(item.confidence)) && <p>{item.confidence}% confidence</p>}
                      {item.days_until_action != null && <p>{item.days_until_action} days</p>}
                    </div>
                  </article>
                )) : <p className="py-2 text-sm text-slate-500">No recommendations for this category.</p>}
              </section>
            ))}
          </div>
        </>
      )}

      <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6 text-sm text-aegis-muted">
        <Link href="/estate-dashboard" className="text-aegis-primary hover:text-sky-300">← Back to Estate Dashboard</Link>
      </div>
    </div>
  );
}
