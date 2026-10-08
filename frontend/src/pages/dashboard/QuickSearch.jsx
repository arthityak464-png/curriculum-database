import { useState } from 'react';
import { Search, Sparkles } from 'lucide-react';
import { Button } from '../../components/ui';
import { navigate, paths } from '../../lib/router';
import { SEARCH_SUGGESTIONS } from '../search/suggestions';

/** ช่องค้นหาด่วนบนหน้าภาพรวม → พาไปหน้าค้นหาเต็ม */
export default function QuickSearch() {
  const [query, setQuery] = useState('');

  const submit = (e) => {
    e.preventDefault();
    if (query.trim()) navigate(paths.search(query.trim()));
  };

  return (
    <section className="rounded-2xl border border-line bg-white p-5">
      <form onSubmit={submit} className="flex flex-col gap-3 sm:flex-row">
        <label className="flex min-h-12 flex-1 items-center gap-3 rounded-xl border-2 border-ksu-lilac px-4 focus-within:border-ksu-blue">
          <Sparkles className="h-5 w-5 shrink-0 text-ksu-blue" aria-hidden="true" />
          <span className="sr-only">ค้นหารายวิชาด้วย AI</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ค้นหารายวิชาด้วย AI เช่น การเขียนโปรแกรม, ระบบควบคุมอัตโนมัติ"
            className="min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-subtle"
          />
        </label>
        <Button type="submit" icon={Search} disabled={!query.trim()} className="min-h-12 px-6">ค้นหา</Button>
      </form>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-muted">ลองค้น:</span>
        {SEARCH_SUGGESTIONS.slice(0, 3).map((s) => (
          <a key={s} href={paths.search(s)} className="rounded-full border border-line-strong px-3 py-1 text-ksu-navy no-underline hover:bg-ksu-mist">
            {s}
          </a>
        ))}
      </div>
    </section>
  );
}
