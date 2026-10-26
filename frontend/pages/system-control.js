import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, CheckCircle, Clock, Zap, AlertTriangle } from 'lucide-react';
import SystemControlPanel from '../components/SystemControlPanel';
import useCurrentUser from '../hooks/useCurrentUser';
import {
  createEstateStateSnapshot,
  createDataSyncJob,
  completeDataSyncJob,
  fleetEmergencyStop,
  getSystemHealthStatus,
} from '../utils/api';

export default function SystemControl() {
  const { user, loading, token } = useCurrentUser();
  const [statusMessage, setStatusMessage] = useState('System control ready.');
  const [statusType, setStatusType] = useState('info'); // info, success, warning, error
  const [actionLoading, setActionLoading] = useState(false);
  const [lastSyncJob, setLastSyncJob] = useState(null);
  const [lastBackupSnapshot, setLastBackupSnapshot] = useState(null);
  const [healthStatus, setHealthStatus] = useState('Checking');
  const [operationHistory, setOperationHistory] = useState([]);
  const [estateDevices, setEstateDevices] = useState([]);
  const [snapshotUpdatedAt, setSnapshotUpdatedAt] = useState(null);
  const [snapshotError, setSnapshotError] = useState('');

  const canOperate = ['admin', 'superadmin', 'manager', 'operator'].includes(String(user?.role || '').toLowerCase());

  const fetchHealthStatus = useCallback(async () => {
    if (!token) return;
    try {
      const data = await getSystemHealthStatus(token);
      setHealthStatus(data?.status || 'Unknown');
    } catch (error) {
      setHealthStatus('Unavailable');
    }
  }, [token]);

  const fetchEstateSnapshot = useCallback(async () => {
    if (!token) return;
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/digital-twin/devices`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => []);
      if (!response.ok) throw new Error(result.detail || 'Unable to load tenant asset status.');
      setEstateDevices(Array.isArray(result) ? result : []);
      setSnapshotUpdatedAt(new Date());
      setSnapshotError('');
    } catch (error) {
      setSnapshotError(error.message || 'Unable to load tenant asset status.');
    }
  }, [token]);

  useEffect(() => {
    if (loading || !token) return undefined;
    fetchHealthStatus();
    fetchEstateSnapshot();
    const interval = window.setInterval(() => {
      fetchHealthStatus();
      fetchEstateSnapshot();
    }, 30000);
    return () => window.clearInterval(interval);
  }, [loading, token, fetchHealthStatus, fetchEstateSnapshot]);

  function addToHistory(action, result, status) {
    const newEntry = { action, result, status, timestamp: new Date() };
    setOperationHistory((prev) => [newEntry, ...prev.slice(0, 9)]); // Keep last 10
  }

  async function triggerBackup() {
    if (!window.confirm('Create a system backup? This may take a few moments.')) return;
    
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Creating backup snapshot...');
    setStatusType('info');

    try {
      const backup = await createEstateStateSnapshot(token, 'System Control recovery snapshot');

      if (backup) {
        setLastBackupSnapshot(backup);
      }
      setStatusMessage('✓ Backup snapshot created successfully.');
      setStatusType('success');
      addToHistory('Backup Creation', `Snapshot ID: ${backup?.snapshot_id || 'N/A'}`, 'success');
    } catch (error) {
      setStatusMessage('✗ Backup creation failed: ' + (error.message || 'Unknown error'));
      setStatusType('error');
      addToHistory('Backup Creation', error.message, 'error');
    } finally {
      setActionLoading(false);
    }
  }

  async function createSyncJob() {
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Creating sync job...');
    setStatusType('info');

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
      setStatusMessage('✓ Data sync job created successfully.');
      setStatusType('success');
      addToHistory('Sync Job Created', `Job ID: ${job?.sync_id || 'N/A'}`, 'success');
    } catch (error) {
      setStatusMessage('✗ Sync job creation failed: ' + (error.message || 'Unknown error'));
      setStatusType('error');
      addToHistory('Sync Job Creation', error.message, 'error');
    } finally {
      setActionLoading(false);
    }
  }

  async function completeSyncJob() {
    if (!lastSyncJob) {
      setStatusMessage('⚠ No sync job to complete.');
      setStatusType('warning');
      return;
    }
    
    if (!window.confirm(`Complete sync job ${lastSyncJob.sync_id}?`)) return;
    
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Completing sync job...');
    setStatusType('info');

    try {
      const completedJob = await completeDataSyncJob(token, lastSyncJob.sync_id, {
        success: true,
        result_summary: 'Manual control completion',
        payload_hash: lastSyncJob.payload_hash,
      });

      setLastSyncJob(completedJob);
      setStatusMessage('✓ Sync job completed successfully.');
      setStatusType('success');
      addToHistory('Sync Job Completed', `Job ${lastSyncJob.sync_id} finished`, 'success');
    } catch (error) {
      setStatusMessage('✗ Sync job completion failed: ' + (error.message || 'Unknown error'));
      setStatusType('error');
      addToHistory('Sync Job Completion', error.message, 'error');
    } finally {
      setActionLoading(false);
    }
  }

  async function emergencyStopCommand() {
    if (!window.confirm('⚠ EMERGENCY STOP: All robots will immediately halt. Continue?')) return;
    
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Issuing EMERGENCY STOP...');
    setStatusType('warning');

    try {
      const result = await fleetEmergencyStop(token, {
        reason: 'Fleet emergency stop from System Control',
      });
      setStatusMessage('🛑 EMERGENCY STOP activated - All robots halted immediately.');
      setStatusType('warning');
      addToHistory('EMERGENCY STOP', result.message || 'Fleet emergency stop activated', 'warning');
    } catch (error) {
      setStatusMessage('✗ Emergency stop command failed: ' + (error.message || 'Unknown error'));
      setStatusType('error');
      addToHistory('EMERGENCY STOP', error.message, 'error');
    } finally {
      setActionLoading(false);
    }
  }

  const getStatusIcon = (type) => {
    switch (type) {
      case 'success': return <CheckCircle className="text-green-400" size={20} />;
      case 'error': return <AlertCircle className="text-red-400" size={20} />;
      case 'warning': return <AlertTriangle className="text-yellow-400" size={20} />;
      default: return <Clock className="text-blue-400" size={20} />;
    }
  };

  const getStatusColor = (type) => {
    switch (type) {
      case 'success': return 'bg-green-900/20 border-green-700 text-green-300';
      case 'error': return 'bg-red-900/20 border-red-700 text-red-300';
      case 'warning': return 'bg-yellow-900/20 border-yellow-700 text-yellow-300';
      default: return 'bg-blue-900/20 border-blue-700 text-blue-300';
    }
  };

  const snapshotCounts = estateDevices.reduce((counts, device) => {
    const status = String(device.status || 'unknown').toLowerCase();
    counts.total += 1;
    counts[status === 'online' ? 'online' : status === 'offline' ? 'offline' : 'unknown'] += 1;
    return counts;
  }, { total: 0, online: 0, offline: 0, unknown: 0 });

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
          Operational control for fleet management, backup orchestration, and system monitoring.
        </p>
      </div>

      {/* System Health Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 flex items-center gap-4">
          <div className={`p-3 rounded-lg ${['healthy', 'ok'].includes(String(healthStatus).toLowerCase()) ? 'bg-green-900/30' : healthStatus === 'Checking' ? 'bg-slate-800/30' : 'bg-amber-900/30'}`}>
            {['healthy', 'ok'].includes(String(healthStatus).toLowerCase()) ? <CheckCircle className="text-green-400" size={24} /> : <AlertCircle className="text-amber-400" size={24} />}
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase">System Status</p>
            <p className={`text-xl font-bold ${['healthy', 'ok'].includes(String(healthStatus).toLowerCase()) ? 'text-green-400' : 'text-amber-300'}`}>{healthStatus}</p>
          </div>
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 flex items-center gap-4">
          <div className="p-3 rounded-lg bg-blue-900/30">
            <Zap className="text-blue-400" size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase">Current Role</p>
            <p className="text-xl font-bold text-blue-400">{user?.role?.toUpperCase() || 'VIEWER'}</p>
          </div>
        </div>
      </div>

      {/* Status Message */}
      {statusMessage && (
        <div className={`mb-6 p-4 rounded-lg border flex items-center gap-3 ${getStatusColor(statusType)}`}>
          {getStatusIcon(statusType)}
          <span className="flex-1">{statusMessage}</span>
          <button onClick={() => setStatusMessage('')} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.55fr_1fr]">
        <div className="space-y-6">
          <SystemControlPanel
            onBackup={triggerBackup}
            onSyncCreate={createSyncJob}
            onSyncComplete={completeSyncJob}
            onEmergencyStop={emergencyStopCommand}
            statusMessage={statusMessage}
            actionLoading={actionLoading}
            lastBackupSnapshot={lastBackupSnapshot}
            lastSyncJob={lastSyncJob}
            healthStatus={healthStatus}
            role={user?.role}
          />

          {/* Operation History */}
          {operationHistory.length > 0 && (
            <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4">
              <h3 className="text-sm font-bold text-aegis-primary mb-3 flex items-center gap-2">
                <Clock size={16} /> Recent Operations
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {operationHistory.map((entry, idx) => (
                  <div key={idx} className={`p-2 rounded text-xs border-l-2 ${
                    entry.status === 'success' ? 'border-green-600 bg-green-900/10 text-green-300' :
                    entry.status === 'error' ? 'border-red-600 bg-red-900/10 text-red-300' :
                    entry.status === 'warning' ? 'border-yellow-600 bg-yellow-900/10 text-yellow-300' :
                    'border-blue-600 bg-blue-900/10 text-blue-300'
                  }`}>
                    <div className="flex justify-between items-start">
                      <span className="font-semibold">{entry.action}</span>
                      <span className="text-[10px] text-slate-400">{entry.timestamp.toLocaleTimeString()}</span>
                    </div>
                    <p className="mt-1 opacity-80">{entry.result}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <section className="rounded-lg border border-slate-700 bg-slate-900/50 p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-slate-800 pb-3">
              <h2 className="text-lg font-semibold text-aegis-primary">Live estate assets</h2>
              <span className="text-xs text-slate-500">{snapshotUpdatedAt ? `Updated ${snapshotUpdatedAt.toLocaleTimeString()}` : 'Waiting for data'}</span>
            </div>
            {snapshotError && <p role="alert" className="mt-3 text-sm text-red-300">{snapshotError}</p>}
            <div className="grid grid-cols-3 gap-3 border-b border-slate-800 py-4 text-center text-xs">
              <div><p className="text-slate-500">Assets</p><p className="mt-1 text-lg font-semibold text-white">{snapshotCounts.total}</p></div>
              <div><p className="text-slate-500">Online</p><p className="mt-1 text-lg font-semibold text-emerald-300">{snapshotCounts.online}</p></div>
              <div><p className="text-slate-500">Offline / unknown</p><p className="mt-1 text-lg font-semibold text-amber-300">{snapshotCounts.offline + snapshotCounts.unknown}</p></div>
            </div>
            <div className="max-h-96 divide-y divide-slate-800 overflow-y-auto">
              {estateDevices.length ? estateDevices.map((device) => (
                <article key={device.id} className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-white">{device.name || device.device_id}</p>
                    <p className="mt-1 text-xs text-slate-500">{device.kind || 'Asset'} · Zone {device.zone_id ?? 'unassigned'} · {device.control_mode || 'mode unavailable'}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-xs font-semibold uppercase ${String(device.status).toLowerCase() === 'online' ? 'text-emerald-300' : String(device.status).toLowerCase() === 'offline' ? 'text-red-300' : 'text-amber-300'}`}>{device.status || 'unknown'}</p>
                    <p className="mt-1 text-[10px] text-slate-500">{device.last_updated ? new Date(device.last_updated).toLocaleTimeString() : 'No update time'}</p>
                  </div>
                </article>
              )) : <p className="py-8 text-center text-sm text-slate-400">{snapshotError ? 'Asset state unavailable.' : 'No registered tenant assets.'}</p>}
            </div>
          </section>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 space-y-4">
            <h2 className="text-lg font-semibold text-aegis-primary">Quick Reference</h2>
            
            <div className="space-y-3 text-sm">
              <div className="p-3 rounded bg-slate-800/50 border border-slate-700">
                <p className="font-semibold text-blue-300">💾 Backup Management</p>
                <p className="text-xs text-slate-400 mt-1">Create system snapshots for disaster recovery and data integrity verification.</p>
              </div>
              
              <div className="p-3 rounded bg-slate-800/50 border border-slate-700">
                <p className="font-semibold text-green-300">🔄 Sync Operations</p>
                <p className="text-xs text-slate-400 mt-1">Manage data synchronization jobs between systems and archive gateways.</p>
              </div>
              
              <div className="p-3 rounded bg-slate-800/50 border border-slate-700">
                <p className="font-semibold text-yellow-300">🤖 Fleet Control</p>
                <p className="text-xs text-slate-400 mt-1">Pause, resume, or emergency stop all robotic fleet operations.</p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-700">
              <Link href="/estate-dashboard" className="text-aegis-primary text-sm font-semibold hover:text-aegis-accent flex items-center gap-2">
                ← Back to Estate Dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
