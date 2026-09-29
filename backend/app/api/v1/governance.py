"""API endpoints for Task 10 Governance, Field Evidence, Land Status, Document AI, and Decision Dossiers."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.governance import (
    AnalyticalOverrideCreate,
    AnalyticalOverrideResponse,
    AuditLogItemResponse,
    ConsultationCreate,
    ConsultationResponse,
    DataHonestyAuditResponse,
    DecisionDossierResponse,
    DocumentConfirmRequest,
    DocumentExtractionRequest,
    DocumentExtractionResponse,
    FieldObservationCreate,
    FieldObservationResponse,
    FieldObservationVerifyRequest,
    GovernanceReviewCreate,
    GovernanceReviewResponse,
    LandStatusCreate,
    LandStatusResponse,
)
from app.services.demo_freeze.engine import DemoFreezeEngine
from app.services.document_ai.engine import DocumentAIEngine
from app.services.dossier.engine import DecisionDossierEngine
from app.services.governance.engine import GovernanceEngine

router = APIRouter(prefix="/governance", tags=["governance"])


# ── Field Observations ──

@router.post("/observations", response_model=FieldObservationResponse)
def create_field_observation(
    req: FieldObservationCreate,
    db: Session = Depends(get_db),
):
    """Records ground-level field observation. Always starts at FIELD_OBSERVED level."""
    engine = GovernanceEngine(db)
    obs = engine.record_field_observation(req)
    return obs


@router.get("/observations", response_model=list[FieldObservationResponse])
def get_field_observations(
    entity_type: str = Query(..., description="HABITATION, HAZARD_ZONE, CANDIDATE_PARCEL, or CANDIDATE_SITE"),
    entity_id: str = Query(..., description="Target ID of entity"),
    db: Session = Depends(get_db),
):
    """Retrieves all field observations for an entity."""
    engine = GovernanceEngine(db)
    return engine.get_observations_for_entity(entity_type, entity_id)


@router.post("/observations/{observation_id}/verify", response_model=FieldObservationResponse)
def verify_field_observation(
    observation_id: str,
    req: FieldObservationVerifyRequest,
    db: Session = Depends(get_db),
):
    """Upgrades a field observation to TECHNICALLY_VERIFIED or AUTHORITY_REVIEWED."""
    engine = GovernanceEngine(db)
    try:
        return engine.verify_field_observation(observation_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Land & Legal Status ──

@router.post("/land-status", response_model=LandStatusResponse)
def record_land_status(
    req: LandStatusCreate,
    db: Session = Depends(get_db),
):
    """Records or updates statutory cadastral, forest, or tenure verification status."""
    engine = GovernanceEngine(db)
    return engine.record_land_status(req)


@router.get("/land-status", response_model=list[LandStatusResponse])
def get_land_status(
    parcel_candidate_id: str = Query(..., description="Candidate parcel or site ID"),
    db: Session = Depends(get_db),
):
    """Retrieves land tenure and restriction records for a parcel."""
    engine = GovernanceEngine(db)
    return engine.get_land_status_for_parcel(parcel_candidate_id)


# ── Community Consultation ──

@router.post("/consultations", response_model=ConsultationResponse)
def record_consultation(
    req: ConsultationCreate,
    db: Session = Depends(get_db),
):
    """Records community consultation or Gram Sabha hearing.
    Strictly updates governance and readiness info, NEVER alters geological hazard risk!
    """
    engine = GovernanceEngine(db)
    return engine.record_consultation(req)


@router.get("/consultations", response_model=list[ConsultationResponse])
def get_consultations(
    habitation_id: str = Query(..., description="Origin Habitation ID"),
    db: Session = Depends(get_db),
):
    """Retrieves recorded public engagement hearings for a habitation."""
    engine = GovernanceEngine(db)
    return engine.get_consultations_for_habitation(habitation_id)


# ── Governance Review Workflow ──

@router.post("/reviews", response_model=GovernanceReviewResponse)
def record_governance_review(
    req: GovernanceReviewCreate,
    db: Session = Depends(get_db),
):
    """Advances an entity through institutional review stages."""
    engine = GovernanceEngine(db)
    return engine.record_governance_review(req)


@router.get("/reviews", response_model=list[GovernanceReviewResponse])
def get_governance_reviews(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Retrieves governance review history for an entity."""
    engine = GovernanceEngine(db)
    return engine.get_governance_reviews(entity_type, entity_id)


# ── Human Analytical Overrides ──

@router.post("/overrides", response_model=AnalyticalOverrideResponse)
def apply_analytical_override(
    req: AnalyticalOverrideCreate,
    db: Session = Depends(get_db),
):
    """Applies an auditable analytical override. Preserves original analytical values."""
    engine = GovernanceEngine(db)
    return engine.apply_analytical_override(req)


@router.get("/overrides", response_model=list[AnalyticalOverrideResponse])
def get_analytical_overrides(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Retrieves applied analytical overrides."""
    engine = GovernanceEngine(db)
    return engine.get_overrides_for_entity(entity_type, entity_id)


# ── Audit Logs ──

@router.get("/audit-logs", response_model=list[AuditLogItemResponse])
def get_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Retrieves immutable audit trail entries."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return logs


# ── Optional Document AI ──

@router.post("/documents/extract", response_model=DocumentExtractionResponse)
def extract_document_evidence(
    req: DocumentExtractionRequest,
    db: Session = Depends(get_db),
):
    """Extracts proposed structured evidence from disaster reports.
    Degrades gracefully if AI is disabled or unconfigured without failing system operations.
    """
    engine = DocumentAIEngine(db)
    return engine.extract_document_evidence(req)


@router.post("/documents/{document_id}/confirm")
def confirm_document_extraction(
    document_id: str,
    req: DocumentConfirmRequest,
    db: Session = Depends(get_db),
):
    """Human expert confirms, edits, or rejects proposed document evidence."""
    engine = DocumentAIEngine(db)
    try:
        return engine.review_and_confirm_extraction(document_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Decision Dossier ──

@router.get("/habitations/{habitation_id}/dossier", response_model=DecisionDossierResponse)
def get_decision_dossier(
    habitation_id: str,
    db: Session = Depends(get_db),
):
    """Compiles the complete 12-section Decision Support Dossier for a habitation."""
    engine = DecisionDossierEngine(db)
    try:
        return engine.generate_dossier(habitation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/habitations/{habitation_id}/dossier/html", response_class=HTMLResponse)
def get_decision_dossier_html(
    habitation_id: str,
    db: Session = Depends(get_db),
):
    """Generates standalone printable HTML decision dossier for PDF export."""
    engine = DecisionDossierEngine(db)
    try:
        return engine.generate_html_report(habitation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Frozen Demo Snapshot & Data Honesty Audit ──

@router.get("/demo-snapshot/raini")
def get_raini_demo_snapshot(
    db: Session = Depends(get_db),
):
    """Retrieves or creates the stable, frozen demo snapshot for Raini HAB-002."""
    engine = DemoFreezeEngine(db)
    return engine.get_or_create_raini_demo_snapshot()


@router.get("/data-honesty-audit", response_model=DataHonestyAuditResponse)
def get_data_honesty_audit(
    db: Session = Depends(get_db),
):
    """Performs a comprehensive database audit classifying records by data mode: PUBLIC, LIVE, MODELED, DEMO, FIELD."""
    engine = DemoFreezeEngine(db)
    return engine.perform_data_honesty_audit()
