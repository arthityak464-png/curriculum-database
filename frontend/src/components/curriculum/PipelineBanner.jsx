import { CheckCircle2, Loader2, X, XCircle } from 'lucide-react';

/** แถบสถานะงานสกัดข้อมูลใต้ส่วนหัว */
export default function PipelineBanner({ job, onDismiss }) {
  if (!job) return null;
  const running = !['completed', 'failed'].includes(job.status);
  const failed = job.status === 'failed';
  const progress = Math.min(100, Math.max(0, Number(job.progress) || 0));

  const tone = failed
    ? 'border-danger/20 bg-danger-bg text-danger'
    : running
      ? 'border-ksu-lilac bg-ksu-mist text-ksu-navy'
      : 'border-ok/20 bg-ok-bg text-ok-fg';
  const Icon = failed ? XCircle : running ? Loader2 : CheckCircle2;

  return (
    <div role="status" className={`border-b px-6 py-2.5 text-sm ${tone}`}>
      <div className="flex items-center gap-3">
        <Icon className={`h-4 w-4 shrink-0 ${running ? 'animate-spin' : ''}`} aria-hidden="true" />
        <span className="min-w-0 flex-1 truncate">
          <strong className="font-semibold">{job.filename || 'เอกสาร'}</strong> · {job.message}
        </span>
        {running ? (
          <span className="font-mono font-semibold">{progress}%</span>
        ) : (
          <button type="button" onClick={onDismiss} aria-label="ปิดแถบสถานะ" className="rounded p-1 hover:bg-white/60">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
      {running && (
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/70">
          <div className="h-full rounded-full bg-ksu-blue transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}
