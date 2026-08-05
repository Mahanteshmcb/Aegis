import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import useEstateState from '../hooks/useEstateState';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function TaskScheduler() {
  const { user, loading } = useCurrentUser();
  const estateState = useEstateState();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    robot_id: '',
    description: '',
    priority: 'medium',
    status: 'pending',
    scheduled_time: '',
  });
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!loading && user) {
      fetchTasks();
    }
  }, [user, loading]);

  const fetchTasks = async () => {
    try {
      estateState.setLoading(true);
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/tasks`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const tasks = res.ok ? await res.json() : [];
      estateState.setTasks(Array.isArray(tasks) ? tasks : []);
      estateState.setLoading(false);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      estateState.setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('aegis_token');
      const method = editingId ? 'PUT' : 'POST';
      const endpoint = editingId ? `/api/v1/tasks/${editingId}` : '/api/v1/tasks';

      const res = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const task = await res.json();
        if (editingId) {
          estateState.updateTask(editingId, task);
        } else {
          estateState.addTask(task);
        }
        setFormData({
          name: '',
          robot_id: '',
          description: '',
          priority: 'medium',
          status: 'pending',
          scheduled_time: '',
        });
        setEditingId(null);
        setShowForm(false);
      }
    } catch (err) {
      console.error('Error saving task:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;

    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/tasks/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        estateState.deleteTask(id);
      }
    } catch (err) {
      console.error('Error deleting task:', err);
    }
  };

  const handleEdit = (task) => {
    setFormData({
      name: task.name || '',
      robot_id: task.robot_id || '',
      description: task.description || '',
      priority: task.priority || 'medium',
      status: task.status || 'pending',
      scheduled_time: task.scheduled_time || '',
    });
    setEditingId(task.id);
    setShowForm(true);
  };

  const filteredTasks = estateState.tasks.filter((t) =>
    t.name?.toLowerCase().includes(search.toLowerCase()) ||
    t.description?.toLowerCase().includes(search.toLowerCase())
  );

  const priorityColors = {
    low: 'text-green-400',
    medium: 'text-yellow-400',
    high: 'text-orange-400',
    critical: 'text-red-400',
  };

  const statusColors = {
    pending: 'text-gray-400',
    scheduled: 'text-blue-400',
    running: 'text-cyan-400',
    completed: 'text-green-400',
    failed: 'text-red-400',
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
            📅 TASK SCHEDULER
          </h1>
          <p className="text-aegis-muted">Schedule and manage robot tasks</p>
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingId(null);
            setFormData({
              name: '',
              robot_id: '',
              description: '',
              priority: 'medium',
              status: 'pending',
              scheduled_time: '',
            });
          }}
          className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-500 hover:to-purple-500 transition-all font-mono text-sm font-bold"
        >
          {showForm ? '✕ Cancel' : '+ Schedule Task'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-bold text-aegis-primary mb-4">
            {editingId ? 'Edit Task' : 'Schedule New Task'}
          </h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Task Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Greenhouse Inspection"
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Assign Robot</label>
              <select
                value={formData.robot_id}
                onChange={(e) => setFormData({ ...formData, robot_id: e.target.value })}
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              >
                <option value="">Select a robot...</option>
                {estateState.robots.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name || `Robot ${r.id}`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              >
                <option value="pending">Pending</option>
                <option value="scheduled">Scheduled</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Scheduled Time</label>
              <input
                type="datetime-local"
                value={formData.scheduled_time}
                onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Description</label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Task details..."
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              className="col-span-1 md:col-span-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
            >
              {editingId ? 'Update Task' : 'Schedule Task'}
            </button>
          </form>
        </div>
      )}

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search tasks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
        />
      </div>

      {/* Tasks List */}
      <div className="space-y-4">
        {filteredTasks.length === 0 ? (
          <div className="text-center py-12 bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg">
            <p className="text-aegis-muted text-lg">No tasks found. Schedule one to get started.</p>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <div
              key={task.id}
              className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 hover:border-aegis-primary/60 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-aegis-primary">{task.name || `Task ${task.id}`}</h3>
                  {task.description && <p className="text-xs text-aegis-muted mt-1">{task.description}</p>}
                </div>
                <div className="flex gap-2 ml-4">
                  <span className={`text-xs font-bold ${priorityColors[task.priority] || 'text-gray-400'}`}>
                    ◆ {(task.priority || 'medium').toUpperCase()}
                  </span>
                  <span className={`text-xs font-bold ${statusColors[task.status] || 'text-gray-400'}`}>
                    ◆ {(task.status || 'pending').toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-xs font-mono mb-4">
                <div>
                  <span className="text-aegis-muted">Assigned Robot:</span>
                  <p className="text-aegis-primary">
                    {estateState.robots.find((r) => r.id == task.robot_id)?.name || 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-aegis-muted">Scheduled:</span>
                  <p className="text-aegis-primary">
                    {task.scheduled_time
                      ? new Date(task.scheduled_time).toLocaleString()
                      : 'Not scheduled'}
                  </p>
                </div>
                <div>
                  <span className="text-aegis-muted">Created:</span>
                  <p className="text-aegis-primary">
                    {task.created_at ? new Date(task.created_at).toLocaleDateString() : 'Unknown'}
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(task)}
                  className="flex-1 px-3 py-2 bg-blue-600 text-white text-xs rounded hover:bg-blue-500 transition-all font-bold"
                >
                  ✎ Edit
                </button>
                <button
                  onClick={() => handleDelete(task.id)}
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
