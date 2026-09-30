"""Tests for Task 6 — Automatic GIS-Based Relocation Candidate Discovery.

Verifies:
1. Candidate discovery configuration & AHP consistency (CR <= 0.10)
2. Distance utility curves (monotonic decreasing, optimal range, monotonic increasing)
3. Hard exclusion engine: slope > 25° exclusion, hazard zone buffer, settlement conflict, mandatory UNKNOWN policy
4. Soft suitability engine: available-component MCDA normalization, missing criteria never zero, decoupled confidence
5. Contiguous parcel extraction, metric area calculation, minimum area threshold enforcement
6. Deterministic explanation generation (why selected, limitations, robustness summary)
7. Full candidate discovery workflow execution & PostGIS persistence
8. API endpoints (POST run, GET runs, GET parcels, GET geojson)
9. Relocation readiness integration: MODELED parcels unlock DEMO cap up to unverified cap (<=55), Need score unaffected
"""

from __future__ import annotations

import math
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from app.models.habitation import Habitation
from app.models.hazard_zone import HazardZone
from app.models.candidate_discovery import CandidateDiscoveryRun, CandidateParcel
from app.models.enums import CandidateDiscoveryStatus, DataMode, ParcelStatus, VerificationStatus
from app.services.candidates.config import (
    CandidateDiscoveryConfig,
    DEFAULT_CANDIDATE_CONFIG,
    DistanceUtilityCurve,
    DistanceUtilityCurveType,
)
from app.services.candidates.exclusions import HardExclusionEngine
from app.services.candidates.suitability import SoftSuitabilityEngine
from app.services.candidates.polygons import (
    ContiguousParcelExtractor,
    FeasibleCell,
)
from app.services.candidates.segmentation import SuitabilitySurfaceSegmenter
from app.services.candidates.explanations import CandidateExplanationEngine
from app.services.candidates.engine import CandidateDiscoveryEngine
from app.services.relocation.engine import RelocationEngine


def test_candidate_discovery_config_and_ahp_consistency():
    """Verify that configuration defines valid AHP pairwise matrix with CR <= 0.10."""
    config = CandidateDiscoveryConfig()
    val = config.validate_ahp_consistency()
    assert val["is_consistent"] is True
    assert val["consistency_ratio"] <= 0.10
    assert val["status"] == "CONFIGURED · CONSISTENT"
    assert sum(config.criteria_weights.values()) == pytest.approx(1.0, abs=1e-3)


def test_distance_utility_curves():
    """Verify monotonic decreasing and optimal range piecewise distance utility curves."""
    # 1. Monotonic decreasing (road access: 0.5 km optimal -> 100, 5.0 km max -> 0)
    road_curve = DistanceUtilityCurve(
        curve_type=DistanceUtilityCurveType.MONOTONIC_DECREASING,
        optimal_min_km=0.5,
        max_acceptable_km=5.0,
    )
    assert road_curve.evaluate(0.2) == 100.0
    assert road_curve.evaluate(0.5) == 100.0
    assert road_curve.evaluate(2.75) == pytest.approx(50.0, abs=1.0)
    assert road_curve.evaluate(5.0) == 0.0
    assert road_curve.evaluate(10.0) == 0.0

    # 2. Optimal range (relocation distance: 2-10 km optimal -> 100, <2 km penalized, >25 km penalized)
    dist_curve = DistanceUtilityCurve(
        curve_type=DistanceUtilityCurveType.OPTIMAL_RANGE,
        optimal_min_km=2.0,
        optimal_max_km=10.0,
        max_acceptable_km=25.0,
    )
    assert dist_curve.evaluate(5.0) == 100.0
    assert dist_curve.evaluate(2.0) == 100.0
    assert dist_curve.evaluate(0.5) < 100.0  # too close to disaster origin
    assert dist_curve.evaluate(26.0) <= 20.0  # excessive displacement distance


def test_hard_exclusion_engine_and_unknown_policy(db: Session):
    """Verify safety-first screening and mandatory UNKNOWN policy."""
    engine = HardExclusionEngine(db)


    # 1. Slope > 25° must FAIL
    res_steep = engine.evaluate_cell(
        lat=30.43, lng=79.35, slope_deg=32.0, hazard_zones=[], habitations=[], dist_to_hazard_m=5000.0
    )
    assert res_steep.is_excluded is True
    assert res_steep.primary_failure_reason == "EXCESSIVE_SLOPE"
    assert res_steep.checks["EXCESSIVE_SLOPE"] == "FAIL"

    # 2. Slope <= 25° passes slope check
    res_gentle = engine.evaluate_cell(
        lat=30.43, lng=79.35, slope_deg=12.0, hazard_zones=[], habitations=[], dist_to_hazard_m=5000.0
    )
    assert res_gentle.checks["EXCESSIVE_SLOPE"] == "PASS"

    # 3. Hazard zone buffer: inside buffer (< 150m) must FAIL
    res_hazard = engine.evaluate_cell(
        lat=30.43, lng=79.35, slope_deg=10.0, hazard_zones=[], habitations=[], dist_to_hazard_m=100.0
    )
    assert res_hazard.is_excluded is True
    assert res_hazard.primary_failure_reason == "CRITICAL_LANDSLIDE_RISK"
    assert res_hazard.checks["CRITICAL_LANDSLIDE_RISK"] == "FAIL"

    # 4. Mandatory UNKNOWN policy: unverified flood and protected area layers are marked UNKNOWN, never PASS
    assert res_gentle.checks["PROTECTED_AREA"] == "UNKNOWN"
    assert res_gentle.checks["RESTRICTED_LAND"] == "UNKNOWN"
    assert res_gentle.checks["CRITICAL_FLOOD_RISK"] == "UNKNOWN"
    assert res_gentle.unknown_count >= 3


def test_soft_suitability_mcda_normalization():
    """Verify available-component weighted MCDA normalization and confidence scoring."""
    engine = SoftSuitabilityEngine()

    # Complete criteria
    res_complete = engine.evaluate(
        slope_deg=8.0,
        dist_to_hazard_km=3.0,
        dist_to_road_km=1.0,
        dist_to_health_km=3.0,
        dist_to_school_km=2.0,
        dist_to_water_km=1.0,
        dist_to_origin_km=4.0,
        unknown_exclusion_count=0,
        is_demo_source=False,
    )
    assert 70.0 <= res_complete.composite_score <= 100.0
    assert res_complete.confidence_score >= 80.0
    assert len(res_complete.missing_criteria) == 0

    # Missing criteria (e.g. road and water unknown) must NOT evaluate to 0
    res_missing = engine.evaluate(
        slope_deg=8.0,
        dist_to_hazard_km=3.0,
        dist_to_road_km=None,
        dist_to_health_km=3.0,
        dist_to_school_km=2.0,
        dist_to_water_km=None,
        dist_to_origin_km=4.0,
        unknown_exclusion_count=3,
        is_demo_source=True,
    )
    # Composite score must be normalized over available weights, not collapsed to zero
    assert res_missing.composite_score >= 70.0
    assert "ROAD_ACCESS" in res_missing.missing_criteria
    assert "WATER_ACCESS" in res_missing.missing_criteria
    # Confidence must reflect penalty for missing criteria, unknown exclusions, and DEMO mode
    assert res_missing.confidence_score < res_complete.confidence_score


def test_contiguous_parcel_extractor_and_minimum_area():
    """Verify 8-connectivity clustering, polygon cleaning, and minimum area rejection."""
    extractor = ContiguousParcelExtractor(CandidateDiscoveryConfig(min_parcel_area_hectares=5.0))

    # Create 2 clusters:

    # Cluster 1: 30 adjacent cells (~3.0 hectares) -> Valid (>= 2.0 ha)
    # Cluster 2: 3 adjacent cells (~0.3 hectares) -> Rejected (< 2.0 ha)
    cells: list[FeasibleCell] = []

    # Cluster 1
    for r in range(5, 10):
        for c in range(5, 11):
            cells.append(
                FeasibleCell(
                    row=r,
                    col=c,
                    lat=30.43 + (r * 0.001),
                    lng=79.35 + (c * 0.001),
                    slope_deg=10.0,
                    suitability_score=85.0,
                    confidence_score=75.0,
                    criterion_scores={"SAFETY_MARGIN": 90.0, "ROAD_ACCESS": 80.0},
                    exclusion_summary={"CRITICAL_LANDSLIDE_RISK": "PASS", "EXCESSIVE_SLOPE": "PASS"},
                    dist_to_origin_km=3.0,
                )
            )

    # Cluster 2 (isolated)
    for c in range(20, 23):
        cells.append(
            FeasibleCell(
                row=18,
                col=c,
                lat=30.43 + (18 * 0.001),
                lng=79.35 + (c * 0.001),
                slope_deg=12.0,
                suitability_score=70.0,
                confidence_score=70.0,
                criterion_scores={"SAFETY_MARGIN": 80.0},
                exclusion_summary={"CRITICAL_LANDSLIDE_RISK": "PASS"},
                dist_to_origin_km=8.0,
            )
        )

    valid_parcels, rejected_parcels = extractor.extract_parcels(
        feasible_cells=cells,
        grid_rows=25,
        grid_cols=25,
        res_deg_x=0.001,
        res_deg_y=0.001,
        origin_lat=30.43,
        origin_lng=79.35,
    )

    assert len(valid_parcels) == 1
    assert len(rejected_parcels) >= 1
    assert valid_parcels[0].area_hectares >= 2.0
    assert rejected_parcels[0].is_rejected is True
    assert rejected_parcels[0].rejection_reason == "INSUFFICIENT_CONTIGUOUS_AREA"
    assert "MULTIPOLYGON" in valid_parcels[0].geom_wkt or "POLYGON" in valid_parcels[0].geom_wkt


def test_deterministic_explanation_engine():
    """Verify deterministic explanations for why parcel survived, limitations, and rejections."""
    explanation = CandidateExplanationEngine.generate_parcel_explanation(
        parcel_rank=1,
        suitability_score=84.5,
        confidence_score=68.0,
        robustness_score=82.0,
        rank_stability=88.5,
        robustness_level="HIGH",
        area_ha=4.2,
        dist_from_origin_km=3.5,
        criteria_scores={"ROAD_ACCESS": 85.0, "HEALTHCARE_ACCESS": 70.0},
        exclusion_summary={"CRITICAL_LANDSLIDE_RISK": "PASS", "EXCESSIVE_SLOPE": "PASS", "PROTECTED_AREA": "UNKNOWN"},
        data_mode="MODELED",
    )

    assert len(explanation["why_selected"]) >= 3
    assert any("landslide susceptibility" in s for s in explanation["why_selected"])
    assert any("slope" in s.lower() for s in explanation["why_selected"])
    assert len(explanation["limitations"]) >= 3
    assert any("forest" in s.lower() or "protected" in s.lower() for s in explanation["limitations"])
    assert any("field" in s.lower() for s in explanation["limitations"])
    assert "HIGH" in explanation["robustness_summary"]


def test_candidate_discovery_workflow_execution(db: Session):
    """Verify full candidate discovery engine execution against seeded habitation."""
    hab = db.query(Habitation).first()
    assert hab is not None

    engine = CandidateDiscoveryEngine(db)
    result = engine.discover_candidates_for_habitation(
        habitation_id=hab.id,
        search_radius_km=10.0,
        min_parcel_area_ha=1.5,
        max_slope_deg=25.0,
    )

    assert result["run_id"].startswith("CDR-")
    assert result["cells_evaluated"] > 0
    assert result["candidate_parcels_discovered"] > 0
    assert result["configuration_version"] == "1.0.0"
    assert result["analysis_version"] == "PRAYAAS-CANDIDATE-1.0"
    assert len(result["top_candidates"]) > 0

    top_parcel = result["top_candidates"][0]
    assert top_parcel["rank"] == 1
    assert top_parcel["suitability_score"] > 0.0
    assert top_parcel["area_hectares"] >= 1.5

    # Check persistence in database
    db_parcels = (
        db.query(CandidateParcel)
        .filter(CandidateParcel.discovery_run_id == result["run_id"])
        .order_by(CandidateParcel.rank)
        .all()
    )
    assert len(db_parcels) == result["candidate_parcels_discovered"]
    assert db_parcels[0].data_mode == DataMode.MODELED.value


def test_relocation_readiness_with_modeled_parcels(db: Session):
    """Verify that discovering MODELED candidate parcels does NOT affect Relocation Need,
    and updates Readiness while respecting the unverified field cap (<= 55.0).
    """
    test_hab = Habitation(
        id="HAB-TEST-MODEL-ONLY",
        name="Remote Test Habitation",
        district="RemoteDistrict",
        state="Uttarakhand",
        district_id=None,
        population=250,
        households=45,
        geom=from_shape(Point(79.35, 30.43), srid=4326),
        risk_score=75,
        confidence=70,
        vulnerability_score=50,
        data_mode=DataMode.DEMO.value,
        verification_status=VerificationStatus.PENDING.value,
    )
    db.add(test_hab)
    db.commit()

    try:
        reloc_engine = RelocationEngine(db)
        baseline_assessment = reloc_engine.assess_habitation(test_hab.id)
        baseline_need = baseline_assessment.need_score
        assert baseline_assessment.readiness_score <= 20.0
        assert "NO_CANDIDATE_SITES_IDENTIFIED_IN_DISTRICT" in baseline_assessment.readiness_gaps

        # Run discovery to generate MODELED candidate parcels
        discovery_engine = CandidateDiscoveryEngine(db)
        discovery_res = discovery_engine.discover_candidates_for_habitation(
            habitation_id=test_hab.id,
            search_radius_km=8.0,
            min_parcel_area_ha=1.5,
        )
        assert discovery_res["candidate_parcels_discovered"] > 0

        # Re-evaluate relocation assessment
        updated_assessment = reloc_engine.assess_habitation(test_hab.id)

        # 1. Structural Need score must have ZERO change
        assert updated_assessment.need_score == pytest.approx(baseline_need, abs=1e-4)

        # 2. Modeled parcels unlock the NO_SITES (20) cap, but cannot exceed 55.0 unverified cap
        assert updated_assessment.readiness_score > 20.0
        assert updated_assessment.readiness_score <= 55.0
        assert "FIELD_VERIFICATION_PENDING_ON_RECEPTION_SITES" in updated_assessment.readiness_gaps

    finally:
        db.query(CandidateParcel).filter(CandidateParcel.origin_habitation_id == test_hab.id).delete()
        db.query(CandidateDiscoveryRun).filter(CandidateDiscoveryRun.origin_habitation_id == test_hab.id).delete()
        from app.models.relocation import RelocationAssessment
        db.query(RelocationAssessment).filter(RelocationAssessment.habitation_id == test_hab.id).delete()
        db.delete(test_hab)
        db.commit()


def test_candidate_discovery_api_endpoints(client: TestClient, db: Session):
    """Verify REST and GeoJSON endpoints for candidate discovery."""
    hab = db.query(Habitation).first()

    assert hab is not None

    # 1. POST /api/analysis/candidates/habitations/{id}
    res_post = client.post(
        f"/api/analysis/candidates/habitations/{hab.id}",
        json={"search_radius_km": 10.0, "min_parcel_area_hectares": 1.5},
    )
    assert res_post.status_code == 200
    data = res_post.json()
    run_id = data["run_id"]
    assert data["candidate_parcels_discovered"] > 0

    # 2. GET /api/habitations/{id}/candidate-discovery-runs
    res_runs = client.get(f"/api/habitations/{hab.id}/candidate-discovery-runs")
    assert res_runs.status_code == 200
    runs = res_runs.json()
    assert len(runs) >= 1
    assert any(r["id"] == run_id for r in runs)

    # 3. GET /api/candidate-discovery-runs/{run_id}
    res_run = client.get(f"/api/candidate-discovery-runs/{run_id}")
    assert res_run.status_code == 200
    assert res_run.json()["id"] == run_id

    # 4. GET /api/candidate-parcels with filters
    res_parcels = client.get(f"/api/candidate-parcels?run_id={run_id}&min_suitability=50")
    assert res_parcels.status_code == 200
    parcels_data = res_parcels.json()
    assert parcels_data["total"] > 0
    parcel_id = parcels_data["items"][0]["id"]

    # 5. GET /api/candidate-parcels/{parcel_id}
    res_parcel = client.get(f"/api/candidate-parcels/{parcel_id}")
    assert res_parcel.status_code == 200
    single_parcel = res_parcel.json()
    assert single_parcel["id"] == parcel_id
    assert "why_selected" in single_parcel["explanation"]
    assert "limitations" in single_parcel["explanation"]
    assert single_parcel["data_mode"] == "MODELED"

    # 6. GET /api/candidate-parcels/geojson
    res_geojson = client.get(f"/api/candidate-parcels/geojson?run_id={run_id}")
    assert res_geojson.status_code == 200
    geojson = res_geojson.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0
    feat = geojson["features"][0]
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert "suitabilityScore" in feat["properties"]
    assert feat["properties"]["dataMode"] == "MODELED"


def test_grid_resolution_vs_min_parcel_area_consistency():
    """Verify that at 100m grid resolution (~1 ha/cell), a 2 ha minimum area filter
    is active and meaningful: 1 cell is rejected, while 2 adjacent cells survive.
    Also verify resolution parameters are properly determined and bounded.
    """
    config = CandidateDiscoveryConfig(
        grid_resolution_meters=100.0,
        min_parcel_area_hectares=2.0,
        connectivity=4,
    )
    analysis_res, source_res = config.determine_analysis_resolution(
        effective_source_resolution_m=30.0,
        requested_resolution_m=100.0,
    )
    assert analysis_res == 100.0
    assert source_res == 30.0
    # Analysis resolution must never claim precision finer than coarsest critical source layer (30m)
    assert analysis_res >= source_res

    extractor = ContiguousParcelExtractor(config)

    # 1 cell = ~1.0 ha at 100m resolution -> must be rejected by 2 ha threshold
    single_cell = [
        FeasibleCell(
            row=1,
            col=1,
            lat=30.43,
            lng=79.35,
            slope_deg=10.0,
            suitability_score=85.0,
            confidence_score=80.0,
            criterion_scores={"SAFETY_MARGIN": 90.0},
            exclusion_summary={"CRITICAL_LANDSLIDE_RISK": "PASS"},
            dist_to_origin_km=2.0,
        )
    ]
    res_lat = 100.0 / 111132.0
    res_lng = 100.0 / (111412.0 * math.cos(math.radians(30.43)))

    valid1, rejected1 = extractor.extract_parcels(
        feasible_cells=single_cell,
        grid_rows=5,
        grid_cols=5,
        res_deg_x=res_lng,
        res_deg_y=res_lat,
        origin_lat=30.43,
        origin_lng=79.35,
    )
    assert len(valid1) == 0
    assert len(rejected1) == 1
    assert rejected1[0].rejection_reason == "INSUFFICIENT_CONTIGUOUS_AREA"

    # 2 edge-adjacent cells = ~2.0 ha -> survives min area filter
    two_cells = [
        single_cell[0],
        FeasibleCell(
            row=1,
            col=2,
            lat=30.43,
            lng=79.35 + res_lng,
            slope_deg=10.0,
            suitability_score=85.0,
            confidence_score=80.0,
            criterion_scores={"SAFETY_MARGIN": 90.0},
            exclusion_summary={"CRITICAL_LANDSLIDE_RISK": "PASS"},
            dist_to_origin_km=2.0,
        ),
    ]
    valid2, rejected2 = extractor.extract_parcels(
        feasible_cells=two_cells,
        grid_rows=5,
        grid_cols=5,
        res_deg_x=res_lng,
        res_deg_y=res_lat,
        origin_lat=30.43,
        origin_lng=79.35,
    )
    assert len(valid2) == 1
    assert valid2[0].area_hectares >= 2.0


def test_diagonal_only_cells_do_not_merge():
    """Verify that diagonal-only cell touches do NOT merge into a single parcel under 4-connectivity."""
    config = CandidateDiscoveryConfig(
        grid_resolution_meters=100.0,
        min_parcel_area_hectares=1.5,
        connectivity=4,
    )
    extractor = ContiguousParcelExtractor(config)

    res_lat = 100.0 / 111132.0
    res_lng = 100.0 / (111412.0 * math.cos(math.radians(30.43)))

    # Two diagonal cells (0,0) and (1,1) touching only at corner
    diagonal_cells = [
        FeasibleCell(
            row=0,
            col=0,
            lat=30.43,
            lng=79.35,
            slope_deg=8.0,
            suitability_score=80.0,
            confidence_score=80.0,
            criterion_scores={},
            exclusion_summary={},
            dist_to_origin_km=1.0,
        ),
        FeasibleCell(
            row=1,
            col=1,
            lat=30.43 + res_lat,
            lng=79.35 + res_lng,
            slope_deg=8.0,
            suitability_score=80.0,
            confidence_score=80.0,
            criterion_scores={},
            exclusion_summary={},
            dist_to_origin_km=1.0,
        ),
    ]

    valid, rejected = extractor.extract_parcels(
        feasible_cells=diagonal_cells,
        grid_rows=4,
        grid_cols=4,
        res_deg_x=res_lng,
        res_deg_y=res_lat,
        origin_lat=30.43,
        origin_lng=79.35,
    )
    # Under 4-connectivity, each cell is isolated (1 cell = 1 ha < 1.5 ha) -> 2 separate rejected parcels
    assert len(valid) == 0
    assert len(rejected) == 2
    assert all(p.cell_count == 1 for p in rejected)


def test_geometric_feasibility_sliver_rejection():
    """Verify that thin slivers and highly fragmented polygons are rejected with explicit reason codes."""
    config = CandidateDiscoveryConfig(
        grid_resolution_meters=20.0,
        min_parcel_area_hectares=1.0,
        min_effective_width_meters=30.0,
        max_aspect_ratio=6.0,
        min_compactness_ratio=0.08,
    )
    extractor = ContiguousParcelExtractor(config)

    # Create a 1-cell wide line of 20m cells (width = 20m < min_effective_width of 30m)
    # 30 cells of 20m x 20m = 12,000 sq m = 1.2 ha (satisfies area threshold >= 1.0 ha)
    res_lat = 20.0 / 111132.0
    res_lng = 20.0 / (111412.0 * math.cos(math.radians(30.43)))

    sliver_cells = [
        FeasibleCell(
            row=0,
            col=c,
            lat=30.43,
            lng=79.35 + (c * res_lng),
            slope_deg=8.0,
            suitability_score=85.0,
            confidence_score=80.0,
            criterion_scores={},
            exclusion_summary={},
            dist_to_origin_km=1.0,
        )
        for c in range(30)
    ]

    valid, rejected = extractor.extract_parcels(
        feasible_cells=sliver_cells,
        grid_rows=5,
        grid_cols=35,
        res_deg_x=res_lng,
        res_deg_y=res_lat,
        origin_lat=30.43,
        origin_lng=79.35,
    )
    assert len(valid) == 0
    assert len(rejected) == 1
    # Must be rejected due to insufficient width or extreme fragmentation
    assert rejected[0].rejection_reason in ("INSUFFICIENT_WIDTH", "EXTREME_FRAGMENTATION")
    assert rejected[0].area_hectares >= 1.0


def test_settlement_overlap_vs_proximity(db: Session):
    """Verify that proximity to an existing settlement (< 100m) is NOT an unconditional hard fail,
    and that exclusion occurs strictly for direct built-up overlap (<= 0m) or an explicitly configured buffer.
    """
    # Default config: dense_builtup_overlap_buffer_meters = 0.0 (overlap only)
    config = CandidateDiscoveryConfig(
        dense_builtup_overlap_buffer_meters=0.0,
        configured_settlement_buffer_meters=None,
    )
    engine = HardExclusionEngine(db, config)

    # 1. Nearby cell (50m away from village, but NOT overlapping): PASS
    res_near = engine.evaluate_cell(
        lat=30.43,
        lng=79.35,
        slope_deg=10.0,
        hazard_zones=[],
        habitations=[],
        dist_to_hazard_m=5000.0,
        nearest_settlement_dist_m=50.0,
    )
    assert res_near.checks["DENSE_EXISTING_SETTLEMENT"] == "PASS"
    assert res_near.is_excluded is False

    # 2. Overlapping cell (dist = 0m, directly on built-up footprint): FAIL
    res_overlap = engine.evaluate_cell(
        lat=30.43,
        lng=79.35,
        slope_deg=10.0,
        hazard_zones=[],
        habitations=[],
        dist_to_hazard_m=5000.0,
        nearest_settlement_dist_m=0.0,
    )
    assert res_overlap.checks["DENSE_EXISTING_SETTLEMENT"] == "FAIL"
    assert res_overlap.is_excluded is True
    assert res_overlap.primary_failure_reason == "DENSE_EXISTING_SETTLEMENT"

    # 3. Explicit authority planning buffer configured (e.g. 150m):
    config_buffered = CandidateDiscoveryConfig(configured_settlement_buffer_meters=150.0)
    engine_buffered = HardExclusionEngine(db, config_buffered)
    res_buffered_fail = engine_buffered.evaluate_cell(
        lat=30.43,
        lng=79.35,
        slope_deg=10.0,
        hazard_zones=[],
        habitations=[],
        dist_to_hazard_m=5000.0,
        nearest_settlement_dist_m=50.0,
    )
    assert res_buffered_fail.checks["DENSE_EXISTING_SETTLEMENT"] == "FAIL"


def test_critical_unknown_prevents_shortlist_promotion(db: Session):
    """Verify that a candidate parcel with any critical exclusion layer UNKNOWN
    cannot be promoted to SHORTLISTED status, even with high suitability and confidence.
    """
    hab = db.query(Habitation).first()
    assert hab is not None

    engine = CandidateDiscoveryEngine(db)
    result = engine.discover_candidates_for_habitation(
        habitation_id=hab.id,
        search_radius_km=5.0,
        min_parcel_area_ha=1.5,
    )
    assert result["candidate_parcels_discovered"] > 0

    parcels = (
        db.query(CandidateParcel)
        .filter(CandidateParcel.discovery_run_id == result["run_id"])
        .all()
    )
    for p in parcels:
        # Since critical layers (flood, protected area, restricted land) are UNKNOWN,
        # status must NEVER be SHORTLISTED
        critical_unknowns = [
            k for k in ["CRITICAL_FLOOD_RISK", "PROTECTED_AREA", "RESTRICTED_LAND", "RIVER_BUFFER"]
            if p.exclusion_summary.get(k) == "UNKNOWN"
        ]
        if critical_unknowns:
            assert p.status in (ParcelStatus.REQUIRES_FIELD_REVIEW.value, ParcelStatus.PRELIMINARY.value)
            assert p.status != ParcelStatus.SHORTLISTED.value


def test_large_feasible_region_produces_multiple_candidates():
    """Verify that a large contiguous feasible area decomposes into distinct planning-scale
    candidates rather than collapsing into a single giant multi-hundred-hectare polygon.
    """
    config = CandidateDiscoveryConfig(
        max_planning_scale_parcel_ha=20.0,
        candidate_core_threshold=70.0,
        candidate_growth_threshold=55.0,
        minimum_candidate_suitability=60.0,
    )
    segmenter = SuitabilitySurfaceSegmenter(config)

    # Create a 20x20 grid of 1 ha cells (total 400 ha)
    # With 2 distinct peaks (75 and 80) surrounded by suitable cells (65)
    feasible_cells = []
    for r in range(20):
        for c in range(20):
            d1 = math.hypot(r - 4, c - 4)
            d2 = math.hypot(r - 15, c - 15)
            score = max(80.0 - d1 * 3.0, 75.0 - d2 * 3.0)
            score = max(56.0, score)
            cell = FeasibleCell(
                row=r,
                col=c,
                lat=30.40 + r * 0.001,
                lng=79.30 + c * 0.001,
                slope_deg=10.0,
                suitability_score=score,
                confidence_score=75.0,
                criterion_scores={},
                exclusion_summary={"SLOPE_25": "PASS"},
                dist_to_origin_km=5.0,
            )
            feasible_cells.append(cell)

    regions, eligible, meta = segmenter.segment(
        feasible_cells=feasible_cells,
        grid_rows=20,
        grid_cols=20,
        cell_area_ha=1.0,
    )

    # Must produce multiple distinct planning parcels
    assert len(regions) > 1
    # Each parcel must respect the planning scale cap (20 ha = 20 cells)
    for reg in regions:
        assert len(reg) * 1.0 <= config.max_planning_scale_parcel_ha


def test_cells_below_suitability_threshold_remain_feasible_not_candidates():
    """Verify that cells surviving hard exclusions but below minimum candidate suitability
    remain in the feasible land mask, but are excluded from candidate parcels.
    """
    config = CandidateDiscoveryConfig(
        minimum_candidate_suitability=60.0,
        candidate_core_threshold=70.0,
        candidate_growth_threshold=55.0,
    )
    segmenter = SuitabilitySurfaceSegmenter(config)

    # 10 feasible cells: 5 cells with score 50 (below min suitability 60), 5 with score 75
    cells = []
    for c in range(5):
        cells.append(
            FeasibleCell(
                row=0, col=c, lat=30.4, lng=79.3 + c * 0.001,
                slope_deg=12.0, suitability_score=50.0,
                confidence_score=70.0, criterion_scores={},
                exclusion_summary={}, dist_to_origin_km=5.0,
            )
        )
    for c in range(5, 10):
        cells.append(
            FeasibleCell(
                row=0, col=c, lat=30.4, lng=79.3 + c * 0.001,
                slope_deg=8.0, suitability_score=75.0,
                confidence_score=70.0, criterion_scores={},
                exclusion_summary={}, dist_to_origin_km=5.0,
            )
        )

    regions, eligible, meta = segmenter.segment(
        feasible_cells=cells,
        grid_rows=1,
        grid_cols=10,
        cell_area_ha=1.0,
    )

    # Feasible cells count is 10, but candidate eligible is 5
    assert len(cells) == 10
    assert len(eligible) == 5
    assert all(c.suitability_score >= 60.0 for c in eligible)

    # Candidate regions only contain cells with score >= candidate_growth_threshold (55.0)
    for reg in regions:
        for c in reg:
            assert c.suitability_score >= 55.0
            assert c.col >= 5


def test_two_peaks_separated_by_suitability_valley_are_segmented():
    """Verify that two suitability peaks separated by a suitability valley (< candidate_growth_threshold)
    are segmented into two distinct candidate parcels and do not merge.
    """
    config = CandidateDiscoveryConfig(
        candidate_core_threshold=70.0,
        candidate_growth_threshold=55.0,
        minimum_candidate_suitability=60.0,
    )
    segmenter = SuitabilitySurfaceSegmenter(config)

    # Cells 0..2: Peak 1 (scores 75, 78, 75)
    # Cells 3..4: Valley (scores 45, 48) -> below growth threshold 55.0
    # Cells 5..7: Peak 2 (scores 72, 76, 72)
    scores = [75.0, 78.0, 75.0, 45.0, 48.0, 72.0, 76.0, 72.0]
    cells = [
        FeasibleCell(
            row=0, col=i, lat=30.4, lng=79.3 + i * 0.001,
            slope_deg=10.0, suitability_score=s,
            confidence_score=70.0, criterion_scores={},
            exclusion_summary={}, dist_to_origin_km=5.0,
        )
        for i, s in enumerate(scores)
    ]

    regions, eligible, meta = segmenter.segment(
        feasible_cells=cells,
        grid_rows=1,
        grid_cols=len(scores),
        cell_area_ha=1.0,
    )

    assert len(regions) == 2
    reg1_cols = {c.col for c in regions[0]}
    reg2_cols = {c.col for c in regions[1]}
    assert (reg1_cols == {0, 1, 2} and reg2_cols == {5, 6, 7}) or (reg1_cols == {5, 6, 7} and reg2_cols == {0, 1, 2})


def test_hard_exclusions_never_crossed_during_segmentation():
    """Verify that suitability segmentation never crosses hard-exclusion barriers."""
    config = CandidateDiscoveryConfig(
        candidate_core_threshold=70.0,
        candidate_growth_threshold=55.0,
        minimum_candidate_suitability=60.0,
    )
    segmenter = SuitabilitySurfaceSegmenter(config)

    # Cells (0, 0) and (0, 2) are feasible with score 80.
    # Cell (0, 1) is EXCLUDED by hard screening (e.g. slope > 25°), so not in feasible_cells.
    cells = [
        FeasibleCell(
            row=0, col=0, lat=30.4, lng=79.3,
            slope_deg=10.0, suitability_score=80.0,
            confidence_score=75.0, criterion_scores={},
            exclusion_summary={}, dist_to_origin_km=5.0,
        ),
        FeasibleCell(
            row=0, col=2, lat=30.4, lng=79.3 + 2 * 0.001,
            slope_deg=10.0, suitability_score=80.0,
            confidence_score=75.0, criterion_scores={},
            exclusion_summary={}, dist_to_origin_km=5.0,
        ),
    ]

    regions, eligible, meta = segmenter.segment(
        feasible_cells=cells,
        grid_rows=1,
        grid_cols=3,
        cell_area_ha=1.0,
    )

    # Since cell (0, 1) was hard-excluded, region 1 and region 2 cannot bridge
    assert len(regions) == 2
    r1 = regions[0]
    r2 = regions[1]
    assert len(r1) == 1 and len(r2) == 1
    assert {r1[0].col, r2[0].col} == {0, 2}


def test_suitability_segmentation_is_deterministic():
    """Verify that suitability segmentation is 100% deterministic across multiple runs."""
    config = CandidateDiscoveryConfig()
    segmenter = SuitabilitySurfaceSegmenter(config)

    cells = [
        FeasibleCell(
            row=r, col=c, lat=30.4 + r * 0.001, lng=79.3 + c * 0.001,
            slope_deg=10.0, suitability_score=60.0 + ((r * 7 + c * 13) % 25),
            confidence_score=75.0, criterion_scores={},
            exclusion_summary={}, dist_to_origin_km=5.0,
        )
        for r in range(5) for c in range(5)
    ]

    regions1, eligible1, meta1 = segmenter.segment(cells, 5, 5, 1.0)
    regions2, eligible2, meta2 = segmenter.segment(cells, 5, 5, 1.0)

    assert meta1 == meta2
    assert len(regions1) == len(regions2)
    for r1, r2 in zip(regions1, regions2):
        assert [(c.row, c.col) for c in r1] == [(c.row, c.col) for c in r2]


def test_geometry_quality_tests_apply_after_segmentation():
    """Verify that geometry quality checks (min area, aspect ratio, min width)
    apply to segmented candidate regions.
    """
    config = CandidateDiscoveryConfig(
        min_parcel_area_hectares=5.0,
        max_aspect_ratio=4.0,
        min_compactness=0.08,
    )
    extractor = ContiguousParcelExtractor(config)

    # Case A: Region with only 2 cells (~1.6 ha, fails min area 5 ha)
    small_cells = [
        FeasibleCell(
            row=0, col=0, lat=30.4000, lng=79.3000,
            slope_deg=8.0, suitability_score=75.0,
            confidence_score=75.0, criterion_scores={},
            exclusion_summary={}, dist_to_origin_km=3.0,
        ),
        FeasibleCell(
            row=0, col=1, lat=30.4000, lng=79.3009,
            slope_deg=8.0, suitability_score=75.0,
            confidence_score=75.0, criterion_scores={},
            exclusion_summary={}, dist_to_origin_km=3.0,
        ),
    ]

    accepted, rejected = extractor.extract_parcels(
        feasible_cells=small_cells,
        grid_rows=1,
        grid_cols=2,
        res_deg_x=0.0009,
        res_deg_y=0.0009,
        origin_lat=30.40,
        origin_lng=79.30,
        segmented_regions=[small_cells],
    )
    assert len(accepted) == 0
    assert len(rejected) == 1
    assert rejected[0].rejection_reason == "INSUFFICIENT_CONTIGUOUS_AREA"

    # Case B: Region that passes min area (8 cells = ~6.5 ha >= 5 ha)
    valid_cells = [
        FeasibleCell(
            row=r, col=c, lat=30.4000 + r * 0.0009, lng=79.3000 + c * 0.0009,
            slope_deg=8.0, suitability_score=75.0,
            confidence_score=75.0, criterion_scores={},
            exclusion_summary={}, dist_to_origin_km=3.0,
        )
        for r in range(2) for c in range(4)
    ]
    accepted_valid, _ = extractor.extract_parcels(
        feasible_cells=valid_cells,
        grid_rows=2,
        grid_cols=4,
        res_deg_x=0.0009,
        res_deg_y=0.0009,
        origin_lat=30.40,
        origin_lng=79.30,
        segmented_regions=[valid_cells],
    )
    assert len(accepted_valid) == 1
    assert accepted_valid[0].area_hectares >= 5.0


def test_confidence_decreases_with_critical_unknown_evidence():
    """Verify that missing critical exclusion evidence layers heavily penalize confidence."""
    engine = SoftSuitabilityEngine()

    # Case 1: 0 critical unknowns, fine resolution
    res_clean = engine.evaluate(
        slope_deg=8.0,
        dist_to_hazard_km=3.0,
        dist_to_road_km=0.5,
        dist_to_health_km=2.0,
        dist_to_school_km=1.5,
        dist_to_water_km=0.8,
        dist_to_origin_km=4.0,
        critical_unknown_count=0,
        resolution_meters=30.0,
    )

    # Case 2: 2 critical unknowns (e.g. flood and protected area unknown)
    res_penalized = engine.evaluate(
        slope_deg=8.0,
        dist_to_hazard_km=3.0,
        dist_to_road_km=0.5,
        dist_to_health_km=2.0,
        dist_to_school_km=1.5,
        dist_to_water_km=0.8,
        dist_to_origin_km=4.0,
        critical_unknown_count=2,
        resolution_meters=30.0,
    )

    # Confidence must decrease significantly (at least 15 points: 2 * 7.5)
    assert res_clean.confidence_score > res_penalized.confidence_score
    assert (res_clean.confidence_score - res_penalized.confidence_score) >= 15.0

    # Composite (MCDA) score must remain identical (suitability and confidence decoupled)
    assert res_clean.composite_score == res_penalized.composite_score


def test_suitability_confidence_robustness_independence():
    """Verify that suitability, confidence, and robustness are mathematically decoupled."""
    from app.services.mcda.sensitivity import MCDASensitivityEngine

    engine = SoftSuitabilityEngine()

    # High suitability (> 80), but low confidence due to multiple critical UNKNOWNs
    eval_res = engine.evaluate(
        slope_deg=6.0,
        dist_to_hazard_km=4.0,
        dist_to_road_km=0.4,
        dist_to_health_km=1.5,
        dist_to_school_km=1.0,
        dist_to_water_km=0.5,
        dist_to_origin_km=3.5,
        critical_unknown_count=4,
        resolution_meters=250.0,
    )

    assert eval_res.composite_score >= 80.0
    assert eval_res.confidence_score < 60.0

    # Sensitivity / Robustness engine evaluates independently
    analyzer = MCDASensitivityEngine(random_seed=42)
    candidate_scores = {
        "P1": eval_res.criterion_scores,
        "P2": {k: v * 0.85 for k, v in eval_res.criterion_scores.items()},
    }
    base_weights = {k: 1.0 / len(eval_res.criterion_scores) for k in eval_res.criterion_scores}
    rob_res = analyzer.evaluate_robustness(candidate_scores, base_weights)

    assert rob_res["robustness_score"] > 0
    assert rob_res["rank_stability"] >= 90.0


def test_topology_driven_segmentation_three_peaks_and_natural_preservation():
    """Verify that a synthetic landscape with 3 distinct peaks and valleys creates
    topology-driven subregions following analytical structure rather than cookie-cutter truncation,
    and that a separate natural candidate below planning scale is preserved unchanged.
    """
    config = CandidateDiscoveryConfig(
        max_planning_scale_parcel_ha=250.0,
        candidate_core_threshold=70.0,
        candidate_growth_threshold=55.0,
        minimum_candidate_suitability=60.0,
    )
    segmenter = SuitabilitySurfaceSegmenter(config)

    # 1. Connected large landscape with 3 peaks:
    # Peak A: (6, 6) with score 92.0
    # Peak B: (6, 22) with score 88.0
    # Peak C: (22, 14) with score 85.0
    # Saddles/valleys between them with scores ~65-70
    feasible_cells = []
    grid_rows, grid_cols = 30, 30

    for r in range(grid_rows):
        for c in range(grid_cols):
            # Reserve rows 26-29 cols 0-7 for isolated pocket area and barrier
            if r >= 25 and c <= 7:
                continue
            # Buffer row 25 as hard exclusion barrier across the rest
            if r == 25:
                continue

            d1 = math.hypot(r - 6, c - 6)
            d2 = math.hypot(r - 6, c - 22)
            d3 = math.hypot(r - 22, c - 14)
            score = max(92.0 - d1 * 1.8, 88.0 - d2 * 1.8, 85.0 - d3 * 1.8)
            score = max(56.0, score)

            feasible_cells.append(
                FeasibleCell(
                    row=r, col=c, lat=30.40 + r * 0.001, lng=79.30 + c * 0.001,
                    slope_deg=10.0, suitability_score=score,
                    confidence_score=75.0, criterion_scores={},
                    exclusion_summary={}, dist_to_origin_km=5.0,
                )
            )

    # 2. Add an isolated natural small region below planning scale (12 cells = 12 ha)
    isolated_coords = [(27, 1), (27, 2), (27, 3), (28, 1), (28, 2), (28, 3),
                       (28, 4), (29, 1), (29, 2), (29, 3), (29, 4), (29, 5)]
    for r, c in isolated_coords:
        feasible_cells.append(
            FeasibleCell(
                row=r, col=c, lat=30.40 + r * 0.001, lng=79.30 + c * 0.001,
                slope_deg=8.0, suitability_score=78.0,
                confidence_score=80.0, criterion_scores={},
                exclusion_summary={}, dist_to_origin_km=7.0,
            )
        )

    # Run segmentation twice to verify determinism
    regions1, eligible1, meta1 = segmenter.segment(feasible_cells, grid_rows, grid_cols, 1.0)
    regions2, eligible2, meta2 = segmenter.segment(feasible_cells, grid_rows, grid_cols, 1.0)

    # Determinism check
    assert meta1 == meta2
    assert len(regions1) == len(regions2)

    # Verify peak separation: Peak A (6, 6), Peak B (6, 22), Peak C (22, 14)
    # must be allocated to distinct candidate regions
    def find_region_for_coord(regs, target_r, target_c):
        for idx, reg in enumerate(regs):
            if any(cell.row == target_r and cell.col == target_c for cell in reg):
                return idx
        return None

    reg_a = find_region_for_coord(regions1, 6, 6)
    reg_b = find_region_for_coord(regions1, 6, 22)
    reg_c = find_region_for_coord(regions1, 22, 14)

    assert reg_a is not None and reg_b is not None and reg_c is not None
    assert len({reg_a, reg_b, reg_c}) == 3, "Peaks A, B, C must belong to distinct candidate regions"

    # Verify natural areas: areas are NOT cookie-cutter 249.4 ha
    region_areas = [len(r) * 1.0 for r in regions1]
    # Distinct varied areas determined by suitability valleys
    assert len(set(region_areas)) >= 3

    # Verify isolated small natural pocket is preserved exactly (12 cells)
    small_pocket = None
    for reg in regions1:
        if any((c.row, c.col) in isolated_coords for c in reg):
            small_pocket = reg
            break

    assert small_pocket is not None
    assert len(small_pocket) == len(isolated_coords)
    assert set((c.row, c.col) for c in small_pocket) == set(isolated_coords)

    # Verify hard exclusion (row 25) was never crossed
    for reg in regions1:
        assert not any(c.row == 25 for c in reg)




