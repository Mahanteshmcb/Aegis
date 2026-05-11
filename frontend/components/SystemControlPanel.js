import Card from './Card';
import Button from './Button';

export default function SystemControlPanel({
  onBackup,
  onSyncCreate,
  onSyncComplete,
  onPauseFleet,
  onResumeFleet,
  onEmergencyStop,
  onToggleAnomaly,
  statusMessage,
  actionLoading,
  lastBackupSnapshot,
  lastSyncJob,
  anomalyMode,
  healthStatus,
  role,
}) {
  return (
    <Card title="System Control Panel">
      <p className="text-sm text-aegis-muted mb-4">
        Manage backup, sync, and robotic fleet control workflows from a single interface.
      </p>

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Button onClick={onBackup} disabled={actionLoading}>
          Start Backup
        </Button>
        <Button variant="secondary" onClick={onSyncCreate} disabled={actionLoading}>
          Create Sync Job
        </Button>
        <Button variant="primary" onClick={onSyncComplete} disabled={actionLoading || !lastSyncJob}>
          Complete Sync Job
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Button variant="secondary" onClick={onPauseFleet} disabled={actionLoading}>
          Pause Fleet
        </Button>
        <Button variant="secondary" onClick={onResumeFleet} disabled={actionLoading}>
          Resume Fleet
        </Button>
        <Button variant="danger" onClick={onEmergencyStop} disabled={actionLoading}>
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

      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" onClick={onToggleAnomaly} disabled={actionLoading}>
          {anomalyMode ? 'Return Nominal' : 'Trigger Anomaly'}
        </Button>
      </div>
    </Card>
  );
}
