import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function CommunicationChannels() {
  const { user, loading } = useCurrentUser();
  const [channels, setChannels] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    type: 'mqtt',
    status: 'active',
    endpoint: '',
  });

  useEffect(() => {
    if (!loading && user) {
      fetchChannels();
    }
  }, [user, loading]);

  const fetchChannels = async () => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/communication/channels`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = res.ok ? await res.json() : [];
      setChannels(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching channels:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/communication/channels`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const channel = await res.json();
        setChannels([...channels, channel]);
        setFormData({ name: '', type: 'mqtt', status: 'active', endpoint: '' });
        setShowForm(false);
      }
    } catch (err) {
      console.error('Error saving channel:', err);
    }
  };

  const typeColors = {
    mqtt: 'text-cyan-400',
    rest: 'text-green-400',
    websocket: 'text-blue-400',
    grpc: 'text-purple-400',
  };

  const statusColors = {
    active: 'text-green-400',
    inactive: 'text-gray-400',
    error: 'text-red-400',
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
          className="px-6 py-3 bg-gradient-to-r from-teal-600 to-cyan-600 text-white rounded-lg hover:from-teal-500 hover:to-cyan-500 transition-all font-mono text-sm font-bold"
        >
          {showForm ? '✕ Cancel' : '+ Add Channel'}
        </button>
      </div>

      {showForm && (
        <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
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
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              >
                <option value="mqtt">MQTT</option>
                <option value="rest">REST</option>
                <option value="websocket">WebSocket</option>
                <option value="grpc">gRPC</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Endpoint</label>
              <input
                type="text"
                value={formData.endpoint}
                onChange={(e) => setFormData({ ...formData, endpoint: e.target.value })}
                placeholder="mqtt://broker.example.com:1883"
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="col-span-1 md:col-span-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
            >
              Create Channel
            </button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {channels.map((ch) => (
          <div key={ch.id} className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-bold text-aegis-primary">{ch.name}</h3>
              <span className={`text-xs font-bold ${statusColors[ch.status] || 'text-gray-400'}`}>
                ◆ {(ch.status || 'active').toUpperCase()}
              </span>
            </div>
            <div className="space-y-2 text-xs font-mono mb-4">
              <div className="flex justify-between">
                <span className="text-aegis-muted">Type:</span>
                <span className={typeColors[ch.type] || 'text-gray-400'}>{ch.type?.toUpperCase()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-aegis-muted">Endpoint:</span>
                <span className="text-aegis-primary truncate">{ch.endpoint || 'N/A'}</span>
              </div>
            </div>
          </div>
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
