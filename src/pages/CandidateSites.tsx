import { useNavigate } from 'react-router-dom';
import { candidateSites } from '../data/mockData';
import { ArrowUpRight, CheckCircle2, XCircle } from 'lucide-react';

export function CandidateSites() {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              CANDIDATE RELOCATION SITES INVENTORY
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gis-green/10 border border-gis-green/30 text-gis-green rounded-[2px] font-bold">
              {candidateSites.length} IDENTIFIED PARCELS
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Suitability analysis, carrying capacity calculations, and infrastructure readiness audit.
          </p>
        </div>

        <button
          onClick={() => navigate('/')}
          className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
        >
          <span>VIEW POLYGONS ON MAP</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto mt-3 border border-border-default rounded-[2px] bg-panel-bg">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead className="sticky top-0 bg-panel-header text-[10px] uppercase tracking-wider text-text-muted border-b border-border-default z-10">
            <tr>
              <th className="py-2 px-3">Site ID</th>
              <th className="py-2 px-3">Site Designation</th>
              <th className="py-2 px-3">District</th>
              <th className="py-2 px-3 text-right">Suitability Score</th>
              <th className="py-2 px-3 text-right">Carrying Capacity</th>
              <th className="py-2 px-3 text-right">Area (Ha)</th>
              <th className="py-2 px-3 text-right">Elevation</th>
              <th className="py-2 px-3 text-right">Hazard Buffer</th>
              <th className="py-2 px-3">Utilities (Road / Water / Grid)</th>
              <th className="py-2 px-3">Land Ownership</th>
              <th className="py-2 px-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-[11px]">
            {candidateSites.map((site) => (
              <tr key={site.id} className="hover:bg-surface-hover text-text-secondary transition-colors">
                <td className="py-2 px-3 text-text-muted font-bold">{site.id}</td>
                <td className="py-2 px-3 font-semibold text-text-primary">{site.name}</td>
                <td className="py-2 px-3 text-text-muted">{site.district}</td>
                <td className="py-2 px-3 text-right font-bold tabular-nums text-gis-green">
                  {site.suitabilityScore}/100
                </td>
                <td className="py-2 px-3 text-right tabular-nums text-text-primary font-bold">
                  {site.carryingCapacity.toLocaleString()}
                </td>
                <td className="py-2 px-3 text-right tabular-nums">{site.areaHectares}</td>
                <td className="py-2 px-3 text-right tabular-nums">{site.elevation}m</td>
                <td className="py-2 px-3 text-right tabular-nums">{site.distanceFromHazard} km</td>
                <td className="py-2 px-3">
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className={site.roadAccess ? 'text-gis-green font-bold' : 'text-text-muted'}>
                      ROAD {site.roadAccess ? '✓' : '✗'}
                    </span>
                    <span>•</span>
                    <span className={site.waterAccess ? 'text-gis-green font-bold' : 'text-text-muted'}>
                      H2O {site.waterAccess ? '✓' : '✗'}
                    </span>
                    <span>•</span>
                    <span className={site.electricityAccess ? 'text-gis-green font-bold' : 'text-text-muted'}>
                      GRID {site.electricityAccess ? '✓' : '✗'}
                    </span>
                  </div>
                </td>
                <td className="py-2 px-3 text-text-muted">{site.ownership}</td>
                <td className="py-2 px-3 text-center">
                  <span
                    className={`text-[10px] font-semibold uppercase ${
                      site.verificationStatus === 'VERIFIED'
                        ? 'text-gis-green'
                        : site.verificationStatus === 'IN_PROGRESS'
                        ? 'text-gis-blue'
                        : 'text-text-muted'
                    }`}
                  >
                    {site.verificationStatus}
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
