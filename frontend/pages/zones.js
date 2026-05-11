import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function ZonesPage() {
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
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
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
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.detail || 'Failed to create zone');
      }

      const createdZone = await resp.json();
      setFormData({ name: '', description: '' });
      setShowForm(false);
      setSuccess(`Zone "${createdZone.name || formData.name}" created successfully!`);
      setTimeout(() => setSuccess(null), 4000);
      fetchZones();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Security Zones</h1>
          <p className="text-aegis-muted">Define and manage monitored areas.</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="px-6 py-2 bg-aegis-primary hover:bg-aegis-primary/80 text-white rounded-xl font-semibold transition-all">
          {showForm ? 'Cancel' : '+ New Zone'}
        </button>
      </div>

      {success && (
        <div className="rounded-2xl border border-green-600/50 bg-green-900/20 p-4 text-green-300">✓ {success}</div>
      )}

      {error && (
        <div className="rounded-2xl border border-red-600/50 bg-red-900/20 p-4 text-red-300">✗ {error}</div>
      )}

      {showForm && (
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <h2 className="text-xl font-semibold text-aegis-primary mb-4">Create New Zone</h2>

          {formError && <div className="mb-4 rounded-xl bg-red-900/20 border border-red-700 p-3 text-red-300">{formError}</div>}

          <form onSubmit={handleCreateZone} className="space-y-4">
            <div>
              <label className="block text-sm text-aegis-muted font-semibold mb-2">Zone Name *</label>
              <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="e.g., Warehouse A" className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white focus:border-aegis-primary outline-none" />
            </div>
            <div>
              <label className="block text-sm text-aegis-muted font-semibold mb-2">Description</label>
              <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} placeholder="Describe the zone's purpose and location..." rows="4" className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white focus:border-aegis-primary outline-none" />
            </div>
            <div className="flex flex-wrap gap-3">
              <button type="submit" disabled={isSubmitting} className="rounded-2xl bg-aegis-primary px-6 py-3 text-white font-semibold hover:bg-sky-400 transition-all">
                {isSubmitting ? 'Creating...' : 'Create Zone'}
              </button>
              <button type="button" onClick={() => { setShowForm(false); setFormError(null); }} className="rounded-2xl border border-slate-700 px-6 py-3 text-aegis-muted hover:border-aegis-primary hover:text-aegis-primary transition-all">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {loadingZones ? (
          <div className="col-span-full rounded-3xl border border-slate-700 bg-slate-900/80 p-8 text-center text-aegis-muted">Loading zones...</div>
        ) : zones.length === 0 ? (
          <div className="col-span-full rounded-3xl border border-slate-700 bg-slate-900/80 p-8 text-center text-aegis-muted">
            <p>No zones found.</p>
            <p className="text-sm mt-2">Create your first zone to begin active monitoring.</p>
          </div>
        ) : (
          zones.map((zone) => (
            <div key={zone.id} className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6 transition hover:border-aegis-primary cursor-pointer">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-white">{zone.name}</h2>
                  <p className="text-sm text-aegis-muted mt-2">{zone.description || 'No description provided.'}</p>
                </div>
                <span className="inline-flex items-center rounded-full border border-green-500/20 bg-green-900/20 px-3 py-1 text-xs font-semibold text-green-300">Active</span>
              </div>
              <div className="grid gap-2 text-xs text-slate-500">
                <p>ID: <span className="font-mono text-slate-400">{zone.id}</span></p>
                <p>Created: {zone.created_at ? new Date(zone.created_at).toLocaleDateString() : 'Unknown'}</p>
              </div>
            </div>
          ))
        )}
      </div>

      {zones.length > 0 && (
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6 text-sm text-aegis-muted">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="uppercase tracking-[0.2em] text-slate-500 text-xs">Total Zones</p>
              <p className="mt-2 text-3xl font-semibold text-white">{zones.length}</p>
            </div>
            <div>
              <p className="uppercase tracking-[0.2em] text-slate-500 text-xs">Active</p>
              <p className="mt-2 text-3xl font-semibold text-green-400">{zones.length}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

