"""Automated GIS Relocation Candidate Discovery — CandidateDiscoveryRun and CandidateParcel.

Revision ID: 004_candidate_discovery
Revises: 003_research_scientific_hardening
Create Date: 2026-09-29 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision: str = "004_candidate_discovery"
down_revision: Union[str, None] = "003_research_scientific_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create candidate_discovery_runs table
    op.create_table(
        "candidate_discovery_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("origin_habitation_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_version", sa.String(length=32), server_default="PRAYAAS-CANDIDATE-1.0", nullable=False),
        sa.Column("config_version", sa.String(length=32), server_default="1.0.0", nullable=False),
        sa.Column("search_radius_km", sa.Float(), server_default="15.0", nullable=False),
        sa.Column(
            "aoi_geometry",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), server_default="QUEUED", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("source_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("cells_evaluated", sa.Integer(), nullable=True),
        sa.Column("cells_excluded", sa.Integer(), nullable=True),
        sa.Column("candidate_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("warning_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["origin_habitation_id"], ["habitations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_discovery_runs_origin_habitation_id", "candidate_discovery_runs", ["origin_habitation_id"])
    op.create_index("ix_candidate_discovery_runs_status", "candidate_discovery_runs", ["status"])
    op.create_index("ix_candidate_discovery_runs_analysis_version", "candidate_discovery_runs", ["analysis_version"])

    # 2. Create candidate_parcels table
    op.create_table(
        "candidate_parcels",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("discovery_run_id", sa.String(length=64), nullable=False),
        sa.Column("origin_habitation_id", sa.String(length=36), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="MULTIPOLYGON", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=False,
        ),
        sa.Column(
            "centroid",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=False,
        ),
        sa.Column("area_sq_km", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("area_hectares", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("distance_from_origin_km", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("suitability_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("robustness_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("rank_stability", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("rank", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PRELIMINARY", nullable=False),
        sa.Column("confidence_score", sa.Float(), server_default="50.0", nullable=False),
        sa.Column("exclusion_summary", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("criteria_scores", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("reason_codes", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("source_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("data_mode", sa.String(length=20), server_default="MODELED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["discovery_run_id"], ["candidate_discovery_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["origin_habitation_id"], ["habitations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_parcels_discovery_run_id", "candidate_parcels", ["discovery_run_id"])
    op.create_index("ix_candidate_parcels_origin_habitation_id", "candidate_parcels", ["origin_habitation_id"])
    op.create_index("ix_candidate_parcels_status", "candidate_parcels", ["status"])
    op.create_index("ix_candidate_parcels_suitability_score", "candidate_parcels", ["suitability_score"])
    op.create_index("ix_candidate_parcels_rank", "candidate_parcels", ["rank"])


def downgrade() -> None:
    op.drop_table("candidate_parcels")
    op.drop_table("candidate_discovery_runs")
