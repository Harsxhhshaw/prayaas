"""Pydantic v2 schemas for Operational Alert."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OperationalAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    message: str
    type: str
    severity: str
    timestamp: str
    habitationId: str | None
    read: bool


class OperationalAlertListResponse(BaseModel):
    items: list[OperationalAlertResponse]
    total: int
