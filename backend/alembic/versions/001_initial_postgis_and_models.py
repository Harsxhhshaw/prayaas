"""Initial PostGIS extension and core domain models.

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-28 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS Extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. States table
    op.create_table(
        "states",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_states_name", "states", ["name"])
    op.create_index("ix_states_code", "states", ["code"])

    # 3. Districts table
    op.create_table(
        "districts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("state_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("headquarters", sa.String(length=128), nullable=True),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_districts_name", "districts", ["name"])
    op.create_index("ix_districts_state_id", "districts", ["state_id"])

    # 4. Habitations table
    op.create_table(
        "habitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("district", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False),
        sa.Column("district_id", sa.String(length=36), nullable=True),
        sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False),
        sa.Column("risk_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("risk_category", sa.String(length=20), server_default="SAFE", nullable=False),
        sa.Column("urgency", sa.String(length=20), server_default="MEDIUM_TERM", nullable=False),
        sa.Column("confidence", sa.Integer(), server_default="50", nullable=False),
        sa.Column("vulnerability_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("hazard_scores", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("risk_history", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("population", sa.Integer(), server_default="0", nullable=False),
        sa.Column("households", sa.Integer(), server_default="0", nullable=False),
        sa.Column("elevation", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("nearest_road", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("nearest_hospital", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("nearest_school", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("last_assessed", sa.String(length=20), nullable=True),
        sa.Column("verification_status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_habitations_name", "habitations", ["name"])
    op.create_index("ix_habitations_district", "habitations", ["district"])
    op.create_index("ix_habitations_state", "habitations", ["state"])

    # 5. Hazard Zones table
    op.create_table(
        "hazard_zones",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False),
        sa.Column("composite_risk_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("hazard_types", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("habitation_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("population_affected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("area_km_sq", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("declared_date", sa.String(length=20), nullable=True),
        sa.Column("last_updated", sa.String(length=20), nullable=True),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hazard_zones_name", "hazard_zones", ["name"])

    # 6. Candidate Sites table
    op.create_table(
        "candidate_sites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("district", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False),
        sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False),
        sa.Column("centroid", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("suitability_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("carrying_capacity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_utilization", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("area_hectares", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("elevation", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("distance_from_hazard", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("road_access", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("water_access", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("electricity_access", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("land_use_type", sa.String(length=64), server_default="Uncategorized", nullable=False),
        sa.Column("ownership", sa.String(length=128), server_default="Unknown", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="SUITABLE", nullable=False),
        sa.Column("verification_status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("assigned_habitations", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_sites_name", "candidate_sites", ["name"])
    op.create_index("ix_candidate_sites_district", "candidate_sites", ["district"])

    # 7. Infrastructure Assets table
    op.create_table(
        "infrastructure_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="OPERATIONAL", nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("district", sa.String(length=128), nullable=True),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_infrastructure_assets_name", "infrastructure_assets", ["name"])
    op.create_index("ix_infrastructure_assets_type", "infrastructure_assets", ["type"])

    # 8. Data Sources table
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="ACTIVE", nullable=False),
        sa.Column("last_sync", sa.String(length=30), nullable=True),
        sa.Column("records_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_sources_name", "data_sources", ["name"])

    # 9. Disaster Events table
    op.create_table(
        "disaster_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("hazard_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="CRITICAL", nullable=False),
        sa.Column("event_date", sa.String(length=20), nullable=False),
        sa.Column("district", sa.String(length=128), nullable=False),
        sa.Column("geom", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True),
        sa.Column("fatalities", sa.Integer(), server_default="0", nullable=False),
        sa.Column("displaced_persons", sa.Integer(), server_default="0", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("data_mode", sa.String(length=20), server_default="DEMO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_disaster_events_title", "disaster_events", ["title"])
    op.create_index("ix_disaster_events_district", "disaster_events", ["district"])

    # 10. Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), server_default="SYSTEM", nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # 11. Relocation Priorities table
    op.create_table(
        "relocation_priorities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("habitation_id", sa.String(length=36), nullable=False),
        sa.Column("habitation_name", sa.String(length=255), nullable=False),
        sa.Column("urgency", sa.String(length=20), server_default="MEDIUM_TERM", nullable=False),
        sa.Column("risk_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("population", sa.Integer(), server_default="0", nullable=False),
        sa.Column("district", sa.String(length=128), nullable=False),
        sa.Column("assigned_site_id", sa.String(length=36), nullable=True),
        sa.Column("assigned_site_name", sa.String(length=255), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("timeline_months", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["habitation_id"], ["habitations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_site_id"], ["candidate_sites.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 12. Operational Alerts table
    op.create_table(
        "operational_alerts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("message", sa.String(length=1024), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="WATCH", nullable=False),
        sa.Column("timestamp", sa.String(length=30), nullable=False),
        sa.Column("habitation_id", sa.String(length=36), nullable=True),
        sa.Column("read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["habitation_id"], ["habitations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("operational_alerts")
    op.drop_table("relocation_priorities")
    op.drop_table("audit_logs")
    op.drop_table("disaster_events")
    op.drop_table("data_sources")
    op.drop_table("infrastructure_assets")
    op.drop_table("candidate_sites")
    op.drop_table("hazard_zones")
    op.drop_table("habitations")
    op.drop_table("districts")
    op.drop_table("states")
