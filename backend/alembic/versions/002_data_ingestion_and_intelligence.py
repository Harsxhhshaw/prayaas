"""Data ingestion pipeline, multi-hazard risk engine, and relocation readiness models.

Revision ID: 002_data_ingestion
Revises: 001_initial
Create Date: 2026-09-28 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision: str = "002_data_ingestion"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update data_sources with provenance and freshness tracking
    op.add_column("data_sources", sa.Column("verified_url", sa.String(length=512), nullable=True))
    op.add_column("data_sources", sa.Column("license", sa.String(length=128), nullable=True))
    op.add_column("data_sources", sa.Column("source_date", sa.String(length=50), nullable=True))
    op.add_column("data_sources", sa.Column("last_ingested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("data_sources", sa.Column("last_successful_ingestion", sa.DateTime(timezone=True), nullable=True))
    op.add_column("data_sources", sa.Column("spatial_resolution", sa.String(length=64), nullable=True))
    op.add_column("data_sources", sa.Column("temporal_resolution", sa.String(length=64), nullable=True))
    op.add_column("data_sources", sa.Column("expected_refresh_seconds", sa.Integer(), nullable=True))
    op.add_column("data_sources", sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False))

    # 2. Update hazard_zones with computed and declared area audit fields
    op.add_column("hazard_zones", sa.Column("computed_area_sq_km", sa.Float(), nullable=True))
    op.add_column("hazard_zones", sa.Column("source_declared_area_sq_km", sa.Float(), nullable=True))

    # 3. Update infrastructure_assets with OSM tracking
    op.add_column("infrastructure_assets", sa.Column("osm_type", sa.String(length=20), nullable=True))
    op.add_column("infrastructure_assets", sa.Column("osm_id", sa.String(length=64), nullable=True))
    op.add_column("infrastructure_assets", sa.Column("osm_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("infrastructure_assets", sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_infrastructure_assets_osm_id", "infrastructure_assets", ["osm_id"])

    # 4. Create ingestion_runs table
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("ingestion_type", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="RUNNING", nullable=False),
        sa.Column("records_received", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_inserted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_skipped", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_rejected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("ingestion_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_runs_source_id", "ingestion_runs", ["source_id"])
    op.create_index("ix_ingestion_runs_ingestion_type", "ingestion_runs", ["ingestion_type"])
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"])

    # 5. Create environmental_observations table
    op.create_table(
        "environmental_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("habitation_id", sa.String(length=36), nullable=True),
        sa.Column("district_id", sa.String(length=36), nullable=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("observation_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True),
        sa.Column("data_mode", sa.String(length=20), server_default="LIVE", nullable=False),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["habitation_id"], ["habitations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_environmental_observations_habitation_id", "environmental_observations", ["habitation_id"])
    op.create_index("ix_environmental_observations_district_id", "environmental_observations", ["district_id"])
    op.create_index("ix_environmental_observations_observation_type", "environmental_observations", ["observation_type"])
    op.create_index("ix_environmental_observations_observed_at", "environmental_observations", ["observed_at"])

    # 6. Create raster_datasets table
    op.create_table(
        "raster_datasets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("dataset_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("crs", sa.String(length=64), server_default="EPSG:4326", nullable=False),
        sa.Column("resolution_x", sa.Float(), nullable=True),
        sa.Column("resolution_y", sa.Float(), nullable=True),
        sa.Column("bounds", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("nodata", sa.Float(), nullable=True),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raster_datasets_name", "raster_datasets", ["name"])
    op.create_index("ix_raster_datasets_dataset_type", "raster_datasets", ["dataset_type"])

    # 7. Create vulnerability_profiles table
    op.create_table(
        "vulnerability_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("habitation_id", sa.String(length=36), nullable=False),
        sa.Column("population", sa.Integer(), server_default="0", nullable=False),
        sa.Column("households", sa.Integer(), server_default="0", nullable=False),
        sa.Column("children_share", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("elderly_share", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("disability_share", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("housing_vulnerability", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("population_density", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("healthcare_access_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("road_access_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("isolation_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("data_confidence", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("raw_attributes", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["habitation_id"], ["habitations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("habitation_id"),
    )
    op.create_index("ix_vulnerability_profiles_habitation_id", "vulnerability_profiles", ["habitation_id"])

    # 8. Create risk_assessments table
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("habitation_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_version", sa.String(length=32), server_default="PRAYAAS-RISK-1.0", nullable=False),
        sa.Column("config_version", sa.String(length=32), server_default="1.0.0", nullable=False),
        sa.Column("baseline_hazard_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("dynamic_hazard_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("hazard_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("exposure_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("vulnerability_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("adaptive_capacity_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("adaptive_capacity_deficit_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("history_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("trend_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("compound_hazard_adjustment", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("baseline_structural_risk", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("current_dynamic_risk", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("composite_risk_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("risk_classification", sa.String(length=30), server_default="WATCH", nullable=False),
        sa.Column("confidence_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("dominant_hazard", sa.String(length=50), server_default="LANDSLIDE", nullable=False),
        sa.Column("sustainability_index", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("reason_codes", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("source_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("explanation", sa.Text(), server_default="", nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["habitation_id"], ["habitations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_assessments_habitation_id", "risk_assessments", ["habitation_id"])
    op.create_index("ix_risk_assessments_risk_classification", "risk_assessments", ["risk_classification"])
    op.create_index("ix_risk_assessments_calculated_at", "risk_assessments", ["calculated_at"])

    # 9. Create relocation_assessments table
    op.create_table(
        "relocation_assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("habitation_id", sa.String(length=36), nullable=False),
        sa.Column("risk_assessment_id", sa.String(length=36), nullable=True),
        sa.Column("analysis_version", sa.String(length=32), server_default="PRAYAAS-RELOCATION-1.0", nullable=False),
        sa.Column("config_version", sa.String(length=32), server_default="1.0.0", nullable=False),
        sa.Column("need_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("urgency", sa.String(length=30), server_default="MEDIUM_TERM", nullable=False),
        sa.Column("readiness_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("readiness_level", sa.String(length=30), server_default="NOT_READY", nullable=False),
        sa.Column("need_components", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("readiness_components", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("readiness_gaps", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("reason_codes", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("explanation", sa.Text(), server_default="", nullable=False),
        sa.Column("confidence_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["habitation_id"], ["habitations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["risk_assessment_id"], ["risk_assessments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_relocation_assessments_habitation_id", "relocation_assessments", ["habitation_id"])
    op.create_index("ix_relocation_assessments_urgency", "relocation_assessments", ["urgency"])
    op.create_index("ix_relocation_assessments_readiness_level", "relocation_assessments", ["readiness_level"])
    op.create_index("ix_relocation_assessments_calculated_at", "relocation_assessments", ["calculated_at"])


def downgrade() -> None:
    op.drop_table("relocation_assessments")
    op.drop_table("risk_assessments")
    op.drop_table("vulnerability_profiles")
    op.drop_table("raster_datasets")
    op.drop_table("environmental_observations")
    op.drop_table("ingestion_runs")

    op.drop_index("ix_infrastructure_assets_osm_id", "infrastructure_assets")
    op.drop_column("infrastructure_assets", "last_seen")
    op.drop_column("infrastructure_assets", "osm_tags")
    op.drop_column("infrastructure_assets", "osm_id")
    op.drop_column("infrastructure_assets", "osm_type")

    op.drop_column("hazard_zones", "source_declared_area_sq_km")
    op.drop_column("hazard_zones", "computed_area_sq_km")

    op.drop_column("data_sources", "metadata_json")
    op.drop_column("data_sources", "expected_refresh_seconds")
    op.drop_column("data_sources", "temporal_resolution")
    op.drop_column("data_sources", "spatial_resolution")
    op.drop_column("data_sources", "last_successful_ingestion")
    op.drop_column("data_sources", "last_ingested_at")
    op.drop_column("data_sources", "source_date")
    op.drop_column("data_sources", "license")
    op.drop_column("data_sources", "verified_url")
