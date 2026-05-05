import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Sidebar from '../components/Sidebar';
import ProtectedRoute from '../components/ProtectedRoute';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

function ZonesContent() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [zones, setZones] = useState([]);
  const [loadingZones, setLoadingZones] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    if (!loading && user) {
      fetchZones();
    }
  }, [user, loading]);

  async function fetchZones() {
    try {
      setLoadingZones(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/zones`, {
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
        throw new Error('Failed to load zones');
      }

      const data = await resp.json();
      setZones(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Fetch zones error:', err);
    } finally {
      setLoadingZones(false);
    }
  }

  async function handleCreateZone(e) {
    e.preventDefault();
    setFormError(null);
    
    // Validation
    if (!formData.name.trim()) {
      setFormError('Zone name is required');
      return;
    }
    
    if (formData.name.trim().length < 2) {
      setFormError('Zone name must be at least 2 characters');
      return;
    }

    try {
      setIsSubmitting(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/zones`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.detail || 'Failed to create zone');
      }

      setFormData({ name: '', description: '' });
      setShowForm(false);
      setSuccess(`Zone "${formData.name}" created successfully!`);
      setTimeout(() => setSuccess(null), 4000);
      fetchZones();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-[#0b1120]">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Security Zones</h1>
            <p className="text-aegis-muted">Define and manage monitored areas</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-6 py-2 bg-aegis-primary hover:bg-aegis-primary/80 text-white rounded-lg font-semibold transition-all"
          >
            {showForm ? 'Cancel' : '+ New Zone'}
          </button>
        </div>

        {/* Success Alert */}
        {success && (
          <div className="mb-6 p-4 bg-green-900/30 border border-green-700 rounded-lg text-green-400 flex items-center justify-between">
            <span>✓ {success}</span>
            <button onClick={() => setSuccess(null)} className="text-green-400 hover:text-green-300">✕</button>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400 flex items-center justify-between">
            <span>✗ {error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">✕</button>
          </div>
        )}

        {/* Create Form */}
        {showForm && (
          <div className="mb-8 p-6 bg-slate-900/50 border border-slate-800 rounded-lg">
            <h2 className="text-lg font-semibold text-aegis-primary mb-4">Create New Zone</h2>
            
            {/* Form Error */}
            {formError && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-400 text-sm">
                {formError}
              </div>
            )}
            
            <form onSubmit={handleCreateZone} className="space-y-4">
              <div>
                <label className="block text-sm text-aegis-muted font-semibold mb-2">Zone Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Warehouse A, Perimeter 1"
                  required
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm text-aegis-muted font-semibold mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the zone's purpose and location..."
                  rows="3"
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none transition-colors"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 text-white rounded-lg font-semibold transition-colors"
                >
                  {isSubmitting ? 'Creating...' : 'Create Zone'}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setFormError(null); }}
                  className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Zones Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loadingZones ? (
            <div className="col-span-full p-8 text-center text-aegis-muted">Loading zones...</div>
          ) : zones.length === 0 ? (
            <div className="col-span-full p-8 text-center text-aegis-muted">
              <p>No zones found.</p>
              <p className="text-sm mt-2">Create your first zone to get started with monitoring.</p>
            </div>
          ) : (
            zones.map((zone) => (
              <div
                key={zone.id}
                className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 hover:border-aegis-primary/50 rounded-lg p-6 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-semibold text-aegis-primary">{zone.name}</h3>
                  <span className="px-3 py-1 bg-green-900/30 border border-green-700 text-green-400 text-xs rounded-full font-semibold">
                    Active
                  </span>
                </div>
                <p className="text-aegis-muted text-sm mb-4">{zone.description || 'No description'}</p>
                <div className="text-xs text-slate-500 space-y-1">
                  <p>ID: <span className="font-mono text-slate-400">{zone.id}</span></p>
                  <p>Created: {new Date(zone.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Stats */}
        {!loadingZones && zones.length > 0 && (
          <div className="mt-12 p-6 bg-slate-900/50 border border-slate-800 rounded-lg">
            <h3 className="text-aegis-primary font-semibold mb-4">Zone Statistics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-aegis-muted">Total Zones</p>
                <p className="text-2xl font-bold text-aegis-primary">{zones.length}</p>
              </div>
              <div>
                <p className="text-aegis-muted">Active Zones</p>
                <p className="text-2xl font-bold text-green-400">{zones.length}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function ZonesPage() {
  return (
    <ProtectedRoute>
      <ZonesContent />
    </ProtectedRoute>
  );
}
