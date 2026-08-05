import { useEffect, useState } from 'react';
import useCurrentUser from '../hooks/useCurrentUser';
import { getWeatherForecast, getMaintenanceRecommendations, ingestWeatherObservation } from '../utils/api';

export default function WeatherCard() {
  const { user } = useCurrentUser();
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [message, setMessage] = useState('');
  const [ingesting, setIngesting] = useState(false);

  const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;

  const fetchWeatherInfo = async () => {
    setLoading(true);
    try {
      const params = {};
      if (user?.tenant_id) params.tenant_id = user.tenant_id;
      const [forecastRes, recsRes] = await Promise.all([
        getWeatherForecast(token, params),
        getMaintenanceRecommendations(token, params),
      ]);
      setForecast(forecastRes.forecast || []);
      setRecommendations(recsRes.recommendations || []);
    } catch (error) {
      console.error('Weather fetch error', error);
      setMessage('Unable to load weather data.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateObservation = async () => {
    setIngesting(true);
    setMessage('Ingesting demo observation...');
    try {
      const now = new Date().toISOString();
      await ingestWeatherObservation(token, {
        tenant_id: user?.tenant_id || 1,
        zone_id: 1,
        temp_c: 18.5,
        humidity_percent: 75.0,
        wind_m_s: 6.2,
        precip_mm: 0.5,
        pressure_hpa: 1013.2,
        timestamp: now,
      });
      setMessage('Observation ingested. Refreshing forecast.');
      await fetchWeatherInfo();
    } catch (error) {
      console.error('Observation ingest error', error);
      setMessage('Failed to ingest weather observation.');
    } finally {
      setIngesting(false);
    }
  };

  useEffect(() => {
    fetchWeatherInfo();
  }, [user]);

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-aegis-primary mb-2">Weather Forecast</h3>
          <p className="text-aegis-muted text-sm">Local estate forecast and maintenance guidance.</p>
        </div>
        <button
          onClick={fetchWeatherInfo}
          className="rounded bg-aegis-primary px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400 transition"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p className="text-aegis-muted mt-4">Loading weather data…</p>
      ) : (
        <>
          <div className="mt-4 grid gap-4">
            <div>
              <p className="text-aegis-muted text-sm mb-2">Next forecast</p>
              <div className="grid grid-cols-1 gap-2 text-sm">
                {forecast.slice(0, 4).map((entry, idx) => (
                  <div key={idx} className="rounded border border-slate-800 p-3 bg-slate-950/20">
                    <div className="flex justify-between">
                      <span className="font-semibold">{new Date(entry.dt).toLocaleString()}</span>
                      <span className="text-aegis-muted">{entry.precip_mm?.toFixed(1)} mm</span>
                    </div>
                    <div className="mt-1 text-aegis-text text-xs">
                      {entry.temp_c?.toFixed(1)}°C • {entry.humidity_percent?.toFixed(0)}% humidity • wind {entry.wind_m_s?.toFixed(1)} m/s
                    </div>
                  </div>
                ))}
                {!forecast.length && <p className="text-aegis-muted">No forecast data available.</p>}
              </div>
            </div>

            <div>
              <p className="text-aegis-muted text-sm mb-2">Maintenance recommendations</p>
              <div className="space-y-2 text-sm">
                {recommendations.length ? (
                  recommendations.map((rec, idx) => (
                    <div key={idx} className="rounded border border-slate-800 p-3 bg-slate-950/20">
                      <p className="font-semibold">{rec.action.replace('_', ' ')}</p>
                      <p className="text-aegis-muted text-xs mt-1">When: {new Date(rec.when).toLocaleString()}</p>
                      <p className="text-aegis-muted text-xs">Reason: {rec.reason.replace('_', ' ')}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-aegis-muted">No recommendations at this time.</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      <div className="mt-6 border-t border-slate-800 pt-4">
        <button
          onClick={handleSimulateObservation}
          disabled={ingesting}
          className="inline-flex items-center rounded bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 transition"
        >
          {ingesting ? 'Simulating observation…' : 'Simulate Local Observation'}
        </button>
        {message && <p className="text-aegis-muted text-xs mt-3">{message}</p>}
      </div>
    </div>
  );
}
