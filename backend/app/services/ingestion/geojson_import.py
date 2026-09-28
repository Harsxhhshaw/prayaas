"""Spatial GeoJSON feature collection importer."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon, shape
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import DataMode
from app.models.habitation import Habitation
from app.models.hazard_zone import HazardZone
from app.models.infrastructure import InfrastructureAsset
from app.services.ingestion.base import BaseIngestionConnector, IngestionContext
from app.services.ingestion.registry import SourceRegistryService


class GeoJSONImporter(BaseIngestionConnector):
    """Parses and validates GeoJSON FeatureCollections into database tables."""

    def __init__(self, db: Session, source_name: str = "GeoJSON Import", source_id: str | None = None) -> None:
        if not source_id:
            registry = SourceRegistryService(db)
            source = registry.get_or_create_source(
                id=f"SRC-GEOJSON-{uuid4().hex[:8].upper()}",
                name=source_name,
                provider="Administrative Upload",
                type="FIELD_SURVEY",
                data_mode=DataMode.PUBLIC.value,
                expected_refresh_seconds=604800,
            )
            source_id = source.id
        super().__init__(db, ingestion_type="GEOJSON_IMPORT", source_id=source_id, data_mode=DataMode.PUBLIC.value)

    def import_features(
        self,
        geojson_data: dict[str, Any],
        entity_type: str,
        data_mode: str = DataMode.PUBLIC.value,
    ) -> IngestionContext:
        features = geojson_data.get("features", [])
        if not features and geojson_data.get("type") == "Feature":
            features = [geojson_data]

        with self.run_context() as ctx:
            ctx.set_metadata("entity_type", entity_type)
            ctx.set_metadata("feature_count", len(features))

            for feat in features:
                ctx.inc_received()
                geometry_dict = feat.get("geometry")
                props = feat.get("properties", {})

                if not geometry_dict:
                    ctx.inc_rejected()
                    continue

                try:
                    geom_obj = shape(geometry_dict)
                    if not geom_obj.is_valid:
                        geom_obj = geom_obj.buffer(0)
                except Exception:
                    ctx.inc_rejected()
                    continue

                if entity_type.upper() == "HAZARD_ZONE":
                    if geom_obj.geom_type not in ("Polygon", "MultiPolygon"):
                        ctx.inc_rejected()
                        continue

                    # If MultiPolygon, take largest or first polygon
                    if geom_obj.geom_type == "MultiPolygon":
                        poly = max(geom_obj.geoms, key=lambda p: p.area)
                    else:
                        poly = geom_obj

                    poly_geom = from_shape(poly, srid=4326)
                    name = props.get("name") or f"Hazard Zone {uuid4().hex[:6]}"
                    declared_area = float(props.get("area_km_sq", 0.0))

                    # PostGIS computed area in sq km
                    zone = HazardZone(
                        id=str(uuid4()),
                        name=name,
                        geom=poly_geom,
                        composite_risk_score=int(props.get("composite_risk_score", 65)),
                        hazard_types=props.get("hazard_types", ["LANDSLIDE"]),
                        habitation_count=0,
                        population_affected=int(props.get("population_affected", 0)),
                        area_km_sq=declared_area or 10.0,
                        source_declared_area_sq_km=declared_area,
                        declared_date=props.get("declared_date", "2026-01-01"),
                        data_mode=data_mode,
                    )
                    self.db.add(zone)
                    self.db.flush()

                    # Compute geodesic area with ST_Area
                    area_m2 = self.db.query(
                        func.ST_Area(func.ST_GeogFromWKB(zone.geom))
                    ).scalar()
                    if area_m2:
                        zone.computed_area_sq_km = round(area_m2 / 1_000_000.0, 3)

                    ctx.inc_inserted()

                elif entity_type.upper() == "INFRASTRUCTURE":
                    if geom_obj.geom_type != "Point":
                        ctx.inc_rejected()
                        continue
                    pt_geom = from_shape(geom_obj, srid=4326)
                    name = props.get("name") or "Infrastructure Asset"
                    asset_type = props.get("type", "HOSPITAL")

                    asset = InfrastructureAsset(
                        id=str(uuid4()),
                        name=name,
                        type=asset_type,
                        geom=pt_geom,
                        status=props.get("status", "OPERATIONAL"),
                        capacity=props.get("capacity"),
                        district=props.get("district", "Chamoli"),
                        data_mode=data_mode,
                    )
                    self.db.add(asset)
                    ctx.inc_inserted()

                elif entity_type.upper() == "HABITATION":
                    if geom_obj.geom_type != "Point":
                        ctx.inc_rejected()
                        continue
                    pt_geom = from_shape(geom_obj, srid=4326)
                    name = props.get("name") or "Habitation Settlement"

                    hab = Habitation(
                        id=str(uuid4()),
                        name=name,
                        district=props.get("district", "Chamoli"),
                        state=props.get("state", "Uttarakhand"),
                        geom=pt_geom,
                        risk_score=int(props.get("risk_score", 50)),
                        population=int(props.get("population", 100)),
                        households=int(props.get("households", 20)),
                        elevation=float(props.get("elevation", 1500.0)),
                        nearest_road=float(props.get("nearest_road", 1.0)),
                        nearest_hospital=float(props.get("nearest_hospital", 5.0)),
                        nearest_school=float(props.get("nearest_school", 2.0)),
                        data_mode=data_mode,
                    )
                    self.db.add(hab)
                    ctx.inc_inserted()
                else:
                    ctx.inc_skipped()

            self.db.flush()
            return ctx
