import { useEffect, useState } from 'react';
import { getSensors, observeSensorTelemetry } from '../utils/api';

export default function SensorTelemetryCard() {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [busySensorId, setBusySensorId] = useState(null);

  const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;

  const fetchSensors = async () => {
    setLoading(true);
    setMessage('');
    try {
      const sensorList = await getSensors(token);
      setSensors(Array.isArray(sensorList) ? sensorList : []);
    } catch (error) {
      console.error('Failed to fetch sensors:', error);
      setMessage('Unable to load live telemetry now.');
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (sensor) => {
    setBusySensorId(sensor.sensor_id);
    setMessage('Ingesting live telemetry into local weather flow...');
    try {
      await observeSensorTelemetry(token, sensor);
      setMessage(`Sensor ${sensor.sensor_id} ingested as weather observation.`);
      await fetchSensors();
    } catch (error) {
      console.error('Telemetry ingestion failed:', error);
      setMessage('Failed to ingest sensor telemetry.');
    } finally {
      setBusySensorId(null);
    }
  };

  useEffect(() => {
    fetchSensors();
  }, []);

  const envSensors = sensors.filter((sensor) => {
    const type = (sensor.type || '').toLowerCase();
    return type.includes('temp') || type.includes('weather') || type.includes('humidity') || type.includes('env');
  });

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-aegis-primary mb-2">Live Sensor Telemetry</h3>
          <p className="text-aegis-muted text-sm">Connected sensors feeding the local weather and energy pipelines.</p>
        </div>
        <button
          onClick={fetchSensors}
          className="rounded bg-aegis-primary px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400 transition"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p className="text-aegis-muted mt-4">Loading sensor telemetry…</p>
      ) : (
        <div className="mt-4 space-y-3">
          {sensors.length ? (
            sensors.slice(0, 5).map((sensor) => (
              <div key={sensor.sensor_id} className="rounded border border-slate-800 p-4 bg-slate-950/20">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-white">{sensor.type || 'Sensor'} / {sensor.location || 'Unknown location'}</p>
                    <p className="text-aegis-muted text-xs mt-1">Zone: {sensor.zone_id ?? 'N/A'} • Sensor ID: {sensor.sensor_id}</p>
                  </div>
                  <span className="text-xs text-slate-400">{sensor.timestamp ? new Date(sensor.timestamp).toLocaleTimeString() : 'No timestamp'}</span>
                </div>
                <div className="mt-3 flex items-center justify-between gap-3 text-sm">
                  <div>
                    <p className="text-aegis-muted text-xs">Last Reading</p>
                    <p className="text-white font-semibold">{sensor.value ?? '—'} {sensor.unit || ''}</p>
                  </div>
                  <button
                    disabled={busySensorId === sensor.sensor_id}
                    onClick={() => handleIngest(sensor)}
                    className="rounded bg-emerald-500 px-3 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400 transition disabled:cursor-not-allowed disabled:bg-slate-700"
                  >
                    {busySensorId === sensor.sensor_id ? 'Ingesting…' : 'Ingest to Weather'}
                  </button>
                </div>
              </div>
            ))
          ) : (
            <p className="text-aegis-muted mt-4">No sensors are currently reporting telemetry.</p>
          )}

          <div className="rounded border border-slate-800 bg-slate-950/10 p-3 text-sm text-slate-400">
            Showing the latest live readings from registered devices. Use a sensor with environmental data to update the weather forecast flow.
          </div>
        </div>
      )}

      {message && <p className="text-aegis-muted text-xs mt-4">{message}</p>}
      {envSensors.length > 0 && (
        <div className="mt-4 text-xs text-emerald-300">Detected {envSensors.length} environmental sensors available for forecast ingestion.</div>
      )}
    </div>
  );
}
