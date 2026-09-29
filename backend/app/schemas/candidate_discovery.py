"""Pydantic request & response schemas for Candidate Relocation Discovery."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CandidateDiscoveryRunRequest(BaseModel):
    """Parameters for executing an automated candidate land discovery analysis."""

    search_radius_km: float | None = Field(None, ge=1.0, le=50.0, description="Search radius in kilometers (default 15.0)")
    min_parcel_area_hectares: float | None = Field(None, ge=0.5, le=50.0, description="Minimum contiguous area threshold (default 2.0 ha)")
    max_slope_degrees: float | None = Field(None, ge=10.0, le=45.0, description="Maximum permissible terrain slope (default 25.0°)")


class CentroidPoint(BaseModel):
    lat: float
    lng: float


class CandidateParcelResponse(BaseModel):
    """Structured response for a single discovered candidate land parcel."""

    id: str
    discovery_run_id: str
    origin_habitation_id: str
    rank: int
    suitability_score: float
    confidence_score: float
    robustness_score: float
    rank_stability: float
    status: str
    area_sq_km: float
    area_hectares: float
    distance_from_origin_km: float
    mean_slope_degrees: float | None = 0.0
    exclusion_summary: dict[str, Any]
    criteria_scores: dict[str, Any]
    reason_codes: list[str]
    limitations: list[str]
    explanation: dict[str, Any]
    data_mode: str
    centroid: CentroidPoint
    created_at: datetime


class CandidateParcelListResponse(BaseModel):
    """List response for candidate parcels."""

    items: list[CandidateParcelResponse]
    total: int


class CandidateDiscoveryRunResponse(BaseModel):
    """Metadata response for a candidate discovery run."""

    id: str
    origin_habitation_id: str
    analysis_version: str
    config_version: str
    search_radius_km: float
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    analysis_resolution_meters: float | None = None
    effective_source_resolution_meters: float | None = None
    cells_evaluated: int | None = None
    cells_excluded: int | None = None
    total_aoi_area_sq_km: float | None = None
    excluded_area_sq_km: float | None = None
    feasible_area_sq_km: float | None = None
    feasible_percent: float | None = None
    candidate_eligible_cells: int | None = None
    candidate_eligible_area_sq_km: float | None = None
    candidate_count: int
    warning_metadata: list[Any] = Field(default_factory=list)
    created_at: datetime


class DiscoveryExecutionResponse(BaseModel):
    """Response returned upon completing a discovery run."""

    run_id: str
    origin_habitation: dict[str, Any]
    configuration_version: str
    analysis_version: str
    search_radius_km: float
    analysis_resolution_meters: float | None = None
    effective_source_resolution_meters: float | None = None
    cells_evaluated: int
    cells_excluded: int
    feasible_cells: int
    total_aoi_area: float | None = None
    excluded_area: float | None = None
    feasible_area: float | None = None
    feasible_percent: float | None = None
    candidate_eligible_area: float | None = None
    candidate_eligible_cells: int | None = None
    candidate_cores_found: int | None = None
    pre_filter_candidate_regions: int | None = None
    contiguous_regions_found: int | None = None
    regions_rejected_by_min_area: int | None = None
    regions_rejected_by_geometry_quality: int | None = None
    total_rejected: int | None = None
    candidate_parcels_discovered: int
    candidates_rejected_by_area: int
    warnings: list[str]
    top_candidates: list[dict[str, Any]]
    rejection_summary: dict[str, Any]
    duration_seconds: float

