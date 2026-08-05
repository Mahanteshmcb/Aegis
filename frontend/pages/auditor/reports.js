import RoleBasedRoute from '../../components/RoleBasedRoute';
import Link from 'next/link';

export default function AuditorReportsPage() {
  return (
    <RoleBasedRoute requiredRole="auditor">
      <div className="min-h-[calc(100vh-4rem)] space-y-8">
        <div>
          <Link href="/estate-dashboard" className="mb-6 inline-flex items-center gap-2 text-sm text-aegis-primary hover:text-sky-300">← Back to Estate Dashboard</Link>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Compliance Reports</h1>
          <p className="text-aegis-muted">Review audit findings, event summaries, and compliance status for tenant operations.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white mb-3">Current Compliance</h2>
            <p className="text-aegis-muted text-sm">No active compliance violations detected in the tenant audit trail.</p>
          </div>
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white mb-3">Recent Findings</h2>
            <ul className="space-y-2 text-sm text-aegis-muted">
              <li>• Zone integrity checks complete</li>
              <li>• Sensor connectivity stable</li>
              <li>• Emergency logs are clean</li>
            </ul>
          </div>
          <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white mb-3">Evidence Streams</h2>
            <p className="text-aegis-muted text-sm">Use the Evidence Review page to inspect detailed event and blockchain records.</p>
          </div>
        </div>
      </div>
    </RoleBasedRoute>
  );
}
