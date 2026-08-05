import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import TaskForm from '../components/forms/TaskForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function TasksManagement() {
  const { user, loading } = useCurrentUser();
  const [tasks, setTasks] = useState([]);
  const [robots, setRobots] = useState([]);
  const [users, setUsers] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    robot_id: null,
    assigned_to: null,
    priority: 'medium',
    status: 'pending',
    due_date: '',
    description: '',
  });
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    if (!loading && user) {
      fetchTasks();
      fetchRobots();
      fetchUsers();
    }
  }, [user, loading]);

  const fetchTasks = async () => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/tasks`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = res.ok ? await res.json() : [];
      setTasks(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching tasks:', err);
    }
  };

  const fetchRobots = async () => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/robots`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = res.ok ? await res.json() : [];
      setRobots(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching robots:', err);
    }
  };

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = res.ok ? await res.json() : [];
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching users:', err);
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
          setTasks(tasks.map((t) => (t.id === editingId ? task : t)));
        } else {
          setTasks([...tasks, task]);
        }
        resetForm();
      }
    } catch (err) {
      console.error('Error saving task:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this task?')) return;

    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/tasks/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        setTasks(tasks.filter((t) => t.id !== id));
      }
    } catch (err) {
      console.error('Error deleting task:', err);
    }
  };

  const handleEdit = (task) => {
    setFormData({
      name: task.name || '',
      robot_id: task.robot_id || null,
      assigned_to: task.assigned_to || null,
      priority: task.priority || 'medium',
      status: task.status || 'pending',
      due_date: task.due_date || '',
      description: task.description || '',
    });
    setEditingId(task.id);
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      robot_id: null,
      assigned_to: null,
      priority: 'medium',
      status: 'pending',
      due_date: '',
      description: '',
    });
    setEditingId(null);
    setShowForm(false);
  };

  const filteredTasks = tasks.filter((t) => {
    const nameMatch = t.name?.toLowerCase().includes(search.toLowerCase());
    const statusMatch = filterStatus === 'all' || t.status === filterStatus;
    return nameMatch && statusMatch;
  });

  const priorityColors = {
    low: 'text-green-400',
    medium: 'text-yellow-400',
    high: 'text-orange-400',
    urgent: 'text-red-400',
  };

  const statusBg = {
    pending: 'bg-gray-700',
    'in-progress': 'bg-blue-700',
    completed: 'bg-green-700',
    failed: 'bg-red-700',
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
            ✓ TASK MANAGEMENT
          </h1>
          <p className="text-aegis-muted">Create and track robotic and operational tasks</p>
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm);
            resetForm();
          }}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-500 hover:to-pink-500 transition-all font-mono text-sm font-bold"
        >
          {showForm ? '✕ Cancel' : '+ New Task'}
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <TaskForm
          formData={formData}
          setFormData={setFormData}
          editingId={editingId}
          onSubmit={handleSubmit}
          robots={robots}
          users={users}
          onCancel={resetForm}
        />
      )}

      {/* Filters */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <input
          type="text"
          placeholder="Search tasks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-3 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
        />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-3 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="in-progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Tasks List */}
      <div className="space-y-3">
        {filteredTasks.length === 0 ? (
          <div className="text-center py-12 border border-aegis-primary/20 rounded">
            <p className="text-aegis-muted text-lg">No tasks found.</p>
          </div>
        ) : (
          filteredTasks.map((task) => {
            const assignedUser = users.find((u) => u.id === task.assigned_to);
            const assignedRobot = robots.find((r) => r.id === task.robot_id);

            return (
              <div
                key={task.id}
                className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 hover:border-aegis-primary/60 transition-all"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-lg font-bold text-aegis-primary">{task.name}</h3>
                    {task.description && (
                      <p className="text-xs text-aegis-muted mt-1">{task.description}</p>
                    )}
                  </div>
                  <span className={`px-3 py-1 rounded text-xs font-bold text-white ${statusBg[task.status] || 'bg-gray-700'}`}>
                    {(task.status || 'pending').toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs mb-3">
                  {assignedRobot && (
                    <div className="text-aegis-muted">
                      🤖 <span className="text-aegis-primary">{assignedRobot.name}</span>
                    </div>
                  )}
                  {assignedUser && (
                    <div className="text-aegis-muted">
                      👤 <span className="text-aegis-primary">{assignedUser.email.split('@')[0]}</span>
                    </div>
                  )}
                  <div className={priorityColors[task.priority] || 'text-gray-400'}>
                    {task.priority?.toUpperCase() || 'MEDIUM'}
                  </div>
                  {task.due_date && (
                    <div className="text-aegis-muted">
                      📅 {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  )}
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
            );
          })
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
