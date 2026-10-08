import { useState } from 'react';
import { CheckCircle2, Clock, FileText } from 'lucide-react';
import { StatCard } from '../../components/ui';
import PageHeader from '../../components/layout/PageHeader';
import { isVerified } from '../../lib/curriculum';
import CurriculumQueue from './CurriculumQueue';
import QuickSearch from './QuickSearch';

export default function DashboardPage({ curriculums, loading, onRefresh, onDelete }) {
  const [statusFilter, setStatusFilter] = useState('ALL');
  const approved = curriculums.filter(isVerified).length;
  const pending = curriculums.length - approved;

  const toggle = (value) => setStatusFilter((prev) => (prev === value ? 'ALL' : value));

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        eyebrow="ภาพรวมระบบ"
        title={pending > 0 ? `มีหลักสูตรรอตรวจทาน ${pending} ฉบับ` : 'ทุกหลักสูตรตรวจทานเรียบร้อย'}
        description="นำเข้าเล่ม มคอ.2 → AI สกัดข้อมูล → ตรวจทานเทียบเอกสารต้นฉบับ → อนุมัติลงฐานข้อมูลและพร้อมค้นหา"
      />

      <QuickSearch />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="เอกสารหลักสูตรทั้งหมด" value={curriculums.length} icon={FileText} onClick={() => setStatusFilter('ALL')} active={statusFilter === 'ALL'} />
        <StatCard label="รอตรวจทาน (Staging)" value={pending} icon={Clock} tone="warn" onClick={() => toggle('STAGED')} active={statusFilter === 'STAGED'} />
        <StatCard label="อนุมัติแล้ว พร้อมค้นหา" value={approved} icon={CheckCircle2} tone="ok" onClick={() => toggle('VERIFIED')} active={statusFilter === 'VERIFIED'} />
      </div>

      <CurriculumQueue
        curriculums={curriculums}
        loading={loading}
        statusFilter={statusFilter}
        onStatusFilter={setStatusFilter}
        onRefresh={onRefresh}
        onDelete={onDelete}
      />
    </div>
  );
}
