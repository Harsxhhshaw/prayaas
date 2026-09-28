import { AlertTriangle, CloudRain, ClipboardCheck, ArrowUpDown, Radio, Server, Circle } from 'lucide-react';
import { operationalAlerts } from '../../data/mockData';
import type { OperationalAlert } from '../../types';

const alertIcons: Record<string, typeof AlertTriangle> = {
  ESCALATION: AlertTriangle,
  WEATHER: CloudRain,
  VERIFICATION: ClipboardCheck,
  PRIORITY_CHANGE: ArrowUpDown,
  FIELD_UPDATE: Radio,
  SYSTEM: Server,
};

const severityColors: Record<string, string> = {
  CRITICAL: 'text-risk-critical',
  HIGH: 'text-risk-high',
  WATCH: 'text-risk-watch',
  SAFE: 'text-risk-safe',
};

export function OperationalAlerts() {
  return (
    <div className="bg-surface-secondary border border-border-primary rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-border-primary flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">Operational Alerts</h3>
          <p className="text-[11px] text-text-tertiary mt-0.5">Real-time activity feed</p>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-risk-critical/15 text-risk-critical font-medium">
          {operationalAlerts.filter((a) => !a.read).length} new
        </span>
      </div>

      <div className="max-h-[380px] overflow-y-auto">
        {operationalAlerts.map((alert) => {
          const Icon = alertIcons[alert.type] || Server;
          const color = severityColors[alert.severity] || 'text-text-tertiary';

          return (
            <div
              key={alert.id}
              className={`flex items-start gap-3 px-4 py-3 border-b border-border-primary/50 last:border-0 hover:bg-navy-800/20 transition-colors ${
                !alert.read ? 'bg-navy-800/10' : ''
              }`}
            >
              <div className={`p-1.5 rounded-md bg-surface-tertiary shrink-0 mt-0.5`}>
                <Icon className={`w-3.5 h-3.5 ${color}`} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-start gap-1.5">
                  {!alert.read && <Circle className="w-1.5 h-1.5 mt-1.5 fill-risk-info text-risk-info shrink-0" />}
                  <p className="text-[11px] text-text-primary leading-relaxed">{alert.message}</p>
                </div>
                <p className="text-[10px] text-text-tertiary mt-1">
                  {new Date(alert.timestamp).toLocaleString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
