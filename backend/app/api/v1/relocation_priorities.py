"""Relocation Priorities endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import relocation_priority_to_dict
from app.models.relocation import RelocationAssessment
from app.models.relocation_priority import RelocationPriority
from app.schemas.relocation_priority import RelocationPriorityListResponse

router = APIRouter(prefix="/relocation-priorities", tags=["relocation-priorities"])


@router.get("", response_model=RelocationPriorityListResponse)
def list_relocation_priorities(
    urgency: str | None = Query(None),
    district: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List relocation priorities enriched with latest Need and Readiness assessments."""
    q = db.query(RelocationPriority)
    if urgency:
        q = q.filter(RelocationPriority.urgency == urgency)
    if district:
        q = q.filter(RelocationPriority.district == district)
    q = q.order_by(RelocationPriority.risk_score.desc())
    rows = q.all()

    # Pre-fetch latest relocation assessments for habitations
    habitation_ids = [rp.habitation_id for rp in rows]
    assessments = (
        db.query(RelocationAssessment)
        .filter(RelocationAssessment.habitation_id.in_(habitation_ids))
        .order_by(RelocationAssessment.calculated_at.desc())
        .all()
    )
    # Map latest by habitation_id
    latest_assessments: dict[str, RelocationAssessment] = {}
    for a in assessments:
        if a.habitation_id not in latest_assessments:
            latest_assessments[a.habitation_id] = a

    items = []
    for rp in rows:
        ass = latest_assessments.get(rp.habitation_id)
        d = relocation_priority_to_dict(rp)
        if ass:
            d["needScore"] = ass.need_score
            d["readinessScore"] = ass.readiness_score
            d["readinessLevel"] = ass.readiness_level
            # Update urgency from latest assessment if newer
            d["urgency"] = ass.urgency
        items.append(d)

    return {"items": items, "total": len(items)}
