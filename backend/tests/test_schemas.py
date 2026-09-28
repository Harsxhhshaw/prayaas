"""Unit tests for Pydantic v2 schemas and domain enums."""

from app.models.enums import (
    CandidateStatus,
    DataMode,
    HazardType,
    InfrastructureType,
    RelocationUrgency,
    RiskClassification,
    VerificationStatus,
)
from app.schemas.administrative import DistrictResponse, StateResponse
from app.schemas.candidate_site import CandidateSiteResponse
from app.schemas.common import GeoPointResponse, HazardScoreResponse, MetricsSummaryResponse
from app.schemas.data_source import DataSourceResponse
from app.schemas.disaster_event import DisasterEventResponse
from app.schemas.habitation import HabitationResponse
from app.schemas.infrastructure import InfrastructurePointResponse
from app.schemas.red_zone import RedZoneResponse


def test_domain_enums():
    """Requirement 8: Domain enums are implemented consistently."""
    assert DataMode.DEMO.value == "DEMO"
    assert DataMode.REALTIME.value == "REALTIME"

    assert RiskClassification.CRITICAL.value == "CRITICAL"
    assert RiskClassification.HIGH.value == "HIGH"
    assert RiskClassification.SAFE.value == "SAFE"

    assert RelocationUrgency.IMMEDIATE.value == "IMMEDIATE"
    assert RelocationUrgency.SHORT_TERM.value == "SHORT_TERM"

    assert CandidateStatus.SUITABLE.value == "SUITABLE"
    assert CandidateStatus.PROVISIONAL.value == "PROVISIONAL"

    assert VerificationStatus.VERIFIED.value == "VERIFIED"
    assert VerificationStatus.PENDING.value == "PENDING"


def test_habitation_schema_validation():
    hab_data = {
        "id": "HAB-001",
        "name": "Khar Village",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "position": {"lat": 30.4983, "lng": 79.5603},
        "riskScore": 91,
        "riskCategory": "CRITICAL",
        "urgency": "IMMEDIATE",
        "population": 3841,
        "households": 712,
        "confidence": 86,
        "hazardScores": [{"type": "LANDSLIDE", "score": 94, "label": "Landslide"}],
        "vulnerabilityScore": 76,
        "riskHistory": [{"year": 2026, "score": 91}],
        "elevation": 1840.0,
        "nearestRoad": 2.3,
        "nearestHospital": 14.5,
        "nearestSchool": 1.8,
        "lastAssessed": "2026-09-15",
        "verificationStatus": "VERIFIED",
    }
    obj = HabitationResponse(**hab_data)
    assert obj.id == "HAB-001"
    assert obj.position.lat == 30.4983
    assert obj.hazardScores[0].type == "LANDSLIDE"


def test_hazard_zone_schema():
    rz_data = {
        "id": "RZ-001",
        "name": "Khar-Raini Landslide Corridor",
        "bounds": [
            {"lat": 30.51, "lng": 79.54},
            {"lat": 30.51, "lng": 79.60},
            {"lat": 30.46, "lng": 79.60},
            {"lat": 30.46, "lng": 79.54},
        ],
        "hazardTypes": ["LANDSLIDE", "FLOOD"],
        "compositRiskScore": 92,
        "habitationCount": 3,
        "populationAffected": 5097,
        "areaKmSq": 28.4,
        "declaredDate": "2024-07-15",
        "lastUpdated": "2026-09-15",
    }
    obj = RedZoneResponse(**rz_data)
    assert obj.id == "RZ-001"
    assert len(obj.bounds) == 4
    assert obj.compositRiskScore == 92


def test_metrics_summary_schema():
    metrics = {
        "total_habitations": 13,
        "critical_habitations": 4,
        "high_habitations": 5,
        "total_population_at_risk": 20120,
        "active_red_zones": 4,
        "candidate_sites": 8,
        "pending_relocations": 6,
        "field_verifications_pending": 3,
    }
    obj = MetricsSummaryResponse(**metrics)
    assert obj.total_habitations == 13
    assert obj.active_red_zones == 4
