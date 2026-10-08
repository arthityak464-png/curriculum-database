import { useCallback, useMemo, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';
import { ToastContext } from '../../context/toast';

const STYLES = {
  success: { icon: CheckCircle2, className: 'border-ok/30 text-ok-fg', iconClass: 'text-ok' },
  error: { icon: AlertCircle, className: 'border-danger/30 text-danger', iconClass: 'text-danger' },
  info: { icon: Info, className: 'border-ksu-lilac text-ksu-navy', iconClass: 'text-ksu-blue' },
};

export default function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id) => setToasts((prev) => prev.filter((t) => t.id !== id)), []);

  const showToast = useCallback(
    (message, type = 'success') => {
      nextId.current += 1;
      const id = nextId.current;
      setToasts((prev) => [...prev.slice(-2), { id, message, type }]);
      window.setTimeout(() => dismiss(id), type === 'error' ? 7000 : 4000);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed right-4 bottom-4 z-[70] flex w-[min(92vw,380px)] flex-col gap-2">
        {toasts.map((toast) => {
          const style = STYLES[toast.type] || STYLES.info;
          const Icon = style.icon;
          return (
            <div key={toast.id} className={`anim-pop pointer-events-auto flex items-start gap-3 rounded-xl border bg-white p-4 shadow-lg ${style.className}`}>
              <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${style.iconClass}`} aria-hidden="true" />
              <p className="flex-1 text-sm leading-relaxed font-medium">{toast.message}</p>
              <button type="button" onClick={() => dismiss(toast.id)} aria-label="ปิดการแจ้งเตือน" className="rounded p-0.5 text-subtle hover:text-ink">
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
