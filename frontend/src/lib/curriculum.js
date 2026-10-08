// ฟังก์ชันช่วยจัดรูปข้อมูลหลักสูตร (ไม่มี React — ทดสอบได้ง่าย)

export const COURSE_GROUPS = ['หมวดวิชาศึกษาทั่วไป', 'หมวดวิชาเฉพาะ', 'หมวดวิชาเลือกเสรี'];

export const isVerified = (item) => item?.verification_status === 'VERIFIED';

const DEPARTMENT_SHORT_CODES = [
  ['โลจิสติกส์', 'LOG'],
  ['อุตสาหการ', 'IE'],
  ['คอมพิวเตอร์', 'CPE'],
  ['ไฟฟ้า', 'EE'],
  ['โยธา', 'CE'],
  ['เครื่องกล', 'ME'],
];

/** รหัสหลักสูตรแบบสั้นสำหรับแสดงผล (รหัส สกอ. 14 หลักอ่านยาก) */
export function getDisplayCode(item) {
  const code = item?.code || item?.curriculum_code;
  if (!code) return 'TQF2';
  if (!/^\d{10,}$/.test(code)) return code;
  const text = `${item?.name || item?.curriculum_name_th || ''} ${item?.department || ''}`;
  const match = DEPARTMENT_SHORT_CODES.find(([keyword]) => text.includes(keyword));
  const cleaned = text.replace(/\d{10,}/g, '');
  const year = cleaned.match(/พ\.ศ\.\s*(25\d\d)/)?.[1] || cleaned.match(/25\d\d/)?.[0] || '';
  return match ? `${match[1]}${year}` : `CURR${code.slice(-4)}`;
}

/** ตัดรหัสที่ซ้ำหน้าชื่อออก และรวมคำ "วิศวกรรม xxx" ที่ OCR แยกไว้ */
export function cleanCurriculumName(item) {
  const name = item?.name || item?.curriculum_name_th || 'เอกสาร มคอ.2';
  const code = item?.code || item?.curriculum_code;
  const escaped = code ? code.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') : null;
  return name
    .replace(escaped ? new RegExp(`^${escaped}\\s*:\\s*`) : /^$/, '')
    .replace(/วิศวกรรม\s+([ก-๙]+)/g, 'วิศวกรรม$1');
}

export function formatThaiDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function prerequisiteText(prerequisites) {
  if (!prerequisites || (Array.isArray(prerequisites) && prerequisites.length === 0)) return '';
  return Array.isArray(prerequisites) ? prerequisites.join(', ') : String(prerequisites);
}

export const creditPattern = (course) =>
  `${course?.credit_lecture ?? 0}-${course?.credit_lab ?? 0}-${course?.credit_self ?? 0}`;

/** เลือกชุด PLO ที่ใช้เป็นคอลัมน์ ตามที่เล่ม PDF ใช้จริง */
export function resolveDisplayPlos(plosData) {
  if (plosData?.display_plos?.length) return plosData.display_plos;
  if (plosData?.sub_plos?.length) return plosData.sub_plos;
  return plosData?.main_plos || [];
}

/** หลักสูตรที่ใช้เครื่องหมาย ✓ แทน ⚫/○ */
export const isCheckmarkProgram = (plos) => plos.some((p) => /^PLO\d+$/i.test(p.plo_code));

/** ค้นหาประเภทความรับผิดชอบของวิชาต่อ PLO (รองรับรหัสที่เขียนต่างกัน) */
export function getResponsibility(row, ploCode) {
  const mappings = row?.mappings || [];
  const candidates = [ploCode, ploCode.replace(/^PLO/i, ''), `PLO${ploCode}`];
  const found = mappings.find((m) => candidates.includes(m.plo_code));
  return found?.responsibility_type || null;
}

export function normalizeInstructor(inst) {
  if (inst && typeof inst === 'object') {
    return {
      position: inst.academic_position || '-',
      name: inst.name || '-',
      educations: Array.isArray(inst.educations) ? inst.educations : [],
      remarks: inst.remarks || '',
    };
  }
  const parts = String(inst || '').split(' ');
  return { position: parts[0] || '-', name: parts.slice(1).join(' ') || '-', educations: [], remarks: '' };
}

export function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
