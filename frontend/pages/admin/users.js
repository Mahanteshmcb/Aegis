import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Plus, Edit2, Trash2, X, Check, Mail, Key, Shield, AlertCircle } from 'lucide-react';
import RoleBasedRoute from '../../components/RoleBasedRoute';
import useCurrentUser from '../../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const ROLE_PERMISSIONS = {
  admin: {
    name: 'Administrator',
    color: 'red',
    permissions: ['All Features', 'User Management', 'System Control', 'Audit Logs', 'Settings'],
    description: 'Full administrative access to all system features',
  },
  auditor: {
    name: 'Auditor',
    color: 'yellow',
    permissions: ['View Audit Logs', 'View Reports', 'View Compliance', 'Export Data'],
    description: 'Access to compliance and audit functionality',
  },
  operator: {
    name: 'Operator',
    color: 'blue',
    permissions: ['Zone Management', 'Sensor Management', 'Fleet Control', 'Dashboard'],
    description: 'Manage zones, sensors, and robots',
  },
  viewer: {
    name: 'Viewer',
    color: 'slate',
    permissions: ['View Dashboard', 'View Reports', 'View Sensors', 'View Zones'],
    description: 'Read-only access to monitoring dashboards',
  },
};

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
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUserData, setNewUserData] = useState({ email: '', password: '', role: 'operator' });
  const [creatingUser, setCreatingUser] = useState(false);
  const [createError, setCreateError] = useState(null);

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
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
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
      const resp = await fetch(`${API_URL}/api/v1/users/${userId}/role`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
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
    const user = users.find((u) => u.id === userId);
    if (!window.confirm(`Are you sure you want to delete ${user?.email}? This action cannot be undone.`)) {
      return;
    }

    try {
      setDeleting(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      });

      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }

      setSuccess('User deleted successfully');
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

  async function handleCreateUser() {
    try {
      // Validation
      if (!newUserData.email?.trim()) {
        setCreateError('Email is required');
        return;
      }
      if (!newUserData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        setCreateError('Please enter a valid email address');
        return;
      }
      if (!newUserData.password || newUserData.password.length < 6) {
        setCreateError('Password must be at least 6 characters');
        return;
      }
      if (!newUserData.role) {
        setCreateError('Please select a role');
        return;
      }

      setCreatingUser(true);
      setCreateError(null);
      const token = localStorage.getItem('aegis_token');
      
      if (!token) {
        setCreateError('Session expired. Please log in again.');
        setCreatingUser(false);
        return;
      }

      const resp = await fetch(`${API_URL}/api/v1/auth/users`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: newUserData.email.toLowerCase().trim(),
          password: newUserData.password,
          role: newUserData.role,
        }),
      });

      // Log the response for debugging
      console.log('Create user response:', resp.status, resp.statusText);

      if (!resp.ok) {
        let errorMessage = 'Failed to create user';
        try {
          const errorData = await resp.json();
          console.log('Error data:', errorData);
          errorMessage = errorData.detail || errorData.message || errorData.error || `Error: ${resp.status} ${resp.statusText}`;
        } catch (e) {
          errorMessage = `Error: ${resp.status} ${resp.statusText}. Please check that the backend API is running.`;
        }
        throw new Error(errorMessage);
      }

      // Success
      const userData = await resp.json().catch(() => ({}));
      setSuccess(`✓ User ${newUserData.email} created successfully as ${newUserData.role.toUpperCase()}`);
      setTimeout(() => setSuccess(null), 4000);
      setNewUserData({ email: '', password: '', role: 'operator' });
      setShowCreateModal(false);
      setCreateError(null);
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      setCreateError(error.message || 'Failed to create user. Please check the connection.');
    } finally {
      setCreatingUser(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">User Management</h1>
          <p className="text-aegis-muted">Manage tenant users, roles, and permissions.</p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <button 
            onClick={() => setShowCreateModal(true)} 
            className="px-5 py-3 rounded-2xl bg-green-600 text-white font-semibold hover:bg-green-700 transition-all flex items-center gap-2"
          >
            <Plus size={18} /> Create User
          </button>
          <button 
            onClick={fetchUsers} 
            className="px-5 py-3 rounded-2xl bg-aegis-primary text-white font-semibold hover:bg-sky-400 transition-all"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* User Creation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black backdrop-blur-md flex items-center justify-center p-4" onClick={() => { setShowCreateModal(false); setCreateError(null); }}>
          <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-700 rounded-lg max-w-md w-full p-6 space-y-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-cyan-300 tracking-wide">Create New User</h2>
              <button 
                onClick={() => { setShowCreateModal(false); setCreateError(null); }} 
                className="text-slate-400 hover:text-cyan-300 transition-colors p-1"
              >
                <X size={24} />
              </button>
            </div>

            {createError && (
              <div className="p-4 bg-red-950/40 border border-red-700/60 rounded-lg text-red-200 text-sm font-semibold flex items-start gap-3">
                <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
                <span>{createError}</span>
              </div>
            )}

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-cyan-100 mb-2 flex items-center gap-2">
                  <Mail size={16} className="text-cyan-400" /> Email Address *
                </label>
                <input 
                  type="email" 
                  placeholder="user@example.com"
                  value={newUserData.email}
                  onChange={(e) => setNewUserData({ ...newUserData, email: e.target.value })}
                  className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-cyan-100 mb-2 flex items-center gap-2">
                  <Key size={16} className="text-cyan-400" /> Password *
                </label>
                <input 
                  type="password" 
                  placeholder="Minimum 6 characters"
                  value={newUserData.password}
                  onChange={(e) => setNewUserData({ ...newUserData, password: e.target.value })}
                  className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-cyan-100 mb-2 flex items-center gap-2">
                  <Shield size={16} className="text-cyan-400" /> Role *
                </label>
                <select 
                  value={newUserData.role}
                  onChange={(e) => setNewUserData({ ...newUserData, role: e.target.value })}
                  className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-600 rounded-lg text-white font-semibold focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 focus:outline-none transition-all"
                >
                  {ROLES.map((role) => (
                    <option key={role} value={role} className="bg-slate-900 text-white">
                      {ROLE_PERMISSIONS[role].name}
                    </option>
                  ))}
                </select>
                {newUserData.role && (
                  <p className="mt-2 text-xs text-slate-300 italic">
                    ℹ️ {ROLE_PERMISSIONS[newUserData.role].description}
                  </p>
                )}
              </div>
            </div>

            <div className="flex gap-3 pt-4 border-t border-slate-700">
              <button 
                onClick={handleCreateUser}
                disabled={creatingUser}
                className="flex-1 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-700 disabled:bg-cyan-600/50 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg"
              >
                <Check size={18} /> 
                {creatingUser ? 'Creating User...' : 'Create User'}
              </button>
              <button 
                onClick={() => { setShowCreateModal(false); setCreateError(null); }}
                disabled={creatingUser}
                className="flex-1 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {success && <div className="rounded-lg border border-green-700 bg-green-900/20 p-4 text-green-300 text-sm">{success}</div>}
      {error && <div className="rounded-lg border border-red-700 bg-red-900/20 p-4 text-red-300 text-sm">{error}</div>}

      <div className="rounded-lg border border-slate-700 bg-slate-900/80 p-6">
        <input 
          type="text" 
          placeholder="Search users by email..." 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-aegis-primary placeholder-slate-500"
        />
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-900/80 overflow-hidden">
        {loadingUsers ? (
          <div className="p-8 text-center text-aegis-muted">Loading users...</div>
        ) : users.filter((u) => !searchQuery || u.email.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 ? (
          <div className="p-8 text-center text-aegis-muted">{users.length === 0 ? 'No users found. Create one to get started.' : 'No users match your search.'}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-700 bg-slate-800/50">
                <tr>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Email</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Role</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Permissions</th>
                  <th className="px-6 py-3 font-semibold text-aegis-primary">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.filter((u) => !searchQuery || u.email.toLowerCase().includes(searchQuery.toLowerCase())).map((u) => (
                  <tr key={u.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-3 font-mono text-aegis-text">{u.email}</td>
                    <td className="px-6 py-3">
                      {editingUserId === u.id ? (
                        <select 
                          value={editingRole} 
                          onChange={(e) => setEditingRole(e.target.value)} 
                          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-aegis-primary"
                        >
                          {ROLES.map((role) => (
                            <option key={role} value={role}>{ROLE_PERMISSIONS[role].name}</option>
                          ))}
                        </select>
                      ) : (
                        <span className={`inline-block rounded-full border px-3 py-1 text-xs font-semibold ${getRoleColor(u.role)}`}>
                          {ROLE_PERMISSIONS[u.role]?.name || u.role?.toUpperCase()}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex flex-wrap gap-1">
                        {ROLE_PERMISSIONS[u.role]?.permissions.slice(0, 2).map((perm, idx) => (
                          <span key={idx} className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">
                            {perm}
                          </span>
                        ))}
                        {ROLE_PERMISSIONS[u.role]?.permissions.length > 2 && (
                          <span className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded">
                            +{ROLE_PERMISSIONS[u.role].permissions.length - 2} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      {editingUserId === u.id ? (
                        <div className="flex flex-wrap gap-2">
                          <button 
                            onClick={() => handleUpdateRole(u.id, editingRole)} 
                            className="rounded-lg bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-500 transition-all flex items-center gap-1"
                          >
                            <Check size={14} /> Save
                          </button>
                          <button 
                            onClick={() => setEditingUserId(null)} 
                            className="rounded-lg border border-slate-700 px-3 py-1 text-xs text-white hover:border-aegis-primary transition-all"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          <button 
                            onClick={() => { setEditingUserId(u.id); setEditingRole(u.role); }} 
                            className="rounded-lg bg-aegis-primary px-3 py-1 text-xs font-semibold text-white hover:bg-sky-400 transition-all flex items-center gap-1"
                          >
                            <Edit2 size={14} /> Edit
                          </button>
                          {currentUser?.id !== u.id && (
                            <button 
                              onClick={() => handleDeleteUser(u.id)} 
                              disabled={deleting} 
                              className="rounded-lg bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500 disabled:bg-red-600/50 transition-all flex items-center gap-1"
                            >
                              <Trash2 size={14} /> Delete
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

      {!loadingUsers && users.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-lg border border-slate-700 bg-slate-900/80 p-4">
            <p className="text-xs text-slate-400 uppercase">Total Users</p>
            <p className="text-2xl font-bold text-white mt-2">{users.length}</p>
          </div>
          <div className="rounded-lg border border-red-700/30 bg-red-900/10 p-4">
            <p className="text-xs text-red-300 uppercase">Admins</p>
            <p className="text-2xl font-bold text-red-300 mt-2">{users.filter((u) => u.role === 'admin').length}</p>
          </div>
          <div className="rounded-lg border border-yellow-700/30 bg-yellow-900/10 p-4">
            <p className="text-xs text-yellow-300 uppercase">Auditors</p>
            <p className="text-2xl font-bold text-yellow-300 mt-2">{users.filter((u) => u.role === 'auditor').length}</p>
          </div>
          <div className="rounded-lg border border-blue-700/30 bg-blue-900/10 p-4">
            <p className="text-xs text-blue-300 uppercase">Operators</p>
            <p className="text-2xl font-bold text-blue-300 mt-2">{users.filter((u) => u.role === 'operator').length}</p>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-slate-700 bg-slate-900/80 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-aegis-primary">Role Permission Guide</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(ROLE_PERMISSIONS).map(([roleKey, roleData]) => (
            <div key={roleKey} className={`rounded-lg border border-${roleData.color}-700/30 bg-${roleData.color}-900/10 p-4`}>
              <h3 className={`font-semibold text-${roleData.color}-300 mb-2`}>{roleData.name}</h3>
              <p className="text-xs text-slate-300 mb-3">{roleData.description}</p>
              <ul className="text-xs text-slate-400 space-y-1">
                {roleData.permissions.map((perm, idx) => (
                  <li key={idx}>✓ {perm}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
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
