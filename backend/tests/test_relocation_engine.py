"""Unit and integration tests for Relocation Need & Readiness Engine (PRAYAAS-RELOCATION-1.0)."""

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.candidate_site import CandidateSite
from app.models.enums import ReadinessLevel, RelocationUrgency
from app.models.habitation import Habitation
from app.models.relocation import RelocationAssessment
from app.models.risk import RiskAssessment
from app.services.relocation.config import DEFAULT_RELOCATION_CONFIG
from app.services.relocation.engine import RelocationEngine


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


def test_candidate_sites_never_reduce_need_score(db):
    """Architectural Rule: Candidate reception site presence must NEVER decrease relocation need."""
    engine = RelocationEngine(db)
    hab = db.query(Habitation).filter(Habitation.id == "HAB-001").first()
    assert hab is not None

    assessment = engine.assess_habitation(hab.id)
    need_score_before = assessment.need_score

    # Check that need score is solely calculated from structural risk, vulnerability, history, trend, isolation, and sustainability deficit
    components = assessment.need_components
    expected_need = (
        (DEFAULT_RELOCATION_CONFIG.NEED_STRUCTURAL_RISK_WEIGHT * components["baseline_structural_risk"])
        + (DEFAULT_RELOCATION_CONFIG.NEED_VULNERABILITY_WEIGHT * components["vulnerability"])
        + (DEFAULT_RELOCATION_CONFIG.NEED_DISASTER_HISTORY_WEIGHT * components["history"])
        + (DEFAULT_RELOCATION_CONFIG.NEED_TREND_WEIGHT * components["trend"])
        + (DEFAULT_RELOCATION_CONFIG.NEED_ISOLATION_WEIGHT * components["isolation_deficit"])
        + (DEFAULT_RELOCATION_CONFIG.NEED_SUSTAINABILITY_DEFICIT_WEIGHT * components["sustainability_deficit"])
    )
    assert abs(need_score_before - round(expected_need, 1)) < 0.2


def test_strict_readiness_caps_applied(db):
    """When candidate sites are in DEMO mode or UNVERIFIED, readiness score MUST be capped."""
    engine = RelocationEngine(db)
    assessment = engine.assess_habitation("HAB-001")

    # In our seed data, candidate sites are currently DEMO mode benchmarks
    # Therefore readiness score MUST be capped at 40.0
    assert assessment.readiness_score <= DEFAULT_RELOCATION_CONFIG.CAP_DEMO_ONLY_SITES
    assert (
        "CANDIDATE_SITES_SYNTHETIC_BENCHMARK_ONLY" in assessment.readiness_gaps
        or "CAP_APPLIED_DEMO_ONLY_SITES" in assessment.reason_codes
    )


def test_relocation_api_endpoints(client):
    # 1. Get habitation relocation assessment
    res = client.get("/api/habitations/HAB-001/relocation")
    assert res.status_code == 200
    data = res.json()
    assert data["habitation_id"] == "HAB-001"
    assert "need_score" in data
    assert "readiness_score" in data
    assert "urgency" in data
    assert "readiness_level" in data
    assert "readiness_gaps" in data

    # 2. Get habitation relocation history
    res_hist = client.get("/api/habitations/HAB-001/relocation/history")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["habitation_id"] == "HAB-001"
    assert len(hist_data["history"]) >= 1

    # 3. Get enriched relocation priorities
    res_prio = client.get("/api/relocation-priorities")
    assert res_prio.status_code == 200
    prio_data = res_prio.json()
    assert prio_data["total"] >= 13
    first_item = prio_data["items"][0]
    assert "needScore" in first_item
    assert "readinessScore" in first_item


def test_red_zone_intelligence_endpoint(client):
    res = client.get("/api/analysis/red-zones")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 4
    for rz in data["red_zones"]:
        assert rz["classification"] in ("PERMANENT_RED", "CONDITIONAL_RED", "DYNAMIC_RED", "WATCH", "ACCEPTABLE")
        assert rz["confidence_score"] > 0
        assert rz["dominant_hazard"] is not None


def test_data_sources_freshness_endpoint(client):
    res = client.get("/api/data-sources/freshness")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 4
    assert "stale_count" in data
