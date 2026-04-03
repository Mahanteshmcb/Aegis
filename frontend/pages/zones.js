import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Card from '../components/Card';
import { getZones } from '../utils/api';
import { getAuthToken } from '../utils/auth';

export default function Zones() {
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.push('/login');
      return;
    }

    const loadZones = async () => {
      setLoading(true);
      try {
        const data = await getZones(token);
        setZones(data || []);
        setError(null);
      } catch (err) {
        if (err.message?.includes('401')) {
          localStorage.removeItem('aegis_token');
          router.push('/login');
        } else {
          setError(err.message || 'Unable to load zones');
        }
      } finally {
        setLoading(false);
      }
    };

    loadZones();
  }, [router]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-white">Zones</h1>
        <p className="mt-2 text-sm text-aegis-muted">Configure and monitor logical asset zones for your estate.</p>
      </div>

      <Card title="Zone Summary">
        {loading ? (
          <p className="text-sm text-aegis-muted">Loading zones...</p>
        ) : error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : zones.length ? (
          <div className="grid gap-4">
            {zones.map((zone) => (
              <div key={zone.id} className="glass-card border border-slate-800 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{zone.name}</h3>
                    <p className="text-sm text-aegis-muted">Zone ID: {zone.id}</p>
                  </div>
                  <span className="rounded-full bg-aegis-primary/15 px-3 py-1 text-xs uppercase tracking-wider text-aegis-primary">Active</span>
                </div>
                <p className="mt-3 text-sm text-aegis-muted">Tenant: {zone.tenant_id}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-aegis-muted">No zones configured yet.</p>
        )}
      </Card>
    </div>
  );
}
