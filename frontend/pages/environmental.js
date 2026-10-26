import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import EnvironmentalDashboard from '../components/EnvironmentalDashboard';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function EnvironmentalControlPage() {
  const router = useRouter();
  const { user, loading, token } = useCurrentUser();
  const [zones, setZones] = useState([]);
  const [selectedZoneId, setSelectedZoneId] = useState(null);
  const [loadingZones, setLoadingZones] = useState(true);
  const [error, setError] = useState(null);

  const fetchZones = useCallback(async () => {
    if (!token) {
      router.push('/login');
      return;
    }

    setLoadingZones(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/zones`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        router.push('/login');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to load zones');
      }

      const data = await response.json();
      const zonesList = Array.isArray(data) ? data : data?.zones ?? [];
      setZones(zonesList);
      setSelectedZoneId((selectedId) => zonesList.some((zone) => String(zone.id) === String(selectedId))
        ? selectedId
        : zonesList[0]?.id ?? null);
    } catch (err) {
      console.error('Failed to fetch zones:', err);
      setError(err.message || 'Unable to load zones');
    } finally {
      setLoadingZones(false);
    }
  }, [router, token]);

  useEffect(() => {
    if (!loading && token) fetchZones();
    else if (!loading && !token) router.push('/login');
  }, [loading, token, fetchZones, router]);

  if (loading || loadingZones) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] p-6">
        <p className="text-gray-300">Loading environmental controls...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="p-6 text-red-400">
        <p>{error}</p>
        <button onClick={fetchZones} disabled={loadingZones} className="mt-4 rounded border border-slate-600 px-4 py-2 text-sm text-white disabled:opacity-50">
          {loadingZones ? 'Retrying...' : 'Retry'}
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Climate Control</h1>
          <p className="text-aegis-muted">Monitor air quality and HVAC settings for your zones.</p>
        </div>
      </div>

      {zones.length === 0 ? (
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8 text-center text-aegis-muted">
          <p>No zones available for environmental monitoring.</p>
          <button onClick={fetchZones} className="mt-4 rounded border border-slate-600 px-4 py-2 text-sm text-white disabled:opacity-50" disabled={loadingZones}>
            {loadingZones ? 'Refreshing...' : 'Retry'}
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
            <label className="block text-sm font-medium text-aegis-muted mb-2">Select Zone</label>
            <select
              value={selectedZoneId || ''}
              onChange={(e) => setSelectedZoneId(parseInt(e.target.value, 10))}
              className="w-full md:w-72 rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white focus:border-aegis-primary outline-none"
            >
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.name}
                </option>
              ))}
            </select>
          </div>

          {selectedZoneId && <EnvironmentalDashboard zoneId={selectedZoneId} token={token} />}
        </div>
      )}
    </div>
  );
}
