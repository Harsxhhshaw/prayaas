"""Unit tests for spatial calculations and GeoJSON helpers.

Verifies:
- RFC 7946 GeoJSON [longitude, latitude] coordinate ordering
- Geodesic Haversine distance in km (not raw degrees)
- Spherical polygon area in sq km (not raw degrees)
- Bounding-box parsing and error handling
"""

import pytest
from shapely.geometry import Point, Polygon
from app.spatial import (
    apply_bbox_filter,
    haversine_distance_km,
    parse_bbox,
    spherical_polygon_area_sq_km,
    to_geojson_point,
    to_geojson_polygon,
)


def test_haversine_distance_km():
    """Verify geodesic distance calculation between known Chamoli points."""
    # Gopeshwar (30.4120, 79.3230) to Joshimath (30.5556, 79.5650)
    dist = haversine_distance_km(30.4120, 79.3230, 30.5556, 79.5650)
    # Geodesic distance should be ~28-30 km, definitely not degree diff (~0.27)
    assert 25.0 < dist < 35.0
    assert isinstance(dist, float)

    # Identical points should be 0.0 km
    assert haversine_distance_km(30.4120, 79.3230, 30.4120, 79.3230) == 0.0


def test_spherical_polygon_area():
    """Verify spherical polygon area is computed in km²."""
    # Approx 0.1 deg x 0.1 deg box in Chamoli region
    coords = [
        (79.4, 30.4),
        (79.5, 30.4),
        (79.5, 30.5),
        (79.4, 30.5),
        (79.4, 30.4),
    ]
    area = spherical_polygon_area_sq_km(coords)
    # 0.1 deg ~ 10-11 km, so area ~ 100-120 km²
    assert 90.0 < area < 130.0
    assert isinstance(area, float)


def test_parse_bbox():
    """Test valid and invalid bounding box strings."""
    min_lng, min_lat, max_lng, max_lat = parse_bbox("79.3,30.2,79.6,30.5")
    assert min_lng == 79.3
    assert min_lat == 30.2
    assert max_lng == 79.6
    assert max_lat == 30.5

    # Invalid length
    with pytest.raises(ValueError, match="exactly 4 comma-separated values"):
        parse_bbox("79.3,30.2,79.6")

    # Inverted coordinates
    with pytest.raises(ValueError, match="cannot exceed max"):
        parse_bbox("79.6,30.5,79.3,30.2")


def test_to_geojson_point_order():
    """Requirement 14: GeoJSON coordinate order must strictly be [longitude, latitude]."""
    pt = Point(79.5603, 30.4983)  # Point(x, y) = Point(lng, lat)
    geojson = to_geojson_point(pt)
    assert geojson["type"] == "Point"
    assert geojson["coordinates"] == [79.5603, 30.4983]
    # First coordinate is longitude (approx 79.5), second is latitude (approx 30.5)
    assert geojson["coordinates"][0] > 70.0
    assert geojson["coordinates"][1] < 40.0


def test_to_geojson_polygon_order():
    """Requirement 14: GeoJSON polygon coordinates must strictly be [longitude, latitude]."""
    coords = [(79.54, 30.51), (79.60, 30.51), (79.60, 30.46), (79.54, 30.46), (79.54, 30.51)]
    poly = Polygon(coords)
    geojson = to_geojson_polygon(poly)
    assert geojson["type"] == "Polygon"
    ring = geojson["coordinates"][0]
    assert len(ring) == 5
    for coord in ring:
        assert len(coord) == 2
        # longitude first, latitude second
        assert coord[0] > 70.0
        assert coord[1] < 40.0
