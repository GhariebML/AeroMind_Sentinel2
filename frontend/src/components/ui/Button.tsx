import { type ButtonHTMLAttributes, forwardRef } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', size = 'md', ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center gap-2 rounded-full font-bold transition-all disabled:opacity-50 disabled:pointer-events-none';
    
    const variants = {
      primary: 'bg-cyan-400 text-slate-950 shadow-[0_0_15px_rgba(34,211,238,0.3)] hover:bg-cyan-300 hover:shadow-[0_0_25px_rgba(34,211,238,0.5)]',
      secondary: 'bg-emerald-400 text-slate-950 shadow-[0_0_15px_rgba(52,211,153,0.3)] hover:bg-emerald-300 hover:shadow-[0_0_25px_rgba(52,211,153,0.5)]',
      outline: 'border border-cyan-400/20 bg-cyan-400/5 text-cyan-300 hover:bg-cyan-400/10 hover:border-cyan-400/40',
      ghost: 'text-slate-300 hover:text-white hover:bg-white/5',
    };

    const sizes = {
      sm: 'px-4 py-2 text-[11px] uppercase tracking-[0.15em]',
      md: 'px-6 py-3 text-sm uppercase tracking-[0.1em]',
      lg: 'px-8 py-4 text-base uppercase tracking-[0.1em]',
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button };
