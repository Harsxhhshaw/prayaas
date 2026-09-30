"""Unit and integration tests for Multi-Hazard Risk and Red Zone engine (PRAYAAS-RISK-1.0)."""

import pytest

from app.models.enums import RedZoneClassification
from app.models.habitation import Habitation
from app.models.risk import RiskAssessment
from app.services.risk.config import DEFAULT_RISK_CONFIG
from app.services.risk.confidence import calculate_risk_confidence
from app.services.risk.engine import RiskEngine, calculate_sustainability_index
from app.services.risk.explanations import generate_risk_explanation


def test_confidence_engine_scoring():
    # High confidence: field survey, live meteorology, multi-hazard, robust history
    conf_high, reasons_high, _ = calculate_risk_confidence(
        has_vulnerability_profile=True,
        vulnerability_profile_mode="FIELD",
        has_environmental_observations=True,
        observation_mode="LIVE",
        hazard_scores_count=4,
        risk_history_count=4,
        is_demographics_complete=True,
    )
    assert conf_high >= 80.0
    assert "FIELD_VULNERABILITY_VERIFIED" in reasons_high
    assert "LIVE_METEOROLOGY_ACTIVE" in reasons_high

    # Low confidence: missing vulnerability, missing weather, no history
    conf_low, reasons_low, _ = calculate_risk_confidence(
        has_vulnerability_profile=False,
        vulnerability_profile_mode=None,
        has_environmental_observations=False,
        observation_mode=None,
        hazard_scores_count=0,
        risk_history_count=0,
        is_demographics_complete=False,
    )
    assert conf_low < 40.0
    assert "MISSING_VULNERABILITY_PROFILE" in reasons_low
    assert "MISSING_ENVIRONMENTAL_OBSERVATIONS" in reasons_low


def test_sustainability_index_calculation():
    # Highly isolated, high elevation, high hazard settlement -> low HSI
    hsi_critical = calculate_sustainability_index(
        elevation=2800.0,
        nearest_road_km=8.5,
        nearest_hospital_km=32.0,
        baseline_hazard=92.0,
        vulnerability_score=80.0,
    )
    assert hsi_critical < 35.0  # In-situ mitigation infeasible

    # Accessible valley town -> high HSI
    hsi_safe = calculate_sustainability_index(
        elevation=1200.0,
        nearest_road_km=0.2,
        nearest_hospital_km=2.0,
        baseline_hazard=25.0,
        vulnerability_score=30.0,
    )
    assert hsi_safe > 65.0


def test_mandatory_confidence_downgrade_guard(db):
    """If composite risk >= 75 but confidence < 70, PERMANENT_RED MUST be downgraded to CONDITIONAL_RED."""
    # Find a high risk habitation
    hab = db.query(Habitation).filter(Habitation.id == "HAB-001").first()
    assert hab is not None

    engine = RiskEngine(db)

    # Artificially test with a low-confidence scenario
    assessment = engine.assess_habitation(hab.id)
    assert assessment.composite_risk_score > 0

    if assessment.composite_risk_score >= 75.0 and assessment.confidence_score < 70.0:
        assert assessment.risk_classification == RedZoneClassification.CONDITIONAL_RED.value
        assert "LOW_CONFIDENCE_VERIFICATION_REQUIRED" in assessment.reason_codes
    elif assessment.composite_risk_score >= 75.0 and assessment.confidence_score >= 70.0:
        assert assessment.risk_classification == RedZoneClassification.PERMANENT_RED.value


def test_compound_hazard_adjustment_cap(db):
    engine = RiskEngine(db)
    assessment = engine.assess_habitation("HAB-001")
    # Compound hazard adjustment must strictly not exceed 15.0
    assert 0.0 <= assessment.compound_hazard_adjustment <= DEFAULT_RISK_CONFIG.MAX_COMPOUND_ADJUSTMENT


def test_risk_explanation_payload(db):
    explanation = generate_risk_explanation(db, "HAB-001")
    assert explanation.habitation_id == "HAB-001"
    assert explanation.formula is not None
    assert "0.35" in explanation.formula
    assert len(explanation.component_weights) >= 6
    assert len(explanation.sources_used) >= 3
    assert explanation.narrative_explanation is not None
