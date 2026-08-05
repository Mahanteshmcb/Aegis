export default function ConfirmModal({ open, title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', loading, onConfirm, onCancel }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-6">
      <div className="w-full max-w-md rounded-3xl border border-slate-700 bg-slate-950 p-6 shadow-2xl shadow-black/40">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-white">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">{message}</p>
        </div>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button type="button" onClick={onCancel} className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm font-semibold text-slate-200 hover:border-slate-500 transition-all">
            {cancelLabel}
          </button>
          <button type="button" onClick={onConfirm} disabled={loading} className="rounded-2xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white hover:bg-rose-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
            {loading ? 'Deleting...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
