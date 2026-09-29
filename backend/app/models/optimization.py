"""ORM Models for Multi-Site Relocation Optimization and Digital Twin."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RelocationOptimizationRun(Base, TimestampMixin):
    """Tracks an automated or decision-support multi-site population allocation run."""

    __tablename__ = "relocation_optimization_runs"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"OPT-{uuid.uuid4().hex[:12].upper()}",
    )
    origin_habitation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("habitations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="PRAYAAS-ALLOCATION-1.0",
    )
    config_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
    )
    mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="EXPLORATORY",  # EXPLORATORY or DECISION_SUPPORT
        index=True,
    )
    target_population: Mapped[int] = mapped_column(Integer, nullable=False)
    solver_status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="OPTIMAL",  # OPTIMAL, PARTIAL_ALLOCATION, INSUFFICIENT_VERIFIED_CAPACITY, INFEASIBLE
    )
    candidate_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    capacity_assessment_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    objective_weights: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False, default=dict)
    constraints: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    origin_habitation = relationship("Habitation", backref="relocation_runs")
    plans = relationship(
        "RelocationPlan",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RelocationPlan.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<RelocationOptimizationRun {self.id}: {self.origin_habitation_id} ({self.mode}/{self.solver_status})>"


class RelocationPlan(Base, TimestampMixin):
    """Represents a specific multi-site allocation alternative (e.g. Min Distance, Min Sites, Balanced)."""

    __tablename__ = "relocation_plans"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"PLAN-{uuid.uuid4().hex[:12].upper()}",
    )
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("relocation_optimization_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,  # e.g. "ALTERNATIVE A", "ALTERNATIVE B", "ALTERNATIVE C"
    )
    strategy_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,  # MIN_DISTANCE, MIN_SITE_COUNT, BALANCED
    )
    allocated_population: Mapped[int] = mapped_column(Integer, nullable=False)
    unallocated_population: Mapped[int] = mapped_column(Integer, nullable=False)
    allocation_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    site_count: Mapped[int] = mapped_column(Integer, nullable=False)
    average_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    max_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_utilization_percent: Mapped[float] = mapped_column(Float, nullable=False)
    relative_infrastructure_burden: Mapped[float] = mapped_column(Float, nullable=False)
    community_fragmentation: Mapped[str | None] = mapped_column(String(64), nullable=True, default="UNKNOWN / NOT AVAILABLE")
    livelihood_disruption: Mapped[str | None] = mapped_column(String(64), nullable=True, default="UNKNOWN")
    environmental_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=65.0)
    assumption_dependence: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="EXPLORATORY / ASSUMPTION-DEPENDENT",
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    binding_constraints: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    # Relationships
    run = relationship("RelocationOptimizationRun", back_populates="plans")
    allocations = relationship(
        "RelocationAllocation",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    robustness_assessments = relationship(
        "PlanRobustnessAssessment",
        back_populates="plan",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<RelocationPlan {self.id}: {self.plan_name} ({self.strategy_type})>"


class RelocationAllocation(Base, TimestampMixin):
    """Specific assignment of a population segment to a destination candidate parcel or site."""

    __tablename__ = "relocation_allocations"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"ALC-{uuid.uuid4().hex[:12].upper()}",
    )
    plan_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("relocation_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_type: Mapped[str] = mapped_column(String(32), nullable=False)  # PARCEL or SITE
    candidate_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    allocated_population: Mapped[int] = mapped_column(Integer, nullable=False)
    usable_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity_utilization_pct: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="PLANNING_ASSUMPTION",
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    plan = relationship("RelocationPlan", back_populates="allocations")


class PlanRobustnessAssessment(Base, TimestampMixin):
    """Evaluates multi-scenario resilience for a specific relocation plan."""

    __tablename__ = "plan_robustness_assessments"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"ROB-{uuid.uuid4().hex[:12].upper()}",
    )
    plan_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("relocation_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenarios_evaluated: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    tested_scenarios: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_scenarios: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    degraded_scenarios: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_scenarios: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unknown_scenarios: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    robustness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Relationships
    plan = relationship("RelocationPlan", back_populates="robustness_assessments")
