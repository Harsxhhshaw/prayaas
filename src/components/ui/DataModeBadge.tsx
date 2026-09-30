import React from 'react';
import { Database, ShieldAlert, Cpu, CheckCircle2, FileText, HelpCircle, WifiOff } from 'lucide-react';

export type DataModeType =
  | 'LIVE'
  | 'DEMO'
  | 'DEMO SNAPSHOT'
  | 'MODELED'
  | 'FIELD'
  | 'FIELD_VERIFIED'
  | 'PUBLIC'
  | 'PUBLIC_VERIFIED'
  | 'PLANNING_ASSUMPTION'
  | 'UNKNOWN'
  | 'OFFLINE';

interface DataModeBadgeProps {
  mode: DataModeType | string;
  label?: string;
  size?: 'sm' | 'md';
  showIcon?: boolean;
  className?: string;
}

export const DataModeBadge: React.FC<DataModeBadgeProps> = ({
  mode,
  label,
  size = 'sm',
  showIcon = true,
  className = '',
}) => {
  const normalized = (mode || 'UNKNOWN').toUpperCase();

  let styles = 'bg-slate-800 text-slate-300 border-slate-700';
  let defaultLabel = normalized;
  let icon = <HelpCircle className="w-3 h-3" />;

  switch (normalized) {
    case 'LIVE':
      styles = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      defaultLabel = 'LIVE POSTGIS';
      icon = <Database className="w-3 h-3 text-emerald-400" />;
      break;
    case 'DEMO':
    case 'DEMO SNAPSHOT':
      styles = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      defaultLabel = 'DEMO SNAPSHOT';
      icon = <ShieldAlert className="w-3 h-3 text-amber-400" />;
      break;
    case 'MODELED':
      styles = 'bg-blue-500/15 text-blue-300 border-blue-500/30';
      defaultLabel = 'MODELED (ALGORITHMIC)';
      icon = <Cpu className="w-3 h-3 text-blue-400" />;
      break;
    case 'FIELD':
    case 'FIELD_VERIFIED':
      styles = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      defaultLabel = 'FIELD VERIFIED';
      icon = <CheckCircle2 className="w-3 h-3 text-emerald-400" />;
      break;
    case 'PUBLIC':
    case 'PUBLIC_VERIFIED':
      styles = 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30';
      defaultLabel = 'PUBLIC VERIFIED';
      icon = <FileText className="w-3 h-3 text-cyan-400" />;
      break;
    case 'PLANNING_ASSUMPTION':
      styles = 'bg-purple-500/15 text-purple-300 border-purple-500/30';
      defaultLabel = 'PLANNING ASSUMPTION';
      icon = <ShieldAlert className="w-3 h-3 text-purple-400" />;
      break;
    case 'OFFLINE':
      styles = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
      defaultLabel = 'OFFLINE SNAPSHOT';
      icon = <WifiOff className="w-3 h-3 text-rose-400" />;
      break;
    case 'UNKNOWN':
    default:
      styles = 'bg-slate-700/50 text-slate-400 border-slate-600/50';
      defaultLabel = 'UNKNOWN / UNMEASURED';
      icon = <HelpCircle className="w-3 h-3 text-slate-400" />;
      break;
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono uppercase tracking-wider rounded border ${padding} ${styles} ${className}`}
      title={`Data provenance mode: ${defaultLabel}`}
    >
      {showIcon && icon}
      <span>{label || defaultLabel}</span>
    </span>
  );
};
