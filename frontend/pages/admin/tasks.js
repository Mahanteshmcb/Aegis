import React, { useEffect, useState } from 'react';
import { getScheduledQueue, enqueueScheduledTask, assignScheduledTasks, cancelScheduledTask } from '../../utils/api';
import useCurrentUser from '../../hooks/useCurrentUser';

export default function AdminTasks() {
  const { token } = useCurrentUser();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState('');
  const [operation, setOperation] = useState('patrol');

  const loadQueue = async () => {
    setLoading(true);
    try {
      const res = await getScheduledQueue(token);
      setQueue(res.data.tasks || []);
    } catch (e) {
      console.error(e);
      alert('Failed to load scheduled tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleEnqueue = async () => {
    if (!taskId) return alert('Provide a task id');
    try {
      await enqueueScheduledTask(token, {
        task_id: taskId,
        operation_type: operation,
        priority: 5,
      });
      setTaskId('');
      loadQueue();
    } catch (e) {
      console.error(e);
      alert('Failed to enqueue task');
    }
  };

  const handleAssign = async () => {
    try {
      await assignScheduledTasks(token);
      loadQueue();
    } catch (e) {
      console.error(e);
      alert('Failed to assign tasks');
    }
  };

  const handleCancel = async (id) => {
    if (!confirm(`Cancel task ${id}?`)) return;
    try {
      await cancelScheduledTask(token, id);
      loadQueue();
    } catch (e) {
      console.error(e);
      alert('Failed to cancel task');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Scheduled Robotic Tasks</h1>
      <div className="mb-4">
        <input className="border p-2 mr-2" value={taskId} onChange={(e) => setTaskId(e.target.value)} placeholder="task id" />
        <select value={operation} onChange={(e) => setOperation(e.target.value)} className="border p-2 mr-2">
          <option value="patrol">patrol</option>
          <option value="collect">collect</option>
          <option value="inspect">inspect</option>
        </select>
        <button className="bg-blue-600 text-white px-3 py-2 rounded" onClick={handleEnqueue}>Enqueue</button>
        <button className="ml-2 bg-green-600 text-white px-3 py-2 rounded" onClick={handleAssign}>Assign Pending</button>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-2">Queue</h2>
        {loading ? <div>Loading...</div> : (
          <table className="w-full table-auto border">
            <thead>
              <tr>
                <th className="border px-2 py-1">Task ID</th>
                <th className="border px-2 py-1">Operation</th>
                <th className="border px-2 py-1">Status</th>
                <th className="border px-2 py-1">Assigned Robot</th>
                <th className="border px-2 py-1">Actions</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((t) => (
                <tr key={t.task_id}>
                  <td className="border px-2 py-1">{t.task_id}</td>
                  <td className="border px-2 py-1">{t.operation_type}</td>
                  <td className="border px-2 py-1">{t.status}</td>
                  <td className="border px-2 py-1">{t.assigned_robot_id || '-'}</td>
                  <td className="border px-2 py-1">
                    <button className="bg-red-600 text-white px-2 py-1 rounded" onClick={() => handleCancel(t.task_id)}>Cancel</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
