"""Pydantic v2 schemas for DisasterEvent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from app.schemas.common import GeoPointResponse


class DisasterEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    hazardType: str
    severity: str
    eventDate: str
    district: str
    position: GeoPointResponse | None = None
    fatalities: int = 0
    displacedPersons: int = 0
    description: str = ""
    dataMode: str = "DEMO"


class DisasterEventListResponse(BaseModel):
    items: list[DisasterEventResponse]
    total: int
