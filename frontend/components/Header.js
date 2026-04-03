import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getAuthToken, clearAuthToken } from '../utils/auth';
import useCurrentUser from '../hooks/useCurrentUser';

export default function Header() {
  const [sysStatus, setSysStatus] = useState({ status: 'HEALTHY', threat_count: 0 });
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const { user } = useCurrentUser();
  const router = useRouter();

  const handleLogout = () => {
    clearAuthToken();
    setIsLoggedIn(false);
    router.push('/login');
  };

  useEffect(() => {
    const token = getAuthToken();
    setIsLoggedIn(Boolean(token));
  }, [router.pathname]);

  useEffect(() => {
    const checkStatus = async () => {
      const token = getAuthToken();
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
        console.error('Health Sync Failed:', err);
      }
    };

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

      <nav className="space-x-4 text-sm font-medium text-aegis-muted">
        <a href="/dashboard" className="hover:text-aegis-primary transition-colors">Dashboard</a>
        <a href="/sensors" className="hover:text-aegis-primary transition-colors">Sensors</a>
        <a href="/zones" className="hover:text-aegis-primary transition-colors">Zones</a>
        <a href="/audit-logs" className="hover:text-aegis-primary transition-colors">Audit Logs</a>
        {!isLoggedIn ? (
          <>
            <a href="/login" className="hover:text-aegis-primary transition-colors">Login</a>
            <a href="/signup" className="hover:text-aegis-primary transition-colors">Sign Up</a>
          </>
        ) : (
          <>
            <span className="text-sm uppercase tracking-[0.24em] text-aegis-muted">{user?.role || 'OPERATOR'}</span>
            <button onClick={handleLogout} className="text-aegis-primary hover:text-violet-300 transition-colors">Logout</button>
          </>
        )}
      </nav>

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