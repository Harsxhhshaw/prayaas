/**
 * PRAYAAS API Client Foundation
 * Configured with VITE_API_BASE_URL (defaults to http://localhost:8000)
 */

import type {
  Habitation,
  CandidateRelocationSite,
  RelocationPriority,
  InfrastructurePoint,
  RedZone,
  OperationalAlert,
  StateDistrict,
  RiskAssessmentData,
  RiskExplanationData,
  RelocationAssessmentData,
  DataSourceFreshnessItem,
  RedZoneIntelligenceItem,
  EvidenceLayerItem,
  CandidateParcelItem,
  CandidateDiscoveryRunResponse,
  RelocationPlanItem,
  RelocationOptimizationRunResponse,
  ScenarioParameters,
  DigitalTwinSimulationResponse,
  PlanRobustnessResponse,
  PlanRobustnessAssessmentResponse,
  FieldObservationItem,
  LandStatusItem,
  ConsultationItem,
  GovernanceReviewItem,
  AnalyticalOverrideItem,
  AuditLogItem,
  DecisionDossierResponse,
  DataHonestyAuditResponse,
} from '../types';

import {
  habitations as mockHabitations,
  redZones as mockRedZones,
  candidateSites as mockCandidateSites,
  infrastructurePoints as mockInfrastructure,
  relocationPriorities as mockPriorities,
  operationalAlerts as mockAlerts,
  statesAndDistricts as mockStatesAndDistricts,
} from '../data/mockData';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

export class ApiError extends Error {
  status?: number;
  url: string;
  detail?: string;

  constructor(message: string, url: string, status?: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.url = url;
    this.detail = detail;
  }
}

export function getStoredApiKey(): string | null {
  try {
    return localStorage.getItem('prayaas_api_key');
  } catch {
    return null;
  }
}

export function setStoredApiKey(key: string): void {
  try {
    localStorage.setItem('prayaas_api_key', key);
  } catch {
    // Ignore in non-browser context
  }
}

async function fetchJson<T>(url: string, fallback: T): Promise<{ data: T; isLive: boolean; error?: string }> {
  try {
    const apiKey = getStoredApiKey();
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (apiKey) headers['X-API-Key'] = apiKey;

    const res = await fetch(`${API_BASE_URL}${url}`, { headers });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const json = await res.json();
    return { data: json, isLive: true };
  } catch (err: any) {
    if (import.meta.env.DEV) {
      console.warn(`[PRAYAAS API] Fallback used for ${url}:`, err.message);
    }
    return { data: fallback, isLive: false, error: err?.message || 'Network error' };
  }
}

async function postAnalysisJson<T>(url: string, body: any): Promise<{ data: T; isLive: boolean }> {
  const apiKey = getStoredApiKey();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (apiKey) headers['X-API-Key'] = apiKey;

  const res = await fetch(`${API_BASE_URL}${url}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = '';
    try {
      const errJson = await res.json();
      detail = errJson.detail || JSON.stringify(errJson);
    } catch {
      detail = await res.text();
    }
    throw new ApiError(`Request to ${url} failed with HTTP ${res.status}: ${detail || res.statusText}`, url, res.status, detail);
  }
  const json = await res.json();
  return { data: json, isLive: true };
}

export interface ApiHealth {
  status: string;
  service?: string;
  postgis_version?: string;
}

export interface DataSourceItem {
  id: string;
  name: string;
  provider: string;
  type: string;
  status: string;
  lastSync?: string;
  recordsCount: number;
  latencyMs: number;
  dataMode: string;
}

export interface DisasterEventItem {
  id: string;
  title: string;
  hazardType: string;
  severity: string;
  eventDate: string;
  district: string;
  fatalities: number;
  displacedPersons: number;
  description: string;
  dataMode: string;
}

export interface MetricsSummary {
  total_habitations: number;
  critical_habitations: number;
  high_habitations: number;
  total_population_at_risk: number;
  active_red_zones: number;
  candidate_sites: number;
  pending_relocations: number;
  field_verifications_pending: number;
}

export const api = {
  // Health
  async getHealth(): Promise<{ data: ApiHealth; isLive: boolean }> {
    return fetchJson<ApiHealth>('/api/health', { status: 'offline' });
  },

  async getDatabaseHealth(): Promise<{ data: ApiHealth; isLive: boolean }> {
    return fetchJson<ApiHealth>('/api/health/database', { status: 'offline' });
  },

  // States & Districts
  async getStates(): Promise<{ data: { items: { id: string; name: string; code: string }[]; total: number }; isLive: boolean }> {
    return fetchJson('/api/states', {
      items: mockStatesAndDistricts.map((s, idx) => ({ id: `ST-${idx + 1}`, name: s.state, code: s.state.slice(0, 2).toUpperCase() })),
      total: mockStatesAndDistricts.length,
    });
  },

  async getDistricts(state?: string): Promise<{ data: { items: { id: string; name: string; state: string }[]; total: number }; isLive: boolean }> {
    const url = state ? `/api/districts?state=${encodeURIComponent(state)}` : '/api/districts';
    const fallbackItems: { id: string; name: string; state: string }[] = [];
    mockStatesAndDistricts.forEach((s) => {
      if (!state || s.state === state) {
        s.districts.forEach((d, idx) => {
          fallbackItems.push({ id: `DIST-${s.state.slice(0, 2)}-${idx + 1}`, name: d, state: s.state });
        });
      }
    });
    return fetchJson(url, { items: fallbackItems, total: fallbackItems.length });
  },

  // Habitations
  async getHabitations(filters?: { district?: string; state?: string; riskCategory?: string; urgency?: string; bbox?: string }): Promise<{ data: { items: Habitation[]; total: number }; isLive: boolean }> {
    const params = new URLSearchParams();
    if (filters?.district) params.append('district', filters.district);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.riskCategory) params.append('riskCategory', filters.riskCategory);
    if (filters?.urgency) params.append('urgency', filters.urgency);
    if (filters?.bbox) params.append('bbox', filters.bbox);

    const query = params.toString() ? `?${params.toString()}` : '';
    let filtered = mockHabitations;
    if (filters?.district) filtered = filtered.filter((h) => h.district === filters.district);
    if (filters?.riskCategory) filtered = filtered.filter((h) => h.riskCategory === filters.riskCategory);
    if (filters?.urgency) filtered = filtered.filter((h) => h.urgency === filters.urgency);

    return fetchJson(`/api/habitations${query}`, { items: filtered, total: filtered.length });
  },

  async getHabitationById(id: string): Promise<{ data: Habitation | null; isLive: boolean }> {
    const fallback = mockHabitations.find((h) => h.id === id) || null;
    return fetchJson(`/api/habitations/${id}`, fallback);
  },

  // Hazard Zones (Red Zones)
  async getHazardZones(bbox?: string): Promise<{ data: { items: RedZone[]; total: number }; isLive: boolean }> {
    const query = bbox ? `?bbox=${encodeURIComponent(bbox)}` : '';
    return fetchJson(`/api/hazard-zones${query}`, { items: mockRedZones, total: mockRedZones.length });
  },

  // Candidate Sites
  async getCandidateSites(district?: string, bbox?: string): Promise<{ data: { items: CandidateRelocationSite[]; total: number }; isLive: boolean }> {
    const params = new URLSearchParams();
    if (district) params.append('district', district);
    if (bbox) params.append('bbox', bbox);
    const query = params.toString() ? `?${params.toString()}` : '';
    const filtered = district ? mockCandidateSites.filter((c) => c.district === district) : mockCandidateSites;
    return fetchJson(`/api/candidate-sites${query}`, { items: filtered, total: filtered.length });
  },

  // Infrastructure
  async getInfrastructure(type?: string, bbox?: string): Promise<{ data: { items: InfrastructurePoint[]; total: number }; isLive: boolean }> {
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    if (bbox) params.append('bbox', bbox);
    const query = params.toString() ? `?${params.toString()}` : '';
    const filtered = type ? mockInfrastructure.filter((i) => i.type === type) : mockInfrastructure;
    return fetchJson(`/api/infrastructure${query}`, { items: filtered, total: filtered.length });
  },

  // Data Sources
  async getDataSources(): Promise<{ data: { items: DataSourceItem[]; total: number }; isLive: boolean }> {
    return fetchJson('/api/data-sources', {
      items: [
        {
          id: 'DS-001',
          name: 'CartoSAT Elevation Matrix (10m DEM - Synthetic Benchmark)',
          provider: 'ISRO NRSC (Format Benchmark)',
          type: 'RASTER_DEM',
          status: 'DEMO_ACTIVE',
          lastSync: '2026-09-28 04:30 IST',
          recordsCount: 14200,
          latencyMs: 42,
          dataMode: 'DEMO',
        },
        {
          id: 'DS-002',
          name: 'Automatic Weather Station Feed (Synthetic Prototype Stream)',
          provider: 'IMD (Format Benchmark)',
          type: 'WEATHER_STATION',
          status: 'DEMO_ACTIVE',
          lastSync: '2026-09-28 05:45 IST',
          recordsCount: 312,
          latencyMs: 18,
          dataMode: 'DEMO',
        },
      ],
      total: 2,
    });
  },

  // Disaster Events
  async getDisasterEvents(): Promise<{ data: { items: DisasterEventItem[]; total: number }; isLive: boolean }> {
    return fetchJson('/api/disaster-events', {
      items: [
        {
          id: 'EVT-001',
          title: '2021 Chamoli Glacial Flash Flood',
          hazardType: 'FLOOD',
          severity: 'CRITICAL',
          eventDate: '2021-02-07',
          district: 'Chamoli',
          fatalities: 204,
          displacedPersons: 1450,
          description: 'Rishi Ganga / Dhauli Ganga gorge flash flood triggered by rock and ice avalanche from Ronti peak.',
          dataMode: 'DEMO',
        },
        {
          id: 'EVT-002',
          title: '2023 Joshimath Land Subsidence Crisis',
          hazardType: 'LANDSLIDE',
          severity: 'CRITICAL',
          eventDate: '2023-01-05',
          district: 'Chamoli',
          fatalities: 0,
          displacedPersons: 870,
          description: 'Structural cracks and massive ground subsidence affecting over 800 buildings in Joshimath municipal area.',
          dataMode: 'DEMO',
        },
      ],
      total: 2,
    });
  },

  // Metrics Summary
  async getMetricsSummary(): Promise<{ data: MetricsSummary; isLive: boolean }> {
    return fetchJson('/api/metrics/summary', {
      total_habitations: mockHabitations.length,
      critical_habitations: mockHabitations.filter((h) => h.riskCategory === 'CRITICAL').length,
      high_habitations: mockHabitations.filter((h) => h.riskCategory === 'HIGH').length,
      total_population_at_risk: mockHabitations
        .filter((h) => h.riskCategory === 'CRITICAL' || h.riskCategory === 'HIGH')
        .reduce((acc, h) => acc + h.population, 0),
      active_red_zones: mockRedZones.length,
      candidate_sites: mockCandidateSites.length,
      pending_relocations: mockPriorities.filter((p) => !p.assignedSiteId).length,
      field_verifications_pending: mockHabitations.filter((h) => h.verificationStatus === 'PENDING').length,
    });
  },

  // GeoJSON Endpoints
  async getHabitationsGeoJson(bbox?: string): Promise<{ data: GeoJSON.FeatureCollection; isLive: boolean }> {
    const query = bbox ? `?bbox=${encodeURIComponent(bbox)}` : '';
    const fallback: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: mockHabitations.map((h) => ({
        type: 'Feature',
        id: h.id,
        geometry: {
          type: 'Point',
          coordinates: [h.position.lng, h.position.lat],
        },
        properties: {
          name: h.name,
          district: h.district,
          riskScore: h.riskScore,
          riskCategory: h.riskCategory,
          urgency: h.urgency,
          population: h.population,
        },
      })),
    };
    return fetchJson(`/api/habitations/geojson${query}`, fallback);
  },

  async getHazardZonesGeoJson(bbox?: string): Promise<{ data: GeoJSON.FeatureCollection; isLive: boolean }> {
    const query = bbox ? `?bbox=${encodeURIComponent(bbox)}` : '';
    const fallback: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: mockRedZones.map((rz) => ({
        type: 'Feature',
        id: rz.id,
        geometry: {
          type: 'Polygon',
          coordinates: [[...rz.bounds.map((b) => [b.lng, b.lat]), [rz.bounds[0].lng, rz.bounds[0].lat]]],
        },
        properties: {
          name: rz.name,
          compositeRiskScore: rz.compositRiskScore,
          hazardTypes: rz.hazardTypes,
          populationAffected: rz.populationAffected,
          areaKmSq: rz.areaKmSq,
        },
      })),
    };
    return fetchJson(`/api/hazard-zones/geojson${query}`, fallback);
  },

  // Relocation Priorities (with need and readiness integration)
  async getRelocationPriorities(filters?: { district?: string; urgency?: string }): Promise<{ data: { items: RelocationPriority[]; total: number }; isLive: boolean }> {
    const params = new URLSearchParams();
    if (filters?.district) params.append('district', filters.district);
    if (filters?.urgency) params.append('urgency', filters.urgency);
    const query = params.toString() ? `?${params.toString()}` : '';
    let filtered = mockPriorities;
    if (filters?.district) filtered = filtered.filter((p) => p.district === filters.district);
    if (filters?.urgency) filtered = filtered.filter((p) => p.urgency === filters.urgency);
    return fetchJson(`/api/relocation-priorities${query}`, { items: filtered, total: filtered.length });
  },

  // Habitation Risk Intelligence
  async getHabitationRisk(id: string): Promise<{ data: RiskAssessmentData | null; isLive: boolean }> {
    return fetchJson<RiskAssessmentData | null>(`/api/habitations/${id}/risk`, null);
  },

  async getHabitationRiskExplanation(id: string): Promise<{ data: RiskExplanationData | null; isLive: boolean }> {
    return fetchJson<RiskExplanationData | null>(`/api/habitations/${id}/risk/explanation`, null);
  },

  // Habitation Relocation Assessment
  async getHabitationRelocation(id: string): Promise<{ data: RelocationAssessmentData | null; isLive: boolean }> {
    return fetchJson<RelocationAssessmentData | null>(`/api/habitations/${id}/relocation`, null);
  },

  // Red Zones Intelligence
  async getRedZonesIntelligence(): Promise<{ data: { red_zones: RedZoneIntelligenceItem[]; total: number; breakdown_by_classification: Record<string, number> }; isLive: boolean }> {
    const fallbackItems: RedZoneIntelligenceItem[] = mockRedZones.map((rz) => ({
      id: rz.id,
      name: rz.name,
      classification: rz.classification || (rz.compositRiskScore >= 80 ? 'PERMANENT_RED' : 'CONDITIONAL_RED'),
      composite_risk_score: rz.compositRiskScore,
      dominant_hazard: rz.hazardTypes[0] || 'LANDSLIDE',
      habitation_count: rz.habitationCount,
      population_affected: rz.populationAffected,
      computed_area_sq_km: rz.areaKmSq,
      source_declared_area_sq_km: rz.areaKmSq,
      reason_codes: ['MONITORED_HAZARD_ZONE'],
      requires_field_verification: false,
    }));

    const res = await fetchJson<{ items: RedZone[]; total: number }>('/api/red-zones', {
      items: mockRedZones,
      total: mockRedZones.length,
    });

    const red_zones: RedZoneIntelligenceItem[] = (res.data.items || []).map((rz) => ({
      id: rz.id,
      name: rz.name,
      classification: rz.classification || (rz.compositRiskScore >= 80 ? 'PERMANENT_RED' : 'CONDITIONAL_RED'),
      composite_risk_score: rz.compositRiskScore,
      dominant_hazard: rz.hazardTypes[0] || 'LANDSLIDE',
      habitation_count: rz.habitationCount,
      population_affected: rz.populationAffected,
      computed_area_sq_km: rz.computedAreaSqKm || rz.areaKmSq,
      source_declared_area_sq_km: rz.sourceDeclaredAreaSqKm || rz.areaKmSq,
      reason_codes: ['MONITORED_HAZARD_ZONE'],
      requires_field_verification: false,
    }));

    const breakdown: Record<string, number> = {};
    red_zones.forEach((rz) => {
      breakdown[rz.classification] = (breakdown[rz.classification] || 0) + 1;
    });

    return {
      data: {
        red_zones,
        total: res.data.total ?? red_zones.length,
        breakdown_by_classification: breakdown,
      },
      isLive: res.isLive,
    };
  },

  // Data Sources Freshness & Telemetry
  async getDataSourcesFreshness(): Promise<{ data: { items: DataSourceFreshnessItem[]; total: number; stale_count: number }; isLive: boolean }> {
    return fetchJson('/api/data-sources/freshness', {
      items: [
        {
          id: 'SRC-OSM-INFRA',
          name: 'OpenStreetMap Critical Infrastructure',
          provider: 'OpenStreetMap Foundation (Format Benchmark)',
          type: 'OSM_VECTOR',
          freshness: 'UNKNOWN',
          lastSuccessfulIngestion: 'UNKNOWN',
          expectedRefreshSeconds: 86400,
          dataMode: 'DEMO',
          isStale: false,
        },
        {
          id: 'SRC-OPEN-METEO',
          name: 'Open-Meteo Mountain Weather Stream',
          provider: 'Open-Meteo / ECMWF (Format Benchmark)',
          type: 'WEATHER_STATION',
          freshness: 'UNKNOWN',
          lastSuccessfulIngestion: 'UNKNOWN',
          expectedRefreshSeconds: 3600,
          dataMode: 'DEMO',
          isStale: false,
        },
        {
          id: 'SRC-ALOS-PALSAR',
          name: 'ALOS PALSAR 12.5m Metric DEM',
          provider: 'JAXA / ASF DAAC (Format Benchmark)',
          type: 'RASTER_DEM',
          freshness: 'UNKNOWN',
          lastSuccessfulIngestion: 'UNKNOWN',
          expectedRefreshSeconds: 31536000,
          dataMode: 'DEMO',
          isStale: false,
        },
      ],
      total: 3,
      stale_count: 0,
    });
  },

  // Derived Scientific Evidence Layers
  async getEvidenceLayers(): Promise<{ data: { items: EvidenceLayerItem[]; total: number }; isLive: boolean }> {
    return fetchJson('/api/data-sources/evidence-layers', {
      items: [
        {
          id: 'EV-ELEV-SRTM30',
          name: 'CartoSAT / SRTM 30m Digital Elevation Model',
          evidence_type: 'ELEVATION',
          data_mode: 'PUBLIC',
          representation_type: 'RASTER',
          spatial_resolution: 30.0,
          derivation_method: 'Direct satellite radar interferometry acquisition via ISRO / USGS',
          quality_score: 92.0,
        },
        {
          id: 'EV-SLOPE-METRIC',
          name: 'Metric Slope Gradient (Degrees)',
          evidence_type: 'SLOPE',
          data_mode: 'MODELED',
          representation_type: 'RASTER',
          spatial_resolution: 30.0,
          derivation_method: 'Horn (1981) metric finite-difference gradient with latitude-adjusted cell metric conversion',
          parent_layer_ids: ['EV-ELEV-SRTM30'],
          quality_score: 88.0,
        },
        {
          id: 'EV-ASPECT-METRIC',
          name: 'Terrain Aspect (Compass Orientation)',
          evidence_type: 'ASPECT',
          data_mode: 'MODELED',
          representation_type: 'RASTER',
          spatial_resolution: 30.0,
          derivation_method: 'Zevenbergen-Thorne / Horn metric compass direction (0-360 degrees)',
          parent_layer_ids: ['EV-ELEV-SRTM30'],
          quality_score: 88.0,
        },
        {
          id: 'EV-DIST-ROAD',
          name: 'Proximity to Road Network',
          evidence_type: 'DISTANCE_TO_ROAD',
          data_mode: 'MODELED',
          representation_type: 'VECTOR',
          spatial_resolution: 10.0,
          derivation_method: 'PostGIS ST_Distance planar metric calculation from highway lines',
          quality_score: 85.0,
        },
        {
          id: 'EV-DIST-DRAINAGE',
          name: 'Distance to Drainage / River Channels',
          evidence_type: 'DISTANCE_TO_DRAINAGE',
          data_mode: 'MODELED',
          representation_type: 'VECTOR',
          spatial_resolution: 15.0,
          derivation_method: 'Hydrological stream network vector buffer and proximity analysis',
          quality_score: 85.0,
        },
        {
          id: 'EV-DIST-FAULT',
          name: 'Distance to Tectonic Fault Lineaments',
          evidence_type: 'DISTANCE_TO_FAULT',
          data_mode: 'MODELED',
          representation_type: 'VECTOR',
          spatial_resolution: 50.0,
          derivation_method: 'Geological Survey of India structural fault and thrust zone proximity',
          quality_score: 80.0,
        },
      ],
      total: 6,
    });
  },

  // ── Candidate Relocation Discovery (Task 6) ──
  async runCandidateDiscovery(
    habitationId: string,
    params?: {
      search_radius_km?: number;
      min_parcel_area_hectares?: number;
      max_slope_degrees?: number;
    }
  ): Promise<{ data: CandidateDiscoveryRunResponse; isLive: boolean }> {
    return postAnalysisJson<CandidateDiscoveryRunResponse>(
      `/api/analysis/candidates/habitations/${habitationId}`,
      params || { search_radius_km: 15.0, min_parcel_area_hectares: 2.0, max_slope_degrees: 25.0 }
    );
  },

  async getCandidateParcels(params?: {
    run_id?: string;
    habitation_id?: string;
    min_suitability?: number;
    status?: string;
  }): Promise<{ data: { items: CandidateParcelItem[]; total: number }; isLive: boolean }> {
    const searchParams = new URLSearchParams();
    if (params?.run_id) searchParams.set('run_id', params.run_id);
    if (params?.habitation_id) searchParams.set('habitation_id', params.habitation_id);
    if (params?.min_suitability !== undefined) searchParams.set('min_suitability', params.min_suitability.toString());
    if (params?.status) searchParams.set('status', params.status);

    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return fetchJson(`/api/candidate-parcels${query}`, { items: [], total: 0 });
  },

  async getCandidateParcel(parcelId: string): Promise<{ data: CandidateParcelItem | null; isLive: boolean }> {
    return fetchJson(`/api/candidate-parcels/${parcelId}`, null as any);
  },

  async getCandidateParcelsGeoJson(params?: {
    run_id?: string;
    habitation_id?: string;
  }): Promise<{ data: GeoJSON.FeatureCollection; isLive: boolean }> {
    const searchParams = new URLSearchParams();
    if (params?.run_id) searchParams.set('run_id', params.run_id);
    if (params?.habitation_id) searchParams.set('habitation_id', params.habitation_id);

    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return fetchJson(`/api/candidate-parcels/geojson${query}`, {
      type: 'FeatureCollection',
      features: [],
    });
  },

  async getCandidateDiscoveryRuns(habitationId: string): Promise<{ data: CandidateDiscoveryRunResponse[]; isLive: boolean }> {
    return fetchJson(`/api/habitations/${habitationId}/candidate-discovery-runs`, []);
  },

  // ── TASK 8: MULTI-SITE RELOCATION OPTIMIZATION ──

  async runRelocationOptimization(
    habitationId: string,
    params?: {
      mode?: 'EXPLORATORY' | 'DECISION_SUPPORT';
      target_population?: number;
      max_sites?: number;
      min_allocation_size?: number;
      include_demo_candidates?: boolean;
      include_benchmark_sites?: boolean;
      objective_weights?: Record<string, number>;
    }
  ): Promise<{ data: RelocationOptimizationRunResponse; isLive: boolean }> {
    return postAnalysisJson<RelocationOptimizationRunResponse>(
      '/api/optimization/run',
      {
        origin_habitation_id: habitationId,
        mode: params?.mode || 'EXPLORATORY',
        target_population: params?.target_population,
        max_sites: params?.max_sites,
        min_allocation_size: params?.min_allocation_size || 50,
        include_demo_candidates: params?.include_demo_candidates ?? false,
        include_benchmark_sites: params?.include_benchmark_sites ?? false,
        objective_weights: params?.objective_weights,
      }
    );
  },

  async getRelocationOptimizationRuns(habitationId: string): Promise<{ data: RelocationPlanItem[]; isLive: boolean }> {
    return fetchJson<RelocationPlanItem[]>(`/api/optimization/habitations/${habitationId}/latest-plans`, []);
  },

  async getRelocationPlans(runId: string): Promise<{ data: RelocationPlanItem[]; isLive: boolean }> {
    const res = await fetchJson<RelocationOptimizationRunResponse>(`/api/optimization/runs/${runId}`, {
      run_id: runId,
      origin_habitation_id: '',
      analysis_version: '',
      config_version: '',
      mode: '',
      target_population: 0,
      solver_status: '',
      candidates_considered_count: 0,
      usable_candidates_count: 0,
      plans: [],
    });
    return { data: res.data?.plans || [], isLive: res.isLive };
  },

  async getRelocationPlanById(planId: string): Promise<{ data: RelocationPlanItem | null; isLive: boolean }> {
    return fetchJson<RelocationPlanItem | null>(`/api/optimization/plans/${planId}`, null);
  },

  // ── TASK 9: DIGITAL TWIN & SCENARIO LAB ──

  async runDigitalTwinSimulation(
    planId: string,
    params?: {
      scenario_name?: string;
      parameters?: ScenarioParameters;
    }
  ): Promise<{ data: DigitalTwinSimulationResponse; isLive: boolean }> {
    return postAnalysisJson<DigitalTwinSimulationResponse>(
      '/api/digital-twin/simulate',
      {
        plan_id: planId,
        scenario_name: params?.scenario_name || 'CUSTOM_SCENARIO',
        parameters: params?.parameters || {},
      }
    );
  },

  async evaluatePlanRobustness(planId: string): Promise<{ data: PlanRobustnessResponse; isLive: boolean }> {
    return postAnalysisJson<PlanRobustnessResponse>(
      `/api/digital-twin/plans/${planId}/robustness`,
      {}
    );
  },

  // ── TASK 10: GOVERNANCE, FIELD EVIDENCE & DECISION DOSSIER ──

  async getDemoSnapshotRaini(): Promise<{ data: any; isLive: boolean }> {
    return fetchJson('/api/governance/demo-snapshot/raini', null);
  },

  async getHabitationDossier(habitationId: string): Promise<{ data: DecisionDossierResponse | null; isLive: boolean }> {
    return fetchJson<DecisionDossierResponse | null>(`/api/governance/habitations/${habitationId}/dossier`, null);
  },

  getHabitationDossierHtmlUrl(habitationId: string): string {
    return `${API_BASE_URL}/api/governance/habitations/${habitationId}/dossier/html`;
  },

  async getDataHonestyAudit(): Promise<{ data: DataHonestyAuditResponse | null; isLive: boolean }> {
    return fetchJson<DataHonestyAuditResponse | null>('/api/governance/data-honesty-audit', null);
  },

  async getGovernanceObservations(entityType: string, entityId: string): Promise<{ data: FieldObservationItem[]; isLive: boolean }> {
    return fetchJson<FieldObservationItem[]>(
      `/api/governance/observations?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}`,
      []
    );
  },

  async createGovernanceObservation(observation: Partial<FieldObservationItem>): Promise<{ data: FieldObservationItem; isLive: boolean }> {
    return postAnalysisJson<FieldObservationItem>('/api/governance/observations', observation);
  },

  async verifyGovernanceObservation(
    observationId: string,
    verification: { verification_level: string; verified_by: string; technical_notes?: string }
  ): Promise<{ data: FieldObservationItem; isLive: boolean }> {
    return postAnalysisJson<FieldObservationItem>(`/api/governance/observations/${observationId}/verify`, verification);
  },

  async getGovernanceLandStatus(parcelCandidateId: string): Promise<{ data: LandStatusItem[]; isLive: boolean }> {
    return fetchJson<LandStatusItem[]>(
      `/api/governance/land-status?parcel_candidate_id=${encodeURIComponent(parcelCandidateId)}`,
      []
    );
  },

  async createGovernanceLandStatus(landStatus: Partial<LandStatusItem>): Promise<{ data: LandStatusItem; isLive: boolean }> {
    return postAnalysisJson<LandStatusItem>('/api/governance/land-status', landStatus);
  },

  async getGovernanceConsultations(habitationId: string): Promise<{ data: ConsultationItem[]; isLive: boolean }> {
    return fetchJson<ConsultationItem[]>(
      `/api/governance/consultations?habitation_id=${encodeURIComponent(habitationId)}`,
      []
    );
  },

  async createGovernanceConsultation(consultation: Partial<ConsultationItem>): Promise<{ data: ConsultationItem; isLive: boolean }> {
    return postAnalysisJson<ConsultationItem>('/api/governance/consultations', consultation);
  },

  async getGovernanceReviews(entityType: string, entityId: string): Promise<{ data: GovernanceReviewItem[]; isLive: boolean }> {
    return fetchJson<GovernanceReviewItem[]>(
      `/api/governance/reviews?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}`,
      []
    );
  },

  async createGovernanceReview(review: Partial<GovernanceReviewItem>): Promise<{ data: GovernanceReviewItem; isLive: boolean }> {
    return postAnalysisJson<GovernanceReviewItem>('/api/governance/reviews', review);
  },

  async getGovernanceOverrides(entityType: string, entityId: string): Promise<{ data: AnalyticalOverrideItem[]; isLive: boolean }> {
    return fetchJson<AnalyticalOverrideItem[]>(
      `/api/governance/overrides?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}`,
      []
    );
  },

  async createGovernanceOverride(override: Partial<AnalyticalOverrideItem>): Promise<{ data: AnalyticalOverrideItem; isLive: boolean }> {
    return postAnalysisJson<AnalyticalOverrideItem>('/api/governance/overrides', override);
  },

  async getGovernanceAuditLogs(limit: number = 50): Promise<{ data: AuditLogItem[]; isLive: boolean }> {
    return fetchJson<AuditLogItem[]>(`/api/governance/audit-logs?limit=${limit}`, []);
  },
};


