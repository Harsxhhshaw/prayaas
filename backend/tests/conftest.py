"""Test configuration and fixtures for PRAYAAS API tests."""

from __future__ import annotations

from typing import Generator
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Point, Polygon
from geoalchemy2.shape import from_shape

from app.api.deps import get_db
from app.main import app
from app.models import (
    CandidateSite,
    DataSource,
    DisasterEvent,
    District,
    Habitation,
    HazardZone,
    InfrastructureAsset,
    OperationalAlert,
    RelocationPriority,
    State,
)
from app.seeds.seed_chamoli import (
    CANDIDATE_SITES_DATA,
    DATA_SOURCES_DATA,
    DISASTER_EVENTS_DATA,
    HABITATIONS_DATA,
    HAZARD_ZONES_DATA,
    INFRASTRUCTURE_DATA,
    STATES_AND_DISTRICTS,
)


@pytest.fixture(scope="session")
def seeded_mock_objects():
    """Build in-memory model instances populated with deterministic Chamoli seed data."""
    # States & Districts
    states = []
    districts = []
    for s_info in STATES_AND_DISTRICTS:
        s = State(id=s_info["id"], name=s_info["name"], code=s_info["code"])
        s.districts = []
        for d_info in s_info["districts"]:
            d = District(
                id=d_info["id"],
                state_id=s_info["id"],
                name=d_info["name"],
                headquarters=d_info.get("headquarters"),
            )
            d.state = s
            s.districts.append(d)
            districts.append(d)
        states.append(s)

    # Habitations
    habitations = []
    for h in HABITATIONS_DATA:
        geom = from_shape(Point(h["lng"], h["lat"]), srid=4326)
        hab = Habitation(
            id=h["id"],
            name=h["name"],
            district=h["district"],
            state=h["state"],
            district_id=h.get("district_id"),
            geom=geom,
            risk_score=h["risk_score"],
            risk_category=h["risk_category"],
            urgency=h["urgency"],
            population=h["population"],
            households=h["households"],
            confidence=h["confidence"],
            hazard_scores=h["hazard_scores"],
            vulnerability_score=h["vulnerability_score"],
            risk_history=h["risk_history"],
            elevation=h["elevation"],
            nearest_road=h["nearest_road"],
            nearest_hospital=h["nearest_hospital"],
            nearest_school=h["nearest_school"],
            last_assessed=h["last_assessed"],
            verification_status=h["verification_status"],
        )
        habitations.append(hab)

    # Hazard Zones
    hazard_zones = []
    for rz in HAZARD_ZONES_DATA:
        coords = [(lng, lat) for lat, lng in rz["polygon_latlng"]]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        geom = from_shape(Polygon(coords), srid=4326)
        zone = HazardZone(
            id=rz["id"],
            name=rz["name"],
            geom=geom,
            hazard_types=rz["hazard_types"],
            composite_risk_score=rz["composite_risk_score"],
            habitation_count=rz["habitation_count"],
            population_affected=rz["population_affected"],
            area_km_sq=rz["area_km_sq"],
            declared_date=rz["declared_date"],
            last_updated=rz["last_updated"],
        )
        hazard_zones.append(zone)

    # Candidate Sites
    candidate_sites = []
    for cs in CANDIDATE_SITES_DATA:
        b_coords = [(lng, lat) for lat, lng in cs["bounds_latlng"]]
        if b_coords[0] != b_coords[-1]:
            b_coords.append(b_coords[0])
        poly_geom = from_shape(Polygon(b_coords), srid=4326)
        c_lat, c_lng = cs["centroid_latlng"]
        centroid_geom = from_shape(Point(c_lng, c_lat), srid=4326)
        site = CandidateSite(
            id=cs["id"],
            name=cs["name"],
            district=cs["district"],
            state=cs["state"],
            geom=poly_geom,
            centroid=centroid_geom,
            suitability_score=cs["suitability_score"],
            carrying_capacity=cs["carrying_capacity"],
            current_utilization=cs["current_utilization"],
            area_hectares=cs["area_hectares"],
            elevation=cs["elevation"],
            distance_from_hazard=cs["distance_from_hazard"],
            road_access=cs["road_access"],
            water_access=cs["water_access"],
            electricity_access=cs["electricity_access"],
            land_use_type=cs["land_use_type"],
            ownership=cs["ownership"],
            status=cs["status"],
            verification_status=cs["verification_status"],
            assigned_habitations=cs["assigned_habitations"],
        )
        candidate_sites.append(site)

    # Infrastructure Assets
    infrastructure = []
    for inf in INFRASTRUCTURE_DATA:
        geom = from_shape(Point(inf["lng"], inf["lat"]), srid=4326)
        ia = InfrastructureAsset(
            id=inf["id"],
            name=inf["name"],
            type=inf["type"],
            geom=geom,
            status=inf["status"],
            capacity=inf["capacity"],
            district=inf.get("district"),
        )
        infrastructure.append(ia)

    # Data Sources
    data_sources = []
    for ds in DATA_SOURCES_DATA:
        obj = DataSource(
            id=ds["id"],
            name=ds["name"],
            provider=ds["provider"],
            type=ds["type"],
            status=ds["status"],
            last_sync=ds["last_sync"],
            records_count=ds["records_count"],
            latency_ms=ds["latency_ms"],
        )
        data_sources.append(obj)

    # Disaster Events
    disaster_events = []
    for de in DISASTER_EVENTS_DATA:
        pt_geom = from_shape(Point(de["lng"], de["lat"]), srid=4326) if "lat" in de else None
        evt = DisasterEvent(
            id=de["id"],
            title=de["title"],
            hazard_type=de["hazard_type"],
            severity=de["severity"],
            event_date=de["event_date"],
            district=de["district"],
            geom=pt_geom,
            fatalities=de["fatalities"],
            displaced_persons=de["displaced_persons"],
            description=de["description"],
        )
        disaster_events.append(evt)

    # Relocation Priorities
    relocation_priorities = [
        RelocationPriority(
            id=f"RP-{i+1:03d}",
            habitation_id=h.id,
            habitation_name=h.name,
            urgency=h.urgency,
            risk_score=h.risk_score,
            population=h.population,
            district=h.district,
            assigned_site_id="RS-001" if i == 0 else None,
            assigned_site_name="Pipalkoti Plateau Site" if i == 0 else None,
            estimated_cost=round(h.population * 0.45, 1),
            timeline_months=6 if h.urgency == "IMMEDIATE" else 18,
        )
        for i, h in enumerate(habitations)
    ]

    # Operational Alerts
    operational_alerts = [
        OperationalAlert(
            id="ALERT-001",
            message="Khar Village landslide sensor alert: Inclinometer threshold exceeded",
            type="ESCALATION",
            severity="CRITICAL",
            timestamp="2026-09-28T05:30:00Z",
            habitation_id="HAB-001",
            read=False,
        )
    ]

    return {
        State: states,
        District: districts,
        Habitation: habitations,
        HazardZone: hazard_zones,
        CandidateSite: candidate_sites,
        InfrastructureAsset: infrastructure,
        DataSource: data_sources,
        DisasterEvent: disaster_events,
        RelocationPriority: relocation_priorities,
        OperationalAlert: operational_alerts,
    }


class MockQuery:
    def __init__(self, items):
        self._items = list(items)

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None

    def scalar(self):
        return len(self._items)


class MockDbSession:
    def __init__(self, data_map):
        self.data_map = data_map

    def query(self, *entities):
        entity = entities[0]
        # Handle func.count or column
        target = getattr(entity, "class_", entity)
        for model_cls, items in self.data_map.items():
            if target is model_cls or (hasattr(entity, "table") and entity.table.name == model_cls.__tablename__):
                return MockQuery(items)
        return MockQuery([])

    def execute(self, stmt):
        mock_result = MagicMock()
        mock_result.scalar.return_value = "3.4 USE_GEOS=1 USE_PROJ=1"
        return mock_result

    def close(self):
        pass


@pytest.fixture
def client(seeded_mock_objects) -> Generator[TestClient, None, None]:
    mock_db = MockDbSession(seeded_mock_objects)

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
