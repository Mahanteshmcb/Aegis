import { useState, useCallback, useEffect } from 'react';
import { Loader2 } from 'lucide-react';

/**
 * Custom hook for fetching data with loading and error states
 */
export function useDataFetch(fetchFn, initialData = null, dependencies = []) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      console.error('Data fetch error:', err);
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    fetchData();
  }, dependencies);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Loading skeleton component for cards
 */
export function SkeletonCard({ variant = 'default' }) {
  return (
    <div className={`rounded-2xl border border-slate-800 p-4 ${
      variant === 'primary' ? 'bg-cyan-900/10' : 'bg-slate-900/40'
    } animate-pulse`}>
      <div className="space-y-3">
        <div className="h-4 bg-slate-700 rounded w-3/4" />
        <div className="h-8 bg-slate-700 rounded w-1/2" />
        <div className="space-y-2">
          <div className="h-3 bg-slate-700 rounded w-full" />
          <div className="h-3 bg-slate-700 rounded w-4/5" />
        </div>
      </div>
    </div>
  );
}

/**
 * Loading state component
 */
export function LoadingState({ message = 'Loading...', fullscreen = false }) {
  if (fullscreen) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="text-center">
          <Loader2 className="text-cyan-400 animate-spin mx-auto mb-4" size={32} />
          <p className="text-slate-300">{message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-8 rounded-2xl border border-slate-800 bg-slate-900/40">
      <Loader2 className="text-cyan-400 animate-spin mb-4" size={24} />
      <p className="text-slate-300 text-sm">{message}</p>
    </div>
  );
}

/**
 * Empty state component
 */
export function EmptyState({ title, description, icon: Icon, action }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-slate-800 bg-slate-900/40">
      {Icon && (
        <Icon className="text-slate-500 mb-4" size={32} />
      )}
      <h3 className="text-lg font-semibold text-slate-300 mb-2">{title}</h3>
      <p className="text-sm text-slate-400 text-center mb-6 max-w-sm">{description}</p>
      {action && (
        <button className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white font-semibold transition-colors">
          {action.label}
        </button>
      )}
    </div>
  );
}

/**
 * Error state component
 */
export function ErrorState({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 rounded-2xl border border-red-900/30 bg-red-900/5">
      <div className="w-12 h-12 rounded-full bg-red-900/20 flex items-center justify-center mb-4">
        <span className="text-red-400 text-xl">⚠</span>
      </div>
      <h3 className="text-lg font-semibold text-red-300 mb-2">Error</h3>
      <p className="text-sm text-red-200 text-center mb-4">{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors text-sm"
        >
          Try Again
        </button>
      )}
    </div>
  );
}

/**
 * Conditional render component
 */
export function ConditionalRender({ 
  loading, 
  error, 
  data, 
  onRetry, 
  children, 
  loadingComponent,
  errorComponent,
  emptyComponent 
}) {
  if (loading) {
    return loadingComponent || <LoadingState />;
  }

  if (error) {
    return errorComponent || <ErrorState error={error} onRetry={onRetry} />;
  }

  if (!data || (Array.isArray(data) && data.length === 0)) {
    return emptyComponent || null;
  }

  return children;
}

export default useDataFetch;
