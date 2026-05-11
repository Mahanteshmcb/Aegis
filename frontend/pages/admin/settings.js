import RoleBasedRoute from '../../components/RoleBasedRoute';
import Link from 'next/link';

export default function TenantSettingsPage() {
  return (
    <RoleBasedRoute requiredRole="admin">
      <div className="min-h-[calc(100vh-4rem)] space-y-8">
        <div>
          <Link href="/admin/users" className="mb-6 inline-flex items-center gap-2 text-sm text-aegis-primary hover:text-sky-300">← Back to User Management</Link>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Tenant Settings</h1>
          <p className="text-aegis-muted">Manage tenant-wide policies, audit retention, and operational parameters.</p>
        </div>

        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8 space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-white mb-3">Audit Retention</h2>
            <p className="text-aegis-muted">Configure how long events and logs are retained for tenant compliance.</p>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white mb-3">Access Policies</h2>
            <p className="text-aegis-muted">Define tenant access policies, role restrictions, and emergency escalation rules.</p>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white mb-3">Integration Endpoints</h2>
            <p className="text-aegis-muted">Manage external connectors, telemetry feeds, and blockchain gateways.</p>
          </div>
        </div>
      </div>
    </RoleBasedRoute>
  );
}
