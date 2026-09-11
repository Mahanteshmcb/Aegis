import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, Trash2, Edit2 } from 'lucide-react';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import SensorForm from '../components/forms/SensorForm';
import Layout3D from '../components/Layout3D';
import Button3D from '../components/Button3D';
import Card3D from '../components/Card3D';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function SensorsManagement() {
  const { user, loading } = useCurrentUser();
  const estateState = useEstateState();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'temperature',
    zone_id: null,
    location: '',
  });
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!loading && user) {
      fetchSensors();
    }
  }, [user, loading]);

  const fetchSensors = async () => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/sensors`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const sensors = res.ok ? await res.json() : [];
      estateState.setSensors(sensors);
    } catch (err) {
      console.error('Error fetching sensors:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('aegis_token');
      const method = editingId ? 'PUT' : 'POST';
      const endpoint = editingId ? `/api/v1/sensors/${editingId}` : '/api/v1/sensors';

      const res = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const sensor = await res.json();
        if (editingId) {
          estateState.updateSensor(editingId, sensor);
        } else {
          estateState.addSensor(sensor);
        }
        resetForm();
      }
    } catch (err) {
      console.error('Error saving sensor:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this sensor?')) return;

    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/sensors/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        estateState.deleteSensor(id);
      }
    } catch (err) {
      console.error('Error deleting sensor:', err);
    }
  };

  const handleEdit = (sensor) => {
    setFormData({
      name: sensor.name || '',
      type: sensor.type || 'temperature',
      zone_id: sensor.zone_id || null,
      location: sensor.location || '',
    });
    setEditingId(sensor.id);
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({ name: '', type: 'temperature', zone_id: null, location: '' });
    setEditingId(null);
    setShowForm(false);
  };

  const filteredSensors = estateState.sensors.filter((s) =>
    s.name?.toLowerCase().includes(search.toLowerCase()) ||
    s.type?.toLowerCase().includes(search.toLowerCase())
  );

  const typeIcons = {
    temperature: '🌡️',
    humidity: '💧',
    pressure: '🎯',
    motion: '👁️',
    light: '💡',
  };

  if (loading) {
    return <Layout3D title="SENSOR MANAGEMENT" icon="📡" subtitle="Loading sensor network...">
      <div className="flex items-center justify-center h-96">
        <div className="text-aegis-muted animate-pulse text-lg">Connecting to sensor grid...</div>
      </div>
    </Layout3D>;
  }

  return (
    <Layout3D
      title="SENSOR MANAGEMENT"
      icon="📡"
      subtitle="Monitor environmental sensors across all zones"
    >
      <div className="space-y-8">
        {/* Controls */}
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-3 text-aegis-muted" size={20} />
            <input
              type="text"
              placeholder="Search sensors..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-black/50 border border-green-500/30 hover:border-green-500/60 rounded-lg text-white placeholder-aegis-muted text-sm focus:border-green-400 focus:outline-none transition-all"
            />
          </div>
          <Button3D
            variant="success"
            size="md"
            icon={showForm ? undefined : Plus}
            onClick={() => {
              showForm ? resetForm() : setShowForm(true);
            }}
          >
            {showForm ? '✕ CANCEL' : '+ ADD SENSOR'}
          </Button3D>
        </div>

        {/* Form */}
        {showForm && (
          <Card3D variant="success" glowing glowColor="#00FF00">
            <SensorForm
              formData={formData}
              setFormData={setFormData}
              zones={estateState.zones}
              editingId={editingId}
              onSubmit={handleSubmit}
              onCancel={resetForm}
            />
          </Card3D>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card3D variant="primary">
            <p className="text-3xl font-bold text-cyan-300">{estateState.sensors.length}</p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Total Sensors</p>
          </Card3D>
          <Card3D variant="success">
            <p className="text-3xl font-bold text-green-300">
              {Object.keys(typeIcons).filter(t => filteredSensors.some(s => s.type === t)).length}
            </p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Types</p>
          </Card3D>
          <Card3D variant="primary">
            <p className="text-3xl font-bold text-blue-300">
              {estateState.zones.length}
            </p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">Zones Monitored</p>
          </Card3D>
          <Card3D variant="warning">
            <p className="text-3xl font-bold text-yellow-300">✓</p>
            <p className="text-xs text-aegis-muted mt-2 uppercase tracking-wider">All Active</p>
          </Card3D>
        </div>

        {/* Sensors Grid */}
        {filteredSensors.length === 0 ? (
          <Card3D variant="default" className="text-center py-12">
            <p className="text-aegis-muted text-lg">No sensors found</p>
          </Card3D>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSensors.map((sensor) => (
              <Card3D key={sensor.id} variant="success" glowing glowColor="#00FF00">
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <p className="text-3xl">{typeIcons[sensor.type] || '📡'}</p>
                    <span className="px-2 py-1 bg-green-600/30 text-green-300 text-xs rounded font-bold">
                      ACTIVE
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white">
                    {sensor.name || `Sensor ${sensor.id}`}
                  </h3>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-aegis-muted">Type:</span>
                      <span className="text-white capitalize">{sensor.type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-aegis-muted">Location:</span>
                      <span className="text-white">{sensor.location || 'N/A'}</span>
                    </div>
                    {sensor.last_reading && (
                      <div className="flex justify-between">
                        <span className="text-aegis-muted">Reading:</span>
                        <span className="text-white font-mono text-xs">{sensor.last_reading}</span>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-4">
                    <Button3D variant="secondary" size="sm" icon={Edit2} onClick={() => handleEdit(sensor)}>
                      EDIT
                    </Button3D>
                    <Button3D variant="danger" size="sm" icon={Trash2} onClick={() => handleDelete(sensor.id)}>
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
          <Link href="/3d-scene">
            <Button3D variant="primary">🌐 3D VIEW</Button3D>
          </Link>
        </div>
      </div>
    </Layout3D>
  );
}
