const escapeRegex = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** ไฮไลต์คำค้นในข้อความ */
export default function Highlight({ text, query }) {
  if (!text) return null;
  const tokens = [query, ...(query || '').split(/\s+/)]
    .map((t) => t?.trim())
    .filter((t) => t && t.length >= 2)
    .sort((a, b) => b.length - a.length);
  if (tokens.length === 0) return text;
  const pattern = new RegExp(`(${tokens.map(escapeRegex).join('|')})`, 'gi');
  const lowerTokens = tokens.map((t) => t.toLowerCase());
  return text.split(pattern).map((part, i) =>
    lowerTokens.includes(part.toLowerCase()) ? (
      <mark key={i} className="rounded bg-[#fff1c2] px-0.5 text-ink">{part}</mark>
    ) : (
      part
    ),
  );
}
