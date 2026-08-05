import { useEffect, useState } from 'react';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function Schedules() {
  const { user, loading } = useCurrentUser();
  const [jobs, setJobs] = useState([]);
  const [logs, setLogs] = useState(null);
  const [loadingData, setLoadingData] = useState(true);
  const [zones, setZones] = useState([]);
  const [hvacSchedules, setHvacSchedules] = useState([]);
  const [hvacForm, setHvacForm] = useState({ name: '', zone_id: '', setpoint: 22, scheduled_at: '', recurring: false, interval_days: '' });

  useEffect(() => {
    if (!loading && user) fetchJobs();
    if (!loading && user) fetchZonesAndSchedules();
    if (!loading && user) fetchEstopStatus();
    // SSE subscription
    let es
    if(!loading && user){
      try{
        es = new EventSource(`${API_URL}/api/v1/stream/events`)
        es.onmessage = (ev) => {
          try{
            const data = JSON.parse(ev.data)
            if(data.type === 'safety_event' || data.type === 'equipment_command' || data.type === 'automation_job'){
              fetchJobs();
              fetchZonesAndSchedules();
            }
          }catch(err){ console.error('SSE parse', err) }
        }
      }catch(err){ console.error('SSE error', err) }
    }
    return ()=>{ if(es) es.close() }
  }, [loading, user]);

  const [estopActive, setEstopActive] = useState(false);
  const [estopReason, setEstopReason] = useState(null);

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


  async function fetchJobs() {
    setLoadingData(true);
    const token = localStorage.getItem('aegis_token');
    try {
      const resp = await fetch(`${API_URL}/api/v1/lab/jobs`, { headers: { Authorization: `Bearer ${token}` } });
      const data = resp.ok ? await resp.json() : [];
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingData(false);
    }
  }

  async function fetchZonesAndSchedules() {
    const token = localStorage.getItem('aegis_token');
    try {
      const [zonesRes, schedRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/zones`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/hvac/schedules`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      const zonesData = zonesRes.ok ? await zonesRes.json() : [];
      const schedData = schedRes.ok ? await schedRes.json() : [];
      setZones(Array.isArray(zonesData) ? zonesData : []);
      setHvacSchedules(Array.isArray(schedData) ? schedData : []);
    } catch (err) {
      console.error(err);
    }
  }

  async function createHvacSchedule(e) {
    e.preventDefault();
    const token = localStorage.getItem('aegis_token');
    try {
      const payload = {
        name: hvacForm.name,
        zone_id: Number(hvacForm.zone_id),
        setpoint: Number(hvacForm.setpoint),
        scheduled_at: hvacForm.scheduled_at ? new Date(hvacForm.scheduled_at).toISOString() : null,
        recurring: !!hvacForm.recurring,
        interval_days: hvacForm.interval_days ? Number(hvacForm.interval_days) : null,
      };
      const resp = await fetch(`${API_URL}/api/v1/hvac/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error('Failed to create schedule');
      setHvacForm({ name: '', zone_id: '', setpoint: 22, scheduled_at: '', recurring: false, interval_days: '' });
      fetchZonesAndSchedules();
    } catch (err) {
      console.error(err);
      alert('Failed to create HVAC schedule');
    }
  }

  async function deleteHvacSchedule(id) {
    if (!confirm('Delete HVAC schedule?')) return;
    const token = localStorage.getItem('aegis_token');
    await fetch(`${API_URL}/api/v1/hvac/schedules/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
    fetchZonesAndSchedules();
  }

  // Edit flow
  const [editing, setEditing] = useState(null);

  function startEdit(s) {
    setEditing({ ...s });
  }

  function cancelEdit() {
    setEditing(null);
  }

  async function submitEdit(e) {
    e.preventDefault();
    const token = localStorage.getItem('aegis_token');
    try {
      const resp = await fetch(`${API_URL}/api/v1/hvac/schedules/${editing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: editing.name,
          zone_id: Number(editing.zone_id),
          setpoint: Number(editing.setpoint),
          scheduled_at: editing.scheduled_at || null,
          recurring: !!editing.recurring,
          interval_days: editing.interval_days ? Number(editing.interval_days) : null,
        })
      });
      if (!resp.ok) throw new Error('Failed to update schedule');
      setEditing(null);
      fetchZonesAndSchedules();
    } catch (err) {
      console.error(err);
      alert('Failed to update schedule');
    }
  }

  async function runJob(id) {
    const token = localStorage.getItem('aegis_token');
    await fetch(`${API_URL}/api/v1/lab/jobs/${id}/run`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
    fetchJobs();
  }

  async function deleteJob(id) {
    if (!confirm('Delete job?')) return;
    const token = localStorage.getItem('aegis_token');
    await fetch(`${API_URL}/api/v1/lab/jobs/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
    fetchJobs();
  }

  async function viewLogs(id) {
    const token = localStorage.getItem('aegis_token');
    const resp = await fetch(`${API_URL}/api/v1/lab/jobs/${id}/logs`, { headers: { Authorization: `Bearer ${token}` } });
    const data = resp.ok ? await resp.json() : [];
    setLogs({ jobId: id, entries: data });
  }

  if (loading || loadingData) return <div className="p-6">Loading schedules...</div>;

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
        <h1 className="text-3xl font-bold">Schedules</h1>
        <EstopControl />
      </div>

      <section>
        <h2 className="text-xl font-semibold mb-2">Scheduled Jobs</h2>
        {jobs.length === 0 ? <p>No jobs scheduled.</p> : (
          <ul className="space-y-2">
            {jobs.map(j => (
              <li key={j.id} className="p-3 border rounded flex items-center justify-between">
                <div>
                  <div className="font-semibold">{j.name}</div>
                  <div className="text-sm text-gray-600">{j.command} — {j.scheduled_at || 'N/A'}</div>
                </div>
                <div className="space-x-2">
                  <button onClick={() => runJob(j.id)} className="px-3 py-1 bg-blue-600 text-white rounded">Run</button>
                  <button onClick={() => viewLogs(j.id)} className="px-3 py-1 bg-gray-200 rounded">Logs</button>
                  <button onClick={() => deleteJob(j.id)} className="px-3 py-1 bg-red-600 text-white rounded">Delete</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {logs && (
        <section>
          <h2 className="text-xl font-semibold">Execution Logs for Job {logs.jobId}</h2>
          <div className="p-3 border rounded max-w-3xl">
            {logs.entries.length === 0 ? <p>No logs.</p> : (
              <ul className="space-y-2">
                {logs.entries.map(l => (
                  <li key={l.id} className="text-sm">
                    <div className="font-medium">{l.status} — {new Date(l.started_at).toLocaleString()}</div>
                    <div className="text-xs text-gray-700 whitespace-pre-wrap">{l.output}</div>
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-3">
              <button onClick={() => setLogs(null)} className="px-3 py-1 bg-gray-300 rounded">Close</button>
            </div>
          </div>
        </section>
      )}

      <section>
        <h2 className="text-xl font-semibold mt-6 mb-2">HVAC Schedules</h2>
        <form onSubmit={createHvacSchedule} className="space-y-3 max-w-lg mb-4">
          <div>
            <label className="block text-sm font-medium">Name</label>
            <input value={hvacForm.name} onChange={e => setHvacForm({ ...hvacForm, name: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium">Zone</label>
            <select value={hvacForm.zone_id} onChange={e => setHvacForm({ ...hvacForm, zone_id: e.target.value })} className="w-full p-2 border rounded">
              <option value="">-- select zone --</option>
              {zones.map(z => <option key={z.id} value={z.id}>{z.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Setpoint (°C)</label>
            <input type="number" value={hvacForm.setpoint} onChange={e => setHvacForm({ ...hvacForm, setpoint: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div>
            <label className="block text-sm font-medium">Scheduled At</label>
            <input type="datetime-local" value={hvacForm.scheduled_at} onChange={e => setHvacForm({ ...hvacForm, scheduled_at: e.target.value })} className="w-full p-2 border rounded" />
          </div>
          <div className="flex items-center space-x-2">
            <input id="hvac-recurring" type="checkbox" checked={hvacForm.recurring} onChange={e => setHvacForm({ ...hvacForm, recurring: e.target.checked })} />
            <label htmlFor="hvac-recurring" className="text-sm">Recurring</label>
            <input type="number" placeholder="Interval days" value={hvacForm.interval_days} onChange={e => setHvacForm({ ...hvacForm, interval_days: e.target.value })} className="ml-4 p-2 border rounded w-36" />
          </div>
          <div>
            <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Create HVAC Schedule</button>
          </div>
        </form>

        {hvacSchedules.length === 0 ? <p>No HVAC schedules.</p> : (
          <ul className="space-y-2">
            {hvacSchedules.map(s => (
              <li key={s.id} className="p-3 border rounded flex items-center justify-between">
                <div>
                  <div className="font-semibold">{s.name} — {s.setpoint}°C</div>
                  <div className="text-sm text-gray-600">Zone: {s.zone_id} — Next: {s.scheduled_at}</div>
                </div>
                <div className="space-x-2">
                    <button onClick={() => startEdit(s)} className="px-3 py-1 bg-yellow-500 text-white rounded">Edit</button>
                    <button onClick={() => deleteHvacSchedule(s.id)} className="px-3 py-1 bg-red-600 text-white rounded">Delete</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

        {editing && (
          <section>
            <h2 className="text-xl font-semibold">Edit HVAC Schedule</h2>
            <form onSubmit={submitEdit} className="space-y-3 max-w-lg mb-4">
              <div>
                <label className="block text-sm font-medium">Name</label>
                <input value={editing.name} onChange={e => setEditing({ ...editing, name: e.target.value })} className="w-full p-2 border rounded" />
              </div>
              <div>
                <label className="block text-sm font-medium">Zone</label>
                <select value={editing.zone_id} onChange={e => setEditing({ ...editing, zone_id: e.target.value })} className="w-full p-2 border rounded">
                  <option value="">-- select zone --</option>
                  {zones.map(z => <option key={z.id} value={z.id}>{z.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium">Setpoint (°C)</label>
                <input type="number" value={editing.setpoint} onChange={e => setEditing({ ...editing, setpoint: e.target.value })} className="w-full p-2 border rounded" />
              </div>
              <div>
                <label className="block text-sm font-medium">Scheduled At</label>
                <input type="datetime-local" value={editing.scheduled_at || ''} onChange={e => setEditing({ ...editing, scheduled_at: e.target.value })} className="w-full p-2 border rounded" />
              </div>
              <div className="flex items-center space-x-2">
                <input id="edit-hvac-recurring" type="checkbox" checked={editing.recurring} onChange={e => setEditing({ ...editing, recurring: e.target.checked })} />
                <label htmlFor="edit-hvac-recurring" className="text-sm">Recurring</label>
                <input type="number" placeholder="Interval days" value={editing.interval_days} onChange={e => setEditing({ ...editing, interval_days: e.target.value })} className="ml-4 p-2 border rounded w-36" />
              </div>
              <div>
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Update Schedule</button>
                <button onClick={cancelEdit} type="button" className="ml-3 px-4 py-2 bg-gray-300 rounded">Cancel</button>
              </div>
            </form>
          </section>
        )}
    </div>
  );
}
