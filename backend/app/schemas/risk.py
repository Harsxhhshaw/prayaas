"""Pydantic v2 schemas for Risk Assessment and Vulnerability Profiles."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class VulnerabilityProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    habitation_id: str
    population: int
    households: int
    children_share: float
    elderly_share: float
    disability_share: float
    housing_vulnerability: float
    population_density: float
    healthcare_access_score: float
    road_access_score: float
    isolation_score: float
    data_confidence: float
    data_mode: str
    raw_attributes: dict[str, Any] = Field(default_factory=dict)


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    habitation_id: str
    habitation_name: str | None = None
    analysis_version: str
    config_version: str
    baseline_hazard_score: float
    dynamic_hazard_score: float
    hazard_score: float
    exposure_score: float
    vulnerability_score: float
    adaptive_capacity_score: float
    adaptive_capacity_deficit_score: float
    history_score: float
    trend_score: float
    compound_hazard_adjustment: float
    baseline_structural_risk: float
    current_dynamic_risk: float
    composite_risk_score: float
    risk_classification: str
    confidence_score: float
    dominant_hazard: str
    sustainability_index: float
    reason_codes: list[str] = Field(default_factory=list)
    explanation: str
    calculated_at: str


class RiskAssessmentExplanationResponse(BaseModel):
    id: str
    habitation_id: str
    habitation_name: str
    composite_risk_score: float
    risk_classification: str
    confidence_score: float
    dominant_hazard: str
    sustainability_index: float
    formula: str
    component_weights: dict[str, float]
    component_values: dict[str, float]
    compound_hazard_adjustment: float
    reason_codes: list[str]
    narrative_explanation: str
    sources_used: list[dict[str, Any]]
    confidence_rationale: str
    calculated_at: str


class RiskAssessmentHistoryItem(BaseModel):
    id: str
    composite_risk_score: float
    risk_classification: str
    confidence_score: float
    hazard_score: float
    vulnerability_score: float
    calculated_at: str


class RiskAssessmentHistoryResponse(BaseModel):
    habitation_id: str
    history: list[RiskAssessmentHistoryItem]


class RedZoneEvaluationItem(BaseModel):
    id: str
    name: str
    classification: str
    composite_risk_score: float
    dominant_hazard: str
    confidence_score: float
    habitation_count: int
    population_affected: int
    computed_area_sq_km: float | None = None
    source_declared_area_sq_km: float | None = None
    reason_codes: list[str]
    requires_field_verification: bool


class RedZoneIntelligenceResponse(BaseModel):
    red_zones: list[RedZoneEvaluationItem]
    total: int
    breakdown_by_classification: dict[str, int]
