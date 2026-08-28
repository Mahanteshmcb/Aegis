import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import useCurrentUser from '../hooks/useCurrentUser';
import ConfirmModal from '../components/ConfirmModal';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function SensorsPage() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [sensors, setSensors] = useState([]);
  const [loadingSensors, setLoadingSensors] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [editingSensorId, setEditingSensorId] = useState(null);
  const [editSensorData, setEditSensorData] = useState({ location: '', name: '' });
  const [confirmDeleteSensorId, setConfirmDeleteSensorId] = useState(null);
  const [confirmDeleteSensorName, setConfirmDeleteSensorName] = useState('');

  useEffect(() => {
    if (!loading && user) {
      fetchSensors();
    }
  }, [user, loading]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchSensors, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  async function fetchSensors() {
    try {
      setLoadingSensors(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/sensors`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
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

  function openDeleteSensorConfirm(sensor) {
    setConfirmDeleteSensorId(sensor.id);
    setConfirmDeleteSensorName(sensor.location || sensor.name || 'this sensor');
  }

  function closeDeleteSensorConfirm() {
    setConfirmDeleteSensorId(null);
    setConfirmDeleteSensorName('');
  }

  async function handleSaveSensor(sensorId) {
    if (!sensorId) return;
    try {
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/sensors/${sensorId}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(editSensorData),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to update sensor');
      }
      console.log('Sensor updated successfully');
      setEditingSensorId(null);
      fetchSensors();
    } catch (err) {
      setError(err.message);
      console.error('Error updating sensor:', err.message);
    }
  }

  async function handleConfirmDeleteSensor() {
    if (!confirmDeleteSensorId) return;
    try {
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/sensors/${confirmDeleteSensorId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to delete sensor');
      }
      console.log('Sensor deleted successfully');
      setConfirmDeleteSensorId(null);
      setConfirmDeleteSensorName('');
      fetchSensors();
    } catch (err) {
      setError(err.message);
      console.error('Error deleting sensor:', err.message);
    }
  }

  const filteredSensors = sensors.filter((sensor) => {
    const searchText = searchTerm.toLowerCase();
    const matchesSearch = (sensor.location || '').toLowerCase().includes(searchText) ||
      (sensor.type || '').toLowerCase().includes(searchText) ||
      (sensor.id?.toString() || '').includes(searchText);
    const matchesType = filterType === 'all' || (sensor.type || '').toLowerCase() === filterType.toLowerCase();
    return matchesSearch && matchesType;
  });

  const sensorTypes = ['all', ...new Set(sensors.map((s) => s.type).filter(Boolean))];
  const onlineSensors = sensors.filter((s) => s.status !== 'offline').length;

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Sensor Fleet</h1>
          <p className="text-aegis-muted">Monitor and manage connected IoT devices.</p>
        </div>
        <button onClick={fetchSensors} className="px-5 py-3 rounded-2xl bg-aegis-primary text-white font-semibold hover:bg-sky-400 transition-all">
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Total Sensors</p>
          <p className="text-3xl font-bold text-white mt-3">{sensors.length}</p>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-green-400">Online</p>
          <p className="text-3xl font-bold text-green-400 mt-3">{onlineSensors}</p>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-red-400">Offline</p>
          <p className="text-3xl font-bold text-red-400 mt-3">{sensors.length - onlineSensors}</p>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Sensor Types</p>
          <p className="text-3xl font-bold text-white mt-3">{sensorTypes.length - 1}</p>
        </div>
      </div>

      {error && (
        <div className="rounded-3xl border border-red-700 bg-red-900/20 p-4 text-red-300">{error}</div>
      )}

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <input type="text" placeholder="Search sensors by location, type, or ID..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary" />
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary">
          {sensorTypes.map((type) => (<option key={type} value={type}>{type === 'all' ? 'All Types' : type}</option>))}
        </select>
        <label className="flex items-center gap-3 rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white cursor-pointer">
          <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-aegis-primary focus:ring-aegis-primary" />
          <span className="text-sm font-semibold">Auto-Refresh</span>
        </label>
      </div>

      <div className="rounded-3xl border border-slate-700 bg-slate-900/80 overflow-hidden">
        {loadingSensors ? (
          <div className="p-8 text-center text-aegis-muted">Loading sensors...</div>
        ) : filteredSensors.length === 0 ? (
          <div className="p-8 text-center text-aegis-muted">{sensors.length === 0 ? 'No sensors connected.' : 'No sensors match your filters.'}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 text-aegis-muted font-semibold">Sensor</th>
                  <th className="px-6 py-4 text-aegis-muted font-semibold">Type</th>
                  <th className="px-6 py-4 text-aegis-muted font-semibold">Status</th>
                  <th className="px-6 py-4 text-aegis-muted font-semibold">Last Reading</th>
                  <th className="px-6 py-4 text-aegis-muted font-semibold">Sensor ID</th>
                  <th className="px-6 py-4 text-aegis-muted font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filteredSensors.map((sensor) => (
                  <tr key={sensor.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 text-white font-medium">
                      {editingSensorId === sensor.id ? (
                        <input value={editSensorData.location} onChange={(e) => setEditSensorData({ ...editSensorData, location: e.target.value })} className="w-full rounded-md bg-slate-900 px-2 py-1 text-white border border-slate-700" />
                      ) : (
                        <div>
                          <div>{sensor.name || `Sensor ${sensor.id}`}</div>
                          <div className="text-xs text-slate-500">{sensor.location || 'Location unavailable'}</div>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-400">{sensor.type || 'Unknown'}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${sensor.status === 'offline' ? 'bg-red-900/30 text-red-400' : 'bg-green-900/30 text-green-400'}`}>
                        <span className={`h-2.5 w-2.5 rounded-full ${sensor.status === 'offline' ? 'bg-red-400' : 'bg-green-400'}`} />
                        {sensor.status === 'offline' ? 'Offline' : 'Online'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-400 text-xs">{sensor.last_reading ? new Date(sensor.last_reading).toLocaleString() : 'N/A'}</td>
                    <td className="px-6 py-4 text-slate-500 font-mono text-xs">{sensor.id}</td>
                    <td className="px-6 py-4">
                      {editingSensorId === sensor.id ? (
                        <div className="flex gap-2">
                          <button onClick={() => handleSaveSensor(sensor.id)} className="rounded-xl bg-aegis-primary px-3 py-1 text-xs text-white">Save</button>
                          <button onClick={() => setEditingSensorId(null)} className="rounded-xl border border-slate-700 px-3 py-1 text-xs text-aegis-muted">Cancel</button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button onClick={() => { setEditingSensorId(sensor.id); setEditSensorData({ location: sensor.location || '', name: sensor.name || '' }); }} className="rounded-xl border border-slate-700 px-3 py-1 text-xs text-aegis-muted hover:border-aegis-primary hover:text-aegis-primary">Edit</button>
                          <button onClick={() => openDeleteSensorConfirm(sensor)} className="rounded-xl border border-rose-700 px-3 py-1 text-xs text-rose-400 hover:bg-rose-900/20">Delete</button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {sensors.length > 0 && (
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6 text-sm text-aegis-muted">
          Showing {filteredSensors.length} of {sensors.length} sensors • {autoRefresh ? 'Auto-refresh enabled' : 'Manual refresh mode'}
        </div>
      )}
      <ConfirmModal
        open={Boolean(confirmDeleteSensorId)}
        title="Confirm delete"
        message={`Delete ${confirmDeleteSensorName} and remove its sensor record? This action cannot be undone.`}
        confirmLabel="Delete Sensor"
        loading={false}
        onConfirm={handleConfirmDeleteSensor}
        onCancel={closeDeleteSensorConfirm}
      />
    </div>
  );
}
