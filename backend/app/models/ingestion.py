"""Ingestion ORM models — IngestionRun, EnvironmentalObservation, RasterDataset."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode, DatasetType, IngestionStatus, ObservationType

if TYPE_CHECKING:
    from app.models.administrative import District
    from app.models.data_source import DataSource
    from app.models.habitation import Habitation


class IngestionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks every execution of an external or local ingestion pipeline."""

    __tablename__ = "ingestion_runs"

    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ingestion_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="OSM_OVERPASS | OPEN_METEO_WEATHER | GEOJSON_IMPORT | CSV_IMPORT | DEM_RASTER",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=IngestionStatus.RUNNING.value,
        index=True,
    )
    records_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
    )
    ingestion_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Relationships
    data_source: Mapped[DataSource | None] = relationship("DataSource")

    def __repr__(self) -> str:
        return f"<IngestionRun id={self.id!r} type={self.ingestion_type!r} status={self.status!r}>"


class EnvironmentalObservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Time-series or discrete observation for weather, seismic, or sensor feeds."""

    __tablename__ = "environmental_observations"

    habitation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("habitations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    district_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        default=ObservationType.RAINFALL_24H.value,
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    geom: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.LIVE.value,
    )
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Relationships
    habitation: Mapped[Habitation | None] = relationship("Habitation")
    district: Mapped[District | None] = relationship("District")
    data_source: Mapped[DataSource | None] = relationship("DataSource")

    def __repr__(self) -> str:
        return f"<EnvironmentalObservation id={self.id!r} type={self.observation_type!r} val={self.value}>"


class RasterDataset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Metadata catalog for raster elevation, slope, and satellite datasets."""

    __tablename__ = "raster_datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dataset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        default=DatasetType.DEM.value,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    crs: Mapped[str] = mapped_column(String(64), nullable=False, default="EPSG:4326")
    resolution_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    bounds: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    nodata: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Relationships
    data_source: Mapped[DataSource | None] = relationship("DataSource")

    def __repr__(self) -> str:
        return f"<RasterDataset id={self.id!r} name={self.name!r} type={self.dataset_type!r}>"
