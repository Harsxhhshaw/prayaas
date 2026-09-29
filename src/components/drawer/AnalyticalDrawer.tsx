import { useState, useEffect } from 'react';
import {
  ChevronUp,
  ChevronDown,
  AlertTriangle,
  Radio,
  Clock,
  Database,
  ExternalLink,
  ShieldAlert,
  AlertOctagon,
} from 'lucide-react';
import { relocationPriorities as mockPriorities, operationalAlerts, habitations } from '../../data/mockData';
import type { Habitation, RelocationPriority } from '../../types';
import { api } from '../../lib/api';

interface AnalyticalDrawerProps {
  onSelectHabitation: (habitation: Habitation) => void;
  selectedHabitationId?: string;
}

type TabType = 'priority' | 'alerts' | 'timeline' | 'quality';

export function AnalyticalDrawer({ onSelectHabitation, selectedHabitationId }: AnalyticalDrawerProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('priority');
  const [priorities, setPriorities] = useState<RelocationPriority[]>(mockPriorities);

  useEffect(() => {
    api.getRelocationPriorities().then((res) => {
      if (res.data?.items && res.data.items.length > 0) {
        setPriorities(res.data.items);
      }
    }).catch(() => {
      // Keep mock fallback
    });
  }, []);

  const unreadAlertsCount = operationalAlerts.filter((a) => !a.read).length;

  const handleRowClick = (habitationId: string) => {
    const hab = habitations.find((h) => h.id === habitationId);
    if (hab) {
      onSelectHabitation(hab);
    }
  };

  return (
    <div
      className={`border-t border-border-default bg-panel-bg flex flex-col z-20 select-none transition-all duration-200 ${
        isExpanded ? 'h-72' : 'h-8'
      }`}
    >
      {/* 1. Collapsed Bar / Tab Header */}
      <div className="h-8 bg-panel-header px-3 flex items-center justify-between shrink-0 border-b border-border-subtle">
        {/* Left Tabs */}
        <div className="flex items-center gap-1 font-mono text-[11px]">
          <button
            onClick={() => {
              setActiveTab('priority');
              setIsExpanded(true);
            }}
            className={`px-2.5 py-1 flex items-center gap-1.5 transition-colors border-b-2 ${
              activeTab === 'priority' && isExpanded
                ? 'border-gis-red text-text-primary bg-panel-bg font-semibold'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            <AlertTriangle className="w-3 h-3 text-gis-red" />
            <span>RELOCATION PRIORITY ({priorities.length})</span>
          </button>


          <button
            onClick={() => {
              setActiveTab('alerts');
              setIsExpanded(true);
            }}
            className={`px-2.5 py-1 flex items-center gap-1.5 transition-colors border-b-2 ${
              activeTab === 'alerts' && isExpanded
                ? 'border-gis-orange text-text-primary bg-panel-bg font-semibold'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            <Radio className="w-3 h-3 text-gis-orange" />
            <span>OPERATIONAL ALERTS ({operationalAlerts.length})</span>
            {unreadAlertsCount > 0 && (
              <span className="w-1.5 h-1.5 rounded-full bg-gis-red" />
            )}
          </button>

          <button
            onClick={() => {
              setActiveTab('timeline');
              setIsExpanded(true);
            }}
            className={`px-2.5 py-1 flex items-center gap-1.5 transition-colors border-b-2 ${
              activeTab === 'timeline' && isExpanded
                ? 'border-gis-blue text-text-primary bg-panel-bg font-semibold'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            <Clock className="w-3 h-3 text-gis-blue" />
            <span>RISK TRAJECTORY (5Y)</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('quality');
              setIsExpanded(true);
            }}
            className={`px-2.5 py-1 flex items-center gap-1.5 transition-colors border-b-2 ${
              activeTab === 'quality' && isExpanded
                ? 'border-gis-green text-text-primary bg-panel-bg font-semibold'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            <Database className="w-3 h-3 text-gis-green" />
            <span>TELEMETRY & SENSORS</span>
          </button>
        </div>

        {/* Right Toggle */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-[11px] font-mono text-text-muted hover:text-text-primary px-2 py-0.5 rounded-[1px] hover:bg-surface-hover"
        >
          <span>{isExpanded ? 'COLLAPSE' : 'EXPAND DRAWER'}</span>
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* 2. Expanded Body (Dense tables, zero card bloat) */}
      {isExpanded && (
        <div className="flex-1 overflow-auto bg-workspace font-mono text-xs">
          {/* =================================================================
              TAB 1: RELOCATION PRIORITY DATA GRID
             ================================================================= */}
          {activeTab === 'priority' && (
            <table className="w-full text-left border-collapse text-[11px]">
              <thead className="sticky top-0 bg-panel-header text-text-muted uppercase text-[10px] tracking-wider border-b border-border-default z-10">
                <tr>
                  <th className="py-2 px-3">Priority</th>
                  <th className="py-2 px-3">Habitation</th>
                  <th className="py-2 px-3">District</th>
                  <th className="py-2 px-3 text-right">Risk</th>
                  <th className="py-2 px-3 text-right">Need Score</th>
                  <th className="py-2 px-3 text-right">Readiness</th>
                  <th className="py-2 px-3">Matrix Position</th>
                  <th className="py-2 px-3 text-right">Population</th>
                  <th className="py-2 px-3">Assigned Site</th>
                  <th className="py-2 px-3 text-right">Timeline</th>
                  <th className="py-2 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {priorities.map((item) => {
                  const isSelected = item.habitationId === selectedHabitationId;
                  const isImmediate = item.urgency === 'IMMEDIATE';
                  const isShortTerm = item.urgency === 'SHORT_TERM';
                  const needScore = item.needScore ?? item.riskScore;
                  const readinessScore = item.readinessScore ?? 40.0;
                  const readinessLevel = item.readinessLevel ?? 'LOW_READINESS';

                  return (
                    <tr
                      key={item.habitationId}
                      onClick={() => handleRowClick(item.habitationId)}
                      className={`cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-surface-active text-text-primary border-l-2 border-gis-blue'
                          : 'hover:bg-surface-hover text-text-secondary'
                      }`}
                    >
                      <td className="py-1.5 px-3">
                        <span
                          className={`font-semibold tracking-wider text-[10px] uppercase ${
                            isImmediate
                              ? 'text-gis-red'
                              : isShortTerm
                              ? 'text-gis-orange'
                              : 'text-gis-yellow'
                          }`}
                        >
                          {item.urgency.replace('_', '-')}
                        </span>
                      </td>
                      <td className="py-1.5 px-3 font-semibold text-text-primary">
                        {item.habitationName}
                        <span className="text-[10px] font-normal text-text-muted ml-1.5">
                          {item.habitationId}
                        </span>
                      </td>
                      <td className="py-1.5 px-3 text-text-secondary">{item.district}</td>
                      <td className="py-1.5 px-3 text-right font-bold tabular-nums">
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
                      </td>
                      <td className="py-1.5 px-3 text-right font-bold tabular-nums text-gis-red">
                        {needScore.toFixed(1)}
                      </td>
                      <td className="py-1.5 px-3 text-right tabular-nums">
                        <span className="text-text-primary font-bold">{readinessScore.toFixed(1)}</span>
                        <span className="text-[9px] text-text-muted ml-1 uppercase">
                          ({readinessLevel.split('_')[0]})
                        </span>
                      </td>
                      <td className="py-1.5 px-3">
                        <span className="px-1 py-0.2 bg-panel-header border border-border-subtle rounded-[1px] text-[9px] text-gis-orange font-bold">
                          {needScore >= 60 && readinessScore < 50 ? 'BOTTLENECK' : needScore >= 60 ? 'READY' : 'MONITOR'}
                        </span>
                      </td>
                      <td className="py-1.5 px-3 text-right tabular-nums text-text-primary">
                        {item.population.toLocaleString()}
                      </td>
                      <td className="py-1.5 px-3 text-text-secondary">
                        {item.assignedSiteName ? (
                          <span className="text-gis-green">{item.assignedSiteName}</span>
                        ) : (
                          <span className="text-text-muted">Unallocated</span>
                        )}
                      </td>
                      <td className="py-1.5 px-3 text-right tabular-nums text-text-secondary">
                        {item.timelineMonths ? `${item.timelineMonths}m` : '—'}
                      </td>
                      <td className="py-1.5 px-3 text-center">
                        <span className="text-[10px] text-gis-blue hover:underline">Inspect →</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}

          {/* =================================================================
              TAB 2: OPERATIONAL ALERTS FEED
             ================================================================= */}
          {activeTab === 'alerts' && (
            <table className="w-full text-left border-collapse text-[11px]">
              <thead className="sticky top-0 bg-panel-header text-text-muted uppercase text-[10px] tracking-wider border-b border-border-default z-10">
                <tr>
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Severity</th>
                  <th className="py-2 px-3">Type</th>
                  <th className="py-2 px-3">Event Telemetry / Intelligence</th>
                  <th className="py-2 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {operationalAlerts.map((alert) => (
                  <tr
                    key={alert.id}
                    onClick={() => alert.habitationId && handleRowClick(alert.habitationId)}
                    className="hover:bg-surface-hover text-text-secondary cursor-pointer transition-colors"
                  >
                    <td className="py-1.5 px-3 tabular-nums text-text-muted whitespace-nowrap">
                      {new Date(alert.timestamp).toLocaleString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-1.5 px-3">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider ${
                          alert.severity === 'CRITICAL'
                            ? 'text-gis-red'
                            : alert.severity === 'HIGH'
                            ? 'text-gis-orange'
                            : alert.severity === 'WATCH'
                            ? 'text-gis-yellow'
                            : 'text-gis-green'
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </td>
                    <td className="py-1.5 px-3 font-medium text-text-primary">{alert.type}</td>
                    <td className="py-1.5 px-3 text-text-primary">{alert.message}</td>
                    <td className="py-1.5 px-3 text-center">
                      {alert.habitationId && (
                        <span className="text-[10px] text-gis-blue hover:underline">Focus Map →</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* =================================================================
              TAB 3: TIMELINE (Risk Trajectory)
             ================================================================= */}
          {activeTab === 'timeline' && (
            <div className="p-3">
              <div className="text-[10px] uppercase tracking-wider text-text-muted mb-2">
                Multi-Year Composite Risk Trajectory (2022 - 2026) • High Priority Habitations
              </div>
              <table className="w-full text-left border-collapse text-[11px]">
                <thead className="bg-panel-header text-text-muted uppercase text-[10px] tracking-wider border-b border-border-default">
                  <tr>
                    <th className="py-1.5 px-3">Habitation</th>
                    <th className="py-1.5 px-3">District</th>
                    <th className="py-1.5 px-3 text-right">2022</th>
                    <th className="py-1.5 px-3 text-right">2023</th>
                    <th className="py-1.5 px-3 text-right">2024</th>
                    <th className="py-1.5 px-3 text-right">2025</th>
                    <th className="py-1.5 px-3 text-right">2026 (Now)</th>
                    <th className="py-1.5 px-3 text-right">5-Year Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {habitations
                    .filter((h) => h.riskScore >= 70)
                    .map((h) => {
                      const first = h.riskHistory[0]?.score ?? h.riskScore;
                      const current = h.riskHistory[h.riskHistory.length - 1]?.score ?? h.riskScore;
                      const delta = current - first;

                      return (
                        <tr
                          key={h.id}
                          onClick={() => handleRowClick(h.id)}
                          className="hover:bg-surface-hover cursor-pointer"
                        >
                          <td className="py-1.5 px-3 font-semibold text-text-primary">{h.name}</td>
                          <td className="py-1.5 px-3 text-text-secondary">{h.district}</td>
                          {h.riskHistory.map((rh) => (
                            <td key={rh.year} className="py-1.5 px-3 text-right tabular-nums text-text-secondary">
                              {rh.score}
                            </td>
                          ))}
                          <td className="py-1.5 px-3 text-right tabular-nums font-bold text-gis-red">
                            +{delta}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          )}

          {/* =================================================================
              TAB 4: SENSORS & DATA QUALITY
             ================================================================= */}
          {activeTab === 'quality' && (
            <div className="p-3 grid grid-cols-3 gap-3 text-[11px]">
              <div className="bg-panel-header p-2.5 rounded-[2px] border border-border-default space-y-1">
                <div className="text-[10px] text-text-muted uppercase font-bold">INSAR INTERFEROMETRY</div>
                <div className="text-text-primary">Sentinel-1 Ascending / Descending Pass</div>
                <div className="text-gis-green">Ground Subsidence Active: Joshimath Sector (4.2mm/mo)</div>
                <div className="text-[10px] text-text-muted">Last Orbit Pass: 2026-09-27 18:30 UTC</div>
              </div>
              <div className="bg-panel-header p-2.5 rounded-[2px] border border-border-default space-y-1">
                <div className="text-[10px] text-text-muted uppercase font-bold">IMD DOPPLER RADAR FEED</div>
                <div className="text-text-primary">Dehradun / Mukteshwar Radar Station</div>
                <div className="text-gis-orange">Precipitation Warning: 65mm/24hr Forecast</div>
                <div className="text-[10px] text-text-muted">Radar Refresh: Every 15 min</div>
              </div>
              <div className="bg-panel-header p-2.5 rounded-[2px] border border-border-default space-y-1">
                <div className="text-[10px] text-text-muted uppercase font-bold">BHUVAN DIGITAL ELEVATION MODEL</div>
                <div className="text-text-primary">Cartosat-1 10m Stereo DEM</div>
                <div className="text-gis-green">Slope Stability & Flow Direction Models Configured</div>
                <div className="text-[10px] text-text-muted">Vertical Accuracy: ±1.8m</div>

              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
