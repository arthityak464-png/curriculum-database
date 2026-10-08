import { useState } from 'react';
import { FileText, Upload } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

const MAX_MB = 50;

/** นำเข้าไฟล์ มคอ.2 (PDF) เข้า Staging */
export default function UploadDialog({ open, onClose, onSubmit }) {
  const [file, setFile] = useState(null);
  const [force, setForce] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');

  const pick = (candidate) => {
    if (!candidate) return;
    if (candidate.type !== 'application/pdf' && !candidate.name.toLowerCase().endsWith('.pdf')) {
      setError('รองรับเฉพาะไฟล์ PDF เท่านั้น');
      return;
    }
    if (candidate.size > MAX_MB * 1024 * 1024) {
      setError(`ไฟล์ใหญ่เกิน ${MAX_MB} MB`);
      return;
    }
    setError('');
    setFile(candidate);
  };

  const close = () => {
    setFile(null);
    setForce(false);
    setError('');
    onClose();
  };

  const submit = (e) => {
    e.preventDefault();
    if (!file) return;
    onSubmit(file, force);
    close();
  };

  return (
    <Modal
      open={open}
      onClose={close}
      title="นำเข้าไฟล์ มคอ.2"
      description="ระบบจะพักข้อมูลไว้ใน Staging ให้ตรวจทานก่อนบันทึกเข้าฐานข้อมูลจริง"
      footer={
        <>
          <Button variant="secondary" onClick={close}>ยกเลิก</Button>
          <Button type="submit" form="upload-form" icon={Upload} disabled={!file}>นำเข้าเอกสาร</Button>
        </>
      }
    >
      <form id="upload-form" onSubmit={submit} className="space-y-4">
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            pick(e.dataTransfer.files?.[0]);
          }}
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${
            dragging ? 'border-ksu-blue bg-ksu-mist' : 'border-ksu-emblem bg-[#f7fafe] hover:bg-ksu-mist'
          }`}
        >
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-ksu-blue shadow-sm">
            {file ? <FileText className="h-7 w-7" /> : <Upload className="h-7 w-7" />}
          </span>
          <span className="text-base font-semibold text-ksu-navy">{file ? file.name : 'ลากไฟล์มาวาง หรือคลิกเพื่อเลือก'}</span>
          <span className="text-sm text-muted">
            {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : `ไฟล์เล่ม มคอ.2 (.pdf) ไม่เกิน ${MAX_MB} MB`}
          </span>
          <input type="file" accept=".pdf,application/pdf" className="sr-only" onChange={(e) => pick(e.target.files?.[0])} />
        </label>

        {error && <p role="alert" className="text-sm font-medium text-danger">{error}</p>}

        <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-line p-3.5">
          <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} className="mt-1 h-4 w-4 accent-ksu-blue" />
          <span className="text-sm">
            <strong className="block font-semibold text-ink">ประมวลผลใหม่อีกครั้ง</strong>
            <span className="text-muted">สกัดข้อมูลใหม่แม้ไฟล์นี้เคยมีในระบบแล้ว</span>
          </span>
        </label>
      </form>
    </Modal>
  );
}
