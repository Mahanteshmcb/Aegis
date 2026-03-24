export default function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded shadow p-6 ${className}`}>
      {children}
    </div>
  );
}
