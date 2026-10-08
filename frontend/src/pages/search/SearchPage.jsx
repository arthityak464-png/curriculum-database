import { useEffect, useState } from 'react';
import { AlertCircle, BrainCircuit, CheckCircle2, ExternalLink, FileSearch, FileUp, SearchX } from 'lucide-react';
import { Button, EmptyState } from '../../components/ui';
import PageHeader from '../../components/layout/PageHeader';
import CourseDetailDialog from '../../components/curriculum/CourseDetailDialog';
import * as api from '../../services/api';
import { isVerified } from '../../lib/curriculum';
import { paths } from '../../lib/router';
import SearchForm from './SearchForm';
import SearchResultCard from './SearchResultCard';

const LIMIT = 12;

function ResultSkeleton() {
  return (
    <div className="space-y-3" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <div key={i} className="animate-pulse rounded-2xl border border-line bg-white p-5">
          <div className="h-4 w-1/3 rounded bg-ksu-mist" />
          <div className="mt-3 h-3 w-2/3 rounded bg-ksu-mist" />
          <div className="mt-2 h-3 w-1/2 rounded bg-ksu-mist" />
        </div>
      ))}
    </div>
  );
}

const HOW_IT_WORKS = [
  { icon: FileSearch, title: 'พิมพ์เป็นประโยคธรรมดา', text: 'ไม่จำเป็นต้องรู้ชื่อวิชาหรือรหัส' },
  { icon: BrainCircuit, title: 'AI เทียบความหมาย', text: 'ใช้ bge-m3 เทียบกับคำอธิบายรายวิชาและ PLO' },
  { icon: CheckCircle2, title: 'เฉพาะหลักสูตรที่อนุมัติแล้ว', text: 'ข้อมูลที่ผ่านการตรวจทานโดยคนแล้วเท่านั้น' },
];

export default function SearchPage({ query, curriculums }) {
  const [filters, setFilters] = useState({ curriculumId: '', courseGroup: '' });
  const [response, setResponse] = useState({ key: '', data: null, error: '' });
  const [selected, setSelected] = useState(null);
  const [attempt, setAttempt] = useState(0);

  const verifiedCurriculums = curriculums.filter(isVerified);
  const requestKey = query ? JSON.stringify([query, filters.curriculumId, filters.courseGroup, attempt]) : '';
  const loading = Boolean(requestKey) && response.key !== requestKey;

  useEffect(() => {
    if (!requestKey) return undefined;
    const controller = new AbortController();
    api
      .searchCourses(query, { limit: LIMIT, curriculumId: filters.curriculumId, courseGroup: filters.courseGroup, signal: controller.signal })
      .then((res) => setResponse({ key: requestKey, data: res.data, error: '' }))
      .catch((err) => {
        if (controller.signal.aborted) return;
        setResponse({ key: requestKey, data: null, error: api.getErrorMessage(err) });
      });
    return () => controller.abort();
  }, [requestKey, query, filters.curriculumId, filters.courseGroup]);

  const current = response.key === requestKey ? response : { data: null, error: '' };
  const results = current.data?.results || [];
  const noIndexedData = current.data && current.data.indexed_courses === 0;

  const retry = () => setAttempt((n) => n + 1);

  let body;
  if (!query) {
    body = (
      <div className="grid gap-4 sm:grid-cols-3">
        {HOW_IT_WORKS.map(({ icon: Icon, title, text }) => (
          <div key={title} className="rounded-2xl border border-line bg-white p-5">
            <Icon className="h-6 w-6 text-ksu-blue" aria-hidden="true" />
            <h3 className="mt-3 font-semibold text-ink">{title}</h3>
            <p className="mt-1 text-sm text-muted">{text}</p>
          </div>
        ))}
      </div>
    );
  } else if (loading) {
    body = <ResultSkeleton />;
  } else if (current.error) {
    body = (
      <EmptyState
        icon={AlertCircle}
        title="ค้นหาไม่สำเร็จ"
        description={current.error}
        action={<Button variant="secondary" onClick={retry}>ลองอีกครั้ง</Button>}
        className="rounded-2xl border border-line bg-white"
      />
    );
  } else if (noIndexedData) {
    body = (
      <EmptyState
        icon={FileUp}
        title="ยังไม่มีข้อมูลให้ค้นหา"
        description={
          current.data.verified_curricula === 0
            ? 'การค้นหาใช้เฉพาะหลักสูตรที่อนุมัติแล้ว กรุณาตรวจทานและอนุมัติหลักสูตรอย่างน้อย 1 ฉบับก่อน'
            : 'หลักสูตรที่อนุมัติแล้วยังสร้าง Vector Embedding ไม่เสร็จ รอสักครู่แล้วลองใหม่'
        }
        action={<Button href={paths.dashboard()}>ไปที่คิวเอกสาร</Button>}
        className="rounded-2xl border border-line bg-white"
      />
    );
  } else if (results.length === 0) {
    body = (
      <EmptyState
        icon={SearchX}
        title={`ไม่พบรายวิชาที่เกี่ยวข้องกับ “${query}”`}
        description="ลองใช้คำที่กว้างขึ้น อธิบายเป็นทักษะหรือหัวข้อที่สอน หรือเอาตัวกรองหลักสูตร/หมวดวิชาออก"
        className="rounded-2xl border border-line bg-white"
      />
    );
  } else {
    body = (
      <div className="space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-lg font-semibold text-ink">
            พบ {results.length} รายวิชาที่เกี่ยวข้องกับ “{query}”
          </h2>
          <p className="text-sm text-muted">
            เรียงตามความเกี่ยวข้อง · คะแนนคำนวณจากความหมาย {current.data?.search_type ? '(Hybrid)' : ''}
          </p>
        </div>
        <ol className="space-y-3">
          {results.map((item, index) => (
            <li key={item.id || `${item.curriculum_code}-${item.course_code}`}>
              <SearchResultCard item={item} query={query} rank={index + 1} onOpen={setSelected} />
            </li>
          ))}
        </ol>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="ค้นหารายวิชาด้วย AI"
        description="ค้นจากความหมายของคำอธิบายรายวิชาและผลลัพธ์การเรียนรู้ (PLO) ไม่จำเป็นต้องพิมพ์ตรงกับชื่อวิชา"
      />
      <SearchForm key={query} initialQuery={query} curriculums={verifiedCurriculums} filters={filters} onFiltersChange={setFilters} loading={loading} />
      <div aria-live="polite">{body}</div>

      <CourseDetailDialog
        course={selected}
        onClose={() => setSelected(null)}
        footerExtra={
          selected?.curriculum_id && (
            <Button variant="secondary" icon={ExternalLink} href={paths.catalog(selected.curriculum_id)}>
              เปิดในคลังหลักสูตร
            </Button>
          )
        }
      />
    </div>
  );
}
