import { createContext, useContext, useMemo, useState } from 'react';

const ToastContext = createContext({ addToast: () => {} });

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info', duration = 4000) => {
    const id = Date.now().toString();
    const toast = { id, message, type };
    setToasts((current) => [...current, toast]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== id));
    }, duration);
  };

  const memoValue = useMemo(() => ({ addToast }), []);

  return (
    <ToastContext.Provider value={memoValue}>
      {children}
      <div className="pointer-events-none fixed bottom-6 right-6 z-50 flex w-full max-w-sm flex-col gap-3">
        {toasts.map((toast) => (
          <div key={toast.id} className={`pointer-events-auto rounded-3xl border p-4 shadow-2xl shadow-black/20 ${toast.type === 'success' ? 'border-emerald-500/40 bg-emerald-950 text-emerald-200' : toast.type === 'error' ? 'border-rose-500/40 bg-rose-950 text-rose-200' : 'border-slate-700 bg-slate-950 text-slate-200'}`}>
            <p className="text-sm leading-6">{toast.message}</p>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
