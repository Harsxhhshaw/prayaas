"""Add relocation optimization and digital twin schema.

Revision ID: 007_relocation_optimization
Revises: 006_candidate_feasible_metrics
Create Date: 2026-09-30 01:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "007_relocation_optimization"
down_revision: Union[str, None] = "006_candidate_feasible_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use inspect/conditional to allow Base.metadata.create_all idempotency
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "relocation_optimization_runs" not in tables:
        op.create_table(
            "relocation_optimization_runs",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("origin_habitation_id", sa.String(length=64), nullable=False),
            sa.Column("analysis_version", sa.String(length=64), nullable=False),
            sa.Column("config_version", sa.String(length=32), nullable=False),
            sa.Column("mode", sa.String(length=32), nullable=False),
            sa.Column("target_population", sa.Integer(), nullable=False),
            sa.Column("solver_status", sa.String(length=64), nullable=False),
            sa.Column("candidate_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("capacity_assessment_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("objective_weights", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("source_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["origin_habitation_id"], ["habitations.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_relocation_optimization_runs_mode"), "relocation_optimization_runs", ["mode"], unique=False)
        op.create_index(op.f("ix_relocation_optimization_runs_origin_habitation_id"), "relocation_optimization_runs", ["origin_habitation_id"], unique=False)

    if "relocation_plans" not in tables:
        op.create_table(
            "relocation_plans",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("run_id", sa.String(length=64), nullable=False),
            sa.Column("plan_name", sa.String(length=64), nullable=False),
            sa.Column("strategy_type", sa.String(length=64), nullable=False),
            sa.Column("allocated_population", sa.Integer(), nullable=False),
            sa.Column("unallocated_population", sa.Integer(), nullable=False),
            sa.Column("allocation_ratio", sa.Float(), nullable=False),
            sa.Column("site_count", sa.Integer(), nullable=False),
            sa.Column("average_distance_km", sa.Float(), nullable=False),
            sa.Column("max_distance_km", sa.Float(), nullable=False),
            sa.Column("capacity_utilization_percent", sa.Float(), nullable=False),
            sa.Column("relative_infrastructure_burden", sa.Float(), nullable=False),
            sa.Column("community_fragmentation", sa.String(length=64), nullable=True),
            sa.Column("livelihood_disruption", sa.String(length=64), nullable=True),
            sa.Column("environmental_pressure", sa.Float(), nullable=True),
            sa.Column("evidence_confidence", sa.Float(), nullable=False),
            sa.Column("assumption_dependence", sa.String(length=64), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=False),
            sa.Column("binding_constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["run_id"], ["relocation_optimization_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_relocation_plans_run_id"), "relocation_plans", ["run_id"], unique=False)

    if "relocation_allocations" not in tables:
        op.create_table(
            "relocation_allocations",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("plan_id", sa.String(length=64), nullable=False),
            sa.Column("candidate_type", sa.String(length=32), nullable=False),
            sa.Column("candidate_id", sa.String(length=64), nullable=False),
            sa.Column("allocated_population", sa.Integer(), nullable=False),
            sa.Column("usable_capacity", sa.Integer(), nullable=False),
            sa.Column("capacity_utilization_pct", sa.Float(), nullable=False),
            sa.Column("distance_km", sa.Float(), nullable=False),
            sa.Column("evidence_status", sa.String(length=64), nullable=False),
            sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["plan_id"], ["relocation_plans.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_relocation_allocations_candidate_id"), "relocation_allocations", ["candidate_id"], unique=False)
        op.create_index(op.f("ix_relocation_allocations_plan_id"), "relocation_allocations", ["plan_id"], unique=False)

    if "plan_robustness_assessments" not in tables:
        op.create_table(
            "plan_robustness_assessments",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("plan_id", sa.String(length=64), nullable=False),
            sa.Column("scenarios_evaluated", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("tested_scenarios", sa.Integer(), nullable=False),
            sa.Column("passed_scenarios", sa.Integer(), nullable=False),
            sa.Column("degraded_scenarios", sa.Integer(), nullable=False),
            sa.Column("failed_scenarios", sa.Integer(), nullable=False),
            sa.Column("unknown_scenarios", sa.Integer(), nullable=False),
            sa.Column("robustness_score", sa.Float(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["plan_id"], ["relocation_plans.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_plan_robustness_assessments_plan_id"), "plan_robustness_assessments", ["plan_id"], unique=False)


def downgrade() -> None:
    op.drop_table("plan_robustness_assessments")
    op.drop_table("relocation_allocations")
    op.drop_table("relocation_plans")
    op.drop_table("relocation_optimization_runs")
