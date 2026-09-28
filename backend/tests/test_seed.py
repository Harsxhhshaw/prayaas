"""Unit tests for deterministic DEMO seed data."""

from app.seeds.seed_chamoli import (
    CANDIDATE_SITES_DATA,
    DATA_SOURCES_DATA,
    DISASTER_EVENTS_DATA,
    HABITATIONS_DATA,
    HAZARD_ZONES_DATA,
    INFRASTRUCTURE_DATA,
    STATES_AND_DISTRICTS,
)


def test_seed_habitations_count_and_content():
    """Requirement 16: about 10-15 habitations for Chamoli."""
    assert 10 <= len(HABITATIONS_DATA) <= 15
    for h in HABITATIONS_DATA:
        assert h["id"].startswith("HAB-")
        assert h["district"] in ["Chamoli", "Rudraprayag"]
        assert 30.0 < h["lat"] < 31.0
        assert 78.5 < h["lng"] < 80.5
        assert 0 <= h["risk_score"] <= 100
        assert len(h["hazard_scores"]) >= 1


def test_seed_hazard_zones():
    """Requirement 16: Hazard zones exist with valid polygons."""
    assert len(HAZARD_ZONES_DATA) >= 4
    for rz in HAZARD_ZONES_DATA:
        assert rz["id"].startswith("RZ-")
        assert len(rz["polygon_latlng"]) >= 4
        assert rz["composite_risk_score"] > 0
        assert rz["area_km_sq"] > 0


def test_seed_candidate_sites():
    """Requirement 16: 6-10 candidate sites."""
    assert 6 <= len(CANDIDATE_SITES_DATA) <= 10
    for cs in CANDIDATE_SITES_DATA:
        assert cs["id"].startswith("RS-")
        assert cs["carrying_capacity"] > 0
        assert cs["suitability_score"] > 0
        assert len(cs["bounds_latlng"]) >= 4


def test_seed_infrastructure():
    """Requirement 16: Infrastructure assets exist."""
    assert len(INFRASTRUCTURE_DATA) >= 10
    types = {inf["type"] for inf in INFRASTRUCTURE_DATA}
    assert "HOSPITAL" in types
    assert "SCHOOL" in types


def test_seed_disaster_history():
    """Requirement 16: Disaster history records exist."""
    assert len(DISASTER_EVENTS_DATA) >= 2
    for de in DISASTER_EVENTS_DATA:
        assert de["id"].startswith("EVT-")
        assert de["event_date"] is not None


def test_seed_data_sources():
    """Requirement 16: Data source records exist."""
    assert len(DATA_SOURCES_DATA) >= 4
    for ds in DATA_SOURCES_DATA:
        assert ds["id"].startswith("DS-")
        assert ds["data_mode"] == "DEMO"
        assert "DEMO" in ds["status"]
