"""Infrastructure Assets endpoints with GeoJSON and bounding-box spatial filtering."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import infrastructure_to_dict, infrastructure_to_geojson_feature
from app.models.infrastructure import InfrastructureAsset
from app.schemas.geojson import GeoJSONFeatureCollection
from app.schemas.infrastructure import InfrastructurePointListResponse
from app.spatial import apply_bbox_filter, parse_bbox

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


@router.get("", response_model=InfrastructurePointListResponse)
def list_infrastructure(
    type: str | None = Query(None),
    status: str | None = Query(None),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """List infrastructure assets with optional type, status, and bbox filters."""
    q = db.query(InfrastructureAsset)
    if type:
        q = q.filter(InfrastructureAsset.type == type)
    if status:
        q = q.filter(InfrastructureAsset.status == status)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, InfrastructureAsset.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    rows = q.order_by(InfrastructureAsset.name).all()
    items = [infrastructure_to_dict(ip) for ip in rows]
    return {"items": items, "total": len(items)}


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
def list_infrastructure_geojson(
    type: str | None = Query(None),
    status: str | None = Query(None),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """Map-friendly GeoJSON Point FeatureCollection (RFC 7946, coordinates: [lng, lat])."""
    q = db.query(InfrastructureAsset)
    if type:
        q = q.filter(InfrastructureAsset.type == type)
    if status:
        q = q.filter(InfrastructureAsset.status == status)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, InfrastructureAsset.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    rows = q.all()
    features = [infrastructure_to_geojson_feature(ip) for ip in rows]
    return {"type": "FeatureCollection", "features": features}
