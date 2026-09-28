"""Red Zones endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import red_zone_to_dict
from app.models.red_zone import RedZone
from app.schemas.red_zone import RedZoneListResponse, RedZoneResponse

router = APIRouter(prefix="/red-zones", tags=["red-zones"])


@router.get("", response_model=RedZoneListResponse)
def list_red_zones(db: Session = Depends(get_db)):
    rows = db.query(RedZone).order_by(RedZone.composit_risk_score.desc()).all()
    items = [red_zone_to_dict(rz) for rz in rows]
    return {"items": items, "total": len(items)}


@router.get("/{zone_id}", response_model=RedZoneResponse)
def get_red_zone(zone_id: str, db: Session = Depends(get_db)):
    rz = db.query(RedZone).filter(RedZone.id == zone_id).first()
    if not rz:
        raise HTTPException(status_code=404, detail="Red Zone not found")
    return red_zone_to_dict(rz)
