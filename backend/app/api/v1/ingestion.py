"""Data Ingestion, pipeline trigger, and observation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.serializers import environmental_observation_to_dict, ingestion_run_to_dict
from app.models.ingestion import EnvironmentalObservation, IngestionRun
from app.schemas.ingestion import (
    CSVImportRequest,
    EnvironmentalObservationListResponse,
    GeoJSONImportRequest,
    IngestionRunListResponse,
    IngestionRunResponse,
    OSMIngestRequest,
    WeatherIngestRequest,
)
from app.services.ingestion.csv_import import CSVImporter
from app.services.ingestion.geojson_import import GeoJSONImporter
from app.services.ingestion.osm import OSMIngestionConnector
from app.services.ingestion.terrain import TerrainProcessingService
from app.services.ingestion.weather import WeatherIngestionConnector

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/osm", response_model=IngestionRunResponse)
def trigger_osm_ingestion(
    payload: OSMIngestRequest | None = None,
    db: Session = Depends(get_db),
):
    """Trigger real OpenStreetMap Overpass ingestion for critical infrastructure in AOI."""
    connector = OSMIngestionConnector(db)
    bbox = payload.bbox if payload else [30.2, 79.0, 30.6, 79.7]
    amenities = payload.amenity_types if payload else None
    try:
        ctx = connector.ingest(bbox=bbox, amenity_types=amenities)
        return ingestion_run_to_dict(ctx.run)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OSM ingestion failed: {exc}")


@router.post("/weather", response_model=IngestionRunResponse)
def trigger_weather_ingestion(
    payload: WeatherIngestRequest | None = None,
    db: Session = Depends(get_db),
):
    """Fetch live meteorological & soil moisture observations from Open-Meteo."""
    connector = WeatherIngestionConnector(db)
    hab_ids = payload.habitation_ids if payload else None
    force = payload.force_refresh if payload else False
    try:
        ctx = connector.ingest_for_habitations(habitation_ids=hab_ids, force_refresh=force)
        return ingestion_run_to_dict(ctx.run)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Weather ingestion failed: {exc}")


@router.post("/terrain-catalog", response_model=IngestionRunResponse)
def trigger_terrain_catalog_sync(db: Session = Depends(get_db)):
    """Registers ALOS PALSAR 12.5m DEM and derived slope datasets in catalog."""
    service = TerrainProcessingService(db)
    ctx = service.register_catalog_datasets()
    return ingestion_run_to_dict(ctx.run)


@router.post("/import/geojson", response_model=IngestionRunResponse)
def import_geojson(
    payload: GeoJSONImportRequest,
    db: Session = Depends(get_db),
):
    """Import spatial GeoJSON FeatureCollection into database."""
    importer = GeoJSONImporter(db, source_name=payload.source_name)
    try:
        ctx = importer.import_features(
            geojson_data=payload.geojson_data,
            entity_type=payload.entity_type,
            data_mode=payload.data_mode,
        )
        return ingestion_run_to_dict(ctx.run)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"GeoJSON import error: {exc}")


@router.post("/import/csv", response_model=IngestionRunResponse)
def import_csv(
    payload: CSVImportRequest,
    db: Session = Depends(get_db),
):
    """Import tabular CSV data for vulnerability surveys, infrastructure, or sensors."""
    importer = CSVImporter(db, source_name=payload.source_name)
    try:
        ctx = importer.import_csv(
            csv_text=payload.csv_text,
            entity_type=payload.entity_type,
            data_mode=payload.data_mode,
        )
        return ingestion_run_to_dict(ctx.run)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"CSV import error: {exc}")


@router.get("/runs", response_model=IngestionRunListResponse)
def list_ingestion_runs(
    status: str | None = Query(None),
    ingestion_type: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """List recent ingestion execution runs."""
    q = db.query(IngestionRun)
    if status:
        q = q.filter(IngestionRun.status == status)
    if ingestion_type:
        q = q.filter(IngestionRun.ingestion_type == ingestion_type)
    rows = q.order_by(IngestionRun.started_at.desc()).limit(limit).all()
    items = [ingestion_run_to_dict(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.get("/observations", response_model=EnvironmentalObservationListResponse)
def list_observations(
    habitation_id: str | None = Query(None),
    observation_type: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """List environmental observations (weather, rainfall, soil moisture)."""
    q = db.query(EnvironmentalObservation)
    if habitation_id:
        q = q.filter(EnvironmentalObservation.habitation_id == habitation_id)
    if observation_type:
        q = q.filter(EnvironmentalObservation.observation_type == observation_type)
    rows = q.order_by(EnvironmentalObservation.observed_at.desc()).limit(limit).all()
    items = [environmental_observation_to_dict(o) for o in rows]
    return {"items": items, "total": len(items)}
