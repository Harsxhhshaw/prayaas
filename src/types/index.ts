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
  score: number; // 0-100
  label: string;
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

