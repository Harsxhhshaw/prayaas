"""Spatial utilities for PRAYAAS.

Handles:
- EPSG:4326 geometry parsing & serialization
- RFC 7946 GeoJSON [longitude, latitude] ordering
- Geodesic distance (Haversine/WGS84) in kilometers (not raw lat/lon degrees)
- Geodesic polygon area (Spherical) in square km and hectares
- PostGIS bounding box filtering
"""

from __future__ import annotations

import math
from typing import Any
from sqlalchemy import cast
from geoalchemy2 import Geography, Geometry, functions as func
from geoalchemy2.shape import to_shape
from shapely.geometry import Point, Polygon


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    """Parse a bbox string formatted as 'minLng,minLat,maxLng,maxLat'.

    Raises ValueError if formatting is invalid.
    """
    parts = [float(p.strip()) for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must contain exactly 4 comma-separated values: minLng,minLat,maxLng,maxLat")
    min_lng, min_lat, max_lng, max_lat = parts
    if min_lng > max_lng or min_lat > max_lat:
        raise ValueError("Invalid bbox coordinates: min cannot exceed max")
    return min_lng, min_lat, max_lng, max_lat


def apply_bbox_filter(query, geom_column, min_lng: float, min_lat: float, max_lng: float, max_lat: float):
    """Filter SQLAlchemy query by bounding box using PostGIS ST_Intersects and ST_MakeEnvelope."""
    envelope = func.ST_MakeEnvelope(min_lng, min_lat, max_lng, max_lat, 4326)
    return query.filter(func.ST_Intersects(geom_column, envelope))


def postgis_distance_km(geom1, geom2):
    """PostGIS expression calculating true geodesic distance in km using geography casting."""
    return func.ST_Distance(cast(geom1, Geography), cast(geom2, Geography)) / 1000.0


def postgis_area_sq_km(geom):
    """PostGIS expression calculating true geodesic area in km² using geography casting."""
    return func.ST_Area(cast(geom, Geography)) / 1000000.0


def postgis_area_hectares(geom):
    """PostGIS expression calculating true geodesic area in hectares using geography casting."""
    return func.ST_Area(cast(geom, Geography)) / 10000.0


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers.

    Requirement 15: Uses proper geodesic/geography calculation, not raw degrees.
    """
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


def spherical_polygon_area_sq_km(coords: list[tuple[float, float]]) -> float:
    """Calculate the surface area of a spherical polygon in square kilometers.

    `coords` is a list of (longitude, latitude) vertices.
    Requirement 15: Projected/spherical area, not degree multiplications.
    """
    if len(coords) < 3:
        return 0.0

    R = 6371.0  # Earth radius in km
    area = 0.0
    n = len(coords)
    if coords[0] == coords[-1]:
        coords = coords[:-1]
        n = len(coords)

    for i in range(n):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[(i + 1) % n]
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        lam1 = math.radians(lon1)
        lam2 = math.radians(lon2)
        area += (lam2 - lam1) * (2.0 + math.sin(phi1) + math.sin(phi2))

    area = abs(area * (R**2) / 2.0)
    return round(area, 4)


def to_geojson_point(geom) -> dict[str, Any]:
    """Convert a PostGIS / Shapely Point into RFC 7946 GeoJSON Point geometry.

    Requirement 14: Coordinate order is [longitude, latitude].
    """
    shape = to_shape(geom) if hasattr(geom, "data") else geom
    return {
        "type": "Point",
        "coordinates": [round(shape.x, 6), round(shape.y, 6)],
    }


def to_geojson_polygon(geom) -> dict[str, Any]:
    """Convert a PostGIS / Shapely Polygon into RFC 7946 GeoJSON Polygon geometry.

    Requirement 14: Coordinate order is [longitude, latitude].
    """
    shape = to_shape(geom) if hasattr(geom, "data") else geom
    coords = [[round(x, 6), round(y, 6)] for x, y in shape.exterior.coords]
    return {
        "type": "Polygon",
        "coordinates": [coords],
    }


def to_geojson_geometry(geom) -> dict[str, Any]:
    """Convert any PostGIS or Shapely geometry (Polygon, MultiPolygon, Point) into GeoJSON."""
    from shapely.geometry import mapping
    shape = to_shape(geom) if hasattr(geom, "data") else geom
    return mapping(shape)

