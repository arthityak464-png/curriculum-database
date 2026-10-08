import SelectField from '../ui/SelectField';
import { cleanCurriculumName, getDisplayCode } from '../../lib/curriculum';

/** dropdown เลือกหลักสูตร */
export default function CurriculumPicker({ curriculums, value, onChange, label = 'เลือกหลักสูตร', includeAll = false, className = '' }) {
  const options = [
    ...(includeAll ? [{ value: '', label: 'ทุกหลักสูตร' }] : []),
    ...curriculums.map((c) => ({ value: c.id, label: `${getDisplayCode(c)} · ${cleanCurriculumName(c)}` })),
  ];
  return (
    <SelectField
      label={label}
      hideLabel
      value={value || ''}
      onChange={onChange}
      options={options}
      className={className}
      selectClassName="min-h-10 max-w-[340px] truncate text-sm font-medium"
    />
  );
}
