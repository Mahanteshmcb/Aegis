import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import EnvironmentalDashboard from '../components/EnvironmentalDashboard';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function EnvironmentalControlPage() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [zones, setZones] = useState([]);
  const [selectedZoneId, setSelectedZoneId] = useState(null);
  const [loadingZones, setLoadingZones] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!loading) {
      fetchZones();
    }
  }, [loading]);

  async function fetchZones() {
    const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;
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
      setSelectedZoneId(zonesList[0]?.id || null);
    } catch (err) {
      console.error('Failed to fetch zones:', err);
      setError(err.message || 'Unable to load zones');
    } finally {
      setLoadingZones(false);
    }
  }

  if (loading || loadingZones) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] p-6">
        <p className="text-gray-300">Loading environmental controls...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-red-400">
        {error}
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
          No zones available. Create a zone first in the Zones section.
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

          {selectedZoneId && <EnvironmentalDashboard zoneId={selectedZoneId} />}
        </div>
      )}
    </div>
  );
}
