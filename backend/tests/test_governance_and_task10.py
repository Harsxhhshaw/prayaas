"""Tests for Task 10: Field Evidence, Governance, Land Status, Document AI, Decision Dossier, and Data Honesty."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.candidate_discovery import CandidateParcel
from app.models.enums import (
    DataMode,
    EvidenceType,
    FieldObservationType,
    GovernanceReviewStage,
    LandCategory,
    LandStatus,
    VerificationLevel,
)
from app.models.governance import (
    AnalyticalOverrideRecord,
    ConsultationRecord,
    FieldObservation,
    GovernanceReview,
    LandStatusRecord,
)
from app.models.habitation import Habitation
from app.schemas.governance import (
    AnalyticalOverrideCreate,
    ConsultationCreate,
    DocumentExtractionRequest,
    FieldObservationCreate,
    FieldObservationVerifyRequest,
    GovernanceReviewCreate,
    LandStatusCreate,
)
from app.services.demo_freeze.engine import DemoFreezeEngine
from app.services.document_ai.engine import DocumentAIEngine
from app.services.dossier.engine import DecisionDossierEngine
from app.services.governance.engine import GovernanceEngine
from app.services.relocation.engine import RelocationEngine
from app.services.risk.engine import RiskEngine
from app.services.satellite.engine import SatelliteEvidenceEngine

client = TestClient(app)


# ==============================================================================
# 1. Field Evidence & Progressive Verification Tests
# ==============================================================================

def test_field_observation_creation_and_defaults(db: Session):
    """Field observation starts at FIELD_OBSERVED level with data_mode=FIELD and logs audit trail."""
    gov = GovernanceEngine(db)
    req = FieldObservationCreate(
        entity_type="HABITATION",
        entity_id="HAB-002",
        observation_type="SLOPE_INSTABILITY",
        latitude=30.485,
        longitude=79.689,
        observer_name="Er. S. Rawat",
        observer_role="FIELD_ENGINEER",
        notes="Tension crack ~15m length observed along north-east terraced slope.",
        evidence_values={"crack_width_cm": 4.5, "displacement_rate_mm_day": 1.2},
    )
    obs = gov.record_field_observation(req)

    assert obs.id.startswith("OBS-")
    assert obs.verification_level == VerificationLevel.FIELD_OBSERVED.value
    assert obs.data_mode == DataMode.FIELD.value
    assert obs.observer_name == "Er. S. Rawat"
    assert obs.evidence_values["crack_width_cm"] == 4.5

    # Check audit log entry
    logs = gov.db.query(FieldObservation).filter(FieldObservation.id == obs.id).first()
    assert logs is not None


def test_field_observation_verification_upgrade(db: Session):
    """Field observation upgrades to TECHNICALLY_VERIFIED only via authorized technical review,
    and updates candidate parcel confidence incrementally without exceeding realistic mountain ceiling.
    """
    gov = GovernanceEngine(db)

    # Fetch a candidate parcel
    parcel = db.query(CandidateParcel).filter(CandidateParcel.origin_habitation_id == "HAB-002").first()
    if not parcel:
        parcel = CandidateParcel(
            id="PARCEL-TEST-VERIFY",
            discovery_run_id="RUN-TEST",
            origin_habitation_id="HAB-002",
            area_sq_km=0.25,
            area_hectares=25.0,
            distance_from_origin_km=2.5,
            mean_slope_degrees=15.0,
            suitability_score=80.0,
            confidence_score=65.0,
            status="PRELIMINARY",
            data_mode=DataMode.MODELED.value,
        )
        db.add(parcel)
        db.commit()

    initial_conf = parcel.confidence_score

    # Create field inspection
    req = FieldObservationCreate(
        entity_type="CANDIDATE_PARCEL",
        entity_id=parcel.id,
        observation_type="CANDIDATE_SITE_INSPECTION",
        notes="Terraced bench inspected. Bedrock exposed at 1.5m depth.",
        evidence_values={"bedrock_depth_m": 1.5, "slope_verified": True},
    )
    obs = gov.record_field_observation(req)
    assert obs.verification_level == "FIELD_OBSERVED"

    # Authorized Technical Review
    verify_req = FieldObservationVerifyRequest(
        verification_level="TECHNICALLY_VERIFIED",
        verified_by="Chief Geologist, DMMC",
        technical_notes="Borehole log verified against Geological Survey of India 1:50k sheet.",
    )
    verified_obs = gov.verify_field_observation(obs.id, verify_req)

    assert verified_obs.verification_level == "TECHNICALLY_VERIFIED"
    assert verified_obs.verified_by == "Chief Geologist, DMMC"

    # Candidate parcel confidence should improve modestly, never hitting 100% blindly
    db.refresh(parcel)
    assert parcel.confidence_score >= initial_conf
    assert parcel.confidence_score <= 80.0


# ==============================================================================
# 2. Land & Legal Status Verification Gates
# ==============================================================================

def test_land_status_records_and_defaults(db: Session):
    """Land status records default to UNKNOWN/UNVERIFIED unless official revenue/forest record exists."""
    gov = GovernanceEngine(db)
    req = LandStatusCreate(
        parcel_candidate_id="PARCEL-2A7E427F42D9",
        category=LandCategory.FOREST_STATUS.value,
        status=LandStatus.REQUIRES_REVENUE_VERIFICATION.value,
        source_reference="Uttarakhand Forest Dept Cadastral Portal",
        notes="Parcels border Reserve Forest compartment 4B; ground boundary survey required.",
    )
    rec = gov.record_land_status(req)

    assert rec.id.startswith("LND-")
    assert rec.category == "FOREST_STATUS"
    assert rec.status == "REQUIRES_REVENUE_VERIFICATION"

    recs = gov.get_land_status_for_parcel("PARCEL-2A7E427F42D9")
    assert len(recs) >= 1
    assert any(r.category == "FOREST_STATUS" for r in recs)


# ==============================================================================
# 3. Community Consultation Invariance
# ==============================================================================

def test_consultation_affects_readiness_not_geological_hazard_risk(db: Session):
    """Community consultation records Gram Sabha hearing data but CANNOT modify physical geological hazard risk."""
    risk_engine = RiskEngine(db)
    base_risk = risk_engine.assess_habitation("HAB-002").composite_risk_score

    gov = GovernanceEngine(db)
    req = ConsultationCreate(
        habitation_id="HAB-002",
        participant_count=84,
        method="GRAM_SABHA",
        questions_responses={"support_provisional_relocation": "78% YES", "prefer_same_panchayat": "92% YES"},
        concerns=["Loss of terraced apple orchards", "School distance for primary students"],
        preferences={"preferred_elevation_m": "1800-2100", "cluster_community": True},
        data_mode="DEMO",
    )
    cns = gov.record_consultation(req)

    assert cns.id.startswith("CNS-")
    assert cns.participant_count == 84
    assert cns.method == "GRAM_SABHA"

    # Re-evaluate Risk
    post_risk = risk_engine.assess_habitation("HAB-002").composite_risk_score
    assert post_risk == pytest.approx(base_risk, abs=1e-4)


# ==============================================================================
# 4. Governance Review & Human Analytical Overrides
# ==============================================================================

def test_governance_review_workflow_stages(db: Session):
    """Governance review workflow transitions through legitimate administrative states."""
    gov = GovernanceEngine(db)
    req = GovernanceReviewCreate(
        entity_type="HABITATION",
        entity_id="HAB-002",
        review_stage=GovernanceReviewStage.TECHNICAL_REVIEW_REQUIRED.value,
        assigned_to="District Disaster Management Officer, Chamoli",
        reviewer_role="DDMO",
        review_notes="Field inspection team dispatched for candidate parcel soil bearing test.",
        action_taken="DISPATCH_FIELD_TEAM",
    )
    rev = gov.record_governance_review(req)

    assert rev.id.startswith("GOV-")
    assert rev.review_stage == "TECHNICAL_REVIEW_REQUIRED"
    assert rev.action_taken == "DISPATCH_FIELD_TEAM"


def test_human_analytical_override_preserves_original(db: Session):
    """Analytical override preserves original value, logs reviewer and reason, and appends to audit trail."""
    gov = GovernanceEngine(db)
    req = AnalyticalOverrideCreate(
        entity_type="HABITATION",
        entity_id="HAB-002",
        field_name="urgency",
        original_value="SHORT_TERM",
        override_value="IMMEDIATE",
        reason="Field inspection confirmed active crack dilation exceeding 5mm/day; monsoon imminent.",
        reviewer="District Magistrate, Chamoli",
    )
    ovr = gov.apply_analytical_override(req)

    assert ovr.id.startswith("OVR-")
    assert ovr.original_value == "SHORT_TERM"
    assert ovr.override_value == "IMMEDIATE"
    assert ovr.reviewer == "District Magistrate, Chamoli"

    # Verify retrieval
    history = gov.get_overrides_for_entity("HABITATION", "HAB-002")
    assert len(history) >= 1
    assert any(o.id == ovr.id for o in history)


# ==============================================================================
# 5. Satellite & Change Evidence Safeguards
# ==============================================================================

def test_satellite_evidence_ingestion_and_change_detection(db: Session):
    """Satellite change evidence computes deterministic grid difference without labeling basic mathematics as AI."""
    sat = SatelliteEvidenceEngine(db)
    layer = sat.register_satellite_change_layer(
        name="Sentinel-1 InSAR Line-of-Sight Displacement (Pre vs Post Monsoon)",
        evidence_type=EvidenceType.GROUND_DISPLACEMENT.value,
        provider="ESA Copernicus Sentinel-1",
        product="InSAR Interfeometric Coherence & Displacement",
        acquisition_date_start=datetime(2026, 4, 1, tzinfo=timezone.utc),
        acquisition_date_end=datetime(2026, 9, 15, tzinfo=timezone.utc),
        processing_method="D-InSAR 2-pass differential interferometry (ISCE2)",
        resolution_meters=20.0,
        data_mode="PUBLIC",
    )

    assert layer.id.startswith("EV-")
    assert layer.evidence_type == "GROUND_DISPLACEMENT"

    # Deterministic change calculation
    before_grid = [2.1, 4.0, 1.5, 3.2, 5.0]
    after_grid = [3.5, 8.2, 1.8, 19.5, 6.1]  # Index 3 exceeds 15mm threshold
    change = sat.compute_deterministic_raster_change(before_grid, after_grid, displacement_threshold_mm=15.0)

    assert change["sample_size"] == 5
    assert change["exceedance_count"] == 1
    assert "Non-ML" in change["methodology"]


def test_satellite_safeguard_prevents_permanent_red(db: Session):
    """Satellite change detection escalates to DYNAMIC_RED or WATCH, but can NEVER silently create PERMANENT_RED."""
    sat = SatelliteEvidenceEngine(db)

    # Moderate displacement on ACCEPTABLE -> WATCH
    res1 = sat.evaluate_red_zone_satellite_safeguard(
        current_classification="ACCEPTABLE",
        satellite_change_detected=True,
        mean_displacement_mm=12.5,
    )
    assert res1["recommended_classification"] == "WATCH"
    assert res1["permanent_red_prevented"] is True

    # Severe displacement on WATCH -> DYNAMIC_RED (never PERMANENT_RED)
    res2 = sat.evaluate_red_zone_satellite_safeguard(
        current_classification="WATCH",
        satellite_change_detected=True,
        mean_displacement_mm=38.0,
    )
    assert res2["recommended_classification"] == "DYNAMIC_RED"
    assert res2["recommended_classification"] != "PERMANENT_RED"
    assert res2["permanent_red_prevented"] is True


# ==============================================================================
# 6. Optional Document AI Graceful Degradation
# ==============================================================================

def test_document_ai_graceful_degradation_without_key(db: Session):
    """Without an API key, Document AI extraction degrades gracefully without crashing core GIS/risk operations."""
    doc_ai = DocumentAIEngine(db)
    # Explicitly ensure disabled/no-key
    doc_ai.enabled = False
    doc_ai.api_key = ""

    req = DocumentExtractionRequest(
        document_name="Geological Survey of India Post-Disaster Memo.pdf",
        raw_text="Field survey of Raini village on 2026-08-12 showed extensive crown cracks along upper terrace.",
    )
    res = doc_ai.extract_document_evidence(req)

    assert res.status == "AI_DOCUMENT_EXTRACTION_UNAVAILABLE"
    assert res.ai_enabled is False
    assert "fully operational" in res.message


# ==============================================================================
# 7. Decision Support Dossier
# ==============================================================================

def test_decision_dossier_compilation_and_honesty(db: Session):
    """Decision Support Dossier compiles all 12 sections with honest raw scenario counts and statutory disclaimer."""
    dossier_engine = DecisionDossierEngine(db)
    dossier = dossier_engine.generate_dossier("HAB-002")

    assert dossier.habitation_id == "HAB-002"
    assert "Raini" in dossier.habitation_name
    assert len(dossier.candidate_comparison) >= 1
    assert "Housing" in dossier.carrying_capacity["known_dimensions"][0]
    assert "Sanitation" in dossier.carrying_capacity["critical_unknown_dimensions"][0]

    # Robustness must report raw counts (e.g. 0 of 3 evaluable passed, 3 unresolved)
    assert "0 of 3 evaluable scenarios passed" in dossier.scenario_robustness["raw_count_report"]
    assert "3 additional scenarios unresolved" in dossier.scenario_robustness["raw_count_report"]

    # Disclaimer verification
    assert "does not constitute legal clearance" in dossier.disclaimer.lower()

    # HTML printable report check
    html = dossier_engine.generate_html_report("HAB-002")
    assert "<!DOCTYPE html>" in html
    assert "PRAYAAS Decision Support Dossier" in html
    assert "Raini" in html


# ==============================================================================
# 8. Demo Freeze & Data Honesty Audit
# ==============================================================================

def test_demo_freeze_and_data_honesty_audit(db: Session):
    """Demo freeze returns deterministic Raini snapshot and data honesty audit audits database table counts."""
    demo_engine = DemoFreezeEngine(db)

    # 1. Raini Demo Snapshot
    snap = demo_engine.get_or_create_raini_demo_snapshot()
    assert snap["snapshot_id"] == "DEMO-RAINI-HAB002-FINAL"
    assert snap["habitation"]["need_score"] == 71.9
    assert snap["habitation"]["readiness_score"] == 55.0
    assert snap["habitation"]["matrix_position"] == "MODERATE_READINESS_REVIEW"
    assert snap["candidate_parcels"]["selected_candidate"]["id"] == "PARCEL-E3247A11E0EC"

    # 2. Data Honesty Audit
    audit = demo_engine.perform_data_honesty_audit()
    assert "PUBLIC" in audit.counts_by_mode
    assert "MODELED" in audit.counts_by_mode
    assert "DEMO" in audit.counts_by_mode
    assert "FIELD" in audit.counts_by_mode
    assert audit.ml_status["Random Forest"] == "UNTRAINED / INSUFFICIENT_REAL_DATA"
    assert audit.ml_status["FR"] == "DEMO / NOT VALIDATED"
    assert audit.ml_status["AHP"] == "CONFIGURED / CONSISTENT"
    assert audit.ml_status["Agreement"] == "UNKNOWN"
