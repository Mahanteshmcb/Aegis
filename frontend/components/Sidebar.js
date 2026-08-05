import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import useCurrentUser from '../hooks/useCurrentUser';
import {
  Home,
  Layers,
  Thermometer,
  ShieldCheck,
  Droplet,
  Trash2,
  Cpu,
  Sparkles,
  User,
  FileText,
  Shield,
  Settings2,
  LogOut,
  Sliders,
} from 'lucide-react';

export default function Sidebar() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const navItems = [
    { name: 'Estate Dashboard', path: '/estate-dashboard', icon: Home },
    { name: 'Zones', path: '/zones', icon: Layers },
    { name: 'Sensors', path: '/sensors', icon: Thermometer },
    { name: 'Climate', path: '/environmental', icon: Shield },
    { name: 'Safety', path: '/safety-dashboard', icon: ShieldCheck },
    { name: 'Water', path: '/water-dashboard', icon: Droplet },
    { name: 'Waste', path: '/waste-dashboard', icon: Trash2 },
    { name: 'System', path: '/system-control', icon: Cpu },
    { name: 'Vryndara AI', path: '/ai', icon: Sparkles },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  const controlItems = [
    { name: 'Task Scheduler', path: '/task-scheduler', icon: Sparkles },
    { name: 'Lab Automation', path: '/lab-automation', icon: Cpu },
    { name: 'Schedules', path: '/schedules', icon: Layers },
    { name: 'System Analytics', path: '/system-analytics', icon: Cpu },
    { name: 'Communication', path: '/communication-channels', icon: ShieldCheck },
    { name: 'Alerts Config', path: '/alerts-configuration', icon: FileText },
    { name: 'Storage', path: '/storage', icon: Droplet },
  ];

  const adminItems = [
    { name: 'User Management', path: '/admin/users' },
    { name: 'Role Management', path: '/admin/roles' },
    { name: 'Tenant Settings', path: '/admin/settings' },
  ];

  const auditorItems = [
    { name: 'Compliance Reports', path: '/auditor/reports' },
    { name: 'Evidence Review', path: '/auditor/evidence' },
  ];

  const getRoleColor = (role) => {
    switch (role?.toLowerCase()) {
      case 'admin':
        return 'text-red-400';
      case 'auditor':
        return 'text-yellow-400';
      case 'operator':
        return 'text-blue-400';
      case 'viewer':
        return 'text-green-400';
      default:
        return 'text-aegis-muted';
    }
  };

  const [mobileOpen, setMobileOpen] = useState(false);
  const [navOffset, setNavOffset] = useState(0);
  const [showSlider, setShowSlider] = useState(true);
  useEffect(() => {
    try {
      const saved = localStorage.getItem('sidebarNavOffset');
      if (saved !== null) setNavOffset(Number(saved));
    } catch (e) {
      // ignore
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('sidebarNavOffset', String(navOffset));
    } catch (e) {
      // ignore
    }
  }, [navOffset]);

  useEffect(() => {
    const handler = () => setMobileOpen((v) => !v);
    window.addEventListener('aegis_toggle_sidebar', handler);
    return () => window.removeEventListener('aegis_toggle_sidebar', handler);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [router.pathname]);

  return (
    <>
      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-64 bg-[#07111f] border-r border-slate-800 flex flex-col h-full">
            <div className="p-6 border-b border-slate-800">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-aegis-primary tracking-widest">AEGIS</h1>
                  <p className="text-xs text-aegis-muted mt-1 uppercase">Sovereign Digital Twin</p>
                </div>
                <button className="p-1 rounded text-aegis-muted" onClick={() => setMobileOpen(false)} aria-label="Close sidebar">✕</button>
              </div>
              {!loading && user && (
                <div className="mt-3 pt-3 border-t border-slate-700">
                  <p className="text-xs text-aegis-muted">Operator</p>
                  <p className="text-sm text-white truncate font-mono">{user.email}</p>
                  <p className={`text-xs font-bold mt-1 ${getRoleColor(user.role)}`}>
                    [{user.role?.toUpperCase()}]
                  </p>
                </div>
              )}
            </div>
              {/* Mobile offset slider (moved to top for visibility) */}
              <div className="p-3 border-t border-slate-800 md:hidden">
                <label className="text-xs text-aegis-muted mb-1 block">Adjust pages</label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={-200}
                    max={200}
                    step={5}
                    value={navOffset}
                    onChange={(e) => setNavOffset(Number(e.target.value))}
                    className="w-full"
                    aria-label="Adjust sidebar pages vertical offset"
                  />
                  <span className="text-xs text-aegis-muted w-10 text-right">{navOffset}px</span>
                </div>
              </div>

              <nav className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800/50 scroll-smooth pr-2">
              <div className="p-6 space-y-3" style={{transform: `translateY(${navOffset}px)`}}>
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = router.pathname === item.path;
                return (
                  <Link
                    key={item.name}
                    href={item.path}
                    className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-all duration-200 whitespace-nowrap ${
                      isActive ? 'bg-slate-900 text-white ring-1 ring-aegis-primary' : 'text-aegis-text hover:bg-slate-800 hover:text-aegis-primary'
                    }`}
                    onClick={() => setMobileOpen(false)}
                  >
                    <Icon className="h-4 w-4 flex-shrink-0" />
                    {item.name}
                  </Link>
                );
              })}

              <div className="pt-6 border-t border-slate-800 space-y-2">
                <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted px-2">Control Panels</p>
                {controlItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = router.pathname === item.path;
                  return (
                    <Link
                      key={item.name}
                      href={item.path}
                      className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-all duration-200 whitespace-nowrap ${
                        isActive ? 'bg-slate-900 text-white ring-1 ring-aegis-primary' : 'text-aegis-text hover:bg-slate-800 hover:text-aegis-primary'
                      }`}
                      onClick={() => setMobileOpen(false)}
                    >
                      <Icon className="h-4 w-4 flex-shrink-0" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>

              {/* Auditor Section */}
              {!loading && (user?.role === 'auditor' || user?.role === 'admin') && (
                <div className="pt-4 border-t border-slate-800 space-y-2">
                  <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Audit</p>
                  {auditorItems.map((item) => (
                    <Link
                      key={item.name}
                      href={item.path}
                      className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-text hover:bg-slate-800 hover:text-aegis-primary transition-all duration-200"
                      onClick={() => setMobileOpen(false)}
                    >
                      <FileText className="h-4 w-4" />
                      {item.name}
                    </Link>
                  ))}
                </div>
              )}

              {/* Admin Section */}
              {!loading && user?.role === 'admin' && (
                <div className="pt-4 border-t border-slate-800 space-y-2">
                  <p className="text-xs uppercase tracking-[0.3em] text-red-400">Admin Actions</p>
                  {adminItems.map((item) => (
                    <Link
                      key={item.name}
                      href={item.path}
                      className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-text hover:bg-slate-800 hover:text-red-300 transition-all duration-200"
                      onClick={() => setMobileOpen(false)}
                    >
                      <Settings2 className="h-4 w-4" />
                      {item.name}
                    </Link>
                  ))}
                </div>
              )}

            {/* Auth Links */}
            {!loading && !user && (
              <div className="pt-4 border-t border-slate-800 space-y-2">
                <Link
                  href="/login"
                  className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-all duration-200"
                  onClick={() => setMobileOpen(false)}
                >
                  <User className="h-4 w-4" />
                  Login
                </Link>
                <Link
                  href="/signup"
                  className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-all duration-200"
                  onClick={() => setMobileOpen(false)}
                >
                  <Sparkles className="h-4 w-4" />
                  Sign Up
                </Link>
              </div>
            )}

            {/* Logout */}
            {!loading && user && (
              <div className="pt-4 border-t border-slate-800">
                <button
                  onClick={() => {
                    localStorage.removeItem('aegis_token');
                    setMobileOpen(false);
                    router.push('/login');
                  }}
                  className="w-full flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-red-400 hover:bg-red-900/20 hover:text-red-300 transition-all duration-200"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            )}
            </div>
            </nav>
          </aside>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="w-64 bg-[#07111f] border-r border-slate-800 hidden md:flex flex-col h-screen overflow-hidden relative">
        <div className="p-6 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-aegis-primary tracking-widest">AEGIS</h1>
            <button
              className="p-1 rounded text-aegis-muted hover:text-aegis-primary"
              onClick={() => setShowSlider((s) => !s)}
              aria-label="Toggle sidebar slider"
            >
              <Sliders className="h-5 w-5" />
            </button>
          </div>
          <p className="text-xs text-aegis-muted mt-1 uppercase">Sovereign Digital Twin</p>
          {!loading && user && (
            <div className="mt-3 pt-3 border-t border-slate-700">
              <p className="text-xs text-aegis-muted">Operator</p>
              <p className="text-sm text-white truncate font-mono">{user.email}</p>
              <p className={`text-xs font-bold mt-1 ${getRoleColor(user.role)}`}>
                [{user.role?.toUpperCase()}]
              </p>
            </div>
          )}
        </div>

        <nav className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-800/50 scroll-smooth pr-2">
          <div className="p-6 space-y-3" style={{transform: `translateY(${navOffset}px)`}}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = router.pathname === item.path;
            return (
              <Link
                key={item.name}
                href={item.path}
                className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-all duration-200 whitespace-nowrap ${
                  isActive ? 'bg-slate-900 text-white ring-1 ring-aegis-primary' : 'text-aegis-text hover:bg-slate-800 hover:text-aegis-primary'
                }`}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                {item.name}
              </Link>
            );
          })}

          <div className="pt-6 border-t border-slate-800 space-y-2">
            <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted px-2">Control Panels</p>
            {controlItems.map((item) => {
              const Icon = item.icon;
              const isActive = router.pathname === item.path;
              return (
                <Link
                  key={item.name}
                  href={item.path}
                  className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-all duration-200 whitespace-nowrap ${
                    isActive ? 'bg-slate-900 text-white ring-1 ring-aegis-primary' : 'text-aegis-text hover:bg-slate-800 hover:text-aegis-primary'
                  }`}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </div>

          {/* Auditor Section */}
          {!loading && (user?.role === 'auditor' || user?.role === 'admin') && (
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted px-2">Audit</p>
              {auditorItems.map((item) => (
                <Link
                  key={item.name}
                  href={item.path}
                  className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-text hover:bg-slate-800 hover:text-aegis-primary transition-all duration-200 whitespace-nowrap"
                >
                  <FileText className="h-4 w-4 flex-shrink-0" />
                  {item.name}
                </Link>
              ))}
            </div>
          )}

          {/* Admin Section */}
          {!loading && user?.role === 'admin' && (
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-red-400 px-2">Admin Actions</p>
              {adminItems.map((item) => (
                <Link
                  key={item.name}
                  href={item.path}
                  className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-text hover:bg-slate-800 hover:text-red-300 transition-all duration-200 whitespace-nowrap"
                >
                  <Settings2 className="h-4 w-4 flex-shrink-0" />
                  {item.name}
                </Link>
              ))}
            </div>
          )}

          {/* Auth Links */}
          {!loading && !user && (
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <Link
                href="/login"
                className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-all duration-200"
              >
                <User className="h-4 w-4" />
                Login
              </Link>
              <Link
                href="/signup"
                className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-all duration-200"
              >
                <Sparkles className="h-4 w-4" />
                Sign Up
              </Link>
            </div>
          )}

          {/* Logout */}
          {!loading && user && (
            <div className="pt-4 border-t border-slate-800">
              <button
                onClick={() => {
                  localStorage.removeItem('aegis_token');
                  router.push('/login');
                }}
                className="w-full flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-red-400 hover:bg-red-900/20 hover:text-red-300 transition-all duration-200"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          )}
          </div>
        </nav>
        {/* Desktop offset slider (vertical, attached to sidebar edge) */}
        {showSlider && (
          <div
            className="hidden md:flex items-center"
            style={{
              position: 'absolute',
              right: -24,
              top: 72,
              transform: 'translateY(0) rotate(-90deg)',
              zIndex: 60,
            }}
          >
            <input
              type="range"
              min={-200}
              max={200}
              step={5}
              value={navOffset}
              onChange={(e) => setNavOffset(Number(e.target.value))}
              style={{ width: 180 }}
              aria-label="Adjust sidebar pages vertical offset"
            />
            <div style={{ transform: 'rotate(90deg)', marginLeft: 8 }} className="text-xs text-aegis-muted">
              {navOffset}px
            </div>
          </div>
        )}
      </aside>
    </>
  );
}