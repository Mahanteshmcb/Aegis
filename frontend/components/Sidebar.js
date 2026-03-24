export default function Sidebar() {
  return (
    <aside className="bg-gray-100 w-64 min-h-screen p-6 hidden md:block border-r">
      <nav className="space-y-4">
        <a href="#" className="block text-gray-700 hover:text-blue-600 font-medium">Overview</a>
        <a href="#" className="block text-gray-700 hover:text-blue-600 font-medium">Sensors</a>
        <a href="#" className="block text-gray-700 hover:text-blue-600 font-medium">Zones</a>
        <a href="#" className="block text-gray-700 hover:text-blue-600 font-medium">Audit Logs</a>
        <a href="#" className="block text-gray-700 hover:text-blue-600 font-medium">Settings</a>
      </nav>
    </aside>
  );
}
