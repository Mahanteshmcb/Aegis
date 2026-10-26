import { useCallback, useEffect, useState } from 'react';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function Schedules() {
  const { user, token, loading } = useCurrentUser();
  const [loadingData, setLoadingData] = useState(true);
  const [zones, setZones] = useState([]);
  const [hvacSchedules, setHvacSchedules] = useState([]);
  const [hvacForm, setHvacForm] = useState({ name: '', zone_id: '', setpoint: 22, scheduled_at: '', recurring: false, interval_days: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchZonesAndSchedules = useCallback(async () => {
    if (!token) return;
    setLoadingData(true);
    try {
      const [zonesRes, schedRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/zones`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/hvac/schedules`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      const zonesData = await zonesRes.json().catch(() => []);
      const schedData = await schedRes.json().catch(() => []);
      if (!zonesRes.ok || !schedRes.ok) throw new Error('Unable to load tenant schedules and zones.');
      setZones(Array.isArray(zonesData) ? zonesData : []);
      setHvacSchedules(Array.isArray(schedData) ? schedData : []);
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to load HVAC schedules.');
    } finally {
      setLoadingData(false);
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) fetchZonesAndSchedules();
  }, [loading, user, fetchZonesAndSchedules]);

  async function createHvacSchedule(e) {
    e.preventDefault();
    if (!token) return setError('Session expired. Please sign in again.');
    setSaving(true);
    setError('');
    try {
      const payload = {
        name: hvacForm.name.trim(),
        zone_id: Number(hvacForm.zone_id),
        setpoint: Number(hvacForm.setpoint),
        scheduled_at: new Date(hvacForm.scheduled_at).toISOString(),
        recurring: !!hvacForm.recurring,
        interval_days: hvacForm.interval_days ? Number(hvacForm.interval_days) : null,
      };
      const resp = await fetch(`${API_URL}/api/v1/hvac/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const result = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(result.detail || 'Failed to create schedule');
      setHvacForm({ name: '', zone_id: '', setpoint: 22, scheduled_at: '', recurring: false, interval_days: '' });
      setSuccess('HVAC schedule created.');
      await fetchZonesAndSchedules();
    } catch (err) {
      setError(err.message || 'Failed to create HVAC schedule.');
    } finally {
      setSaving(false);
    }
  }

  async function deleteHvacSchedule(id) {
    if (!confirm('Delete HVAC schedule?')) return;
    if (!token) return setError('Session expired. Please sign in again.');
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/hvac/schedules/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Failed to delete schedule.');
      setSuccess('HVAC schedule deleted.');
      await fetchZonesAndSchedules();
    } catch (deleteError) {
      setError(deleteError.message || 'Failed to delete schedule.');
    } finally {
      setSaving(false);
    }
  }

  // Edit flow
  const [editing, setEditing] = useState(null);

  function startEdit(s) {
    setEditing({ ...s, scheduled_at: s.scheduled_at ? new Date(s.scheduled_at).toISOString().slice(0, 16) : '' });
  }

  function cancelEdit() {
    setEditing(null);
  }

  async function submitEdit(e) {
    e.preventDefault();
    if (!token) return setError('Session expired. Please sign in again.');
    setSaving(true);
    setError('');
    try {
      const resp = await fetch(`${API_URL}/api/v1/hvac/schedules/${editing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: editing.name,
          zone_id: Number(editing.zone_id),
          setpoint: Number(editing.setpoint),
          scheduled_at: editing.scheduled_at ? new Date(editing.scheduled_at).toISOString() : null,
          recurring: !!editing.recurring,
          interval_days: editing.interval_days ? Number(editing.interval_days) : null,
        })
      });
      const result = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(result.detail || 'Failed to update schedule');
      setEditing(null);
      setSuccess('HVAC schedule updated.');
      await fetchZonesAndSchedules();
    } catch (err) {
      setError(err.message || 'Failed to update schedule.');
    } finally {
      setSaving(false);
    }
  }

  if (loading || loadingData) return <div className="p-6 text-slate-400">Loading HVAC schedules...</div>;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6 text-slate-100">
      <header className="border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-semibold">HVAC Schedules</h1>
        <p className="mt-2 text-sm text-slate-400">Schedule zone setpoints and recurrence.</p>
      </header>
      {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>}
      {success && <div role="status" className="rounded border border-emerald-700 bg-emerald-900/20 p-3 text-sm text-emerald-200">{success}</div>}

      <form onSubmit={createHvacSchedule} className="grid gap-4 border-b border-slate-800 pb-6 md:grid-cols-2">
        <label className="text-sm text-slate-300">Name
          <input required maxLength={255} value={hvacForm.name} onChange={(e) => setHvacForm({ ...hvacForm, name: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" />
        </label>
        <label className="text-sm text-slate-300">Zone
          <select required value={hvacForm.zone_id} onChange={(e) => setHvacForm({ ...hvacForm, zone_id: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white">
            <option value="">Select zone</option>{zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}
          </select>
        </label>
        <label className="text-sm text-slate-300">Setpoint (°C)
          <input required type="number" min="16" max="30" step="0.1" value={hvacForm.setpoint} onChange={(e) => setHvacForm({ ...hvacForm, setpoint: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" />
        </label>
        <label className="text-sm text-slate-300">Scheduled at
          <input required type="datetime-local" value={hvacForm.scheduled_at} onChange={(e) => setHvacForm({ ...hvacForm, scheduled_at: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" />
        </label>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={hvacForm.recurring} onChange={(e) => setHvacForm({ ...hvacForm, recurring: e.target.checked })} /> Recurring</label>
          {hvacForm.recurring && <input required type="number" min="1" step="1" aria-label="Interval days" placeholder="Interval days" value={hvacForm.interval_days} onChange={(e) => setHvacForm({ ...hvacForm, interval_days: e.target.value })} className="w-36 rounded border border-slate-700 bg-slate-950 p-2 text-white" />}
        </div>
        <button type="submit" disabled={saving || zones.length === 0} className="w-fit rounded bg-cyan-700 px-4 py-2 font-semibold text-white disabled:opacity-50">{saving ? 'Saving...' : 'Create schedule'}</button>
      </form>

      <section className="divide-y divide-slate-800 border-y border-slate-800">
        {hvacSchedules.length === 0 ? <p className="py-8 text-center text-slate-400">No HVAC schedules configured.</p> : hvacSchedules.map((schedule) => {
          const zoneName = zones.find((zone) => String(zone.id) === String(schedule.zone_id))?.name || `Zone ${schedule.zone_id}`;
          return <article key={schedule.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-semibold text-white">{schedule.name}</h2>
              <p className="mt-1 text-sm text-slate-400">{zoneName} · {schedule.setpoint}°C · {new Date(schedule.scheduled_at).toLocaleString()}</p>
              <p className="mt-1 text-xs text-slate-500">{schedule.enabled ? 'Enabled' : 'Disabled'} · {schedule.recurring ? `Repeats every ${schedule.interval_days} days` : 'One-time'}</p>
            </div>
            <div className="flex gap-2">
              <button disabled={saving} onClick={() => startEdit(schedule)} className="rounded border border-slate-700 px-3 py-2 text-xs text-slate-200 disabled:opacity-50">Edit</button>
              <button disabled={saving} onClick={() => deleteHvacSchedule(schedule.id)} className="rounded border border-red-800 px-3 py-2 text-xs text-red-300 disabled:opacity-50">Delete</button>
            </div>
          </article>;
        })}
      </section>

      {editing && <section className="space-y-4 border-t border-slate-800 pt-5">
        <h2 className="text-lg font-semibold">Edit {editing.name}</h2>
        <form onSubmit={submitEdit} className="grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-300">Name<input required value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" /></label>
          <label className="text-sm text-slate-300">Zone<select required value={editing.zone_id} onChange={(e) => setEditing({ ...editing, zone_id: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white"><option value="">Select zone</option>{zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}</select></label>
          <label className="text-sm text-slate-300">Setpoint (°C)<input required type="number" min="16" max="30" step="0.1" value={editing.setpoint} onChange={(e) => setEditing({ ...editing, setpoint: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" /></label>
          <label className="text-sm text-slate-300">Scheduled at<input required type="datetime-local" value={editing.scheduled_at} onChange={(e) => setEditing({ ...editing, scheduled_at: e.target.value })} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" /></label>
          <div className="flex items-center gap-3"><label className="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={editing.recurring} onChange={(e) => setEditing({ ...editing, recurring: e.target.checked })} /> Recurring</label>{editing.recurring && <input required type="number" min="1" step="1" aria-label="Edit interval days" placeholder="Interval days" value={editing.interval_days || ''} onChange={(e) => setEditing({ ...editing, interval_days: e.target.value })} className="w-36 rounded border border-slate-700 bg-slate-950 p-2 text-white" />}</div>
          <div className="flex gap-2"><button type="submit" disabled={saving} className="rounded bg-cyan-700 px-4 py-2 text-white disabled:opacity-50">{saving ? 'Saving...' : 'Save changes'}</button><button type="button" onClick={cancelEdit} className="rounded border border-slate-700 px-4 py-2 text-slate-300">Cancel</button></div>
        </form>
      </section>}
    </div>
  );
}
