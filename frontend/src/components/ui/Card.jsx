/** กล่องเนื้อหามาตรฐาน มีหัวข้อและปุ่มด้านขวาได้ */
export default function Card({ title, description, actions, className = '', bodyClassName = '', children, as: Tag = 'section' }) {
  return (
    <Tag className={`rounded-2xl border border-line bg-white ${className}`}>
      {(title || actions) && (
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
          <div className="min-w-0">
            {title && <h2 className="text-base font-semibold text-ink">{title}</h2>}
            {description && <p className="mt-0.5 text-sm text-muted">{description}</p>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
    </Tag>
  );
}
