import { AlertTriangle, Upload } from 'lucide-react';
import BrandLogo from './BrandLogo';
import Sidebar from './Sidebar';
import Button from '../ui/Button';
import PipelineBanner from '../curriculum/PipelineBanner';

/**
 * โครงหน้าหลัก: ส่วนหัว + เมนูซ้าย + เนื้อหา
 * fill = เนื้อหาเต็มความสูงจอ (ใช้กับห้องตรวจทานที่มี 2 แผง)
 */
export default function AppShell({ page, curriculumId, pendingCount, apiError, job, onDismissJob, onUpload, fill = false, children }) {
  return (
    <div className={`flex flex-col bg-canvas ${fill ? 'h-screen' : 'min-h-screen'}`}>
      <header className="z-30 shrink-0 border-b border-line bg-white">
        <div className="flex items-center justify-between gap-4 px-4 py-2.5 sm:px-6">
          <BrandLogo />
          {/* แสดงปุ่มนำเข้าเฉพาะเมื่ออยู่ที่หน้าภาพรวม (dashboard) เท่านั้น */}
          {page === 'dashboard' && (
            <Button icon={Upload} onClick={onUpload}>
              <span className="hidden sm:inline">นำเข้า มคอ.2</span>
              <span className="sm:hidden">นำเข้า</span>
            </Button>
          )}
        </div>
      </header>

      {apiError && (
        <div role="alert" className="flex items-center gap-2 border-b border-danger/20 bg-danger-bg px-6 py-2.5 text-sm text-danger">
          <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
          เชื่อมต่อเซิร์ฟเวอร์ไม่ได้: {apiError}
        </div>
      )}
      <PipelineBanner job={job} onDismiss={onDismissJob} />

      <div className={`flex flex-1 flex-col lg:flex-row ${fill ? 'min-h-0' : ''}`}>
        <Sidebar page={page} curriculumId={curriculumId} pendingCount={pendingCount} compact={fill} />
        <main className={`min-w-0 flex-1 ${fill ? 'flex min-h-0 flex-col' : ''}`}>{children}</main>
      </div>
    </div>
  );
}