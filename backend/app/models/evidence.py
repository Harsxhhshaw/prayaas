"""ORM models for Evidence Layers, Hazard Inventories, Hazard Models and Validation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    DataMode,
    EvidenceType,
    HazardModelStatus,
    HazardModelType,
    HazardType,
    InventoryVerificationStatus,
    RepresentationType,
    ValidationType,
)


class EvidenceLayer(Base, TimestampMixin):
    """Tracks analytical layers derived from raw data sources or rasters.

    Stores provenance, spatial resolution, CRS, derivation method, and quality metrics.
    """

    __tablename__ = "evidence_layers"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"EV-{uuid.uuid4().hex[:12].upper()}",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        default=EvidenceType.ELEVATION.value,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    raster_dataset_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("raster_datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    data_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DataMode.MODELED.value,
        index=True,
    )
    representation_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RepresentationType.RASTER.value,
    )
    hazard_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    crs: Mapped[str | None] = mapped_column(String(32), nullable=True, default="EPSG:4326")
    spatial_resolution: Mapped[float | None] = mapped_column(Float, nullable=True)
    temporal_resolution: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Spatial coverage
    coverage_geometry = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326),
        nullable=True,
    )
    coverage_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    derivation_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_layer_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    source = relationship("DataSource", backref="derived_evidence_layers")
    raster_dataset = relationship("RasterDataset", backref="evidence_layers")

    def __repr__(self) -> str:
        return f"<EvidenceLayer {self.id}: {self.name} ({self.evidence_type}/{self.data_mode})>"


class HazardInventoryEvent(Base, TimestampMixin):
    """Ground-truth and cataloged hazard inventory event for model training and validation.

    Distinct from generic operational alerts/events, this directly backs frequency ratio
    and ML susceptibility calibration.
    """

    __tablename__ = "hazard_inventory_events"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"HIE-{uuid.uuid4().hex[:12].upper()}",
    )
    hazard_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        default=HazardType.LANDSLIDE.value,
    )
    geom = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326),
        nullable=False,
    )
    event_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)

    source_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    data_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DataMode.DEMO.value,
        index=True,
    )
    verification_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=InventoryVerificationStatus.UNVERIFIED.value,
        index=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    source = relationship("DataSource", backref="inventory_events")

    def __repr__(self) -> str:
        return f"<HazardInventoryEvent {self.id}: {self.hazard_type} ({self.data_mode}/{self.verification_status})>"


class HazardModel(Base, TimestampMixin):
    """Versioned susceptibility and hazard analytical model configuration and state."""

    __tablename__ = "hazard_models"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"MOD-{uuid.uuid4().hex[:12].upper()}",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hazard_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        default=HazardType.LANDSLIDE.value,
    )
    model_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        default=HazardModelType.AHP.value,
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")

    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    training_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    validation_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=HazardModelStatus.CONFIGURED.value,
        index=True,
    )

    validations = relationship(
        "ModelValidation",
        back_populates="hazard_model",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<HazardModel {self.id}: {self.name} ({self.model_type} v{self.version})>"


class ModelValidation(Base):
    """Persisted performance and validation benchmarks for a HazardModel."""

    __tablename__ = "model_validations"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"VAL-{uuid.uuid4().hex[:12].upper()}",
    )
    hazard_model_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("hazard_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validation_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=ValidationType.SPATIAL_BLOCK_SPLIT.value,
    )
    training_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    roc_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    pr_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1: Mapped[float | None] = mapped_column(Float, nullable=True)

    spatial_holdout_used: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    hazard_model = relationship("HazardModel", back_populates="validations")

    def __repr__(self) -> str:
        return f"<ModelValidation {self.id}: model={self.hazard_model_id} auc={self.roc_auc}>"
