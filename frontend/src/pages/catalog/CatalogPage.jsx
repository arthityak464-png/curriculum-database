import { useMemo, useState } from 'react';
import { AlertTriangle, Download, Layers, LibraryBig, Search, Table } from 'lucide-react';
import { Button, EmptyState, SegmentedTabs, SelectField, inputClass } from '../../components/ui';
import PageHeader from '../../components/layout/PageHeader';
import CurriculumPicker from '../../components/curriculum/CurriculumPicker';
import CourseCard from '../../components/curriculum/CourseCard';
import CourseDetailDialog from '../../components/curriculum/CourseDetailDialog';
import PloMatrix, { MatrixLegend } from '../../components/curriculum/PloMatrix';
import PloInfoDialog from '../../components/curriculum/PloInfoDialog';
import { useCurriculumBundle } from '../../hooks/useCurriculumBundle';
import { useToast } from '../../context/toast';
import * as api from '../../services/api';
import { COURSE_GROUPS, downloadJson, isCheckmarkProgram, isVerified, resolveDisplayPlos } from '../../lib/curriculum';
import { navigate, paths } from '../../lib/router';
import CurriculumSummary from './CurriculumSummary';

const VIEWS = [
  { value: 'browser', label: 'แค็ตตาล็อกรายวิชา', icon: Layers },
  { value: 'matrix', label: 'ตาราง PLO Mapping', icon: Table },
];

export default function CatalogPage({ curriculumId, curriculums }) {
  const { showToast } = useToast();
  const { detail, courses, plos, mapping, loading } = useCurriculumBundle(curriculumId);
  const [view, setView] = useState('browser');
  const [text, setText] = useState('');
  const [group, setGroup] = useState('ALL');
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [ploInfo, setPloInfo] = useState(null);

  const displayPlos = resolveDisplayPlos(plos);
  const q = text.trim().toLowerCase();

  const filteredCourses = useMemo(
    () =>
      courses.filter(
        (c) =>
          (group === 'ALL' || c.course_group === group) &&
          (!q || [c.course_code, c.course_name_th, c.course_name_en].join(' ').toLowerCase().includes(q)),
      ),
    [courses, group, q],
  );

  const filteredMapping = useMemo(() => {
    const byCode = new Map(courses.map((c) => [c.course_code, c]));
    return mapping.filter((row) => {
      const course = byCode.get(row.course_code);
      const groupOk = group === 'ALL' || !course || course.course_group === group;
      const textOk = !q || `${row.course_code} ${row.course_name_th}`.toLowerCase().includes(q);
      return groupOk && textOk;
    });
  }, [mapping, courses, group, q]);

  if (!curriculumId) {
    const first = curriculums.find(isVerified) || curriculums[0];
    return (
      <div className="mx-auto w-full max-w-3xl p-6">
        <EmptyState
          icon={LibraryBig}
          title="เลือกหลักสูตรที่ต้องการดู"
          description="คลังหลักสูตรแสดงรายวิชาและตาราง PLO ของแต่ละหลักสูตร"
          action={first && <Button href={paths.catalog(first.id)}>เปิดหลักสูตรล่าสุด</Button>}
          className="rounded-2xl border border-line bg-white"
        />
      </div>
    );
  }

  const exportJson = async () => {
    try {
      const res = await api.exportCurriculumJson(curriculumId);
      downloadJson(res.data, `curriculum_${detail?.curriculum_code || 'export'}.json`);
      showToast('ส่งออกไฟล์ Tree JSON แล้ว');
    } catch (err) {
      showToast(`ส่งออกไม่สำเร็จ: ${api.getErrorMessage(err)}`, 'error');
    }
  };

  const openCourseByCode = (code) => {
    const course = courses.find((c) => c.course_code === code);
    if (course) setSelectedCourse(course);
  };

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="คลังหลักสูตรและรายวิชา"
        actions={
          <>
            <CurriculumPicker curriculums={curriculums} value={curriculumId} onChange={(id) => navigate(paths.catalog(id))} />
            <Button variant="secondary" icon={Download} onClick={exportJson}>Tree JSON</Button>
          </>
        }
      />

      {detail && !isVerified(detail) && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-warn-line bg-warn-bg p-4 text-sm text-warn-fg">
          <span className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" /> หลักสูตรนี้ยังไม่ผ่านการตรวจทาน ข้อมูลอาจยังไม่ถูกต้อง และยังค้นหาด้วย AI ไม่ได้
          </span>
          <Button size="sm" href={paths.studio(curriculumId)}>ไปตรวจทาน</Button>
        </div>
      )}

      {loading ? (
        <p className="py-16 text-center text-sm text-muted">กำลังโหลดข้อมูล…</p>
      ) : (
        <>
          <CurriculumSummary detail={detail} courseCount={courses.length} ploCount={displayPlos.length} />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <SegmentedTabs label="มุมมอง" items={VIEWS} value={view} onChange={setView} />
            <div className="flex flex-wrap gap-2">
              <label className="relative block w-full sm:w-64">
                <span className="sr-only">ค้นหาวิชา</span>
                <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-subtle" aria-hidden="true" />
                <input type="search" value={text} onChange={(e) => setText(e.target.value)} placeholder="รหัส หรือชื่อวิชา" className={`${inputClass} min-h-10 pl-9 text-sm`} />
              </label>
              <SelectField
                label="หมวดวิชา"
                hideLabel
                value={group}
                onChange={setGroup}
                options={[{ value: 'ALL', label: 'ทุกหมวดวิชา' }, ...COURSE_GROUPS.map((g) => ({ value: g, label: g }))]}
                selectClassName="min-h-10 text-sm"
              />
            </div>
          </div>

          {view === 'browser' ? (
            <>
              <p className="text-sm text-muted">แสดง {filteredCourses.length} จาก {courses.length} รายวิชา</p>
              {filteredCourses.length ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {filteredCourses.map((c) => (
                    <CourseCard key={c.id || c.course_code} course={c} onOpen={setSelectedCourse} />
                  ))}
                </div>
              ) : (
                <EmptyState icon={Search} title="ไม่พบรายวิชาตามเงื่อนไข" className="rounded-2xl border border-line bg-white" />
              )}
            </>
          ) : (
            <section className="overflow-hidden rounded-2xl border border-line bg-white">
              <div className="border-b border-line px-5 py-4">
                <h2 className="font-semibold text-ink">ตารางการกระจายความรับผิดชอบ PLO สู่รายวิชา</h2>
                <div className="mt-1"><MatrixLegend checkmark={isCheckmarkProgram(displayPlos)} /></div>
              </div>
              <PloMatrix plos={displayPlos} rows={filteredMapping} onCourseClick={openCourseByCode} onPloClick={setPloInfo} />
            </section>
          )}
        </>
      )}

      <CourseDetailDialog course={selectedCourse} onClose={() => setSelectedCourse(null)} />
      <PloInfoDialog plo={ploInfo} onClose={() => setPloInfo(null)} />
    </div>
  );
}
