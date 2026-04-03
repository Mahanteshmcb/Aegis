import Link from 'next/link';
import useCurrentUser from '../hooks/useCurrentUser';

export default function Sidebar() {
  const { user, loading } = useCurrentUser();
  const navItems = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Zones', path: '/zones' },
    { name: 'Sensors', path: '/sensors' },
    { name: 'Audit Logs', path: '/audit-logs' },
    { name: 'Vryndara AI', path: '/ai' },
    { name: 'Profile', path: '/profile' },
  ];

  const adminItems = [
    { name: 'User Management', path: '/admin/users' },
  ];

  return (
    <aside className="w-64 bg-[#07111f] border-r border-slate-800 hidden md:flex flex-col h-screen">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-2xl font-bold text-aegis-primary tracking-widest">AEGIS</h1>
        <p className="text-xs text-aegis-muted mt-1 uppercase">Sovereign Digital Twin</p>
      </div>
      <nav className="flex-1 p-6 space-y-3">
        {navItems.map((item) => (
          <Link key={item.name} href={item.path} className="block rounded-2xl px-4 py-3 text-aegis-text hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200">
            {item.name}
          </Link>
        ))}

        {!loading && user?.role === 'ADMIN' && (
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <p className="text-xs uppercase tracking-[0.3em] text-aegis-muted">Admin Actions</p>
            {adminItems.map((item) => (
              <Link key={item.name} href={item.path} className="block rounded-2xl px-4 py-3 text-aegis-text hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200">
                {item.name}
              </Link>
            ))}
          </div>
        )}

        <div className="pt-4 border-t border-slate-800">
          <Link href="/login" className="block rounded-2xl px-4 py-3 text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200">
            Login
          </Link>
          <Link href="/signup" className="mt-2 block rounded-2xl px-4 py-3 text-aegis-muted hover:bg-slate-800 hover:text-aegis-primary transition-colors duration-200">
            Sign Up
          </Link>
        </div>
      </nav>
    </aside>
  );
}