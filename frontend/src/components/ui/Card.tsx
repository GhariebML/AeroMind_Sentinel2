import { type HTMLAttributes, forwardRef } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', hoverEffect = false, ...props }, ref) => {
    const baseStyles = 'rounded-2xl border border-white/10 bg-slate-950/60 p-6 backdrop-blur-xl shadow-xl shadow-black/20';
    const hoverStyles = hoverEffect ? 'transition-all duration-300 hover:-translate-y-1 hover:border-cyan-400/30 hover:shadow-[0_10px_30px_rgba(34,211,238,0.1)] hover:bg-slate-900/80' : '';
    
    return (
      <div
        ref={ref}
        className={`${baseStyles} ${hoverStyles} ${className}`}
        {...props}
      />
    );
  }
);
Card.displayName = 'Card';

export { Card };
