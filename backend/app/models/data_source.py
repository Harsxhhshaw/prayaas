"""DataSource ORM model — tracks external geospatial feeds and ingestion pipelines."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode


class DataSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """External geospatial dataset or sensor stream."""

    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="RASTER_DEM | SATELLITE_OPTICAL | RADAR_SAR | WEATHER_STATION | SEISMIC | FIELD_SURVEY | OSM_VECTOR",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
        doc="ACTIVE | SYNCING | DEGRADED | OFFLINE",
    )
    last_sync: Mapped[str | None] = mapped_column(String(30), nullable=True)
    records_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
        doc="DEMO | REALTIME | HISTORICAL | SIMULATED | PUBLIC | LIVE",
    )

    # ── Provenance & Freshness extensions ──
    verified_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    license: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_ingestion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    spatial_resolution: Mapped[str | None] = mapped_column(String(64), nullable=True)
    temporal_resolution: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_refresh_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    def __repr__(self) -> str:
        return f"<DataSource id={self.id!r} name={self.name!r} status={self.status!r}>"
