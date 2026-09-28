interface RiskBarProps {
  label: string;
  value: number;
  maxValue?: number;
  showValue?: boolean;
  size?: 'sm' | 'md';
}

function getRiskColor(value: number): string {
  if (value >= 80) return 'bg-risk-critical';
  if (value >= 60) return 'bg-risk-high';
  if (value >= 40) return 'bg-risk-watch';
  return 'bg-risk-safe';
}

function getRiskTextColor(value: number): string {
  if (value >= 80) return 'text-risk-critical';
  if (value >= 60) return 'text-risk-high';
  if (value >= 40) return 'text-risk-watch';
  return 'text-risk-safe';
}

export function RiskBar({ label, value, maxValue = 100, showValue = true, size = 'md' }: RiskBarProps) {
  const percentage = Math.min((value / maxValue) * 100, 100);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className={`text-text-secondary ${size === 'sm' ? 'text-[11px]' : 'text-xs'}`}>{label}</span>
        {showValue && (
          <span className={`font-semibold ${size === 'sm' ? 'text-[11px]' : 'text-xs'} ${getRiskTextColor(value)}`}>
            {value}
          </span>
        )}
      </div>
      <div className={`w-full bg-navy-800 rounded-full overflow-hidden ${size === 'sm' ? 'h-1' : 'h-1.5'}`}>
        <div
          className={`h-full rounded-full transition-all duration-500 ${getRiskColor(value)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
