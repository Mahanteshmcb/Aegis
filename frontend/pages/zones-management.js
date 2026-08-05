import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import ZoneForm from '../components/forms/ZoneForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function ZonesManagement() {
  const { user, loading } = useCurrentUser();
  const estateState = useEstateState();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    location: '',
    type: 'greenhouse',
  });
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!loading && user) {
      fetchZones();
    }
  }, [user, loading]);

  const fetchZones = async () => {
    try {
      estateState.setLoading(true);
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/zones`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const zones = res.ok ? await res.json() : [];

      const zonesWithPositions = (Array.isArray(zones) ? zones : []).map((z, i) => ({
        ...z,
        position: [-5 + (i % 2) * 10, 0, 5 - Math.floor(i / 2) * 10],
        size: [3, 3, 3],
        color: ['#0088ff', '#00ffaa', '#88ff00', '#ff8800', '#ffaa00'][i % 5],
      }));

      estateState.setZones(zonesWithPositions);
      estateState.setLoading(false);
    } catch (err) {
      console.error('Error fetching zones:', err);
      estateState.setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('aegis_token');
      const method = editingId ? 'PUT' : 'POST';
      const endpoint = editingId ? `/api/v1/zones/${editingId}` : '/api/v1/zones';

      const res = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const zone = await res.json();
        if (editingId) {
          estateState.updateZone(editingId, zone);
        } else {
          estateState.addZone(zone);
        }
        setFormData({ name: '', description: '', type: 'work', status: 'active' });
        setEditingId(null);
        setShowForm(false);
      }
    } catch (err) {
      console.error('Error saving zone:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this zone?')) return;

    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/zones/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        estateState.deleteZone(id);
      }
    } catch (err) {
      console.error('Error deleting zone:', err);
    }
  };

  const handleEdit = (zone) => {
    setFormData({
      name: zone.name || '',
      description: zone.description || '',
      location: zone.location || '',
      type: zone.type || 'greenhouse',
    });
    setEditingId(zone.id);
    setShowForm(true);
  };

  const filteredZones = estateState.zones.filter((z) =>
    z.name?.toLowerCase().includes(search.toLowerCase()) ||
    z.description?.toLowerCase().includes(search.toLowerCase())
  );

  const typeColors = {
    work: 'text-cyan-400',
    storage: 'text-yellow-400',
    environmental: 'text-green-400',
    emergency: 'text-red-400',
    maintenance: 'text-orange-400',
  };

  const statusColors = {
    active: 'text-green-400',
    maintenance: 'text-yellow-400',
    restricted: 'text-red-400',
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="text-aegis-muted animate-pulse">Loading...</div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">
            📍 ZONE MANAGEMENT
          </h1>
          <p className="text-aegis-muted">Manage your estate zones and areas</p>
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingId(null);
            setFormData({ name: '', description: '', location: '', type: 'greenhouse' });
          }}
          className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-lg hover:from-cyan-500 hover:to-blue-500 transition-all font-mono text-sm font-bold"
        >
          {showForm ? '✕ Cancel' : '+ Add Zone'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <ZoneForm
          formData={formData}
          setFormData={setFormData}
          editingId={editingId}
          onSubmit={handleSubmit}
          onCancel={() => {
            setShowForm(false);
            setEditingId(null);
            setFormData({ name: '', description: '', location: '', type: 'greenhouse' });
          }}
        />
      )}

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search zones by name or description..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
        />
      </div>

      {/* Zones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredZones.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <p className="text-aegis-muted text-lg">No zones found. Create one to get started.</p>
          </div>
        ) : (
          filteredZones.map((zone) => (
            <div
              key={zone.id}
              className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 hover:border-aegis-primary/60 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-bold text-aegis-primary">{zone.name || `Zone ${zone.id}`}</h3>
                <span className={`text-xs font-bold ${statusColors[zone.status] || 'text-gray-400'}`}>
                  ◆ {(zone.status || 'active').toUpperCase()}
                </span>
              </div>

              {zone.description && (
                <p className="text-xs text-aegis-muted mb-3">{zone.description}</p>
              )}

              <div className="space-y-2 mb-4 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-aegis-muted">Type:</span>
                  <span className={typeColors[zone.type] || 'text-gray-400'}>
                    {(zone.type || 'unknown').toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-aegis-muted">Area:</span>
                  <span className="text-aegis-primary">3m × 3m × 3m</span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(zone)}
                  className="flex-1 px-3 py-2 bg-blue-600 text-white text-xs rounded hover:bg-blue-500 transition-all font-bold"
                >
                  ✎ Edit
                </button>
                <button
                  onClick={() => handleDelete(zone.id)}
                  className="flex-1 px-3 py-2 bg-red-600 text-white text-xs rounded hover:bg-red-500 transition-all font-bold"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Back Button */}
      <div className="mt-8">
        <Link href="/dashboard" className="text-aegis-primary hover:text-aegis-primary/80 transition-colors">
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
