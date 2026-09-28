"""Pydantic v2 schemas for Infrastructure Point."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import GeoPointResponse


class InfrastructurePointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    position: GeoPointResponse
    status: str
    capacity: int | None


class InfrastructurePointListResponse(BaseModel):
    items: list[InfrastructurePointResponse]
    total: int
