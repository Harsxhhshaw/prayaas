"""Habitation ORM model — core entity for multi-hazard risk tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode, RelocationUrgency, RiskClassification, VerificationStatus

if TYPE_CHECKING:
    from app.models.administrative import District
    from app.models.relocation import RelocationAssessment
    from app.models.risk import RiskAssessment, VulnerabilityProfile


class Habitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A habitation (village/settlement) monitored for multi-hazard risk.

    The geometry column stores a Point(lon, lat) in EPSG:4326.
    hazard_scores and risk_history are stored as JSONB arrays.
    """

    __tablename__ = "habitations"

    # ── Identity ──
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    district_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── Spatial ──
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    # ── Risk Assessment ──
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Composite 0-100")
    risk_category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RiskClassification.SAFE.value,
        doc="CRITICAL | HIGH | WATCH | SAFE",
    )
    urgency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RelocationUrgency.MEDIUM_TERM.value,
        doc="IMMEDIATE | SHORT_TERM | MEDIUM_TERM | MONITOR",
    )
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50, doc="0-100 confidence index")
    vulnerability_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Social vulnerability 0-100"
    )

    # ── Hazard detail (JSONB) ──
    hazard_scores: Mapped[dict | list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc='[{"type": "LANDSLIDE", "score": 94, "label": "Landslide"}, ...]',
    )
    risk_history: Mapped[dict | list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc='[{"year": 2022, "score": 64}, ...]',
    )

    # ── Demographics ──
    population: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    households: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Physical ──
    elevation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="meters ASL")
    nearest_road: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="km")
    nearest_hospital: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="km")
    nearest_school: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="km")

    # ── Verification & Mode ──
    last_assessed: Mapped[str | None] = mapped_column(String(20), nullable=True, doc="ISO date")
    verification_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=VerificationStatus.PENDING.value,
        doc="VERIFIED | PENDING | IN_PROGRESS | FLAGGED",
    )
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
        doc="DEMO | REALTIME | HISTORICAL | SIMULATED | PUBLIC | LIVE",
    )

    # ── Relationships ──
    district_rel: Mapped[District | None] = relationship("District", back_populates="habitations")
    vulnerability_profile: Mapped[VulnerabilityProfile | None] = relationship(
        "VulnerabilityProfile", back_populates="habitation", uselist=False, cascade="all, delete-orphan"
    )
    risk_assessments: Mapped[list[RiskAssessment]] = relationship(
        "RiskAssessment", back_populates="habitation", cascade="all, delete-orphan"
    )
    relocation_assessments: Mapped[list[RelocationAssessment]] = relationship(
        "RelocationAssessment", back_populates="habitation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Habitation id={self.id!r} name={self.name!r} risk={self.risk_score}>"
