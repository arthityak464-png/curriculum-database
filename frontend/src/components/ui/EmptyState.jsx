export default function EmptyState({ icon: Icon, title, description, action, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 px-6 py-14 text-center ${className}`}>
      {Icon && (
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-ksu-mist text-ksu-blue">
          <Icon className="h-7 w-7" aria-hidden="true" />
        </span>
      )}
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      {description && <p className="max-w-md text-sm leading-relaxed text-muted">{description}</p>}
      {action}
    </div>
  );
}
