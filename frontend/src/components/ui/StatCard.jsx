const TONES = {
  neutral: { card: 'border-line bg-white', label: 'text-muted', value: 'text-ksu-navy', icon: 'bg-ksu-mist text-ksu-blue' },
  warn: { card: 'border-warn-line bg-[#fffaf4]', label: 'text-warn-fg', value: 'text-warn-fg', icon: 'bg-warn-bg text-warn-fg' },
  ok: { card: 'border-line bg-white', label: 'text-ok-fg', value: 'text-ok-fg', icon: 'bg-ok-bg text-ok-fg' },
};

export default function StatCard({ label, value, hint, icon: Icon, tone = 'neutral', onClick, active = false }) {
  const t = TONES[tone];
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      aria-pressed={onClick ? active : undefined}
      className={`flex items-center justify-between gap-4 rounded-2xl border p-5 text-left transition ${t.card} ${
        onClick ? 'cursor-pointer hover:shadow-md' : ''
      } ${active ? 'ring-2 ring-ksu-blue' : ''}`}
    >
      <div>
        <p className={`text-sm font-medium ${t.label}`}>{label}</p>
        <p className={`mt-1 text-3xl font-bold ${t.value}`}>{value}</p>
        {hint && <p className={`mt-0.5 text-xs ${t.label}`}>{hint}</p>}
      </div>
      {Icon && (
        <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${t.icon}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      )}
    </Tag>
  );
}
