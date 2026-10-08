/**
 * แท็บแบบปุ่มเรียงกัน
 * items: [{ value, label, icon?, done? }]
 */
export default function SegmentedTabs({ items, value, onChange, label, className = '' }) {
  return (
    <div role="tablist" aria-label={label} className={`inline-flex flex-wrap gap-1 rounded-xl bg-ksu-mist p-1 ${className}`}>
      {items.map((item) => {
        const active = item.value === value;
        const Icon = item.icon;
        return (
          <button
            key={item.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(item.value)}
            className={`inline-flex min-h-10 items-center gap-2 rounded-lg px-3.5 text-sm font-semibold transition ${
              active ? 'bg-white text-ksu-navy shadow-sm' : 'text-muted hover:text-ksu-navy'
            }`}
          >
            {Icon && <Icon className="h-4 w-4" aria-hidden="true" />}
            {item.label}
            {item.done && <span className="h-2 w-2 rounded-full bg-ok" aria-label="ตรวจแล้ว" />}
          </button>
        );
      })}
    </div>
  );
}
