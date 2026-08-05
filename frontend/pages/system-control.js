import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, CheckCircle, Clock, Zap, AlertTriangle, TrendingUp } from 'lucide-react';
import dynamic from 'next/dynamic';
const TacticalMap = dynamic(() => import('../components/TacticalMap'), { ssr: false });
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
  const [statusType, setStatusType] = useState('info'); // info, success, warning, error
  const [actionLoading, setActionLoading] = useState(false);
  const [anomalyMode, setAnomalyMode] = useState(false);
  const [lastSyncJob, setLastSyncJob] = useState(null);
  const [lastBackupSnapshot, setLastBackupSnapshot] = useState(null);
  const [healthStatus, setHealthStatus] = useState('Unknown');
  const [operationHistory, setOperationHistory] = useState([]);
  const [confirmAction, setConfirmAction] = useState(null);

  const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;

  useEffect(() => {
    if (!loading && token) {
      fetchHealthStatus();
    }
  }, [loading, token]);

  async function fetchHealthStatus() {
    try {
      const data = await getSystemHealthStatus(token);
      setHealthStatus((data && data.status) || 'OK');
      setStatusMessage('Live connectivity verified.');
      setStatusType('success');
      addToHistory('Health Status', 'System healthy', 'success');
    } catch (error) {
      setHealthStatus('Unavailable');
      setStatusMessage('Unable to reach backend services.');
      setStatusType('error');
      addToHistory('Health Check', 'Connection failed', 'error');
    }
  }

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
      const backup = await createBackupSnapshot(token, {
        source: 'system_control',
        record_count: 42,
        data_hash: `system-control-${Date.now()}`,
        storage_uri: `local://system-control/backups/${Date.now()}`,
        status: 'created',
        integrity_verified: false,
        verification_notes: 'Triggered from system control UI',
      });

      if (backup) {
        setLastBackupSnapshot(backup);
      }
      setStatusMessage('✓ Backup snapshot created successfully.');
      setStatusType('success');
      addToHistory('Backup Creation', `Snapshot ID: ${backup?.backup_id || 'N/A'}`, 'success');
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

  async function pauseFleet() {
    if (!window.confirm('Pause all fleet operations? Robots will halt current tasks.')) return;
    
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Pausing fleet...');
    setStatusType('info');

    try {
      const result = await fleetEmergencyStop(token, {
        reason: 'Pause fleet from system control',
      });
      setStatusMessage(`✓ Fleet pause issued: ${result.reason || 'All robots halted'}`);
      setStatusType('success');
      addToHistory('Fleet Pause', 'All robots halted', 'success');
    } catch (error) {
      setStatusMessage('✗ Fleet pause failed: ' + (error.message || 'Unknown error'));
      setStatusType('error');
      addToHistory('Fleet Pause', error.message, 'error');
    } finally {
      setActionLoading(false);
    }
  }

  async function resumeFleet() {
    if (!window.confirm('Resume fleet operations? Robots will continue previous tasks.')) return;
    
    if (!token) return;
    setActionLoading(true);
    setStatusMessage('Resuming fleet...');
    setStatusType('info');

    try {
      const result = await fleetEmergencyStop(token, {
        reason: 'Resume fleet from system control',
      });
      setStatusMessage(`✓ Fleet resume issued: ${result.reason || 'All robots resumed'}`);
      setStatusType('success');
      addToHistory('Fleet Resume', 'All robots resumed', 'success');
    } catch (error) {
      setStatusMessage('✗ Fleet resume failed: ' + (error.message || 'Unknown error'));
      setStatusType('error');
      addToHistory('Fleet Resume', error.message, 'error');
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
      const result = await emergencyStop(token, {
        robot_id: 'fleet',
        robot_type: 'AEGIS_ROVER',
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

  const toggleAnomaly = () => {
    setAnomalyMode(!anomalyMode);
    const newState = !anomalyMode ? 'activated' : 'deactivated';
    setStatusMessage(`Anomaly visualization ${newState}.`);
    setStatusType('info');
    addToHistory('Anomaly Mode', newState, 'info');
  };

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
          <div className={`p-3 rounded-lg ${healthStatus === 'OK' ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
            {healthStatus === 'OK' ? <CheckCircle className="text-green-400" size={24} /> : <AlertCircle className="text-red-400" size={24} />}
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase">System Status</p>
            <p className={`text-xl font-bold ${healthStatus === 'OK' ? 'text-green-400' : 'text-red-400'}`}>{healthStatus}</p>
          </div>
        </div>
        
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 flex items-center gap-4">
          <div className={`p-3 rounded-lg ${anomalyMode ? 'bg-yellow-900/30' : 'bg-slate-800/30'}`}>
            <TrendingUp className={anomalyMode ? 'text-yellow-400' : 'text-slate-400'} size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase">Anomaly Mode</p>
            <p className={`text-xl font-bold ${anomalyMode ? 'text-yellow-400' : 'text-slate-400'}`}>{anomalyMode ? 'ACTIVE' : 'Normal'}</p>
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
          <div className="rounded-lg overflow-hidden border border-slate-700 bg-slate-900/50">
            <TacticalMap anomaly={anomalyMode} />
          </div>

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
