"""GeoJSON Pydantic schemas (RFC 7946 compliant).

Requirement 14: Coordinate order is strictly [longitude, latitude].
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class GeoJSONGeometryPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(..., description="[longitude, latitude]")


class GeoJSONGeometryPolygon(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]] = Field(..., description="Linear rings of [longitude, latitude]")


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str | None = None
    geometry: dict[str, Any]
    properties: dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeature]
