import React, { useState } from 'react';
import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

export default function AlertsConfiguration() {
  const { user, loading } = useCurrentUser();
  const [alerts, setAlerts] = useState([
    { id: 1, type: 'high_temp', threshold: 35, severity: 'high', enabled: true },
    { id: 2, type: 'low_battery', threshold: 20, severity: 'medium', enabled: true },
    { id: 3, type: 'network_latency', threshold: 1000, severity: 'medium', enabled: true },
  ]);
  const [showForm, setShowForm] = useState(false);

  const typeLabels = {
    high_temp: '🌡️ High Temperature',
    low_battery: '🔋 Low Battery',
    network_latency: '📡 Network Latency',
    system_error: '⚠️ System Error',
    unauthorized_access: '🔒 Unauthorized Access',
  };

  const severityColors = {
    low: 'text-green-400',
    medium: 'text-yellow-400',
    high: 'text-red-400',
  };

  if (loading) {
    return <div className="text-aegis-muted animate-pulse">Loading...</div>;
  }

  return (
    <div className="w-full">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em] mb-2">
            🚨 ALERT CONFIGURATION
          </h1>
          <p className="text-aegis-muted">Configure alert rules and thresholds</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-6 py-3 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-lg hover:from-orange-500 hover:to-red-500 transition-all font-mono text-sm font-bold"
        >
          {showForm ? '✕ Cancel' : '+ Add Alert Rule'}
        </button>
      </div>

      {showForm && (
        <div className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-6 mb-8">
          <form className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Alert Type</label>
              <select className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none">
                <option value="high_temp">High Temperature</option>
                <option value="low_battery">Low Battery</option>
                <option value="network_latency">Network Latency</option>
                <option value="system_error">System Error</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-aegis-muted uppercase tracking-wider">Threshold</label>
              <input
                type="number"
                placeholder="Enter threshold value"
                className="w-full mt-2 px-3 py-2 bg-black/50 border border-aegis-primary/30 rounded text-aegis-primary text-sm focus:border-aegis-primary/60 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="col-span-1 md:col-span-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 transition-all text-sm font-bold"
            >
              Create Rule
            </button>
          </form>
        </div>
      )}

      <div className="space-y-4">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="bg-gradient-to-br from-black/40 to-black/60 border border-aegis-primary/30 rounded-lg p-4 hover:border-aegis-primary/60 transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-bold text-aegis-primary">
                  {typeLabels[alert.type] || alert.type}
                </h3>
                <div className="grid grid-cols-3 gap-4 mt-3 text-xs font-mono">
                  <div>
                    <span className="text-aegis-muted">Threshold:</span>
                    <p className="text-cyan-400 font-bold">{alert.threshold}</p>
                  </div>
                  <div>
                    <span className="text-aegis-muted">Severity:</span>
                    <p className={`font-bold ${severityColors[alert.severity]}`}>
                      {alert.severity.toUpperCase()}
                    </p>
                  </div>
                  <div>
                    <span className="text-aegis-muted">Status:</span>
                    <p className={alert.enabled ? 'text-green-400 font-bold' : 'text-gray-400 font-bold'}>
                      {alert.enabled ? 'ENABLED' : 'DISABLED'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <button className="px-3 py-2 bg-blue-600 text-white text-xs rounded hover:bg-blue-500 transition-all">
                  Edit
                </button>
                <button className="px-3 py-2 bg-red-600 text-white text-xs rounded hover:bg-red-500 transition-all">
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8">
        <Link href="/estate-dashboard" className="text-aegis-primary hover:text-aegis-primary/80 transition-colors">
          ← Back to Estate Dashboard
        </Link>
      </div>
    </div>
  );
}
