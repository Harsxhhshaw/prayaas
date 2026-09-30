import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { relocationPriorities as fallbackPriorities } from '../data/mockData';
import type { RelocationPriority as PriorityItem } from '../types';
import { api } from '../lib/api';
import { useAppStore } from '../state/AppContext';
import { ArrowUpRight } from 'lucide-react';

export function RelocationPriority() {
  const navigate = useNavigate();
  const { selectedDistrict } = useAppStore();
  const [priorities, setPriorities] = useState<PriorityItem[]>(fallbackPriorities);
  const [isLive, setIsLive] = useState(false);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    let active = true;
    api.getRelocationPriorities({ district: selectedDistrict }).then((res) => {
      if (active) {
        if (res.data?.items && res.data.items.length > 0) {
          setPriorities(res.data.items);
        } else {
          setPriorities(fallbackPriorities.filter((p) => !selectedDistrict || p.district.toLowerCase() === selectedDistrict.toLowerCase()));
        }
        setIsLive(res.isLive);
      }
    });
    return () => {
      active = false;
    };
  }, [selectedDistrict]);

  const filtered = priorities.filter(
    (p) => filter === 'ALL' || p.urgency === filter
  );

  const immediateCount = priorities.filter((p) => p.urgency === 'IMMEDIATE').length;
  const shortCount = priorities.filter((p) => p.urgency === 'SHORT_TERM').length;
  const mediumCount = priorities.filter((p) => p.urgency === 'MEDIUM_TERM').length;

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              EVIDENCE-BASED RELOCATION PRIORITY MATRIX // {selectedDistrict.toUpperCase()}
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-panel-header border border-border-default text-text-muted rounded-[2px]">
              {priorities.length} HABITATIONS SCHEDULED
            </span>
            <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded-[2px] border ${isLive ? 'border-gis-green/30 text-gis-green bg-gis-green/10' : 'border-gis-yellow/30 text-gis-yellow bg-gis-yellow/10'}`}>
              {isLive ? 'LIVE' : 'DEMO'}
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Algorithmic prioritization ranking based on multi-hazard vulnerability and carrying capacity match.
          </p>
        </div>

        {/* Urgency Filter buttons */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-2 py-1 rounded-[2px] border text-[11px] transition-colors ${
              filter === 'ALL'
                ? 'bg-surface-active border-border-active text-text-primary'
                : 'bg-panel-header border-border-default text-text-muted hover:text-text-primary'
            }`}
          >
            ALL ({priorities.length})
          </button>
          <button
            onClick={() => setFilter('IMMEDIATE')}
            className={`px-2 py-1 rounded-[2px] border text-[11px] transition-colors ${
              filter === 'IMMEDIATE'
                ? 'bg-gis-red/20 border-gis-red/40 text-gis-red font-bold'
                : 'bg-panel-header border-border-default text-text-muted hover:text-gis-red'
            }`}
          >
            IMMEDIATE ({immediateCount})
          </button>
          <button
            onClick={() => setFilter('SHORT_TERM')}
            className={`px-2 py-1 rounded-[2px] border text-[11px] transition-colors ${
              filter === 'SHORT_TERM'
                ? 'bg-gis-orange/20 border-gis-orange/40 text-gis-orange font-bold'
                : 'bg-panel-header border-border-default text-text-muted hover:text-gis-orange'
            }`}
          >
            SHORT-TERM ({shortCount})
          </button>
          <button
            onClick={() => setFilter('MEDIUM_TERM')}
            className={`px-2 py-1 rounded-[2px] border text-[11px] transition-colors ${
              filter === 'MEDIUM_TERM'
                ? 'bg-gis-yellow/20 border-gis-yellow/40 text-gis-yellow font-bold'
                : 'bg-panel-header border-border-default text-text-muted hover:text-gis-yellow'
            }`}
          >
            MEDIUM-TERM ({mediumCount})
          </button>

          <button
            onClick={() => navigate('/')}
            className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] text-text-primary transition-colors flex items-center gap-1.5 ml-2"
          >
            <span>MAP WORKSTATION</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto mt-3 border border-border-default rounded-[2px] bg-panel-bg">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead className="sticky top-0 bg-panel-header text-[10px] uppercase tracking-wider text-text-muted border-b border-border-default z-10">
            <tr>
              <th className="py-2 px-3">Priority Tier</th>
              <th className="py-2 px-3">Habitation Entity</th>
              <th className="py-2 px-3">District</th>
              <th className="py-2 px-3 text-right">Composite Score</th>
              <th className="py-2 px-3 text-right">Displaced Population</th>
              <th className="py-2 px-3">Allocated Relocation Site</th>
              <th className="py-2 px-3 text-right">Est. Budget (INR)</th>
              <th className="py-2 px-3 text-right">Target Horizon</th>
              <th className="py-2 px-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-[11px]">
            {filtered.map((item) => (
              <tr key={item.habitationId} className="hover:bg-surface-hover text-text-secondary transition-colors">
                <td className="py-2 px-3">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider ${
                      item.urgency === 'IMMEDIATE'
                        ? 'text-gis-red'
                        : item.urgency === 'SHORT_TERM'
                        ? 'text-gis-orange'
                        : 'text-gis-yellow'
                    }`}
                  >
                    {item.urgency.replace('_', '-')}
                  </span>
                </td>
                <td className="py-2 px-3 font-semibold text-text-primary">
                  {item.habitationName}
                  <span className="text-[10px] text-text-muted font-normal ml-1.5">
                    ({item.habitationId})
                  </span>
                </td>
                <td className="py-2 px-3 text-text-muted">{item.district}</td>
                <td className="py-2 px-3 text-right font-bold tabular-nums">
                  <span
                    className={
                      item.riskScore >= 80
                        ? 'text-gis-red'
                        : item.riskScore >= 60
                        ? 'text-gis-orange'
                        : 'text-text-primary'
                    }
                  >
                    {item.riskScore}
                  </span>
                  <span className="text-[9px] text-text-muted font-normal ml-0.5">/100</span>
                </td>
                <td className="py-2 px-3 text-right tabular-nums text-text-primary font-bold">
                  {item.population.toLocaleString()}
                </td>
                <td className="py-2 px-3">
                  {item.assignedSiteName ? (
                    <span className="text-gis-green font-medium">{item.assignedSiteName}</span>
                  ) : (
                    <span className="text-text-muted">Unallocated / Site Search Pending</span>
                  )}
                </td>
                <td className="py-2 px-3 text-right tabular-nums text-text-primary">
                  {item.estimatedCost ? `₹${item.estimatedCost} Lakhs` : '—'}
                </td>
                <td className="py-2 px-3 text-right tabular-nums text-text-muted">
                  {item.timelineMonths ? `${item.timelineMonths} Months` : '—'}
                </td>
                <td className="py-2 px-3 text-center">
                  <span
                    className={`text-[10px] font-semibold uppercase ${
                      item.assignedSiteName ? 'text-gis-green' : 'text-text-muted'
                    }`}
                  >
                    {item.assignedSiteName ? 'ALLOCATED' : 'QUEUED'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
