"""Pydantic v2 schemas for State and District."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DistrictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    state_id: str
    state_name: str | None = None
    headquarters: str | None = None
    data_mode: str = "DEMO"


class DistrictListResponse(BaseModel):
    items: list[DistrictResponse]
    total: int


class StateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    data_mode: str = "DEMO"
    districts: list[DistrictResponse] = []


class StateListResponse(BaseModel):
    items: list[StateResponse]
    total: int
