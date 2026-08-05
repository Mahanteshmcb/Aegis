import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';
import UserForm from '../components/forms/UserForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function UserManagement() {
  const { user, loading } = useCurrentUser();
  const [users, setUsers] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    role: 'operator',
    status: 'active',
    permissions: [],
  });
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!loading && user) {
      fetchUsers();
    }
  }, [user, loading]);

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
      const endpoint = editingId ? `/api/v1/users/${editingId}` : '/api/v1/users';

      const res = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const newUser = await res.json();
        if (editingId) {
          setUsers(users.map((u) => (u.id === editingId ? newUser : u)));
        } else {
          setUsers([...users, newUser]);
        }
        setFormData({ email: '', role: 'operator', status: 'active', permissions: [] });
        setEditingId(null);
        setShowForm(false);
      }
    } catch (err) {
      console.error('Error saving user:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;

    try {
      const token = localStorage.getItem('aegis_token');
      const res = await fetch(`${API_URL}/api/v1/users/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        setUsers(users.filter((u) => u.id !== id));
      }
    } catch (err) {
      console.error('Error deleting user:', err);
    }
  };

  const handleEdit = (u) => {
    setFormData({
      email: u.email || '',
      role: u.role || 'operator',
      status: u.status || 'active',
      permissions: u.permissions || [],
    });
    setEditingId(u.id);
    setShowForm(true);
  };

  const filteredUsers = users.filter((u) =>
    u.email?.toLowerCase().includes(search.toLowerCase()) ||
    u.role?.toLowerCase().includes(search.toLowerCase())
  );

  const roleColors = {
    admin: 'text-red-400',
    operator: 'text-cyan-400',
    viewer: 'text-green-400',
    technician: 'text-yellow-400',
  };

  const statusColors = {
    active: 'text-green-400',
    inactive: 'text-gray-400',
    suspended: 'text-red-400',
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
            👥 USER MANAGEMENT
          </h1>
          <p className="text-aegis-muted">Manage users and permissions</p>
        </div>
        {user?.role === 'admin' && (
          <button
            onClick={() => {
              setShowForm(!showForm);
              setEditingId(null);
              setFormData({ email: '', role: 'operator', status: 'active', permissions: [] });
            }}
            className="px-6 py-3 bg-gradient-to-r from-pink-600 to-red-600 text-white rounded-lg hover:from-pink-500 hover:to-red-500 transition-all font-mono text-sm font-bold"
          >
            {showForm ? '✕ Cancel' : '+ Add User'}
          </button>
        )}
      </div>

      {/* Add/Edit Form */}
      {user?.role === 'admin' && showForm && (
        <UserForm
          formData={formData}
          setFormData={setFormData}
          editingId={editingId}
          onSubmit={handleSubmit}
          onCancel={() => {
            setShowForm(false);
            setEditingId(null);
            setFormData({ email: '', role: 'operator', status: 'active', permissions: [] });
          }}
        />
      )}

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search users by email or role..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
        />
      </div>

      {/* Users Table */}
      <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-aegis-primary/30 bg-black/50">
                <th className="px-6 py-3 text-left text-xs font-bold text-aegis-muted uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-bold text-aegis-muted uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-bold text-aegis-muted uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-bold text-aegis-muted uppercase tracking-wider">
                  Joined
                </th>
                {user?.role === 'admin' && (
                  <th className="px-6 py-3 text-left text-xs font-bold text-aegis-muted uppercase tracking-wider">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={user?.role === 'admin' ? 5 : 4} className="px-6 py-8 text-center text-aegis-muted">
                    No users found.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => (
                  <tr key={u.id} className="border-b border-aegis-primary/20 hover:bg-black/30 transition-colors">
                    <td className="px-6 py-4 text-sm font-mono text-aegis-primary">{u.email}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`${roleColors[u.role] || 'text-gray-400'} font-bold`}>
                        {(u.role || 'unknown').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`${statusColors[u.status] || 'text-gray-400'} font-bold`}>
                        ◆ {(u.status || 'unknown').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-aegis-muted">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    {user?.role === 'admin' && (
                      <td className="px-6 py-4 text-sm flex gap-2">
                        <button
                          onClick={() => handleEdit(u)}
                          className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-500 transition-all"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(u.id)}
                          className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-500 transition-all"
                        >
                          Delete
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
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
