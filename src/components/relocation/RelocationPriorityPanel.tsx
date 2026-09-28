import { AlertTriangle, Clock, Timer, ChevronRight } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { relocationPriorities } from '../../data/mockData';
import type { UrgencyLevel } from '../../types';

interface RelocationPriorityPanelProps {
  onSelectHabitation: (habitationId: string) => void;
}

const urgencyConfig: Record<UrgencyLevel, { label: string; icon: typeof AlertTriangle; colorClass: string }> = {
  IMMEDIATE: { label: 'Immediate', icon: AlertTriangle, colorClass: 'text-risk-critical' },
  SHORT_TERM: { label: 'Short-Term', icon: Clock, colorClass: 'text-risk-high' },
  MEDIUM_TERM: { label: 'Medium-Term', icon: Timer, colorClass: 'text-risk-watch' },
};

export function RelocationPriorityPanel({ onSelectHabitation }: RelocationPriorityPanelProps) {
  const urgencyGroups: UrgencyLevel[] = ['IMMEDIATE', 'SHORT_TERM', 'MEDIUM_TERM'];

  return (
    <div className="bg-surface-secondary border border-border-primary rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-border-primary">
        <h3 className="text-sm font-semibold text-text-primary">Relocation Priority Queue</h3>
        <p className="text-[11px] text-text-tertiary mt-0.5">{relocationPriorities.length} habitations queued</p>
      </div>

      <div className="max-h-[380px] overflow-y-auto">
        {urgencyGroups.map((urgency) => {
          const config = urgencyConfig[urgency];
          const Icon = config.icon;
          const items = relocationPriorities.filter((p) => p.urgency === urgency);

          return (
            <div key={urgency}>
              {/* Group Header */}
              <div className="flex items-center gap-2 px-4 py-2 bg-navy-800/30 border-y border-border-primary">
                <Icon className={`w-3.5 h-3.5 ${config.colorClass}`} />
                <span className={`text-[11px] font-semibold uppercase tracking-wider ${config.colorClass}`}>
                  {config.label}
                </span>
                <span className="text-[10px] text-text-tertiary ml-auto">{items.length} habitations</span>
              </div>

              {/* Items */}
              {items.map((item) => (
                <button
                  key={item.habitationId}
                  onClick={() => onSelectHabitation(item.habitationId)}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-navy-800/20 transition-colors border-b border-border-primary/50 last:border-0 text-left group"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-text-primary truncate">{item.habitationName}</span>
                      <span className={`text-[10px] font-bold ${config.colorClass}`}>{item.riskScore}</span>
                    </div>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-[10px] text-text-tertiary">{item.district}</span>
                      <span className="text-[10px] text-text-tertiary">Pop: {item.population.toLocaleString()}</span>
                      {item.assignedSiteName && (
                        <span className="text-[10px] text-risk-safe">→ {item.assignedSiteName}</span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-text-muted group-hover:text-text-tertiary shrink-0" />
                </button>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
