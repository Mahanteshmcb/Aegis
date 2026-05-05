import { useState } from 'react';
import { useRouter } from 'next/router';
import Sidebar from '../components/Sidebar';
import ProtectedRoute from '../components/ProtectedRoute';
import useCurrentUser from '../hooks/useCurrentUser';

function ProfileContent() {
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
      const resp = await fetch('http://localhost:8001/api/v1/auth/change-password', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
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
    return (
      <div className="flex min-h-screen bg-[#0b1120]">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <div className="text-aegis-muted">Loading profile...</div>
        </main>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen bg-[#0b1120]">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <div className="text-red-400">Unable to load profile. Please login again.</div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#0b1120]">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="mb-6 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-aegis-primary rounded-lg transition-colors duration-200 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Profile</h1>
          <p className="text-aegis-muted">Manage your account settings and preferences</p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Left Column - Profile Info */}
          <div className="lg:col-span-2 space-y-6">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-8">
            <h2 className="text-lg font-semibold text-aegis-primary mb-6">Account Identity</h2>
            <div className="space-y-6">
              <div>
                <p className="text-xs text-aegis-muted font-semibold uppercase tracking-[0.15em] mb-2">
                  Email Address
                </p>
                <p className="text-lg text-white font-mono">{user.email}</p>
              </div>
              <div>
                <p className="text-xs text-aegis-muted font-semibold uppercase tracking-[0.15em] mb-2">
                  Role
                </p>
                <div>
                  <span className={`inline-block px-4 py-2 rounded-full border font-bold text-sm ${getRoleColor(user.role)}`}>
                    {user.role?.toUpperCase()}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-xs text-aegis-muted font-semibold uppercase tracking-[0.15em] mb-2">
                  Tenant ID
                </p>
                <p className="text-white font-mono">{user.tenant_id}</p>
              </div>
              <div>
                <p className="text-xs text-aegis-muted font-semibold uppercase tracking-[0.15em] mb-2">
                  User ID
                </p>
                <p className="text-white font-mono text-sm">{user.id}</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-8">
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

        {/* Security Settings */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-aegis-primary">Security</h2>
            {!showChangePassword && (
              <button
                onClick={() => setShowChangePassword(true)}
                className="px-4 py-2 bg-aegis-primary hover:bg-aegis-primary/80 text-white rounded-lg font-semibold text-sm transition-all"
              >
                Change Password
              </button>
            )}
          </div>

          {showChangePassword ? (
            <form onSubmit={handleChangePassword} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}
              {success && (
                <div className="p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-400 text-sm">
                  Password changed successfully!
                </div>
              )}
              <div>
                <label className="block text-sm text-aegis-muted font-semibold mb-2">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter your current password"
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-aegis-muted font-semibold mb-2">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password (min 8 characters)"
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-aegis-muted font-semibold mb-2">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-aegis-primary focus:outline-none"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 text-white rounded-lg font-semibold text-sm"
                >
                  {isSubmitting ? 'Updating...' : 'Update Password'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowChangePassword(false);
                    setCurrentPassword('');
                    setNewPassword('');
                    setConfirmPassword('');
                    setError(null);
                    setSuccess(false);
                  }}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold text-sm"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <p className="text-sm text-aegis-muted">
              Keep your account secure by changing your password regularly. Use a strong password with a mix of letters, numbers, and special characters.
            </p>
          )}
        </div>

        {/* Role Descriptions */}
        <div className="mt-8 p-6 bg-slate-900/50 border border-slate-800 rounded-lg">
          <h3 className="text-aegis-primary font-semibold mb-4">Role Descriptions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-red-900/20 border border-red-700/30 rounded-lg">
              <p className="font-bold text-red-400 mb-1">Admin</p>
              <p className="text-aegis-muted">Full access to all features, user management, and system configuration</p>
            </div>
            <div className="p-4 bg-yellow-900/20 border border-yellow-700/30 rounded-lg">
              <p className="font-bold text-yellow-400 mb-1">Auditor</p>
              <p className="text-aegis-muted">Can view compliance reports, audit logs, and monitoring dashboards</p>
            </div>
            <div className="p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
              <p className="font-bold text-blue-400 mb-1">Operator</p>
              <p className="text-aegis-muted">Can manage zones, sensors, and handle operational workflows</p>
            </div>
            <div className="p-4 bg-slate-900/20 border border-slate-700/30 rounded-lg">
              <p className="font-bold text-slate-400 mb-1">Viewer</p>
              <p className="text-aegis-muted">Read-only access to dashboards and system information</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
