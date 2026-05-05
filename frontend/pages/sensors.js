import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Sidebar from '../components/Sidebar';
import ProtectedRoute from '../components/ProtectedRoute';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

function SensorsContent() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [sensors, setSensors] = useState([]);
  const [loadingSensors, setLoadingSensors] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      fetchSensors();
    }
  }, [user, loading]);

  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchSensors();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  async function fetchSensors() {
    try {
      setLoadingSensors(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/sensors`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (resp.status === 401) {
        router.push('/login');
        return;
      }

      if (!resp.ok) {
        throw new Error('Failed to load sensors');
      }

      const data = await resp.json();
      setSensors(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Fetch sensors error:', err);
    } finally {
      setLoadingSensors(false);
    }
  }

  // Filter and search sensors
  const filteredSensors = sensors.filter((sensor) => {
    const matchesSearch = 
      (sensor.location?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (sensor.type?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (sensor.id?.toString() || '').includes(searchTerm);
    
    const matchesType = filterType === 'all' || (sensor.type?.toLowerCase() === filterType.toLowerCase());
    
    return matchesSearch && matchesType;
  });

  // Get unique sensor types
  const sensorTypes = ['all', ...new Set(sensors.map((s) => s.type).filter(Boolean))];

  // Get status summary
  const onlineSensors = sensors.filter((s) => s.status !== 'offline').length;
  const offlineSensors = sensors.length - onlineSensors;

  return (
    <div className="flex min-h-screen bg-[#0b1120]">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Sensor Fleet</h1>
            <p className="text-aegis-muted">Monitor and manage connected IoT devices</p>
          </div>
          <button
            onClick={() => { setLoadingSensors(true); fetchSensors(); }}
            className="px-4 py-2 bg-aegis-primary hover:bg-aegis-primary/80 text-white rounded-lg font-semibold transition-colors"
          >
            ↻ Refresh
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-6">
            <p className="text-aegis-muted text-sm font-semibold">Total Sensors</p>
            <p className="text-3xl font-bold text-white mt-2">{sensors.length}</p>
          </div>
          <div className="bg-gradient-to-br from-green-900/30 to-slate-900 border border-green-700/50 rounded-lg p-6">
            <p className="text-green-400 text-sm font-semibold">Online</p>
            <p className="text-3xl font-bold text-green-400 mt-2">{onlineSensors}</p>
          </div>
          <div className="bg-gradient-to-br from-red-900/30 to-slate-900 border border-red-700/50 rounded-lg p-6">
            <p className="text-red-400 text-sm font-semibold">Offline</p>
            <p className="text-3xl font-bold text-red-400 mt-2">{offlineSensors}</p>
          </div>
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-6">
            <p className="text-aegis-muted text-sm font-semibold">Sensor Types</p>
            <p className="text-3xl font-bold text-white mt-2">{sensorTypes.length - 1}</p>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Search and Filter Bar */}
        <div className="mb-6 flex flex-col md:flex-row gap-4">
          <input
            type="text"
            placeholder="Search sensors by location, type, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none transition-colors"
          />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:border-aegis-primary focus:outline-none min-w-[180px] transition-colors"
          >
            {sensorTypes.map((type) => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:border-aegis-primary transition-colors">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-white text-sm font-semibold whitespace-nowrap">Auto-Refresh</span>
          </label>
        </div>

        {/* Sensors Table */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
          {loadingSensors ? (
            <div className="p-8 text-center text-aegis-muted">Loading sensors...</div>
          ) : filteredSensors.length === 0 ? (
            <div className="p-8 text-center text-aegis-muted">
              {sensors.length === 0 ? 'No sensors connected.' : 'No sensors match your filters.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-800 border-b border-slate-700">
                  <tr>
                    <th className="px-6 py-4 text-left text-aegis-muted font-semibold">Location</th>
                    <th className="px-6 py-4 text-left text-aegis-muted font-semibold">Type</th>
                    <th className="px-6 py-4 text-left text-aegis-muted font-semibold">Status</th>
                    <th className="px-6 py-4 text-left text-aegis-muted font-semibold">Last Reading</th>
                    <th className="px-6 py-4 text-left text-aegis-muted font-semibold">Sensor ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {filteredSensors.map((sensor) => (
                    <tr
                      key={sensor.id}
                      className="hover:bg-slate-800/50 transition-colors cursor-pointer"
                    >
                      <td className="px-6 py-4 text-white font-medium">
                        {sensor.location || 'Unnamed Sensor'}
                      </td>
                      <td className="px-6 py-4 text-slate-400">
                        <span className="px-3 py-1 bg-slate-700 rounded-full text-xs font-semibold">
                          {sensor.type || 'Unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1 w-fit ${
                            sensor.status === 'online' || sensor.status !== 'offline'
                              ? 'bg-green-900/30 text-green-400'
                              : 'bg-red-900/30 text-red-400'
                          }`}
                        >
                          <span className={`w-2 h-2 rounded-full ${sensor.status === 'online' || sensor.status !== 'offline' ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></span>
                          {sensor.status === 'online' || sensor.status !== 'offline' ? 'Online' : 'Offline'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-400 text-xs">
                        {sensor.last_reading ? new Date(sensor.last_reading).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-slate-500 font-mono text-xs">
                        {sensor.id}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Summary */}
        {!loadingSensors && sensors.length > 0 && (
          <div className="mt-6 p-4 bg-slate-900/50 border border-slate-800 rounded-lg text-sm text-aegis-muted">
            Showing {filteredSensors.length} of {sensors.length} sensors • {autoRefresh && <span className="text-green-400">🔄 Auto-refreshing every 5s</span>}
          </div>
        )}
      </main>
    </div>
  );
}

export default function SensorsPage() {
  return (
    <ProtectedRoute>
      <SensorsContent />
    </ProtectedRoute>
  );
}
