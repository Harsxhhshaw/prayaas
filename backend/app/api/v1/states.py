"""States and Districts administrative API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.api.serializers import district_to_dict, state_to_dict
from app.models.administrative import District, State
from app.schemas.administrative import (
    DistrictListResponse,
    DistrictResponse,
    StateListResponse,
    StateResponse,
)

states_router = APIRouter(prefix="/states", tags=["administrative"])
districts_router = APIRouter(prefix="/districts", tags=["administrative"])


@states_router.get("", response_model=StateListResponse)
def list_states(db: Session = Depends(get_db)):
    """List all supported states with their districts."""
    states = db.query(State).options(joinedload(State.districts)).order_by(State.name).all()
    items = [state_to_dict(s) for s in states]
    return {"items": items, "total": len(items)}


@states_router.get("/{state_id}", response_model=StateResponse)
def get_state(state_id: str, db: Session = Depends(get_db)):
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state_to_dict(state)


@districts_router.get("", response_model=DistrictListResponse)
def list_districts(
    state: str | None = Query(None, description="Filter by state name or ID"),
    db: Session = Depends(get_db),
):
    """List all districts, optionally filtered by state."""
    q = db.query(District).options(joinedload(District.state))
    if state:
        q = q.join(State).filter((State.name == state) | (District.state_id == state))
    districts = q.order_by(District.name).all()
    items = [district_to_dict(d) for d in districts]
    return {"items": items, "total": len(items)}


@districts_router.get("/{district_id}", response_model=DistrictResponse)
def get_district(district_id: str, db: Session = Depends(get_db)):
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district_to_dict(district)
