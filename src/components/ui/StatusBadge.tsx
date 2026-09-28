import type { RiskCategory, UrgencyLevel, VerificationStatus } from '../../types';

type BadgeVariant = RiskCategory | UrgencyLevel | VerificationStatus | 'INFO';

interface StatusBadgeProps {
  variant: BadgeVariant;
  label?: string;
  size?: 'sm' | 'md';
  pulse?: boolean;
}

const variantStyles: Record<string, string> = {
  CRITICAL: 'bg-risk-critical/15 text-risk-critical border-risk-critical/30',
  HIGH: 'bg-risk-high/15 text-risk-high border-risk-high/30',
  WATCH: 'bg-risk-watch/15 text-risk-watch border-risk-watch/30',
  SAFE: 'bg-risk-safe/15 text-risk-safe border-risk-safe/30',
  IMMEDIATE: 'bg-risk-critical/15 text-risk-critical border-risk-critical/30',
  SHORT_TERM: 'bg-risk-high/15 text-risk-high border-risk-high/30',
  MEDIUM_TERM: 'bg-risk-watch/15 text-risk-watch border-risk-watch/30',
  VERIFIED: 'bg-risk-safe/15 text-risk-safe border-risk-safe/30',
  PENDING: 'bg-risk-watch/15 text-risk-watch border-risk-watch/30',
  IN_PROGRESS: 'bg-risk-info/15 text-risk-info border-risk-info/30',
  FLAGGED: 'bg-risk-critical/15 text-risk-critical border-risk-critical/30',
  INFO: 'bg-risk-info/15 text-risk-info border-risk-info/30',
};

const displayLabels: Record<string, string> = {
  CRITICAL: 'Critical',
  HIGH: 'High Risk',
  WATCH: 'Watch',
  SAFE: 'Safe',
  IMMEDIATE: 'Immediate',
  SHORT_TERM: 'Short-Term',
  MEDIUM_TERM: 'Medium-Term',
  VERIFIED: 'Verified',
  PENDING: 'Pending',
  IN_PROGRESS: 'In Progress',
  FLAGGED: 'Flagged',
  INFO: 'Info',
};

export function StatusBadge({ variant, label, size = 'sm', pulse = false }: StatusBadgeProps) {
  const styles = variantStyles[variant] || variantStyles.INFO;
  const displayLabel = label || displayLabels[variant] || variant;
  
  return (
    <span className={`inline-flex items-center gap-1.5 border rounded-full font-medium ${
      size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs'
    } ${styles}`}>
      {pulse && (
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-current" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-current" />
        </span>
      )}
      {displayLabel}
    </span>
  );
}
