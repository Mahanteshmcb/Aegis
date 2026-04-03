import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Card from '../components/Card';
import { getSensors } from '../utils/api';
import { getAuthToken } from '../utils/auth';

export default function Sensors() {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.push('/login');
      return;
    }

    const loadSensors = async () => {
      setLoading(true);
      try {
        const data = await getSensors(token);
        setSensors(data || []);
        setError(null);
      } catch (err) {
        if (err.message?.includes('401')) {
          localStorage.removeItem('aegis_token');
          router.push('/login');
        } else {
          setError(err.message || 'Unable to load sensors');
        }
      } finally {
        setLoading(false);
      }
    };

    loadSensors();
  }, [router]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-white">Sensors</h1>
        <p className="mt-2 text-sm text-aegis-muted">View the latest sensor fleet telemetry and node health.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Sensor Count">
          <div className="text-5xl font-bold text-white">{sensors.length}</div>
          <p className="mt-2 text-sm text-aegis-muted">Total connected devices.</p>
        </Card>
        <Card title="Status Overview">
          <div className="text-sm text-aegis-muted">Real-time status and connectivity health will appear here.</div>
        </Card>
      </div>

      <Card title="Sensor Fleet">
        {loading ? (
          <p className="text-sm text-aegis-muted">Loading sensors...</p>
        ) : error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : sensors.length ? (
          <div className="space-y-4">
            {sensors.map((sensor) => (
              <div key={sensor.id} className="glass-card border border-slate-800 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{sensor.location || 'Unnamed Sensor'}</h3>
                    <p className="text-sm text-aegis-muted">Type: {sensor.type || 'Unknown'}</p>
                  </div>
                  <span className="text-sm text-aegis-success">Online</span>
                </div>
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  <div className="rounded-2xl bg-[#0a1220] p-3">
                    <div className="text-xs uppercase text-aegis-muted">Last Reading</div>
                    <div className="mt-2 text-white font-semibold">{sensor.last_reading ?? 'N/A'}</div>
                  </div>
                  <div className="rounded-2xl bg-[#0a1220] p-3">
                    <div className="text-xs uppercase text-aegis-muted">Sensor ID</div>
                    <div className="mt-2 text-white font-semibold">{sensor.id}</div>
                  </div>
                  <div className="rounded-2xl bg-[#0a1220] p-3">
                    <div className="text-xs uppercase text-aegis-muted">Tenant</div>
                    <div className="mt-2 text-white font-semibold">{sensor.tenant_id}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-aegis-muted">No sensors registered yet.</p>
        )}
      </Card>
    </div>
  );
}
