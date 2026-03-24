export default function Input({ label, type = 'text', id, placeholder, required = false, value, onChange }) {
  return (
    <div className="mb-4">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-aegis-muted mb-1">
          {label} {required && <span className="text-aegis-danger">*</span>}
        </label>
      )}
      <input
        type={type}
        id={id}
        name={id}
        value={value}
        onChange={onChange}
        required={required}
        placeholder={placeholder}
        style={{ color: 'white' }} /* Absolute fallback to force white text */
        className="w-full px-4 py-3 bg-[#0f172a] border border-slate-700 rounded-md !text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-aegis-primary focus:border-transparent transition-all duration-200 autofill:bg-[#0f172a] autofill:text-white"
      />
    </div>
  );
}