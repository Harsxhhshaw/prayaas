"""Tabular CSV survey and attribute importer."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from app.models.enums import DataMode, InfrastructureType
from app.models.habitation import Habitation
from app.models.infrastructure import InfrastructureAsset
from app.models.ingestion import EnvironmentalObservation
from app.models.risk import VulnerabilityProfile
from app.services.ingestion.base import BaseIngestionConnector, IngestionContext
from app.services.ingestion.registry import SourceRegistryService


class CSVImporter(BaseIngestionConnector):
    """Parses tabular CSV files for socio-economic vulnerability surveys and field data."""

    def __init__(self, db: Session, source_name: str = "CSV Survey Import", source_id: str | None = None) -> None:
        if not source_id:
            registry = SourceRegistryService(db)
            source = registry.get_or_create_source(
                id=f"SRC-CSV-{uuid4().hex[:8].upper()}",
                name=source_name,
                provider="SDMA Field Surveys",
                type="FIELD_SURVEY",
                data_mode=DataMode.FIELD.value,
                expected_refresh_seconds=2592000,
            )
            source_id = source.id
        super().__init__(db, ingestion_type="CSV_IMPORT", source_id=source_id, data_mode=DataMode.FIELD.value)

    def import_csv(
        self,
        csv_text: str,
        entity_type: str,
        data_mode: str = DataMode.FIELD.value,
    ) -> IngestionContext:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        rows = list(reader)

        with self.run_context() as ctx:
            ctx.set_metadata("entity_type", entity_type)
            ctx.set_metadata("row_count", len(rows))

            for row in rows:
                ctx.inc_received()
                try:
                    if entity_type.upper() == "VULNERABILITY":
                        # Match habitation by id or name
                        hab_id = row.get("habitation_id") or row.get("id")
                        hab_name = row.get("habitation_name") or row.get("name")
                        hab = None
                        if hab_id:
                            hab = self.db.query(Habitation).filter(Habitation.id == hab_id).first()
                        if not hab and hab_name:
                            hab = self.db.query(Habitation).filter(Habitation.name.ilike(hab_name.strip())).first()

                        if not hab:
                            ctx.inc_skipped()
                            continue

                        # Check if profile exists
                        profile = (
                            self.db.query(VulnerabilityProfile)
                            .filter(VulnerabilityProfile.habitation_id == hab.id)
                            .first()
                        )
                        if not profile:
                            profile = VulnerabilityProfile(
                                id=str(uuid4()),
                                habitation_id=hab.id,
                                source_id=self.source_id,
                                data_mode=data_mode,
                            )
                            self.db.add(profile)
                            ctx.inc_inserted()
                        else:
                            profile.data_mode = data_mode
                            ctx.inc_updated()

                        if "population" in row:
                            profile.population = int(row["population"])
                        if "households" in row:
                            profile.households = int(row["households"])
                        if "children_share" in row:
                            profile.children_share = float(row["children_share"])
                        if "elderly_share" in row:
                            profile.elderly_share = float(row["elderly_share"])
                        if "disability_share" in row:
                            profile.disability_share = float(row["disability_share"])
                        if "housing_vulnerability" in row:
                            profile.housing_vulnerability = float(row["housing_vulnerability"])
                        if "population_density" in row:
                            profile.population_density = float(row["population_density"])
                        if "healthcare_access_score" in row:
                            profile.healthcare_access_score = float(row["healthcare_access_score"])
                        if "road_access_score" in row:
                            profile.road_access_score = float(row["road_access_score"])
                        if "isolation_score" in row:
                            profile.isolation_score = float(row["isolation_score"])
                        if "data_confidence" in row:
                            profile.data_confidence = float(row["data_confidence"])
                        profile.raw_attributes = dict(row)

                    elif entity_type.upper() == "INFRASTRUCTURE":
                        lat = float(row["lat"])
                        lng = float(row["lng"])
                        name = row.get("name", "Asset")
                        type_str = row.get("type", "HOSPITAL")

                        asset = InfrastructureAsset(
                            id=str(uuid4()),
                            name=name,
                            type=type_str,
                            geom=from_shape(Point(lng, lat), srid=4326),
                            status=row.get("status", "OPERATIONAL"),
                            capacity=int(row["capacity"]) if row.get("capacity") else None,
                            district=row.get("district", "Chamoli"),
                            data_mode=data_mode,
                        )
                        self.db.add(asset)
                        ctx.inc_inserted()

                    elif entity_type.upper() == "OBSERVATION":
                        hab_id = row.get("habitation_id")
                        obs_type = row.get("observation_type", "RAINFALL_24H")
                        val = float(row["value"])
                        unit = row.get("unit", "mm")
                        obs_time = datetime.now(timezone.utc)
                        if "observed_at" in row:
                            try:
                                obs_time = datetime.fromisoformat(row["observed_at"])
                            except Exception:
                                pass

                        obs = EnvironmentalObservation(
                            id=str(uuid4()),
                            habitation_id=hab_id,
                            source_id=self.source_id,
                            observation_type=obs_type,
                            value=val,
                            unit=unit,
                            observed_at=obs_time,
                            fetched_at=datetime.now(timezone.utc),
                            data_mode=data_mode,
                            raw_metadata=dict(row),
                        )
                        self.db.add(obs)
                        ctx.inc_inserted()
                    else:
                        ctx.inc_skipped()

                except Exception:
                    ctx.inc_rejected()

            self.db.flush()
            return ctx
