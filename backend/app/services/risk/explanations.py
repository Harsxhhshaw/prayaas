"""Deterministic explanation generator for Multi-Hazard Risk Assessments."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.models.habitation import Habitation
from app.models.risk import RiskAssessment
from app.schemas.risk import RiskAssessmentExplanationResponse
from app.services.risk.config import DEFAULT_RISK_CONFIG


def generate_risk_explanation(db: Session, habitation_id: str) -> RiskAssessmentExplanationResponse:
    hab = db.query(Habitation).filter(Habitation.id == habitation_id).first()
    if not hab:
        raise ValueError(f"Habitation with id {habitation_id} not found")

    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.habitation_id == habitation_id)
        .order_by(RiskAssessment.calculated_at.desc())
        .first()
    )

    if not assessment:
        # Run risk engine to create an assessment if none exists
        from app.services.risk.engine import RiskEngine

        engine = RiskEngine(db)
        assessment = engine.assess_habitation(habitation_id)

    weights = {
        "Hazard Score (35%)": DEFAULT_RISK_CONFIG.HAZARD_WEIGHT,
        "Exposure Score (20%)": DEFAULT_RISK_CONFIG.EXPOSURE_WEIGHT,
        "Vulnerability Score (20%)": DEFAULT_RISK_CONFIG.VULNERABILITY_WEIGHT,
        "Adaptive Capacity Deficit (10%)": DEFAULT_RISK_CONFIG.ADAPTIVE_DEFICIT_WEIGHT,
        "Disaster History (10%)": DEFAULT_RISK_CONFIG.HISTORY_WEIGHT,
        "Risk Trend (5%)": DEFAULT_RISK_CONFIG.TREND_WEIGHT,
    }

    values = {
        "Hazard Score": assessment.hazard_score,
        "Baseline Hazard": assessment.baseline_hazard_score,
        "Dynamic Hazard": assessment.dynamic_hazard_score,
        "Exposure Score": assessment.exposure_score,
        "Vulnerability Score": assessment.vulnerability_score,
        "Adaptive Capacity Deficit": assessment.adaptive_capacity_deficit_score,
        "History Score": assessment.history_score,
        "Trend Score": assessment.trend_score,
    }

    sources: list[dict[str, Any]] = [
        {"name": "GSI Landslide Susceptibility Atlas", "type": "HAZARD_BASELINE", "status": "VERIFIED"},
        {"name": "Open-Meteo High-Resolution Precipitation", "type": "WEATHER_DYNAMIC", "status": "LIVE"},
        {"name": "Census & SDMA Social Vulnerability Survey", "type": "DEMOGRAPHICS", "status": "FIELD/DEMO"},
        {"name": "OpenStreetMap Road & Hospital Distances", "type": "INFRASTRUCTURE", "status": "PUBLIC"},
    ]

    formula_str = (
        "Composite Risk = min(100, (0.35 * Hazard) + (0.20 * Exposure) + (0.20 * Vulnerability) + "
        "(0.10 * AdaptiveDeficit) + (0.10 * History) + (0.05 * Trend) + CompoundAdjustment)"
    )

    narrative = (
        f"Settlement {hab.name} is classified as {assessment.risk_classification} with an overall composite "
        f"risk score of {assessment.composite_risk_score:.1f}/100. The dominant physical hazard driving risk is "
        f"{assessment.dominant_hazard} (Baseline score: {assessment.baseline_hazard_score:.1f}, Dynamic monsoon "
        f"score: {assessment.dynamic_hazard_score:.1f}). Compound hazard adjustment added +{assessment.compound_hazard_adjustment:.1f} "
        f"points due to intersecting geological and meteorological risks. The Habitation Sustainability Index (HSI) "
        f"is {assessment.sustainability_index:.1f}/100."
    )

    confidence_rationale = (
        f"Assessment confidence is {assessment.confidence_score:.1f}%. Built from statutory hazard zones, "
        f"multi-year disaster event records, and live weather telemetry."
    )

    return RiskAssessmentExplanationResponse(
        id=assessment.id,
        habitation_id=habitation_id,
        habitation_name=hab.name,
        composite_risk_score=assessment.composite_risk_score,
        risk_classification=assessment.risk_classification,
        confidence_score=assessment.confidence_score,
        dominant_hazard=assessment.dominant_hazard,
        sustainability_index=assessment.sustainability_index,
        formula=formula_str,
        component_weights=weights,
        component_values=values,
        compound_hazard_adjustment=assessment.compound_hazard_adjustment,
        reason_codes=assessment.reason_codes,
        narrative_explanation=narrative,
        sources_used=sources,
        confidence_rationale=confidence_rationale,
        calculated_at=assessment.calculated_at.isoformat(),
    )
