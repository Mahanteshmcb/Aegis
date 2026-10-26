import Card from './Card';
import Button from './Button';
import Link from 'next/link';

export default function SystemControlPanel({
  onBackup,
  onSyncCreate,
  onSyncComplete,
  onEmergencyStop,
  statusMessage,
  actionLoading,
  lastBackupSnapshot,
  lastSyncJob,
  healthStatus,
  role,
}) {
  const canOperate = ['admin', 'superadmin', 'manager', 'operator'].includes(String(role || '').toLowerCase());
  return (
    <Card title="System Control Panel">
      <p className="text-sm text-aegis-muted mb-4">
        Manage backup, sync, and robotic fleet control workflows from a single interface.
      </p>

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Button onClick={onBackup} disabled={actionLoading || !canOperate}>
          Start Backup
        </Button>
        <Button variant="secondary" onClick={onSyncCreate} disabled={actionLoading || !canOperate}>
          Create Sync Job
        </Button>
        <Button variant="primary" onClick={onSyncComplete} disabled={actionLoading || !canOperate || !lastSyncJob}>
          Complete Sync Job
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <div className="md:col-span-2 rounded-lg border border-slate-700 bg-slate-950/60 p-3 text-sm text-slate-300">
          Routine fleet missions and availability are managed on <Link className="text-cyan-300 underline" href="/robots-management">Robots</Link>.
        </div>
        <Button variant="danger" onClick={onEmergencyStop} disabled={actionLoading || !canOperate}>
          Emergency Stop
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <div className="rounded-xl bg-slate-950/70 border border-slate-700 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Last Backup Snapshot</p>
          <p className="mt-2 text-sm text-aegis-text">{lastBackupSnapshot?.snapshot_id || 'None yet'}</p>
          <p className="text-xs text-aegis-muted mt-1">{lastBackupSnapshot?.source || ''}</p>
        </div>

        <div className="rounded-xl bg-slate-950/70 border border-slate-700 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Last Sync Job</p>
          <p className="mt-2 text-sm text-aegis-text">{lastSyncJob?.sync_id || 'None yet'}</p>
          <p className="text-xs text-aegis-muted mt-1">{lastSyncJob?.status || ''}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <div className="rounded-xl bg-slate-950/70 border border-slate-700 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Backend Health</p>
          <p className="mt-2 text-lg font-semibold text-aegis-primary">{healthStatus}</p>
        </div>
        <div className="rounded-xl bg-slate-950/70 border border-slate-700 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Current Role</p>
          <p className="mt-2 text-lg font-semibold text-aegis-primary">{role || 'operator'}</p>
        </div>
      </div>

      <div className="mb-6 rounded-xl bg-slate-950/70 border border-slate-700 p-4">
        <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Status Message</p>
        <p className="mt-2 text-aegis-text font-medium">{statusMessage}</p>
      </div>

    </Card>
  );
}
