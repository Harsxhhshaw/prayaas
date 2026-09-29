"""API Router for Digital Twin & Scenario Lab."""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.optimization import (
    DigitalTwinSimulationResponse,
    PlanRobustnessResponse,
    ScenarioParameters,
)
from app.services.digital_twin.engine import DigitalTwinEngine

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin & Scenario Lab"])


class SimulateScenarioRequest(BaseModel):
    plan_id: str
    scenario_name: str = "CUSTOM_SCENARIO"
    parameters: ScenarioParameters


@router.post("/simulate", response_model=DigitalTwinSimulationResponse)
def simulate_plan_scenario(
    request: SimulateScenarioRequest,
    db: Session = Depends(get_db),
) -> DigitalTwinSimulationResponse:
    """Run a deterministic scenario simulation against a relocation plan."""
    engine = DigitalTwinEngine(db)
    try:
        return engine.simulate_plan(
            plan_id=request.plan_id,
            parameters=request.parameters,
            scenario_name=request.scenario_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation failed: {e}")


@router.post("/plans/{plan_id}/robustness", response_model=PlanRobustnessResponse)
def evaluate_plan_robustness(
    plan_id: str,
    db: Session = Depends(get_db),
) -> PlanRobustnessResponse:
    """Run full stress-testing suite against a relocation plan to evaluate robustness."""
    engine = DigitalTwinEngine(db)
    try:
        return engine.evaluate_plan_robustness(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Robustness evaluation failed: {e}")
