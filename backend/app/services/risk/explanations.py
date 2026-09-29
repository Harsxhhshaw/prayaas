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

    # Construct structured explanation sections
    input_snap = assessment.input_snapshot or {}
    model_scores = input_snap.get("model_scores") or {}
    model_agreement_level = input_snap.get("model_agreement_level", "MEDIUM")
    missing_comps = input_snap.get("missing_components") or []

    primary_drivers: list[str] = [
        f"Dominant physical hazard: {assessment.dominant_hazard} (Baseline score: {assessment.baseline_hazard_score:.1f}/100)",
        f"Structural baseline risk: {assessment.baseline_structural_risk:.1f}/100 with composite risk at {assessment.composite_risk_score:.1f}/100",
    ]
    if assessment.vulnerability_score >= 50.0:
        primary_drivers.append(f"High social vulnerability ({assessment.vulnerability_score:.1f}/100) amplifying exposure hazards")
    if assessment.exposure_score >= 50.0:
        primary_drivers.append(f"Direct habitation spatial exposure ({assessment.exposure_score:.1f}/100) within high-hazard perimeter")
    if assessment.compound_hazard_adjustment > 0:
        primary_drivers.append(f"Compound multi-hazard escalation added +{assessment.compound_hazard_adjustment:.1f} points")

    dynamic_factors: list[str] = []
    if assessment.risk_classification == "DYNAMIC_RED":
        dynamic_factors.append("DYNAMIC RED: Current conditions materially elevate risk. Immediate operational review recommended.")
    if assessment.dynamic_hazard_score > assessment.baseline_hazard_score:
        surge = assessment.dynamic_hazard_score - assessment.baseline_hazard_score
        dynamic_factors.append(f"Active meteorological surge (+{surge:.1f} pts) driven by recent rainfall")
    else:
        dynamic_factors.append("No active weather surge detected; meteorological conditions match seasonal baseline")
    rainfall_24h = input_snap.get("rainfall_24h")
    if rainfall_24h is not None:
        dynamic_factors.append(f"24-hour antecedent rainfall telemetry: {rainfall_24h:.1f} mm")
    dynamic_factors.append(f"Current dynamic risk score: {assessment.current_dynamic_risk:.1f}/100")

    protective_factors: list[str] = []
    if hab.nearest_road <= 2.0:
        protective_factors.append(f"Close arterial road access ({hab.nearest_road:.1f} km) supports emergency access and egress")
    else:
        protective_factors.append(f"Road access is distant ({hab.nearest_road:.1f} km), impeding emergency access")
    if hab.nearest_hospital <= 10.0:
        protective_factors.append(f"Medical facility accessible within {hab.nearest_hospital:.1f} km")
    if assessment.adaptive_capacity_score >= 40.0:
        protective_factors.append(f"Community adaptive capacity ({assessment.adaptive_capacity_score:.1f}/100) provides baseline shock resilience")
    if hab.elevation < 2000:
        protective_factors.append(f"Habitation elevation ({hab.elevation:.0f} m) avoids permafrost degradation hazards")

    model_agreement_data = {
        "level": model_agreement_level,
        "ahp_score": model_scores.get("AHP"),
        "frequency_ratio_score": model_scores.get("FREQUENCY_RATIO"),
        "ml_score": model_scores.get("RANDOM_FOREST"),
        "status": "AHP model CONFIGURED · CONSISTENT; Frequency Ratio model FRAMEWORK READY (DEMO / NOT VALIDATED); ML model UNTRAINED / INSUFFICIENT_REAL_DATA.",
    }


    data_limitations: list[str] = []
    if missing_comps:
        data_limitations.append(f"Missing analytical components: {', '.join(missing_comps)} (handled via available-weight normalization)")
    data_limitations.append("InSAR ground deformation and bore-hole geotechnical logs are not continuously monitored")
    data_limitations.append("Hazard inventory events rely on post-disaster administrative reports without sub-meter continuous telemetry")

    what_would_improve: list[str] = [
        "Execution of high-resolution UAV/LiDAR slope kinematics survey",
        "Door-to-door socio-economic household census update",
        "Installation of automated catchment rain gauge (AWS) for micro-climate precipitation",
        "Multi-temporal InSAR satellite interferometry for millimeter-scale subsidence tracking",
    ]

    from app.schemas.risk import RiskExplanationSections

    sections = RiskExplanationSections(
        primary_drivers=primary_drivers,
        dynamic_factors=dynamic_factors,
        protective_factors=protective_factors,
        model_agreement=model_agreement_data,
        data_limitations=data_limitations,
        what_would_improve_confidence=what_would_improve,
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
        sections=sections,
    )
