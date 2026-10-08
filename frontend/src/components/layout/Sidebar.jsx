import { LayoutDashboard, LibraryBig, ScanSearch, Sparkles } from 'lucide-react';
import { paths } from '../../lib/router';

/**
 * เมนูหลัก — compact = แสดงเฉพาะไอคอน (ใช้ในห้องตรวจทานที่ต้องการพื้นที่กว้าง)
 */
export default function Sidebar({ page, curriculumId, pendingCount = 0, compact = false }) {
  const items = [
    { key: 'dashboard', label: 'ภาพรวม', icon: LayoutDashboard, href: paths.dashboard() },
    { key: 'search', label: 'ค้นหาด้วย AI', icon: Sparkles, href: paths.search() },
    { key: 'catalog', label: 'คลังหลักสูตร', icon: LibraryBig, href: paths.catalog(curriculumId) },
    { key: 'studio', label: 'ห้องตรวจทาน', icon: ScanSearch, href: paths.studio(curriculumId), badge: pendingCount },
  ];

  return (
    <nav
      aria-label="เมนูหลัก"
      className={`flex shrink-0 gap-1 overflow-x-auto border-b border-line bg-white px-3 py-2 lg:flex-col lg:overflow-visible lg:border-r lg:border-b-0 lg:py-4 ${
        compact ? 'lg:w-[72px] lg:px-2' : 'lg:w-60 lg:px-3'
      }`}
    >
      {items.map(({ key, label, icon: Icon, href, badge }) => {
        const active = page === key;
        return (
          <a
            key={key}
            href={href}
            title={compact ? label : undefined}
            aria-label={compact ? label : undefined}
            aria-current={active ? 'page' : undefined}
            className={`relative flex min-h-11 shrink-0 items-center gap-3 rounded-xl px-3 text-[15px] font-medium no-underline transition ${
              compact ? 'lg:justify-center lg:px-0' : ''
            } ${active ? 'bg-ksu-navy text-white' : 'text-muted hover:bg-ksu-mist hover:text-ksu-navy'}`}
          >
            <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span className={compact ? 'lg:sr-only' : ''}>{label}</span>
            {badge > 0 && (
              <span
                className={`rounded-full bg-warn-bg px-2 text-xs font-bold text-warn-fg ${
                  compact ? 'lg:absolute lg:-top-1 lg:-right-1 lg:px-1.5' : 'ml-auto'
                }`}
              >
                {badge}
              </span>
            )}
          </a>
        );
      })}
    </nav>
  );
}
