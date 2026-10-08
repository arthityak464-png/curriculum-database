import { useState } from 'react';
import { Save } from 'lucide-react';
import { Button, inputClass, labelClass, textareaClass } from '../../components/ui';
import InstructorTable from '../../components/curriculum/InstructorTable';

const EDITABLE_FIELDS = ['curriculum_name_th', 'curriculum_name_en', 'total_credits', 'philosophy', 'objectives', 'graduate_attributes', 'responsible_instructors'];

/** ส่วนที่ 1: ข้อมูลทั่วไปของหลักสูตร (แก้ไขได้) */
export default function GeneralSection({ detail, saving, onSave }) {
  const [form, setForm] = useState(() => ({ ...detail }));
  const dirty = EDITABLE_FIELDS.some((key) => String(form[key] ?? '') !== String(detail[key] ?? ''));
  const set = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const submit = (e) => {
    e.preventDefault();
    onSave({
      curriculum_name_th: form.curriculum_name_th,
      curriculum_name_en: form.curriculum_name_en,
      total_credits: form.total_credits === '' || form.total_credits == null ? null : Number(form.total_credits),
      philosophy: form.philosophy,
      objectives: form.objectives,
      graduate_attributes: form.graduate_attributes,
      responsible_instructors: form.responsible_instructors,
    });
  };

  const instructorCount = Array.isArray(form.responsible_instructors) ? form.responsible_instructors.length : 0;

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="grid gap-4">
        <label className="block">
          <span className={labelClass}>ชื่อหลักสูตร (ภาษาไทย)</span>
          <input className={inputClass} value={form.curriculum_name_th || ''} onChange={set('curriculum_name_th')} />
        </label>
        <label className="block">
          <span className={labelClass}>ชื่อหลักสูตร (ภาษาอังกฤษ)</span>
          <input className={inputClass} value={form.curriculum_name_en || ''} onChange={set('curriculum_name_en')} />
        </label>
        <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
          <label className="block">
            <span className={labelClass}>หน่วยกิตรวม</span>
            <input type="number" min="0" className={`${inputClass} font-mono`} value={form.total_credits ?? ''} onChange={set('total_credits')} />
          </label>
          <label className="block">
            <span className={labelClass}>คณะ / สาขาวิชา</span>
            <input disabled className={inputClass} value={`${form.faculty || '-'} / ${form.department || '-'}`} />
          </label>
        </div>
        <label className="block">
          <span className={labelClass}>ปรัชญาของหลักสูตร</span>
          <textarea rows={3} className={textareaClass} value={form.philosophy || ''} onChange={set('philosophy')} />
        </label>
        <label className="block">
          <span className={labelClass}>วัตถุประสงค์ของหลักสูตร</span>
          <textarea rows={5} className={textareaClass} value={form.objectives || ''} onChange={set('objectives')} />
        </label>
      </div>

      <section className="space-y-2">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-sm font-bold text-ink">อาจารย์ผู้รับผิดชอบหลักสูตร</h3>
          <span className="text-xs text-muted">สกัดได้ {instructorCount} ท่าน</span>
        </div>
        <InstructorTable instructors={form.responsible_instructors} />
      </section>

      <div className="flex items-center justify-end gap-3">
        {dirty && <span className="text-sm font-medium text-warn-fg">มีการแก้ไขที่ยังไม่บันทึก</span>}
        <Button type="submit" variant="secondary" icon={Save} loading={saving} disabled={!dirty}>บันทึกการแก้ไข</Button>
      </div>
    </form>
  );
}
