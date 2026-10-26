import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import Layout3D from '../../components/Layout3D';
import { ShieldCheck, UserCog, ClipboardList, Eye, Plus, Trash2 } from 'lucide-react';
import useCurrentUser from '../../hooks/useCurrentUser';

const BUILTIN_ROLE_ICONS = {
  admin: UserCog,
  superadmin: UserCog,
  operator: ShieldCheck,
  auditor: ClipboardList,
  viewer: Eye,
};
const EDITABLE_PERMISSIONS = [
  ['users.manage', 'Manage tenant users'],
  ['zones.manage', 'Manage zones'],
  ['devices.manage', 'Manage digital-twin devices'],
  ['devices.control', 'Control devices'],
  ['alerts.manage', 'Manage alert delivery'],
  ['audit.read', 'Review audit records'],
];
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

function emptyForm() {
  return { key: '', name: '', description: '', permissions: [] };
}

export default function RoleManagement() {
  const { user, token, loading } = useCurrentUser();
  const [roles, setRoles] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const fetchRoles = useCallback(async () => {
    if (!token) return;
    const response = await fetch(`${API_URL}/api/v1/roles`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || 'Unable to load roles.');
    setRoles(Array.isArray(result.data) ? result.data : []);
  }, [token]);

  useEffect(() => {
    if (!loading && token) {
      fetchRoles().catch((fetchError) => setError(fetchError.message));
    }
  }, [fetchRoles, loading, token]);

  async function saveRole(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const response = await fetch(`${API_URL}/api/v1/roles`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to create role.');
      setForm(emptyForm());
      setShowForm(false);
      setNotice('Custom role created.');
      await fetchRoles();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setBusy(false);
    }
  }

  async function deleteRole(role) {
    if (!window.confirm(`Delete role "${role.name}"? Users assigned to it must be reassigned first.`)) return;
    setError('');
    setNotice('');
    try {
      const response = await fetch(`${API_URL}/api/v1/roles/${role.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to delete role.');
      setNotice('Role deleted.');
      await fetchRoles();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  }

  function updatePermission(permission) {
    setForm((current) => ({
      ...current,
      permissions: current.permissions.includes(permission)
        ? current.permissions.filter((item) => item !== permission)
        : [...current.permissions, permission],
    }));
  }

  if (loading) {
    return <Layout3D title="System Roles" icon="👥" subtitle="Checking permissions"><p className="text-slate-400">Loading role access...</p></Layout3D>;
  }

  if (!['admin', 'superadmin'].includes(String(user?.role || '').toLowerCase())) {
    return (
      <Layout3D title="System Roles" icon="👥" subtitle="Access restricted">
        <div role="alert" className="rounded border border-red-700 bg-red-950/30 p-5 text-red-200">Administrator access is required to manage role definitions.</div>
      </Layout3D>
    );
  }

  return (
    <Layout3D title="System Roles" icon="👥" subtitle="Tenant-scoped access definitions">
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Available roles</h2>
            <p className="mt-1 text-sm text-slate-400">Custom role permissions are persisted and checked by the API on each request.</p>
          </div>
          <div className="flex gap-3">
            <Link href="/admin/users" className="rounded border border-cyan-600/50 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-900/30">Manage user assignments</Link>
            <button type="button" onClick={() => setShowForm((shown) => !shown)} className="flex items-center gap-2 rounded bg-cyan-700 px-4 py-2 text-sm text-white hover:bg-cyan-600"><Plus size={16} />{showForm ? 'Cancel' : 'Create role'}</button>
          </div>
        </div>
        {error && <p role="alert" className="rounded border border-red-700 p-3 text-red-200">{error}</p>}
        {notice && <p role="status" className="rounded border border-emerald-700 p-3 text-emerald-200">{notice}</p>}
        {showForm && (
          <form onSubmit={saveRole} className="grid gap-4 rounded border border-slate-800 p-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm text-slate-300">Role key
                <input required pattern="[a-z][a-z0-9_-]{1,49}" maxLength={50} value={form.key} onChange={(event) => setForm({ ...form, key: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
              </label>
              <label className="text-sm text-slate-300">Display name
                <input required maxLength={100} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
              </label>
            </div>
            <label className="text-sm text-slate-300">Description
              <input maxLength={500} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </label>
            <fieldset className="grid gap-2 sm:grid-cols-2">
              <legend className="mb-2 text-sm font-semibold text-slate-200">Permissions</legend>
              {EDITABLE_PERMISSIONS.map(([permission, label]) => (
                <label key={permission} className="flex items-center gap-2 text-sm text-slate-300">
                  <input type="checkbox" checked={form.permissions.includes(permission)} onChange={() => updatePermission(permission)} />
                  {label}
                </label>
              ))}
            </fieldset>
            <button type="submit" disabled={busy} className="w-fit rounded bg-cyan-700 px-4 py-2 text-sm text-white disabled:opacity-50">{busy ? 'Saving...' : 'Save role'}</button>
          </form>
        )}
        <div className="divide-y divide-slate-800 border-y border-slate-800">
          {roles.map((role) => {
            const Icon = BUILTIN_ROLE_ICONS[role.key] || ShieldCheck;
            return (
              <article key={role.key} className="grid gap-3 py-5 sm:grid-cols-[12rem_minmax(0,1fr)_auto] sm:items-center">
                <div className="flex items-center gap-3">
                  <Icon className="h-5 w-5 text-cyan-300" aria-hidden="true" />
                  <div><h3 className="font-semibold text-white">{role.name}</h3><span className="text-xs text-slate-500">{role.key}</span></div>
                </div>
                <div>
                  <p className="text-sm text-slate-400">{role.description || 'No description'}</p>
                  <p className="mt-1 text-xs text-cyan-200">{(role.permissions || []).join(', ') || 'No permissions'}</p>
                </div>
                {role.built_in ? <span className="w-fit rounded border border-slate-700 px-2 py-1 text-xs uppercase text-slate-300">Built-in</span> : (
                  <button type="button" aria-label={`Delete ${role.name}`} onClick={() => deleteRole(role)} className="w-fit rounded border border-red-800 px-3 py-2 text-red-300 hover:bg-red-950"><Trash2 size={16} /></button>
                )}
              </article>
            );
          })}
          {!roles.length && <p className="py-6 text-slate-400">Loading roles...</p>}
        </div>
      </div>
    </Layout3D>
  );
}
