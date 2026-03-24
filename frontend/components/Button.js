export default function Button({ children, variant = 'primary', onClick, type = 'button', className = '' }) {
  const baseStyle = "px-4 py-2 rounded-md font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-aegis-dark";
  
  const variants = {
    primary: "bg-aegis-primary hover:bg-blue-600 text-white focus:ring-aegis-primary",
    secondary: "bg-slate-700 hover:bg-slate-600 text-white focus:ring-slate-500",
    danger: "bg-aegis-danger hover:bg-red-600 text-white focus:ring-aegis-danger",
  };

  return (
    <button 
      type={type} 
      onClick={onClick} 
      className={`${baseStyle} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}