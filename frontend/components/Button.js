export default function Button({ children, variant = 'primary', onClick, type = 'button', className = '' }) {
  const baseStyle = "px-5 py-3 rounded-xl font-semibold transition duration-200 ease-out shadow-aet focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aegis-primary";
  
  const variants = {
    primary: "bg-gradient-to-r from-aegis-primary to-aegis-accent hover:from-sky-400 hover:to-violet-500 text-white shadow-xl focus:ring-aegis-primary",
    secondary: "bg-slate-700 hover:bg-slate-600 text-white shadow-lg focus:ring-slate-500",
    danger: "bg-aegis-danger hover:bg-red-500 text-white shadow-lg focus:ring-aegis-danger",
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