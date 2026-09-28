"""Pydantic v2 schemas for Ingestion pipelines and observations."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str | None = None
    ingestion_type: str
    started_at: str
    finished_at: str | None = None
    status: str
    records_received: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_rejected: int = 0
    error_message: str | None = None
    data_mode: str = "DEMO"
    ingestion_metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionRunListResponse(BaseModel):
    items: list[IngestionRunResponse]
    total: int


class EnvironmentalObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    habitation_id: str | None = None
    district_id: str | None = None
    source_id: str | None = None
    observation_type: str
    value: float
    unit: str
    observed_at: str
    fetched_at: str
    data_mode: str = "LIVE"
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class EnvironmentalObservationListResponse(BaseModel):
    items: list[EnvironmentalObservationResponse]
    total: int


class RasterDatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    dataset_type: str
    source_id: str | None = None
    file_path: str | None = None
    crs: str
    resolution_x: float | None = None
    resolution_y: float | None = None
    bounds: dict[str, Any] | None = None
    nodata: float | None = None
    data_mode: str = "DEMO"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class OSMIngestRequest(BaseModel):
    bbox: list[float] = Field(
        default=[30.2, 79.0, 30.6, 79.7],
        description="Bounding box [min_lat, min_lon, max_lat, max_lon]",
    )
    amenity_types: list[str] = Field(
        default=["hospital", "clinic", "school", "helipad", "shelter"],
        description="OSM tags to filter",
    )


class WeatherIngestRequest(BaseModel):
    habitation_ids: list[str] | None = Field(
        default=None,
        description="Optional list of specific habitation IDs. If None, all habitations in Chamoli are queried.",
    )
    force_refresh: bool = Field(
        default=False,
        description="Bypass 15-minute TTL cache if true",
    )


class GeoJSONImportRequest(BaseModel):
    source_name: str
    entity_type: str = Field(description="HAZARD_ZONE | INFRASTRUCTURE | HABITATION")
    geojson_data: dict[str, Any]
    data_mode: str = "PUBLIC"


class CSVImportRequest(BaseModel):
    source_name: str
    entity_type: str = Field(description="VULNERABILITY | INFRASTRUCTURE | OBSERVATION")
    csv_text: str
    data_mode: str = "PUBLIC"
