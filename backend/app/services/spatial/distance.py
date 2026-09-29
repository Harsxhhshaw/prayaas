"""Geospatial distance helpers for hazard susceptibility evidence.

Provides metric distance calculations (road, drainage, tectonic fault)
backed by actual PostGIS features or evidence layers. Returns UNKNOWN
when the underlying evidence layer is absent. Never invents fake features.
"""

from __future__ import annotations

import math
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceLayer
from app.models.enums import AnalyticalStatus, EvidenceType
from app.models.infrastructure import InfrastructureAsset
from app.services.risk.semantics import AnalyticalValue


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 3)


def distance_to_road(
    db: Session,
    lat: float,
    lng: float,
    max_search_km: float = 50.0,
) -> AnalyticalValue[float]:
    """Calculates metric distance to the nearest road asset.

    Returns UNKNOWN if no road infrastructure assets exist in the database.
    """
    # Check for road junctions or road assets
    road_assets = (
        db.query(InfrastructureAsset)
        .filter(InfrastructureAsset.type.in_(["ROAD_JUNCTION", "BRIDGE"]))
        .all()
    )

    if not road_assets:
        return AnalyticalValue.unknown(reason="No road infrastructure evidence layer registered")

    from geoalchemy2.shape import to_shape
    min_dist = float("inf")
    for asset in road_assets:
        pt = to_shape(asset.geom)
        d = haversine_distance_km(lat, lng, pt.y, pt.x)
        if d < min_dist:
            min_dist = d

    if min_dist > max_search_km:
        return AnalyticalValue.from_value(round(max_search_km, 2), confidence=70.0)

    return AnalyticalValue.from_value(round(min_dist, 2), confidence=85.0)


def distance_to_drainage(
    db: Session,
    lat: float,
    lng: float,
) -> AnalyticalValue[float]:
    """Calculates metric distance to nearest river / drainage line.

    Strict scientific rule:
    Returns UNKNOWN if no genuine drainage/hydrology layer is registered.
    Never fabricates fake rivers to artificially fill scores.
    """
    layer = (
        db.query(EvidenceLayer)
        .filter(EvidenceLayer.evidence_type == EvidenceType.DRAINAGE_DISTANCE.value)
        .first()
    )

    if not layer:
        return AnalyticalValue.unknown(reason="Hydrological drainage network layer unavailable")

    # If layer exists with metadata or features, compute distance; otherwise unknown
    meta = layer.metadata_json or {}
    if "reference_features" in meta:
        features = meta["reference_features"]
        if features:
            min_dist = min(haversine_distance_km(lat, lng, f["lat"], f["lng"]) for f in features)
            return AnalyticalValue.from_value(round(min_dist, 2), confidence=layer.quality_score or 75.0)

    return AnalyticalValue.unknown(reason="Drainage network layer lacks vector geometries for distance calculation")


def distance_to_fault(
    db: Session,
    lat: float,
    lng: float,
) -> AnalyticalValue[float]:
    """Calculates metric distance to nearest tectonic fault (e.g., Main Central Thrust).

    Strict scientific rule:
    Returns UNKNOWN if tectonic fault evidence layer is unavailable.
    """
    layer = (
        db.query(EvidenceLayer)
        .filter(EvidenceLayer.evidence_type == EvidenceType.FAULT_DISTANCE.value)
        .first()
    )

    if not layer:
        return AnalyticalValue.unknown(reason="Seismotectonic fault map layer unavailable")

    meta = layer.metadata_json or {}
    if "fault_segments" in meta:
        segments = meta["fault_segments"]
        if segments:
            min_dist = min(haversine_distance_km(lat, lng, s["lat"], s["lng"]) for s in segments)
            return AnalyticalValue.from_value(round(min_dist, 2), confidence=layer.quality_score or 80.0)

    return AnalyticalValue.unknown(reason="Fault layer contains no geographic traces")


# Compatibility aliases
calculate_distance_to_road = distance_to_road
calculate_distance_to_drainage = distance_to_drainage
calculate_distance_to_fault = distance_to_fault
