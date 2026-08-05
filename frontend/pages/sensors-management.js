import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';
import SensorForm from '../components/forms/SensorForm';

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
      estateState.setLoading(true);
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/sensors`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const sensors = res.ok ? await res.json() : [];

      const sensorsWithPositions = (Array.isArray(sensors) ? sensors : []).map((s, i) => ({
        ...s,
        position: [-4 + (i % 5) * 2, 2, 4 - Math.floor(i / 5) * 4],
        type: s.type || ['temperature', 'humidity', 'light', 'pressure', 'motion'][i % 5],
        value: s.value || '00',
      }));

      estateState.setSensors(sensorsWithPositions);
      estateState.setLoading(false);
    } catch (err) {
      console.error('Error fetching sensors:', err);
      estateState.setLoading(false);
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
        setFormData({
          name: '',
          type: 'temperature',
          zone: 'living-quarters',
          unit: '°C',
          min_range: 0,
          max_range: 50,
        });
        setEditingId(null);
        setShowForm(false);
      }
    } catch (err) {
      console.error('Error saving sensor:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this sensor?')) return;

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

  const filteredSensors = estateState.sensors.filter((s) =>
    s.name?.toLowerCase().includes(search.toLowerCase()) ||
    s.type?.toLowerCase().includes(search.toLowerCase())
  );

  const typeColors = {
    temperature: 'text-red-400',
    humidity: 'text-cyan-400',
    light: 'text-yellow-400',
    pressure: 'text-purple-400',
    motion: 'text-pink-400',
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
            📊 SENSOR MANAGEMENT
          </h1>
          <p className="text-aegis-muted">Manage and configure your sensor network</p>
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingId(null);
            setFormData({
              name: '',
              type: 'temperature',
              zone_id: null,
              location: '',
            });
          }}
          className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-500 hover:to-emerald-500 transition-all font-mono text-sm font-bold"
        >
          {showForm ? '✕ Cancel' : '+ Add Sensor'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <SensorForm
          formData={formData}
          setFormData={setFormData}
          editingId={editingId}
          onSubmit={handleSubmit}
          zones={estateState.zones}
          onCancel={() => {
            setShowForm(false);
            setEditingId(null);
            setFormData({
              name: '',
              type: 'temperature',
              zone_id: null,
              location: '',
            });
          }}
        />
      )}

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search sensors by name or type..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
        />
      </div>

      {/* Sensors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSensors.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <p className="text-aegis-muted text-lg">No sensors found. Create one to get started.</p>
          </div>
        ) : (
          filteredSensors.map((sensor) => (
            <div
              key={sensor.id}
              className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 hover:border-aegis-primary/60 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-bold text-aegis-primary">{sensor.name || `Sensor ${sensor.id}`}</h3>
                <span className={`text-xs font-bold ${typeColors[sensor.type] || 'text-gray-400'}`}>
                  ◆ {(sensor.type || 'unknown').toUpperCase()}
                </span>
              </div>

              <div className="space-y-2 mb-4 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-aegis-muted">Zone:</span>
                  <span className="text-aegis-primary capitalize">{sensor.zone || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-aegis-muted">Current Value:</span>
                  <span className="text-cyan-400 font-bold">{sensor.value || '--'} {sensor.unit}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-aegis-muted">Range:</span>
                  <span className="text-aegis-primary">
                    {sensor.min_range || 0} - {sensor.max_range || 100} {sensor.unit}
                  </span>
                </div>
              </div>

              {/* Value Bar */}
              <div className="w-full bg-black/50 border border-aegis-primary/20 rounded h-2 mb-4 overflow-hidden">
                <div
                  className="h-full transition-all rounded"
                  style={{
                    width: `${(((sensor.value || sensor.min_range) - (sensor.min_range || 0)) / ((sensor.max_range || 100) - (sensor.min_range || 0))) * 100}%`,
                    backgroundColor: typeColors[sensor.type]?.replace('text-', '#') || '#00ffff',
                  }}
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(sensor)}
                  className="flex-1 px-3 py-2 bg-blue-600 text-white text-xs rounded hover:bg-blue-500 transition-all font-bold"
                >
                  ✎ Edit
                </button>
                <button
                  onClick={() => handleDelete(sensor.id)}
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
