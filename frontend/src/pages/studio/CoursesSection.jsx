import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { Badge, inputClass } from '../../components/ui';
import { creditPattern, prerequisiteText } from '../../lib/curriculum';

/** ส่วนที่ 2: รายวิชาที่ AI สกัดได้ */
export default function CoursesSection({ courses }) {
  const [text, setText] = useState('');
  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    if (!q) return courses;
    return courses.filter((c) => [c.course_code, c.course_name_th, c.course_name_en].join(' ').toLowerCase().includes(q));
  }, [courses, text]);

  const missingDescription = courses.filter((c) => !c.description_th).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          พบ <strong className="text-ink">{courses.length}</strong> รายวิชา
          {missingDescription > 0 && <span className="text-warn-fg"> · ไม่มีคำอธิบาย {missingDescription} วิชา</span>}
        </p>
        <label className="relative block w-full sm:w-64">
          <span className="sr-only">ค้นหารายวิชา</span>
          <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-subtle" aria-hidden="true" />
          <input type="search" value={text} onChange={(e) => setText(e.target.value)} placeholder="รหัส หรือชื่อวิชา" className={`${inputClass} min-h-10 pl-9 text-sm`} />
        </label>
      </div>

      <ul className="space-y-2">
        {filtered.map((course) => {
          const prereq = prerequisiteText(course.prerequisites);
          const noDescription = !course.description_th;
          return (
            <li
              key={course.id || course.course_code}
              className={`rounded-xl border p-4 ${noDescription ? 'border-warn-line bg-[#fffaf4]' : 'border-line bg-white'}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="flex flex-wrap items-baseline gap-2">
                    <span className="font-mono text-sm font-semibold text-ksu-blue">{course.course_code}</span>
                    <span className="font-semibold text-ink">{course.course_name_th}</span>
                  </p>
                  {course.course_name_en && <p className="text-sm text-muted">{course.course_name_en}</p>}
                </div>
                <Badge mono>{course.total_credits ?? '-'} ({creditPattern(course)})</Badge>
              </div>
              {prereq && <p className="mt-2 text-xs font-medium text-warn-fg">วิชาบังคับก่อน: {prereq}</p>}
              <p className={`mt-2 line-clamp-2 text-sm leading-relaxed ${noDescription ? 'font-medium text-warn-fg' : 'text-muted'}`}>
                {course.description_th || 'ไม่พบคำอธิบายรายวิชา — ตรวจสอบกับเอกสารต้นฉบับ'}
              </p>
            </li>
          );
        })}
        {filtered.length === 0 && <li className="py-10 text-center text-sm text-muted">ไม่พบรายวิชาตามคำค้น</li>}
      </ul>
    </div>
  );
}
