import { type ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: ReactNode;
  color?: 'blue' | 'red' | 'orange' | 'yellow' | 'green' | 'default';
}

const colorMap = {
  blue: 'text-risk-info',
  red: 'text-risk-critical',
  orange: 'text-risk-high',
  yellow: 'text-risk-watch',
  green: 'text-risk-safe',
  default: 'text-text-secondary',
};

const bgColorMap = {
  blue: 'bg-risk-info/10',
  red: 'bg-risk-critical/10',
  orange: 'bg-risk-high/10',
  yellow: 'bg-risk-watch/10',
  green: 'bg-risk-safe/10',
  default: 'bg-navy-700/50',
};

export function MetricCard({ label, value, change, changeLabel, icon, color = 'default' }: MetricCardProps) {
  return (
    <div className="bg-surface-secondary border border-border-primary rounded-lg p-4 hover:border-border-secondary transition-colors">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">{label}</span>
        {icon && (
          <div className={`p-1.5 rounded-md ${bgColorMap[color]}`}>
            <div className={colorMap[color]}>{icon}</div>
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-text-primary mb-1">{value}</div>
      {change !== undefined && (
        <div className="flex items-center gap-1 text-xs">
          {change > 0 ? (
            <TrendingUp className="w-3 h-3 text-risk-high" />
          ) : change < 0 ? (
            <TrendingDown className="w-3 h-3 text-risk-safe" />
          ) : (
            <Minus className="w-3 h-3 text-text-tertiary" />
          )}
          <span className={change > 0 ? 'text-risk-high' : change < 0 ? 'text-risk-safe' : 'text-text-tertiary'}>
            {change > 0 ? '+' : ''}{change}
          </span>
          {changeLabel && <span className="text-text-tertiary">{changeLabel}</span>}
        </div>
      )}
    </div>
  );
}
