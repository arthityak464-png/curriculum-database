import { getResponsibility, isCheckmarkProgram } from '../../lib/curriculum';

function Mark({ type, checkmark }) {
  if (!type) return null;
  if (checkmark || type === '✓' || type === '✔') {
    return <span className="text-base font-bold text-ok">✓</span>;
  }
  if (type === 'ความรับผิดชอบหลัก') {
    return <span className="inline-block h-3 w-3 rounded-full bg-ksu-navy" />;
  }
  if (type === 'ความรับผิดชอบรอง') {
    return <span className="inline-block h-3 w-3 rounded-full border-2 border-ksu-navy" />;
  }
  return <span className="text-xs text-muted">{type}</span>;
}

export function MatrixLegend({ checkmark }) {
  return (
    <div className="flex flex-wrap items-center gap-4 text-sm text-muted">
      {checkmark ? (
        <span className="flex items-center gap-1.5"><span className="font-bold text-ok">✓</span> รับผิดชอบ PLO</span>
      ) : (
        <>
          <span className="flex items-center gap-1.5"><span className="inline-block h-3 w-3 rounded-full bg-ksu-navy" /> รับผิดชอบหลัก</span>
          <span className="flex items-center gap-1.5"><span className="inline-block h-3 w-3 rounded-full border-2 border-ksu-navy" /> รับผิดชอบรอง</span>
        </>
      )}
      <span>· คลิกหัวคอลัมน์เพื่อดูคำอธิบาย PLO</span>
    </div>
  );
}

/**
 * ตาราง Curriculum Mapping (รายวิชา × PLO)
 * ใช้ร่วมกันในห้องตรวจทานและคลังหลักสูตร
 */
export default function PloMatrix({ plos, rows, onCourseClick, onPloClick, maxHeightClass = 'max-h-[640px]' }) {
  const checkmark = isCheckmarkProgram(plos);

  if (rows.length === 0) {
    return <p className="py-12 text-center text-sm text-muted">ไม่พบข้อมูลการกระจายความรับผิดชอบ</p>;
  }

  return (
    <div className={`scroll-thin overflow-auto ${maxHeightClass}`}>
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 z-20 bg-canvas">
          <tr className="border-b border-line text-left text-xs font-semibold text-muted">
            <th scope="col" className="sticky left-0 z-10 w-28 bg-canvas px-4 py-3">รหัสวิชา</th>
            <th scope="col" className="min-w-[220px] px-4 py-3">ชื่อรายวิชา</th>
            {plos.map((plo) => (
              <th key={plo.plo_code} scope="col" className="px-1 py-2 text-center">
                <button
                  type="button"
                  onClick={() => onPloClick?.(plo)}
                  title={plo.plo_description}
                  className="rounded-md px-1.5 py-1 font-mono text-xs text-ksu-navy underline decoration-dotted underline-offset-4 hover:bg-ksu-mist"
                >
                  {plo.plo_code}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row) => (
            <tr key={row.course_code} className="hover:bg-ksu-mist/50">
              <td className="sticky left-0 z-10 bg-white px-4 py-2.5">
                <button type="button" onClick={() => onCourseClick?.(row.course_code)} className="font-mono font-semibold text-ksu-blue hover:underline">
                  {row.course_code}
                </button>
              </td>
              <td className="max-w-xs truncate px-4 py-2.5 text-ink" title={row.course_name_th}>{row.course_name_th}</td>
              {plos.map((plo) => {
                const type = getResponsibility(row, plo.plo_code);
                return (
                  <td key={plo.plo_code} className="px-1 py-2 text-center">
                    {type && (
                      <button
                        type="button"
                        onClick={() => onPloClick?.({ ...plo, contextCourse: row.course_name_th, contextType: type })}
                        aria-label={`${row.course_code} ${plo.plo_code}: ${type}`}
                        className="inline-flex h-7 w-7 items-center justify-center rounded-md hover:bg-ksu-mist"
                      >
                        <Mark type={type} checkmark={checkmark} />
                      </button>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
