import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function AlertsConfiguration() {
  const { user, token, loading } = useCurrentUser();
  const [rules, setRules] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [deliveryConfigs, setDeliveryConfigs] = useState([]);
  const [deliveryStatuses, setDeliveryStatuses] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showDeliveryForm, setShowDeliveryForm] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [sensorId, setSensorId] = useState('');
  const [comparison, setComparison] = useState('<');
  const [threshold, setThreshold] = useState('30');
  const [provider, setProvider] = useState('webhook');
  const [providerConfig, setProviderConfig] = useState('{}');
  const [providerEnabled, setProviderEnabled] = useState(true);
  const [loadingRules, setLoadingRules] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [evaluatingId, setEvaluatingId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const fetchRules = useCallback(async () => {
    if (!token) return;
    setLoadingRules(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [response, sensorResponse, configResponse, statusResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/notifications/rules`, { headers }),
        fetch(`${API_URL}/api/v1/digital-twin/devices`, { headers }),
        fetch(`${API_URL}/api/v1/notifications/delivery-configs`, { headers }),
        fetch(`${API_URL}/api/v1/notifications/delivery-statuses`, { headers }),
      ]);
      const [result, sensorResult, configResult, statusResult] = await Promise.all([
        response.json().catch(() => ({})),
        sensorResponse.json().catch(() => []),
        configResponse.json().catch(() => ({})),
        statusResponse.json().catch(() => ({})),
      ]);
      if (!response.ok) throw new Error(result.detail || 'Unable to load notification rules.');
      setRules(Array.isArray(result.data) ? result.data : []);
      setSensors(sensorResponse.ok && Array.isArray(sensorResult) ? sensorResult.filter((device) => device.kind === 'sensor') : []);
      setDeliveryConfigs(configResponse.ok && Array.isArray(configResult.data) ? configResult.data : []);
      setDeliveryStatuses(statusResponse.ok && Array.isArray(statusResult.data) ? statusResult.data : []);
      setError('');
    } catch (loadError) {
      setError(loadError.message || 'Unable to load notification rules.');
    } finally {
      setLoadingRules(false);
    }
  }, [token]);

  useEffect(() => {
    if (!loading && user) fetchRules();
  }, [loading, user, fetchRules]);

  const selectedSensor = sensors.find((sensor) => String(sensor.device_id) === sensorId);
  const numericThreshold = Number(threshold);
  const condition = selectedSensor && Number.isFinite(numericThreshold)
    ? `sensors[${JSON.stringify(selectedSensor.device_id)}].value ${comparison} ${numericThreshold}`
    : '';

  async function handleCreateRule(event) {
    event.preventDefault();
    if (!ruleName.trim() || !condition) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const response = await fetch(`${API_URL}/api/v1/notifications/rules`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: ruleName.trim(), condition: condition.trim(), enabled: true }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to create alert rule.');
      setRuleName('');
      setShowForm(false);
      setSuccess('Alert rule created.');
      await fetchRules();
    } catch (saveError) {
      setError(saveError.message || 'Unable to create alert rule.');
    } finally {
      setSaving(false);
    }
  }

  async function handleEvaluateRule(rule) {
    setEvaluatingId(rule.id);
    setError('');
    setSuccess('');
    try {
      const response = await fetch(`${API_URL}/api/v1/notifications/rules/${rule.id}/evaluate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to evaluate this rule.');
      setSuccess(result.triggered ? `Rule matched. Alert #${result.alert_id} was created.` : 'Rule checked: the current sensor values did not match.');
    } catch (evaluateError) {
      setError(evaluateError.message || 'Unable to evaluate this rule.');
    } finally {
      setEvaluatingId(null);
    }
  }

  async function handleDeleteRule(rule) {
    if (!window.confirm(`Delete alert rule "${rule.name}"?`)) return;
    setDeletingId(rule.id);
    setError('');
    try {
      const response = await fetch(`${API_URL}/api/v1/notifications/rules/${rule.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to delete alert rule.');
      setSuccess('Alert rule deleted.');
      await fetchRules();
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to delete alert rule.');
    } finally {
      setDeletingId(null);
    }
  }

  async function handleCreateDeliveryConfig(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      let parsedConfig;
      try {
        parsedConfig = JSON.parse(providerConfig);
      } catch {
        throw new Error('Provider configuration must be valid JSON.');
      }
      if (!parsedConfig || Array.isArray(parsedConfig) || typeof parsedConfig !== 'object') {
        throw new Error('Provider configuration must be a JSON object.');
      }
      const response = await fetch(`${API_URL}/api/v1/notifications/delivery-configs`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, enabled: providerEnabled, config: parsedConfig }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || 'Unable to save provider configuration.');
      setProviderConfig('{}');
      setShowDeliveryForm(false);
      setSuccess('Alert delivery provider saved.');
      await fetchRules();
    } catch (saveError) {
      setError(saveError.message || 'Unable to save provider configuration.');
    } finally {
      setSaving(false);
    }
  }

  const canManageDelivery = user?.permissions?.includes('alerts.manage')
    || ['admin', 'superadmin', 'operator'].includes(String(user?.role || '').toLowerCase());

  if (loading) {
    return <div className="text-aegis-muted animate-pulse">Loading...</div>;
  }

  return (
    <div className="w-full">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-aegis-primary mb-2">Alert Configuration</h1>
          <p className="text-aegis-muted">Create and test tenant rules against current digital-twin sensor readings.</p>
        </div>
          <button
            type="button"
          onClick={() => setShowForm(!showForm)}
          className="rounded border border-cyan-600/50 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-950"
        >
          {showForm ? 'Cancel' : 'Add rule'}
        </button>
      </div>

      {error && <div role="alert" className="mb-4 rounded border border-red-700 bg-red-900/20 p-4 text-sm text-red-200">{error}</div>}
      {success && <div role="status" className="mb-4 rounded border border-emerald-700 bg-emerald-900/20 p-4 text-sm text-emerald-200">{success}</div>}

      {showForm && (
        <form onSubmit={handleCreateRule} className="mb-8 grid max-w-3xl gap-4 border-y border-slate-800 py-5">
            <div>
              <label htmlFor="alert-rule-name" className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Rule name</label>
              <input id="alert-rule-name" required maxLength={255} value={ruleName} onChange={(event) => setRuleName(event.target.value)} className="mt-2 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-white" />
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Sensor
                <select required value={sensorId} onChange={(event) => setSensorId(event.target.value)} className="mt-2 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm font-normal text-white">
                  <option value="">Choose a registered sensor</option>
                  {sensors.map((sensor) => <option key={sensor.id} value={sensor.device_id}>{sensor.name} ({sensor.device_id})</option>)}
                </select>
              </label>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Condition
                <select value={comparison} onChange={(event) => setComparison(event.target.value)} className="mt-2 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm font-normal text-white">
                  <option value="<">Below</option><option value="<=">At or below</option><option value=">">Above</option><option value=">=">At or above</option><option value="==">Equal to</option>
                </select>
              </label>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Threshold
                <input type="number" step="any" required value={threshold} onChange={(event) => setThreshold(event.target.value)} className="mt-2 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm font-normal text-white" />
              </label>
            </div>
            <div className="rounded border border-slate-800 bg-slate-950/70 p-3 text-xs">
              <p className="text-slate-500">Rule expression</p><code className="mt-1 block break-all text-cyan-200">{condition || 'Select a sensor and valid threshold'}</code>
              <p className="mt-2 text-slate-500">Rules evaluate current registered sensor states when manually tested. Missing readings do not trigger a match.</p>
            </div>
            <button
              type="submit"
              disabled={saving || !condition}
              className="w-fit rounded bg-aegis-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Create rule'}
            </button>
        </form>
      )}

      <div className="divide-y divide-slate-800 border-y border-slate-800">
        {loadingRules ? <p className="py-8 text-center text-slate-400">Loading notification rules...</p> : rules.length === 0 ? (
          <p className="py-8 text-center text-slate-400">No notification rules configured for this tenant.</p>
        ) : rules.map((rule) => (
          <article key={rule.id} className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <h2 className="font-semibold text-white">{rule.name}</h2>
              <code className="mt-1 block break-all text-sm text-cyan-200">{rule.condition}</code>
              <p className={`mt-1 text-xs ${rule.enabled ? 'text-emerald-300' : 'text-slate-500'}`}>{rule.enabled ? 'Enabled' : 'Disabled'}</p>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => handleEvaluateRule(rule)} disabled={!rule.enabled || evaluatingId === rule.id} className="w-fit rounded border border-cyan-800 px-3 py-2 text-xs text-cyan-200 hover:bg-cyan-950 disabled:opacity-50">{evaluatingId === rule.id ? 'Checking...' : 'Evaluate now'}</button>
              <button type="button" onClick={() => handleDeleteRule(rule)} disabled={deletingId === rule.id} className="w-fit rounded border border-red-800 px-3 py-2 text-xs text-red-300 hover:bg-red-950 disabled:opacity-50">{deletingId === rule.id ? 'Deleting...' : 'Delete'}</button>
            </div>
          </article>
        ))}
      </div>

      <section className="mt-10 space-y-4 border-t border-slate-800 pt-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-white">Delivery providers</h2>
            <p className="mt-1 text-sm text-slate-400">Provider secrets are masked in API responses. Configure SMTP, webhook, or SMS delivery for this tenant.</p>
          </div>
          {canManageDelivery && <button type="button" onClick={() => setShowDeliveryForm((shown) => !shown)} className="rounded border border-cyan-700 px-3 py-2 text-sm text-cyan-200 hover:bg-cyan-950">{showDeliveryForm ? 'Cancel' : 'Add provider'}</button>}
        </div>
        {showDeliveryForm && canManageDelivery && (
          <form onSubmit={handleCreateDeliveryConfig} className="grid max-w-3xl gap-4 border-y border-slate-800 py-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm text-slate-300">Provider
                <select value={provider} onChange={(event) => setProvider(event.target.value)} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-white">
                  <option value="webhook">Webhook</option><option value="smtp">SMTP</option><option value="sms">SMS</option>
                </select>
              </label>
              <label className="flex items-center gap-2 self-end pb-2 text-sm text-slate-300">
                <input type="checkbox" checked={providerEnabled} onChange={(event) => setProviderEnabled(event.target.checked)} /> Enabled
              </label>
            </div>
            <label className="text-sm text-slate-300">Provider configuration (JSON)
              <textarea required rows={5} value={providerConfig} onChange={(event) => setProviderConfig(event.target.value)} className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs text-white" />
            </label>
            <p className="text-xs text-amber-200">Sensitive JSON keys such as password, token, secret, and api_key are never returned in full. Keep production credentials in environment-managed secret storage.</p>
            <button type="submit" disabled={saving} className="w-fit rounded bg-cyan-700 px-4 py-2 text-sm text-white disabled:opacity-50">{saving ? 'Saving...' : 'Save provider'}</button>
          </form>
        )}
        {deliveryConfigs.length === 0 ? <p className="py-4 text-sm text-slate-500">No delivery providers configured for this tenant.</p> : (
          <div className="divide-y divide-slate-800 border-y border-slate-800">
            {deliveryConfigs.map((config) => {
              const latestStatus = deliveryStatuses.find((status) => status.provider === config.provider);
              return <article key={config.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
                <div>
                  <h3 className="font-semibold uppercase text-white">{config.provider}</h3>
                  <p className="text-xs text-slate-400">{config.enabled ? 'Enabled' : 'Disabled'} · retries {config.retry_policy?.retries ?? 3} · backoff {config.retry_policy?.backoff_seconds ?? 5}s</p>
                  {latestStatus && <p className="mt-1 text-xs text-slate-500">Latest delivery: {latestStatus.status}{latestStatus.last_error ? ` · ${latestStatus.last_error}` : ''}</p>}
                </div>
                <span className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-300">Tenant #{config.id}</span>
              </article>;
            })}
          </div>
        )}
      </section>

      <div className="mt-8">
        <Link href="/estate-dashboard" className="text-aegis-primary hover:text-aegis-primary/80 transition-colors">
          ← Back to Estate Dashboard
        </Link>
      </div>
    </div>
  );
}
