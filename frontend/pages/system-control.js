import { useEffect, useState } from 'react';
import Link from 'next/link';
import TacticalMap from '../components/TacticalMap';
import SystemControlPanel from '../components/SystemControlPanel';
import useCurrentUser from '../hooks/useCurrentUser';
import {
  createBackupSnapshot,
  createDataSyncJob,
  completeDataSyncJob,
  emergencyStop,
  fleetEmergencyStop,
  getSystemHealthStatus,
} from '../utils/api';

export default function SystemControl() {
  const { user, loading } = useCurrentUser();
  const [statusMessage, setStatusMessage] = useState('System control ready.');
  const [actionLoading, setActionLoading] = useState(false);
  const [anomalyMode, setAnomalyMode] = useState(false);
  const [lastSyncJob, setLastSyncJob] = useState(null);
  const [lastBackupSnapshot, setLastBackupSnapshot] = useState(null);
  const [healthStatus, setHealthStatus] = useState('Unknown');

  const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;

  useEffect(() => {
    if (!loading && token) {
      fetchHealthStatus();
    }
  }, [loading, token]);

  async function fetchHealthStatus() {
    try {
      const data = await getSystemHealthStatus(token);
      setHealthStatus(data.status || 'OK');
      setStatusMessage('Live connectivity verified.');
    } catch (error) {
      setHealthStatus('Unavailable');
      setStatusMessage('Unable to reach backend services.');
    }
  }

  async function triggerBackup() {
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Creating backup snapshot...');

    try {
      const backup = await createBackupSnapshot(token, {
        source: 'system_control',
        record_count: 42,
        data_hash: `system-control-${Date.now()}`,
        storage_uri: `local://system-control/backups/${Date.now()}`,
        status: 'created',
        integrity_verified: false,
        verification_notes: 'Triggered from system control UI',
      });

      setLastBackupSnapshot(backup);
      setStatusMessage('Backup snapshot created successfully.');
    } catch (error) {
      setStatusMessage('Backup creation failed.');
    } finally {
      setActionLoading(false);
    }
  }

  async function createSyncJob() {
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Creating sync job...');

    try {
      const job = await createDataSyncJob(token, {
        source_system: 'system_control',
        target_system: 'archive_gateway',
        status: 'pending',
        attempt_count: 0,
        payload_hash: `sync-control-${Date.now()}`,
        result_summary: 'Awaiting execution',
      });

      setLastSyncJob(job);
      setStatusMessage('Data sync job created successfully.');
    } catch (error) {
      setStatusMessage('Sync job creation failed.');
    } finally {
      setActionLoading(false);
    }
  }

  async function completeSyncJob() {
    if (!token || !lastSyncJob) return;
    setActionLoading(true);
    setStatusMessage('Completing sync job...');

    try {
      const completedJob = await completeDataSyncJob(token, lastSyncJob.sync_id, {
        success: true,
        result_summary: 'Manual control completion',
        payload_hash: lastSyncJob.payload_hash,
      });

      setLastSyncJob(completedJob);
      setStatusMessage('Sync job completed successfully.');
    } catch (error) {
      setStatusMessage('Sync job completion failed.');
    } finally {
      setActionLoading(false);
    }
  }

  async function pauseFleet() {
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Pausing fleet...');

    try {
      const result = await fleetEmergencyStop(token, {
        reason: 'Pause fleet from system control',
      });
      setStatusMessage(`Fleet pause issued: ${result.reason}`);
    } catch (error) {
      setStatusMessage('Fleet pause failed.');
    } finally {
      setActionLoading(false);
    }
  }

  async function resumeFleet() {
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Resuming fleet...');

    try {
      const result = await fleetEmergencyStop(token, {
        reason: 'Resume fleet from system control',
      });
      setStatusMessage(`Fleet resume issued: ${result.reason}`);
    } catch (error) {
      setStatusMessage('Fleet resume failed.');
    } finally {
      setActionLoading(false);
    }
  }

  async function emergencyStopCommand() {
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Issuing emergency stop...');

    try {
      const result = await emergencyStop(token, {
        robot_id: 'fleet',
        robot_type: 'AEGIS_ROVER',
      });
      setStatusMessage(result.message || 'Emergency stop issued.');
    } catch (error) {
      setStatusMessage('Emergency stop failed.');
    } finally {
      setActionLoading(false);
    }
  }

  const toggleAnomaly = () => {
    setAnomalyMode(!anomalyMode);
    setStatusMessage(anomalyMode ? 'Visualization returned to nominal state.' : 'Anomaly mode activated.');
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="text-aegis-muted animate-pulse">Loading system control...</div>
      </div>
    );
  }

  return (
    <>
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">System Control</h1>
        <p className="text-aegis-muted max-w-2xl">
          Operational control panels for robotic fleet coordination, backup orchestration, and tactical visualization.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.55fr_1fr]">
        <div className="space-y-6">
          <SystemControlPanel
            onBackup={triggerBackup}
            onSyncCreate={createSyncJob}
            onSyncComplete={completeSyncJob}
            onPauseFleet={pauseFleet}
            onResumeFleet={resumeFleet}
            onEmergencyStop={emergencyStopCommand}
            onToggleAnomaly={toggleAnomaly}
            statusMessage={statusMessage}
            actionLoading={actionLoading}
            lastBackupSnapshot={lastBackupSnapshot}
            lastSyncJob={lastSyncJob}
            anomalyMode={anomalyMode}
            healthStatus={healthStatus}
            role={user?.role}
          />
        </div>

        <div className="space-y-6">
          <div className="rounded-xl overflow-hidden border border-slate-700">
            <TacticalMap anomaly={anomalyMode} />
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-aegis-primary mb-4">Action Reference</h2>
            <p className="text-sm text-aegis-muted mb-3">
              Use this control surface to validate Day 50 system control workflows and demonstrate live operator interactions.
            </p>
            <ul className="space-y-3 text-sm text-aegis-text">
              <li>• Start backup snapshots and keep the audit trail intact.</li>
              <li>• Create and complete sync jobs from a single console.</li>
              <li>• Simulate fleet control and anomaly awareness.</li>
            </ul>
            <div className="mt-6">
              <Link href="/dashboard" className="text-aegis-primary text-sm font-semibold hover:text-aegis-accent">
                ← Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
