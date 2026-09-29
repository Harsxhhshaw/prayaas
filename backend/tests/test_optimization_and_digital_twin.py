"""Tests for Task 8 Multi-Site Relocation Optimization and Task 9 Digital Twin."""

from __future__ import annotations

import pytest
from app.models.candidate_discovery import CandidateParcel
from app.models.candidate_site import CandidateSite
from app.models.enums import DataMode, VerificationStatus
from app.models.habitation import Habitation
from app.models.optimization import RelocationPlan
from app.schemas.optimization import (
    RelocationOptimizationRunRequest,
    ScenarioParameters,
)
from app.services.digital_twin.engine import DigitalTwinEngine
from app.services.optimization.engine import RelocationOptimizationEngine
from app.services.relocation.engine import (
    RelocationEngine,
    calculate_reception_readiness,
)


# ==============================================================================
# 0. Readiness Stale Demo Cap & Evidence Semantics Tests
# ==============================================================================

def test_readiness_stale_demo_cap_fix():
    """MODELED candidates must NOT be clamped by the DEMO-only cap (40.0)."""
    score, level, gaps, codes = calculate_reception_readiness(
        candidate_sites_count=5,
        only_demo_candidates=True,  # Old demo sites exist
        has_modeled_candidates=True,  # Real modeled parcels also exist!
        has_field_verified_candidate=False,
        carrying_capacity_assessed=True,
        carrying_capacity_insufficient_evidence=True,
        total_carrying_capacity=500,
        population_to_house=100,
        base_site_suitability=80.0,
    )

    # Must be capped at 55.0 (unverified candidates), NOT 40.0 (demo-only)!
    assert score == 55.0
    assert "CANDIDATE_SITES_SYNTHETIC_BENCHMARK_ONLY" not in gaps
    assert "FIELD_VERIFICATION_PENDING_ON_RECEPTION_SITES" in gaps
    assert "CARRYING_CAPACITY_INSUFFICIENT_EVIDENCE" in gaps


def test_readiness_no_candidates_cap_20():
    """No candidate sites at all yields maximum readiness 20.0."""
    score, level, gaps, codes = calculate_reception_readiness(
        candidate_sites_count=0,
        only_demo_candidates=False,
        has_field_verified_candidate=False,
        total_carrying_capacity=0,
    )
    assert score <= 20.0
    assert "NO_CANDIDATE_SITES_IDENTIFIED_IN_DISTRICT" in gaps


def test_readiness_only_demo_candidates_cap_40():
    """Only demo candidate sites (no modeled parcels) yields maximum readiness 40.0."""
    score, level, gaps, codes = calculate_reception_readiness(
        candidate_sites_count=2,
        only_demo_candidates=True,
        has_modeled_candidates=False,
        has_field_verified_candidate=False,
        total_carrying_capacity=500,
        population_to_house=100,
        base_site_suitability=85.0,
    )
    assert score <= 40.0
    assert "CANDIDATE_SITES_SYNTHETIC_BENCHMARK_ONLY" in gaps


def test_capacity_assessed_vs_not_assessed_distinction():
    """Differentiate CARRYING_CAPACITY_NOT_ASSESSED from CARRYING_CAPACITY_INSUFFICIENT_EVIDENCE."""
    # Never assessed
    _, _, gaps_never, codes_never = calculate_reception_readiness(
        candidate_sites_count=1,
        carrying_capacity_assessed=False,
        total_carrying_capacity=0,
    )
    assert "CARRYING_CAPACITY_NOT_ASSESSED" in gaps_never

    # Assessed with insufficient/preliminary evidence
    _, _, gaps_prelim, codes_prelim = calculate_reception_readiness(
        candidate_sites_count=1,
        carrying_capacity_assessed=True,
        carrying_capacity_insufficient_evidence=True,
        total_carrying_capacity=0,
    )
    assert "CARRYING_CAPACITY_INSUFFICIENT_EVIDENCE" in gaps_prelim
    assert "CARRYING_CAPACITY_NOT_ASSESSED" not in gaps_prelim


# ==============================================================================
# 1. Task 8: Relocation Optimization Engine Tests
# ==============================================================================

def test_optimization_respects_capacity_and_excludes_rejected(db):
    """Allocation must strictly respect candidate capacities and never allocate to rejected candidates."""
    engine = RelocationOptimizationEngine(db)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=500,
    )
    res = engine.run_optimization(req)

    assert len(res.plans) == 3
    plan_a = res.plans[0]
    for alloc in plan_a.allocations:
        assert alloc.allocated_population > 0
        assert alloc.allocated_population <= alloc.usable_capacity
        # Check that no allocated candidate has status REJECTED
        if alloc.candidate_type == "PARCEL":
            p = db.query(CandidateParcel).filter(CandidateParcel.id == alloc.candidate_id).first()
            if p:
                assert p.status != "REJECTED"


def test_decision_support_mode_insufficient_verified_capacity(db):
    """DECISION_SUPPORT mode must return INSUFFICIENT_VERIFIED_CAPACITY when unverified."""
    engine = RelocationOptimizationEngine(db)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="DECISION_SUPPORT",
        target_population=1256,
    )
    res = engine.run_optimization(req)

    assert res.solver_status == "INSUFFICIENT_VERIFIED_CAPACITY"
    assert len(res.plans) == 0


def test_partial_allocation_when_target_exceeds_available(db):
    """If target population exceeds candidate capacity, engine returns PARTIAL_ALLOCATION without crashing."""
    engine = RelocationOptimizationEngine(db)
    # Target 50,000 people with max_sites=1 (single site cannot hold 50k)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=50000,
        max_sites=1,
    )
    res = engine.run_optimization(req)

    assert res.solver_status == "PARTIAL_ALLOCATION"
    plan = res.plans[0]
    assert plan.unallocated_population > 0
    assert plan.allocated_population < 50000
    assert "USABLE_RECEPTION_CAPACITY_EXHAUSTED" in plan.binding_constraints or "MAX_DESTINATION_SITES_LIMIT_REACHED" in plan.binding_constraints


def test_multiple_non_dominated_alternatives_and_trade_offs(db):
    """Generates ALTERNATIVE A (Min Distance), ALTERNATIVE B (Min Site Count), and ALTERNATIVE C (Balanced)."""
    engine = RelocationOptimizationEngine(db)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=1256,
    )
    res = engine.run_optimization(req)

    plan_names = [p.plan_name for p in res.plans]
    assert any("MIN_DISTANCE" in n for n in plan_names)
    assert any("MIN_SITE_COUNT" in n for n in plan_names)
    assert any("BALANCED" in n for n in plan_names)

    # Strategy trade-offs: MIN_SITE_COUNT should have <= sites than or equal to BALANCED
    min_dist_plan = next(p for p in res.plans if "MIN_DISTANCE" in p.plan_name)
    min_site_plan = next(p for p in res.plans if "MIN_SITE_COUNT" in p.plan_name)

    # Distance in Min Distance plan should be short
    assert min_dist_plan.average_distance_km <= 15.0
    assert min_site_plan.site_count <= 2


def test_unknown_livelihood_and_community_cohesion(db):
    """Livelihood and community metrics must be explicitly UNKNOWN, never zero or fabricated."""
    engine = RelocationOptimizationEngine(db)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=500,
    )
    res = engine.run_optimization(req)
    plan = res.plans[0]

    assert plan.livelihood_disruption == "UNKNOWN"
    assert "UNKNOWN" in (plan.community_fragmentation or "")


def test_deterministic_optimizer_reproducibility(db):
    """Running optimization twice with identical inputs yields identical allocations."""
    engine = RelocationOptimizationEngine(db)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=600,
    )
    res1 = engine.run_optimization(req)
    res2 = engine.run_optimization(req)

    p1 = res1.plans[0]
    p2 = res2.plans[0]

    assert p1.allocated_population == p2.allocated_population
    assert p1.site_count == p2.site_count
    assert p1.average_distance_km == p2.average_distance_km


# ==============================================================================
# 2. Task 9: Digital Twin & Scenario Lab Tests
# ==============================================================================

def test_digital_twin_destination_service_loads(db):
    """Digital Twin accurately simulates loads across the 8 PRAYAAS carrying-capacity dimensions."""
    engine = RelocationOptimizationEngine(db)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=800,
    )
    res = engine.run_optimization(req)
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    sim = twin.simulate_plan(plan_id, ScenarioParameters())

    assert sim.overall_plan_feasibility in ("PASS", "DEGRADED", "FAIL", "UNKNOWN")
    assert len(sim.destinations) > 0

    first_dest = sim.destinations[0]
    dim_names = [d.dimension for d in first_dest.dimensions]
    assert "Housing" in dim_names
    assert "Water" in dim_names
    assert "Sanitation" in dim_names
    assert "Healthcare" in dim_names
    assert "Education" in dim_names
    assert "Transport" in dim_names
    assert "Utilities" in dim_names
    assert "Environment" in dim_names


def test_unknown_services_remain_unknown_in_digital_twin(db):
    """Healthcare, Sanitation, Utilities with unknown evidence MUST report UNKNOWN status, not 0% or PASS."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=500))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    sim = twin.simulate_plan(plan_id, ScenarioParameters())

    first_dest = sim.destinations[0]
    health = next(d for d in first_dest.dimensions if d.dimension == "Healthcare")
    sanitation = next(d for d in first_dest.dimensions if d.dimension == "Sanitation")
    utilities = next(d for d in first_dest.dimensions if d.dimension == "Utilities")

    assert health.status == "UNKNOWN"
    assert health.utilization_pct is None
    assert sanitation.status == "UNKNOWN"
    assert utilities.status == "UNKNOWN"


def test_digital_twin_water_reduction_scenario(db):
    """Water reduction (-50%) triggers higher water utilization or bottleneck."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=1200))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    base_sim = twin.simulate_plan(plan_id, ScenarioParameters(water_supply_change_pct=0.0))
    stress_sim = twin.simulate_plan(plan_id, ScenarioParameters(water_supply_change_pct=-50.0))

    base_water = next(d for d in base_sim.destinations[0].dimensions if d.dimension == "Water")
    stress_water = next(d for d in stress_sim.destinations[0].dimensions if d.dimension == "Water")

    assert stress_water.utilization_pct > base_water.utilization_pct


def test_digital_twin_road_failure_scenario(db):
    """Road outage scenario marks transport as EXCEEDED and degrades/fails plan."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=500))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    sim = twin.simulate_plan(plan_id, ScenarioParameters(road_unavailable=True))

    assert sim.overall_plan_feasibility == "FAIL"
    trans = next(d for d in sim.destinations[0].dimensions if d.dimension == "Transport")
    assert trans.status == "EXCEEDED"


def test_digital_twin_candidate_outage_scenario(db):
    """Disabling an assigned candidate parcel renders population unallocated and fails plan."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=500))
    plan = res.plans[0]
    assigned_cand_id = plan.allocations[0].candidate_id

    twin = DigitalTwinEngine(db)
    sim = twin.simulate_plan(plan.id, ScenarioParameters(unavailable_candidate_ids=[assigned_cand_id]))

    assert sim.overall_plan_feasibility == "FAIL"
    assert sim.total_unallocated > 0


def test_counterfactual_infrastructure_upgrade_scenario(db):
    """Counterfactual water upgrade expands water capacity and lowers utilization."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=1000))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    base_sim = twin.simulate_plan(plan_id, ScenarioParameters())
    upg_sim = twin.simulate_plan(plan_id, ScenarioParameters(water_upgrade_capacity=500))

    base_water = next(d for d in base_sim.destinations[0].dimensions if d.dimension == "Water")
    upg_water = next(d for d in upg_sim.destinations[0].dimensions if d.dimension == "Water")

    assert upg_water.capacity > base_water.capacity
    assert upg_water.utilization_pct < base_water.utilization_pct


def test_plan_robustness_evaluation(db):
    """Plan robustness stress suite tests multi-scenario resilience without faking AI predictions."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=800))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    rob = twin.evaluate_plan_robustness(plan_id)

    assert rob.tested_scenarios >= 5
    assert rob.passed_scenarios + rob.degraded_scenarios + rob.failed_scenarios + rob.unknown_scenarios == rob.tested_scenarios
    assert 0.0 <= rob.robustness_score <= 100.0


def test_need_score_remains_strictly_unchanged(db):
    """Relocation Need Score must remain strictly invariant regardless of optimization or candidate availability."""
    reloc_engine = RelocationEngine(db)
    need_before = reloc_engine.assess_habitation("HAB-002").need_score

    # Run optimization
    opt_engine = RelocationOptimizationEngine(db)
    opt_engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=1256))

    need_after = reloc_engine.assess_habitation("HAB-002").need_score

    assert need_before == need_after
    assert need_after == 71.9


# ==============================================================================
# 3. Correctness Patch Regression Tests
# ==============================================================================

def test_readiness_55_blockers_not_ready_for_execution(db):
    """Need ~71.9, Readiness 55 with blockers must map to MODERATE_READINESS_REVIEW, never READY_FOR_EXECUTION."""
    reloc_engine = RelocationEngine(db)
    assessment = reloc_engine.assess_habitation("HAB-002")

    assert assessment.readiness_score == 55.0
    assert "MODERATE_READINESS_REVIEW" in assessment.reason_codes
    assert "READY_FOR_EXECUTION" not in assessment.reason_codes
    assert "READY_FOR_EXECUTION" not in assessment.explanation
    assert "FIELD_VERIFICATION_PENDING_ON_RECEPTION_SITES" in assessment.readiness_gaps
    assert "CARRYING_CAPACITY_INSUFFICIENT_EVIDENCE" in assessment.readiness_gaps


def test_critical_unknown_dimension_prevents_overall_pass(db):
    """When critical dimensions are UNKNOWN and no constraints fail, overall feasibility is UNKNOWN (not PASS)."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=600))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    sim = twin.simulate_plan(plan_id, ScenarioParameters())

    assert sim.overall_plan_feasibility == "UNKNOWN"
    assert sim.overall_plan_feasibility != "PASS"
    assert sim.limiting_bottleneck == "KNOWN_DIMENSIONS_FEASIBLE"


def test_known_critical_failure_overrides_unknown(db):
    """If a critical constraint is exceeded, FAIL strictly overrides UNKNOWN."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=1256))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    # Severe water reduction causes water capacity to fall below demand -> EXCEEDED
    sim = twin.simulate_plan(plan_id, ScenarioParameters(water_supply_change_pct=-20.0))

    assert sim.overall_plan_feasibility == "FAIL"
    assert sim.limiting_bottleneck == "Water"


def test_utilization_over_100_percent_is_exceeded(db):
    """Utilization > 100% must have status EXCEEDED, never OK or WARNING."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=1256))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    # At -20% water, utilization is 1256 / 1200 = 104.7%
    sim = twin.simulate_plan(plan_id, ScenarioParameters(water_supply_change_pct=-20.0))

    water_dim = next(d for d in sim.destinations[0].dimensions if d.dimension == "Water")
    assert water_dim.utilization_pct > 100.0
    assert water_dim.status == "EXCEEDED"


def test_critical_over_100_percent_is_fail(db):
    """When a critical service utilization exceeds 100%, destination is EXCEEDED and scenario is FAIL."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=1256))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    sim = twin.simulate_plan(plan_id, ScenarioParameters(water_supply_change_pct=-20.0))

    assert sim.destinations[0].overall_status == "EXCEEDED"
    assert sim.overall_plan_feasibility == "FAIL"


def test_demo_candidates_excluded_by_default_when_modeled_exist(db):
    """Default optimization excludes DEMO benchmark sites when MODELED candidate parcels exist."""
    engine = RelocationOptimizationEngine(db)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=1256,
        include_demo_candidates=False,
    )
    res = engine.run_optimization(req)

    for plan in res.plans:
        for alloc in plan.allocations:
            assert alloc.candidate_type == "PARCEL"
            assert not alloc.evidence_status.startswith("DEMO")


def test_demo_candidates_explicitly_tagged_demo_comparison_only(db):
    """When DEMO candidates are enabled and allocated, plan must be tagged DEMO_COMPARISON_ONLY."""
    engine = RelocationOptimizationEngine(db)
    # Request large population that exhausts modeled parcels (if parcels < target or with demo enabled)
    req = RelocationOptimizationRunRequest(
        origin_habitation_id="HAB-002",
        mode="EXPLORATORY",
        target_population=2500,
        include_demo_candidates=True,
    )
    res = engine.run_optimization(req)

    # Any plan with demo allocations must have assumption_dependence="DEMO_COMPARISON_ONLY"
    for plan in res.plans:
        has_demo = any(a.evidence_status.startswith("DEMO") for a in plan.allocations)
        if has_demo:
            assert plan.assumption_dependence == "DEMO_COMPARISON_ONLY"
            assert "DEMO_COMPARISON_ONLY" in plan.binding_constraints
            assert "[DEMO_COMPARISON_ONLY]" in plan.explanation


def test_unknown_robustness_scenario_not_counted_as_pass(db):
    """UNKNOWN scenarios are tracked separately and strictly never counted as passed_scenarios."""
    engine = RelocationOptimizationEngine(db)
    res = engine.run_optimization(RelocationOptimizationRunRequest(origin_habitation_id="HAB-002", mode="EXPLORATORY", target_population=1256))
    plan_id = res.plans[0].id

    twin = DigitalTwinEngine(db)
    rob = twin.evaluate_plan_robustness(plan_id)

    assert rob.unknown_scenarios > 0
    assert rob.passed_scenarios == 0  # Since critical dimensions are UNKNOWN, baseline & upgrade cannot be PASS
    assert rob.unknown_scenarios + rob.failed_scenarios + rob.degraded_scenarios + rob.passed_scenarios == rob.tested_scenarios
