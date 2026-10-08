import { useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, FileText, FolderOpen, RefreshCw, Search, Trash2 } from 'lucide-react';
import { Button, Card, EmptyState, SelectField, inputClass } from '../../components/ui';
import VerificationBadge from '../../components/curriculum/VerificationBadge';
import { cleanCurriculumName, formatThaiDate, getDisplayCode, isVerified } from '../../lib/curriculum';
import { paths } from '../../lib/router';

const PAGE_SIZE = 8;

const STATUS_OPTIONS = [
  { value: 'ALL', label: 'ทุกสถานะ' },
  { value: 'STAGED', label: 'รอตรวจทาน' },
  { value: 'VERIFIED', label: 'อนุมัติแล้ว' },
];

function SortHeader({ label, sortKey, sort, onSort, className = '' }) {
  const active = sort.key === sortKey;
  const Icon = !active ? ArrowUpDown : sort.direction === 'asc' ? ArrowUp : ArrowDown;
  return (
    <th scope="col" aria-sort={active ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none'} className={`px-4 py-3 ${className}`}>
      <button type="button" onClick={() => onSort(sortKey)} className="inline-flex items-center gap-1.5 font-semibold hover:text-ksu-navy">
        {label}
        <Icon className={`h-3.5 w-3.5 ${active ? 'text-ksu-blue' : 'text-subtle'}`} aria-hidden="true" />
      </button>
    </th>
  );
}

/** ตารางคิวเอกสารหลักสูตร พร้อมตัวกรอง เรียงลำดับ และแบ่งหน้า */
export default function CurriculumQueue({ curriculums, loading, statusFilter, onStatusFilter, onRefresh, onDelete }) {
  const [text, setText] = useState('');
  const [faculty, setFaculty] = useState('ALL');
  const [sort, setSort] = useState({ key: 'updated_at', direction: 'desc' });
  const [page, setPage] = useState(1);

  const facultyOptions = useMemo(() => {
    const set = new Set(curriculums.map((c) => c.faculty).filter(Boolean));
    return [{ value: 'ALL', label: 'ทุกคณะ' }, ...[...set].map((f) => ({ value: f, label: f }))];
  }, [curriculums]);

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    const list = curriculums.filter((item) => {
      const haystack = [item.name, item.code, item.faculty, item.department, getDisplayCode(item)].join(' ').toLowerCase();
      const statusOk =
        statusFilter === 'ALL' || (statusFilter === 'VERIFIED' ? isVerified(item) : !isVerified(item));
      return (!q || haystack.includes(q)) && statusOk && (faculty === 'ALL' || item.faculty === faculty);
    });
    const dir = sort.direction === 'asc' ? 1 : -1;
    return [...list].sort((a, b) => {
      let va = a[sort.key] ?? '';
      let vb = b[sort.key] ?? '';
      if (sort.key === 'updated_at') {
        va = new Date(va).getTime() || 0;
        vb = new Date(vb).getTime() || 0;
      }
      if (typeof va === 'string') return va.localeCompare(vb, 'th') * dir;
      return (va - vb) * dir;
    });
  }, [curriculums, text, faculty, statusFilter, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const rows = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const resetPage = (setter) => (value) => {
    setter(value);
    setPage(1);
  };
  const onSort = (key) =>
    setSort((prev) => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));

  return (
    <Card
      title={`คิวเอกสารในระบบ (${filtered.length})`}
      actions={
        <>
          <label className="relative block w-full sm:w-72">
            <span className="sr-only">ค้นหาในคิว</span>
            <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-subtle" aria-hidden="true" />
            <input
              type="search"
              value={text}
              onChange={(e) => resetPage(setText)(e.target.value)}
              placeholder="รหัส ชื่อหลักสูตร หรือสาขา"
              className={`${inputClass} min-h-10 pl-9 text-sm`}
            />
          </label>
          <SelectField label="คณะ" hideLabel value={faculty} onChange={resetPage(setFaculty)} options={facultyOptions} selectClassName="min-h-10 text-sm max-w-[180px]" />
          <SelectField label="สถานะ" hideLabel value={statusFilter} onChange={resetPage(onStatusFilter)} options={STATUS_OPTIONS} selectClassName="min-h-10 text-sm" />
          <Button variant="secondary" size="icon" onClick={onRefresh} aria-label="รีเฟรชข้อมูล" title="รีเฟรชข้อมูล">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </>
      }
    >
      <div className="scroll-thin overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-sm">
          <thead className="bg-canvas text-left text-xs text-muted">
            <tr>
              <th scope="col" className="w-14 px-4 py-3 text-center font-semibold">ที่</th>
              <SortHeader label="หลักสูตร" sortKey="name" sort={sort} onSort={onSort} />
              <SortHeader label="คณะ / สาขา" sortKey="faculty" sort={sort} onSort={onSort} />
              <SortHeader label="หน่วยกิต" sortKey="total_credits" sort={sort} onSort={onSort} className="text-center" />
              <SortHeader label="สถานะ" sortKey="verification_status" sort={sort} onSort={onSort} />
              <SortHeader label="นำเข้าเมื่อ" sortKey="updated_at" sort={sort} onSort={onSort} />
              <th scope="col" className="px-4 py-3 text-right font-semibold">ดำเนินการ</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((item, index) => {
              const verified = isVerified(item);
              const name = cleanCurriculumName(item);
              return (
                <tr key={item.id} className="hover:bg-ksu-mist/40">
                  <td className="px-4 py-3.5 text-center font-mono text-subtle">{(currentPage - 1) * PAGE_SIZE + index + 1}</td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-3">
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-ksu-mist text-ksu-blue" title={`SHA-256: ${item.file_hash_sha256 || '-'}`}>
                        <FileText className="h-5 w-5" aria-hidden="true" />
                      </span>
                      <div className="min-w-0">
                        <span className="font-mono text-xs font-semibold text-ksu-blue" title={item.code}>{getDisplayCode(item)}</span>
                        <p className="max-w-[340px] truncate font-semibold text-ink" title={name}>{name}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <p className="max-w-[200px] truncate text-ink">{item.faculty || '-'}</p>
                    {item.department && <p className="max-w-[200px] truncate text-xs text-muted">{item.department}</p>}
                  </td>
                  <td className="px-4 py-3.5 text-center font-mono text-ink">{item.total_credits ?? '-'}</td>
                  <td className="px-4 py-3.5"><VerificationBadge verified={verified} /></td>
                  <td className="px-4 py-3.5 whitespace-nowrap text-muted">{formatThaiDate(item.updated_at)}</td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center justify-end gap-2">
                      {verified ? (
                        <Button size="sm" variant="secondary" href={paths.catalog(item.id)}>ดูคลัง</Button>
                      ) : (
                        <Button size="sm" href={paths.studio(item.id)}>ตรวจทาน</Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDelete(item)}
                        aria-label={`ลบ ${name}`}
                        title="ลบหลักสูตร"
                        className="px-2 hover:bg-danger-bg hover:text-danger"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!loading && rows.length === 0 && (
          <EmptyState
            icon={FolderOpen}
            title={curriculums.length === 0 ? 'ยังไม่มีเอกสารในระบบ' : 'ไม่พบเอกสารตามเงื่อนไข'}
            description={curriculums.length === 0 ? 'กดปุ่ม "นำเข้า มคอ.2" ด้านบนเพื่อเริ่มต้น' : 'ลองล้างคำค้นหรือเปลี่ยนตัวกรอง'}
          />
        )}
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3 text-sm text-muted">
        <span>
          แสดง {filtered.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, filtered.length)} จาก {filtered.length} รายการ
        </span>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="icon" className="h-9 w-9" onClick={() => setPage(currentPage - 1)} disabled={currentPage === 1} aria-label="หน้าก่อนหน้า">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="font-medium text-ink">หน้า {currentPage} / {totalPages}</span>
          <Button variant="secondary" size="icon" className="h-9 w-9" onClick={() => setPage(currentPage + 1)} disabled={currentPage === totalPages} aria-label="หน้าถัดไป">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </footer>
    </Card>
  );
}
