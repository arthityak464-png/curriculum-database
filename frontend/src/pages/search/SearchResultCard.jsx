import { ChevronRight, Target } from 'lucide-react';
import Badge from '../../components/ui/Badge';
import { getDisplayCode } from '../../lib/curriculum';
import Highlight from './Highlight';

const MATCH_LABELS = {
  both: { label: 'ตรงทั้งคำและความหมาย', tone: 'ok' },
  keyword: { label: 'ตรงคำค้น', tone: 'ok' },
  semantic: { label: 'ความหมายใกล้เคียง', tone: 'info' },
};

/** ระดับความเกี่ยวข้องจากค่า cosine similarity (ปรับเกณฑ์ได้ตามข้อมูลจริง) */
function relevanceLevel(similarity) {
  if (similarity == null) return null;
  if (similarity >= 0.65) return { label: 'เกี่ยวข้องสูง', bar: 'bg-ok' };
  if (similarity >= 0.55) return { label: 'เกี่ยวข้อง', bar: 'bg-ksu-blue' };
  return { label: 'ใกล้เคียง', bar: 'bg-ksu-emblem' };
}

export default function SearchResultCard({ item, query, rank, onOpen }) {
  // รองรับทั้ง API ใหม่ (score/match_type) และ API เดิม (similarity_score/is_keyword_match)
  const score = item.score ?? item.similarity_score ?? 0;
  const matchType = item.match_type || (item.is_keyword_match ? 'keyword' : 'semantic');
  const match = MATCH_LABELS[matchType] || MATCH_LABELS.semantic;
  const level = relevanceLevel(item.similarity);
  const topPlo = item.related_plos?.[0];

  return (
    <article>
      <button
        type="button"
        onClick={() => onOpen(item)}
        className="group flex w-full flex-col gap-4 rounded-2xl border border-line bg-white p-5 text-left transition hover:border-ksu-emblem hover:shadow-md sm:flex-row sm:items-center"
      >
        <span className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-full bg-ksu-mist font-mono text-sm font-semibold text-ksu-navy sm:flex">
          {rank}
        </span>

        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-lg bg-ksu-mist px-2.5 py-0.5 font-mono text-sm font-semibold text-ksu-blue">{item.course_code}</span>
            <h3 className="text-base font-semibold text-ink group-hover:text-ksu-blue">
              <Highlight text={item.course_name_th} query={query} />
            </h3>
          </div>
          {item.course_name_en && (
            <p className="text-sm text-muted"><Highlight text={item.course_name_en} query={query} /></p>
          )}
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge tone="neutral" title={item.curriculum_name_th}>{getDisplayCode({ code: item.curriculum_code, name: item.curriculum_name_th, department: item.department })}</Badge>
            {item.course_group && <Badge>{item.course_group}</Badge>}
            <Badge>{item.total_credits ?? '-'} หน่วยกิต</Badge>
            <Badge tone={match.tone} dot>{match.label}</Badge>
          </div>
          <p className="line-clamp-2 text-sm leading-relaxed text-muted">
            <Highlight text={item.description_th || item.description_en || 'ไม่มีคำอธิบายรายวิชา'} query={query} />
          </p>
          {(item.matched_fields?.length > 0 || topPlo) && (
            <div className="flex flex-col gap-1 text-xs text-muted">
              {item.matched_fields?.length > 0 && <span>พบคำค้นใน: {item.matched_fields.join(', ')}</span>}
              {topPlo && (
                <span className="flex items-start gap-1.5">
                  <Target className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ksu-blue" aria-hidden="true" />
                  <span className="line-clamp-1">
                    สอดคล้องกับ <strong className="font-mono text-ksu-navy">{topPlo.plo_code}</strong> {topPlo.plo_description}
                  </span>
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-4 sm:w-40 sm:flex-col sm:items-stretch sm:gap-1.5">
          <div className="flex items-baseline justify-between gap-2">
            <span className="text-xs text-muted">{level?.label || 'คะแนน'}</span>
            <span className="font-mono text-lg font-semibold text-ksu-navy">{Number(score).toFixed(0)}</span>
          </div>
          <div className="h-2 w-24 overflow-hidden rounded-full bg-ksu-mist sm:w-full" aria-hidden="true">
            <div className={`h-full rounded-full ${level?.bar || 'bg-ksu-blue'}`} style={{ width: `${Math.min(100, Math.max(4, score))}%` }} />
          </div>
          <span className="ml-auto flex items-center gap-1 text-sm font-semibold text-ksu-blue sm:ml-0 sm:justify-end">
            ดูรายละเอียด <ChevronRight className="h-4 w-4 transition group-hover:translate-x-0.5" aria-hidden="true" />
          </span>
        </div>
      </button>
    </article>
  );
}
