"""Candidate Relocation Sites endpoints with GeoJSON and bounding-box spatial filtering."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import candidate_site_to_dict, candidate_site_to_geojson_feature
from app.models.candidate_site import CandidateSite
from app.schemas.candidate_site import CandidateSiteListResponse, CandidateSiteResponse
from app.schemas.geojson import GeoJSONFeatureCollection
from app.spatial import apply_bbox_filter, parse_bbox

router = APIRouter(prefix="/candidate-sites", tags=["candidate-sites"])


@router.get("", response_model=CandidateSiteListResponse)
def list_candidate_sites(
    district: str | None = Query(None),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """List candidate relocation sites, optionally filtered by district or bbox."""
    q = db.query(CandidateSite)
    if district:
        q = q.filter(CandidateSite.district == district)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, CandidateSite.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    q = q.order_by(CandidateSite.suitability_score.desc())
    rows = q.all()
    items = [candidate_site_to_dict(cs) for cs in rows]
    return {"items": items, "total": len(items)}


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
def list_candidate_sites_geojson(
    district: str | None = Query(None),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """Map-friendly GeoJSON FeatureCollection of candidate sites."""
    q = db.query(CandidateSite)
    if district:
        q = q.filter(CandidateSite.district == district)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, CandidateSite.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    rows = q.order_by(CandidateSite.suitability_score.desc()).all()
    features = [candidate_site_to_geojson_feature(cs) for cs in rows]
    return {"type": "FeatureCollection", "features": features}


@router.get("/{site_id}", response_model=CandidateSiteResponse)
def get_candidate_site(site_id: str, db: Session = Depends(get_db)):
    cs = db.query(CandidateSite).filter(CandidateSite.id == site_id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="Candidate site not found")
    return candidate_site_to_dict(cs)
