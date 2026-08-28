import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getAuthToken, clearAuthToken } from '../utils/auth';
import { getSystemHealthStatus } from '../utils/api';
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
        const data = await getSystemHealthStatus(token);
        setSysStatus((prev) => ({ ...prev, ...data }));
      } catch (err) {
        console.error('Health Sync Failed:', err);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const statusText = String(sysStatus.status || '').toLowerCase();
  const isWarning = statusText === 'warning' || statusText === 'degraded' || statusText === 'alert';

  return (
    <header className="aegis-header h-16 bg-aegis-dark border-b border-slate-700 flex items-center justify-between px-6">
      <div className="aegis-header-view flex items-center gap-3 min-w-0">
        <button
          onClick={() => window.dispatchEvent(new CustomEvent('aegis_toggle_sidebar'))}
          className="aegis-mobile-menu-trigger p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-aegis-primary"
          aria-label="Toggle sidebar"
        >
          ☰
        </button>
        <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.36em] text-aegis-muted">Current View</p>
        <p className="text-base font-semibold text-white">
          {router.pathname === '/dashboard' || router.pathname === '/estate-dashboard' ? 'Estate Command Center' : router.pathname.replace('/', '').replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
        </p>
      </div>
      </div>

      <div className="aegis-header-session flex items-center gap-4 shrink-0">
        {!isLoggedIn ? (
          <div className="flex items-center gap-3">
            <a href="/login" className="text-sm text-aegis-muted hover:text-aegis-primary transition-colors">Login</a>
            <a href="/signup" className="text-sm text-aegis-muted hover:text-aegis-primary transition-colors">Sign Up</a>
          </div>
        ) : (
          <>
            <span className="text-xs uppercase tracking-[0.24em] text-aegis-muted">{user?.role || 'OPERATOR'}</span>
            <button onClick={handleLogout} className="px-3 py-1 rounded-full border border-aegis-primary text-aegis-primary hover:bg-aegis-primary/10 transition-colors text-sm">Logout</button>
          </>
        )}
      </div>

      <div className="aegis-header-status flex items-center space-x-6 shrink-0">
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