import { habitations, redZones, relocationPriorities, candidateSites } from '../../data/mockData';

export function MetricsStrip() {
  const totalHabitations = habitations.length;
  const totalRedZones = redZones.length;
  const totalExposedPop = habitations.reduce((acc, h) => acc + h.population, 0);
  const immediateReloc = relocationPriorities.filter((p) => p.urgency === 'IMMEDIATE').length;
  const totalCandidateSites = candidateSites.length;
  const verifiedCount = candidateSites.filter((s) => s.verificationStatus === 'VERIFIED').length;
  const verifiedPercentage = Math.round((verifiedCount / totalCandidateSites) * 100);

  return (
    <div className="h-7 bg-panel-header border-b border-border-default px-3 flex items-center justify-between text-[11px] font-mono tracking-wider text-text-muted select-none shrink-0 overflow-x-auto">
      <div className="flex items-center gap-3 whitespace-nowrap">
        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-text-primary tabular-nums">{totalHabitations}</span>
          <span className="text-[10px] uppercase text-text-secondary">Habitations Monitored</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-gis-red tabular-nums">{totalRedZones}</span>
          <span className="text-[10px] uppercase text-text-secondary">Red Zones Active</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-text-primary tabular-nums">{totalExposedPop.toLocaleString()}</span>
          <span className="text-[10px] uppercase text-text-secondary">Population Exposed</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-gis-red tabular-nums">{immediateReloc}</span>
          <span className="text-[10px] uppercase text-text-secondary">Immediate Relocation</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-text-primary tabular-nums">{totalCandidateSites}</span>
          <span className="text-[10px] uppercase text-text-secondary">Candidate Sites</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-gis-green tabular-nums">{verifiedPercentage}%</span>
          <span className="text-[10px] uppercase text-text-secondary">Ground Verified</span>
        </div>
      </div>

      <div className="hidden lg:flex items-center gap-3 text-[10px] text-text-muted">
        <span>AOI: CHAMOLI CATCHMENT</span>
        <span>•</span>
        <span>ELEV: 610m - 2,680m</span>
      </div>
    </div>
  );
}
