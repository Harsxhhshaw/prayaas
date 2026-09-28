"""Pydantic v2 schemas for Red Zone."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import GeoPointResponse


class RedZoneResponse(BaseModel):
    """Read-only red zone schema matching the frontend RedZone type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    bounds: list[GeoPointResponse]
    hazardTypes: list[str]
    compositRiskScore: int
    habitationCount: int
    populationAffected: int
    areaKmSq: float
    computedAreaSqKm: float | None = None
    sourceDeclaredAreaSqKm: float | None = None
    declaredDate: str | None = None
    lastUpdated: str | None = None
    dataMode: str = "DEMO"
    classification: str | None = None


class RedZoneListResponse(BaseModel):
    items: list[RedZoneResponse]
    total: int
