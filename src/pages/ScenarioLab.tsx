import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sliders,
  ArrowUpRight,
  Play,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Layers,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import { useAppStore } from '../state/AppContext';
import { api } from '../lib/api';
import type { RelocationPlanItem, DigitalTwinSimulationResponse, ScenarioParameters } from '../types';
import rainiSnapshot from '../data/raini-snapshot.json';
import { DataModeBadge } from '../components/ui/DataModeBadge';

export function ScenarioLab() {
  const navigate = useNavigate();
  const { habitations, selectedHabitationId, selectHabitation } = useAppStore();

  const [activeHabId, setActiveHabId] = useState<string>(selectedHabitationId || 'HAB-002');
  const [plans, setPlans] = useState<RelocationPlanItem[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string>('');
  const [isLive, setIsLive] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<DigitalTwinSimulationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Simulation Parametric Sliders
  const [popChangePct, setPopChangePct] = useState<number>(0);
  const [waterChangePct, setWaterChangePct] = useState<number>(0);
  const [roadUnavailable, setRoadUnavailable] = useState<boolean>(false);
  const [topSiteFailed, setTopSiteFailed] = useState<boolean>(false);
  const [waterUpgradeCapacity, setWaterUpgradeCapacity] = useState<number>(0);
  const [healthUpgradeCapacity, setHealthUpgradeCapacity] = useState<number>(0);

  // Load plans
  useEffect(() => {
    let mounted = true;
    api.getRelocationOptimizationRuns(activeHabId).then((res) => {
      if (!mounted) return;
      if (res.data && res.data.length > 0) {
        setPlans(res.data);
        setSelectedPlanId(res.data[0].id || 'PLAN-1');
        setIsLive(res.isLive);
      } else {
        const fallbackPlans: RelocationPlanItem[] = rainiSnapshot.optimization_alternatives.map((alt, idx) => ({
          id: `PLAN-FROZEN-${idx + 1}`,
          plan_name: alt.name,
          strategy_type: alt.strategy,
          allocated_population: alt.allocated_population,
          unallocated_population: alt.unallocated_population,
          allocation_ratio: 1.0,
          site_count: alt.site_count,
          average_distance_km: alt.avg_distance_km,
          max_distance_km: alt.avg_distance_km * 1.2,
          capacity_utilization_percent: alt.capacity_utilization_pct,
          relative_infrastructure_burden: 45.0,
          community_fragmentation: 'NONE',
          livelihood_disruption: 'MODERATE',
          environmental_pressure: 10.0,
          evidence_confidence: 68.0,
          assumption_dependence: 'EXPLORATORY',
          explanation: 'Frozen baseline plan alternative',
          binding_constraints: [],
          allocations: alt.candidate_ids.map((cid) => ({
            candidate_type: 'PARCEL',
            candidate_id: cid,
            allocated_population: Math.floor(alt.allocated_population / alt.site_count),
            usable_capacity: 1500,
            capacity_utilization_pct: alt.capacity_utilization_pct,
            distance_km: alt.avg_distance_km,
            evidence_status: 'MODELED',
          })),
        }));
        setPlans(fallbackPlans);
        setSelectedPlanId(fallbackPlans[0].id || 'PLAN-FROZEN-1');
        setIsLive(false);
      }
    });

    return () => {
      mounted = false;
    };
  }, [activeHabId]);

  const handleResetSliders = () => {
    setPopChangePct(0);
    setWaterChangePct(0);
    setRoadUnavailable(false);
    setTopSiteFailed(false);
    setWaterUpgradeCapacity(0);
    setHealthUpgradeCapacity(0);
    setSimulationResult(null);
  };

  const handleRunSimulation = async () => {
    if (!selectedPlanId) return;
    setIsRunning(true);
    setErrorMessage(null);

    const activePlan = plans.find((p) => p.id === selectedPlanId) || plans[0];
    const topSiteId = activePlan?.allocations?.[0]?.candidate_id;

    const params: ScenarioParameters = {
      population_change_pct: popChangePct,
      water_supply_change_pct: waterChangePct,
      road_unavailable: roadUnavailable,
      unavailable_candidate_ids: topSiteFailed && topSiteId ? [topSiteId] : [],
      water_upgrade_capacity: waterUpgradeCapacity,
      health_upgrade_capacity: healthUpgradeCapacity,
    };

    try {
      if (isLive) {
        const res = await api.runDigitalTwinSimulation(selectedPlanId, {
          scenario_name: 'CUSTOM_SIMULATION',
          parameters: params,
        });
        setSimulationResult(res.data);
      } else {
        // Deterministic simulation logic
        const baselinePop = activePlan?.allocated_population || 1256;
        const adjustedPop = Math.round(baselinePop * (1 + popChangePct / 100));

        let feasibility: 'PASS' | 'DEGRADED' | 'FAIL' | 'UNKNOWN' = 'UNKNOWN';
        let bottleneck: string | null = null;
        let summary = 'Deterministic stress test evaluation complete.';

        if (topSiteFailed) {
          feasibility = 'FAIL';
          bottleneck = 'HOUSING';
          summary = `Critical reception parcel ${topSiteId} outage leaves ${adjustedPop} persons unhoused.`;
        } else if (roadUnavailable) {
          feasibility = 'FAIL';
          bottleneck = 'TRANSPORT';
          summary = 'Primary arterial corridor severed; reception site is completely cut off from emergency supply.';
        } else if (waterChangePct <= -20 && waterUpgradeCapacity < 150) {
          feasibility = 'FAIL';
          bottleneck = 'WATER';
          summary = `Water supply deficit: dry-season yield reduced by ${Math.abs(waterChangePct)}%, utilization exceeds 100%.`;
        } else if (popChangePct > 20) {
          feasibility = 'DEGRADED';
          bottleneck = 'HOUSING';
          summary = `Population surge (+${popChangePct}%) operates at high capacity margin without secondary reserve.`;
        } else {
          feasibility = 'UNKNOWN';
          bottleneck = null;
          summary = 'Known dimensions feasible; critical sanitation and health capacities unmeasured (marked UNKNOWN).';
        }

        setSimulationResult({
          plan_id: selectedPlanId,
          scenario_name: 'CUSTOM_SIMULATION',
          parameters: params,
          destinations: activePlan.allocations.map((alloc) => ({
            candidate_id: alloc.candidate_id,
            candidate_type: alloc.candidate_type,
            allocated_population: topSiteFailed && alloc.candidate_id === topSiteId ? 0 : alloc.allocated_population,
            distance_km: alloc.distance_km,
            overall_status: topSiteFailed && alloc.candidate_id === topSiteId ? 'EXCEEDED' : 'OK',
            bottleneck_dimension: bottleneck,
            dimensions: [
              {
                dimension: 'HOUSING',
                allocated_load: adjustedPop,
                capacity: 1500,
                utilization_pct: (adjustedPop / 1500) * 100,
                status: topSiteFailed ? 'EXCEEDED' : 'OK',
                evidence_status: 'MODELED',
                notes: 'Capacity modeled from 2.0 ha parcel slope footprint.',
              },
              {
                dimension: 'WATER',
                allocated_load: adjustedPop * 55,
                capacity: 82500 * (1 + waterChangePct / 100) + waterUpgradeCapacity * 55,
                utilization_pct: ((adjustedPop * 55) / (82500 * (1 + waterChangePct / 100) + waterUpgradeCapacity * 55)) * 100,
                status: waterChangePct <= -20 && waterUpgradeCapacity < 150 ? 'EXCEEDED' : 'OK',
                evidence_status: 'PLANNING_ASSUMPTION',
                notes: 'JJM standard 55 lpcd benchmark.',
              },
              {
                dimension: 'SANITATION',
                allocated_load: adjustedPop,
                capacity: null,
                utilization_pct: null,
                status: 'UNKNOWN',
                evidence_status: 'UNKNOWN',
                notes: 'No percolation test or DEWATS telemetry recorded.',
              },
            ],
          })),
          total_allocated: topSiteFailed ? 0 : adjustedPop,
          total_unallocated: topSiteFailed ? adjustedPop : 0,
          overall_plan_feasibility: feasibility,
          limiting_bottleneck: bottleneck,
          reoptimization_recommended: feasibility === 'FAIL',
          summary,
        });
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Simulation execution failed');
    } finally {
      setIsRunning(false);
    }
  };

  const selectedPlan = plans.find((p) => p.id === selectedPlanId) || plans[0];

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              MULTI-HAZARD SCENARIO LAB // WHAT-IF SIMULATOR
            </h1>
            <DataModeBadge mode={isLive ? 'LIVE' : 'DEMO SNAPSHOT'} />
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-panel-header border border-border-default text-text-muted rounded-[2px]">
              DETERMINISTIC SIMULATION
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Parametric stress testing of carrying capacity thresholds, arterial outages, and candidate parcel failures.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/digital-twin')}
            className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
          >
            <span>DIGITAL TWIN OVERVIEW</span>
            <Layers className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="mt-2 p-2 bg-rose-950/60 border border-rose-500/40 rounded text-xs font-mono text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-3 mt-3 flex-1 overflow-hidden font-mono">
        {/* Left Column: Parametric Sliders (5 cols) */}
        <div className="col-span-5 bg-panel-bg border border-border-default rounded-[2px] p-3 flex flex-col text-xs overflow-y-auto">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <span className="text-[10px] uppercase text-text-muted font-bold">
              SCENARIO PARAMETER CONTROLS
            </span>
            <button
              onClick={handleResetSliders}
              className="text-[10px] text-text-muted hover:text-text-primary flex items-center gap-1"
              title="Reset all sliders to baseline"
            >
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          </div>

          {/* Plan Selector */}
          <div className="py-2.5 border-b border-border-subtle">
            <label className="text-[10px] text-text-muted uppercase block mb-1">EVALUATED RELOCATION PLAN:</label>
            <select
              value={selectedPlanId}
              onChange={(e) => setSelectedPlanId(e.target.value)}
              className="w-full bg-panel-header border border-border-default rounded px-2 py-1 text-xs text-text-primary focus:border-gis-blue focus:outline-none"
            >
              {plans.map((p, idx) => (
                <option key={p.id || idx} value={p.id || `PLAN-${idx}`}>
                  {p.plan_name} ({p.strategy_type})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-4 py-3 flex-1 overflow-y-auto">
            {/* 1. Population Change */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">Displaced Population Surge</span>
                <span className={`font-bold ${popChangePct > 0 ? 'text-gis-orange' : 'text-text-primary'}`}>
                  {popChangePct > 0 ? `+${popChangePct}%` : `${popChangePct}%`}
                </span>
              </div>
              <input
                type="range"
                min="-50"
                max="50"
                step="5"
                value={popChangePct}
                onChange={(e) => setPopChangePct(Number(e.target.value))}
                className="w-full h-1 bg-border-default rounded accent-gis-blue"
              />
              <span className="text-[9px] text-text-muted block mt-0.5">
                Simulates influx of additional displaced households from adjacent red zones.
              </span>
            </div>

            {/* 2. Water Yield Multiplier */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">Water Supply Yield Deviation</span>
                <span className={`font-bold ${waterChangePct < 0 ? 'text-gis-red' : 'text-text-primary'}`}>
                  {waterChangePct > 0 ? `+${waterChangePct}%` : `${waterChangePct}%`}
                </span>
              </div>
              <input
                type="range"
                min="-50"
                max="30"
                step="5"
                value={waterChangePct}
                onChange={(e) => setWaterChangePct(Number(e.target.value))}
                className="w-full h-1 bg-border-default rounded accent-gis-blue"
              />
              <span className="text-[9px] text-text-muted block mt-0.5">
                Simulates seasonal monsoon drop or drought stress on local gravity spring feeders.
              </span>
            </div>

            {/* 3. Road Network Cut-off Toggle */}
            <div className="p-2 rounded border border-border-subtle bg-panel-header/40 flex items-center justify-between">
              <div>
                <span className="text-text-primary font-bold block text-[11px]">Sever NH-7 Arterial Road</span>
                <span className="text-[9px] text-text-muted block">Simulates landslide severance at Helang bridge corridor.</span>
              </div>
              <input
                type="checkbox"
                checked={roadUnavailable}
                onChange={(e) => setRoadUnavailable(e.target.checked)}
                className="w-4 h-4 accent-gis-red"
              />
            </div>

            {/* 4. Top Reception Parcel Outage */}
            <div className="p-2 rounded border border-border-subtle bg-panel-header/40 flex items-center justify-between">
              <div>
                <span className="text-text-primary font-bold block text-[11px]">Top Candidate Parcel Failure</span>
                <span className="text-[9px] text-text-muted block">Simulates sudden geotechnical disqualification of primary parcel.</span>
              </div>
              <input
                type="checkbox"
                checked={topSiteFailed}
                onChange={(e) => setTopSiteFailed(e.target.checked)}
                className="w-4 h-4 accent-gis-red"
              />
            </div>

            {/* 5. Infrastructure Augmentation */}
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-text-secondary">Targeted Water Augmentation</span>
                <span className="font-bold text-gis-green">+{waterUpgradeCapacity} pers. eq.</span>
              </div>
              <input
                type="range"
                min="0"
                max="500"
                step="50"
                value={waterUpgradeCapacity}
                onChange={(e) => setWaterUpgradeCapacity(Number(e.target.value))}
                className="w-full h-1 bg-border-default rounded accent-gis-green"
              />
              <span className="text-[9px] text-text-muted block mt-0.5">
                Simulates state Jal Sansthan pipeline capacity expansion intervention.
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-border-subtle">
            <button
              onClick={handleRunSimulation}
              disabled={isRunning}
              className="w-full py-2 bg-gis-blue hover:bg-gis-blue/80 text-black font-bold rounded text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
              <span>{isRunning ? 'SIMULATING TWIN...' : 'RUN STRESS SIMULATION'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Simulation Outcomes & Feasibility (7 cols) */}
        <div className="col-span-7 bg-panel-bg border border-border-default rounded-[2px] p-3 flex flex-col text-xs overflow-hidden">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle shrink-0">
            <span className="text-[10px] uppercase text-text-muted font-bold">
              SIMULATION RESULTS // IMPACT ON CARRYING CAPACITY
            </span>
            {simulationResult && (
              <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                simulationResult.overall_plan_feasibility === 'PASS'
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                  : simulationResult.overall_plan_feasibility === 'FAIL'
                  ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                  : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
              }`}>
                STATUS: {simulationResult.overall_plan_feasibility}
              </span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto py-2 space-y-3">
            {!simulationResult ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-text-muted">
                <Sliders className="w-10 h-10 text-gis-blue/40 mb-2" />
                <p className="font-bold text-text-secondary">No Custom Simulation Run</p>
                <p className="text-[11px] text-text-muted mt-1 max-w-sm">
                  Adjust the stress parameter sliders on the left and click "RUN STRESS SIMULATION" to evaluate reception site bottlenecks.
                </p>
              </div>
            ) : (
              <>
                {/* Executive Feasibility Banner */}
                <div className={`p-3 rounded border ${
                  simulationResult.overall_plan_feasibility === 'PASS'
                    ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
                    : simulationResult.overall_plan_feasibility === 'FAIL'
                    ? 'bg-rose-950/40 border-rose-500/40 text-rose-200'
                    : 'bg-amber-950/40 border-amber-500/40 text-amber-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold flex items-center gap-1.5">
                      {simulationResult.overall_plan_feasibility === 'PASS' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                      {simulationResult.overall_plan_feasibility === 'FAIL' && <XCircle className="w-4 h-4 text-rose-400" />}
                      {simulationResult.overall_plan_feasibility === 'UNKNOWN' && <HelpCircle className="w-4 h-4 text-amber-400" />}
                      FEASIBILITY: {simulationResult.overall_plan_feasibility}
                    </span>
                    {simulationResult.limiting_bottleneck && (
                      <span className="text-[10px] font-bold uppercase bg-rose-900/60 text-rose-300 px-2 py-0.5 rounded border border-rose-600/50">
                        CRITICAL BOTTLENECK: {simulationResult.limiting_bottleneck}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] mt-1.5 text-text-secondary leading-relaxed">
                    {simulationResult.summary}
                  </p>
                  {simulationResult.reoptimization_recommended && (
                    <div className="mt-2 text-[10px] text-rose-300 font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-rose-400" />
                      <span>Plan failed under stress. Recommended action: Trigger Task 8 Multi-Site Reoptimization with relaxed constraints.</span>
                    </div>
                  )}
                </div>

                {/* Destination Load Breakdown */}
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-text-muted uppercase block">
                    RECEPTION SITES CAPACITY BREAKDOWN:
                  </span>
                  {simulationResult.destinations.map((dest, i) => (
                    <div key={i} className="p-3 bg-panel-header rounded border border-border-default space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-text-primary text-xs">{dest.candidate_id}</span>
                        <span className="text-text-secondary text-[11px]">
                          Allocated: {dest.allocated_population.toLocaleString()} persons ({dest.distance_km.toFixed(1)} km)
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-[10px]">
                        {dest.dimensions.map((dim, di) => (
                          <div key={di} className="p-1.5 rounded bg-panel-bg border border-border-subtle">
                            <div className="flex items-center justify-between text-text-muted">
                              <span>{dim.dimension}</span>
                              <span className={`font-bold ${
                                dim.status === 'EXCEEDED' ? 'text-gis-red' : dim.status === 'OK' ? 'text-gis-green' : 'text-slate-400'
                              }`}>
                                {dim.status}
                              </span>
                            </div>
                            {dim.utilization_pct !== null && (
                              <div className="text-text-primary font-bold mt-0.5">
                                {dim.utilization_pct.toFixed(1)}% util
                              </div>
                            )}
                            <div className="text-[9px] text-text-muted truncate mt-0.5" title={dim.notes}>
                              {dim.notes}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
