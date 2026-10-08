import { useState } from 'react';
import { Search, Sparkles, X } from 'lucide-react';
import { Button, SelectField } from '../../components/ui';
import { COURSE_GROUPS, cleanCurriculumName, getDisplayCode } from '../../lib/curriculum';
import { navigate, paths } from '../../lib/router';
import { SEARCH_SUGGESTIONS } from './suggestions';

/** ฟอร์มค้นหา + ตัวกรอง (คำค้นเก็บใน URL เพื่อแชร์ลิงก์/กดย้อนกลับได้) */
export default function SearchForm({ initialQuery, curriculums, filters, onFiltersChange, loading }) {
  const [query, setQuery] = useState(initialQuery);

  const submit = (e) => {
    e.preventDefault();
    const q = query.trim();
    if (q) navigate(paths.search(q));
  };

  const curriculumOptions = [
    { value: '', label: 'ทุกหลักสูตรที่อนุมัติแล้ว' },
    ...curriculums.map((c) => ({ value: c.id, label: `${getDisplayCode(c)} · ${cleanCurriculumName(c)}` })),
  ];
  const groupOptions = [{ value: '', label: 'ทุกหมวดวิชา' }, ...COURSE_GROUPS.map((g) => ({ value: g, label: g }))];

  return (
    <section className="space-y-4 rounded-2xl border border-line bg-white p-5">
      <form onSubmit={submit} role="search" className="flex flex-col gap-3 sm:flex-row">
        <label className="flex min-h-14 flex-1 items-center gap-3 rounded-xl border-2 border-ksu-blue bg-white px-4">
          <Sparkles className="h-5 w-5 shrink-0 text-ksu-blue" aria-hidden="true" />
          <span className="sr-only">คำค้นหา</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="อธิบายสิ่งที่อยากหา เช่น วิชาที่สอนเขียนโปรแกรมควบคุมหุ่นยนต์"
            className="min-w-0 flex-1 bg-transparent text-[17px] outline-none placeholder:text-subtle"
            autoFocus={!initialQuery}
          />
          {query && (
            <button type="button" onClick={() => setQuery('')} aria-label="ล้างคำค้น" className="rounded-full p-1 text-subtle hover:bg-ksu-mist hover:text-ink">
              <X className="h-4 w-4" />
            </button>
          )}
        </label>
        <Button type="submit" icon={Search} loading={loading} disabled={!query.trim()} className="min-h-14 px-7 text-base">
          ค้นหา
        </Button>
      </form>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-muted">ลองค้น:</span>
        {SEARCH_SUGGESTIONS.map((s) => (
          <a key={s} href={paths.search(s)} className="rounded-full border border-line-strong px-3 py-1.5 text-ksu-navy no-underline hover:bg-ksu-mist">
            {s}
          </a>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <SelectField
          label="หลักสูตร"
          value={filters.curriculumId}
          onChange={(curriculumId) => onFiltersChange({ ...filters, curriculumId })}
          options={curriculumOptions}
        />
        <SelectField
          label="หมวดวิชา"
          value={filters.courseGroup}
          onChange={(courseGroup) => onFiltersChange({ ...filters, courseGroup })}
          options={groupOptions}
        />
      </div>
    </section>
  );
}
