import { ExternalLink, FileText } from 'lucide-react';

/** แผงซ้าย: เอกสารต้นฉบับ มคอ.2 */
export default function PdfPane({ url }) {
  return (
    <section aria-label="เอกสารต้นฉบับ" className="flex min-h-[60vh] flex-col border-line bg-[#e4eaf3] lg:min-h-0 lg:border-r">
      <div className="flex h-11 shrink-0 items-center justify-between border-b border-line bg-white px-4 text-sm">
        <span className="flex items-center gap-2 font-semibold text-ink">
          <FileText className="h-4 w-4 text-ksu-blue" aria-hidden="true" /> เอกสารต้นฉบับ มคอ.2
        </span>
        {url && (
          <a href={url} target="_blank" rel="noreferrer" className="flex items-center gap-1 font-medium">
            เปิดแท็บใหม่ <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        )}
      </div>
      <div className="relative flex-1">
        {url ? (
          <object data={`${url}#toolbar=1&navpanes=0`} type="application/pdf" className="absolute inset-0 h-full w-full">
            <iframe src={`${url}#toolbar=1&navpanes=0`} title="เอกสาร มคอ.2" className="h-full w-full border-0" />
          </object>
        ) : (
          <p className="flex h-full items-center justify-center text-sm text-muted">ไม่พบไฟล์ PDF</p>
        )}
      </div>
    </section>
  );
}
