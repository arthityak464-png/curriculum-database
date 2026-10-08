import emblem from '../../assets/ksu-emblem.png';

/** ตรามหาวิทยาลัย + ชื่อระบบ */
export default function BrandLogo({ href = '#/' }) {
  return (
    <a href={href} className="flex min-w-0 items-center gap-3 text-ink no-underline">
      <img src={emblem} alt="ตรามหาวิทยาลัยกาฬสินธุ์" className="h-11 w-auto shrink-0" />
      <span className="flex min-w-0 flex-col border-l border-line pl-3 leading-tight">
        <span className="truncate text-xs text-muted">มหาวิทยาลัยกาฬสินธุ์</span>
        <strong className="truncate text-base text-ksu-navy sm:text-lg">ระบบฐานข้อมูลหลักสูตร มคอ.2</strong>
      </span>
    </a>
  );
}
