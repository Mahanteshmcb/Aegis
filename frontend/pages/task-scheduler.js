import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function TaskScheduler() {
  const { user, token, loading } = useCurrentUser();
  const [robots, setRobots] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [search, setSearch] = useState('');
  const [operation, setOperation] = useState('INSPECT');
  const [robotId, setRobotId] = useState('');
  const [zoneId, setZoneId] = useState('');
  const [priority, setPriority] = useState('5');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [cancellingId, setCancellingId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const fetchQueue = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [queueResponse, deviceResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/robotics/schedule/queue`, { headers }),
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }),
      ]);
      const [queuePayload, devicePayload] = await Promise.all([
        queueResponse.json().catch(() => ({})),
        deviceResponse.json().catch(() => []),
      ]);
      if (!queueResponse.ok) throw new Error(queuePayload.detail || 'Unable to load robot task queue.');
      if (!deviceResponse.ok) throw new Error(devicePayload.detail || 'Unable to load tenant robots.');
      setTasks(Array.isArray(queuePayload?.data?.tasks) ? queuePayload.data.tasks : []);
      setRobots(Array.isArray(devicePayload) ? devicePayload.filter((device) => device.kind === 'robot') : []);
      setError('');
    } catch (loadError) {
      setError(loadError.message || 'Unable to load robot task queue.');
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) fetchQueue();
  }, [loading, user, fetchQueue]);

  const filteredTasks = useMemo(() => {
    const query = search.trim().toLowerCase();
    return tasks.filter((task) => [
      task.task_id,
      task.operation_type,
      task.requested_robot_id,
      task.assigned_robot_id,
      task.zone_id,
      task.status,
      task.task_detail?.description,
    ].some((value) => String(value || '').toLowerCase().includes(query)));
  }, [search, tasks]);

  async function enqueueTask(event) {
    event.preventDefault();
    if (!token) return setError('Session expired. Please sign in again.');
    setIsSubmitting(true);
    setError('');
    setNotice('');
    try {
      const response = await fetch(`${API_URL}/api/v1/robotics/schedule/enqueue`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: `task-${Date.now()}`,
          operation_type: operation,
          robot_id: robotId || null,
          zone_id: zoneId || null,
          priority: Number(priority),
          task_detail: { description: description.trim() },
          timeout_seconds: 120,
          metadata: { source: 'task_scheduler' },
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to enqueue task.');
      setDescription('');
      setNotice(`Task ${result.data?.task_id || ''} added to the queue.`);
      await fetchQueue();
    } catch (submitError) {
      setError(submitError.message || 'Unable to enqueue task.');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function assignPending() {
    if (!token) return setError('Session expired. Please sign in again.');
    setAssigning(true);
    setError('');
    setNotice('');
    try {
      const response = await fetch(`${API_URL}/api/v1/robotics/schedule/assign`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to assign queued tasks.');
      setNotice(`${result.data?.assigned_count ?? 0} pending tasks assigned.`);
      await fetchQueue();
    } catch (assignError) {
      setError(assignError.message || 'Unable to assign queued tasks.');
    } finally {
      setAssigning(false);
    }
  }

  async function cancelTask(task) {
    if (task.status !== 'pending') return;
    if (!window.confirm(`Cancel task ${task.task_id}?`)) return;
    setCancellingId(task.task_id);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/v1/robotics/schedule/cancel/${encodeURIComponent(task.task_id)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to cancel task.');
      setNotice(`Task ${task.task_id} canceled.`);
      await fetchQueue();
    } catch (cancelError) {
      setError(cancelError.message || 'Unable to cancel task.');
    } finally {
      setCancellingId(null);
    }
  }

  if (loading) return <div className="p-6 text-slate-400">Checking session...</div>;
  if (!user) return <div className="p-6 text-slate-300">Sign in to manage robot tasks. <Link href="/login" className="text-cyan-300">Sign in</Link></div>;

  const pendingCount = tasks.filter((task) => task.status === 'pending').length;
  const assignedCount = tasks.filter((task) => task.status === 'assigned').length;
  const conflictedCount = tasks.filter((task) => task.status === 'conflicted').length;

  return (
    <main className="mx-auto max-w-6xl space-y-7 p-6 text-slate-100">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-semibold">Robot Task Scheduler</h1>
          <p className="mt-2 text-sm text-slate-400">Queue robot work, assign available robots, and cancel pending tasks.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchQueue} disabled={isLoading} className="rounded border border-slate-700 px-3 py-2 text-sm text-slate-200 disabled:opacity-50">{isLoading ? 'Refreshing...' : 'Refresh'}</button>
          <button onClick={assignPending} disabled={assigning || pendingCount === 0} className="rounded bg-cyan-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">{assigning ? 'Assigning...' : 'Assign pending'}</button>
        </div>
      </header>

      {error && <div role="alert" className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>}
      {notice && <div role="status" className="rounded border border-emerald-700 bg-emerald-900/20 p-3 text-sm text-emerald-200">{notice}</div>}

      <div className="grid grid-cols-3 gap-4 border-b border-slate-800 pb-5">
        {[['Pending', pendingCount], ['Assigned', assignedCount], ['Conflicted', conflictedCount]].map(([label, count]) => <div key={label}><p className="text-xs uppercase tracking-wider text-slate-500">{label}</p><p className="mt-1 text-2xl font-semibold">{count}</p></div>)}
      </div>

      <form onSubmit={enqueueTask} className="grid gap-4 border-b border-slate-800 pb-6 md:grid-cols-2 xl:grid-cols-3">
        <label className="text-sm text-slate-300">Operation
          <select value={operation} onChange={(event) => setOperation(event.target.value)} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white">
            {['INSPECT', 'HARVEST', 'PLANT', 'PRUNE', 'SPRAY', 'SAMPLE', 'MAINTAIN', 'NAVIGATE'].map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label className="text-sm text-slate-300">Robot (optional)
          <select value={robotId} onChange={(event) => setRobotId(event.target.value)} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white">
            <option value="">Assign during scheduling</option>{robots.map((robot) => <option key={robot.id} value={robot.device_id}>{robot.name} · {robot.status}</option>)}
          </select>
        </label>
        <label className="text-sm text-slate-300">Zone ID (optional)
          <input value={zoneId} onChange={(event) => setZoneId(event.target.value)} inputMode="numeric" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" />
        </label>
        <label className="text-sm text-slate-300">Priority (1-10)
          <input required type="number" min="1" max="10" step="1" value={priority} onChange={(event) => setPriority(event.target.value)} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" />
        </label>
        <label className="text-sm text-slate-300 md:col-span-2">Task details
          <input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Inspection notes or operation parameters" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 p-2 text-white" />
        </label>
        <button type="submit" disabled={isSubmitting} className="w-fit rounded bg-emerald-700 px-4 py-2 font-semibold text-white disabled:opacity-50">{isSubmitting ? 'Enqueuing...' : 'Add to queue'}</button>
      </form>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-2">
          <h2 className="text-lg font-semibold">Queued tasks</h2>
          <input type="search" aria-label="Search task queue" placeholder="Search task, robot, zone, status" value={search} onChange={(event) => setSearch(event.target.value)} className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
        </div>
        {isLoading ? <p className="py-6 text-center text-slate-400">Loading task queue...</p> : filteredTasks.length === 0 ? <p className="py-6 text-center text-slate-400">No tasks match this queue.</p> : (
          <div className="divide-y divide-slate-800 border-y border-slate-800">
            {filteredTasks.map((task) => <article key={task.task_id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="font-semibold text-white">{task.operation_type} <span className="font-mono text-xs text-slate-500">{task.task_id}</span></h3>
                <p className="mt-1 text-sm text-slate-400">{task.task_detail?.description || 'No additional details'}</p>
                <p className="mt-1 text-xs text-slate-500">Requested: {task.requested_robot_id || 'Unassigned'} · Assigned: {task.assigned_robot_id || 'Not assigned'} · Zone: {task.zone_id || 'Unspecified'} · Priority: {task.priority}</p>
                {task.conflict_reason && <p className="mt-1 text-xs text-amber-300">{task.conflict_reason}</p>}
              </div>
              <div className="flex items-center gap-3"><span className="text-xs uppercase text-cyan-200">{task.status}</span><button onClick={() => cancelTask(task)} disabled={task.status !== 'pending' || cancellingId === task.task_id} className="rounded border border-red-800 px-3 py-2 text-xs text-red-300 disabled:opacity-40">{cancellingId === task.task_id ? 'Canceling...' : 'Cancel'}</button></div>
            </article>)}
          </div>
        )}
      </section>
    </main>
  );
}