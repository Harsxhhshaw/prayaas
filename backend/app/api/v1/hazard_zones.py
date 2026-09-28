"""Hazard Zones (Red Zones) endpoints with GeoJSON and bounding-box spatial filtering."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import hazard_zone_to_dict, hazard_zone_to_geojson_feature
from app.models.hazard_zone import HazardZone
from app.schemas.geojson import GeoJSONFeatureCollection
from app.schemas.red_zone import RedZoneListResponse, RedZoneResponse
from app.spatial import apply_bbox_filter, parse_bbox

router = APIRouter(tags=["hazard-zones"])


@router.get("/hazard-zones", response_model=RedZoneListResponse)
@router.get("/red-zones", response_model=RedZoneListResponse, include_in_schema=False)
def list_hazard_zones(
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """List all declared Hazard / Red Zones, optionally filtered by bounding box."""
    q = db.query(HazardZone)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, HazardZone.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    rows = q.order_by(HazardZone.composite_risk_score.desc()).all()
    items = [hazard_zone_to_dict(rz) for rz in rows]
    return {"items": items, "total": len(items)}


@router.get("/hazard-zones/geojson", response_model=GeoJSONFeatureCollection)
@router.get("/red-zones/geojson", response_model=GeoJSONFeatureCollection, include_in_schema=False)
def list_hazard_zones_geojson(
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """Map-friendly GeoJSON Polygon FeatureCollection (RFC 7946, coordinates: [lng, lat])."""
    q = db.query(HazardZone)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, HazardZone.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    rows = q.order_by(HazardZone.composite_risk_score.desc()).all()
    features = [hazard_zone_to_geojson_feature(rz) for rz in rows]
    return {"type": "FeatureCollection", "features": features}


@router.get("/hazard-zones/{zone_id}", response_model=RedZoneResponse)
@router.get("/red-zones/{zone_id}", response_model=RedZoneResponse, include_in_schema=False)
def get_hazard_zone(zone_id: str, db: Session = Depends(get_db)):
    rz = db.query(HazardZone).filter(HazardZone.id == zone_id).first()
    if not rz:
        raise HTTPException(status_code=404, detail="Hazard Zone not found")
    return hazard_zone_to_dict(rz)
