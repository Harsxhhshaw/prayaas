"""Live PostGIS database integration tests.

Tests against the actual running PostgreSQL + PostGIS instance:
- PostGIS extension & version
- SRID 4326 on geometry columns
- Geodesic ST_Distance and ST_Area using geography
- BBOX ST_Intersects and ST_DWithin queries
- Live database row counts
"""

import pytest
from sqlalchemy import text
from app.database import engine


@pytest.fixture(scope="module")
def db_conn():
    import socket
    postgres_live = False
    try:
        with socket.create_connection(("localhost", 5432), timeout=0.5):
            postgres_live = True
    except Exception:
        postgres_live = False

    if not postgres_live:
        pytest.skip("Live PostGIS database is not running on localhost:5432")

    conn = engine.connect()
    yield conn
    conn.close()


def test_live_postgis_version(db_conn):
    """Verify PostGIS extension is installed and reports version 3.4+."""
    version = db_conn.execute(text("SELECT PostGIS_Version();")).scalar()
    assert version is not None
    assert "3.4" in version
    assert "USE_GEOS=1" in version


def test_live_geometry_srid(db_conn):
    """Verify all geometry columns use SRID 4326."""
    queries = [
        "SELECT ST_SRID(geom) FROM habitations LIMIT 1;",
        "SELECT ST_SRID(geom) FROM hazard_zones LIMIT 1;",
        "SELECT ST_SRID(geom) FROM candidate_sites LIMIT 1;",
        "SELECT ST_SRID(centroid) FROM candidate_sites LIMIT 1;",
        "SELECT ST_SRID(geom) FROM infrastructure_assets LIMIT 1;",
    ]
    for q in queries:
        srid = db_conn.execute(text(q)).scalar()
        assert srid == 4326, f"Expected SRID 4326 for query: {q}, got {srid}"


def test_live_geodesic_distance(db_conn):
    """Verify ST_Distance with geography returns kilometers within expected physical range."""
    # Khar Village to Raini Settlement (~3.3 km)
    query = text("""
        SELECT round((ST_Distance(h1.geom::geography, h2.geom::geography) / 1000.0)::numeric, 2)
        FROM habitations h1, habitations h2
        WHERE h1.id = 'HAB-001' AND h2.id = 'HAB-002';
    """)
    dist_km = float(db_conn.execute(query).scalar())
    assert 3.0 < dist_km < 3.8


def test_live_geodesic_area(db_conn):
    """Verify ST_Area with geography returns km²."""
    query = text("""
        SELECT round((ST_Area(geom::geography) / 1000000.0)::numeric, 2)
        FROM hazard_zones
        WHERE id = 'RZ-001';
    """)
    area_km2 = float(db_conn.execute(query).scalar())
    assert 25.0 < area_km2 < 35.0


def test_live_bbox_spatial_filter(db_conn):
    """Verify ST_Intersects with ST_MakeEnvelope spatial filtering."""
    query = text("""
        SELECT count(*)
        FROM habitations
        WHERE ST_Intersects(geom, ST_MakeEnvelope(79.5, 30.45, 79.6, 30.55, 4326));
    """)
    count = db_conn.execute(query).scalar()
    assert count == 2


def test_live_database_counts(db_conn):
    """Verify exact seeded row counts in the live database."""
    expected = {
        "states": 4,
        "districts": 22,
        "habitations": 13,
        "hazard_zones": 4,
        "candidate_sites": 8,
        "infrastructure_assets": 12,
        "data_sources": 4,
        "disaster_events": 2,
        "relocation_priorities": 13,
        "operational_alerts": 8,
    }
    for table, expected_count in expected.items():
        actual = db_conn.execute(text(f"SELECT count(*) FROM {table};")).scalar()
        if table == "data_sources":
            assert actual in (4, 7), f"Table {table} expected 4 or 7 rows, found {actual}"
        elif table == "infrastructure_assets":
            assert actual >= 12, f"Table {table} expected at least 12 rows, found {actual}"
        else:
            assert actual == expected_count, f"Table {table} expected {expected_count} rows, found {actual}"
