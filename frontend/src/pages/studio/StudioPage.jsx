import { useState } from 'react';
import { BookOpen, CheckCircle2, Download, LayoutGrid, ListChecks, ScanSearch, Table } from 'lucide-react';
import { Badge, Button, ConfirmDialog, EmptyState, SegmentedTabs } from '../../components/ui';
import CurriculumPicker from '../../components/curriculum/CurriculumPicker';
import VerificationBadge from '../../components/curriculum/VerificationBadge';
import PloMatrix, { MatrixLegend } from '../../components/curriculum/PloMatrix';
import PloInfoDialog from '../../components/curriculum/PloInfoDialog';
import { useCurriculumBundle } from '../../hooks/useCurriculumBundle';
import { useSectionProgress } from '../../hooks/useSectionProgress';
import { useToast } from '../../context/toast';
import * as api from '../../services/api';
import { downloadJson, isCheckmarkProgram, isVerified, resolveDisplayPlos } from '../../lib/curriculum';
import { navigate, paths } from '../../lib/router';
import GeneralSection from './GeneralSection';
import CoursesSection from './CoursesSection';
import PdfPane from './PdfPane';

const SECTIONS = [
  { value: 'general', label: '01 ข้อมูลทั่วไป', icon: BookOpen },
  { value: 'courses', label: '02 รายวิชา', icon: ListChecks },
  { value: 'mapping', label: '03 ตาราง PLO', icon: Table },
];

export default function StudioPage({ curriculumId, curriculums, onApproved }) {
  const { showToast } = useToast();
  const bundle = useCurriculumBundle(curriculumId);
  const progress = useSectionProgress(curriculumId);
  const [tab, setTab] = useState('general');
  const [saving, setSaving] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [ploInfo, setPloInfo] = useState(null);

  if (!curriculumId) {
    const pending = curriculums.filter((c) => !isVerified(c));
    return (
      <div className="mx-auto w-full max-w-3xl p-6">
        <EmptyState
          icon={ScanSearch}
          title="เลือกหลักสูตรที่จะตรวจทาน"
          description={pending.length ? `มี ${pending.length} หลักสูตรรอตรวจทาน` : 'ยังไม่มีหลักสูตรรอตรวจทาน'}
          action={pending[0] && <Button href={paths.studio(pending[0].id)}>เริ่มตรวจฉบับแรก</Button>}
          className="rounded-2xl border border-line bg-white"
        />
      </div>
    );
  }

  const { detail, courses, plos, mapping, loading } = bundle;
  const verified = isVerified(detail);
  const displayPlos = resolveDisplayPlos(plos);
  const tabIndex = SECTIONS.findIndex((s) => s.value === tab);
  const doneCount = progress.done.filter(Boolean).length;

  const save = async (payload) => {
    try {
      setSaving(true);
      await api.updateCurriculum(curriculumId, payload);
      showToast('บันทึกการแก้ไขข้อมูลหลักสูตรแล้ว');
      await bundle.reload();
    } catch (err) {
      showToast(`บันทึกไม่สำเร็จ: ${api.getErrorMessage(err)}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  const exportJson = async () => {
    try {
      const res = await api.exportCurriculumJson(curriculumId);
      downloadJson(res.data, `curriculum_${detail?.curriculum_code || 'export'}.json`);
      showToast('ส่งออกไฟล์ Tree JSON แล้ว');
    } catch (err) {
      showToast(`ส่งออกไม่สำเร็จ: ${api.getErrorMessage(err)}`, 'error');
    }
  };

  const confirmSection = () => {
    progress.markDone(tabIndex);
    if (tabIndex < SECTIONS.length - 1) {
      setTab(SECTIONS[tabIndex + 1].value);
    } else {
      setConfirmOpen(true);
    }
  };

  const commit = async () => {
    try {
      setCommitting(true);
      await api.commitCurriculum(curriculumId);
      bundle.setDetail((prev) => ({ ...prev, verification_status: 'VERIFIED' }));
      onApproved(curriculumId);
      setConfirmOpen(false);
      showToast('อนุมัติแล้ว ระบบกำลังสร้าง Vector สำหรับค้นหาด้วย AI');
      navigate(paths.catalog(curriculumId));
    } catch (err) {
      showToast(`อนุมัติไม่สำเร็จ: ${api.getErrorMessage(err)}`, 'error');
    } finally {
      setCommitting(false);
    }
  };

  const openCourse = () => setTab('courses');

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* แถบเครื่องมือ */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-line bg-white px-4 py-2.5">
        <div className="flex min-w-0 flex-wrap items-center gap-3">
          <h1 className="text-base font-bold text-ksu-navy">ห้องตรวจทาน</h1>
          <CurriculumPicker curriculums={curriculums} value={curriculumId} onChange={(id) => navigate(paths.studio(id))} />
          {detail && <VerificationBadge verified={verified} />}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" icon={LayoutGrid} href={paths.catalog(curriculumId)}>ดูในคลัง</Button>
          <Button size="sm" variant="secondary" icon={Download} onClick={exportJson}>Tree JSON</Button>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-2">
        <PdfPane url={api.getCurriculumPdfUrl(curriculumId)} />

        <section aria-label="ข้อมูลที่ AI สกัดได้" className="flex min-h-0 flex-col bg-white">
          <div className="shrink-0 space-y-3 border-b border-line px-5 py-3">
            <div className="flex items-center gap-3 text-sm">
              <span className="text-muted">ตรวจแล้ว {doneCount} จาก 3 ส่วน</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-ksu-mist" aria-hidden="true">
                <div className="h-full rounded-full bg-ok transition-all" style={{ width: `${(doneCount / 3) * 100}%` }} />
              </div>
            </div>
            <SegmentedTabs
              label="ส่วนที่ต้องตรวจทาน"
              items={SECTIONS.map((s, i) => ({ ...s, done: progress.done[i] }))}
              value={tab}
              onChange={setTab}
            />
          </div>

          <div className="scroll-thin min-h-0 flex-1 overflow-y-auto p-5">
            {loading || !detail ? (
              <p className="py-16 text-center text-sm text-muted">{loading ? 'กำลังโหลดข้อมูล…' : bundle.error || 'ไม่พบข้อมูลหลักสูตร'}</p>
            ) : (
              <>
                {tab === 'general' && <GeneralSection key={`${detail.id}-${detail.updated_at}`} detail={detail} saving={saving} onSave={save} />}
                {tab === 'courses' && <CoursesSection courses={courses} />}
                {tab === 'mapping' && (
                  <div className="space-y-3">
                    <MatrixLegend checkmark={isCheckmarkProgram(displayPlos)} />
                    <div className="rounded-xl border border-line">
                      <PloMatrix plos={displayPlos} rows={mapping} onPloClick={setPloInfo} onCourseClick={openCourse} maxHeightClass="max-h-none" />
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <footer className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-t border-line bg-canvas px-5 py-3">
            {verified ? (
              <Badge tone="ok" dot>หลักสูตรนี้อนุมัติแล้ว · พร้อมใช้ค้นหา</Badge>
            ) : (
              <span className="text-sm text-muted">
                ส่วนนี้: {progress.done[tabIndex] ? <strong className="text-ok-fg">ตรวจแล้ว</strong> : 'ยังไม่ได้ยืนยัน'}
              </span>
            )}
            {!verified && (
              <Button icon={tabIndex === SECTIONS.length - 1 ? CheckCircle2 : undefined} variant={tabIndex === SECTIONS.length - 1 ? 'success' : 'primary'} onClick={confirmSection} disabled={!detail}>
                {tabIndex === SECTIONS.length - 1 ? 'ยืนยันและอนุมัติหลักสูตร' : 'ยืนยันส่วนนี้ ไปส่วนถัดไป'}
              </Button>
            )}
          </footer>
        </section>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="อนุมัติหลักสูตรลงฐานข้อมูล?"
        message={`ข้อมูลทั้ง 3 ส่วนจะถูกบันทึกเป็นข้อมูลจริง และนำไปสร้าง Vector สำหรับค้นหาด้วย AI${doneCount < 3 ? ` (ยังมี ${3 - doneCount} ส่วนที่ไม่ได้กดยืนยัน)` : ''}`}
        confirmLabel="อนุมัติ"
        tone="primary"
        loading={committing}
        onConfirm={commit}
        onCancel={() => setConfirmOpen(false)}
      />
      <PloInfoDialog plo={ploInfo} onClose={() => setPloInfo(null)} />
    </div>
  );
}
