"""InfrastructureAsset (Point) ORM model — hospitals, bridges, helipads, etc."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode, InfrastructureType


class InfrastructureAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Critical infrastructure asset with a Point geometry."""

    __tablename__ = "infrastructure_assets"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        default=InfrastructureType.HOSPITAL.value,
        doc="HOSPITAL | SCHOOL | ROAD_JUNCTION | BRIDGE | HELIPAD | SHELTER | CLINIC | WATER_SOURCE",
    )

    # ── Spatial ──
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OPERATIONAL",
        doc="OPERATIONAL | DAMAGED | UNDER_CONSTRUCTION",
    )
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
        doc="DEMO | REALTIME | HISTORICAL | SIMULATED | PUBLIC | LIVE",
    )

    # ── OSM & Provenance Tracking ──
    osm_type: Mapped[str | None] = mapped_column(String(20), nullable=True, doc="node | way | relation")
    osm_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    osm_tags: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<InfrastructureAsset id={self.id!r} name={self.name!r} type={self.type!r}>"


# Compatibility alias
InfrastructurePoint = InfrastructureAsset
