"""Pydantic v2 schemas for Relocation Assessment and Prioritization."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RelocationAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    habitation_id: str
    habitation_name: str | None = None
    risk_assessment_id: str | None = None
    analysis_version: str
    config_version: str
    need_score: float
    urgency: str
    readiness_score: float
    readiness_level: str
    need_components: dict[str, Any] = Field(default_factory=dict)
    readiness_components: dict[str, Any] = Field(default_factory=dict)
    readiness_gaps: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    explanation: str
    confidence_score: float
    calculated_at: str


class RelocationAssessmentHistoryItem(BaseModel):
    id: str
    need_score: float
    urgency: str
    readiness_score: float
    readiness_level: str
    calculated_at: str


class RelocationAssessmentHistoryResponse(BaseModel):
    habitation_id: str
    history: list[RelocationAssessmentHistoryItem]


class RelocationPrioritySummaryResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    immediate_count: int
    short_term_count: int
    medium_term_count: int
    monitor_count: int
