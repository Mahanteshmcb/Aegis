import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
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
      const resp = await fetch(`${API_URL}/api/v1/auth/users/${userId}/role`, {
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
      const resp = await fetch(`${API_URL}/api/v1/auth/users/${userId}`, {
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

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">User Management</h1>
          <p className="text-aegis-muted">Manage tenant users and role assignments.</p>
        </div>
        <button onClick={fetchUsers} className="px-5 py-3 rounded-2xl bg-aegis-primary text-white font-semibold hover:bg-sky-400 transition-all">Refresh</button>
      </div>

      {success && <div className="rounded-3xl border border-green-700 bg-green-900/20 p-4 text-green-300">{success}</div>}
      {error && <div className="rounded-3xl border border-red-700 bg-red-900/20 p-4 text-red-300">{error}</div>}

      <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
        <input type="text" placeholder="Search users by email..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary" />
      </div>

      <div className="rounded-3xl border border-slate-700 bg-slate-900/80 overflow-hidden">
        {loadingUsers ? (
          <div className="p-8 text-center text-aegis-muted">Loading users...</div>
        ) : users.filter((u) => !searchQuery || u.email.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 ? (
          <div className="p-8 text-center text-aegis-muted">{users.length === 0 ? 'No users found in your tenant.' : 'No users match your search.'}</div>
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
                {users.filter((u) => !searchQuery || u.email.toLowerCase().includes(searchQuery.toLowerCase())).map((u) => (
                  <tr key={u.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-3 font-mono text-aegis-text">{u.email}</td>
                    <td className="px-6 py-3">
                      {editingUserId === u.id ? (
                        <select value={editingRole} onChange={(e) => setEditingRole(e.target.value)} className="rounded-2xl border border-slate-700 bg-[#0f172a] px-3 py-2 text-white outline-none focus:border-aegis-primary">
                          {ROLES.map((role) => (<option key={role} value={role}>{role.toUpperCase()}</option>))}
                        </select>
                      ) : (
                        <span className={`inline-block rounded-full border px-3 py-1 text-xs font-semibold ${getRoleColor(u.role)}`}>{u.role?.toUpperCase()}</span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      {editingUserId === u.id ? (
                        <div className="flex flex-wrap gap-2">
                          <button onClick={() => handleUpdateRole(u.id, editingRole)} className="rounded-2xl bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-500 transition-all">Save</button>
                          <button onClick={() => setEditingUserId(null)} className="rounded-2xl border border-slate-700 px-3 py-1 text-xs text-white hover:border-aegis-primary transition-all">Cancel</button>
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          <button onClick={() => { setEditingUserId(u.id); setEditingRole(u.role); }} className="rounded-2xl bg-aegis-primary px-3 py-1 text-xs font-semibold text-white hover:bg-sky-400 transition-all">Edit</button>
                          {currentUser?.id !== u.id && (
                            <button onClick={() => handleDeleteUser(u.id)} disabled={deleting} className="rounded-2xl bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500 disabled:bg-red-600/50 transition-all">Delete</button>
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
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6 text-sm text-aegis-muted">
          Total Users: {users.length} • Admins: {users.filter((u) => u.role === 'admin').length} • Auditors: {users.filter((u) => u.role === 'auditor').length}
        </div>
      )}

      <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6 text-sm text-aegis-muted">
        <h2 className="text-aegis-primary font-semibold mb-3">Role Descriptions</h2>
        <ul className="space-y-2">
          <li><span className="font-bold text-red-400">Admin:</span> Full access to all features and user management.</li>
          <li><span className="font-bold text-yellow-400">Auditor:</span> View compliance reports and audit logs.</li>
          <li><span className="font-bold text-blue-400">Operator:</span> Manage zones and sensors.</li>
          <li><span className="font-bold text-slate-400">Viewer:</span> Read-only dashboard access.</li>
        </ul>
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
