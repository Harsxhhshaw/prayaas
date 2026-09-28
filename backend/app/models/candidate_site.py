"""Candidate Relocation Site ORM model."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CandidateStatus, DataMode, VerificationStatus


class CandidateSite(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A potential relocation site assessed for suitability and carrying capacity.

    The geometry stores a Polygon boundary in EPSG:4326.
    The centroid point is also stored for fast lookups.
    """

    __tablename__ = "candidate_sites"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(128), nullable=False)

    # ── Spatial ──
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )
    centroid: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # ── Assessment ──
    suitability_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    carrying_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="max population")
    current_utilization: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="percent 0-100")
    area_hectares: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    elevation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    distance_from_hazard: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, doc="km")

    # ── Infrastructure ──
    road_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    water_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    electricity_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Land ──
    land_use_type: Mapped[str] = mapped_column(String(64), nullable=False, default="Uncategorized")
    ownership: Mapped[str] = mapped_column(String(128), nullable=False, default="Unknown")

    # ── Status & Mode ──
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CandidateStatus.SUITABLE.value,
        doc="SUITABLE | PROVISIONAL | UNSUITABLE | PENDING",
    )
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
        doc="DEMO | REALTIME | HISTORICAL | SIMULATED",
    )

    # ── Assignments (IDs of habitations allocated here) ──
    assigned_habitations: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    def __repr__(self) -> str:
        return f"<CandidateSite id={self.id!r} name={self.name!r} suit={self.suitability_score}>"
