import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

export default function Sidebar() {
  const { user, loading } = useCurrentUser();
  const navItems = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Zones', path: '/zones' },
    { name: 'Sensors', path: '/sensors' },
    { name: 'Audit Logs', path: '/audit-logs' },
    { name: 'System Control', path: '/system-control' },
    { name: 'Vryndara AI', path: '/ai' },
    { name: 'Profile', path: '/profile' },
  ];

  const adminItems = [
    { name: 'User Management', path: '/admin/users' },
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

  return (
    <aside className="w-64 bg-[#07111f] border-r border-slate-800 hidden md:flex flex-col h-screen">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-2xl font-bold text-aegis-primary tracking-widest">AEGIS</h1>
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

      <nav className="flex-1 p-6 space-y-3 overflow-y-auto">
        {/* Standard Navigation */}
        {navItems.map((item) => (
          <Link 
            key={item.name} 
            href={item.path} 
            className="block rounded-2xl px-4 py-3 text-aegis-text hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200"
          >
            {item.name}
          </Link>
        ))}

        {/* Auditor Section */}
        {!loading && (user?.role === 'auditor' || user?.role === 'admin') && (
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Audit</p>
            {auditorItems.map((item) => (
              <Link 
                key={item.name} 
                href={item.path} 
                className="block rounded-2xl px-4 py-3 text-aegis-text hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200"
              >
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
                className="block rounded-2xl px-4 py-3 text-aegis-text hover:bg-slate-800 hover:text-red-300 transition-colors duration-200"
              >
                {item.name}
              </Link>
            ))}
          </div>
        )}

        {/* Auth Links */}
        <div className="pt-4 border-t border-slate-800 space-y-2">
          <Link 
            href="/login" 
            className="block rounded-2xl px-4 py-3 text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200"
          >
            Login
          </Link>
          <Link 
            href="/signup" 
            className="block rounded-2xl px-4 py-3 text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200"
          >
            Sign Up
          </Link>
        </div>
      </nav>
    </aside>
  );
}