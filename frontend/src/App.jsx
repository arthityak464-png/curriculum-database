import { useState } from 'react';
import AppShell from './components/layout/AppShell';
import UploadDialog from './components/curriculum/UploadDialog';
import { ConfirmDialog } from './components/ui';
import ToastProvider from './components/ui/ToastProvider';
import { useToast } from './context/toast';
import { useCurriculums } from './hooks/useCurriculums';
import { usePipelineJob } from './hooks/usePipelineJob';
import * as api from './services/api';
import { cleanCurriculumName, isVerified } from './lib/curriculum';
import { navigate, paths, useHashRoute } from './lib/router';
import DashboardPage from './pages/dashboard/DashboardPage';
import SearchPage from './pages/search/SearchPage';
import CatalogPage from './pages/catalog/CatalogPage';
import StudioPage from './pages/studio/StudioPage';

function AppContent() {
  const route = useHashRoute();
  const { showToast } = useToast();
  const curriculums = useCurriculums();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const pipeline = usePipelineJob({
    onComplete: (job) => {
      showToast(`ประมวลผล ${job.filename || 'เอกสาร'} สำเร็จ พร้อมให้ตรวจทาน`);
      curriculums.refresh();
    },
    onFail: (job) => showToast(`ประมวลผลล้มเหลว: ${job.message}`, 'error'),
  });

  const items = curriculums.items;
  const pendingCount = items.filter((c) => !isVerified(c)).length;
  const sidebarCurriculumId = route.id || items[0]?.id || '';

  const handleUpload = async (file, force) => {
    pipeline.start({ job_id: null, status: 'uploading', progress: 0, message: 'กำลังอัปโหลดไฟล์…', filename: file.name });
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.uploadCurriculum(formData, force);
      if (res.data?.status === 'already_exists') {
        pipeline.dismiss();
        showToast(res.data.message || 'เอกสารนี้มีอยู่ในระบบแล้ว', 'info');
        await curriculums.refresh();
        if (res.data.curriculum_id) navigate(paths.studio(res.data.curriculum_id));
      } else if (res.data?.job_id) {
        pipeline.start({
          job_id: res.data.job_id,
          status: 'queued',
          progress: 5,
          message: 'รับไฟล์แล้ว กำลังเริ่มสกัดข้อมูล…',
          filename: file.name,
        });
      }
    } catch (err) {
      pipeline.dismiss();
      showToast(`อัปโหลดไม่สำเร็จ: ${api.getErrorMessage(err)}`, 'error');
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      setDeleting(true);
      await api.deleteCurriculum(deleteTarget.id);
      window.localStorage.removeItem(`verification-sections:${deleteTarget.id}`);
      showToast(`ลบหลักสูตร "${cleanCurriculumName(deleteTarget)}" แล้ว`);
      if (route.id === deleteTarget.id) navigate(paths.dashboard());
      setDeleteTarget(null);
      await curriculums.refresh();
    } catch (err) {
      showToast(`ลบไม่สำเร็จ: ${api.getErrorMessage(err)}`, 'error');
    } finally {
      setDeleting(false);
    }
  };

  let content;
  switch (route.page) {
    case 'search':
      content = <SearchPage query={route.params.get('q') || ''} curriculums={items} />;
      break;
    case 'catalog':
      content = <CatalogPage curriculumId={route.id} curriculums={items} />;
      break;
    case 'studio':
      content = (
        <StudioPage
          curriculumId={route.id}
          curriculums={items}
          onApproved={(id) => curriculums.patch(id, { verification_status: 'VERIFIED' })}
        />
      );
      break;
    default:
      content = (
        <DashboardPage
          curriculums={items}
          loading={curriculums.loading}
          onRefresh={curriculums.refresh}
          onDelete={setDeleteTarget}
        />
      );
  }

  return (
    <AppShell
      page={route.page}
      curriculumId={sidebarCurriculumId}
      pendingCount={pendingCount}
      apiError={curriculums.error}
      job={pipeline.job}
      onDismissJob={pipeline.dismiss}
      onUpload={() => setUploadOpen(true)}
      fill={route.page === 'studio' && Boolean(route.id)}
    >
      {content}

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} onSubmit={handleUpload} />
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="ลบหลักสูตรนี้?"
        message={`"${deleteTarget ? cleanCurriculumName(deleteTarget) : ''}" รวมถึงรายวิชาและ PLO ทั้งหมดจะถูกลบถาวร`}
        confirmLabel="ลบถาวร"
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </AppShell>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}
