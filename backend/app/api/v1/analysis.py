"""Analytical intelligence endpoints for Multi-Hazard Risk and Red Zone Classification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import relocation_assessment_to_dict, risk_assessment_to_dict
from app.models.habitation import Habitation
from app.models.hazard_zone import HazardZone
from app.schemas.relocation import RelocationAssessmentResponse
from app.schemas.risk import (
    RedZoneEvaluationItem,
    RedZoneIntelligenceResponse,
    RiskAssessmentResponse,
)
from app.services.relocation.engine import RelocationEngine
from app.services.risk.engine import RiskEngine

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/risk/habitations/{habitation_id}", response_model=RiskAssessmentResponse)
def run_habitation_risk_assessment(habitation_id: str, db: Session = Depends(get_db)):
    """Run deterministic multi-hazard risk engine (PRAYAAS-RISK-1.0) on a habitation."""
    engine = RiskEngine(db)
    try:
        assessment = engine.assess_habitation(habitation_id)
        return risk_assessment_to_dict(assessment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/risk/districts/{district_id}", response_model=list[RiskAssessmentResponse])
def run_district_risk_assessments(district_id: str, db: Session = Depends(get_db)):
    """Run multi-hazard risk engine for all habitations in a district."""
    habitations = db.query(Habitation).filter(Habitation.district_id == district_id).all()
    if not habitations:
        # Fallback to district name if district_id is name
        habitations = db.query(Habitation).filter(Habitation.district == district_id).all()

    engine = RiskEngine(db)
    results = []
    for hab in habitations:
        assessment = engine.assess_habitation(hab.id)
        results.append(risk_assessment_to_dict(assessment))
    return results


@router.post("/relocation/habitations/{habitation_id}", response_model=RelocationAssessmentResponse)
def run_habitation_relocation_assessment(habitation_id: str, db: Session = Depends(get_db)):
    """Run relocation need and readiness engine (PRAYAAS-RELOCATION-1.0) on a habitation."""
    engine = RelocationEngine(db)
    try:
        assessment = engine.assess_habitation(habitation_id)
        return relocation_assessment_to_dict(assessment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/red-zones", response_model=RedZoneIntelligenceResponse)
def evaluate_red_zones(db: Session = Depends(get_db)):
    """Evaluate and classify all statutory Red Zones with confidence and dynamic surge intelligence."""
    zones = db.query(HazardZone).order_by(HazardZone.composite_risk_score.desc()).all()
    items: list[RedZoneEvaluationItem] = []
    breakdown: dict[str, int] = {}

    for z in zones:
        # Assess classification
        score = z.composite_risk_score
        confidence = 65.0  # Default baseline for statutory zones
        dominant = z.hazard_types[0] if (z.hazard_types and len(z.hazard_types) > 0) else "LANDSLIDE"
        reasons = []

        if score >= 75:
            # Downgrade guard: If confidence < 70, cannot be PERMANENT_RED without field audit
            if confidence >= 70:
                classification = "PERMANENT_RED"
                reasons.append("STATUTORY_PERMANENT_RED_ZONE")
            else:
                classification = "CONDITIONAL_RED"
                reasons.append("LOW_CONFIDENCE_FIELD_VERIFICATION_REQUIRED")
        elif score >= 60:
            classification = "CONDITIONAL_RED"
            reasons.append("HIGH_STRUCTURAL_HAZARD")
        elif score >= 40:
            classification = "WATCH"
            reasons.append("ELEVATED_VULNERABILITY_ZONE")
        else:
            classification = "ACCEPTABLE"

        breakdown[classification] = breakdown.get(classification, 0) + 1

        items.append(
            RedZoneEvaluationItem(
                id=z.id,
                name=z.name,
                classification=classification,
                composite_risk_score=float(score),
                dominant_hazard=dominant,
                confidence_score=confidence,
                habitation_count=z.habitation_count,
                population_affected=z.population_affected,
                computed_area_sq_km=z.computed_area_sq_km,
                source_declared_area_sq_km=z.source_declared_area_sq_km or z.area_km_sq,
                reason_codes=reasons,
                requires_field_verification=classification == "CONDITIONAL_RED" and score >= 75,
            )
        )

    return RedZoneIntelligenceResponse(
        red_zones=items,
        total=len(items),
        breakdown_by_classification=breakdown,
    )
