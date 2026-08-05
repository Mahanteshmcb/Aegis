import { useEffect, useState } from 'react';
import useCurrentUser from '../hooks/useCurrentUser';
import { getEnergyStatus, getEnergyOverview, getEnergyPolicy, setEnergyPolicy, getSmartEnergySchedule } from '../utils/api';

export default function EnergyCard() {
  const { user } = useCurrentUser();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [overview, setOverview] = useState(null);
  const [smartSchedule, setSmartSchedule] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showSmartSchedule, setShowSmartSchedule] = useState(false);

  const token = typeof window !== 'undefined' ? localStorage.getItem('aegis_token') : null;

  const handleSavePolicy = async (p) => {
    setSaving(true);
    try {
      await setEnergyPolicy(token, p);
      setPolicy(p);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save policy', err);
    } finally {
      setSaving(false);
    }
  };

  const fetchSmartSchedule = async () => {
    try {
      const params = {};
      if (user?.tenant_id) params.tenant_id = user.tenant_id;
      const result = await getSmartEnergySchedule(token, params);
      setSmartSchedule(result);
      setShowSmartSchedule(true);
    } catch (err) {
      console.error('Failed to fetch smart schedule', err);
    }
  };

  const fetchOverview = async () => {
    try {
      const params = {};
      if (user?.tenant_id) params.tenant_id = user.tenant_id;
      const result = await getEnergyOverview(token, params);
      setOverview(result);
      return result;
    } catch (err) {
      console.error('Failed to fetch energy overview', err);
      return null;
    }
  };

  useEffect(() => {
    let mounted = true;

    Promise.all([getEnergyStatus(token), getEnergyPolicy(token), fetchOverview()])
      .then((data) => {
        if (mounted) {
          setStatus(data[0]);
          setPolicy(data[1] || { charge_threshold: 0.6, discharge_threshold: 0.3, max_charge_rate_kw: 2.0 });
        }
      })
      .catch((err) => {
        console.error('Energy status fetch error', err);
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, [token, user]);

  if (loading) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <p className="text-aegis-muted">Loading energy status…</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <p className="text-aegis-muted">Energy data unavailable</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-aegis-primary mb-2">Energy Overview</h3>
          <p className="text-aegis-muted text-sm">Net balance: <span className="font-mono">{status.balance_kwh.toFixed(2)} kWh</span></p>
          <div className="grid grid-cols-2 gap-2 mt-2 text-xs text-aegis-muted">
            <div>Total Gen: <span className="font-mono text-white">{status.generation_kwh.toFixed(1)} kWh</span></div>
            <div>Total Use: <span className="font-mono text-white">{status.consumption_kwh.toFixed(1)} kWh</span></div>
            <div>Battery SOC: <span className="font-mono text-white">{Math.round(status.battery_soc * 100)}%</span></div>
            <div>Solar assets: <span className="font-mono text-white">{status.solar_asset_count}</span></div>
          </div>
        </div>
        <button
          onClick={fetchSmartSchedule}
          className="rounded bg-emerald-700 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-600 transition"
        >
          Smart Schedule
        </button>
      </div>

      <div className="mt-4">
        <p className="text-aegis-muted text-sm mb-2">Upcoming battery actions</p>
        <ul className="text-sm space-y-2">
          {status.schedule.slice(0, 4).map((s, idx) => (
            <li key={idx} className="flex justify-between">
              <span className="text-aegis-text">Hour {s.hour}</span>
              <span className="text-aegis-muted">{s.action} — SOC {Math.round(s.soc*100)}%</span>
            </li>
          ))}
        </ul>
      </div>

      {overview && (
        <div className="mt-4 rounded border border-slate-800 bg-slate-950/40 p-3 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="text-aegis-muted">Battery capacity</span>
              <div className="font-mono text-white">{overview.battery_capacity_kwh.toFixed(1)} kWh</div>
            </div>
            <div>
              <span className="text-aegis-muted">Grid assets</span>
              <div className="font-mono text-white">{overview.grid_asset_count}</div>
            </div>
            <div>
              <span className="text-aegis-muted">Solar generation</span>
              <div className="font-mono text-white">{overview.source_breakdown?.solar?.toFixed(1) ?? '0.0'} kWh</div>
            </div>
            <div>
              <span className="text-aegis-muted">Wind generation</span>
              <div className="font-mono text-white">{overview.source_breakdown?.wind?.toFixed(1) ?? '0.0'} kWh</div>
            </div>
            <div>
              <span className="text-aegis-muted">Hydro generation</span>
              <div className="font-mono text-white">{overview.source_breakdown?.hydro?.toFixed(1) ?? '0.0'} kWh</div>
            </div>
            <div>
              <span className="text-aegis-muted">Grid capacity</span>
              <div className="font-mono text-white">{overview.source_counts?.grid ?? 0}</div>
            </div>
          </div>
        </div>
      )}

      {showSmartSchedule && smartSchedule && (
        <div className="mt-6 border-t border-slate-800 pt-4">
          <h4 className="text-sm font-semibold text-emerald-400 mb-3">📊 Adaptive Weather-Aware Schedule</h4>
          
          {smartSchedule.metrics && (
            <div className="grid grid-cols-2 gap-3 text-xs mb-4 p-3 bg-slate-950/50 rounded">
              <div><span className="text-aegis-muted">Peak Load:</span> <span className="text-emerald-300 font-mono">{smartSchedule.metrics.peak_load_kw}kW</span></div>
              <div><span className="text-aegis-muted">Min SOC:</span> <span className="text-emerald-300 font-mono">{(smartSchedule.metrics.min_soc*100).toFixed(0)}%</span></div>
              <div><span className="text-aegis-muted">Final SOC:</span> <span className="text-emerald-300 font-mono">{(smartSchedule.metrics.final_soc*100).toFixed(0)}%</span></div>
              <div><span className="text-aegis-muted">Gen/Cons:</span> <span className="text-emerald-300 font-mono">{smartSchedule.metrics.total_generation_kwh.toFixed(1)}/{smartSchedule.metrics.total_consumption_kwh.toFixed(1)}</span></div>
            </div>
          )}

          {smartSchedule.recommendations && smartSchedule.recommendations.length > 0 && (
            <div className="space-y-2 mb-4">
              <p className="text-xs text-aegis-muted">Key Recommendations:</p>
              {smartSchedule.recommendations.map((rec, idx) => (
                <div key={idx} className="text-xs p-2 rounded border border-yellow-800/30 bg-yellow-900/10 text-yellow-200">
                  {rec.type === 'capacity_warning' && '⚠️ Generation is low - consider reducing non-critical loads'}
                  {rec.type === 'low_battery_risk' && '⛔ Battery reaches critical low - backup power may be needed'}
                  {rec.type === 'defer_load' && `⏸️ Defer load at hour ${rec.hour} - battery too low`}
                </div>
              ))}
            </div>
          )}

          <div className="mt-3 max-h-48 overflow-y-auto">
            <p className="text-xs text-aegis-muted mb-2">Next 6 hours (weather-informed):</p>
            <ul className="text-xs space-y-1">
              {smartSchedule.schedule.slice(0, 6).map((s, idx) => (
                <li key={idx} className="flex justify-between p-1 rounded bg-slate-950/30 hover:bg-slate-950/50">
                  <span className="text-slate-400">Hour {s.hour}</span>
                  <span className="text-emerald-300">{s.action}</span>
                  <span className="text-cyan-300">SOC {(s.soc*100).toFixed(0)}%</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="mt-6 border-t border-slate-800 pt-4">
        <h4 className="text-sm font-semibold text-aegis-primary mb-2">Charging Policy</h4>
        <PolicyForm policyInitial={policy} onSave={handleSavePolicy} saving={saving} saved={saved} />
      </div>
    </div>
  );
}



function PolicyForm({ policyInitial, onSave, saving, saved }) {
  const [policy, setPolicyState] = useState(policyInitial || { charge_threshold: 0.6, discharge_threshold: 0.3, max_charge_rate_kw: 2.0 });

  useEffect(() => setPolicyState(policyInitial || policy), [policyInitial]);

  return (
    <div className="grid grid-cols-1 gap-3">
      <div className="flex items-center gap-3">
        <label className="text-xs text-aegis-muted w-36">Charge threshold</label>
        <input type="number" step="0.05" min="0" max="1" value={policy.charge_threshold} onChange={(e) => setPolicyState({...policy, charge_threshold: parseFloat(e.target.value)})} className="w-full rounded px-3 py-2 bg-[#0f172a] border border-slate-700 text-white" />
      </div>
      <div className="flex items-center gap-3">
        <label className="text-xs text-aegis-muted w-36">Discharge threshold</label>
        <input type="number" step="0.05" min="0" max="1" value={policy.discharge_threshold} onChange={(e) => setPolicyState({...policy, discharge_threshold: parseFloat(e.target.value)})} className="w-full rounded px-3 py-2 bg-[#0f172a] border border-slate-700 text-white" />
      </div>
      <div className="flex items-center gap-3">
        <label className="text-xs text-aegis-muted w-36">Max charge rate (kW)</label>
        <input type="number" step="0.1" min="0" value={policy.max_charge_rate_kw} onChange={(e) => setPolicyState({...policy, max_charge_rate_kw: parseFloat(e.target.value)})} className="w-full rounded px-3 py-2 bg-[#0f172a] border border-slate-700 text-white" />
      </div>
      <div className="flex items-center gap-3">
        <button onClick={() => onSave(policy)} disabled={saving} className="px-4 py-2 rounded bg-aegis-primary text-white font-semibold hover:bg-sky-400 transition-all">{saving ? 'Saving…' : 'Save Policy'}</button>
        {saved && <span className="text-green-400 text-sm">Saved</span>}
      </div>
    </div>
  );
}
