import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useEffect, useRef, useCallback } from 'react';
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
  Square,
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
    { name: '3D Scene', path: '/3d-scene', icon: Square },
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
  const [desktopOpen, setDesktopOpen] = useState(true);
  const mobileNavRef = useRef(null);
  const desktopNavRef = useRef(null);
  const itemRefs = useRef({});

  const scrollActiveIntoView = useCallback(() => {
    const activeEl = itemRefs.current[router.pathname];
    const container = mobileOpen ? mobileNavRef.current : desktopNavRef.current;
    if (activeEl && container) {
      try {
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } catch (e) {
        const offset = activeEl.offsetTop - container.clientHeight / 2 + activeEl.clientHeight / 2;
        container.scrollTop = Math.max(0, offset);
      }
      // nothing else to sync; native scrollbar is authoritative
    }
  }, [router.pathname, mobileOpen]);

  useEffect(() => {
    const handler = () => {
      if (window.matchMedia('(max-width: 767px)').matches) {
        setMobileOpen((value) => !value);
      } else {
        setDesktopOpen((value) => !value);
      }
    };
    window.addEventListener('aegis_toggle_sidebar', handler);
    return () => window.removeEventListener('aegis_toggle_sidebar', handler);
  }, []);

  useEffect(() => {
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setMobileOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, []);

  useEffect(() => {
    if (!mobileOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [mobileOpen]);

  useEffect(() => {
    setMobileOpen(false);
  }, [router.pathname]);

  // Ensure active nav item is visible on route change or when opening mobile drawer
  useEffect(() => {
    scrollActiveIntoView();
  }, [router.pathname, scrollActiveIntoView]);

  useEffect(() => {
    if (mobileOpen) scrollActiveIntoView();
  }, [mobileOpen, scrollActiveIntoView]);

  return (
    <>
      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="aegis-mobile-sidebar-shell fixed inset-0 z-50 overscroll-contain">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} aria-hidden="true" />
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
              {/* Mobile: use native scrolling; removed custom slider for reliability */}

              <nav
                ref={mobileNavRef}
                className="aegis-sidebar-scroll min-h-0 flex-1 basis-0 overflow-y-scroll overflow-x-hidden overscroll-contain scroll-smooth pr-2 touch-pan-y"
                style={{ height: 'calc(100dvh - 180px)', maxHeight: 'calc(100dvh - 180px)', WebkitOverflowScrolling: 'touch' }}
              >
              <div className="aegis-sidebar-content p-6 space-y-3">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = router.pathname === item.path;
                return (
                  <Link key={item.name} href={item.path} legacyBehavior>
                    <a
                      className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-all duration-200 whitespace-nowrap ${
                        isActive ? 'bg-slate-900 text-white ring-1 ring-aegis-primary' : 'text-aegis-text hover:bg-slate-800 hover:text-aegis-primary'
                      }`}
                      onClick={() => setMobileOpen(false)}
                      ref={(el) => (itemRefs.current[item.path] = el)}
                      data-active={isActive}
                    >
                      <Icon className="h-4 w-4 flex-shrink-0" />
                      {item.name}
                    </a>
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

              {/* Desktop: native scrollbar used; slider removed for consistent UX */}

              {/* Auditor Section */}
              {(
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
              {(
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
      {desktopOpen && <aside className="aegis-desktop-sidebar w-64 bg-[#07111f] border-r border-slate-800 flex flex-col h-screen overflow-visible relative">
        <div className="p-6 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-aegis-primary tracking-widest">AEGIS</h1>
            <button
              className="rounded bg-slate-700 px-2 py-1 text-lg leading-none text-white hover:bg-slate-600"
              onClick={() => setDesktopOpen(false)}
              aria-label="Close sidebar"
              title="Close sidebar"
            >
              ×
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

            <nav
              ref={desktopNavRef}
              className="aegis-sidebar-scroll min-h-0 flex-1 basis-0 overflow-y-scroll overflow-x-hidden overscroll-contain scroll-smooth pr-2"
            >
          <div className="aegis-sidebar-content p-6 space-y-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = router.pathname === item.path;
            return (
              <Link key={item.name} href={item.path} legacyBehavior>
                <a
                  className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-all duration-200 whitespace-nowrap ${
                    isActive ? 'bg-slate-900 text-white ring-1 ring-aegis-primary' : 'text-aegis-text hover:bg-slate-800 hover:text-aegis-primary'
                  }`}
                  ref={(el) => (itemRefs.current[item.path] = el)}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  {item.name}
                </a>
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
          {(
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
          {(
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
      </aside>}
      {!desktopOpen && (
        <button
          className="aegis-desktop-sidebar-reopen fixed left-3 top-3 z-40 rounded bg-slate-700 px-3 py-2 text-lg leading-none text-white shadow-lg hover:bg-slate-600"
          onClick={() => setDesktopOpen(true)}
          aria-label="Open sidebar"
          title="Open sidebar"
        >
          ☰
        </button>
      )}
    </>
  );
}