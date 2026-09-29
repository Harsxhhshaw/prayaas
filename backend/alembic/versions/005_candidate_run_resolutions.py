"""Add analysis_resolution_meters and effective_source_resolution_meters to candidate_discovery_runs.

Revision ID: 005_candidate_run_resolutions
Revises: 004_candidate_discovery
Create Date: 2026-09-29 22:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005_candidate_run_resolutions"
down_revision: Union[str, None] = "004_candidate_discovery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidate_discovery_runs",
        sa.Column("analysis_resolution_meters", sa.Float(), nullable=True),
    )
    op.add_column(
        "candidate_discovery_runs",
        sa.Column("effective_source_resolution_meters", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidate_discovery_runs", "effective_source_resolution_meters")
    op.drop_column("candidate_discovery_runs", "analysis_resolution_meters")
