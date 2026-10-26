import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function CommunicationChannels() {
  const { user, token, loading } = useCurrentUser();
  const [channels, setChannels] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loadingChannels, setLoadingChannels] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncingId, setSyncingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    type: 'mqtt',
    meshTopology: 'star',
  });

  const fetchChannels = useCallback(async () => {
    if (!token) return;
    try {
      setLoadingChannels(true);
      const res = await fetch(`${API_URL}/api/v1/communication/devices/channels`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json().catch(() => []);
      if (!res.ok) throw new Error(data.detail || 'Unable to load communication channels.');
      setChannels(Array.isArray(data) ? data : []);
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to load communication channels.');
    } finally {
      setLoadingChannels(false);
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) fetchChannels();
  }, [user, loading, fetchChannels]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (!formData.name.trim()) return setError('Channel name is required.');
      setSaving(true);
      setError('');
      const res = await fetch(`${API_URL}/api/v1/communication/devices/channels`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          channel_name: formData.name.trim(),
          protocol: formData.type,
          device_ids: [],
          mesh_topology: formData.meshTopology,
        }),
      });
      const result = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(result.detail || 'Unable to create channel.');
      setFormData({ name: '', type: 'mqtt', meshTopology: 'star' });
      setShowForm(false);
      setSuccess('Communication channel created.');
      await fetchChannels();
    } catch (err) {
      setError(err.message || 'Unable to create channel.');
    } finally {
      setSaving(false);
    }
  };

  const syncChannel = async (channelId) => {
    setSyncingId(channelId);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/v1/communication/devices/channels/${channelId}/sync`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Channel sync failed.');
      setSuccess('Channel synchronized.');
      await fetchChannels();
    } catch (syncError) {
      setError(syncError.message || 'Channel sync failed.');
    } finally {
      setSyncingId(null);
    }
  };

  const typeColors = {
    mqtt: 'text-cyan-300',
    rest: 'text-emerald-300',
    websocket: 'text-sky-300',
    grpc: 'text-amber-300',
  };

  if (loading) {
    return <div className="text-aegis-muted animate-pulse">Loading...</div>;
  }

  return (
    <div className="w-full">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">
            📡 COMMUNICATION CHANNELS
          </h1>
          <p className="text-aegis-muted">Configure and monitor communication channels</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-6 py-3 br-linear-to-r from-teal-600 to-cyan-600 text-white rounded-lg hover:from-teal-500 hover:to-cyan-500 transition-all font-mono text-sm font-bold"
        >
          {showForm ? 'Cancel' : 'Add channel'}
        </button>
      </div>
      {error && <div role="alert" className="mb-4 rounded border border-red-700 bg-red-900/20 p-4 text-sm text-red-200">{error}</div>}
      {success && <div role="status" className="mb-4 rounded border border-emerald-700 bg-emerald-900/20 p-4 text-sm text-emerald-200">{success}</div>}

      {showForm && (
        <div className="br-linear-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Channel Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Protocol</label>
              <select value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })} className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm">
                <option value="mqtt">MQTT</option>
                <option value="rest">REST</option>
                <option value="websocket">WebSocket</option>
                <option value="grpc">gRPC</option>
              </select>
            </div>
            <div className="col-span-1 md:col-span-2">
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Mesh topology</label>
              <select value={formData.meshTopology} onChange={(e) => setFormData({ ...formData, meshTopology: e.target.value })} className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm">
                <option value="star">Star</option>
                <option value="mesh">Mesh</option>
                <option value="bus">Bus</option>
                <option value="tree">Tree</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={saving}
              className="col-span-1 md:col-span-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
            >
              {saving ? 'Creating...' : 'Create channel'}
            </button>
          </form>
        </div>
      )}

      <div className="divide-y divide-slate-800 border-y border-slate-800">
        {loadingChannels ? <p className="py-8 text-center text-slate-400">Loading channels...</p> : channels.length === 0 ? (
          <p className="py-8 text-center text-slate-400">No communication channels registered for this tenant.</p>
        ) : channels.map((channel) => (
          <article key={channel.id} className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <h2 className="font-semibold text-white">{channel.channel_name || `Channel ${channel.id}`}</h2>
              <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-400">
                <span className={typeColors[String(channel.protocol || '').toLowerCase()] || 'text-slate-300'}>{channel.protocol || 'Protocol unknown'}</span>
                <span className={channel.status === 'connected' ? 'text-emerald-300' : 'text-amber-300'}>{channel.status || 'Status unknown'}</span>
                <span>{channel.active_devices ?? 0} active devices</span>
                <span>{channel.latency_ms ?? '—'} ms latency</span>
                <span>{channel.signal_strength ?? '—'}% signal</span>
                <span>Topology: {channel.mesh_topology || 'unknown'}</span>
              </div>
            </div>
            <button onClick={() => syncChannel(channel.id)} disabled={syncingId === channel.id} className="w-fit rounded border border-cyan-700 px-3 py-2 text-xs text-cyan-200 hover:bg-cyan-950 disabled:opacity-50">
              {syncingId === channel.id ? 'Syncing...' : 'Sync'}
            </button>
          </article>
        ))}
      </div>

      <div className="mt-8">
        <Link href="/estate-dashboard" className="text-aegis-primary hover:text-aegis-primary/80 transition-colors">
          ← Back to Estate Dashboard
        </Link>
      </div>
    </div>
  );
}
