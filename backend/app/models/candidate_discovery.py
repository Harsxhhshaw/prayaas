"""ORM models for Automated GIS Relocation Candidate Discovery — Runs and Parcels."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import CandidateDiscoveryStatus, DataMode, ParcelStatus


class CandidateDiscoveryRun(Base, TimestampMixin):
    """Tracks an automated spatial suitability & candidate discovery analysis run."""

    __tablename__ = "candidate_discovery_runs"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"CDR-{uuid.uuid4().hex[:12].upper()}",
    )
    origin_habitation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("habitations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PRAYAAS-CANDIDATE-1.0",
        index=True,
    )
    config_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
    )
    search_radius_km: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)

    # Spatial AOI representation
    aoi_geometry = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CandidateDiscoveryStatus.QUEUED.value,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    analysis_resolution_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_source_resolution_meters: Mapped[float | None] = mapped_column(Float, nullable=True)

    cells_evaluated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cells_excluded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_aoi_area_sq_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    excluded_area_sq_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    feasible_area_sq_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    feasible_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    candidate_eligible_cells: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candidate_eligible_area_sq_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_metadata: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # Relationships
    origin_habitation = relationship("Habitation", backref="candidate_discovery_runs")
    parcels = relationship(
        "CandidateParcel",
        back_populates="discovery_run",
        cascade="all, delete-orphan",
        order_by="CandidateParcel.rank",
    )

    def __repr__(self) -> str:
        return f"<CandidateDiscoveryRun id={self.id!r} hab={self.origin_habitation_id!r} status={self.status!r}>"


class CandidateParcel(Base, TimestampMixin):
    """Contiguous feasible land parcel surviving safety exclusions and evaluated via MCDA."""

    __tablename__ = "candidate_parcels"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"PARCEL-{uuid.uuid4().hex[:12].upper()}",
    )
    discovery_run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("candidate_discovery_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    origin_habitation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("habitations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Canonical Spatial Representation (MultiPolygon for disconnected islands if unioned) ──
    geom = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )
    centroid = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    area_sq_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    area_hectares: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    distance_from_origin_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mean_slope_degrees: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)

    # ── Multi-Criteria Evaluation & Ranking ──
    suitability_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        index=True,
        doc="Composite MCDA suitability 0-100",
    )
    robustness_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Ranking stability under weight perturbation 0-100",
    )
    rank_stability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Percentage of Monte Carlo runs retaining #1 rank",
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ParcelStatus.PRELIMINARY.value,
        index=True,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=50.0,
        doc="Confidence accounting for data completeness & resolution 0-100",
    )

    # ── Auditability, Exclusions & Limitations ──
    exclusion_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Status of hard exclusions (PASS, FAIL, UNKNOWN, NOT_APPLICABLE)",
    )
    criteria_scores: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Normalized 0-100 individual criterion scores",
    )
    reason_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    source_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.MODELED.value,
        index=True,
    )

    # Relationships
    discovery_run = relationship("CandidateDiscoveryRun", back_populates="parcels")
    origin_habitation = relationship("Habitation")

    def __repr__(self) -> str:
        return f"<CandidateParcel id={self.id!r} rank={self.rank} suit={self.suitability_score:.1f}>"
