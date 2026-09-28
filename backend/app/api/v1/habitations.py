"""Habitations CRUD, GeoJSON, Risk, and Relocation assessment endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import (
    habitation_to_dict,
    habitation_to_geojson_feature,
    relocation_assessment_to_dict,
    risk_assessment_to_dict,
)
from app.models.habitation import Habitation
from app.models.relocation import RelocationAssessment
from app.models.risk import RiskAssessment
from app.schemas.geojson import GeoJSONFeatureCollection
from app.schemas.habitation import HabitationListResponse, HabitationResponse
from app.schemas.relocation import (
    RelocationAssessmentHistoryItem,
    RelocationAssessmentHistoryResponse,
    RelocationAssessmentResponse,
)
from app.schemas.risk import (
    RiskAssessmentExplanationResponse,
    RiskAssessmentHistoryItem,
    RiskAssessmentHistoryResponse,
    RiskAssessmentResponse,
)
from app.services.relocation.engine import RelocationEngine
from app.services.risk.engine import RiskEngine
from app.services.risk.explanations import generate_risk_explanation
from app.spatial import apply_bbox_filter, parse_bbox

router = APIRouter(prefix="/habitations", tags=["habitations"])


@router.get("", response_model=HabitationListResponse)
def list_habitations(
    district: str | None = Query(None),
    state: str | None = Query(None),
    risk_category: str | None = Query(None, alias="riskCategory"),
    urgency: str | None = Query(None),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """List all habitations with optional administrative, risk, and bbox spatial filters."""
    q = db.query(Habitation)
    if district:
        q = q.filter(Habitation.district == district)
    if state:
        q = q.filter(Habitation.state == state)
    if risk_category:
        q = q.filter(Habitation.risk_category == risk_category)
    if urgency:
        q = q.filter(Habitation.urgency == urgency)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, Habitation.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    q = q.order_by(Habitation.risk_score.desc())
    rows = q.all()
    items = [habitation_to_dict(h) for h in rows]
    return {"items": items, "total": len(items)}


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
def list_habitations_geojson(
    district: str | None = Query(None),
    risk_category: str | None = Query(None, alias="riskCategory"),
    urgency: str | None = Query(None),
    bbox: str | None = Query(None, description="Bounding box as minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    """Map-friendly GeoJSON FeatureCollection endpoint (RFC 7946, coordinates: [lng, lat])."""
    q = db.query(Habitation)
    if district:
        q = q.filter(Habitation.district == district)
    if risk_category:
        q = q.filter(Habitation.risk_category == risk_category)
    if urgency:
        q = q.filter(Habitation.urgency == urgency)
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = parse_bbox(bbox)
            q = apply_bbox_filter(q, Habitation.geom, min_lng, min_lat, max_lng, max_lat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    rows = q.order_by(Habitation.risk_score.desc()).all()
    features = [habitation_to_geojson_feature(h) for h in rows]
    return {"type": "FeatureCollection", "features": features}


@router.get("/{habitation_id}", response_model=HabitationResponse)
def get_habitation(habitation_id: str, db: Session = Depends(get_db)):
    """Get a single habitation by ID."""
    h = db.query(Habitation).filter(Habitation.id == habitation_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Habitation not found")
    return habitation_to_dict(h)


# ── Risk Assessment Endpoints ──

@router.get("/{habitation_id}/risk", response_model=RiskAssessmentResponse)
def get_habitation_risk(habitation_id: str, db: Session = Depends(get_db)):
    """Get latest multi-hazard risk assessment for a habitation."""
    ra = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.habitation_id == habitation_id)
        .order_by(RiskAssessment.calculated_at.desc())
        .first()
    )
    if not ra:
        # Run assessment on-demand
        try:
            engine = RiskEngine(db)
            ra = engine.assess_habitation(habitation_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
    return risk_assessment_to_dict(ra)


@router.get("/{habitation_id}/risk/history", response_model=RiskAssessmentHistoryResponse)
def get_habitation_risk_history(habitation_id: str, db: Session = Depends(get_db)):
    """Get temporal history of risk calculations for a habitation."""
    hab = db.query(Habitation).filter(Habitation.id == habitation_id).first()
    if not hab:
        raise HTTPException(status_code=404, detail="Habitation not found")

    rows = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.habitation_id == habitation_id)
        .order_by(RiskAssessment.calculated_at.desc())
        .all()
    )
    items = [
        RiskAssessmentHistoryItem(
            id=r.id,
            composite_risk_score=r.composite_risk_score,
            risk_classification=r.risk_classification,
            confidence_score=r.confidence_score,
            hazard_score=r.hazard_score,
            vulnerability_score=r.vulnerability_score,
            calculated_at=r.calculated_at.isoformat(),
        )
        for r in rows
    ]
    return RiskAssessmentHistoryResponse(habitation_id=habitation_id, history=items)


@router.get("/{habitation_id}/risk/explanation", response_model=RiskAssessmentExplanationResponse)
def get_habitation_risk_explanation(habitation_id: str, db: Session = Depends(get_db)):
    """Get transparent, auditable formula and factor explanation for risk score."""
    try:
        return generate_risk_explanation(db, habitation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Relocation Assessment Endpoints ──

@router.get("/{habitation_id}/relocation", response_model=RelocationAssessmentResponse)
def get_habitation_relocation(habitation_id: str, db: Session = Depends(get_db)):
    """Get latest relocation need, urgency, and readiness assessment for a habitation."""
    ra = (
        db.query(RelocationAssessment)
        .filter(RelocationAssessment.habitation_id == habitation_id)
        .order_by(RelocationAssessment.calculated_at.desc())
        .first()
    )
    if not ra:
        try:
            engine = RelocationEngine(db)
            ra = engine.assess_habitation(habitation_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
    return relocation_assessment_to_dict(ra)


@router.get("/{habitation_id}/relocation/history", response_model=RelocationAssessmentHistoryResponse)
def get_habitation_relocation_history(habitation_id: str, db: Session = Depends(get_db)):
    """Get historical relocation assessments for a habitation."""
    hab = db.query(Habitation).filter(Habitation.id == habitation_id).first()
    if not hab:
        raise HTTPException(status_code=404, detail="Habitation not found")

    rows = (
        db.query(RelocationAssessment)
        .filter(RelocationAssessment.habitation_id == habitation_id)
        .order_by(RelocationAssessment.calculated_at.desc())
        .all()
    )
    items = [
        RelocationAssessmentHistoryItem(
            id=r.id,
            need_score=r.need_score,
            urgency=r.urgency,
            readiness_score=r.readiness_score,
            readiness_level=r.readiness_level,
            calculated_at=r.calculated_at.isoformat(),
        )
        for r in rows
    ]
    return RelocationAssessmentHistoryResponse(habitation_id=habitation_id, history=items)
