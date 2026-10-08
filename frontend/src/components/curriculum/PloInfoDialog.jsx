import { BookCheck } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

/** คำอธิบาย PLO เมื่อคลิกหัวคอลัมน์/ช่องในตาราง */
export default function PloInfoDialog({ plo, onClose }) {
  if (!plo) return null;
  return (
    <Modal
      open
      onClose={onClose}
      size="md"
      title={
        <span className="flex items-center gap-2 font-mono text-ksu-blue">
          <BookCheck className="h-5 w-5" aria-hidden="true" /> {plo.plo_code}
        </span>
      }
      footer={<Button onClick={onClose}>เข้าใจแล้ว</Button>}
    >
      <p className="text-[15px] leading-relaxed text-ink">{plo.plo_description || 'ไม่มีคำอธิบายสำหรับผลลัพธ์การเรียนรู้นี้'}</p>
      {plo.contextCourse && (
        <p className="mt-4 rounded-xl border border-line bg-canvas p-3 text-sm text-muted">
          วิชา <strong className="text-ink">{plo.contextCourse}</strong>
          <br />
          ระดับความรับผิดชอบ: <strong className="text-ksu-blue">{plo.contextType || 'ไม่ได้ระบุ'}</strong>
        </p>
      )}
    </Modal>
  );
}
