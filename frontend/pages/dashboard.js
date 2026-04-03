import { useEffect, useState } from 'react';
import Card from '../components/Card';
import { getTenantInfo, getZones, getSensors, getAuditLogs } from '../utils/api';
import { getAuthToken } from '../utils/auth';
import { useRouter } from 'next/router';

export default function Dashboard() {
  const [tenantName, setTenantName] = useState('Aegis Operator');
  const [zones, setZones] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.push('/login');
      return;
    }

    const loadData = async () => {
      setLoading(true);
      try {
        const [tenant, zoneData, sensorData, logData] = await Promise.all([
          getTenantInfo(token),
          getZones(token),
          getSensors(token),
          getAuditLogs(token),
        ]);

        setTenantName(tenant.name || 'Aegis Operator');
        setZones(zoneData || []);
        setSensors(sensorData || []);
        setLogs(logData || []);
        setError(null);
      } catch (err) {
        if (err.message?.includes('401')) {
          localStorage.removeItem('aegis_token');
          router.push('/login');
        } else {
          setError(err.message || 'Unable to load dashboard data');
        }
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [router]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-white">Dashboard</h1>
          <p className="mt-2 text-sm text-aegis-muted">Overview of current zones, sensors, and audit activity for {tenantName}.</p>
        </div>
      </div>

      {error && (
        <div className="rounded-3xl glass-card border border-red-500/20 p-4 text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-3">
        <Card title="Active Zones">
          <div className="text-5xl font-bold text-white">{zones.length}</div>
          <p className="mt-3 text-sm text-aegis-muted">Managed zones currently instrumented.</p>
        </Card>
        <Card title="Connected Sensors">
          <div className="text-5xl font-bold text-white">{sensors.length}</div>
          <p className="mt-3 text-sm text-aegis-muted">Sensors streaming data to the platform.</p>
        </Card>
        <Card title="Recent Audit Entries">
          <div className="text-5xl font-bold text-white">{logs.length}</div>
          <p className="mt-3 text-sm text-aegis-muted">Events logged for compliance and integrity.</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Latest Zones">
          {zones.length ? (
            <ul className="space-y-3">
              {zones.slice(0, 5).map((zone) => (
                <li key={zone.id} className="rounded-2xl border border-slate-800 p-4 bg-[#0c1728]">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-white">{zone.name}</span>
                    <span className="text-xs uppercase text-aegis-primary">Active</span>
                  </div>
                  <p className="mt-2 text-sm text-aegis-muted">Zone ID: {zone.id}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-aegis-muted">No zones found yet.</p>
          )}
        </Card>

        <Card title="Latest Sensor Activity">
          {sensors.length ? (
            <ul className="space-y-3">
              {sensors.slice(0, 5).map((sensor) => (
                <li key={sensor.id} className="rounded-2xl border border-slate-800 p-4 bg-[#0c1728]">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-white">{sensor.location || 'Unknown location'}</span>
                    <span className="text-xs uppercase text-aegis-success">{sensor.type || 'Sensor'}</span>
                  </div>
                  <p className="mt-2 text-sm text-aegis-muted">Latest reading: {sensor.last_reading ?? 'N/A'}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-aegis-muted">No sensor telemetry available.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
