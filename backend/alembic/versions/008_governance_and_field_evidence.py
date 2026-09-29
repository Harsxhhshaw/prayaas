"""Add Task 10 governance, field evidence, land status, consultations, and dossiers.

Revision ID: 008_governance_and_field_evidence
Revises: 007_relocation_optimization
Create Date: 2026-09-30 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2


revision: str = "008_governance_and_field_evidence"
down_revision: Union[str, None] = "007_relocation_optimization"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "field_observations" not in tables:
        op.create_table(
            "field_observations",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.String(length=64), nullable=False),
            sa.Column("observation_type", sa.String(length=64), nullable=False),
            sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False, from_text="ST_GeomFromEWKT", name="geometry"), nullable=True),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("observer_name", sa.String(length=128), nullable=True),
            sa.Column("observer_role", sa.String(length=128), nullable=True),
            sa.Column("notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("evidence_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("data_mode", sa.String(length=32), nullable=False, server_default="FIELD"),
            sa.Column("verification_level", sa.String(length=64), nullable=False, server_default="FIELD_OBSERVED"),
            sa.Column("verified_by", sa.String(length=128), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("technical_notes", sa.Text(), nullable=True),
            sa.Column("attachments_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_field_observations_entity_id"), "field_observations", ["entity_id"], unique=False)
        op.create_index(op.f("ix_field_observations_entity_type"), "field_observations", ["entity_type"], unique=False)
        op.create_index(op.f("ix_field_observations_observation_type"), "field_observations", ["observation_type"], unique=False)
        op.create_index("idx_field_observations_geom", "field_observations", ["geom"], postgresql_using="gist")

    if "land_status_records" not in tables:
        op.create_table(
            "land_status_records",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("parcel_candidate_id", sa.String(length=64), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=64), nullable=False),
            sa.Column("source_reference", sa.String(length=255), nullable=True),
            sa.Column("document_reference", sa.String(length=255), nullable=True),
            sa.Column("reviewed_by", sa.String(length=128), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("data_mode", sa.String(length=32), nullable=False, server_default="PUBLIC"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_land_status_records_parcel_candidate_id"), "land_status_records", ["parcel_candidate_id"], unique=False)

    if "consultation_records" not in tables:
        op.create_table(
            "consultation_records",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("habitation_id", sa.String(length=64), nullable=False),
            sa.Column("consultation_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("participant_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("method", sa.String(length=64), nullable=False, server_default="GRAM_SABHA"),
            sa.Column("questions_responses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("concerns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("source_attachment", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("verification_status", sa.String(length=64), nullable=False, server_default="PENDING"),
            sa.Column("data_mode", sa.String(length=32), nullable=False, server_default="DEMO"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_consultation_records_habitation_id"), "consultation_records", ["habitation_id"], unique=False)

    if "governance_reviews" not in tables:
        op.create_table(
            "governance_reviews",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.String(length=64), nullable=False),
            sa.Column("review_stage", sa.String(length=64), nullable=False),
            sa.Column("assigned_to", sa.String(length=128), nullable=True),
            sa.Column("reviewer_role", sa.String(length=128), nullable=True),
            sa.Column("review_notes", sa.Text(), nullable=True),
            sa.Column("action_taken", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_governance_reviews_entity_id"), "governance_reviews", ["entity_id"], unique=False)
        op.create_index(op.f("ix_governance_reviews_entity_type"), "governance_reviews", ["entity_type"], unique=False)

    if "analytical_overrides" not in tables:
        op.create_table(
            "analytical_overrides",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.String(length=64), nullable=False),
            sa.Column("field_name", sa.String(length=64), nullable=False),
            sa.Column("original_value", sa.String(length=255), nullable=False),
            sa.Column("override_value", sa.String(length=255), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("reviewer", sa.String(length=128), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_analytical_overrides_entity_id"), "analytical_overrides", ["entity_id"], unique=False)
        op.create_index(op.f("ix_analytical_overrides_entity_type"), "analytical_overrides", ["entity_type"], unique=False)

    if "document_extractions" not in tables:
        op.create_table(
            "document_extractions",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("document_name", sa.String(length=255), nullable=False),
            sa.Column("document_type", sa.String(length=64), nullable=False, server_default="GEOTECHNICAL_REPORT"),
            sa.Column("file_path", sa.String(length=512), nullable=True),
            sa.Column("raw_text", sa.Text(), nullable=True),
            sa.Column("extracted_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PROPOSED"),
            sa.Column("source_reference", sa.String(length=255), nullable=True),
            sa.Column("confirmed_by", sa.String(length=128), nullable=True),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if "demo_snapshots" not in tables:
        op.create_table(
            "demo_snapshots",
            sa.Column("snapshot_id", sa.String(length=64), nullable=False),
            sa.Column("habitation_id", sa.String(length=64), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("snapshot_id"),
        )
        op.create_index(op.f("ix_demo_snapshots_habitation_id"), "demo_snapshots", ["habitation_id"], unique=False)


def downgrade() -> None:
    op.drop_table("demo_snapshots")
    op.drop_table("document_extractions")
    op.drop_table("analytical_overrides")
    op.drop_table("governance_reviews")
    op.drop_table("consultation_records")
    op.drop_table("land_status_records")
    op.drop_table("field_observations")
