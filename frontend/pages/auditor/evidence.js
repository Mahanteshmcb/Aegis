import RoleBasedRoute from '../../components/RoleBasedRoute';
import Link from 'next/link';

export default function EvidenceReviewPage() {
  return (
    <RoleBasedRoute requiredRole="auditor">
      <div className="min-h-[calc(100vh-4rem)] space-y-8">
        <div>
          <Link href="/auditor/reports" className="mb-6 inline-flex items-center gap-2 text-sm text-aegis-primary hover:text-sky-300">← Back to Reports</Link>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Evidence Review</h1>
          <p className="text-aegis-muted">Inspect immutably recorded events, blockchain references, and compliance evidence.</p>
        </div>

        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-8">
          <h2 className="text-lg font-semibold text-white mb-4">Evidence Overview</h2>
          <p className="text-aegis-muted text-sm mb-4">Detailed evidence logs are not yet connected to blockchain payloads in this prototype, but the reporting workflow is scaffolded for Day 1–50 integration.</p>
          <ul className="space-y-3 text-sm text-aegis-muted">
            <li>• Event hashes can be cross-referenced with audit records</li>
            <li>• Evidence statements remain read-only for compliance review</li>
            <li>• Admins and auditors can confirm system integrity</li>
          </ul>
        </div>
      </div>
    </RoleBasedRoute>
  );
}
