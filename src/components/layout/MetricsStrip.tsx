import { useEffect, useState } from 'react';
import { api, type MetricsSummary } from '../../lib/api';
import { useAppStore } from '../../state/AppContext';

export function MetricsStrip() {
  const { selectedDistrict } = useAppStore();
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    api.getMetricsSummary().then((res) => {
      if (mounted) {
        setMetrics(res.data);
        setIsLive(res.isLive);
        setLoading(false);
      }
    }).catch(() => {
      if (mounted) setLoading(false);
    });
    return () => {
      mounted = false;
    };
  }, [selectedDistrict]);

  const totalHabitations = metrics?.total_habitations ?? 13;
  const totalRedZones = metrics?.active_red_zones ?? 4;
  const totalExposedPop = metrics?.total_population_at_risk ?? 4250;
  const immediateReloc = metrics?.critical_habitations ?? 3;
  const totalCandidateSites = metrics?.candidate_sites ?? 8;
  const pendingRelocations = metrics?.pending_relocations ?? 9;

  return (
    <div className="h-7 bg-panel-header border-b border-border-default px-3 flex items-center justify-between text-[11px] font-mono tracking-wider text-text-muted select-none shrink-0 overflow-x-auto">
      <div className="flex items-center gap-3 whitespace-nowrap">
        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-text-primary tabular-nums">
            {loading ? '...' : totalHabitations}
          </span>
          <span className="text-[10px] uppercase text-text-secondary">Habitations Monitored</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-gis-red tabular-nums">
            {loading ? '...' : totalRedZones}
          </span>
          <span className="text-[10px] uppercase text-text-secondary">Red Zones Active</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-text-primary tabular-nums">
            {loading ? '...' : totalExposedPop.toLocaleString()}
          </span>
          <span className="text-[10px] uppercase text-text-secondary">Population Exposed</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-gis-red tabular-nums">
            {loading ? '...' : immediateReloc}
          </span>
          <span className="text-[10px] uppercase text-text-secondary">Critical Habitations</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-text-primary tabular-nums">
            {loading ? '...' : totalCandidateSites}
          </span>
          <span className="text-[10px] uppercase text-text-secondary">Candidate Sites</span>
        </div>

        <span className="text-border-active">·</span>

        <div className="flex items-baseline gap-1.5">
          <span className="font-bold text-gis-yellow tabular-nums">
            {loading ? '...' : pendingRelocations}
          </span>
          <span className="text-[10px] uppercase text-text-secondary">Pending Allocation</span>
        </div>
      </div>

      <div className="hidden lg:flex items-center gap-3 text-[10px] text-text-muted shrink-0">
        <span className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isLive ? 'bg-gis-green animate-pulse' : 'bg-gis-yellow'
            }`}
          />
          <span
            className={`font-semibold tracking-wider px-1 py-0.2 rounded-[2px] border ${
              isLive
                ? 'text-gis-green border-gis-green/40 bg-gis-green/10'
                : 'text-gis-yellow border-gis-yellow/40 bg-gis-yellow/10'
            }`}
          >
            {isLive ? 'LIVE' : 'DEMO'}
          </span>
        </span>
        <span>•</span>
        <span>AOI: {selectedDistrict.toUpperCase()} CATCHMENT</span>
        <span>•</span>
        <span>ELEV: 610m - 2,680m</span>
      </div>
    </div>
  );
}
