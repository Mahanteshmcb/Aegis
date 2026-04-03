import useCurrentUser from '../hooks/useCurrentUser';

export default function Profile() {
  const { user, loading } = useCurrentUser();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-aegis-primary font-mono">
        Loading profile...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-red-400">
        Unable to load profile. Please login again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-white">Profile</h1>
          <p className="mt-2 text-sm text-aegis-muted">Your current operator identity and tenant details.</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl glass-card border border-slate-800 p-6">
          <h2 className="text-xl font-semibold text-white">Identity</h2>
          <div className="mt-6 space-y-4 text-sm text-aegis-muted">
            <div>
              <div className="text-xs uppercase tracking-[0.3em] text-aegis-primary">Email</div>
              <div className="mt-1 text-white">{user.email}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.3em] text-aegis-primary">Role</div>
              <div className="mt-1 text-white">{user.role}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.3em] text-aegis-primary">Tenant</div>
              <div className="mt-1 text-white">{user.tenant_id}</div>
            </div>
          </div>
        </div>

        <div className="rounded-3xl glass-card border border-slate-800 p-6">
          <h2 className="text-xl font-semibold text-white">Access notes</h2>
          <p className="mt-4 text-sm text-aegis-muted">
            Roles are used to show user-specific actions inside the Aegis control plane. Administrators can see extra management tools.
          </p>
          <div className="mt-6 grid gap-4">
            <div className="rounded-3xl bg-[#0b1320] p-4 border border-slate-800">
              <div className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Active scope</div>
              <div className="mt-2 text-white">Tenant {user.tenant_id} monitoring and compliance</div>
            </div>
            <div className="rounded-3xl bg-[#0b1320] p-4 border border-slate-800">
              <div className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Role privileges</div>
              <div className="mt-2 text-white">{user.role === 'ADMIN' ? 'Full admin console access' : 'Operator dashboards and sensor workflows'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
