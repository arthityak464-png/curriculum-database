import { ChevronDown } from 'lucide-react';
import { selectClass } from './styles';

/** select ที่มีลูกศรและ label (ใส่ hideLabel เพื่อซ่อน label แต่ยังอ่านได้ด้วย screen reader) */
export default function SelectField({ label, hideLabel = false, value, onChange, options, className = '', selectClassName = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className={hideLabel ? 'sr-only' : 'mb-1.5 block text-sm font-semibold text-muted'}>{label}</span>
      <span className="relative block">
        <select value={value} onChange={(e) => onChange(e.target.value)} className={`${selectClass} ${selectClassName}`}>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute top-1/2 right-3 h-4 w-4 -translate-y-1/2 text-subtle" aria-hidden="true" />
      </span>
    </label>
  );
}
