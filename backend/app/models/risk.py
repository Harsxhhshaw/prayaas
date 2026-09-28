"""Risk and Vulnerability ORM models — RiskAssessment and VulnerabilityProfile."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode, RedZoneClassification

if TYPE_CHECKING:
    from app.models.data_source import DataSource
    from app.models.habitation import Habitation
    from app.models.relocation import RelocationAssessment


class VulnerabilityProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Detailed social, structural, and isolation vulnerability attributes for a habitation."""

    __tablename__ = "vulnerability_profiles"

    habitation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("habitations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    population: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    households: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    children_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="Fraction 0-1")
    elderly_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="Fraction 0-1")
    disability_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="Fraction 0-1")
    housing_vulnerability: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, doc="0-100 index (e.g. kuccha construction)"
    )
    population_density: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="Habitants / km²")
    healthcare_access_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0, doc="0-100 access score")
    road_access_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0, doc="0-100 access score")
    isolation_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0, doc="0-100 isolation score")
    data_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=50.0, doc="0-100 survey confidence")
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
    )
    raw_attributes: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Relationships
    habitation: Mapped[Habitation] = relationship("Habitation", back_populates="vulnerability_profile")
    data_source: Mapped[DataSource | None] = relationship("DataSource")

    def __repr__(self) -> str:
        return f"<VulnerabilityProfile habitation_id={self.habitation_id!r} pop={self.population}>"


class RiskAssessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable, auditable calculation output from PRAYAAS Risk Engine."""

    __tablename__ = "risk_assessments"

    habitation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("habitations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PRAYAAS-RISK-1.0",
        index=True,
    )
    config_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
    )

    # ── Risk Components (0 - 100) ──
    baseline_hazard_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dynamic_hazard_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hazard_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    exposure_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    vulnerability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    adaptive_capacity_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    adaptive_capacity_deficit_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    history_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    compound_hazard_adjustment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="Capped at 15.0")

    # ── Synthesized Scores ──
    baseline_structural_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_dynamic_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    composite_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    risk_classification: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=RedZoneClassification.WATCH.value,
        index=True,
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    dominant_hazard: Mapped[str] = mapped_column(String(50), nullable=False, default="LANDSLIDE")
    sustainability_index: Mapped[float] = mapped_column(Float, nullable=False, default=50.0, doc="0-100 HSI")

    # ── Audit & Traceability ──
    reason_codes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    source_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True,
    )

    # Relationships
    habitation: Mapped[Habitation] = relationship("Habitation", back_populates="risk_assessments")
    relocation_assessments: Mapped[list[RelocationAssessment]] = relationship(
        "RelocationAssessment", back_populates="risk_assessment"
    )

    def __repr__(self) -> str:
        return f"<RiskAssessment id={self.id!r} habitation_id={self.habitation_id!r} score={self.composite_risk_score}>"
