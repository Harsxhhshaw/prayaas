// ── Core Domain Types for PRAYAAS ──

export type UrgencyLevel = 'IMMEDIATE' | 'SHORT_TERM' | 'MEDIUM_TERM';
export type RiskCategory = 'CRITICAL' | 'HIGH' | 'WATCH' | 'SAFE';
export type HazardType = 'LANDSLIDE' | 'FLOOD' | 'CLOUDBURST' | 'COASTAL_EROSION' | 'EARTHQUAKE' | 'AVALANCHE';
export type VerificationStatus = 'VERIFIED' | 'PENDING' | 'IN_PROGRESS' | 'FLAGGED';
export type LayerGroup = 'HAZARDS' | 'HABITATION' | 'RELOCATION' | 'TERRAIN';

export interface GeoPoint {
  lat: number;
  lng: number;
}

export interface GeoBounds {
  northEast: GeoPoint;
  southWest: GeoPoint;
}

export interface HazardScore {
  type: HazardType;
  score: number | null; // 0-100 or null if unknown / not applicable
  label: string;
  status?: 'VALUE' | 'UNKNOWN' | 'NOT_APPLICABLE';
}

export interface RiskHistoryEntry {
  year: number;
  score: number;
}

export interface Habitation {
  id: string;
  name: string;
  district: string;
  state: string;
  position: GeoPoint;
  riskScore: number; // 0-100
  riskCategory: RiskCategory;
  urgency: UrgencyLevel;
  population: number;
  households: number;
  confidence: number; // 0-100
  hazardScores: HazardScore[];
  vulnerabilityScore: number; // 0-100
  riskHistory: RiskHistoryEntry[];
  elevation: number; // meters
  nearestRoad: number; // km
  nearestHospital: number; // km
  nearestSchool: number; // km
  lastAssessed: string; // ISO date
  verificationStatus: VerificationStatus;
}

export interface CandidateRelocationSite {
  id: string;
  name: string;
  district: string;
  state: string;
  position: GeoPoint;
  bounds: [GeoPoint, GeoPoint, GeoPoint, GeoPoint];
  suitabilityScore: number; // 0-100
  carryingCapacity: number; // max population
  currentUtilization: number; // percentage
  areaHectares: number;
  elevation: number;
  distanceFromHazard: number; // km
  roadAccess: boolean;
  waterAccess: boolean;
  electricityAccess: boolean;
  landUseType: string;
  ownership: string;
  verificationStatus: VerificationStatus;
  assignedHabitations: string[]; // habitation IDs
}

export interface RelocationPriority {
  habitationId: string;
  habitationName: string;
  urgency: UrgencyLevel;
  riskScore: number;
  population: number;
  district: string;
  assignedSiteId?: string;
  assignedSiteName?: string;
  estimatedCost?: number; // in lakhs
  timelineMonths?: number;
  needScore?: number;
  readinessScore?: number;
  readinessLevel?: string;
  matrixPosition?: string | null;
}

export interface InfrastructurePoint {
  id: string;
  name: string;
  type: 'HOSPITAL' | 'SCHOOL' | 'ROAD_JUNCTION' | 'BRIDGE' | 'HELIPAD' | 'SHELTER';
  position: GeoPoint;
  status: 'OPERATIONAL' | 'DAMAGED' | 'UNDER_CONSTRUCTION';
  capacity?: number;
}

export interface RedZone {
  id: string;
  name: string;
  bounds: GeoPoint[];
  hazardTypes: HazardType[];
  compositRiskScore: number;
  habitationCount: number;
  populationAffected: number;
  areaKmSq: number;
  declaredDate: string;
  lastUpdated: string;
  computedAreaSqKm?: number;
  sourceDeclaredAreaSqKm?: number;
  classification?: string;
  requiresFieldVerification?: boolean;
  dominantHazard?: string;
  confidenceScore?: number;
  reasonCodes?: string[];
}

export interface OperationalAlert {
  id: string;
  message: string;
  type: 'ESCALATION' | 'WEATHER' | 'VERIFICATION' | 'PRIORITY_CHANGE' | 'FIELD_UPDATE' | 'SYSTEM';
  severity: RiskCategory;
  timestamp: string;
  habitationId?: string;
  read: boolean;
}

export interface MapLayer {
  id: string;
  name: string;
  group: LayerGroup;
  enabled: boolean;
  description?: string;
  icon?: string;
}

export interface KPIMetric {
  label: string;
  value: number | string;
  change?: number; // percentage change
  changeLabel?: string;
  icon?: string;
  color?: string;
}

export interface StateDistrict {
  state: string;
  districts: string[];
}

// ── Task 4 & 5 Domain Intelligence Types ──

export interface RiskAssessmentData {
  id: string;
  habitation_id: string;
  habitation_name?: string;
  analysis_version: string;
  config_version: string;
  baseline_hazard_score: number;
  dynamic_hazard_score: number;
  hazard_score: number;
  exposure_score: number;
  vulnerability_score: number;
  adaptive_capacity_score: number;
  adaptive_capacity_deficit_score: number;
  history_score: number;
  trend_score: number;
  compound_hazard_adjustment: number;
  baseline_structural_risk: number;
  current_dynamic_risk: number;
  composite_risk_score: number;
  risk_classification: string;
  confidence_score: number;
  dominant_hazard: string;
  sustainability_index: number;
  reason_codes: string[];
  explanation: string;
  calculated_at: string;
  input_snapshot?: Record<string, any>;
  source_snapshot?: Record<string, any>;
}

export interface RiskExplanationSectionsData {
  primary_drivers: string[];
  dynamic_factors: string[];
  protective_factors: string[];
  model_agreement: {
    level: string;
    ahp_score?: number | null;
    frequency_ratio_score?: number | null;
    ml_score?: number | null;
    status?: string;
    [key: string]: any;
  };
  data_limitations: string[];
  what_would_improve_confidence: string[];
}

export interface RiskExplanationData {
  id: string;
  habitation_id: string;
  habitation_name: string;
  composite_risk_score: number;
  risk_classification: string;
  confidence_score: number;
  dominant_hazard: string;
  sustainability_index: number;
  formula: string;
  component_weights: Record<string, number>;
  component_values: Record<string, number>;
  compound_hazard_adjustment: number;
  reason_codes: string[];
  narrative_explanation: string;
  sources_used: Array<{
    name: string;
    type: string;
    status: string;
  }>;
  confidence_rationale: string;
  calculated_at: string;
  sections?: RiskExplanationSectionsData;
}

export interface RelocationAssessmentData {
  id: string;
  habitation_id: string;
  habitation_name?: string;
  risk_assessment_id?: string;
  analysis_version: string;
  config_version: string;
  need_score: number;
  urgency: string;
  readiness_score: number;
  readiness_level: string;
  need_components: Record<string, any>;
  readiness_components: Record<string, any>;
  readiness_gaps: string[];
  reason_codes: string[];
  explanation: string;
  confidence_score: number;
  calculated_at: string;
}

export interface DataSourceFreshnessItem {
  id: string;
  name: string;
  provider: string;
  type: string;
  freshness: 'CURRENT' | 'AGING' | 'STALE' | 'UNKNOWN';
  lastSuccessfulIngestion?: string | null;
  expectedRefreshSeconds?: number | null;
  dataMode: string;
  isStale: boolean;
}

export interface RedZoneIntelligenceItem {
  id: string;
  name: string;
  classification: string;
  composite_risk_score: number;
  dominant_hazard: string;
  confidence_score?: number | null;
  habitation_count: number;
  population_affected: number;
  computed_area_sq_km: number;
  source_declared_area_sq_km?: number | null;
  reason_codes: string[];
  requires_field_verification: boolean;
}

export interface EvidenceLayerItem {
  id: string;
  name: string;
  evidence_type: string;
  source_id?: string | null;
  data_mode: string;
  representation_type: string;
  spatial_resolution?: number | null;
  derivation_method?: string | null;
  parent_layer_ids?: string[];
  quality_score?: number | null;
}

export interface CandidateParcelItem {
  id: string;
  discovery_run_id: string;
  origin_habitation_id: string;
  rank: number;
  suitability_score: number;
  confidence_score: number;
  robustness_score: number;
  rank_stability: number;
  robustness_level: 'HIGH' | 'MEDIUM' | 'LOW';
  area_hectares: number;
  distance_from_origin_km: number;
  mean_slope_degrees: number;
  status: 'PRELIMINARY' | 'SHORTLISTED' | 'REQUIRES_FIELD_REVIEW' | 'REJECTED' | 'ARCHIVED';
  data_mode: 'REAL' | 'MODELED' | 'DEMO' | 'FALLBACK';
  criteria_scores: Record<string, number>;
  exclusion_checks: Record<string, string>;
  explanation: {
    why_selected?: string[];
    limitations?: string[];
    robustness_summary?: string;
    rejection_summary?: string;
  };
  centroid: {
    lat: number;
    lng: number;
  };
  geometry?: any;
  created_at?: string;
}

export interface CandidateDiscoveryRunResponse {
  id: string;
  origin_habitation_id: string;
  status: string;
  configuration_version: string;
  analysis_version: string;
  search_radius_km: number;
  min_parcel_area_hectares: number;
  max_slope_degrees: number;
  candidate_parcels_discovered: number;
  top_candidates: CandidateParcelItem[];
  execution_duration_ms?: number;
  created_at: string;
}

// ── TASK 8 & 9: MULTI-SITE RELOCATION OPTIMIZATION & DIGITAL TWIN ──

export interface RelocationAllocationItem {
  id?: string | null;
  candidate_type: string;
  candidate_id: string;
  candidate_name?: string | null;
  allocated_population: number;
  usable_capacity: number;
  capacity_utilization_pct: number;
  distance_km: number;
  evidence_status: string;
  metadata?: Record<string, any>;
}

export interface RelocationPlanItem {
  id?: string | null;
  plan_name: string;
  strategy_type: string;
  allocated_population: number;
  unallocated_population: number;
  allocation_ratio: number;
  site_count: number;
  average_distance_km: number;
  max_distance_km: number;
  capacity_utilization_percent: number;
  relative_infrastructure_burden: number;
  community_fragmentation: string | null;
  livelihood_disruption: string | null;
  environmental_pressure: number | null;
  evidence_confidence: number;
  assumption_dependence: string;
  explanation: string;
  binding_constraints: string[];
  allocations: RelocationAllocationItem[];
}

export interface RelocationOptimizationRunRequest {
  origin_habitation_id: string;
  mode?: 'EXPLORATORY' | 'DECISION_SUPPORT';
  target_population?: number | null;
  max_sites?: number | null;
  min_allocation_size?: number;
  candidate_ids?: string[] | null;
  include_demo_candidates?: boolean;
  include_benchmark_sites?: boolean;
  objective_weights?: Record<string, number>;
}

export interface RelocationOptimizationRunResponse {
  run_id: string;
  origin_habitation_id: string;
  analysis_version: string;
  config_version: string;
  mode: string;
  target_population: number;
  solver_status: string;
  candidates_considered_count: number;
  usable_candidates_count: number;
  plans: RelocationPlanItem[];
  message?: string | null;
}

export interface ScenarioParameters {
  population_change_pct?: number;
  water_supply_change_pct?: number;
  road_unavailable?: boolean;
  unavailable_candidate_ids?: string[];
  health_capacity_change_pct?: number;
  education_capacity_change_pct?: number;
  utility_capacity_change_pct?: number;
  water_upgrade_capacity?: number;
  education_upgrade_capacity?: number;
  health_upgrade_capacity?: number;
  hazard_score_change?: number;
}

export interface ServiceDimensionLoad {
  dimension: string;
  allocated_load: number;
  capacity: number | null;
  utilization_pct: number | null;
  status: 'OK' | 'WARNING' | 'EXCEEDED' | 'UNKNOWN';
  evidence_status: string;
  notes: string;
}

export interface DestinationTwinState {
  candidate_id: string;
  candidate_type: string;
  allocated_population: number;
  distance_km: number;
  dimensions: ServiceDimensionLoad[];
  overall_status: 'OK' | 'WARNING' | 'EXCEEDED' | 'UNKNOWN';
  bottleneck_dimension: string | null;
}

export interface DigitalTwinSimulationResponse {
  plan_id: string;
  scenario_name: string;
  parameters: ScenarioParameters;
  destinations: DestinationTwinState[];
  total_allocated: number;
  total_unallocated: number;
  overall_plan_feasibility: 'PASS' | 'DEGRADED' | 'FAIL' | 'UNKNOWN';
  limiting_bottleneck: string | null;
  reoptimization_recommended: boolean;
  summary: string;
}

export interface ScenarioOutcome {
  scenario_id: string;
  name: string;
  status: 'PASS' | 'DEGRADED' | 'FAIL' | 'UNKNOWN';
  binding_dimension: string | null;
  summary: string;
}

export interface PlanRobustnessResponse {
  plan_id: string;
  plan_name: string;
  tested_scenarios: number;
  passed_scenarios: number;
  degraded_scenarios: number;
  failed_scenarios: number;
  unknown_scenarios: number;
  robustness_score: number;
  scenarios: ScenarioOutcome[];
  summary: string;
}

// Backward compatibility alias for PlanRobustnessResponse
export type PlanRobustnessAssessmentResponse = PlanRobustnessResponse;

// ── TASK 10: GOVERNANCE, FIELD EVIDENCE & DECISION DOSSIER ──

export interface FieldObservationItem {
  id: string;
  entity_type: 'HABITATION' | 'HAZARD_ZONE' | 'CANDIDATE_PARCEL' | 'CANDIDATE_SITE';
  entity_id: string;
  observation_type: string;
  observed_at: string;
  observer_name?: string | null;
  observer_role?: string | null;
  notes: string;
  evidence_values?: Record<string, any>;
  data_mode: string;
  verification_level: 'FIELD_OBSERVED' | 'TECHNICALLY_VERIFIED' | 'AUTHORITY_REVIEWED';
  verified_by?: string | null;
  verified_at?: string | null;
  technical_notes?: string | null;
  attachments_metadata?: Record<string, any>;
  source_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LandStatusItem {
  id: string;
  parcel_candidate_id: string;
  category: string;
  status: string;
  source_reference?: string | null;
  document_reference?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  notes?: string | null;
  data_mode: string;
  created_at: string;
}

export interface ConsultationItem {
  id: string;
  habitation_id: string;
  consultation_date: string;
  participant_count: number;
  method: string;
  questions_responses?: Record<string, any>;
  concerns?: string[];
  preferences?: Record<string, any>;
  source_attachment?: Record<string, any>;
  verification_status: string;
  data_mode: string;
  created_at: string;
}

export interface GovernanceReviewItem {
  id: string;
  entity_type: string;
  entity_id: string;
  review_stage: string;
  assigned_to?: string | null;
  reviewer_role?: string | null;
  review_notes?: string | null;
  action_taken?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalyticalOverrideItem {
  id: string;
  entity_type: 'HABITATION' | 'RISK_ASSESSMENT' | 'CANDIDATE_PARCEL' | 'RELOCATION_PLAN';
  entity_id: string;
  field_name: string;
  original_value: string;
  override_value: string;
  reason: string;
  reviewer: string;
  timestamp: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  user_id: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface DecisionDossierResponse {
  habitation_id: string;
  habitation_name: string;
  district: string;
  state: string;
  dossier_id: string;
  generated_at: string;
  analysis_version: string;
  config_version: string;
  executive_summary: string;
  risk_profile: Record<string, any>;
  relocation_assessment: Record<string, any>;
  candidate_land_discovery: Record<string, any>;
  candidate_comparison: Array<Record<string, any>>;
  carrying_capacity: Record<string, any>;
  relocation_alternatives: Array<Record<string, any>>;
  scenario_robustness: Record<string, any>;
  evidence_data_quality: Record<string, any>;
  verification_required: string[];
  provenance: Record<string, any>;
  disclaimer: string;
}

export interface DataHonestyAuditResponse {
  counts_by_mode: Record<string, number>;
  table_breakdown: Record<string, Record<string, number>>;
  ml_status: Record<string, string>;
  timestamp: string;
}



