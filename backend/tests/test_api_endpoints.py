"""Integration tests for all required PRAYAAS API endpoints.

Requirement 11:
- /api/health
- /api/health/database
- /api/states
- /api/districts
- /api/habitations
- /api/habitations/{id}
- /api/hazard-zones
- /api/infrastructure
- /api/candidate-sites
- /api/data-sources
- /api/disaster-events

Requirement 12:
- Map-friendly GeoJSON endpoints

Requirement 13 & 14:
- Bounding-box spatial filtering & [lng, lat] coordinate ordering

Requirement 25:
- Swagger/OpenAPI docs at /docs
"""


def test_health_endpoints(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "prayaas-api"

    res_db = client.get("/api/health/database")
    assert res_db.status_code == 200
    db_data = res_db.json()
    assert db_data["status"] == "ok"
    assert "postgis_version" in db_data


def test_docs_endpoints(client):
    """Requirement 25: Swagger/OpenAPI works at /docs."""
    res = client.get("/docs")
    assert res.status_code == 200
    assert "swagger" in res.text.lower() or "html" in res.headers.get("content-type", "")

    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    schema = res_openapi.json()
    assert "paths" in schema
    assert "/api/habitations" in schema["paths"]


def test_states_and_districts(client):
    res_states = client.get("/api/states")
    assert res_states.status_code == 200
    states_data = res_states.json()
    assert "items" in states_data
    assert states_data["total"] >= 1
    assert any(s["name"] == "Uttarakhand" for s in states_data["items"])

    res_dist = client.get("/api/districts")
    assert res_dist.status_code == 200
    dist_data = res_dist.json()
    assert "items" in dist_data
    assert any(d["name"] == "Chamoli" for d in dist_data["items"])


def test_habitations_list_and_detail(client):
    res = client.get("/api/habitations")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 10
    first_hab = data["items"][0]
    assert "position" in first_hab
    assert "lat" in first_hab["position"]
    assert "lng" in first_hab["position"]
    assert "riskScore" in first_hab

    # Detail
    res_single = client.get(f"/api/habitations/{first_hab['id']}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == first_hab["id"]


def test_habitations_geojson(client):
    """Requirement 12 & 14: GeoJSON FeatureCollection with [lng, lat] coordinates."""
    res = client.get("/api/habitations/geojson")
    assert res.status_code == 200
    geojson = res.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) >= 10

    f = geojson["features"][0]
    assert f["type"] == "Feature"
    assert f["geometry"]["type"] == "Point"
    coords = f["geometry"]["coordinates"]
    # Check [longitude, latitude] ordering (lng ~ 79.x, lat ~ 30.x)
    assert coords[0] > 70.0
    assert coords[1] < 40.0
    assert "properties" in f
    assert "riskScore" in f["properties"]


def test_hazard_zones_endpoints(client):
    res = client.get("/api/hazard-zones")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 4
    first_zone = data["items"][0]
    assert "bounds" in first_zone
    assert len(first_zone["bounds"]) >= 4

    # GeoJSON
    res_geo = client.get("/api/hazard-zones/geojson")
    assert res_geo.status_code == 200
    geo_data = res_geo.json()
    assert geo_data["type"] == "FeatureCollection"
    f = geo_data["features"][0]
    assert f["geometry"]["type"] == "Polygon"
    ring = f["geometry"]["coordinates"][0]
    assert len(ring) >= 4
    # Longitude first
    assert ring[0][0] > 70.0
    assert ring[0][1] < 40.0


def test_candidate_sites_endpoints(client):
    res = client.get("/api/candidate-sites")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 6
    site = data["items"][0]
    assert "carryingCapacity" in site
    assert "suitabilityScore" in site

    # GeoJSON
    res_geo = client.get("/api/candidate-sites/geojson")
    assert res_geo.status_code == 200
    assert res_geo.json()["type"] == "FeatureCollection"


def test_infrastructure_endpoints(client):
    res = client.get("/api/infrastructure")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 10
    asset = data["items"][0]
    assert "type" in asset
    assert "status" in asset

    # GeoJSON
    res_geo = client.get("/api/infrastructure/geojson")
    assert res_geo.status_code == 200
    assert res_geo.json()["type"] == "FeatureCollection"


def test_data_sources_endpoint(client):
    res = client.get("/api/data-sources")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 2
    ds = data["items"][0]
    assert "provider" in ds
    assert "recordsCount" in ds


def test_disaster_events_endpoint(client):
    res = client.get("/api/disaster-events")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 2
    evt = data["items"][0]
    assert "hazardType" in evt
    assert "eventDate" in evt


def test_bbox_filtering_params(client):
    """Requirement 13: Bounding-box spatial filtering parameter validation."""
    # Valid bbox parameter
    res = client.get("/api/habitations?bbox=79.2,30.2,79.8,30.8")
    assert res.status_code == 200

    # Invalid bbox format
    res_err = client.get("/api/habitations?bbox=79.2,30.2")
    assert res_err.status_code == 400
