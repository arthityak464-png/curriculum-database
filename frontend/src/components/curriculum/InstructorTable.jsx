import { normalizeInstructor } from '../../lib/curriculum';

/** ตารางอาจารย์ผู้รับผิดชอบหลักสูตร ตามโครงสร้างในเล่ม มคอ.2 */
export default function InstructorTable({ instructors }) {
  const list = Array.isArray(instructors) ? instructors.map(normalizeInstructor) : [];

  return (
    <div className="scroll-thin overflow-x-auto rounded-xl border border-line">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead className="bg-canvas text-xs font-semibold text-muted">
          <tr>
            <th scope="col" className="w-12 px-3 py-2.5 text-center">ที่</th>
            <th scope="col" className="px-3 py-2.5 text-left">ตำแหน่ง</th>
            <th scope="col" className="px-3 py-2.5 text-left">ชื่อ-นามสกุล</th>
            <th scope="col" className="px-3 py-2.5 text-left">คุณวุฒิ</th>
            <th scope="col" className="px-3 py-2.5 text-left">สถาบัน</th>
            <th scope="col" className="px-3 py-2.5 text-center">ปีที่จบ</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {list.length === 0 && (
            <tr>
              <td colSpan={6} className="py-8 text-center text-muted">ไม่พบข้อมูลอาจารย์ผู้รับผิดชอบหลักสูตร</td>
            </tr>
          )}
          {list.map((inst, idx) => (
            <tr key={`${inst.name}-${idx}`} className="align-top">
              <td className="px-3 py-3 text-center text-muted">{idx + 1}</td>
              <td className="px-3 py-3 text-ink">{inst.position}</td>
              <td className="px-3 py-3 font-semibold text-ksu-navy">
                {inst.name}
                {inst.remarks && <span className="mt-1 block text-xs font-medium text-ok-fg">{inst.remarks}</span>}
              </td>
              <td className="px-3 py-3 text-ink">
                {inst.educations.length ? inst.educations.map((ed, i) => <div key={i}>{ed.degree || '-'}</div>) : '-'}
              </td>
              <td className="px-3 py-3 text-muted">
                {inst.educations.length ? inst.educations.map((ed, i) => <div key={i}>{ed.institution || '-'}</div>) : '-'}
              </td>
              <td className="px-3 py-3 text-center font-mono text-muted">
                {inst.educations.length ? inst.educations.map((ed, i) => <div key={i}>{ed.year || '-'}</div>) : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
