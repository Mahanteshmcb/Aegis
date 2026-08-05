import { useState } from 'react';
import { useRouter } from 'next/router';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function ProfilePage() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getRoleColor = (role) => {
    switch (role?.toLowerCase()) {
      case 'admin':
        return 'bg-red-900/30 border-red-700 text-red-400';
      case 'auditor':
        return 'bg-yellow-900/30 border-yellow-700 text-yellow-400';
      case 'operator':
        return 'bg-blue-900/30 border-blue-700 text-blue-400';
      case 'viewer':
        return 'bg-slate-900/30 border-slate-700 text-slate-400';
      default:
        return 'bg-slate-900/30 border-slate-700 text-slate-400';
    }
  };

  async function handleChangePassword(e) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('All fields are required');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }

    try {
      setIsSubmitting(true);
      const token = localStorage.getItem('aegis_token');
      const resp = await fetch(`${API_URL}/api/v1/auth/change-password`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });

      if (!resp.ok) {
        const errorData = await resp.json();
        throw new Error(errorData.detail || 'Failed to change password');
      }

      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => {
        setShowChangePassword(false);
        setSuccess(false);
      }, 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center text-aegis-muted">Loading profile...</div>;
  }

  if (!user) {
    return <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center text-red-400">Unable to load profile. Please login again.</div>;
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div>
        <button onClick={() => router.push('/estate-dashboard')} className="mb-6 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-2 text-aegis-primary hover:border-aegis-primary transition-all">← Back to Estate Dashboard</button>
        <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Profile</h1>
        <p className="text-aegis-muted">Manage your account settings and security posture.</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8">
            <h2 className="text-lg font-semibold text-aegis-primary mb-6">Account Identity</h2>
            <div className="space-y-6 text-sm text-aegis-muted">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">Email Address</p>
                <p className="text-white font-mono">{user.email}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">Role</p>
                <span className={`inline-flex rounded-full border px-4 py-2 text-sm font-semibold ${getRoleColor(user.role)}`}>
                  {user.role?.toUpperCase()}
                </span>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">Tenant ID</p>
                <p className="text-white font-mono">{user.tenant_id}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">User ID</p>
                <p className="text-white font-mono text-sm">{user.id}</p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8">
            <h2 className="text-lg font-semibold text-aegis-primary mb-6">Access & Permissions</h2>
            <div className="space-y-4 text-sm text-aegis-muted">
              <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                <p className="font-semibold text-white mb-2">Active Scope</p>
                <p>Tenant {user.tenant_id} monitoring and compliance operations</p>
              </div>
              <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                <p className="font-semibold text-white mb-2">Role Privileges</p>
                <p>
                  {user.role?.toLowerCase() === 'admin'
                    ? 'Full administrative access to console and user management'
                    : user.role?.toLowerCase() === 'auditor'
                    ? 'View compliance reports, audit logs, and system health'
                    : user.role?.toLowerCase() === 'operator'
                    ? 'Manage zones, sensors, and operational workflows'
                    : 'Read-only access to dashboards and reports'}
                </p>
              </div>
              <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                <p className="font-semibold text-white mb-2">Multi-Tenant Isolation</p>
                <p>Your data is completely isolated within Tenant {user.tenant_id}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8">
            <h2 className="text-lg font-semibold text-aegis-primary mb-4">Security</h2>
            {!showChangePassword && (
              <button onClick={() => setShowChangePassword(true)} className="rounded-2xl bg-aegis-primary px-4 py-2 text-sm font-semibold text-white hover:bg-sky-400 transition-all">Change Password</button>
            )}
          </div>
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8">
            {showChangePassword ? (
              <form onSubmit={handleChangePassword} className="space-y-4">
                {error && <div className="rounded-2xl border border-red-700 bg-red-900/20 p-3 text-red-300">{error}</div>}
                {success && <div className="rounded-2xl border border-green-700 bg-green-900/20 p-3 text-green-300">Password changed successfully!</div>}
                <div>
                  <label className="block text-sm text-aegis-muted mb-2">Current Password</label>
                  <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary" />
                </div>
                <div>
                  <label className="block text-sm text-aegis-muted mb-2">New Password</label>
                  <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary" />
                </div>
                <div>
                  <label className="block text-sm text-aegis-muted mb-2">Confirm New Password</label>
                  <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full rounded-2xl border border-slate-700 bg-[#0f172a] px-4 py-3 text-white outline-none focus:border-aegis-primary" />
                </div>
                <div className="flex flex-wrap gap-3">
                  <button type="submit" disabled={isSubmitting} className="rounded-2xl bg-green-600 px-6 py-3 text-white font-semibold hover:bg-green-500 transition-all">{isSubmitting ? 'Saving...' : 'Save Password'}</button>
                  <button type="button" onClick={() => { setShowChangePassword(false); setError(null); }} className="rounded-2xl border border-slate-700 px-6 py-3 text-slate-300 hover:border-aegis-primary transition-all">Cancel</button>
                </div>
              </form>
            ) : (
              <div className="space-y-4 text-sm text-aegis-muted">
                <p>Secure your account by keeping your passphrase unique and complex.</p>
                <p className="text-slate-500">Password rotation is recommended every 90 days.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
