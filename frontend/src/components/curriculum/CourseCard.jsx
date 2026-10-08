import { ChevronRight } from 'lucide-react';
import Badge from '../ui/Badge';
import { creditPattern, prerequisiteText } from '../../lib/curriculum';

/** การ์ดรายวิชาในคลังหลักสูตร */
export default function CourseCard({ course, onOpen }) {
  const prereq = prerequisiteText(course.prerequisites);
  return (
    <button
      type="button"
      onClick={() => onOpen(course)}
      className="group flex h-full flex-col justify-between rounded-2xl border border-line bg-white p-4 text-left transition hover:border-ksu-emblem hover:shadow-md"
    >
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <span className="font-mono text-sm font-semibold text-ksu-blue">{course.course_code}</span>
          <Badge mono>{course.total_credits ?? '-'} ({creditPattern(course)})</Badge>
        </div>
        <div>
          <h3 className="font-semibold text-ink group-hover:text-ksu-blue">{course.course_name_th}</h3>
          {course.course_name_en && <p className="line-clamp-1 text-sm text-muted">{course.course_name_en}</p>}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {course.course_group && <Badge>{course.course_group}</Badge>}
          {course.study_year && <Badge tone="info">ปี {course.study_year} ภาค {course.study_semester || 1}</Badge>}
        </div>
        {prereq && <p className="line-clamp-1 text-xs font-medium text-warn-fg">วิชาบังคับก่อน: {prereq}</p>}
        <p className="line-clamp-2 text-sm leading-relaxed text-muted">{course.description_th || 'ไม่มีคำอธิบายรายวิชา'}</p>
      </div>
      <span className="mt-3 flex items-center justify-between border-t border-line pt-3 text-sm font-semibold text-ksu-blue">
        ดูรายละเอียด
        <ChevronRight className="h-4 w-4 transition group-hover:translate-x-0.5" aria-hidden="true" />
      </span>
    </button>
  );
}
