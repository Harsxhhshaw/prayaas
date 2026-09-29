"""Add feasible land metrics and parcel slope to candidate discovery schema.

Revision ID: 006_candidate_feasible_metrics
Revises: 005_candidate_run_resolutions
Create Date: 2026-09-29 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006_candidate_feasible_metrics"
down_revision: Union[str, None] = "005_candidate_run_resolutions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Columns on candidate_discovery_runs
    op.add_column("candidate_discovery_runs", sa.Column("total_aoi_area_sq_km", sa.Float(), nullable=True))
    op.add_column("candidate_discovery_runs", sa.Column("excluded_area_sq_km", sa.Float(), nullable=True))
    op.add_column("candidate_discovery_runs", sa.Column("feasible_area_sq_km", sa.Float(), nullable=True))
    op.add_column("candidate_discovery_runs", sa.Column("feasible_percent", sa.Float(), nullable=True))
    op.add_column("candidate_discovery_runs", sa.Column("candidate_eligible_cells", sa.Integer(), nullable=True))
    op.add_column("candidate_discovery_runs", sa.Column("candidate_eligible_area_sq_km", sa.Float(), nullable=True))

    # Columns on candidate_parcels
    op.add_column("candidate_parcels", sa.Column("mean_slope_degrees", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_parcels", "mean_slope_degrees")
    op.drop_column("candidate_discovery_runs", "candidate_eligible_area_sq_km")
    op.drop_column("candidate_discovery_runs", "candidate_eligible_cells")
    op.drop_column("candidate_discovery_runs", "feasible_percent")
    op.drop_column("candidate_discovery_runs", "feasible_area_sq_km")
    op.drop_column("candidate_discovery_runs", "excluded_area_sq_km")
    op.drop_column("candidate_discovery_runs", "total_aoi_area_sq_km")
