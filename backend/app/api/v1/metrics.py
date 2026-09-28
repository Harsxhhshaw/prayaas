"""Aggregate metrics endpoint for the Command Centre strip."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.habitation import Habitation
from app.models.red_zone import RedZone
from app.models.candidate_site import CandidateSite
from app.models.relocation_priority import RelocationPriority
from app.schemas.common import MetricsSummaryResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummaryResponse)
def get_metrics_summary(db: Session = Depends(get_db)):
    """Compute real-time aggregate KPIs from the database."""
    total_hab = db.query(func.count(Habitation.id)).scalar() or 0
    critical_hab = db.query(func.count(Habitation.id)).filter(Habitation.risk_category == "CRITICAL").scalar() or 0
    high_hab = db.query(func.count(Habitation.id)).filter(Habitation.risk_category == "HIGH").scalar() or 0
    pop_at_risk = (
        db.query(func.coalesce(func.sum(Habitation.population), 0))
        .filter(Habitation.risk_category.in_(["CRITICAL", "HIGH"]))
        .scalar()
    )
    active_red = db.query(func.count(RedZone.id)).scalar() or 0
    sites = db.query(func.count(CandidateSite.id)).scalar() or 0
    pending_reloc = (
        db.query(func.count(RelocationPriority.id))
        .filter(RelocationPriority.assigned_site_id.is_(None))
        .scalar() or 0
    )
    field_pending = (
        db.query(func.count(Habitation.id))
        .filter(Habitation.verification_status == "PENDING")
        .scalar() or 0
    )

    return MetricsSummaryResponse(
        total_habitations=total_hab,
        critical_habitations=critical_hab,
        high_habitations=high_hab,
        total_population_at_risk=pop_at_risk,
        active_red_zones=active_red,
        candidate_sites=sites,
        pending_relocations=pending_reloc,
        field_verifications_pending=field_pending,
    )
