import { useEffect, useState } from 'react';

export default function Header() {
  const [sysStatus, setSysStatus] = useState({ status: 'HEALTHY', threat_count: 0 });

  useEffect(() => {
    const checkStatus = async () => {
      const token = localStorage.getItem('aegis_token');
      if (!token) return;

      try {
        const res = await fetch('http://localhost:8080/api/v1/health/status', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setSysStatus(data);
        }
      } catch (err) {
        console.error("Health Sync Failed:", err);
      }
    };

    // Initial check and 10-second heartbeat
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const isWarning = sysStatus.status === 'WARNING';

  return (
    <header className="h-16 bg-aegis-dark border-b border-slate-700 flex items-center justify-between px-6">
      <div className="flex items-center">
        <span className="text-aegis-muted font-medium uppercase tracking-tighter text-xs">
          Main Estate <span className="text-aegis-primary mx-2">|</span> Sector: Alpha
        </span>
      </div>

      <div className="flex items-center space-x-6">
        {/* Dynamic Status Indicator */}
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full shadow-[0_0_8px] ${
            isWarning 
              ? 'bg-red-500 shadow-red-500 animate-pulse' 
              : 'bg-aegis-success shadow-aegis-success'
          }`}></div>
          <span className={`text-xs font-mono uppercase tracking-widest ${
            isWarning ? 'text-red-500 font-bold' : 'text-aegis-muted'
          }`}>
            {isWarning ? `SYSTEM WARNING (${sysStatus.threat_count} THREATS)` : 'SYSTEM HEALTHY'}
          </span>
        </div>

        {/* User Profile / Avatar */}
        <div className="w-8 h-8 rounded-full border border-aegis-primary/30 bg-aegis-dark flex items-center justify-center text-aegis-primary font-bold text-sm shadow-[inset_0_0_4px_rgba(0,242,255,0.2)]">
          A
        </div>
      </div>
    </header>
  );
}