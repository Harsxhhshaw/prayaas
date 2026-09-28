"""Pydantic v2 schemas for Habitation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import GeoPointResponse, HazardScoreResponse, RiskHistoryEntryResponse


class HabitationResponse(BaseModel):
    """Read-only habitation schema matching the frontend Habitation type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    district: str
    state: str
    position: GeoPointResponse
    riskScore: int
    riskCategory: str
    urgency: str
    population: int
    households: int
    confidence: int
    hazardScores: list[HazardScoreResponse]
    vulnerabilityScore: int
    riskHistory: list[RiskHistoryEntryResponse]
    elevation: float
    nearestRoad: float
    nearestHospital: float
    nearestSchool: float
    lastAssessed: str | None
    verificationStatus: str


class HabitationListResponse(BaseModel):
    items: list[HabitationResponse]
    total: int
