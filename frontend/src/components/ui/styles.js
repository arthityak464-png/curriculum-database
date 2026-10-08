// คลาสพื้นฐานของฟอร์ม ใช้ร่วมกันทั้งระบบ
export const inputClass =
  'w-full min-h-11 rounded-lg border border-line-strong bg-white px-3 text-[15px] text-ink placeholder:text-subtle ' +
  'transition focus:border-ksu-blue focus:outline-none focus:ring-4 focus:ring-ksu-mist disabled:cursor-not-allowed disabled:bg-canvas disabled:text-muted';

export const textareaClass = `${inputClass} py-2.5 leading-relaxed`;

export const selectClass = `${inputClass} cursor-pointer appearance-none pr-9`;

export const labelClass = 'mb-1.5 block text-sm font-semibold text-muted';
