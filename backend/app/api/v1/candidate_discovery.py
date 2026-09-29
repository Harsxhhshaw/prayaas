"""API endpoints for Automated GIS Candidate Relocation Discovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import (
    candidate_discovery_run_to_dict,
    candidate_parcel_to_dict,
    candidate_parcel_to_geojson_feature,
)
from app.models.candidate_discovery import CandidateDiscoveryRun, CandidateParcel
from app.schemas.candidate_discovery import (
    CandidateDiscoveryRunRequest,
    CandidateDiscoveryRunResponse,
    CandidateParcelListResponse,
    CandidateParcelResponse,
    DiscoveryExecutionResponse,
)
from app.schemas.geojson import GeoJSONFeatureCollection
from app.services.candidates.engine import CandidateDiscoveryEngine
from app.spatial import apply_bbox_filter, parse_bbox

router = APIRouter(tags=["candidate-discovery"])


# ── 1. Execution Endpoint ──

@router.post(
    "/analysis/candidates/habitations/{habitation_id}",
    response_model=DiscoveryExecutionResponse,
)
def run_candidate_discovery(
    habitation_id: str,
    request: CandidateDiscoveryRunRequest | None = None,
    db: Session = Depends(get_db),
):
    """Executes the automated GIS candidate discovery workflow for an origin habitation."""
    engine = CandidateDiscoveryEngine(db)
    try:
        search_radius = request.search_radius_km if request else None
        min_area = request.min_parcel_area_hectares if request else None
        max_slope = request.max_slope_degrees if request else None

        res = engine.discover_candidates_for_habitation(
            habitation_id=habitation_id,
            search_radius_km=search_radius,
            min_parcel_area_ha=min_area,
            max_slope_deg=max_slope,
        )
        return res
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Discovery engine error: {str(exc)}")


# ── 2. Discovery Runs Query Endpoints ──

@router.get(
    "/habitations/{habitation_id}/candidate-discovery-runs",
    response_model=list[CandidateDiscoveryRunResponse],
)
def list_habitation_discovery_runs(habitation_id: str, db: Session = Depends(get_db)):
    """Lists past candidate discovery analysis runs for a given habitation."""
    runs = (
        db.query(CandidateDiscoveryRun)
        .filter(CandidateDiscoveryRun.origin_habitation_id == habitation_id)
        .order_by(CandidateDiscoveryRun.created_at.desc())
        .all()
    )
    return [candidate_discovery_run_to_dict(r) for r in runs]


@router.get(
    "/candidate-discovery-runs/{run_id}",
    response_model=CandidateDiscoveryRunResponse,
)
def get_candidate_discovery_run(run_id: str, db: Session = Depends(get_db)):
    """Fetches details of a specific candidate discovery run."""
    run = db.query(CandidateDiscoveryRun).filter(CandidateDiscoveryRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Discovery run '{run_id}' not found.")
    return candidate_discovery_run_to_dict(run)


# ── 3. Candidate Parcels Query Endpoints ──

@router.get("/candidate-parcels", response_model=CandidateParcelListResponse)
def list_candidate_parcels(
    habitation_id: str | None = Query(None, description="Filter by origin habitation ID"),
    run_id: str | None = Query(None, description="Filter by discovery run ID"),
    status: str | None = Query(None, description="Filter by parcel status (SHORTLISTED, PRELIMINARY, etc.)"),
    min_suitability: float | None = Query(None, ge=0, le=100),
    min_confidence: float | None = Query(None, ge=0, le=100),
    min_robustness: float | None = Query(None, ge=0, le=100),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """Lists discovered candidate parcels with multi-attribute filtering."""
    q = db.query(CandidateParcel)

    if habitation_id:
        q = q.filter(CandidateParcel.origin_habitation_id == habitation_id)
    if run_id:
        q = q.filter(CandidateParcel.discovery_run_id == run_id)
    if status:
        q = q.filter(CandidateParcel.status == status)
    if min_suitability is not None:
        q = q.filter(CandidateParcel.suitability_score >= min_suitability)
    if min_confidence is not None:
        q = q.filter(CandidateParcel.confidence_score >= min_confidence)
    if min_robustness is not None:
        q = q.filter(CandidateParcel.robustness_score >= min_robustness)

    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, CandidateParcel.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    parcels = q.order_by(CandidateParcel.suitability_score.desc()).all()
    items = [candidate_parcel_to_dict(p) for p in parcels]
    return {"items": items, "total": len(items)}


@router.get("/candidate-parcels/geojson", response_model=GeoJSONFeatureCollection)
def list_candidate_parcels_geojson(
    habitation_id: str | None = Query(None),
    run_id: str | None = Query(None),
    status: str | None = Query(None),
    min_suitability: float | None = Query(None, ge=0, le=100),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """Map-friendly GeoJSON FeatureCollection of candidate parcels (MultiPolygons)."""
    q = db.query(CandidateParcel)

    if habitation_id:
        q = q.filter(CandidateParcel.origin_habitation_id == habitation_id)
    if run_id:
        q = q.filter(CandidateParcel.discovery_run_id == run_id)
    if status:
        q = q.filter(CandidateParcel.status == status)
    if min_suitability is not None:
        q = q.filter(CandidateParcel.suitability_score >= min_suitability)

    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, CandidateParcel.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    parcels = q.order_by(CandidateParcel.suitability_score.desc()).all()
    features = [candidate_parcel_to_geojson_feature(p) for p in parcels]
    return {"type": "FeatureCollection", "features": features}


@router.get("/candidate-parcels/{parcel_id}", response_model=CandidateParcelResponse)
def get_candidate_parcel(parcel_id: str, db: Session = Depends(get_db)):
    """Fetches full dossier and criteria breakdown for a single candidate parcel."""
    parcel = db.query(CandidateParcel).filter(CandidateParcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Candidate parcel '{parcel_id}' not found.")
    return candidate_parcel_to_dict(parcel)
