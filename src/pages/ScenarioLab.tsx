import { useNavigate } from 'react-router-dom';
import { Sliders, ArrowUpRight, Play, RotateCcw, AlertTriangle } from 'lucide-react';

export function ScenarioLab() {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              MULTI-HAZARD SCENARIO LAB // WHAT-IF SIMULATION
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gis-yellow/10 border border-gis-yellow/30 text-gis-yellow rounded-[2px] font-bold">
              MONTE CARLO PROJECTION MATRIX
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Parametric simulation of cascading extreme weather impacts on slope failure and carrying capacity thresholds.
          </p>
        </div>

        <button
          onClick={() => navigate('/')}
          className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
        >
          <span>VIEW BASELINE MAP</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-12 gap-3 mt-3 flex-1 overflow-hidden">
        {/* Left Column: Parameter controls */}
        <div className="col-span-5 bg-panel-bg border border-border-default rounded-[2px] p-3 flex flex-col font-mono text-xs overflow-y-auto">
          <div className="text-[10px] uppercase text-text-muted font-bold pb-2 border-b border-border-subtle">
            SIMULATION PARAMETERS
          </div>

          <div className="space-y-4 py-3 flex-1">
            {/* 1. Precipitation */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">24-Hour Precipitation Pulse</span>
                <span className="text-gis-red font-bold">120 mm/day (+65%)</span>
              </div>
              <input
                type="range"
                defaultValue={65}
                className="w-full h-1 bg-border-default rounded-[1px] accent-gis-red"
              />
              <span className="text-[9px] text-text-muted">Cloudburst recurrence threshold exceeded</span>
            </div>

            {/* 2. Slope Saturation Index */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">Soil Pore Water Pressure</span>
                <span className="text-gis-orange font-bold">88 kPa (Critical)</span>
              </div>
              <input
                type="range"
                defaultValue={88}
                className="w-full h-1 bg-border-default rounded-[1px] accent-gis-orange"
              />
              <span className="text-[9px] text-text-muted">Factor of Safety (FoS) drops below 1.05</span>
            </div>

            {/* 3. Seismic Peak Ground Acceleration (PGA) */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">Peak Ground Acceleration (PGA)</span>
                <span className="text-text-primary font-bold">0.36g (Zone V)</span>
              </div>
              <input
                type="range"
                defaultValue={36}
                className="w-full h-1 bg-border-default rounded-[1px] accent-gis-yellow"
              />
              <span className="text-[9px] text-text-muted">Bureau of Indian Standards seismic coefficient</span>
            </div>

            {/* 4. Evacuation Road Blockage Probability */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">Corridor Cut-off Likelihood</span>
                <span className="text-gis-red font-bold">78% (NH-7 / Helang)</span>
              </div>
              <input
                type="range"
                defaultValue={78}
                className="w-full h-1 bg-border-default rounded-[1px] accent-gis-red"
              />
              <span className="text-[9px] text-text-muted">Bridge INF-010 structural failure risk</span>
            </div>
          </div>

          <div className="pt-2 border-t border-border-subtle flex gap-2">
            <button className="flex-1 py-1.5 bg-gis-blue/15 hover:bg-gis-blue/25 border border-gis-blue/40 text-gis-blue rounded-[2px] font-mono text-[11px] font-bold flex items-center justify-center gap-1.5 transition-colors">
              <Play className="w-3 h-3" />
              <span>EXECUTE SCENARIO ITERATION</span>
            </button>
            <button className="px-2.5 py-1.5 bg-panel-header hover:bg-surface-hover border border-border-default text-text-muted hover:text-text-primary rounded-[2px] transition-colors">
              <RotateCcw className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Right Column: Comparative Cascade Output */}
        <div className="col-span-7 bg-panel-bg border border-border-default rounded-[2px] p-3 flex flex-col font-mono text-xs overflow-y-auto">
          <div className="text-[10px] uppercase text-text-muted font-bold pb-2 border-b border-border-subtle flex justify-between items-center">
            <span>CASCADING IMPACT MATRIX [SCENARIO RUN #104]</span>
            <span className="text-gis-red">● SEVERE IMPACT DETECTED</span>
          </div>

          <div className="grid grid-cols-3 gap-2 py-3">
            <div className="bg-panel-header p-2 border border-border-subtle rounded-[2px]">
              <div className="text-[9px] text-text-muted">NEW HABITATIONS COMPROMISED</div>
              <div className="text-xl font-bold text-gis-red mt-1">+4</div>
              <div className="text-[9px] text-text-muted">Urgam Valley & Tharali escalate</div>
            </div>
            <div className="bg-panel-header p-2 border border-border-subtle rounded-[2px]">
              <div className="text-[9px] text-text-muted">ADDITIONAL EXPOSED POPULATION</div>
              <div className="text-xl font-bold text-text-primary mt-1">+7,642</div>
              <div className="text-[9px] text-text-muted">Total exposed rises to 45,061</div>
            </div>
            <div className="bg-panel-header p-2 border border-border-subtle rounded-[2px]">
              <div className="text-[9px] text-text-muted">RELOCATION DEFICIT</div>
              <div className="text-xl font-bold text-gis-yellow mt-1">2,800 Cap.</div>
              <div className="text-[9px] text-text-muted">Pipalkoti site capacity overwhelmed</div>
            </div>
          </div>

          <div className="flex-1 border-t border-border-subtle pt-2 space-y-2">
            <div className="text-[10px] uppercase text-text-muted">Recommended Mitigation Strategy</div>
            <div className="p-2.5 bg-panel-header rounded-[2px] border border-border-subtle text-[11px] leading-relaxed text-text-secondary space-y-1">
              <p className="text-text-primary font-bold">1. Phase-1 Preemptive Evacuation:</p>
              <p>Immediately trigger staged relocation of Khar Village (HAB-001) households to Pipalkoti Plateau (RS-001) prior to 48-hour rainfall surge.</p>
              <p className="text-text-primary font-bold mt-2">2. Alternate Logistics Routing:</p>
              <p>Reroute heavy disaster-relief vehicles via Rudraprayag Terrace bypass (RS-004) to avoid Helang Bridge choke point.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
