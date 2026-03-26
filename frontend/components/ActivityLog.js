import React from 'react';

const ActivityLog = ({ logs }) => {
  return (
    <div className="mt-8 bg-black/40 border border-white/10 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
        <h3 className="text-sm font-bold uppercase tracking-widest text-aegis-primary">System Audit Trail</h3>
        <span className="text-[10px] font-mono text-aegis-muted">Real-time Ledger Sync</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="text-aegis-muted border-b border-white/5">
              <th className="p-4">Timestamp</th>
              <th className="p-4">Event</th>
              <th className="p-4">Entity ID</th>
              <th className="p-4">Hash Integrity</th>
            </tr>
          </thead>
          <tbody>
            {logs.length > 0 ? logs.map((log) => (
              <tr key={log.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                <td className="p-4 text-aegis-muted">{new Date(log.created_at).toLocaleTimeString()}</td>
                <td className="p-4">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                    log.event_type.includes('error') ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'
                  }`}>
                    {log.event_type.toUpperCase()}
                  </span>
                </td>
                <td className="p-4 text-white">#00{log.sensor_id || log.zone_id || 'SYS'}</td>
                <td className="p-4 text-aegis-primary truncate max-w-[150px] opacity-60">
                  {log.data_hash}
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan="4" className="p-8 text-center text-aegis-muted italic">No audit records found in current session.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ActivityLog;