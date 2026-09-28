"""Pydantic v2 schemas for DataSource."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    provider: str
    type: str
    status: str
    lastSync: str | None = None
    recordsCount: int = 0
    latencyMs: int = 0
    dataMode: str = "DEMO"
    verifiedUrl: str | None = None
    license: str | None = None
    sourceDate: str | None = None
    lastIngestedAt: str | None = None
    lastSuccessfulIngestion: str | None = None
    spatialResolution: str | None = None
    temporalResolution: str | None = None
    expectedRefreshSeconds: int | None = None
    freshness: str = "UNKNOWN"


class DataSourceFreshnessItem(BaseModel):
    id: str
    name: str
    provider: str
    type: str
    freshness: str
    lastSuccessfulIngestion: str | None = None
    expectedRefreshSeconds: int | None = None
    dataMode: str
    isStale: bool


class FreshnessReportResponse(BaseModel):
    items: list[DataSourceFreshnessItem]
    total: int
    stale_count: int


class DataSourceListResponse(BaseModel):
    items: list[DataSourceResponse]
    total: int
