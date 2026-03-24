import Link from 'next/link';

export default function Sidebar() {
  const navItems = [
    { name: 'Dashboard', path: '/' },
    { name: 'Zones', path: '/zones' },
    { name: 'Sensors', path: '/sensors' },
    { name: 'Audit Logs', path: '/audit' },
    { name: 'Vryndara AI', path: '/ai' },
  ];

  return (
    <aside className="w-64 bg-aegis-dark border-r border-slate-700 hidden md:flex flex-col h-screen">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-2xl font-bold text-aegis-primary tracking-wider">AEGIS</h1>
        <p className="text-xs text-aegis-muted mt-1">Sovereign Digital Twin</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <Link key={item.name} href={item.path} className="block px-4 py-2 text-aegis-text hover:bg-slate-800 rounded-md transition-colors">
            {item.name}
          </Link>
        ))}
      </nav>
    </aside>
  );
}