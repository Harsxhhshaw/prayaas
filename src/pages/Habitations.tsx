import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Download, ArrowUpRight } from 'lucide-react';
import { habitations } from '../data/mockData';
import type { UrgencyLevel } from '../types';

export function Habitations() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [urgencyFilter, setUrgencyFilter] = useState<string>('ALL');

  const filtered = habitations.filter((h) => {
    const matchesSearch =
      h.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      h.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      h.district.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesUrgency = urgencyFilter === 'ALL' || h.urgency === urgencyFilter;
    return matchesSearch && matchesUrgency;
  });

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              HABITATIONS REGISTRY // CHAMOLI STUDY AREA
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-panel-header border border-border-default text-text-muted rounded-[2px]">
              {filtered.length} ENTRIES
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Geospatial multi-hazard risk assessment and demographic exposure database.
          </p>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <div className="flex items-center bg-panel-header border border-border-default px-2 py-1 rounded-[2px]">
            <Search className="w-3.5 h-3.5 text-text-muted mr-1.5" />
            <input
              type="text"
              placeholder="FILTER BY NAME / ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-transparent text-[11px] text-text-primary placeholder:text-text-muted focus:outline-none w-44"
            />
          </div>

          <select
            value={urgencyFilter}
            onChange={(e) => setUrgencyFilter(e.target.value)}
            className="bg-panel-header border border-border-default text-[11px] px-2 py-1 rounded-[2px] text-text-secondary focus:outline-none"
          >
            <option value="ALL">ALL URGENCIES</option>
            <option value="IMMEDIATE">IMMEDIATE</option>
            <option value="SHORT_TERM">SHORT-TERM</option>
            <option value="MEDIUM_TERM">MEDIUM-TERM</option>
          </select>

          <button
            onClick={() => navigate('/')}
            className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] text-text-primary transition-colors flex items-center gap-1.5"
          >
            <span>MAP VIEW</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Dense Data Grid */}
      <div className="flex-1 overflow-auto mt-3 border border-border-default rounded-[2px] bg-panel-bg">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead className="sticky top-0 bg-panel-header text-[10px] uppercase tracking-wider text-text-muted border-b border-border-default z-10">
            <tr>
              <th className="py-2 px-3">ID</th>
              <th className="py-2 px-3">Habitation</th>
              <th className="py-2 px-3">District</th>
              <th className="py-2 px-3 text-right">Composite Risk</th>
              <th className="py-2 px-3">Primary Hazards</th>
              <th className="py-2 px-3">Urgency Status</th>
              <th className="py-2 px-3 text-right">Population</th>
              <th className="py-2 px-3 text-right">Elevation</th>
              <th className="py-2 px-3 text-right">Road Distance</th>
              <th className="py-2 px-3 text-center">Ground Verification</th>
              <th className="py-2 px-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-[11px]">
            {filtered.map((hab) => {
              const isCritical = hab.riskScore >= 80;
              return (
                <tr
                  key={hab.id}
                  className="hover:bg-surface-hover transition-colors text-text-secondary"
                >
                  <td className="py-2 px-3 text-text-muted">{hab.id}</td>
                  <td className="py-2 px-3 font-semibold text-text-primary">{hab.name}</td>
                  <td className="py-2 px-3 text-text-muted">{hab.district}</td>
                  <td className="py-2 px-3 text-right font-bold tabular-nums">
                    <span
                      className={
                        isCritical
                          ? 'text-gis-red'
                          : hab.riskScore >= 60
                          ? 'text-gis-orange'
                          : 'text-gis-yellow'
                      }
                    >
                      {hab.riskScore}
                    </span>
                    <span className="text-[9px] text-text-muted font-normal ml-0.5">/100</span>
                  </td>
                  <td className="py-2 px-3 text-[10px]">
                    <div className="flex gap-1">
                      {hab.hazardScores.slice(0, 2).map((hz) => (
                        <span
                          key={hz.type}
                          className="px-1.5 py-0.5 bg-panel-header border border-border-subtle rounded-[1px] text-text-muted"
                        >
                          {hz.label}: {hz.score}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider ${
                        hab.urgency === 'IMMEDIATE'
                          ? 'text-gis-red'
                          : hab.urgency === 'SHORT_TERM'
                          ? 'text-gis-orange'
                          : 'text-gis-yellow'
                      }`}
                    >
                      {hab.urgency.replace('_', '-')}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-text-primary">
                    {hab.population.toLocaleString()}
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums">{hab.elevation}m</td>
                  <td className="py-2 px-3 text-right tabular-nums">{hab.nearestRoad}km</td>
                  <td className="py-2 px-3 text-center">
                    <span
                      className={`text-[10px] uppercase font-semibold ${
                        hab.verificationStatus === 'VERIFIED'
                          ? 'text-gis-green'
                          : hab.verificationStatus === 'FLAGGED'
                          ? 'text-gis-red'
                          : 'text-text-muted'
                      }`}
                    >
                      {hab.verificationStatus}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <button
                      onClick={() => navigate('/')}
                      className="text-[10px] text-gis-blue hover:underline"
                    >
                      Inspect in Map →
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
