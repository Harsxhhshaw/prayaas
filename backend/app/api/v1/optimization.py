"""API Router for Multi-Site Relocation Optimization."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.optimization import RelocationOptimizationRun, RelocationPlan
from app.schemas.optimization import (
    RelocationAllocationSchema,
    RelocationOptimizationRunRequest,
    RelocationOptimizationRunResponse,
    RelocationPlanSchema,
)
from app.services.optimization.engine import RelocationOptimizationEngine

router = APIRouter(prefix="/optimization", tags=["Relocation Optimization"])


@router.post("/run", response_model=RelocationOptimizationRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_optimization_run(
    request: RelocationOptimizationRunRequest,
    db: Session = Depends(get_db),
) -> RelocationOptimizationRunResponse:
    """Trigger multi-site relocation optimization producing non-dominated trade-off plans."""
    engine = RelocationOptimizationEngine(db)
    try:
        return engine.run_optimization(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Optimization failed: {e}")


@router.get("/runs/{run_id}", response_model=RelocationOptimizationRunResponse)
def get_optimization_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> RelocationOptimizationRunResponse:
    """Fetch an optimization run and all generated alternative plans."""
    run = db.query(RelocationOptimizationRun).filter(RelocationOptimizationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found.")

    plans_schema: list[RelocationPlanSchema] = []
    for p in run.plans:
        allocs = [
            RelocationAllocationSchema(
                id=a.id,
                candidate_type=a.candidate_type,
                candidate_id=a.candidate_id,
                allocated_population=a.allocated_population,
                usable_capacity=a.usable_capacity,
                capacity_utilization_pct=a.capacity_utilization_pct,
                distance_km=a.distance_km,
                evidence_status=a.evidence_status,
                metadata=a.metadata_json,
            )
            for a in p.allocations
        ]
        plans_schema.append(
            RelocationPlanSchema(
                id=p.id,
                plan_name=p.plan_name,
                strategy_type=p.strategy_type,
                allocated_population=p.allocated_population,
                unallocated_population=p.unallocated_population,
                allocation_ratio=p.allocation_ratio,
                site_count=p.site_count,
                average_distance_km=p.average_distance_km,
                max_distance_km=p.max_distance_km,
                capacity_utilization_percent=p.capacity_utilization_percent,
                relative_infrastructure_burden=p.relative_infrastructure_burden,
                community_fragmentation=p.community_fragmentation,
                livelihood_disruption=p.livelihood_disruption,
                environmental_pressure=p.environmental_pressure,
                evidence_confidence=p.evidence_confidence,
                assumption_dependence=p.assumption_dependence,
                explanation=p.explanation,
                binding_constraints=p.binding_constraints,
                allocations=allocs,
            )
        )

    return RelocationOptimizationRunResponse(
        run_id=run.id,
        origin_habitation_id=run.origin_habitation_id,
        analysis_version=run.analysis_version,
        config_version=run.config_version,
        mode=run.mode,
        target_population=run.target_population,
        solver_status=run.solver_status,
        candidates_considered_count=len(run.candidate_ids),
        usable_candidates_count=len(run.candidate_ids),
        plans=plans_schema,
    )


@router.get("/plans/{plan_id}", response_model=RelocationPlanSchema)
def get_relocation_plan(
    plan_id: str,
    db: Session = Depends(get_db),
) -> RelocationPlanSchema:
    """Retrieve details and allocations for a specific relocation plan alternative."""
    plan = db.query(RelocationPlan).filter(RelocationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")

    allocs = [
        RelocationAllocationSchema(
            id=a.id,
            candidate_type=a.candidate_type,
            candidate_id=a.candidate_id,
            allocated_population=a.allocated_population,
            usable_capacity=a.usable_capacity,
            capacity_utilization_pct=a.capacity_utilization_pct,
            distance_km=a.distance_km,
            evidence_status=a.evidence_status,
            metadata=a.metadata_json,
        )
        for a in plan.allocations
    ]
    return RelocationPlanSchema(
        id=plan.id,
        plan_name=plan.plan_name,
        strategy_type=plan.strategy_type,
        allocated_population=plan.allocated_population,
        unallocated_population=plan.unallocated_population,
        allocation_ratio=plan.allocation_ratio,
        site_count=plan.site_count,
        average_distance_km=plan.average_distance_km,
        max_distance_km=plan.max_distance_km,
        capacity_utilization_percent=plan.capacity_utilization_percent,
        relative_infrastructure_burden=plan.relative_infrastructure_burden,
        community_fragmentation=plan.community_fragmentation,
        livelihood_disruption=plan.livelihood_disruption,
        environmental_pressure=plan.environmental_pressure,
        evidence_confidence=plan.evidence_confidence,
        assumption_dependence=plan.assumption_dependence,
        explanation=plan.explanation,
        binding_constraints=plan.binding_constraints,
        allocations=allocs,
    )


@router.get("/habitations/{habitation_id}/latest-plans", response_model=list[RelocationPlanSchema])
def get_latest_plans_for_habitation(
    habitation_id: str,
    db: Session = Depends(get_db),
) -> list[RelocationPlanSchema]:
    """Retrieve the latest alternative plans generated for a specific habitation."""
    run = (
        db.query(RelocationOptimizationRun)
        .filter(RelocationOptimizationRun.origin_habitation_id == habitation_id)
        .order_by(RelocationOptimizationRun.created_at.desc())
        .first()
    )
    if not run:
        return []

    plans_schema: list[RelocationPlanSchema] = []
    for p in run.plans:
        allocs = [
            RelocationAllocationSchema(
                id=a.id,
                candidate_type=a.candidate_type,
                candidate_id=a.candidate_id,
                allocated_population=a.allocated_population,
                usable_capacity=a.usable_capacity,
                capacity_utilization_pct=a.capacity_utilization_pct,
                distance_km=a.distance_km,
                evidence_status=a.evidence_status,
                metadata=a.metadata_json,
            )
            for a in p.allocations
        ]
        plans_schema.append(
            RelocationPlanSchema(
                id=p.id,
                plan_name=p.plan_name,
                strategy_type=p.strategy_type,
                allocated_population=p.allocated_population,
                unallocated_population=p.unallocated_population,
                allocation_ratio=p.allocation_ratio,
                site_count=p.site_count,
                average_distance_km=p.average_distance_km,
                max_distance_km=p.max_distance_km,
                capacity_utilization_percent=p.capacity_utilization_percent,
                relative_infrastructure_burden=p.relative_infrastructure_burden,
                community_fragmentation=p.community_fragmentation,
                livelihood_disruption=p.livelihood_disruption,
                environmental_pressure=p.environmental_pressure,
                evidence_confidence=p.evidence_confidence,
                assumption_dependence=p.assumption_dependence,
                explanation=p.explanation,
                binding_constraints=p.binding_constraints,
                allocations=allocs,
            )
        )
    return plans_schema
