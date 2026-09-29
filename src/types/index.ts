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
  confidence_score: number;
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
  id: string;
  candidate_type: string;
  candidate_id: string;
  allocated_population: number;
  usable_capacity: number;
  capacity_utilization_pct: number;
  distance_km: number;
  evidence_status: string;
  metadata?: Record<string, any>;
}

export interface RelocationPlanItem {
  id: string;
  plan_name: string;
  strategy_type: 'MIN_DISTANCE' | 'MIN_SITE_COUNT' | 'BALANCED';
  allocated_population: number;
  unallocated_population: number;
  allocation_ratio: number;
  site_count: number;
  average_distance_km: number;
  max_distance_km: number;
  capacity_utilization_percent: number;
  relative_infrastructure_burden: number;
  community_fragmentation: number;
  livelihood_disruption: number;
  environmental_pressure: number;
  evidence_confidence: number;
  assumption_dependence: string;
  explanation: Record<string, any>;
  binding_constraints: string[];
  allocations: RelocationAllocationItem[];
}

export interface RelocationOptimizationRunResponse {
  run_id: string;
  origin_habitation_id: string;
  analysis_version: string;
  config_version: string;
  mode: 'PLANNING_EXPLORATORY' | 'DECISION_SUPPORT';
  target_population: number;
  solver_status: string;
  candidates_considered_count: number;
  usable_candidates_count: number;
  plans: RelocationPlanItem[];
  message: string;
}

export interface SimulatedDestinationLoad {
  candidate_id: string;
  candidate_name: string;
  baseline_population: number;
  incoming_population: number;
  total_projected_population: number;
  status_by_dimension: Record<string, 'OK' | 'WARNING' | 'EXCEEDED' | 'UNKNOWN'>;
  loads_by_dimension: Record<string, { demand: number; capacity: number; utilization_pct: number | null }>;
  severed_access: boolean;
  operational_status: 'NOMINAL' | 'DEGRADED' | 'EXCEEDED' | 'OUTAGE';
  warnings: string[];
}

export interface DigitalTwinSimulationResponse {
  run_id: string;
  plan_id: string;
  scenario_name: string;
  system_status: 'STABLE' | 'DEGRADED' | 'FAILURE';
  destination_loads: SimulatedDestinationLoad[];
  unhoused_due_to_failure: number;
  bottleneck_dimension: string;
  summary_notes: string[];
}

export interface PlanRobustnessAssessmentResponse {
  plan_id: string;
  plan_name: string;
  scenarios_evaluated: number;
  pass_count: number;
  degraded_count: number;
  fail_count: number;
  unknown_count: number;
  robustness_ratio: number;
  primary_vulnerability: string;
  recommendations: string[];
}


