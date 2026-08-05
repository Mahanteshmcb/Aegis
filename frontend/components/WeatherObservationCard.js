import { useEffect, useState } from 'react';
import useCurrentUser from '../hooks/useCurrentUser';
import { getWeatherObservations } from '../utils/api';

export default function WeatherObservationCard() {
  const { user } = useCurrentUser();
  const [loading, setLoading] = useState(true);
  const [observations, setObservations] = useState([]);
  const [message, setMessage] = useState('');

  const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;

  const fetchObservations = async () => {
    setLoading(true);
    setMessage('');
    try {
      const params = {};
      if (user?.tenant_id) params.tenant_id = user.tenant_id;
      params.limit = 10;
      const response = await getWeatherObservations(token, params);
      setObservations(response.observations || []);
    } catch (error) {
      console.error('Observation fetch error:', error);
      setMessage('Unable to load local observations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchObservations();
    }
  }, [user]);

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-aegis-primary mb-2">Local Weather Observations</h3>
          <p className="text-aegis-muted text-sm">Recent sensor-derived weather data from your estate.</p>
        </div>
        <button
          onClick={fetchObservations}
          className="rounded bg-aegis-primary px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400 transition"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p className="text-aegis-muted mt-4">Loading observations…</p>
      ) : (
        <div className="mt-4 space-y-2">
          {observations.length ? (
            observations.map((obs, idx) => (
              <div key={idx} className="rounded border border-slate-800 p-3 bg-slate-950/20">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-white">
                      {obs.timestamp ? new Date(obs.timestamp).toLocaleString() : 'Unknown time'}
                    </p>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-aegis-muted">
                      {obs.temp_c !== null && (
                        <div><span className="text-aegis-text font-semibold">{obs.temp_c.toFixed(1)}°C</span> temp</div>
                      )}
                      {obs.humidity_percent !== null && (
                        <div><span className="text-aegis-text font-semibold">{obs.humidity_percent.toFixed(0)}%</span> humidity</div>
                      )}
                      {obs.wind_m_s !== null && (
                        <div><span className="text-aegis-text font-semibold">{obs.wind_m_s.toFixed(1)} m/s</span> wind</div>
                      )}
                      {obs.precip_mm !== null && (
                        <div><span className="text-aegis-text font-semibold">{obs.precip_mm.toFixed(1)} mm</span> precip</div>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">
                    {obs.sensor_id ? `Sensor ${obs.sensor_id}` : 'Manual'}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-aegis-muted mt-4">No observations recorded yet. Ingest sensor telemetry to populate this panel.</p>
          )}
        </div>
      )}

      {message && <p className="text-aegis-muted text-xs mt-4">{message}</p>}
    </div>
  );
}
