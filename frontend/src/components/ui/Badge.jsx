const TONES = {
  ok: 'bg-ok-bg text-ok-fg',
  warn: 'bg-warn-bg text-warn-fg',
  info: 'bg-ksu-mist text-ksu-navy',
  neutral: 'bg-canvas text-muted border border-line',
  danger: 'bg-danger-bg text-danger',
};

const DOTS = {
  ok: 'bg-ok',
  warn: 'bg-warn',
  info: 'bg-ksu-blue',
  neutral: 'bg-subtle',
  danger: 'bg-danger',
};

export default function Badge({ tone = 'neutral', dot = false, mono = false, className = '', children, ...rest }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${TONES[tone]} ${mono ? 'font-mono' : ''} ${className}`}
      {...rest}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${DOTS[tone]}`} aria-hidden="true" />}
      {children}
    </span>
  );
}
