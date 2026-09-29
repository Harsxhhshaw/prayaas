"""Pydantic schemas for Task 10 Governance, Field Evidence, Land Status, Document AI, and Decision Dossiers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


# ── Field Observations ──

class FieldObservationCreate(BaseModel):
    entity_type: Literal["HABITATION", "HAZARD_ZONE", "CANDIDATE_PARCEL", "CANDIDATE_SITE"]
    entity_id: str
    observation_type: str = "SLOPE_INSTABILITY"
    latitude: float | None = None
    longitude: float | None = None
    observer_name: str | None = None
    observer_role: str | None = None
    notes: str = ""
    evidence_values: dict[str, Any] = Field(default_factory=dict)
    attachments_metadata: dict[str, Any] = Field(default_factory=dict)
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class FieldObservationVerifyRequest(BaseModel):
    verification_level: Literal["TECHNICALLY_VERIFIED", "AUTHORITY_REVIEWED"]
    verified_by: str
    technical_notes: str = ""


class FieldObservationResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    observation_type: str
    observed_at: datetime
    observer_name: str | None = None
    observer_role: str | None = None
    notes: str
    evidence_values: dict[str, Any] = Field(default_factory=dict)
    data_mode: str = "FIELD"
    verification_level: str
    verified_by: str | None = None
    verified_at: datetime | None = None
    technical_notes: str | None = None
    attachments_metadata: dict[str, Any] = Field(default_factory=dict)
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# ── Land & Legal Status ──

class LandStatusCreate(BaseModel):
    parcel_candidate_id: str
    category: str = "LAND_OWNERSHIP"
    status: str = "UNKNOWN"
    source_reference: str | None = None
    document_reference: str | None = None
    reviewed_by: str | None = None
    notes: str | None = None
    data_mode: str = "PUBLIC"


class LandStatusResponse(BaseModel):
    id: str
    parcel_candidate_id: str
    category: str
    status: str
    source_reference: str | None = None
    document_reference: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    notes: str | None = None
    data_mode: str
    created_at: datetime


# ── Community Consultation ──

class ConsultationCreate(BaseModel):
    habitation_id: str
    participant_count: int = 0
    method: str = "GRAM_SABHA"
    questions_responses: dict[str, Any] = Field(default_factory=dict)
    concerns: list[str] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)
    source_attachment: dict[str, Any] = Field(default_factory=dict)
    data_mode: str = "DEMO"


class ConsultationResponse(BaseModel):
    id: str
    habitation_id: str
    consultation_date: datetime
    participant_count: int
    method: str
    questions_responses: dict[str, Any] = Field(default_factory=dict)
    concerns: list[str] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)
    source_attachment: dict[str, Any] = Field(default_factory=dict)
    verification_status: str
    data_mode: str
    created_at: datetime


# ── Governance Review ──

class GovernanceReviewCreate(BaseModel):
    entity_type: str
    entity_id: str
    review_stage: str
    assigned_to: str | None = None
    reviewer_role: str | None = None
    review_notes: str | None = None
    action_taken: str | None = None


class GovernanceReviewResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    review_stage: str
    assigned_to: str | None = None
    reviewer_role: str | None = None
    review_notes: str | None = None
    action_taken: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Human Analytical Override ──

class AnalyticalOverrideCreate(BaseModel):
    entity_type: Literal["HABITATION", "RISK_ASSESSMENT", "CANDIDATE_PARCEL", "RELOCATION_PLAN"]
    entity_id: str
    field_name: str
    original_value: str
    override_value: str
    reason: str
    reviewer: str


class AnalyticalOverrideResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    field_name: str
    original_value: str
    override_value: str
    reason: str
    reviewer: str
    timestamp: datetime


# ── Audit Log ──

class AuditLogItemResponse(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: str
    user_id: str
    details: dict[str, Any]
    timestamp: datetime


# ── Document AI ──

class DocumentExtractionRequest(BaseModel):
    document_name: str
    document_type: str = "GEOTECHNICAL_REPORT"
    raw_text: str
    source_reference: str | None = None


class DocumentExtractionResponse(BaseModel):
    id: str
    document_name: str
    document_type: str
    status: str
    ai_enabled: bool
    extracted_fields: dict[str, Any]
    source_reference: str | None = None
    message: str


class DocumentConfirmRequest(BaseModel):
    confirmed_by: str
    edited_fields: dict[str, Any] | None = None
    action: Literal["CONFIRM", "REJECT"] = "CONFIRM"


# ── Decision Dossier ──

class DecisionDossierResponse(BaseModel):
    habitation_id: str
    habitation_name: str
    district: str
    state: str
    dossier_id: str
    generated_at: datetime
    analysis_version: str
    config_version: str
    executive_summary: str
    risk_profile: dict[str, Any]
    relocation_assessment: dict[str, Any]
    candidate_land_discovery: dict[str, Any]
    candidate_comparison: list[dict[str, Any]]
    carrying_capacity: dict[str, Any]
    relocation_alternatives: list[dict[str, Any]]
    scenario_robustness: dict[str, Any]
    evidence_data_quality: dict[str, Any]
    verification_required: list[str]
    provenance: dict[str, Any]
    disclaimer: str


# ── Data Honesty Audit ──

class DataHonestyAuditResponse(BaseModel):
    counts_by_mode: dict[str, int]
    table_breakdown: dict[str, dict[str, int]]
    ml_status: dict[str, str]
    timestamp: datetime
