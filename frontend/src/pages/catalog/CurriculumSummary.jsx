import { UserRound } from 'lucide-react';
import { getDisplayCode, normalizeInstructor } from '../../lib/curriculum';

/** สรุปข้อมูลหลักสูตรด้านบนคลังหลักสูตร */
export default function CurriculumSummary({ detail, courseCount, ploCount }) {
  const instructors = Array.isArray(detail?.responsible_instructors) ? detail.responsible_instructors.map(normalizeInstructor) : [];
  const stats = [
    { label: 'หน่วยกิตรวม', value: detail?.total_credits ?? '-' },
    { label: 'รายวิชา', value: courseCount },
    { label: 'PLO', value: ploCount },
  ];

  return (
    <section className="space-y-5 rounded-2xl border border-line bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <span className="rounded-lg bg-ksu-mist px-2.5 py-0.5 font-mono text-sm font-semibold text-ksu-blue" title={detail?.curriculum_code}>
            {getDisplayCode(detail)}
          </span>
          <h2 className="mt-2 text-xl font-bold text-ksu-navy">{detail?.curriculum_name_th || 'เอกสารหลักสูตร'}</h2>
          {detail?.curriculum_name_en && <p className="text-sm text-muted">{detail.curriculum_name_en}</p>}
          <p className="mt-1 text-sm text-ink">{[detail?.faculty, detail?.department].filter(Boolean).join(' · ')}</p>
        </div>
        <dl className="flex gap-6">
          {stats.map((s) => (
            <div key={s.label} className="text-right">
              <dt className="text-xs text-muted">{s.label}</dt>
              <dd className="text-2xl font-bold text-ksu-navy">{s.value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl bg-canvas p-4">
          <h3 className="mb-1 text-sm font-bold text-ink">ปรัชญาของหลักสูตร</h3>
          <p className="line-clamp-4 text-sm leading-relaxed text-muted">{detail?.philosophy || '-'}</p>
        </div>
        <div className="rounded-xl bg-canvas p-4">
          <h3 className="mb-2 text-sm font-bold text-ink">อาจารย์ผู้รับผิดชอบหลักสูตร</h3>
          {instructors.length ? (
            <ul className="flex flex-wrap gap-1.5">
              {instructors.map((inst, i) => (
                <li key={i} className="inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-2.5 py-1 text-xs font-medium text-ksu-navy">
                  <UserRound className="h-3.5 w-3.5" aria-hidden="true" />
                  {inst.position !== '-' ? `${inst.position} ` : ''}{inst.name}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">ไม่มีข้อมูล</p>
          )}
        </div>
      </div>
    </section>
  );
}
