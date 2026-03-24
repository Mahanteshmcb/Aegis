export default function Header() {
  return (
    <header className="bg-blue-700 text-white px-6 py-4 shadow flex items-center justify-between">
      <div className="text-2xl font-bold tracking-tight">Aegis</div>
      <nav className="space-x-4">
        <a href="#" className="hover:underline">Dashboard</a>
        <a href="#" className="hover:underline">Sensors</a>
        <a href="#" className="hover:underline">Zones</a>
        <a href="#" className="hover:underline">Audit Logs</a>
      </nav>
    </header>
  );
}
