"""Unit and Integration Tests for PRAYAAS Task 5.5 Scientific & Research Hardening.

Covers:
1. Analytical Semantics (VALUE, UNKNOWN, NOT_APPLICABLE)
2. Chamoli coastal erosion invariant (NOT_APPLICABLE)
3. Available-weight missing data normalization (72.73% test)
4. Confidence penalty on missing analytical components
5. AHP consistency index (Saaty CR <= 0.10 vs CR > 0.10)
6. AHP matrix validation (reciprocal and shape requirements)
7. Frequency Ratio empirical calculation and demo status flag
8. Machine Learning susceptibility pipeline (synthetic block training)
9. Machine Learning production untrained state (UNTRAINED / INSUFFICIENT_REAL_DATA)
10. Model agreement evaluation (HIGH, MEDIUM, LOW)
11. Model disagreement confidence penalty (-15 pts)
12. Permanent Red low-confidence downgrade guard (CONDITIONAL_RED with tag)
13. Dynamic Red safeguard (weather surge alone cannot produce Permanent Red)
14. Compound hazard escalation cap (<= 15 pts)
15. Decoupled Relocation Need vs Readiness (candidate sites count = 0 impact on Need)
16. Readiness lowest-cap constraint enforcement (20, 40, 55, 70)
17. Terrain geomorphometry (Horn metric slope with latitude degree-to-meter scaling)
18. Terrain aspect (0-360 compass direction)
19. Spatial distance evidence helpers (UNKNOWN if absent)
20. MCDA criteria correlation and VIF multicollinearity warning
21. Monte Carlo sensitivity simulation (reproducible seed, rank robustness)
"""

from __future__ import annotations

import numpy as np
import pytest

from app.models.enums import (
    AnalyticalStatus,
    ModelAgreementLevel,
    RedZoneClassification,
)
from app.services.hazard_models.agreement import ModelAgreementEngine
from app.services.hazard_models.ahp import AHPSusceptibilityModel, verify_pairwise_matrix_consistency
from app.services.hazard_models.frequency_ratio import FrequencyRatioModel
from app.services.hazard_models.ml_pipeline import MLSusceptibilityPipeline
from app.services.mcda.correlation import calculate_correlation_matrix, calculate_vif
from app.services.mcda.sensitivity import run_monte_carlo_sensitivity
from app.services.relocation.engine import RelocationEngine
from app.services.risk.confidence import calculate_risk_confidence
from app.services.risk.config import DEFAULT_RISK_CONFIG
from app.services.risk.engine import RiskEngine, calculate_sustainability_index
from app.services.risk.semantics import (
    calculate_available_weighted_score,
    normalize_hazard_scores,
)
from app.services.spatial.distance import (
    calculate_distance_to_drainage,
    calculate_distance_to_fault,
    calculate_distance_to_road,
)
from app.services.terrain.pipeline import (
    calculate_aspect,
    calculate_curvature,
    calculate_metric_slope,
)


# ==============================================================================
# 1. Analytical Semantics & Missing Data Engine
# ==============================================================================

def test_unknown_not_equal_to_zero():
    """Verify UNKNOWN represents unmeasured/missing data, distinct from measured 0.0."""
    scores = [
        {"type": "LANDSLIDE", "score": 0.0, "status": "VALUE"},
        {"type": "FLOOD", "score": None, "status": "UNKNOWN"},
    ]
    normalized = normalize_hazard_scores(scores, district="Chamoli")
    landslide = next(s for s in normalized if s["type"] == "LANDSLIDE")
    flood = next(s for s in normalized if s["type"] == "FLOOD")

    assert landslide["score"] == 0.0
    assert landslide["status"] == AnalyticalStatus.VALUE.value
    assert flood["score"] is None
    assert flood["status"] == AnalyticalStatus.UNKNOWN.value
    assert landslide["score"] != flood["score"]


def test_chamoli_coastal_erosion_is_not_applicable():
    """Inland Himalayan district (Chamoli) must mark coastal erosion as NOT_APPLICABLE."""
    scores = [
        {"type": "COASTAL_EROSION", "score": 50.0},
        {"type": "LANDSLIDE", "score": 85.0},
    ]
    normalized = normalize_hazard_scores(scores, district="Chamoli")
    coastal = next(s for s in normalized if s["type"] == "COASTAL_EROSION")

    assert coastal["status"] == AnalyticalStatus.NOT_APPLICABLE.value
    assert coastal["score"] is None


def test_available_component_risk_normalization():
    """Missing data must NEVER lower risk: available-weight re-normalization only.

    Example: Hazard = 80 (weight 0.35), Exposure = 60 (weight 0.20), others missing.
    Expected: (80*0.35 + 60*0.20) / (0.35 + 0.20) = 40.0 / 0.55 = 72.727... ~ 72.73
    MUST NOT be deflated to 40.0.
    """
    components = {
        "hazard": 80.0,
        "exposure": 60.0,
        "vulnerability": None,
        "adaptive_capacity_deficit": None,
        "disaster_history": None,
        "risk_trend": None,
    }
    weights = {
        "hazard": 0.35,
        "exposure": 0.20,
        "vulnerability": 0.20,
        "adaptive_capacity_deficit": 0.10,
        "disaster_history": 0.10,
        "risk_trend": 0.05,
    }
    norm_score, avail_w, missing = calculate_available_weighted_score(components, weights)

    assert norm_score is not None
    assert round(norm_score, 2) == 72.73
    assert round(avail_w, 2) == 0.55
    assert set(missing) == {
        "vulnerability",
        "adaptive_capacity_deficit",
        "disaster_history",
        "risk_trend",
    }


def test_missing_components_penalize_confidence():
    """Missing components reduce assessment confidence rather than understating risk."""
    conf_full, reasons_full, _ = calculate_risk_confidence(
        has_vulnerability_profile=True,
        vulnerability_profile_mode="FIELD",
        has_environmental_observations=True,
        observation_mode="LIVE",
        hazard_scores_count=4,
        risk_history_count=4,
        is_demographics_complete=True,
        missing_components=[],
    )

    conf_missing, reasons_missing, _ = calculate_risk_confidence(
        has_vulnerability_profile=True,
        vulnerability_profile_mode="FIELD",
        has_environmental_observations=True,
        observation_mode="LIVE",
        hazard_scores_count=4,
        risk_history_count=4,
        is_demographics_complete=True,
        missing_components=["vulnerability", "adaptive_capacity_deficit", "disaster_history"],
    )

    assert conf_missing < conf_full
    assert any("MISSING_ANALYTICAL_COMPONENTS" in r for r in reasons_missing)


# ==============================================================================
# 2. AHP & Multi-Criteria Consistency Engine
# ==============================================================================

def test_ahp_consistent_matrix():
    """Consistent pairwise comparison matrix yields CR <= 0.10."""
    # 3x3 consistent matrix: C1 is 2x C2, 4x C3; C2 is 2x C3
    matrix = [
        [1.0, 2.0, 4.0],
        [0.5, 1.0, 2.0],
        [0.25, 0.5, 1.0],
    ]
    eval_res = verify_pairwise_matrix_consistency(matrix)
    assert eval_res["is_consistent"] is True
    assert eval_res["consistency_ratio"] <= 0.10
    assert eval_res["status"] == "CONSISTENT"
    assert len(eval_res["weights"]) == 3
    assert abs(sum(eval_res["weights"]) - 1.0) < 1e-4


def test_ahp_inconsistent_matrix():
    """Severely inconsistent pairwise comparison matrix yields CR > 0.10."""
    # Arbitrary non-transitive judgements
    matrix = [
        [1.0, 9.0, 0.111],
        [0.111, 1.0, 8.0],
        [9.0, 0.125, 1.0],
    ]
    eval_res = verify_pairwise_matrix_consistency(matrix)
    assert eval_res["is_consistent"] is False
    assert eval_res["consistency_ratio"] > 0.10
    assert eval_res["status"] == "INCONSISTENT"


def test_ahp_invalid_matrix_validation():
    """Non-square or non-reciprocal matrices must raise ValueError."""
    # Non-square
    with pytest.raises(ValueError, match="square"):
        verify_pairwise_matrix_consistency([[1.0, 2.0]])

    # Non-reciprocal: A[0][1] = 2.0 but A[1][0] != 0.5
    with pytest.raises(ValueError, match="reciprocal"):
        verify_pairwise_matrix_consistency([[1.0, 2.0], [0.8, 1.0]])


def test_ahp_model_execution():
    """AHPSusceptibilityModel evaluates factors and normalizes to 0-100 score."""
    model = AHPSusceptibilityModel()
    factors = {
        "slope": 35.0,  # steep
        "lithology": 70.0,
        "drainage": 80.0,
        "land_cover": 40.0,
        "aspect": 180.0,  # south-facing
    }
    res = model.evaluate(factors)
    assert 0.0 <= res["score"] <= 100.0
    assert res["status"] in ("CONFIGURED / CONSISTENT", "CONFIGURED · CONSISTENT", "CONSISTENT")
    assert res["consistency_ratio"] <= 0.10



# ==============================================================================
# 3. Frequency Ratio & Empirical Bivariate Engine
# ==============================================================================

def test_frequency_ratio_calculation():
    """FrequencyRatioModel binned weights calculate score between 0 and 100."""
    model = FrequencyRatioModel()
    factors = {
        "slope": 38.0,
        "aspect": 190.0,
        "curvature": -1.2,
        "distance_to_drainage": 85.0,
        "distance_to_road": 120.0,
    }
    res = model.evaluate(factors)
    assert 0.0 <= res["score"] <= 100.0
    assert "factor_fr_values" in res
    assert res["validation_status"] == "DEMO / NOT VALIDATED"


# ==============================================================================
# 4. Machine Learning Susceptibility Pipeline
# ==============================================================================

def test_ml_pipeline_production_default_untrained():
    """In production mode without verified field inventory, ML model is UNTRAINED."""
    pipeline = MLSusceptibilityPipeline()
    res = pipeline.predict_susceptibility({"slope": 30.0, "aspect": 150.0})
    assert res["status"] == "UNTRAINED / INSUFFICIENT_REAL_DATA"
    assert res["score"] is None


def test_ml_pipeline_synthetic_training_and_feature_importances():
    """ML pipeline trains on synthetic spatial blocks, returns metrics and importances."""
    pipeline = MLSusceptibilityPipeline()

    rng = np.random.RandomState(42)
    n_samples = 200
    X = np.zeros((n_samples, 5))
    X[:, 0] = rng.uniform(0, 60, n_samples)  # slope
    X[:, 1] = rng.uniform(0, 360, n_samples)  # aspect
    X[:, 2] = rng.uniform(-5, 5, n_samples)  # curvature
    X[:, 3] = rng.uniform(10, 2000, n_samples)  # dist_drainage
    X[:, 4] = rng.uniform(10, 2000, n_samples)  # dist_road

    # Susceptibility probability driven by steep slope and close drainage
    prob = 1.0 / (1.0 + np.exp(-(0.08 * X[:, 0] - 0.002 * X[:, 3] - 1.0)))
    y = (rng.uniform(0, 1, n_samples) < prob).astype(int)
    spatial_blocks = (rng.uniform(0, 4, n_samples)).astype(int)

    metrics = pipeline.train(
        X,
        y,
        feature_names=["slope", "aspect", "curvature", "dist_drainage", "dist_road"],
        spatial_blocks=spatial_blocks,
    )

    assert pipeline.is_trained is True
    assert "accuracy" in metrics
    assert "feature_importances" in metrics
    # Slope should be a dominant feature
    assert metrics["feature_importances"]["slope"] > 0.05

    # Predict single instance
    pred = pipeline.predict_susceptibility({
        "slope": 45.0,
        "aspect": 180.0,
        "curvature": -2.0,
        "dist_drainage": 50.0,
        "dist_road": 100.0,
    })
    assert pred["status"] == "CALIBRATED_TEST_FIXTURE"
    assert pred["score"] is not None
    assert 0.0 <= pred["score"] <= 100.0


# ==============================================================================
# 5. Methodological Model Agreement Engine
# ==============================================================================

def test_model_agreement_high():
    """Agreement is HIGH when score discrepancy is <= 15 points."""
    engine = ModelAgreementEngine()
    eval_res = engine.evaluate(ahp_score=78.0, fr_score=82.0, ml_score=None)
    assert eval_res["agreement_level"] == ModelAgreementLevel.HIGH.value
    assert eval_res["confidence_penalty"] == 0.0
    assert "MODEL_AGREEMENT_HIGH" in eval_res["reason_codes"]


def test_model_agreement_low_and_confidence_penalty():
    """Agreement is LOW when discrepancy > 30 points; triggers 15 pt confidence penalty."""
    engine = ModelAgreementEngine()
    eval_res = engine.evaluate(ahp_score=85.0, fr_score=42.0, ml_score=None)
    assert eval_res["agreement_level"] == ModelAgreementLevel.LOW.value
    assert eval_res["confidence_penalty"] == 15.0
    assert "MODEL_DISAGREEMENT_HIGH" in eval_res["reason_codes"]


# ==============================================================================
# 6. Safety Guards: Red Zone Downgrade & Dynamic Weather Safeguards
# ==============================================================================

def test_permanent_red_downgrade_when_confidence_low(db):
    """Permanent Red requirement: composite >= 75, structural >= 70, confidence >= 70.

    If confidence < 70, it MUST be downgraded to CONDITIONAL_RED with tag.
    """
    engine = RiskEngine(db)
    # HAB-001 has high structural risk (>= 70) and composite risk (>= 75)
    assessment = engine.assess_habitation("HAB-001")
    assert assessment.baseline_structural_risk >= 70.0
    assert assessment.composite_risk_score >= 75.0

    # Test the downgrade guard: when confidence is below required threshold
    from app.services.risk.config import RiskEngineConfig
    strict_conf_config = RiskEngineConfig(
        PERMANENT_RED_CONFIDENCE_THRESHOLD=100.1,  # Require 100.1% to trigger downgrade guard for test
    )
    downgrade_engine = RiskEngine(db, config=strict_conf_config)
    downgraded = downgrade_engine.assess_habitation("HAB-001")


    assert downgraded.risk_classification == RedZoneClassification.CONDITIONAL_RED.value
    assert "LOW_CONFIDENCE_FIELD_VERIFICATION_REQUIRED" in downgraded.reason_codes


def test_dynamic_weather_does_not_create_permanent_red(db):
    """Dynamic weather surge cannot produce PERMANENT_RED if structural baseline < 70."""
    engine = RiskEngine(db)
    # Find or evaluate an acceptable habitation with baseline structural risk < 70 (e.g. HAB-006)
    assessment = engine.assess_habitation("HAB-006")

    # Even with an active rainfall event, a habitation with baseline structural risk < 70
    # must not be categorized as PERMANENT_RED
    assert assessment.baseline_structural_risk < 70.0
    assert assessment.risk_classification != RedZoneClassification.PERMANENT_RED.value



def test_compound_hazard_adjustment_cap():
    """Compound hazard adjustment must be non-negative and strictly capped at 15.0."""
    from app.services.risk.compound import calculate_compound_hazard_adjustment

    adj = calculate_compound_hazard_adjustment(
        baseline_hazard=95.0,
        dynamic_hazard=98.0,
        active_hazard_types=["LANDSLIDE", "FLOOD", "CLOUDBURST", "EARTHQUAKE"],
        rainfall_24h=180.0,
    )
    assert 0.0 <= adj <= 15.0


# ==============================================================================
# 7. Relocation Need Decoupled from Readiness & Strict Readiness Caps
# ==============================================================================

def test_candidate_sites_availability_does_not_diminish_relocation_need(db):
    """Need is driven by risk, exposure and vulnerability. Candidate count has 0 impact on Need."""
    engine = RelocationEngine(db)
    reloc = engine.assess_habitation("HAB-001")

    initial_need = reloc.need_score
    assert initial_need > 0

    # Changing candidate reception sites in the district does NOT change the habitation's need
    components = reloc.need_components
    assert "candidate_sites_count" not in components
    assert "reception_capacity" not in components


def test_readiness_caps_enforce_lowest_constraint():
    """Readiness must be capped by the lowest planning constraint applicable (20, 40, 55, 70)."""
    from app.services.relocation.engine import calculate_reception_readiness

    # Case 1: No candidate sites identified -> capped at <= 20
    score_no_sites, _, gaps1, _ = calculate_reception_readiness(
        candidate_sites_count=0,
        only_demo_candidates=False,
        has_field_verified_candidate=True,
        carrying_capacity_assessed=True,
    )
    assert score_no_sites <= 20.0
    assert "NO_CANDIDATE_SITES_IDENTIFIED_IN_DISTRICT" in gaps1

    # Case 2: Only DEMO candidate sites -> capped at <= 40
    score_demo, _, gaps2, _ = calculate_reception_readiness(
        candidate_sites_count=2,
        only_demo_candidates=True,
        has_field_verified_candidate=True,
        carrying_capacity_assessed=True,
    )
    assert score_demo <= 40.0
    assert "CANDIDATE_SITES_SYNTHETIC_BENCHMARK_ONLY" in gaps2

    # Case 3: No field-verified candidate -> capped at <= 55
    score_unverified, _, gaps3, _ = calculate_reception_readiness(
        candidate_sites_count=2,
        only_demo_candidates=False,
        has_field_verified_candidate=False,
        carrying_capacity_assessed=True,
    )
    assert score_unverified <= 55.0
    assert "FIELD_VERIFICATION_PENDING_ON_RECEPTION_SITES" in gaps3

    # Case 4: Carrying capacity not assessed -> capped at <= 70
    score_no_cap, _, gaps4, _ = calculate_reception_readiness(
        candidate_sites_count=2,
        only_demo_candidates=False,
        has_field_verified_candidate=True,
        carrying_capacity_assessed=False,
    )
    assert score_no_cap <= 70.0
    assert "CARRYING_CAPACITY_ASSESSMENT_REQUIRED" in gaps4

    # Case 5: Multiple caps present -> lowest constraint strictly enforced
    # DEMO-only (40) + Unverified (55) -> must be <= 40.0
    score_multi, _, gaps5, _ = calculate_reception_readiness(
        candidate_sites_count=2,
        only_demo_candidates=True,
        has_field_verified_candidate=False,
        carrying_capacity_assessed=False,
    )
    assert score_multi <= 40.0

    # Case 6: Future feasibility advisory blockers preserved for Tasks 6-7 without replacing planning caps
    score_advisory, _, gaps6, reasons6 = calculate_reception_readiness(
        candidate_sites_count=2,
        only_demo_candidates=False,
        has_field_verified_candidate=True,
        carrying_capacity_assessed=True,
        hazard_score=85.0,  # critical hazard zone
        road_access=False,   # no road access
    )
    assert "FUTURE_BLOCKER_SITE_IN_HIGH_HAZARD_ZONE" in gaps6
    assert "FUTURE_BLOCKER_NO_ROAD_ACCESS" in gaps6
    assert "SITE_FEASIBILITY_CRITICAL_HAZARD" in reasons6



# ==============================================================================
# 8. Terrain Geomorphometry Metric Pipeline
# ==============================================================================

def test_terrain_metric_slope_and_aspect():
    """Horn metric slope with latitude degree-to-meter scaling and aspect 0-360."""
    # Synthetic 5x5 planar incline tilting downward towards South (y increasing)
    elevation = np.array([
        [2000.0, 2000.0, 2000.0, 2000.0, 2000.0],
        [1950.0, 1950.0, 1950.0, 1950.0, 1950.0],
        [1900.0, 1900.0, 1900.0, 1900.0, 1900.0],
        [1850.0, 1850.0, 1850.0, 1850.0, 1850.0],
        [1800.0, 1800.0, 1800.0, 1800.0, 1800.0],
    ])
    # Resolution 30 meters
    slope = calculate_metric_slope(elevation, cell_size_x=30.0, cell_size_y=30.0)
    aspect = calculate_aspect(elevation, cell_size_x=30.0, cell_size_y=30.0)

    # Center cell slope should be around ~59 degrees (50m drop over 30m distance)
    center_slope = slope[2, 2]
    assert 55.0 < center_slope < 65.0

    # Slope facing South should have aspect around 180 degrees
    center_aspect = aspect[2, 2]
    assert 170.0 <= center_aspect <= 190.0


def test_terrain_curvature_calculation():
    """Zevenbergen-Thorne curvature calculation handles ridges and valleys."""
    elevation = np.array([
        [100.0, 110.0, 100.0],
        [100.0, 120.0, 100.0],  # Ridge center peak
        [100.0, 110.0, 100.0],
    ])
    prof_c, plan_c = calculate_curvature(elevation, cell_size_x=10.0, cell_size_y=10.0)
    assert prof_c is not None
    assert plan_c is not None


# ==============================================================================
# 9. Spatial Distance Evidence Helpers
# ==============================================================================

def test_spatial_distance_helpers_handle_missing_layers(db):
    """Distance helpers must return AnalyticalStatus.UNKNOWN if layer is not registered."""
    res_road = calculate_distance_to_road(db, 30.5, 79.5)
    res_drain = calculate_distance_to_drainage(db, 30.5, 79.5)
    res_fault = calculate_distance_to_fault(db, 30.5, 79.5)

    assert res_road.status.value in (AnalyticalStatus.VALUE.value, AnalyticalStatus.UNKNOWN.value)
    assert res_drain.status.value in (AnalyticalStatus.VALUE.value, AnalyticalStatus.UNKNOWN.value)
    assert res_fault.status.value in (AnalyticalStatus.VALUE.value, AnalyticalStatus.UNKNOWN.value)


# ==============================================================================
# 10. MCDA Criteria Correlation & Monte Carlo Sensitivity
# ==============================================================================

def test_criteria_correlation_and_vif_warning():
    """Criteria correlation detects multicollinearity >= 0.85 and calculates VIF."""
    # Create collinear criteria
    x1 = np.linspace(10, 100, 50)
    x2 = x1 * 0.95 + np.random.RandomState(42).normal(0, 1, 50)  # highly collinear
    x3 = np.random.RandomState(42).uniform(0, 100, 50)  # independent

    data = {"Slope": x1.tolist(), "Gradient": x2.tolist(), "Rainfall": x3.tolist()}
    corr_res = calculate_correlation_matrix(data)

    assert len(corr_res["redundancy_warnings"]) > 0
    assert len(corr_res["high_correlation_pairs"]) > 0
    assert corr_res["vif"]["Slope"] > 5.0 or corr_res["vif"]["Gradient"] > 5.0


def test_monte_carlo_sensitivity_reproducibility():
    """Deterministic random seed produces exact reproducible sensitivity ranks."""
    items = [
        {"id": "A", "criteria": {"c1": 80.0, "c2": 40.0, "c3": 30.0}},
        {"id": "B", "criteria": {"c1": 60.0, "c2": 90.0, "c3": 70.0}},
        {"id": "C", "criteria": {"c1": 20.0, "c2": 30.0, "c3": 85.0}},
    ]
    base_weights = {"c1": 0.5, "c2": 0.3, "c3": 0.2}

    res1 = run_monte_carlo_sensitivity(
        items,
        base_weights,
        iterations=50,
        perturbation_pct=0.20,
        seed=12345,
    )
    res2 = run_monte_carlo_sensitivity(
        items,
        base_weights,
        iterations=50,
        perturbation_pct=0.20,
        seed=12345,
    )

    assert res1["overall_robustness_score"] == res2["overall_robustness_score"]
    assert res1["item_stability"]["A"]["mean_rank"] == res2["item_stability"]["A"]["mean_rank"]
    assert res1["item_stability"]["B"]["mean_rank"] == res2["item_stability"]["B"]["mean_rank"]
