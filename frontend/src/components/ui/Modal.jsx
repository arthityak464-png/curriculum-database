import { useEffect, useId } from 'react';
import { X } from 'lucide-react';

const SIZES = { sm: 'max-w-sm', md: 'max-w-lg', lg: 'max-w-3xl', xl: 'max-w-4xl' };

/** หน้าต่างซ้อน ปิดได้ด้วย Esc / คลิกพื้นหลัง / ปุ่ม X */
export default function Modal({ open, onClose, title, description, size = 'md', footer, children, hideClose = false }) {
  const titleId = useId();

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="anim-fade fixed inset-0 z-50 flex items-center justify-center bg-ink/50 p-4 backdrop-blur-[2px]">
      <button type="button" aria-label="ปิดหน้าต่าง" className="absolute inset-0 cursor-default" onClick={onClose} tabIndex={-1} />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        className={`anim-pop relative flex max-h-[88vh] w-full flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ${SIZES[size]}`}
      >
        {(title || !hideClose) && (
          <header className="flex items-start justify-between gap-4 border-b border-line px-6 py-4">
            <div className="min-w-0">
              {title && <h2 id={titleId} className="text-lg font-bold text-ink">{title}</h2>}
              {description && <p className="mt-0.5 text-sm text-muted">{description}</p>}
            </div>
            {!hideClose && (
              <button type="button" onClick={onClose} aria-label="ปิด" className="rounded-lg p-2 text-muted transition hover:bg-ksu-mist hover:text-ink">
                <X className="h-5 w-5" />
              </button>
            )}
          </header>
        )}
        <div className="scroll-thin flex-1 overflow-y-auto px-6 py-5">{children}</div>
        {footer && <footer className="flex flex-wrap justify-end gap-2 border-t border-line bg-canvas px-6 py-4">{footer}</footer>}
      </div>
    </div>
  );
}
