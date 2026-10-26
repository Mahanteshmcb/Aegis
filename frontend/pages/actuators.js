import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Activity, ArrowLeft, Power, PowerOff } from 'lucide-react';
import Layout3D from '../components/Layout3D';
import Card3D from '../components/Card3D';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function ActuatorsPage() {
  const { user, loading, token } = useCurrentUser();
  const [actuators, setActuators] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState('');
  const [commandingId, setCommandingId] = useState(null);
  const canControl = ['admin', 'superadmin', 'manager', 'operator'].includes(String(user?.role || '').toLowerCase());

  const fetchActuators = useCallback(async () => {
    if (!token) return;
    try {
      setLoadingData(true);
      const headers = { Authorization: `Bearer ${token}` };
      const [response, zonesResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }),
        fetch(`${API_URL}/api/v1/zones`, { headers }).catch(() => null),
      ]);

      if (!response.ok) {
        throw new Error('Unable to load actuator fleet.');
      }

      const payload = await response.json().catch(() => []);
      const rows = Array.isArray(payload) ? payload : [];
      const zonePayload = zonesResponse?.ok ? await zonesResponse.json().catch(() => []) : [];
      const zoneNames = new Map((Array.isArray(zonePayload) ? zonePayload : []).map((zone) => [String(zone.id), zone.name]));
      setActuators(
        rows
          .filter((device) => device.kind === 'actuator')
          .map((device) => ({
            ...device,
            id: device.id,
            output: device.state?.output ?? 'unknown',
            status: device.status || 'unknown',
            zoneName: zoneNames.get(String(device.zone_id)) || (device.zone_id == null ? 'Unassigned' : `Zone ${device.zone_id}`),
          }))
      );
      setError('');
    } catch (fetchError) {
      setError(fetchError.message || 'Unable to load actuator fleet.');
      setActuators([]);
    } finally {
      setLoadingData(false);
    }
  }, [token]);

  const updateActuatorState = async (actuatorId, command) => {
    try {
      setCommandingId(actuatorId);
      setError('');
      const response = await fetch(`${API_URL}/api/v1/digital-twin/devices/${actuatorId}/control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ command, parameters: {} }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || 'Unable to update actuator state.');
      }

      const result = await response.json();
      setActuators((previous) => previous.map((actuator) => actuator.id === actuatorId
        ? { ...actuator, ...result, output: result.state?.output ?? actuator.output, status: result.status || actuator.status }
        : actuator));
    } catch (controlError) {
      setError(controlError.message || 'Unable to update actuator state.');
    } finally {
      setCommandingId(null);
    }
  };

  useEffect(() => {
    if (!loading && user) {
      fetchActuators();
    }
  }, [user, loading, fetchActuators]);

  const stats = useMemo(() => {
    const active = actuators.filter((item) => ['active', 'on', 'open', 'running'].includes(String(item.output).toLowerCase())).length;
    const total = actuators.length;
    const unknown = actuators.filter((item) => String(item.output).toLowerCase() === 'unknown').length;
    return {
      total,
      active,
      inactive: total - active - unknown,
      unknown,
    };
  }, [actuators]);

  return (
    <Layout3D
      title="ACTUATOR CONTROL"
      icon="⚙️"
      subtitle="Manual automation operations and actuator state monitoring"
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-3">
          <Link href="/estate-dashboard" className="inline-flex items-center gap-2 text-sm text-cyan-300 hover:text-cyan-200">
            <ArrowLeft size={16} /> Back to Estate Dashboard
          </Link>
          <button
            onClick={fetchActuators}
            disabled={loadingData}
            className="rounded border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200 disabled:opacity-50"
          >
            {loadingData ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card3D variant="primary">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Total Actuators</p>
            <p className="mt-3 text-3xl font-bold text-white">{stats.total}</p>
          </Card3D>
          <Card3D variant="success">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Active</p>
            <p className="mt-3 text-3xl font-bold text-emerald-300">{stats.active}</p>
          </Card3D>
          <Card3D variant="warning">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Not active</p>
            <p className="mt-3 text-3xl font-bold text-amber-300">{stats.inactive}</p>
          </Card3D>
          <Card3D variant="secondary">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Unknown output</p>
            <p className="mt-3 text-3xl font-bold text-slate-300">{stats.unknown}</p>
          </Card3D>
        </div>

        {error && (
          <div className="rounded border border-red-700 bg-red-900/20 p-3 text-sm text-red-200">{error}</div>
        )}

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          {loadingData ? (
            <div className="p-10 text-center text-slate-400">Loading actuator fleet...</div>
          ) : actuators.length === 0 ? (
            <div className="p-10 text-center text-slate-400">No actuators are registered for this tenant.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-800 text-slate-300">
                  <tr>
                    <th className="px-4 py-3">Actuator</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Zone</th>
                    <th className="px-4 py-3">State</th>
                    <th className="px-4 py-3">Mode / Health</th>
                    <th className="px-4 py-3">Command</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200">
                  {actuators.map((actuator) => (
                    <tr key={actuator.id} className="hover:bg-slate-800/50">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-white">{actuator.name || `Actuator ${actuator.id}`}</div>
                        <div className="text-xs text-slate-400">{actuator.device_id || actuator.id}</div>
                      </td>
                      <td className="px-4 py-3">{actuator.device_type || actuator.type || 'actuator'}</td>
                      <td className="px-4 py-3 text-slate-300">{actuator.zoneName}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-1 text-xs font-medium ${['active', 'on', 'open', 'running'].includes(String(actuator.output).toLowerCase()) ? 'bg-emerald-500/20 text-emerald-200' : actuator.output === 'unknown' ? 'bg-slate-500/20 text-slate-200' : 'bg-amber-500/10 text-amber-200'}`}>
                          {actuator.output}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300">{actuator.control_mode || 'unknown'} · {actuator.status}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => updateActuatorState(actuator.id, 'start')}
                            disabled={!canControl || Boolean(commandingId) || loadingData}
                            title={!canControl ? 'Operator permission required' : 'Start actuator'}
                            className="inline-flex items-center gap-1 rounded border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-xs text-emerald-200 disabled:cursor-not-allowed disabled:opacity-40"
                          >
                            <Power size={12} /> {commandingId === actuator.id ? 'Sending...' : 'Start'}
                          </button>
                          <button
                            onClick={() => updateActuatorState(actuator.id, 'stop')}
                            disabled={!canControl || Boolean(commandingId) || loadingData}
                            title={!canControl ? 'Operator permission required' : 'Stop actuator'}
                            className="inline-flex items-center gap-1 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-xs text-amber-200 disabled:cursor-not-allowed disabled:opacity-40"
                          >
                            <PowerOff size={12} /> Stop
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout3D>
  );
}
