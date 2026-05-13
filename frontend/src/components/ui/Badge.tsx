import { type HTMLAttributes, forwardRef } from 'react';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'warning' | 'critical';
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className = '', variant = 'primary', ...props }, ref) => {
    const baseStyles = 'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest whitespace-nowrap';
    
    const variants = {
      primary: 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/20',
      secondary: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
      outline: 'bg-white/5 text-slate-300 border border-white/10',
      warning: 'bg-orange-500/10 text-orange-400 border border-orange-500/20',
      critical: 'bg-red-500/10 text-red-400 border border-red-500/20',
    };

    return (
      <span
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${className}`}
        {...props}
      />
    );
  }
);
Badge.displayName = 'Badge';

export { Badge };
