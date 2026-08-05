import { useState, useEffect } from 'react';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function LabAutomation() {
  const { user, loading } = useCurrentUser();
  const [devices, setDevices] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loadingData, setLoadingData] = useState(true);

  const [estopActive, setEstopActive] = useState(false);
  const [estopReason, setEstopReason] = useState(null);

  useEffect(() => {
    if (!loading && user) fetchData();
    if (!loading && user) fetchEstopStatus();
    // subscribe to SSE for live updates
    let es
    if(!loading && user){
      try{
        es = new EventSource(`${API_URL}/api/v1/stream/events`)
        es.onmessage = (ev) => {
          try{
            const data = JSON.parse(ev.data)
            if(data.type === 'equipment_command' || data.type === 'safety_event' || data.type === 'automation_job'){
              // refresh lists to reflect recent changes
              fetchData()
            }
          }catch(err){ console.error('SSE parse', err) }
        }
      }catch(err){ console.error('SSE error', err) }
    }
    return ()=>{ if(es) es.close() }
  }, [loading, user]);

  async function fetchEstopStatus() {
    const token = localStorage.getItem('aegis_token');
    try {
      const resp = await fetch(`${API_URL}/api/v1/safety/estop`, { headers: { Authorization: `Bearer ${token}` } });
      const data = resp.ok ? await resp.json() : { active: false };
      setEstopActive(!!data.active);
      setEstopReason(data.reason || null);
    } catch (err) {
      console.error('Failed to fetch estop status', err);
    }
  }

  async function activateEstop() {
    const token = localStorage.getItem('aegis_token');
    const resp = await fetch(`${API_URL}/api/v1/safety/estop`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ reason: 'manual triggered from UI' }) });
    if (resp.ok) fetchEstopStatus();
  }

  async function releaseEstop() {
    const token = localStorage.getItem('aegis_token');
    const resp = await fetch(`${API_URL}/api/v1/safety/estop/release`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
    if (resp.ok) fetchEstopStatus();
  }

  async function fetchData() {
    setLoadingData(true);
    const token = localStorage.getItem('aegis_token');
    try {
      const [devResp, jobResp] = await Promise.all([
        fetch(`${API_URL}/api/v1/lab/devices`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/lab/jobs`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      const devs = devResp.ok ? await devResp.json() : [];
      const js = jobResp.ok ? await jobResp.json() : [];
      setDevices(Array.isArray(devs) ? devs : []);
      setJobs(Array.isArray(js) ? js : []);
    } catch (err) {
      console.error('Failed to load lab automation data', err);
    } finally {
      setLoadingData(false);
    }
  }

  // Form state
  const [form, setForm] = useState({ name: '', device_id: '', command: '', scheduled_at: '', recurring: false });
  const [submitting, setSubmitting] = useState(false);

  async function submitJob(e) {
    e.preventDefault();
    setSubmitting(true);
    const token = localStorage.getItem('aegis_token');
    try {
      const payload = {
        name: form.name,
        device_id: form.device_id ? Number(form.device_id) : null,
        command: form.command,
        scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
        recurring: !!form.recurring,
      };
      const resp = await fetch(`${API_URL}/api/v1/lab/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error('Create job failed');
      setForm({ name: '', device_id: '', command: '', scheduled_at: '', recurring: false });
      fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to create job');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || loadingData) return <div className="p-6">Loading lab automation...</div>;

  const EstopControl = () => (
    <div className="p-3 border rounded inline-flex items-center space-x-3">
      <div>
        <div className="text-sm font-semibold">Emergency Stop</div>
        <div className="text-xs text-gray-600">Status: {estopActive ? 'ACTIVE' : 'Clear'}{estopReason ? ` — ${estopReason}` : ''}</div>
      </div>
      {estopActive ? (
        <button onClick={releaseEstop} className="px-3 py-1 bg-green-600 text-white rounded">Release</button>
      ) : (
        <button onClick={activateEstop} className="px-3 py-1 bg-red-600 text-white rounded">Activate E-Stop</button>
      )}
    </div>
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Lab Automation</h1>
        <EstopControl />
      </div>

      <section>
        <h2 className="text-xl font-semibold mb-2">Devices</h2>
        {devices.length === 0 ? <p>No devices registered.</p> : (
          <ul className="space-y-2">
            {devices.map(d => (
              <li key={d.id} className="p-3 border rounded">{d.name} — {d.device_type} — {d.status}</li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Scheduled Jobs</h2>
        {jobs.length === 0 ? <p>No jobs scheduled.</p> : (
          <ul className="space-y-2">
            {jobs.map(j => (
              <li key={j.id} className="p-3 border rounded">{j.name} — {j.status} — {j.scheduled_at || 'N/A'}</li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Create Job</h2>
        <form onSubmit={submitJob} className="space-y-3 max-w-md">
          <div>
            <label className="block text-sm font-medium">Name</label>
            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium">Device</label>
            <select value={form.device_id} onChange={e => setForm({ ...form, device_id: e.target.value })} className="w-full p-2 border rounded">
              <option value="">-- select device --</option>
              {devices.map(d => <option key={d.id} value={d.id}>{d.name} ({d.device_type})</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Command</label>
            <input value={form.command} onChange={e => setForm({ ...form, command: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium">Scheduled At</label>
            <input type="datetime-local" value={form.scheduled_at} onChange={e => setForm({ ...form, scheduled_at: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div className="flex items-center space-x-2">
            <input id="recurring" type="checkbox" checked={form.recurring} onChange={e => setForm({ ...form, recurring: e.target.checked })} />
            <label htmlFor="recurring" className="text-sm">Recurring (daily)</label>
          </div>
          <div>
            <button type="submit" disabled={submitting} className="px-4 py-2 bg-blue-600 text-white rounded">{submitting ? 'Creating...' : 'Create Job'}</button>
          </div>
        </form>
      </section>
    </div>
  );
}
