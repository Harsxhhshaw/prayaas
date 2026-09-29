"""ORM models for Field Evidence, Land Status, Governance Reviews, Human Overrides, and Decision Dossiers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    DataMode,
    FieldObservationType,
    GovernanceReviewStage,
    LandCategory,
    LandStatus,
    VerificationLevel,
    VerificationStatus,
)


class FieldObservation(Base, TimestampMixin):
    """Ground-truth observational evidence collected by field teams."""

    __tablename__ = "field_observations"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"OBS-{uuid.uuid4().hex[:12].upper()}",
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # HABITATION, HAZARD_ZONE, CANDIDATE_PARCEL, CANDIDATE_SITE
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    observation_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        default=FieldObservationType.SLOPE_INSTABILITY.value,
    )
    geom: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    observer_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    observer_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_values: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    data_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DataMode.FIELD.value,
    )
    verification_level: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=VerificationLevel.FIELD_OBSERVED.value,
    )
    verified_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    technical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<FieldObservation {self.id}: {self.observation_type} on {self.entity_type}:{self.entity_id}>"


class LandStatusRecord(Base, TimestampMixin):
    """Structured legal, cadastral, and tenure status for candidate parcels and reception sites."""

    __tablename__ = "land_status_records"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"LND-{uuid.uuid4().hex[:12].upper()}",
    )
    parcel_candidate_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=LandCategory.LAND_OWNERSHIP.value,
    )
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=LandStatus.UNKNOWN.value,
    )
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DataMode.PUBLIC.value,
    )

    def __repr__(self) -> str:
        return f"<LandStatusRecord {self.id}: {self.category}={self.status} for {self.parcel_candidate_id}>"


class ConsultationRecord(Base, TimestampMixin):
    """Structured record of public engagement, Gram Sabha hearings, and community consultations."""

    __tablename__ = "consultation_records"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"CNS-{uuid.uuid4().hex[:12].upper()}",
    )
    habitation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    consultation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    method: Mapped[str] = mapped_column(String(64), nullable=False, default="GRAM_SABHA")
    questions_responses: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    concerns: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_attachment: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    verification_status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=VerificationStatus.PENDING.value,
    )
    data_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DataMode.DEMO.value,
    )

    def __repr__(self) -> str:
        return f"<ConsultationRecord {self.id}: {self.habitation_id} ({self.participant_count} participants)>"


class GovernanceReview(Base, TimestampMixin):
    """Formal administrative and technical workflow stage tracking."""

    __tablename__ = "governance_reviews"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"GOV-{uuid.uuid4().hex[:12].upper()}",
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    review_stage: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=GovernanceReviewStage.ANALYTICAL_REVIEW.value,
    )
    assigned_to: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewer_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<GovernanceReview {self.id}: {self.entity_type}:{self.entity_id} -> {self.review_stage}>"


class AnalyticalOverrideRecord(Base):
    """Auditable log of human analytical overrides. Preserves original values."""

    __tablename__ = "analytical_overrides"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"OVR-{uuid.uuid4().hex[:12].upper()}",
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    original_value: Mapped[str] = mapped_column(String(255), nullable=False)
    override_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<AnalyticalOverride {self.id}: {self.field_name} {self.original_value} -> {self.override_value}>"


class DocumentExtractionRecord(Base, TimestampMixin):
    """Proposed vs confirmed structured evidence extracted from disaster or inspection reports."""

    __tablename__ = "document_extractions"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"DOC-{uuid.uuid4().hex[:12].upper()}",
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False, default="GEOTECHNICAL_REPORT")
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")  # PROPOSED, CONFIRMED, EDITED, REJECTED
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<DocumentExtraction {self.id}: {self.document_name} [{self.status}]>"


class DemoSnapshot(Base):
    """Frozen deterministic snapshot of an end-to-end habitation planning analysis."""

    __tablename__ = "demo_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    habitation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<DemoSnapshot {self.snapshot_id}: {self.title}>"
