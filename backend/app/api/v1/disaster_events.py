"""Disaster Events catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import disaster_event_to_dict
from app.models.disaster_event import DisasterEvent
from app.schemas.disaster_event import DisasterEventListResponse

router = APIRouter(prefix="/disaster-events", tags=["disaster-events"])


@router.get("", response_model=DisasterEventListResponse)
def list_disaster_events(
    district: str | None = Query(None),
    hazard_type: str | None = Query(None, alias="hazardType"),
    db: Session = Depends(get_db),
):
    """List historical and real-time disaster event records."""
    q = db.query(DisasterEvent)
    if district:
        q = q.filter(DisasterEvent.district == district)
    if hazard_type:
        q = q.filter(DisasterEvent.hazard_type == hazard_type)
    rows = q.order_by(DisasterEvent.event_date.desc()).all()
    items = [disaster_event_to_dict(de) for de in rows]
    return {"items": items, "total": len(items)}
