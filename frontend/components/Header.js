export default function Header() {
  return (
    <header className="h-16 bg-aegis-dark border-b border-slate-700 flex items-center justify-between px-6">
      <div className="flex items-center">
        {/* Mobile menu button could go here */}
        <span className="text-aegis-muted font-medium">Main Estate (Tenant A)</span>
      </div>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-aegis-success"></div>
          <span className="text-sm text-aegis-muted">System Healthy</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-aegis-primary flex items-center justify-center text-white font-bold">
          A
        </div>
      </div>
    </header>
  );
}