import type { ReactNode } from 'react';

interface SectionCardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  headerRight?: ReactNode;
  noPadding?: boolean;
}

export function SectionCard({ title, subtitle, children, className = '', headerRight, noPadding = false }: SectionCardProps) {
  return (
    <div className={`bg-surface-secondary border border-border-primary rounded-lg overflow-hidden ${className}`}>
      {(title || headerRight) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border-primary">
          <div>
            {title && <h3 className="text-sm font-semibold text-text-primary">{title}</h3>}
            {subtitle && <p className="text-xs text-text-tertiary mt-0.5">{subtitle}</p>}
          </div>
          {headerRight}
        </div>
      )}
      <div className={noPadding ? '' : 'p-4'}>{children}</div>
    </div>
  );
}
