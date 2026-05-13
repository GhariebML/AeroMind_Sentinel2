import { type HTMLAttributes, forwardRef } from 'react';

export interface SectionHeaderProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  eyebrow?: string;
  title: React.ReactNode;
  description?: string;
  align?: 'left' | 'center';
}

const SectionHeader = forwardRef<HTMLDivElement, SectionHeaderProps>(
  ({ className = '', eyebrow, title, description, align = 'center', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`flex flex-col gap-5 ${align === 'center' ? 'items-center text-center mx-auto' : 'items-start text-left'} max-w-3xl ${className}`}
        {...props}
      >
        {eyebrow && (
          <div className="inline-flex items-center rounded-full border border-cyan-400/25 bg-cyan-400/8 px-4 py-2 shadow-[0_0_20px_rgba(34,211,238,0.08)]">
            <span className="text-[11px] font-black uppercase tracking-[0.22em] text-cyan-300">
              {eyebrow}
            </span>
          </div>
        )}
        <h2 className="text-4xl font-black leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-[3.5rem]">
          {title}
        </h2>
        {description && (
          <p className="text-[15px] leading-[1.85] text-slate-400 sm:text-base max-w-2xl">
            {description}
          </p>
        )}
      </div>
    );
  }
);
SectionHeader.displayName = 'SectionHeader';

export { SectionHeader };
