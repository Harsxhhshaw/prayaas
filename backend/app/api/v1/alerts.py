"""Operational Alerts endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import alert_to_dict
from app.models.operational_alert import OperationalAlert
from app.schemas.operational_alert import OperationalAlertListResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=OperationalAlertListResponse)
def list_alerts(
    severity: str | None = Query(None),
    type: str | None = Query(None, alias="alertType"),
    db: Session = Depends(get_db),
):
    q = db.query(OperationalAlert)
    if severity:
        q = q.filter(OperationalAlert.severity == severity)
    if type:
        q = q.filter(OperationalAlert.type == type)
    q = q.order_by(OperationalAlert.timestamp.desc())
    rows = q.all()
    items = [alert_to_dict(a) for a in rows]
    return {"items": items, "total": len(items)}
