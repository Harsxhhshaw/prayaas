"""Test configuration and fixtures for PRAYAAS API tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Point, Polygon, MultiPolygon
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
from app.models.candidate_discovery import CandidateDiscoveryRun, CandidateParcel
from app.models.enums import DataMode
from app.models.risk import VulnerabilityProfile
from app.seeds.seed_chamoli import (
    CANDIDATE_SITES_DATA,
    DATA_SOURCES_DATA,
    DISASTER_EVENTS_DATA,
    HABITATIONS_DATA,
    HAZARD_ZONES_DATA,
    INFRASTRUCTURE_DATA,
    STATES_AND_DISTRICTS,
    VULNERABILITY_PROFILES_DATA,
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
            data_mode=rz.get("data_mode", DataMode.DEMO.value),
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
            data_mode=cs.get("data_mode", DataMode.DEMO.value),
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
            data_mode=inf.get("data_mode", DataMode.DEMO.value),
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
            data_mode=ds.get("data_mode", DataMode.DEMO.value),
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
            data_mode=de.get("data_mode", DataMode.DEMO.value),
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

    # Vulnerability Profiles
    vulnerability_profiles = [
        VulnerabilityProfile(
            id=f"VP-{vp['habitation_id']}",
            habitation_id=vp["habitation_id"],
            population=vp["population"],
            households=vp["households"],
            children_share=vp["children_share"],
            elderly_share=vp["elderly_share"],
            disability_share=vp["disability_share"],
            housing_vulnerability=vp["housing_vulnerability"],
            population_density=vp["population_density"],
            healthcare_access_score=vp["healthcare_access_score"],
            road_access_score=vp["road_access_score"],
            isolation_score=vp["isolation_score"],
            data_confidence=vp["data_confidence"],
            data_mode=DataMode.FIELD.value,
        )
        for vp in VULNERABILITY_PROFILES_DATA
    ]

    # Candidate Discovery Run for HAB-002 (Raini)
    cd_run = CandidateDiscoveryRun(
        id="CDR-8E12008ADCC0",
        origin_habitation_id="HAB-002",
        analysis_version="PRAYAAS-CANDIDATE-1.0",
        config_version="1.0.0",
        search_radius_km=15.0,
        status="COMPLETED",
        started_at=datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 9, 30, 0, 5, tzinfo=timezone.utc),
        created_at=datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 30, 0, 5, tzinfo=timezone.utc),
        candidate_count=3,
        total_aoi_area_sq_km=706.86,
        excluded_area_sq_km=419.32,
        feasible_area_sq_km=287.54,
        feasible_percent=40.7,
    )
    discovery_runs = [cd_run]

    # Modeled Candidate Parcels for HAB-002
    p_poly = MultiPolygon([Polygon([(79.55, 30.50), (79.56, 30.50), (79.56, 30.51), (79.55, 30.51), (79.55, 30.50)])])
    p_geom = from_shape(p_poly, srid=4326)
    c_geom = from_shape(Point(79.555, 30.505), srid=4326)

    candidate_parcels = [
        CandidateParcel(
            id="PARCEL-5958B764DA60",
            discovery_run_id="CDR-8E12008ADCC0",
            origin_habitation_id="HAB-002",
            geom=p_geom,
            centroid=c_geom,
            area_sq_km=0.20,
            area_hectares=20.0,
            distance_from_origin_km=0.46,
            mean_slope_degrees=8.5,
            suitability_score=88.5,
            robustness_score=75.0,
            rank_stability=95.0,
            rank=1,
            status="REQUIRES_FIELD_REVIEW",
            confidence_score=75.0,
            exclusion_summary={"SLOPE": "PASS", "HAZARD": "PASS", "SETTLEMENT": "PASS"},
            criteria_scores={"ROAD_ACCESS": 85.0, "WATER_ACCESS": 80.0},
            reason_codes=["OPTIMAL_DISTANCE", "SAFE_SLOPE"],
            limitations=["ROAD_CONNECTIVITY_GAP"],
            explanation={},
            data_mode=DataMode.MODELED.value,
            created_at=datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 9, 30, 0, 5, tzinfo=timezone.utc),
        ),
        CandidateParcel(
            id="PARCEL-E3247A11E0EC",
            discovery_run_id="CDR-8E12008ADCC0",
            origin_habitation_id="HAB-002",
            geom=p_geom,
            centroid=c_geom,
            area_sq_km=0.02,
            area_hectares=2.0,
            distance_from_origin_km=9.35,
            mean_slope_degrees=9.9,
            suitability_score=91.2,
            robustness_score=61.5,
            rank_stability=85.0,
            rank=2,
            status="REQUIRES_FIELD_REVIEW",
            confidence_score=37.8,
            exclusion_summary={"SLOPE": "PASS", "HAZARD": "PASS", "SETTLEMENT": "PASS"},
            criteria_scores={"ROAD_ACCESS": 70.0, "WATER_ACCESS": 75.0},
            reason_codes=["HIGH_SUITABILITY"],
            limitations=["LIMITED_AREA"],
            explanation={},
            data_mode=DataMode.MODELED.value,
            created_at=datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 9, 30, 0, 5, tzinfo=timezone.utc),
        ),
        CandidateParcel(
            id="PARCEL-287BBE825053",
            discovery_run_id="CDR-8E12008ADCC0",
            origin_habitation_id="HAB-002",
            geom=p_geom,
            centroid=c_geom,
            area_sq_km=0.18,
            area_hectares=18.0,
            distance_from_origin_km=8.85,
            mean_slope_degrees=11.0,
            suitability_score=85.0,
            robustness_score=68.0,
            rank_stability=88.0,
            rank=3,
            status="REQUIRES_FIELD_REVIEW",
            confidence_score=60.0,
            exclusion_summary={"SLOPE": "PASS", "HAZARD": "PASS", "SETTLEMENT": "PASS"},
            criteria_scores={"ROAD_ACCESS": 65.0, "WATER_ACCESS": 70.0},
            reason_codes=["EXPANSION_CAPACITY"],
            limitations=["MODERATE_SLOPE"],
            explanation={},
            data_mode=DataMode.MODELED.value,
            created_at=datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 9, 30, 0, 5, tzinfo=timezone.utc),
        ),
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
        VulnerabilityProfile: vulnerability_profiles,
        CandidateDiscoveryRun: discovery_runs,
        CandidateParcel: candidate_parcels,
    }


class MockQuery:
    def __init__(self, items, parent_list=None, entities=None):
        self._items = list(items)
        self._parent_list = parent_list if parent_list is not None else items
        self._entities = entities or ()

    def filter(self, *criterion, **kwargs):
        if not criterion:
            return self
        filtered = []
        for item in self._items:
            match = True
            for c in criterion:
                if hasattr(c, "left") and hasattr(c, "right"):
                    attr_name = getattr(c.left, "name", None) or getattr(c.left, "key", None)
                    val = getattr(c.right, "value", c.right)
                    if attr_name and hasattr(item, attr_name):
                        item_val = getattr(item, attr_name)
                        op = getattr(c, "operator", None)
                        op_name = getattr(op, "__name__", "") if op else ""
                        if op_name == "in_op":
                            if not isinstance(val, (list, tuple, set)) or item_val not in val:
                                match = False
                                break
                        elif op_name == "notin_op":
                            if isinstance(val, (list, tuple, set)) and item_val in val:
                                match = False
                                break
                        elif op is not None:
                            try:
                                if not op(item_val, val):
                                    match = False
                                    break
                            except Exception:
                                if item_val != val:
                                    match = False
                                    break
                        else:
                            if item_val != val:
                                match = False
                                break
            if match:
                filtered.append(item)
        return MockQuery(filtered, parent_list=self._parent_list, entities=self._entities)

    def order_by(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        if len(self._entities) >= 2:
            first = self._entities[0]
            attr = getattr(first, "name", None) or getattr(first, "key", "data_mode")
            counts = {}
            for item in self._items:
                val = getattr(item, attr, None) or "DEMO"
                counts[val] = counts.get(val, 0) + 1
            return MockQuery([(k, v) for k, v in counts.items()], entities=self._entities)
        return self

    def distinct(self, *args, **kwargs):
        return self

    def limit(self, n):
        return MockQuery(self._items[:n], parent_list=self._parent_list, entities=self._entities)

    def offset(self, n):
        return MockQuery(self._items[n:], parent_list=self._parent_list, entities=self._entities)

    def delete(self, *args, **kwargs):
        count = len(self._items)
        if isinstance(self._parent_list, list):
            for item in list(self._items):
                if item in self._parent_list:
                    self._parent_list.remove(item)
        self._items.clear()
        return count

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
                return MockQuery(items, parent_list=items, entities=entities)
        return MockQuery([], entities=entities)

    def add(self, instance):
        cls = type(instance)
        if cls not in self.data_map:
            self.data_map[cls] = []
        self.data_map[cls].append(instance)

    def add_all(self, instances):
        for inst in instances:
            self.add(inst)

    def delete(self, instance):
        cls = type(instance)
        if cls in self.data_map and instance in self.data_map[cls]:
            self.data_map[cls].remove(instance)

    def commit(self):
        pass

    def rollback(self):
        pass

    def flush(self):
        pass

    def refresh(self, instance):
        pass

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


@pytest.fixture
def db(seeded_mock_objects):
    """Provides a SQLAlchemy session. If real PostGIS is reachable, connects to it; otherwise uses MockDbSession."""
    import socket
    from app.database import SessionLocal

    postgres_live = False
    try:
        with socket.create_connection(("localhost", 5432), timeout=0.5):
            postgres_live = True
    except Exception:
        postgres_live = False

    if postgres_live:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    else:
        yield MockDbSession(seeded_mock_objects)


