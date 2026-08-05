import { useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

export default function AiPage() {
  const { loading } = useCurrentUser();
  const [report, setReport] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateReport = async () => {
    setIsGenerating(true);
    setReport(null);
    await new Promise((resolve) => setTimeout(resolve, 900));
    setReport({
      summary: 'Vryndara analysis completed. No critical anomalies detected.',
      findings: ['Sensor network stable', 'Audit trail integrity preserved', 'No emergency states detected'],
      timestamp: new Date().toLocaleString(),
    });
    setIsGenerating(false);
  };

  if (loading) {
    return <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center text-aegis-muted">Loading AI workspace...</div>;
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">Vryndara AI</h1>
        <p className="text-aegis-muted max-w-2xl">A secure research dashboard for anomaly detection, audit intelligence, and threat modeling.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold text-aegis-primary mb-4">AI Summary</h2>
          <p className="text-aegis-muted text-sm">Generate intelligence reports based on the current sensor and audit state.</p>
          <button onClick={generateReport} disabled={isGenerating} className="mt-6 w-full rounded-2xl bg-aegis-primary px-5 py-3 text-white font-semibold hover:bg-sky-400 transition-all">{isGenerating ? 'Analyzing...' : 'Run Vryndara Audit'}</button>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold text-aegis-primary mb-4">Operational Focus</h2>
          <ul className="space-y-3 text-sm text-aegis-muted">
            <li>• High-fidelity sensor anomaly detection</li>
            <li>• Audit log correlation across zones</li>
            <li>• Threat scoring and evidence flags</li>
          </ul>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold text-aegis-primary mb-4">Notes</h2>
          <p className="text-aegis-muted text-sm">This workspace is designed for Day 1–50 research integration and is intentionally lightweight for early prototypes.</p>
        </div>
      </div>

      {report && (
        <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold text-aegis-primary mb-3">Latest Report</h2>
          <p className="text-slate-300 mb-4">{report.summary}</p>
          <div className="grid gap-3 sm:grid-cols-3">
            {report.findings.map((finding, index) => (
              <div key={index} className="rounded-2xl border border-slate-700 bg-[#0f172a] p-4 text-sm text-aegis-muted">{finding}</div>
            ))}
          </div>
          <p className="mt-4 text-xs uppercase text-slate-500">Generated {report.timestamp}</p>
        </div>
      )}

      <div className="rounded-3xl border border-slate-700 bg-slate-900/80 p-6 text-sm text-aegis-muted">
        <Link href="/estate-dashboard" className="text-aegis-primary hover:text-sky-300">← Back to Estate Dashboard</Link>
      </div>
    </div>
  );
}
