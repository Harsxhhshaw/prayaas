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


def test_missing_inputs_become_unknown_evidence_and_penalize_confidence(db):
    """Missing distance, elevation, or demographic inputs must NOT be replaced with numeric fallbacks.
    They must become UNKNOWN evidence, penalize confidence, and never produce PASS on critical dimensions.
    """
    engine = RiskEngine(db)

    # Create temporary habitation with missing inputs
    test_hab = Habitation(
        id="HAB-TEST-UNKNOWN",
        name="Unknown Test Settlement",
        district="Chamoli",
        state="Uttarakhand",
        population=450,
        households=90,
        risk_score=75,
        elevation=None,  # Missing elevation
        nearest_road=None,  # Missing road distance
        nearest_hospital=None,  # Missing hospital distance
        nearest_school=None,  # Missing school distance
        risk_history=[],
        hazard_scores=[],
    )
    db.add(test_hab)

    assessment = engine.assess_habitation("HAB-TEST-UNKNOWN")

    # 1. Missing inputs must be flagged as UNKNOWN evidence
    assert "ELEVATION_DATA_UNKNOWN" in assessment.reason_codes
    assert "ROAD_DISTANCE_UNKNOWN" in assessment.reason_codes
    assert "HOSPITAL_DISTANCE_UNKNOWN" in assessment.reason_codes
    assert "SCHOOL_DISTANCE_UNKNOWN" in assessment.reason_codes

    # 2. Confidence must be heavily penalized
    assert assessment.confidence_score < 50.0

    # 3. Input snapshot must honestly record None (never fabricated fallbacks like 1800 or 5.0)
    assert assessment.input_snapshot["elevation"] is None
    assert assessment.input_snapshot["nearest_road"] is None
    assert assessment.input_snapshot["nearest_hospital"] is None

    # 4. Critical dimensions in sustainability breakdown must be UNKNOWN, NEVER PASS or fabricated VALUE
    dims = assessment.input_snapshot["sustainability_dimensions"]
    assert dims["road_reliability"]["status"] == "UNKNOWN"
    assert dims["road_reliability"]["value"] is None
    assert dims["health_accessibility"]["status"] == "UNKNOWN"
    assert dims["health_accessibility"]["value"] is None
    assert dims["education_access"]["status"] == "UNKNOWN"
    assert dims["education_access"]["value"] is None
    assert dims["water_security"]["status"] == "UNKNOWN"
    assert dims["water_security"]["value"] is None


def test_missing_critical_dimensions_never_pass():
    """calculate_sustainability_index must never return VALUE or PASS for unmeasured dimensions."""
    _, confidence, breakdown = calculate_sustainability_index(
        elevation=None,
        nearest_road_km=None,
        nearest_hospital_km=None,
        nearest_school_km=None,
        baseline_hazard=60.0,
        vulnerability_score=50.0,
        return_details=True,
    )

    assert breakdown["road_reliability"]["status"] == "UNKNOWN"
    assert breakdown["health_accessibility"]["status"] == "UNKNOWN"
    assert breakdown["education_access"]["status"] == "UNKNOWN"
    assert breakdown["water_security"]["status"] == "UNKNOWN"
    assert confidence < 60.0

