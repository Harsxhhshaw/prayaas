"""Relocation Assessment ORM model — RelocationAssessment."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ReadinessLevel, RelocationUrgency

if TYPE_CHECKING:
    from app.models.habitation import Habitation
    from app.models.risk import RiskAssessment


class RelocationAssessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Calculated Relocation Need, Urgency, and Institutional Readiness for a habitation."""

    __tablename__ = "relocation_assessments"

    habitation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("habitations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_assessment_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("risk_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    analysis_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PRAYAAS-RELOCATION-1.0",
        index=True,
    )
    config_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
    )

    # ── Scores ──
    need_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Structural relocation need 0-100 (candidate sites NEVER reduce this)",
    )
    urgency: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=RelocationUrgency.MEDIUM_TERM.value,
        index=True,
        doc="IMMEDIATE | SHORT_TERM | MEDIUM_TERM | MONITOR",
    )
    readiness_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Institutional & physical readiness 0-100 (subject to strict caps)",
    )
    readiness_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ReadinessLevel.NOT_READY.value,
        index=True,
        doc="NOT_READY | LOW_READINESS | MODERATE_READINESS | HIGH_READINESS",
    )

    # ── Detailed breakdown & gaps ──
    need_components: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    readiness_components: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    readiness_gaps: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc='["NO_VERIFIED_CANDIDATE_SITE", ...]',
    )
    reason_codes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True,
    )

    # Relationships
    habitation: Mapped[Habitation] = relationship("Habitation", back_populates="relocation_assessments")
    risk_assessment: Mapped[RiskAssessment | None] = relationship("RiskAssessment", back_populates="relocation_assessments")

    def __repr__(self) -> str:
        return f"<RelocationAssessment id={self.id!r} habitation_id={self.habitation_id!r} need={self.need_score}>"
