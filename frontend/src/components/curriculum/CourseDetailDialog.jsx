import { AlertTriangle, Target } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { creditPattern, prerequisiteText } from '../../lib/curriculum';

/** รายละเอียดรายวิชาเต็ม (ใช้ทั้งคลังหลักสูตรและหน้าค้นหา) */
export default function CourseDetailDialog({ course, onClose, footerExtra }) {
  if (!course) return null;
  const prereq = prerequisiteText(course.prerequisites);
  const stats = [
    { label: 'หน่วยกิต', value: course.total_credits ?? '-' },
    { label: 'ชั่วโมง (บ-ป-ศ)', value: creditPattern(course), mono: true },
    { label: 'หมวดวิชา', value: course.course_group || '-' },
    { label: 'แผนการศึกษา', value: course.study_year ? `ปี ${course.study_year} ภาค ${course.study_semester || 1}` : '-' },
  ];

  return (
    <Modal
      open
      onClose={onClose}
      size="xl"
      title={
        <span className="flex flex-wrap items-center gap-3">
          <span className="rounded-lg bg-ksu-mist px-3 py-1 font-mono text-base text-ksu-blue">{course.course_code}</span>
          {course.course_name_th}
        </span>
      }
      description={course.course_name_en}
      footer={
        <>
          {footerExtra}
          <Button variant="secondary" onClick={onClose}>ปิด</Button>
        </>
      }
    >
      <div className="space-y-5">
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="rounded-xl border border-line bg-canvas p-3.5">
              <dt className="text-xs text-muted">{s.label}</dt>
              <dd className={`mt-0.5 font-semibold text-ink ${s.mono ? 'font-mono' : ''}`}>{s.value}</dd>
            </div>
          ))}
        </dl>

        {prereq && (
          <p className="flex items-center gap-2 rounded-xl border border-warn-line bg-warn-bg p-3.5 text-sm font-medium text-warn-fg">
            <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
            วิชาบังคับก่อน: <span className="font-mono">{prereq}</span>
          </p>
        )}

        {course.related_plos?.length > 0 && (
          <section>
            <h3 className="mb-2 flex items-center gap-2 text-sm font-bold text-ink">
              <Target className="h-4 w-4 text-ksu-blue" aria-hidden="true" /> PLO ที่เกี่ยวกับคำค้นมากที่สุด
            </h3>
            <ul className="space-y-2">
              {course.related_plos.map((plo) => (
                <li key={plo.plo_code} className="rounded-xl border border-ksu-lilac bg-ksu-mist p-3 text-sm">
                  <span className="mr-2 font-mono font-semibold text-ksu-navy">{plo.plo_code}</span>
                  {plo.plo_description}
                </li>
              ))}
            </ul>
          </section>
        )}

        {course.plo_codes?.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-sm text-muted">รับผิดชอบ PLO:</span>
            {course.plo_codes.map((code) => (
              <Badge key={code} tone="info" mono>{code}</Badge>
            ))}
          </div>
        )}

        <section>
          <h3 className="mb-2 text-sm font-bold text-ink">คำอธิบายรายวิชา</h3>
          <p className="rounded-xl border border-line bg-canvas p-4 text-[15px] leading-7 text-ink">
            {course.description_th || 'ไม่มีคำอธิบายรายวิชาภาษาไทย'}
          </p>
        </section>

        {course.description_en && (
          <section>
            <h3 className="mb-2 text-sm font-bold text-ink">Course Description</h3>
            <p className="rounded-xl border border-line bg-canvas p-4 text-[15px] leading-7 text-muted">{course.description_en}</p>
          </section>
        )}
      </div>
    </Modal>
  );
}
