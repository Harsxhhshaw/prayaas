"""Data Sources telemetry and pipeline registry endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import data_source_to_dict
from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceListResponse, FreshnessReportResponse
from app.services.ingestion.registry import SourceRegistryService

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.get("", response_model=DataSourceListResponse)
def list_data_sources(
    status: str | None = Query(None),
    type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List all registered external geospatial feeds and sensor streams."""
    q = db.query(DataSource)
    if status:
        q = q.filter(DataSource.status == status)
    if type:
        q = q.filter(DataSource.type == type)
    rows = q.order_by(DataSource.name).all()
    items = [data_source_to_dict(ds) for ds in rows]
    return {"items": items, "total": len(items)}


@router.get("/freshness", response_model=FreshnessReportResponse)
def get_sources_freshness(db: Session = Depends(get_db)):
    """Evaluate and return real-time data freshness across all registered sources."""
    service = SourceRegistryService(db)
    return service.get_freshness_report()


@router.get("/evidence-layers")
def list_evidence_layers(db: Session = Depends(get_db)):
    """List derived terrain, proximity, and geological evidence layers with provenance."""
    from app.models.evidence import EvidenceLayer

    layers = db.query(EvidenceLayer).order_by(EvidenceLayer.name).all()
    items = [
        {
            "id": el.id,
            "name": el.name,
            "evidence_type": el.evidence_type,
            "source_id": el.source_id,
            "data_mode": el.data_mode,
            "representation_type": el.representation_type,
            "spatial_resolution": el.spatial_resolution,
            "derivation_method": el.derivation_method,
            "parent_layer_ids": el.parent_layer_ids or [],
            "quality_score": el.quality_score,
        }
        for el in layers
    ]
    return {"items": items, "total": len(items)}


@router.get("/hazard-models")
def list_hazard_models(db: Session = Depends(get_db)):
    """List scientific hazard models and their validation / calibration status."""
    from app.models.evidence import HazardModel

    models = db.query(HazardModel).order_by(HazardModel.name).all()
    items = [
        {
            "id": m.id,
            "name": m.name,
            "hazard_type": m.hazard_type,
            "model_type": m.model_type,
            "version": m.version,
            "status": m.status,
            "config": m.config,
        }
        for m in models
    ]
    return {"items": items, "total": len(items)}
