"""Health and database readiness check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "prayaas-api"}


@router.get("/health/db")
@router.get("/health/database")
def health_database(db: Session = Depends(get_db)):
    """Check database connectivity and PostGIS availability."""
    try:
        row = db.execute(text("SELECT PostGIS_Version()")).scalar()
        return {"status": "ok", "database": "postgresql+postgis", "postgis_version": row}
    except Exception as exc:
        return {"status": "error", "database": "unreachable", "detail": str(exc)}
