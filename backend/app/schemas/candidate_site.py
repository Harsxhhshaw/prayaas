"""Pydantic v2 schemas for Candidate Relocation Site."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import GeoPointResponse


class CandidateSiteResponse(BaseModel):
    """Read-only candidate site schema matching the frontend type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    district: str
    state: str
    position: GeoPointResponse
    bounds: list[GeoPointResponse]
    suitabilityScore: int
    carryingCapacity: int
    currentUtilization: float
    areaHectares: float
    elevation: float
    distanceFromHazard: float
    roadAccess: bool
    waterAccess: bool
    electricityAccess: bool
    landUseType: str
    ownership: str
    verificationStatus: str
    assignedHabitations: list[str]


class CandidateSiteListResponse(BaseModel):
    items: list[CandidateSiteResponse]
    total: int
