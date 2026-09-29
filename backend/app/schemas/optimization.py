"""Pydantic schemas for Multi-Site Relocation Optimization and Digital Twin."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class RelocationAllocationSchema(BaseModel):
    id: str | None = None
    candidate_type: str
    candidate_id: str
    candidate_name: str | None = None
    allocated_population: int
    usable_capacity: int
    capacity_utilization_pct: float
    distance_km: float
    evidence_status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelocationPlanSchema(BaseModel):
    id: str | None = None
    plan_name: str
    strategy_type: str
    allocated_population: int
    unallocated_population: int
    allocation_ratio: float
    site_count: int
    average_distance_km: float
    max_distance_km: float
    capacity_utilization_percent: float
    relative_infrastructure_burden: float
    community_fragmentation: str | None = "UNKNOWN / NOT AVAILABLE"
    livelihood_disruption: str | None = "UNKNOWN"
    environmental_pressure: float | None = None
    evidence_confidence: float = 65.0
    assumption_dependence: str = "EXPLORATORY / ASSUMPTION-DEPENDENT"
    explanation: str
    binding_constraints: list[str] = Field(default_factory=list)
    allocations: list[RelocationAllocationSchema] = Field(default_factory=list)


class RelocationOptimizationRunRequest(BaseModel):
    origin_habitation_id: str
    mode: Literal["EXPLORATORY", "DECISION_SUPPORT"] = "EXPLORATORY"
    target_population: int | None = None  # None = use habitation population
    max_sites: int | None = None
    min_allocation_size: int = 10
    candidate_ids: list[str] | None = None  # None = all available for origin
    include_demo_candidates: bool = False
    include_benchmark_sites: bool = False
    objective_weights: dict[str, float] = Field(default_factory=dict)


class RelocationOptimizationRunResponse(BaseModel):
    run_id: str
    origin_habitation_id: str
    analysis_version: str
    config_version: str
    mode: str
    target_population: int
    solver_status: str
    candidates_considered_count: int
    usable_candidates_count: int
    plans: list[RelocationPlanSchema]
    message: str | None = None


# ── Task 9: Digital Twin Schemas ──

class ServiceDimensionLoad(BaseModel):
    dimension: str  # Housing, Water, Sanitation, Healthcare, Education, Transport, Utilities, Environment
    allocated_load: int
    capacity: int | None
    utilization_pct: float | None
    status: Literal["OK", "WARNING", "EXCEEDED", "UNKNOWN"]
    evidence_status: str  # OBSERVED, PUBLIC_VERIFIED, MODELED, PLANNING_ASSUMPTION, DEMO, UNKNOWN
    notes: str


class DestinationTwinState(BaseModel):
    candidate_id: str
    candidate_type: str
    allocated_population: int
    distance_km: float
    dimensions: list[ServiceDimensionLoad]
    overall_status: Literal["OK", "WARNING", "EXCEEDED", "UNKNOWN"]
    bottleneck_dimension: str | None


class ScenarioParameters(BaseModel):
    population_change_pct: float = 0.0  # e.g. +15.0 or -10.0
    water_supply_change_pct: float = 0.0  # e.g. -20.0
    road_unavailable: bool = False
    unavailable_candidate_ids: list[str] = Field(default_factory=list)
    health_capacity_change_pct: float = 0.0
    education_capacity_change_pct: float = 0.0
    utility_capacity_change_pct: float = 0.0
    water_upgrade_capacity: int = 0  # Counterfactual water addition
    education_upgrade_capacity: int = 0  # Counterfactual school addition
    health_upgrade_capacity: int = 0
    hazard_score_change: float = 0.0  # Stress scenario


class DigitalTwinSimulationResponse(BaseModel):
    plan_id: str
    scenario_name: str
    parameters: ScenarioParameters
    destinations: list[DestinationTwinState]
    total_allocated: int
    total_unallocated: int
    overall_plan_feasibility: Literal["PASS", "DEGRADED", "FAIL", "UNKNOWN"]
    limiting_bottleneck: str | None
    reoptimization_recommended: bool
    summary: str


class ScenarioOutcome(BaseModel):
    scenario_id: str
    name: str
    status: Literal["PASS", "DEGRADED", "FAIL", "UNKNOWN"]
    binding_dimension: str | None
    summary: str


class PlanRobustnessResponse(BaseModel):
    plan_id: str
    plan_name: str
    tested_scenarios: int
    passed_scenarios: int
    degraded_scenarios: int
    failed_scenarios: int
    unknown_scenarios: int
    robustness_score: float  # 0.0 - 100.0
    scenarios: list[ScenarioOutcome]
    summary: str
