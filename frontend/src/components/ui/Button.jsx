import { Loader2 } from 'lucide-react';

const VARIANTS = {
  primary: 'bg-ksu-blue text-white hover:bg-ksu-navy disabled:hover:bg-ksu-blue',
  secondary: 'bg-white text-ksu-navy border border-line-strong hover:bg-ksu-mist',
  ghost: 'text-muted hover:bg-ksu-mist hover:text-ksu-navy',
  danger: 'bg-danger text-white hover:bg-[#912018]',
  success: 'bg-ok text-white hover:bg-ok-fg',
};

const SIZES = {
  md: 'min-h-11 px-4 text-[15px] gap-2',
  sm: 'min-h-9 px-3 text-sm gap-1.5',
  icon: 'h-10 w-10 justify-center',
};

/**
 * ปุ่มมาตรฐาน — ใช้ href เพื่อให้เป็นลิงก์ (<a>) แทนปุ่ม
 * <Button icon={Save} loading={saving}>บันทึก</Button>
 */
export default function Button({
  variant = 'primary',
  size = 'md',
  icon: Icon,
  loading = false,
  href,
  className = '',
  children,
  type = 'button',
  disabled,
  ...rest
}) {
  const classes =
    `inline-flex shrink-0 items-center justify-center rounded-lg font-semibold whitespace-nowrap transition ` +
    `disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${SIZES[size]} ${className}`;
  const content = (
    <>
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : Icon && <Icon className="h-4 w-4" aria-hidden="true" />}
      {children}
    </>
  );

  if (href) {
    return (
      <a href={href} className={`${classes} no-underline`} {...rest}>
        {content}
      </a>
    );
  }
  return (
    <button type={type} className={classes} disabled={disabled || loading} {...rest}>
      {content}
    </button>
  );
}
