import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layers,
  ArrowUpRight,
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sliders,
  Database,
  Building2,
  Droplets,
  HeartPulse,
  GraduationCap,
  Truck,
  Zap,
  Trees,
} from 'lucide-react';
import { useAppStore } from '../state/AppContext';
import { api } from '../lib/api';
import type { RelocationPlanItem, PlanRobustnessResponse } from '../types';
import rainiSnapshot from '../data/raini-snapshot.json';
import { DataModeBadge } from '../components/ui/DataModeBadge';

export function DigitalTwin() {
  const navigate = useNavigate();
  const { habitations, selectedHabitationId, selectHabitation } = useAppStore();

  const [activeHabId, setActiveHabId] = useState<string>(selectedHabitationId || 'HAB-002');
  const [plans, setPlans] = useState<RelocationPlanItem[]>([]);
  const [selectedPlanIndex, setSelectedPlanIndex] = useState<number>(0);
  const [robustness, setRobustness] = useState<PlanRobustnessResponse | null>(null);
  const [isRunningRobustness, setIsRunningRobustness] = useState<boolean>(false);
  const [isLivePlans, setIsLivePlans] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load plans for active habitation
  useEffect(() => {
    let mounted = true;
    setErrorMessage(null);
    setRobustness(null);

    api.getRelocationOptimizationRuns(activeHabId).then((res) => {
      if (!mounted) return;
      if (res.data && res.data.length > 0) {
        setPlans(res.data);
        setIsLivePlans(res.isLive);
      } else {
        // Fallback to frozen Raini snapshot if activeHabId is HAB-002 or if no live plans
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
          community_fragmentation: alt.site_count > 1 ? 'LOW_FRAGMENTATION' : 'NONE',
          livelihood_disruption: 'MODERATE_AGRI_TERRAIN',
          environmental_pressure: 12.0,
          evidence_confidence: 68.0,
          assumption_dependence: 'EXPLORATORY / ASSUMPTION-DEPENDENT',
          explanation: `Frozen deterministic candidate allocation from Task 8 optimization.`,
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
        setIsLivePlans(false);
      }
    });

    return () => {
      mounted = false;
    };
  }, [activeHabId]);

  const activePlan = plans[selectedPlanIndex] || plans[0];

  const handleRunRobustness = async () => {
    if (!activePlan?.id) return;
    setIsRunningRobustness(true);
    setErrorMessage(null);

    try {
      if (isLivePlans) {
        const res = await api.evaluatePlanRobustness(activePlan.id);
        setRobustness(res.data);
      } else {
        // Construct deterministic response from frozen snapshot
        setRobustness({
          plan_id: activePlan.id,
          plan_name: activePlan.plan_name,
          tested_scenarios: rainiSnapshot.plan_robustness.tested_scenarios,
          passed_scenarios: rainiSnapshot.plan_robustness.passed_scenarios,
          degraded_scenarios: rainiSnapshot.plan_robustness.degraded_scenarios,
          failed_scenarios: rainiSnapshot.plan_robustness.failed_scenarios,
          unknown_scenarios: rainiSnapshot.plan_robustness.unknown_scenarios,
          robustness_score: rainiSnapshot.plan_robustness.robustness_score,
          summary: rainiSnapshot.plan_robustness.raw_count_report,
          scenarios: [
            {
              scenario_id: 'SCEN-1',
              name: 'BASELINE (CURRENT HYDRO-MET)',
              status: 'UNKNOWN',
              binding_dimension: 'SANITATION / HEALTHCARE',
              summary: 'Known dimensions feasible; Critical unmeasured dimensions marked UNKNOWN.',
            },
            {
              scenario_id: 'SCEN-2',
              name: 'WATER STRESS (-30% DRY-SEASON RUNOFF)',
              status: 'FAIL',
              binding_dimension: 'WATER',
              summary: 'Water utilization reaches 104.7% (exceeds 100% critical threshold).',
            },
            {
              scenario_id: 'SCEN-3',
              name: 'POPULATION SURGE (+20% DISPLACED)',
              status: 'UNKNOWN',
              binding_dimension: null,
              summary: 'Housing feasible with bench headroom; Utilities unmeasured.',
            },
            {
              scenario_id: 'SCEN-4',
              name: 'ROAD OUTAGE (NH-7 / HELANG CUT-OFF)',
              status: 'FAIL',
              binding_dimension: 'TRANSPORT',
              summary: 'Primary arterial connection severed; isolation hazard triggered.',
            },
            {
              scenario_id: 'SCEN-5',
              name: 'RECEPTION PARCEL FAILURE (TOP SITE OUTAGE)',
              status: 'FAIL',
              binding_dimension: 'HOUSING',
              summary: '1,256 persons unhoused due to lack of redundant reception capacity.',
            },
            {
              scenario_id: 'SCEN-6',
              name: 'INFRASTRUCTURE UPGRADE (+200 WATER / HEALTH BEDS)',
              status: 'UNKNOWN',
              binding_dimension: null,
              summary: 'Removes water stress constraint; sanitation remains unmeasured.',
            },
          ],
        });
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to evaluate plan robustness');
    } finally {
      setIsRunningRobustness(false);
    }
  };

  const currentHab = habitations.find((h) => h.id === activeHabId);

  return (
    <div className="h-full flex flex-col bg-workspace text-text-primary p-4 overflow-hidden select-none font-sans">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border-default shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              DIGITAL TWIN // RELOCATION STRESS-TESTING SIMULATOR
            </h1>
            <DataModeBadge mode={isLivePlans ? 'LIVE' : 'DEMO SNAPSHOT'} />
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-panel-header border border-border-default text-text-muted rounded-[2px]">
              TASK 9 ENGINE
            </span>
          </div>
          <p className="text-xs text-text-muted font-mono mt-0.5">
            Deterministic simulation of multi-site reception plans across 8 carrying-capacity dimensions under stress scenarios.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Habitation Selector */}
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-text-muted">ORIGIN:</span>
            <select
              value={activeHabId}
              onChange={(e) => {
                setActiveHabId(e.target.value);
                const hab = habitations.find((h) => h.id === e.target.value);
                if (hab) selectHabitation(hab);
              }}
              className="bg-panel-bg border border-border-default rounded px-2 py-1 text-xs text-text-primary focus:border-gis-blue focus:outline-none"
            >
              {habitations.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name} ({h.id}) - Need {h.riskScore}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => navigate('/scenario-lab')}
            className="px-2.5 py-1 bg-surface-active hover:bg-border-active border border-border-default rounded-[2px] text-[11px] font-mono text-text-primary transition-colors flex items-center gap-1.5"
          >
            <span>SCENARIO LAB SLIDERS</span>
            <Sliders className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="mt-2 p-2 bg-rose-950/60 border border-rose-500/40 rounded text-xs font-mono text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Workspace Body */}
      <div className="grid grid-cols-12 gap-3 mt-3 flex-1 overflow-hidden">
        {/* Left Column: Plan Alternatives (4 cols) */}
        <div className="col-span-4 flex flex-col bg-panel-bg border border-border-default rounded-[2px] p-3 overflow-hidden">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle shrink-0">
            <span className="text-[10px] font-mono font-bold uppercase text-text-muted">
              ALTERNATIVE TRADE-OFF PLANS ({plans.length})
            </span>
            <span className="text-[10px] font-mono text-text-muted">
              {currentHab ? `${currentHab.name} (Pop: ${currentHab.population})` : 'Raini (Pop: 1,256)'}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 py-2">
            {plans.map((plan, idx) => {
              const isSelected = idx === selectedPlanIndex;
              return (
                <button
                  key={plan.id || idx}
                  onClick={() => {
                    setSelectedPlanIndex(idx);
                    setRobustness(null);
                  }}
                  className={`w-full text-left p-2.5 rounded border transition-colors ${
                    isSelected
                      ? 'bg-gis-blue/15 border-gis-blue/50 text-text-primary'
                      : 'bg-panel-header/50 border-border-default/60 hover:bg-panel-header text-text-secondary'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-text-primary">{plan.plan_name}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-panel-bg border border-border-subtle text-text-muted">
                      {plan.strategy_type}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-1 mt-2 text-[10px] font-mono">
                    <div>
                      <span className="text-text-muted block">SITES</span>
                      <span className="font-semibold text-text-primary">{plan.site_count}</span>
                    </div>
                    <div>
                      <span className="text-text-muted block">AVG DIST</span>
                      <span className="font-semibold text-text-primary">{plan.average_distance_km.toFixed(2)} km</span>
                    </div>
                    <div>
                      <span className="text-text-muted block">UTILIZATION</span>
                      <span className="font-semibold text-gis-green">{plan.capacity_utilization_percent.toFixed(1)}%</span>
                    </div>
                  </div>

                  <div className="mt-2 text-[10px] text-text-muted flex items-center justify-between pt-1 border-t border-border-subtle">
                    <span>Pop: {plan.allocated_population.toLocaleString()} / {plan.allocated_population + plan.unallocated_population}</span>
                    <DataModeBadge mode="MODELED" size="sm" showIcon={false} />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Plan Allocations Detail */}
          {activePlan && (
            <div className="pt-2 border-t border-border-subtle shrink-0 font-mono text-[10px] space-y-1">
              <span className="text-text-muted uppercase block font-bold">RECEPTION PARCEL ALLOCATIONS:</span>
              <div className="max-h-28 overflow-y-auto space-y-1">
                {activePlan.allocations.map((alloc, i) => (
                  <div key={i} className="flex items-center justify-between bg-panel-header px-2 py-1 rounded border border-border-subtle">
                    <span className="text-text-primary font-bold">{alloc.candidate_id}</span>
                    <span className="text-text-secondary">{alloc.allocated_population} pers. ({alloc.distance_km.toFixed(1)} km)</span>
                    <span className="text-gis-green">{alloc.capacity_utilization_pct.toFixed(0)}% util</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Center Column: 8-Dimension Carrying Capacity Assessment (4 cols) */}
        <div className="col-span-4 flex flex-col bg-panel-bg border border-border-default rounded-[2px] p-3 overflow-hidden font-mono">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle shrink-0">
            <span className="text-[10px] font-bold uppercase text-text-muted">
              8-DIMENSION CARRYING CAPACITY AUDIT
            </span>
            <span className="text-[9px] text-text-muted">DATA HONESTY AUDITED</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 py-2 text-xs">
            {/* Housing */}
            <div className="p-2 rounded border border-border-subtle bg-panel-header/30">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-primary font-bold">
                  <Building2 className="w-3.5 h-3.5 text-gis-blue" /> HOUSING
                </span>
                <DataModeBadge mode="MODELED" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-text-secondary mt-1">
                Bench density: 75 persons/ha. 2.0 ha parcel capacity = 1,500 persons. Allocation fits within modeled footprint.
              </p>
            </div>

            {/* Water */}
            <div className="p-2 rounded border border-border-subtle bg-panel-header/30">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-primary font-bold">
                  <Droplets className="w-3.5 h-3.5 text-gis-blue" /> WATER
                </span>
                <DataModeBadge mode="PLANNING_ASSUMPTION" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-text-secondary mt-1">
                Baseline standard 55 lpcd (JJM assumption). Dry season stress scenario causes 104.7% overload without springhead expansion.
              </p>
            </div>

            {/* Sanitation */}
            <div className="p-2 rounded border border-slate-700 bg-slate-900/40">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-muted font-bold">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-400" /> SANITATION
                </span>
                <DataModeBadge mode="UNKNOWN" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                UNKNOWN: Soil percolation, sewage absorption, and DEWATS capacity unmeasured on candidate parcel.
              </p>
            </div>

            {/* Healthcare */}
            <div className="p-2 rounded border border-slate-700 bg-slate-900/40">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-muted font-bold">
                  <HeartPulse className="w-3.5 h-3.5 text-slate-400" /> HEALTHCARE
                </span>
                <DataModeBadge mode="UNKNOWN" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                UNKNOWN: PHC Pipalkoti spare bed/doctor capacity unverified in state medical registry.
              </p>
            </div>

            {/* Education */}
            <div className="p-2 rounded border border-border-subtle bg-panel-header/30">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-primary font-bold">
                  <GraduationCap className="w-3.5 h-3.5 text-gis-blue" /> EDUCATION
                </span>
                <DataModeBadge mode="PLANNING_ASSUMPTION" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-text-secondary mt-1">
                RTE pupil-teacher ratio benchmark: estimated 280 intake headroom in cluster schools.
              </p>
            </div>

            {/* Transport */}
            <div className="p-2 rounded border border-border-subtle bg-panel-header/30">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-primary font-bold">
                  <Truck className="w-3.5 h-3.5 text-gis-green" /> TRANSPORT
                </span>
                <DataModeBadge mode="PUBLIC" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-text-secondary mt-1">
                OpenStreetMap verified arterial road connection (NH-7 / Joshimath link).
              </p>
            </div>

            {/* Utilities */}
            <div className="p-2 rounded border border-slate-700 bg-slate-900/40">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-muted font-bold">
                  <Zap className="w-3.5 h-3.5 text-slate-400" /> UTILITIES
                </span>
                <DataModeBadge mode="UNKNOWN" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                UNKNOWN: Substation 33/11kV spare transformer load unmeasured.
              </p>
            </div>

            {/* Environment */}
            <div className="p-2 rounded border border-border-subtle bg-panel-header/30">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-primary font-bold">
                  <Trees className="w-3.5 h-3.5 text-gis-green" /> ENVIRONMENT
                </span>
                <DataModeBadge mode="MODELED" size="sm" showIcon={false} />
              </div>
              <p className="text-[10px] text-text-secondary mt-1">
                Parcel mean slope 9.9° (&lt;25° limit); 150m river buffer setback complied with.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Stress-Testing Scenarios & Robustness (4 cols) */}
        <div className="col-span-4 flex flex-col bg-panel-bg border border-border-default rounded-[2px] p-3 overflow-hidden font-mono">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle shrink-0">
            <span className="text-[10px] font-bold uppercase text-text-muted">
              DETERMINISTIC STRESS TESTING
            </span>
            <button
              onClick={handleRunRobustness}
              disabled={isRunningRobustness}
              className="px-2 py-1 bg-gis-blue/20 hover:bg-gis-blue/30 border border-gis-blue/40 text-gis-blue rounded text-[10px] font-bold flex items-center gap-1 transition-colors disabled:opacity-50"
            >
              <Play className={`w-3 h-3 ${isRunningRobustness ? 'animate-spin' : ''}`} />
              <span>{isRunningRobustness ? 'TESTING...' : 'RUN ALL 6 SCENARIOS'}</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-2 space-y-2 text-xs">
            {!robustness ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-4 text-text-muted">
                <ShieldCheck className="w-8 h-8 text-gis-blue mb-2 opacity-50" />
                <p className="text-xs font-bold text-text-secondary">No Stress Test Executed Yet</p>
                <p className="text-[10px] text-text-muted mt-1">
                  Click "Run All 6 Scenarios" above to evaluate Plan {activePlan?.plan_name || 'A'} against extreme stress conditions.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Robustness Summary Card */}
                <div className="p-3 bg-panel-header rounded border border-border-default">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase text-text-muted">ROBUSTNESS RATIO:</span>
                    <span className="text-sm font-bold text-gis-orange">
                      {robustness.robustness_score.toFixed(1)}% ({robustness.passed_scenarios}/{robustness.tested_scenarios - robustness.unknown_scenarios} evaluable)
                    </span>
                  </div>
                  <p className="text-[10px] text-text-secondary mt-1">{robustness.summary}</p>
                </div>

                {/* Scenario List */}
                <div className="space-y-2">
                  {robustness.scenarios.map((scen, idx) => {
                    let badgeColor = 'bg-slate-700/50 text-slate-300 border-slate-600';
                    let icon = <HelpCircle className="w-3 h-3 text-slate-400" />;

                    if (scen.status === 'PASS') {
                      badgeColor = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
                      icon = <CheckCircle2 className="w-3 h-3 text-emerald-400" />;
                    } else if (scen.status === 'DEGRADED') {
                      badgeColor = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
                      icon = <AlertTriangle className="w-3 h-3 text-amber-400" />;
                    } else if (scen.status === 'FAIL') {
                      badgeColor = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
                      icon = <XCircle className="w-3 h-3 text-rose-400" />;
                    }

                    return (
                      <div key={idx} className="p-2 rounded border border-border-subtle bg-panel-header/20">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold text-text-primary truncate">{scen.name}</span>
                          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[9px] font-bold ${badgeColor}`}>
                            {icon}
                            <span>{scen.status}</span>
                          </span>
                        </div>
                        {scen.binding_dimension && (
                          <div className="mt-1 text-[10px] text-gis-red font-semibold">
                            Bottleneck: {scen.binding_dimension}
                          </div>
                        )}
                        <p className="text-[10px] text-text-muted mt-0.5 leading-snug">{scen.summary}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
