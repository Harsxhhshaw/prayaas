import { useState, useEffect } from 'react';
import { X, ArrowRight, ExternalLink, ShieldAlert, CheckCircle2, MapPin, Calculator, Layers, AlertTriangle, FileText, Check, AlertOctagon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type {
  Habitation,
  CandidateRelocationSite,
  RedZone,
  InfrastructurePoint,
  RiskAssessmentData,
  RiskExplanationData,
  RelocationAssessmentData,
} from '../../types';
import { api } from '../../lib/api';

export type SelectedFeature =
  | { type: 'HABITATION'; data: Habitation }
  | { type: 'CANDIDATE_SITE'; data: CandidateRelocationSite }
  | { type: 'RED_ZONE'; data: RedZone }
  | { type: 'INFRASTRUCTURE'; data: InfrastructurePoint }
  | null;

interface FeatureInspectorProps {
  feature: SelectedFeature;
  onClose: () => void;
  onFocusFeature?: (coords: { lat: number; lng: number }) => void;
}

export function FeatureInspector({ feature, onClose, onFocusFeature }: FeatureInspectorProps) {
  const navigate = useNavigate();
  const [subTab, setSubTab] = useState<'OVERVIEW' | 'EXPLANATION' | 'RELOCATION'>('OVERVIEW');
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentData | null>(null);
  const [riskExplanation, setRiskExplanation] = useState<RiskExplanationData | null>(null);
  const [relocationAssessment, setRelocationAssessment] = useState<RelocationAssessmentData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (feature?.type === 'HABITATION') {
      const habId = feature.data.id;
      setLoading(true);
      Promise.all([
        api.getHabitationRisk(habId),
        api.getHabitationRiskExplanation(habId),
        api.getHabitationRelocation(habId),
      ])
        .then(([riskRes, explRes, relocRes]) => {
          setRiskAssessment(riskRes.data);
          setRiskExplanation(explRes.data);
          setRelocationAssessment(relocRes.data);
          setLoading(false);
        })
        .catch(() => {
          setLoading(false);
        });
    } else {
      setRiskAssessment(null);
      setRiskExplanation(null);
      setRelocationAssessment(null);
    }
  }, [feature]);

  if (!feature) return null;

  return (
    <aside className="w-[360px] bg-panel-bg border-l border-border-default flex flex-col h-full z-20 select-none overflow-hidden shrink-0 text-xs font-sans">
      {/* 1. Header with Close Button */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-panel-header border-b border-border-default shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
            FEATURE INSPECTION
          </span>
          <span className="text-[10px] font-mono px-1 py-0.2 bg-panel-bg border border-border-default rounded-[1px] text-text-secondary">
            {feature.type}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-text-muted hover:text-text-primary hover:bg-surface-hover rounded-[2px] transition-colors"
          title="Close Inspector (Esc)"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 2. Inspector Content Area (Flat sections, dense technical layout) */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {/* ===================================================================
            A. HABITATION INSPECTION
           =================================================================== */}
        {feature.type === 'HABITATION' && (() => {
          const h = feature.data;
          const displayScore = riskAssessment?.composite_risk_score ?? h.riskScore;
          const classification = riskAssessment?.risk_classification ?? (h.riskScore >= 80 ? 'PERMANENT_RED' : h.riskScore >= 60 ? 'CONDITIONAL_RED' : 'WATCH');
          const isRedZone = classification === 'PERMANENT_RED' || classification === 'DYNAMIC_RED' || classification === 'CONDITIONAL_RED';
          const trendDiff = h.riskHistory.length >= 2 
            ? h.riskHistory[h.riskHistory.length - 1].score - h.riskHistory[0].score 
            : 0;
          const dominantHazard = riskAssessment?.dominant_hazard ?? 'LANDSLIDE';
          const hsi = riskAssessment?.sustainability_index;

          return (
            <div className="space-y-3">
              {/* Feature Title & Subtitle */}
              <div>
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-bold text-text-primary uppercase tracking-tight font-mono">
                    {h.name}
                  </h2>
                  {riskAssessment && (
                    <span className="text-[9px] font-mono px-1 py-0.5 bg-gis-blue/15 border border-gis-blue/40 text-gis-blue rounded-[1px]">
                      {riskAssessment.analysis_version}
                    </span>
                  )}
                </div>
                <div className="text-[11px] font-mono text-text-muted flex items-center gap-1.5 mt-0.5">
                  <span>{h.district}</span>
                  <span>/</span>
                  <span>{h.state}</span>
                  <span>•</span>
                  <span>ID: {h.id}</span>
                </div>
              </div>

              {/* Sub-tab Navigation */}
              <div className="flex border-b border-border-default bg-panel-header/50 p-0.5 rounded-[2px] font-mono text-[10px]">
                <button
                  onClick={() => setSubTab('OVERVIEW')}
                  className={`flex-1 py-1 text-center font-medium transition-colors rounded-[1px] ${
                    subTab === 'OVERVIEW'
                      ? 'bg-panel-bg text-text-primary shadow-sm'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  RISK OVERVIEW
                </button>
                <button
                  onClick={() => setSubTab('EXPLANATION')}
                  className={`flex-1 py-1 text-center font-medium transition-colors rounded-[1px] ${
                    subTab === 'EXPLANATION'
                      ? 'bg-panel-bg text-text-primary shadow-sm'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  FORMULA & DATA
                </button>
                <button
                  onClick={() => setSubTab('RELOCATION')}
                  className={`flex-1 py-1 text-center font-medium transition-colors rounded-[1px] ${
                    subTab === 'RELOCATION'
                      ? 'bg-panel-bg text-text-primary shadow-sm'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  RELOCATION NEED
                </button>
              </div>

              {/* TAB 1: RISK OVERVIEW */}
              {subTab === 'OVERVIEW' && (
                <div className="space-y-3.5">
                  {/* Status Header: Classification + Composite Risk Score */}
                  <div className="flex items-baseline justify-between border-b border-border-default pb-2">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`font-mono text-xs font-bold uppercase tracking-wider ${
                            classification === 'PERMANENT_RED'
                              ? 'text-gis-red'
                              : classification === 'DYNAMIC_RED'
                              ? 'text-gis-orange'
                              : classification === 'CONDITIONAL_RED'
                              ? 'text-gis-orange'
                              : 'text-gis-yellow'
                          }`}
                        >
                          {classification.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-[10px] font-mono text-text-muted">
                        Dominant: <span className="text-text-secondary font-semibold">{dominantHazard}</span>
                      </div>
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span
                        className={`text-2xl font-bold font-mono tabular-nums ${
                          isRedZone ? 'text-gis-red' : 'text-text-primary'
                        }`}
                      >
                        {displayScore.toFixed(1)}
                      </span>
                      <span className="text-[10px] font-mono text-text-muted">/100</span>
                    </div>
                  </div>

                  {/* Baseline vs Dynamic Hazard Comparison (when live) */}
                  {riskAssessment && (
                    <div className="bg-panel-header/70 p-2 rounded-[2px] border border-border-subtle font-mono text-[10px] space-y-1.5">
                      <div className="text-text-muted uppercase tracking-wider flex justify-between">
                        <span>Hazard Calibration</span>
                        {riskAssessment.compound_hazard_adjustment > 0 && (
                          <span className="text-gis-orange font-bold">
                            Compound +{riskAssessment.compound_hazard_adjustment.toFixed(1)}
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div>
                          <span className="text-text-muted text-[9px] block">BASELINE HAZARD</span>
                          <span className="font-bold text-text-primary">{riskAssessment.baseline_hazard_score.toFixed(1)}</span>
                        </div>
                        <div>
                          <span className="text-text-muted text-[9px] block">DYNAMIC HAZARD (METEO)</span>
                          <span className={`font-bold ${riskAssessment.dynamic_hazard_score > riskAssessment.baseline_hazard_score ? 'text-gis-orange' : 'text-text-primary'}`}>
                            {riskAssessment.dynamic_hazard_score.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Multi-Hazard Breakdown */}
                  <div className="space-y-2">
                    <div className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                      Hazard Drivers & Vulnerability
                    </div>
                    <div className="space-y-1.5">
                      {h.hazardScores.map((hz) => (
                        <div key={hz.type} className="space-y-0.5">
                          <div className="flex justify-between text-[11px]">
                            <span className="text-text-secondary">{hz.label}</span>
                            <span
                              className={`font-mono tabular-nums font-medium ${
                                hz.score >= 80
                                  ? 'text-gis-red'
                                  : hz.score >= 60
                                  ? 'text-gis-orange'
                                  : 'text-text-primary'
                              }`}
                            >
                              {hz.score}
                            </span>
                          </div>
                          <div className="w-full h-1 bg-panel-header rounded-[1px] overflow-hidden">
                            <div
                              className={`h-full ${
                                hz.score >= 80
                                  ? 'bg-gis-red'
                                  : hz.score >= 60
                                  ? 'bg-gis-orange'
                                  : 'bg-gis-yellow'
                              }`}
                              style={{ width: `${hz.score}%` }}
                            />
                          </div>
                        </div>
                      ))}

                      {/* Social Vulnerability */}
                      <div className="space-y-0.5 pt-1">
                        <div className="flex justify-between text-[11px]">
                          <span className="text-text-secondary">Social Vulnerability</span>
                          <span className="font-mono tabular-nums text-text-primary font-medium">
                            {riskAssessment?.vulnerability_score?.toFixed(1) ?? h.vulnerabilityScore}
                          </span>
                        </div>
                        <div className="w-full h-1 bg-panel-header rounded-[1px] overflow-hidden">
                          <div
                            className="h-full bg-gis-blue"
                            style={{ width: `${riskAssessment?.vulnerability_score ?? h.vulnerabilityScore}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Dense Numerical Matrix with HSI */}
                  <div className="border-t border-border-default pt-2.5 grid grid-cols-4 gap-1.5 text-[11px] font-mono text-center">
                    <div className="bg-panel-header p-1.5 rounded-[2px] border border-border-subtle">
                      <div className="text-text-muted text-[8px] uppercase">POPULATION</div>
                      <div className="font-bold text-text-primary tabular-nums mt-0.5">
                        {h.population.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-panel-header p-1.5 rounded-[2px] border border-border-subtle">
                      <div className="text-text-muted text-[8px] uppercase">RISK TREND</div>
                      <div className="font-bold text-gis-red tabular-nums mt-0.5">
                        +{trendDiff} (5Y)
                      </div>
                    </div>
                    <div className="bg-panel-header p-1.5 rounded-[2px] border border-border-subtle">
                      <div className="text-text-muted text-[8px] uppercase">CONFIDENCE</div>
                      <div className="font-bold text-text-primary tabular-nums mt-0.5">
                        {riskAssessment?.confidence_score ?? h.confidence}%
                      </div>
                    </div>
                    <div className="bg-panel-header p-1.5 rounded-[2px] border border-border-subtle">
                      <div className="text-text-muted text-[8px] uppercase">HSI SCORE</div>
                      <div className={`font-bold tabular-nums mt-0.5 ${hsi !== undefined && hsi < 35 ? 'text-gis-red' : 'text-text-primary'}`}>
                        {hsi !== undefined ? `${hsi.toFixed(1)}` : 'N/A'}
                      </div>
                    </div>
                  </div>

                  {/* Reason Codes Pill Badges */}
                  {riskAssessment && riskAssessment.reason_codes.length > 0 && (
                    <div className="border-t border-border-default pt-2.5">
                      <div className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1.5">
                        Intelligence Factor Tags
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {riskAssessment.reason_codes.slice(0, 6).map((rc) => (
                          <span
                            key={rc}
                            className="px-1.5 py-0.5 bg-panel-header border border-border-subtle rounded-[1px] text-[9px] font-mono text-text-secondary"
                          >
                            {rc.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Primary Driver Intelligence Narrative */}
                  <div className="border-t border-border-default pt-2.5">
                    <div className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1">
                      Primary Assessment Narrative
                    </div>
                    <p className="text-[11px] text-text-secondary leading-relaxed bg-panel-header p-2 rounded-[2px] border border-border-subtle font-mono">
                      {riskAssessment?.explanation || (h.riskScore >= 85
                        ? 'Repeated slope instability detected via InSAR (4.2mm/mo subsidence). Heavy monsoonal saturation elevates debris-flow threshold above critical limit.'
                        : 'Steep catchment geometry with alluvial toe-cutting along river bank. Severe exposure during high-precipitation cloudburst episodes.')}
                    </p>
                  </div>

                  {/* Proximity & Critical Access */}
                  <div className="border-t border-border-default pt-2.5">
                    <div className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-2">
                      Proximity & Infrastructure Access
                    </div>
                    <div className="grid grid-cols-3 gap-1.5 text-[11px] font-mono">
                      <div className="bg-panel-header p-1.5 rounded-[2px] border border-border-subtle">
                        <span className="text-[9px] text-text-muted block">ROAD</span>
                        <span className="text-text-primary font-medium">{h.nearestRoad} km</span>
                      </div>
                      <div className="bg-panel-header p-1.5 rounded-[2px] border border-border-subtle">
                        <span className="text-[9px] text-text-muted block">HOSPITAL</span>
                        <span className="text-text-primary font-medium">{h.nearestHospital} km</span>
                      </div>
                      <div className="bg-panel-header p-1.5 rounded-[2px] border border-border-subtle">
                        <span className="text-[9px] text-text-muted block">ELEVATION</span>
                        <span className="text-text-primary font-medium">{h.elevation} m</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: FORMULA & PROVENANCE */}
              {subTab === 'EXPLANATION' && (
                <div className="space-y-3 font-mono text-xs">
                  {riskExplanation ? (
                    <>
                      <div>
                        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">
                          Deterministic Multi-Hazard Formula
                        </div>
                        <div className="p-2 bg-panel-header border border-border-subtle rounded-[2px] text-[10px] text-text-secondary leading-normal break-words font-mono">
                          {riskExplanation.formula}
                        </div>
                      </div>

                      {/* Component breakdown table */}
                      <div className="border border-border-subtle rounded-[2px] overflow-hidden">
                        <table className="w-full text-left border-collapse text-[10px]">
                          <thead className="bg-panel-header text-text-muted border-b border-border-subtle uppercase">
                            <tr>
                              <th className="p-1.5">Component</th>
                              <th className="p-1.5 text-right">Weight</th>
                              <th className="p-1.5 text-right">Value</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border-subtle text-text-secondary">
                            {Object.entries(riskExplanation.component_weights).map(([k, weight]) => {
                              const valKey = k.split(' (')[0];
                              const val = riskExplanation.component_values[valKey] ?? 0;
                              return (
                                <tr key={k}>
                                  <td className="p-1.5 text-text-primary font-medium">{valKey}</td>
                                  <td className="p-1.5 text-right font-mono text-text-muted">{(weight * 100).toFixed(0)}%</td>
                                  <td className="p-1.5 text-right font-mono font-bold text-text-primary">{val.toFixed(1)}</td>
                                </tr>
                              );
                            })}
                            {riskExplanation.compound_hazard_adjustment > 0 && (
                              <tr className="bg-gis-orange/10 font-bold">
                                <td className="p-1.5 text-gis-orange">Compound Escalation</td>
                                <td className="p-1.5 text-right font-mono text-gis-orange">Add</td>
                                <td className="p-1.5 text-right font-mono text-gis-orange">+{riskExplanation.compound_hazard_adjustment.toFixed(1)}</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>

                      {/* Data Sources Provenance */}
                      <div>
                        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">
                          Evidence Provenance ({riskExplanation.sources_used.length} Sources)
                        </div>
                        <div className="space-y-1">
                          {riskExplanation.sources_used.map((s, idx) => (
                            <div key={idx} className="p-1.5 bg-panel-header rounded-[2px] border border-border-subtle flex items-center justify-between text-[10px]">
                              <span className="text-text-primary font-medium truncate max-w-[200px]">{s.name}</span>
                              <span className="px-1 py-0.2 bg-panel-bg border border-border-subtle rounded-[1px] text-[9px] text-gis-green font-bold">
                                {s.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Confidence Rationale */}
                      <div className="p-2 bg-panel-header rounded-[2px] border border-border-subtle text-[10px] text-text-secondary">
                        <span className="text-text-muted uppercase tracking-wider block text-[9px] mb-0.5">Confidence Rationale</span>
                        {riskExplanation.confidence_rationale}
                      </div>
                    </>
                  ) : (
                    <div className="p-4 text-center text-text-muted text-[11px]">
                      Loading explanation and factor breakdown...
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: RELOCATION NEED */}
              {subTab === 'RELOCATION' && (
                <div className="space-y-3 font-mono text-xs">
                  {relocationAssessment ? (
                    <>
                      {/* Need vs Readiness Split */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                          <span className="text-[9px] text-text-muted uppercase block">RELOCATION NEED</span>
                          <div className="flex items-baseline gap-1 mt-0.5">
                            <span className="text-xl font-bold text-gis-red tabular-nums">
                              {relocationAssessment.need_score.toFixed(1)}
                            </span>
                            <span className="text-[10px] text-text-muted">/100</span>
                          </div>
                          <span className="text-[9px] text-gis-red font-bold uppercase tracking-wider">
                            {relocationAssessment.urgency.replace('_', ' ')}
                          </span>
                        </div>

                        <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                          <span className="text-[9px] text-text-muted uppercase block">RECEPTION READINESS</span>
                          <div className="flex items-baseline gap-1 mt-0.5">
                            <span className="text-xl font-bold text-gis-blue tabular-nums">
                              {relocationAssessment.readiness_score.toFixed(1)}
                            </span>
                            <span className="text-[10px] text-text-muted">/100</span>
                          </div>
                          <span className="text-[9px] text-gis-blue font-bold uppercase tracking-wider">
                            {relocationAssessment.readiness_level.replace('_', ' ')}
                          </span>
                        </div>
                      </div>

                      {/* Matrix Position Banner */}
                      <div className="p-2 bg-gis-orange/10 border border-gis-orange/30 rounded-[2px] text-[10px] text-gis-orange font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                        <span>MATRIX: {relocationAssessment.reason_codes.find(c => c.includes('BOTTLENECK') || c.includes('EXECUTION') || c.includes('MONITOR')) || 'ACUTE RISK READINESS BOTTLENECK'}</span>
                      </div>

                      {/* Rule Reminder Note */}
                      <div className="p-2 bg-panel-header border border-border-subtle rounded-[2px] text-[10px] text-text-muted leading-relaxed">
                        <span className="font-bold text-text-secondary">Methodological Guard:</span> Candidate reception sites strictly do NOT diminish relocation need. Relocation need is driven entirely by physical exposure, structural risk, and social vulnerability.
                      </div>

                      {/* Readiness Gaps Blockers */}
                      {relocationAssessment.readiness_gaps.length > 0 && (
                        <div>
                          <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">
                            Execution Blockers & Readiness Gaps
                          </div>
                          <div className="space-y-1">
                            {relocationAssessment.readiness_gaps.map((gap, idx) => (
                              <div key={idx} className="p-1.5 bg-gis-red/10 border border-gis-red/30 rounded-[2px] text-[10px] text-gis-red font-medium flex items-center gap-1.5">
                                <AlertOctagon className="w-3 h-3 shrink-0" />
                                <span>{gap.replace(/_/g, ' ')}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Relocation Narrative */}
                      <div className="p-2 bg-panel-header rounded-[2px] border border-border-subtle text-[10px] text-text-secondary leading-relaxed">
                        {relocationAssessment.explanation}
                      </div>
                    </>
                  ) : (
                    <div className="p-4 text-center text-text-muted text-[11px]">
                      Loading relocation need assessment...
                    </div>
                  )}
                </div>
              )}

              {/* Actions (Flat professional workstation buttons) */}
              <div className="border-t border-border-default pt-3 space-y-2">
                <button
                  onClick={() => navigate(`/habitations?id=${h.id}`)}
                  className="w-full py-1.5 px-3 bg-surface-active hover:bg-border-active border border-border-default text-text-primary rounded-[2px] font-mono text-[11px] flex items-center justify-between transition-colors"
                >
                  <span>OPEN FULL HABITATION DOSSIER</span>
                  <ExternalLink className="w-3.5 h-3.5 text-text-muted" />
                </button>
                <button
                  onClick={() => navigate(`/candidate-sites?for=${h.id}`)}
                  className="w-full py-1.5 px-3 bg-gis-blue/15 hover:bg-gis-blue/25 border border-gis-blue/40 text-gis-blue rounded-[2px] font-mono text-[11px] flex items-center justify-between transition-colors font-medium"
                >
                  <span>FIND RELOCATION SITES</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })()}


        {/* ===================================================================
            B. CANDIDATE RELOCATION SITE INSPECTION
           =================================================================== */}
        {feature.type === 'CANDIDATE_SITE' && (() => {
          const s = feature.data;
          return (
            <div className="space-y-4">
              <div>
                <h2 className="text-base font-bold text-text-primary uppercase tracking-tight font-mono">
                  {s.name}
                </h2>
                <div className="text-[11px] font-mono text-text-muted flex items-center gap-1.5 mt-0.5">
                  <span>{s.district}</span>
                  <span>/</span>
                  <span>{s.state}</span>
                  <span>•</span>
                  <span>ID: {s.id}</span>
                </div>
              </div>

              <div className="flex items-baseline justify-between border-b border-border-default pb-2">
                <span className="font-mono text-xs font-bold text-gis-green uppercase tracking-wider">
                  CANDIDATE RELOCATION SITE
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold font-mono text-gis-green tabular-nums">
                    {s.suitabilityScore}
                  </span>
                  <span className="text-[10px] font-mono text-text-muted">/100</span>
                </div>
              </div>

              {/* Capacity & Parameters */}
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  <span className="text-[10px] text-text-muted block">CARRYING CAPACITY</span>
                  <span className="text-text-primary font-bold text-sm">
                    {s.carryingCapacity.toLocaleString()}
                  </span>
                  <span className="text-[9px] text-text-muted ml-1">persons</span>
                </div>
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  <span className="text-[10px] text-text-muted block">AREA</span>
                  <span className="text-text-primary font-bold text-sm">{s.areaHectares}</span>
                  <span className="text-[9px] text-text-muted ml-1">hectares</span>
                </div>
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  <span className="text-[10px] text-text-muted block">ELEVATION</span>
                  <span className="text-text-primary font-bold text-sm">{s.elevation}</span>
                  <span className="text-[9px] text-text-muted ml-1">meters</span>
                </div>
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  <span className="text-[10px] text-text-muted block">HAZARD BUFFER</span>
                  <span className="text-text-primary font-bold text-sm">{s.distanceFromHazard}</span>
                  <span className="text-[9px] text-text-muted ml-1">km distance</span>
                </div>
              </div>

              {/* Utility Connectivity */}
              <div className="border-t border-border-default pt-3">
                <div className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-2">
                  Infrastructure Readiness
                </div>
                <div className="space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-text-secondary">All-Weather Road Access</span>
                    <span className={s.roadAccess ? 'text-gis-green' : 'text-gis-red'}>
                      {s.roadAccess ? '● CONNECTED' : '○ PENDING'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-text-secondary">Piped Water Infrastructure</span>
                    <span className={s.waterAccess ? 'text-gis-green' : 'text-gis-red'}>
                      {s.waterAccess ? '● CONNECTED' : '○ PENDING'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-0.5">
                    <span className="text-text-secondary">High-Tension Power Grid</span>
                    <span className={s.electricityAccess ? 'text-gis-green' : 'text-gis-red'}>
                      {s.electricityAccess ? '● CONNECTED' : '○ PENDING'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Land Ownership */}
              <div className="border-t border-border-default pt-3 font-mono text-[11px]">
                <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">
                  Land Registry Data
                </div>
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle space-y-1">
                  <div>Classification: <span className="text-text-primary">{s.landUseType}</span></div>
                  <div>Ownership: <span className="text-text-primary">{s.ownership}</span></div>
                  <div>Verification: <span className="text-gis-green">{s.verificationStatus}</span></div>
                </div>
              </div>

              <div className="border-t border-border-default pt-3">
                <button
                  onClick={() => navigate(`/candidate-sites?site=${s.id}`)}
                  className="w-full py-1.5 px-3 bg-gis-green/15 hover:bg-gis-green/25 border border-gis-green/40 text-gis-green rounded-[2px] font-mono text-[11px] flex items-center justify-between transition-colors font-medium"
                >
                  <span>ALLOCATE TO PRIORITY HABITATIONS</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })()}

        {/* ===================================================================
            C. RED ZONE INSPECTION
           =================================================================== */}
        {feature.type === 'RED_ZONE' && (() => {
          const rz = feature.data;
          return (
            <div className="space-y-4">
              <div>
                <h2 className="text-base font-bold text-text-primary uppercase tracking-tight font-mono">
                  {rz.name}
                </h2>
                <div className="text-[11px] font-mono text-text-muted mt-0.5">
                  ID: {rz.id} • DECLARED: {rz.declaredDate}
                </div>
              </div>

              <div className="flex items-baseline justify-between border-b border-border-default pb-2">
                <span className="font-mono text-xs font-bold text-gis-red uppercase tracking-wider">
                  STATUTORY RED ZONE
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold font-mono text-gis-red tabular-nums">
                    {rz.compositRiskScore}
                  </span>
                  <span className="text-[10px] font-mono text-text-muted">/100</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  <span className="text-[10px] text-text-muted block">ZONE AREA</span>
                  <span className="text-text-primary font-bold">{rz.areaKmSq} km²</span>
                </div>
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  <span className="text-[10px] text-text-muted block">POPULATION</span>
                  <span className="text-gis-red font-bold">{rz.populationAffected.toLocaleString()}</span>
                </div>
                <div className="bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  <span className="text-[10px] text-text-muted block">VILLAGES</span>
                  <span className="text-text-primary font-bold">{rz.habitationCount}</span>
                </div>
              </div>

              <div className="border-t border-border-default pt-3">
                <div className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-2">
                  Active Hazard Multipliers
                </div>
                <div className="flex flex-wrap gap-1 font-mono text-[10px]">
                  {rz.hazardTypes.map((ht) => (
                    <span
                      key={ht}
                      className="px-2 py-0.5 bg-gis-red/10 border border-gis-red/30 text-gis-red rounded-[1px]"
                    >
                      {ht}
                    </span>
                  ))}
                </div>
              </div>

              <div className="border-t border-border-default pt-3">
                <p className="text-[11px] font-mono text-text-secondary leading-relaxed bg-panel-header p-2 rounded-[2px] border border-border-subtle">
                  Mandatory prohibition of permanent human habitation under NDMA guidelines Section 31.
                  Immediate priority for relocation scheduling.
                </p>
              </div>

              <div className="border-t border-border-default pt-3">
                <button
                  onClick={() => navigate('/red-zones')}
                  className="w-full py-1.5 px-3 bg-surface-active hover:bg-border-active border border-border-default text-text-primary rounded-[2px] font-mono text-[11px] flex items-center justify-between transition-colors"
                >
                  <span>VIEW RED ZONE REGISTRY</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })()}

        {/* ===================================================================
            D. INFRASTRUCTURE INSPECTION
           =================================================================== */}
        {feature.type === 'INFRASTRUCTURE' && (() => {
          const inf = feature.data;
          return (
            <div className="space-y-4">
              <div>
                <h2 className="text-base font-bold text-text-primary uppercase tracking-tight font-mono">
                  {inf.name}
                </h2>
                <div className="text-[11px] font-mono text-text-muted mt-0.5">
                  ID: {inf.id} • TYPE: {inf.type}
                </div>
              </div>

              <div className="flex items-baseline justify-between border-b border-border-default pb-2">
                <span className="font-mono text-xs font-bold text-gis-blue uppercase tracking-wider">
                  CRITICAL INFRASTRUCTURE
                </span>
                <span
                  className={`text-xs font-mono font-bold ${
                    inf.status === 'OPERATIONAL' ? 'text-gis-green' : 'text-gis-red'
                  }`}
                >
                  {inf.status}
                </span>
              </div>

              <div className="bg-panel-header p-2.5 rounded-[2px] border border-border-subtle font-mono text-[11px] space-y-1.5">
                <div>Class: <span className="text-text-primary">{inf.type.replace('_', ' ')}</span></div>
                {inf.capacity && (
                  <div>Rated Capacity: <span className="text-text-primary">{inf.capacity} units</span></div>
                )}
                <div>
                  Coordinates: <span className="text-text-primary">{inf.position.lat.toFixed(4)}°N, {inf.position.lng.toFixed(4)}°E</span>
                </div>
              </div>
            </div>
          );
        })()}
      </div>
    </aside>
  );
}
