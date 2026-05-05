import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Sidebar from '../../components/Sidebar';
import RoleBasedRoute from '../../components/RoleBasedRoute';
import useCurrentUser from '../../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

function UserManagementContent() {
  const router = useRouter();
  const { user: currentUser, loading } = useCurrentUser();
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingUserId, setEditingUserId] = useState(null);
  const [editingRole, setEditingRole] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const ROLES = ['admin', 'auditor', 'operator', 'viewer'];

  useEffect(() => {
    if (!loading && currentUser) {
      fetchUsers();
    }
  }, [currentUser, loading]);

  async function fetchUsers() {
    try {
      setLoadingUsers(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/auth/users`, {
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
        throw new Error('Failed to load users');
      }

      const data = await resp.json();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Fetch users error:', err);
    } finally {
      setLoadingUsers(false);
    }
  }

  async function handleUpdateRole(userId, newRole) {
    try {
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/auth/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: newRole }),
      });

      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.detail || 'Failed to update role');
      }

      setSuccess(`Role updated to ${newRole.toUpperCase()}`);
      setTimeout(() => setSuccess(null), 3000);
      setEditingUserId(null);
      fetchUsers();
    } catch (err) {
      setError(err.message);
      console.error('Update role error:', err);
    }
  }

  async function handleDeleteUser(userId) {
    const user = users.find(u => u.id === userId);
    if (!window.confirm(`Are you sure you want to delete ${user?.email}? This action cannot be undone.`)) {
      return;
    }

    try {
      setDeleting(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/auth/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }

      setSuccess(`User deleted successfully`);
      setTimeout(() => setSuccess(null), 3000);
      fetchUsers();
    } catch (err) {
      setError(err.message);
      console.error('Delete user error:', err);
    } finally {
      setDeleting(false);
    }
  }

  const getRoleColor = (role) => {
    switch (role?.toLowerCase()) {
      case 'admin':
        return 'bg-red-900/30 text-red-400 border-red-700';
      case 'auditor':
        return 'bg-yellow-900/30 text-yellow-400 border-yellow-700';
      case 'operator':
        return 'bg-blue-900/30 text-blue-400 border-blue-700';
      case 'viewer':
        return 'bg-slate-900/30 text-slate-400 border-slate-700';
      default:
        return 'bg-slate-900/30 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="flex min-h-screen bg-[#0b1120]">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">User Management</h1>
            <p className="text-aegis-muted">Manage tenant users and assign roles</p>
          </div>
          <button
            onClick={() => { setLoadingUsers(true); fetchUsers(); }}
            className="px-4 py-2 bg-aegis-primary hover:bg-aegis-primary/80 text-white rounded-lg font-semibold transition-colors"
          >
            ↻ Refresh
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

        {/* Search Bar */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search users by email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none transition-colors"
          />
        </div>

        {/* Users Table */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
          {loadingUsers ? (
            <div className="p-8 text-center text-aegis-muted">Loading users...</div>
          ) : users.filter(u => searchQuery === '' || u.email.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 ? (
            <div className="p-8 text-center text-aegis-muted">
              {users.length === 0 ? 'No users found in your tenant.' : 'No users match your search.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-700 bg-slate-800/50">
                  <tr>
                    <th className="px-6 py-3 font-semibold text-aegis-primary">Email</th>
                    <th className="px-6 py-3 font-semibold text-aegis-primary">Role</th>
                    <th className="px-6 py-3 font-semibold text-aegis-primary">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.filter(u => searchQuery === '' || u.email.toLowerCase().includes(searchQuery.toLowerCase())).map((u) => (
                    <tr key={u.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-3 font-mono text-aegis-text">{u.email}</td>
                      <td className="px-6 py-3">
                        {editingUserId === u.id ? (
                          <div className="flex items-center gap-2">
                            <select
                              value={editingRole}
                              onChange={(e) => setEditingRole(e.target.value)}
                              className="px-3 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:border-aegis-primary focus:outline-none"
                            >
                              {ROLES.map((role) => (
                                <option key={role} value={role}>
                                  {role.toUpperCase()}
                                </option>
                              ))}
                            </select>
                          </div>
                        ) : (
                          <span className={`inline-block px-3 py-1 rounded-full border font-bold text-xs ${getRoleColor(u.role)}`}>
                            {u.role?.toUpperCase()}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-3">
                        {editingUserId === u.id ? (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleUpdateRole(u.id, editingRole)}
                              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded font-semibold transition-colors"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setEditingUserId(null)}
                              className="px-3 py-1 bg-slate-600 hover:bg-slate-700 text-white text-xs rounded transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                setEditingUserId(u.id);
                                setEditingRole(u.role);
                              }}
                              className="px-3 py-1 bg-aegis-primary hover:bg-aegis-primary/80 text-white text-xs rounded font-semibold transition-colors"
                            >
                              Edit
                            </button>
                            {currentUser?.id !== u.id && (
                              <button
                                onClick={() => handleDeleteUser(u.id)}
                                disabled={deleting}
                                className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:bg-red-600/50 text-white text-xs rounded font-semibold transition-colors"
                              >
                                Delete
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer Stats */}
        {!loadingUsers && users.length > 0 && (
          <div className="mt-6 p-4 bg-slate-900/50 border border-slate-800 rounded-lg text-sm text-aegis-muted">
            Total Users: {users.length} • Admins: {users.filter(u => u.role === 'admin').length} • Auditors: {users.filter(u => u.role === 'auditor').length}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-8 p-6 bg-slate-900/50 border border-slate-800 rounded-lg">
          <h3 className="text-aegis-primary font-semibold mb-3">Role Descriptions</h3>
          <ul className="text-sm text-aegis-muted space-y-2">
            <li>
              <span className="font-bold text-red-400">Admin:</span> Full access to all features and user management
            </li>
            <li>
              <span className="font-bold text-yellow-400">Auditor:</span> Can view compliance reports and audit logs
            </li>
            <li>
              <span className="font-bold text-blue-400">Operator:</span> Can manage zones and sensors
            </li>
            <li>
              <span className="font-bold text-slate-400">Viewer:</span> Read-only access to dashboards
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export default function UserManagementPage() {
  return (
    <RoleBasedRoute requiredRole="admin">
      <UserManagementContent />
    </RoleBasedRoute>
  );
}
