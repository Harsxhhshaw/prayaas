"""Shared Pydantic v2 types used across multiple schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GeoPointResponse(BaseModel):
    """Latitude / longitude pair matching frontend GeoPoint."""

    lat: float
    lng: float


class HazardScoreResponse(BaseModel):
    type: str
    score: int | None = None
    label: str
    status: str = "VALUE"



class RiskHistoryEntryResponse(BaseModel):
    year: int
    score: int


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int


class PaginatedResponse(BaseModel):
    """Generic paginated envelope."""

    model_config = ConfigDict(from_attributes=True)

    meta: PaginationMeta
    items: list


class MetricsSummaryResponse(BaseModel):
    """Aggregate KPI metrics for the command centre."""

    total_habitations: int
    critical_habitations: int
    high_habitations: int
    total_population_at_risk: int
    active_red_zones: int
    candidate_sites: int
    pending_relocations: int
    field_verifications_pending: int
