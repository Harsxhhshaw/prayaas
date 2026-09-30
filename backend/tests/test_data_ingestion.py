"""Unit and integration tests for Data Ingestion pipelines and Source Registry."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, Polygon

from app.models.data_source import DataSource
from app.models.enums import DataMode, IngestionStatus, SourceFreshness
from app.models.hazard_zone import HazardZone
from app.models.infrastructure import InfrastructureAsset
from app.models.ingestion import EnvironmentalObservation, IngestionRun, RasterDataset
from app.models.risk import VulnerabilityProfile
from app.services.ingestion.base import BaseIngestionConnector
from app.services.ingestion.csv_import import CSVImporter
from app.services.ingestion.geojson_import import GeoJSONImporter
from app.services.ingestion.osm import OSMIngestionConnector, map_osm_tags_to_type
from app.services.ingestion.registry import SourceRegistryService, evaluate_source_freshness
from app.services.ingestion.terrain import TerrainProcessingService, calculate_slope_degrees
from app.services.ingestion.weather import WeatherIngestionConnector


def test_source_freshness_evaluation():
    now = datetime.now(timezone.utc)

    # 1. Fresh source (< expected refresh)
    source_fresh = DataSource(
        id="SRC-TEST-1",
        name="Fresh Feed",
        provider="Test",
        type="WEATHER_STATION",
        expected_refresh_seconds=3600,
        last_successful_ingestion=now - timedelta(minutes=30),
    )
    freshness, is_stale = evaluate_source_freshness(source_fresh, now)
    assert freshness == SourceFreshness.CURRENT
    assert is_stale is False

    # 2. Aging source (between 1x and 3x expected refresh)
    source_aging = DataSource(
        id="SRC-TEST-2",
        name="Aging Feed",
        provider="Test",
        type="WEATHER_STATION",
        expected_refresh_seconds=3600,
        last_successful_ingestion=now - timedelta(minutes=90),
    )
    freshness, is_stale = evaluate_source_freshness(source_aging, now)
    assert freshness == SourceFreshness.AGING
    assert is_stale is False

    # 3. Stale source (> 3x expected refresh)
    source_stale = DataSource(
        id="SRC-TEST-3",
        name="Stale Feed",
        provider="Test",
        type="WEATHER_STATION",
        expected_refresh_seconds=3600,
        last_successful_ingestion=now - timedelta(hours=5),
    )
    freshness, is_stale = evaluate_source_freshness(source_stale, now)
    assert freshness == SourceFreshness.STALE
    assert is_stale is True

    # 4. Unknown source (never ingested)
    source_unknown = DataSource(
        id="SRC-TEST-4",
        name="Unknown Feed",
        provider="Test",
        type="WEATHER_STATION",
        expected_refresh_seconds=3600,
        last_successful_ingestion=None,
    )
    freshness, is_stale = evaluate_source_freshness(source_unknown, now)
    assert freshness == SourceFreshness.UNKNOWN
    assert is_stale is True


def test_base_ingestion_connector_lifecycle(db):
    connector = BaseIngestionConnector(db, ingestion_type="UNIT_TEST_INGEST", data_mode="DEMO")
    with connector.run_context() as ctx:
        ctx.inc_received(10)
        ctx.inc_inserted(8)
        ctx.inc_updated(1)
        ctx.inc_rejected(1)
        ctx.set_metadata("test_param", "unit_value")

    run = db.query(IngestionRun).filter(IngestionRun.id == ctx.run.id).first()
    assert run is not None
    assert run.status == IngestionStatus.COMPLETED.value
    assert run.records_received == 10
    assert run.records_inserted == 8
    assert run.records_updated == 1
    assert run.records_rejected == 1
    assert run.ingestion_metadata["test_param"] == "unit_value"
    assert run.finished_at is not None


def test_osm_tag_mapping():
    assert map_osm_tags_to_type({"amenity": "hospital"}) == "HOSPITAL"
    assert map_osm_tags_to_type({"amenity": "clinic"}) == "HOSPITAL"
    assert map_osm_tags_to_type({"amenity": "school"}) == "SCHOOL"
    assert map_osm_tags_to_type({"aeroway": "helipad"}) == "HELIPAD"
    assert map_osm_tags_to_type({"amenity": "shelter"}) == "SHELTER"


def test_osm_ingestion_idempotency(db):
    from app.services.ingestion.osm import FALLBACK_CHAMOLI_OSM
    connector = OSMIngestionConnector(db)
    try:
        with patch.object(connector, "fetch_overpass_data", return_value=FALLBACK_CHAMOLI_OSM):
            # Run first ingestion
            ctx1 = connector.ingest(bbox=[30.2, 79.0, 30.6, 79.7])
            assert ctx1.received > 0

            # Run second ingestion (should update rather than re-inserting)
            ctx2 = connector.ingest(bbox=[30.2, 79.0, 30.6, 79.7])
            assert ctx2.inserted == 0  # Deduplicated!
            assert ctx2.updated == ctx2.received
    finally:
        db.query(InfrastructureAsset).filter(~InfrastructureAsset.id.startswith("INF-")).delete(synchronize_session=False)
        db.commit()


def test_weather_ingestion_ttl_cache(db):
    connector = WeatherIngestionConnector(db)
    # Ingest for HAB-001
    ctx1 = connector.ingest_for_habitations(["HAB-001"], force_refresh=True)
    assert ctx1.inserted > 0

    # Ingest again without force_refresh (should hit TTL cache and skip)
    ctx2 = connector.ingest_for_habitations(["HAB-001"], force_refresh=False)
    assert ctx2.skipped == 1
    assert ctx2.inserted == 0


def test_geojson_importer_hazard_zone(db):
    geojson_payload = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[79.55, 30.55], [79.57, 30.55], [79.57, 30.57], [79.55, 30.57], [79.55, 30.55]]
            ],
        },
        "properties": {
            "name": "Test Geodesic Zone",
            "composite_risk_score": 85,
            "area_km_sq": 4.2,
        },
    }
    importer = GeoJSONImporter(db, source_name="Test Hazard Upload", source_id="DS-001")
    ctx = importer.import_features(geojson_payload, entity_type="HAZARD_ZONE")
    assert ctx.inserted == 1

    zone = db.query(HazardZone).filter(HazardZone.name == "Test Geodesic Zone").first()
    try:
        assert zone is not None
        assert zone.computed_area_sq_km is not None
        assert 3.5 < zone.computed_area_sq_km < 5.0
        assert zone.source_declared_area_sq_km == 4.2
    finally:
        if zone:
            db.delete(zone)
            db.commit()


def test_csv_importer_vulnerability_profile(db):
    csv_data = """habitation_id,population,households,children_share,elderly_share,disability_share,housing_vulnerability,healthcare_access_score,road_access_score,isolation_score,data_confidence
HAB-001,450,92,0.25,0.19,0.06,85.0,22.0,28.0,80.0,90.0
"""
    importer = CSVImporter(db, source_name="Test Survey Import", source_id="DS-001")
    ctx = importer.import_csv(csv_data, entity_type="VULNERABILITY")
    assert ctx.received == 1

    vp = db.query(VulnerabilityProfile).filter(VulnerabilityProfile.habitation_id == "HAB-001").first()
    assert vp is not None
    assert vp.population == 450
    assert vp.housing_vulnerability == 85.0
    assert vp.data_confidence == 90.0


def test_terrain_processor(db):
    service = TerrainProcessingService(db)
    ctx = service.register_catalog_datasets()
    assert ctx.received >= 2

    # Check slope math
    slope = calculate_slope_degrees(dz_dx=0.5, dz_dy=0.5)
    assert 34.0 < slope < 36.0  # atan(sqrt(0.5)) ~ 35.26 degrees
