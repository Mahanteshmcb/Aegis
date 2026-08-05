import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, Trash2, Edit2 } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import ZoneForm from '../components/forms/ZoneForm';
import Layout3D from '../components/Layout3D';
import Button3D from '../components/Button3D';
import Card3D from '../components/Card3D';

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
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/zones`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const zones = res.ok ? await res.json() : [];
      estateState.setZones(zones);
    } catch (err) {
      console.error('Error fetching zones:', err);
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
        resetForm();
      }
    } catch (err) {
      console.error('Error saving zone:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this zone?')) return;

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

  const resetForm = () => {
    setFormData({ name: '', description: '', location: '', type: 'greenhouse' });
    setEditingId(null);
    setShowForm(false);
  };

  const filteredZones = estateState.zones.filter((z) =>
    z.name?.toLowerCase().includes(search.toLowerCase()) ||
    z.type?.toLowerCase().includes(search.toLowerCase())
  );

  const typeIcons = {
    greenhouse: '🌱',
    laboratory: '🔬',
    storage: '📦',
    quarters: '🏠',
    common: '🏛️',
  };

  const typeColors = {
    greenhouse: 'from-green-600 to-emerald-600',
    laboratory: 'from-purple-600 to-blue-600',
    storage: 'from-yellow-600 to-orange-600',
    quarters: 'from-pink-600 to-rose-600',
    common: 'from-indigo-600 to-blue-600',
  };

  if (loading) {
    return (
      <Layout3D title="ZONE MANAGEMENT" icon="📍" subtitle="Loading zone configuration...">
        <div className="flex items-center justify-center h-96">
          <div className="text-aegis-muted animate-pulse text-lg">Mapping secure zones...</div>
        </div>
      </Layout3D>
    );
  }

  return (
    <Layout3D
      title="ZONE MANAGEMENT"
      icon="📍"
      subtitle="Create and manage estate security zones"
    >
      <div className="space-y-8">
        {/* Controls */}
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-3 text-aegis-muted" size={20} />
            <input
              type="text"
              placeholder="Search zones..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-black/50 border border-purple-500/30 hover:border-purple-500/60 rounded-lg text-white placeholder-aegis-muted text-sm focus:border-purple-400 focus:outline-none transition-all"
            />
          </div>
          <Button3D
            variant="secondary"
            size="md"
            icon={showForm ? undefined : Plus}
            onClick={() => {
              showForm ? resetForm() : setShowForm(true);
            }}
          >
            {showForm ? '✕ CANCEL' : '+ ADD ZONE'}
          </Button3D>
        </div>

        {/* Form */}
        {showForm && (
          <Card3D variant="purple" glowing glowColor="#FF1493">
            <ZoneForm
              formData={formData}
              setFormData={setFormData}
              editingId={editingId}
              onSubmit={handleSubmit}
              onCancel={resetForm}
            />
          </Card3D>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card3D variant="primary">
            <p className="text-3xl font-bold text-cyan-300">{estateState.zones.length}</p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Total Zones</p>
          </Card3D>
          <Card3D variant="success">
            <p className="text-3xl font-bold text-green-300">{filteredZones.length}</p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Visible</p>
          </Card3D>
          <Card3D variant="warning">
            <p className="text-3xl font-bold text-yellow-300">100%</p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Coverage</p>
          </Card3D>
          <Card3D variant="danger">
            <p className="text-3xl font-bold text-red-300">0</p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Breaches</p>
          </Card3D>
        </div>

        {/* Zones Grid */}
        {filteredZones.length === 0 ? (
          <Card3D variant="default" className="text-center py-12">
            <p className="text-aegis-muted text-lg">No zones found</p>
            <p className="text-xs text-aegis-muted mt-2">Create a new zone to start</p>
          </Card3D>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredZones.map((zone) => (
              <Card3D
                key={zone.id}
                variant="purple"
                glowing
                glowColor={
                  zone.type === 'greenhouse'
                    ? '#00FF00'
                    : zone.type === 'laboratory'
                    ? '#9900FF'
                    : zone.type === 'storage'
                    ? '#FFD700'
                    : zone.type === 'quarters'
                    ? '#FF69B4'
                    : '#4169E1'
                }
              >
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <p className="text-3xl">{typeIcons[zone.type] || '📍'}</p>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${typeColors[zone.type] || typeColors.common}`}
                    >
                      {(zone.type || 'common').toUpperCase()}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white">{zone.name || `Zone ${zone.id}`}</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-aegis-muted">Location:</span>
                      <span className="text-white">{zone.location || 'N/A'}</span>
                    </div>
                    {zone.description && (
                      <div>
                        <p className="text-aegis-muted text-xs mb-1">Description:</p>
                        <p className="text-white text-xs line-clamp-2">{zone.description}</p>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-4">
                    <Button3D variant="secondary" size="sm" icon={Edit2} onClick={() => handleEdit(zone)}>
                      EDIT
                    </Button3D>
                    <Button3D variant="danger" size="sm" icon={Trash2} onClick={() => handleDelete(zone.id)}>
                      DELETE
                    </Button3D>
                  </div>
                </div>
              </Card3D>
            ))}
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-4 pt-8">
          <Link href="/dashboard">
            <Button3D variant="ghost">← BACK</Button3D>
          </Link>
          <Link href="/dashboard-3d">
            <Button3D variant="primary">🌐 3D VIEW</Button3D>
          </Link>
        </div>
      </div>
    </Layout3D>
  );
}
