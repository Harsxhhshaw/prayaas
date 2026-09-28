"""HazardZone (Red Zone) ORM model — statutory areas unsuitable for permanent habitation."""

from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode


class HazardZone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A declared Hazard/Red Zone polygon where permanent habitation is prohibited.

    The geometry column stores a Polygon boundary in EPSG:4326.
    """

    __tablename__ = "hazard_zones"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # ── Spatial ──
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )

    # ── Risk ──
    composite_risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hazard_types: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc='["LANDSLIDE", "FLOOD", ...]',
    )

    # ── Impact ──
    habitation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    population_affected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    area_km_sq: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Explicit Area Audit Fields (fixes GIS vs statutory area discrepancies) ──
    computed_area_sq_km: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="Exact geodesic area derived from PostGIS ST_Area"
    )
    source_declared_area_sq_km: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="Area declared in gazette notification or official report"
    )

    # ── Administrative ──
    declared_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_updated: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
        doc="DEMO | REALTIME | HISTORICAL | SIMULATED | PUBLIC | LIVE",
    )

    def __repr__(self) -> str:
        return f"<HazardZone id={self.id!r} name={self.name!r} score={self.composite_risk_score}>"


# Backward-compatibility alias
RedZone = HazardZone
