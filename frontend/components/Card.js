export default function Card({ title, children, className = '' }) {
  return (
    <div className={`bg-aegis-card rounded-lg border border-slate-700 shadow-lg overflow-hidden ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-aegis-text">{title}</h3>
        </div>
      )}
      <div className="p-6 text-aegis-muted">
        {children}
      </div>
    </div>
  );
}