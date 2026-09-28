"""Pydantic v2 schemas for Relocation Priority."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RelocationPriorityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    habitationId: str
    habitationName: str
    urgency: str
    riskScore: int
    population: int
    district: str
    assignedSiteId: str | None = None
    assignedSiteName: str | None = None
    estimatedCost: float | None = None
    timelineMonths: int | None = None
    needScore: float | None = None
    readinessScore: float | None = None
    readinessLevel: str | None = None
    matrixPosition: str | None = None


class RelocationPriorityListResponse(BaseModel):
    items: list[RelocationPriorityResponse]
    total: int
