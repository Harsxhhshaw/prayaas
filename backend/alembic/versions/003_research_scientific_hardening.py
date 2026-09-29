"""Research and scientific hardening models: EvidenceLayer, HazardInventoryEvent, HazardModel, ModelValidation.

Revision ID: 003_research_scientific_hardening
Revises: 002_data_ingestion
Create Date: 2026-09-29 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision: str = "003_research_scientific_hardening"
down_revision: Union[str, None] = "002_data_ingestion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Expand alembic_version column to accommodate descriptive revision names
    op.alter_column("alembic_version", "version_num", type_=sa.String(length=64))

    # 1. Create evidence_layers table
    op.create_table(
        "evidence_layers",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("raster_dataset_id", sa.String(length=36), nullable=True),
        sa.Column("data_mode", sa.String(length=32), server_default="MODELED", nullable=False),
        sa.Column("representation_type", sa.String(length=32), server_default="RASTER", nullable=False),
        sa.Column("hazard_type", sa.String(length=64), nullable=True),
        sa.Column("crs", sa.String(length=32), server_default="EPSG:4326", nullable=True),
        sa.Column("spatial_resolution", sa.Float(), nullable=True),
        sa.Column("temporal_resolution", sa.String(length=64), nullable=True),
        sa.Column(
            "coverage_geometry",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=True,
        ),
        sa.Column("coverage_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("derivation_method", sa.Text(), nullable=True),
        sa.Column("parent_layer_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["raster_dataset_id"], ["raster_datasets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_layers_evidence_type", "evidence_layers", ["evidence_type"])
    op.create_index("ix_evidence_layers_data_mode", "evidence_layers", ["data_mode"])
    op.create_index("ix_evidence_layers_hazard_type", "evidence_layers", ["hazard_type"])
    op.create_index("ix_evidence_layers_source_id", "evidence_layers", ["source_id"])

    # 2. Create hazard_inventory_events table
    op.create_table(
        "hazard_inventory_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("hazard_type", sa.String(length=64), server_default="LANDSLIDE", nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=False,
        ),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("data_mode", sa.String(length=32), server_default="DEMO", nullable=False),
        sa.Column("verification_status", sa.String(length=32), server_default="UNVERIFIED", nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hazard_inventory_events_hazard_type", "hazard_inventory_events", ["hazard_type"])
    op.create_index("ix_hazard_inventory_events_data_mode", "hazard_inventory_events", ["data_mode"])
    op.create_index("ix_hazard_inventory_events_verification_status", "hazard_inventory_events", ["verification_status"])

    # 3. Create hazard_models table
    op.create_table(
        "hazard_models",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hazard_type", sa.String(length=64), server_default="LANDSLIDE", nullable=False),
        sa.Column("model_type", sa.String(length=32), server_default="AHP", nullable=False),
        sa.Column("version", sa.String(length=32), server_default="1.0.0", nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("training_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validation_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="CONFIGURED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hazard_models_hazard_type", "hazard_models", ["hazard_type"])
    op.create_index("ix_hazard_models_model_type", "hazard_models", ["model_type"])
    op.create_index("ix_hazard_models_status", "hazard_models", ["status"])

    # 4. Create model_validations table
    op.create_table(
        "model_validations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("hazard_model_id", sa.String(length=64), nullable=False),
        sa.Column("validation_type", sa.String(length=64), server_default="SPATIAL_BLOCK_SPLIT", nullable=False),
        sa.Column("training_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("validation_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("roc_auc", sa.Float(), nullable=True),
        sa.Column("pr_auc", sa.Float(), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1", sa.Float(), nullable=True),
        sa.Column("spatial_holdout_used", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("validation_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hazard_model_id"], ["hazard_models.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_validations_hazard_model_id", "model_validations", ["hazard_model_id"])


def downgrade() -> None:
    op.drop_table("model_validations")
    op.drop_table("hazard_models")
    op.drop_table("hazard_inventory_events")
    op.drop_table("evidence_layers")
