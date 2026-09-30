"""ORM -> Pydantic and GeoJSON serializer helpers.

Translates between SQLAlchemy ORM models with GeoAlchemy2 columns,
camelCase API response models, and RFC 7946 GeoJSON collections.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from geoalchemy2.shape import to_shape

from app.schemas.common import GeoPointResponse
from app.services.risk.semantics import normalize_hazard_scores
from app.spatial import to_geojson_point, to_geojson_polygon


def geom_to_point(geom) -> GeoPointResponse:
    """Convert a PostGIS Point geometry to a GeoPointResponse (lat, lng)."""
    shape = to_shape(geom)
    return GeoPointResponse(lat=round(shape.y, 6), lng=round(shape.x, 6))


def geom_to_bounds(geom) -> list[GeoPointResponse]:
    """Convert a PostGIS Polygon geometry to a list of GeoPointResponse vertices."""
    shape = to_shape(geom)
    coords = list(shape.exterior.coords)[:-1]  # drop closing repeat
    return [GeoPointResponse(lat=round(y, 6), lng=round(x, 6)) for x, y in coords]


# ── REST Dict Serializers ──

def state_to_dict(s) -> dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "code": s.code,
        "data_mode": getattr(s, "data_mode", None) or "DEMO",
        "districts": [district_to_dict(d) for d in getattr(s, "districts", [])],
    }


def district_to_dict(d) -> dict[str, Any]:
    return {
        "id": d.id,
        "name": d.name,
        "state_id": d.state_id,
        "state_name": d.state.name if getattr(d, "state", None) else None,
        "headquarters": d.headquarters,
        "data_mode": getattr(d, "data_mode", None) or "DEMO",
    }


def habitation_to_dict(h) -> dict[str, Any]:
    norm_hazards = normalize_hazard_scores(h.hazard_scores, district=h.district, state=h.state)
    return {
        "id": h.id,
        "name": h.name,
        "district": h.district,
        "state": h.state,
        "position": geom_to_point(h.geom),
        "riskScore": h.risk_score,
        "riskCategory": h.risk_category,
        "urgency": h.urgency,
        "population": h.population,
        "households": h.households,
        "confidence": h.confidence,
        "hazardScores": norm_hazards,
        "vulnerabilityScore": h.vulnerability_score,
        "riskHistory": h.risk_history or [],
        "elevation": h.elevation,
        "nearestRoad": h.nearest_road,
        "nearestHospital": h.nearest_hospital,
        "nearestSchool": h.nearest_school,
        "lastAssessed": h.last_assessed,
        "verificationStatus": h.verification_status,
        "data_mode": getattr(h, "data_mode", None) or "DEMO",
    }


def hazard_zone_to_dict(hz) -> dict[str, Any]:
    return {
        "id": hz.id,
        "name": hz.name,
        "bounds": geom_to_bounds(hz.geom),
        "hazardTypes": hz.hazard_types or [],
        "compositRiskScore": hz.composite_risk_score,
        "habitationCount": hz.habitation_count,
        "populationAffected": hz.population_affected,
        "areaKmSq": hz.area_km_sq,
        "computedAreaSqKm": getattr(hz, "computed_area_sq_km", None),
        "sourceDeclaredAreaSqKm": getattr(hz, "source_declared_area_sq_km", None),
        "declaredDate": hz.declared_date,
        "lastUpdated": hz.last_updated,
        "data_mode": getattr(hz, "data_mode", None) or "DEMO",
    }


# Compatibility alias
red_zone_to_dict = hazard_zone_to_dict


def candidate_site_to_dict(cs) -> dict[str, Any]:
    bounds = geom_to_bounds(cs.geom)
    centroid = geom_to_point(cs.centroid)
    return {
        "id": cs.id,
        "name": cs.name,
        "district": cs.district,
        "state": cs.state,
        "position": centroid,
        "bounds": bounds,
        "suitabilityScore": cs.suitability_score,
        "carryingCapacity": cs.carrying_capacity,
        "currentUtilization": cs.current_utilization,
        "areaHectares": cs.area_hectares,
        "elevation": cs.elevation,
        "distanceFromHazard": cs.distance_from_hazard,
        "roadAccess": cs.road_access,
        "waterAccess": cs.water_access,
        "electricityAccess": cs.electricity_access,
        "landUseType": cs.land_use_type,
        "ownership": cs.ownership,
        "status": getattr(cs, "status", "SUITABLE"),
        "verificationStatus": cs.verification_status,
        "assignedHabitations": cs.assigned_habitations or [],
        "data_mode": getattr(cs, "data_mode", None) or "DEMO",
    }


def infrastructure_to_dict(ip) -> dict[str, Any]:
    return {
        "id": ip.id,
        "name": ip.name,
        "type": ip.type,
        "position": geom_to_point(ip.geom),
        "status": ip.status,
        "capacity": ip.capacity,
        "district": getattr(ip, "district", None),
        "data_mode": getattr(ip, "data_mode", None) or "DEMO",
    }


def data_source_to_dict(ds) -> dict[str, Any]:
    from app.services.ingestion.registry import evaluate_source_freshness
    freshness, _ = evaluate_source_freshness(ds)
    return {
        "id": ds.id,
        "name": ds.name,
        "provider": ds.provider,
        "type": ds.type,
        "status": ds.status,
        "lastSync": ds.last_sync,
        "recordsCount": ds.records_count,
        "latencyMs": ds.latency_ms,
        "dataMode": getattr(ds, "data_mode", None) or "DEMO",
        "verifiedUrl": getattr(ds, "verified_url", None),
        "license": getattr(ds, "license", None),
        "sourceDate": getattr(ds, "source_date", None),
        "lastIngestedAt": ds.last_ingested_at.isoformat() if ds.last_ingested_at else None,
        "lastSuccessfulIngestion": ds.last_successful_ingestion.isoformat() if ds.last_successful_ingestion else (ds.last_sync or None),
        "spatialResolution": getattr(ds, "spatial_resolution", None),
        "temporalResolution": getattr(ds, "temporal_resolution", None),
        "expectedRefreshSeconds": getattr(ds, "expected_refresh_seconds", None),
        "freshness": freshness.value,
    }


def disaster_event_to_dict(de) -> dict[str, Any]:
    position = geom_to_point(de.geom) if getattr(de, "geom", None) is not None else None
    return {
        "id": de.id,
        "title": de.title,
        "hazardType": de.hazard_type,
        "severity": de.severity,
        "eventDate": de.event_date,
        "district": de.district,
        "position": position,
        "fatalities": de.fatalities,
        "displacedPersons": de.displaced_persons,
        "description": de.description,
        "dataMode": getattr(de, "data_mode", None) or "DEMO",
    }


def relocation_priority_to_dict(rp) -> dict[str, Any]:
    return {
        "id": rp.id,
        "habitationId": rp.habitation_id,
        "habitationName": rp.habitation_name,
        "urgency": rp.urgency,
        "riskScore": rp.risk_score,
        "population": rp.population,
        "district": rp.district,
        "assignedSiteId": rp.assigned_site_id,
        "assignedSiteName": rp.assigned_site_name,
        "estimatedCost": rp.estimated_cost,
        "timelineMonths": rp.timeline_months,
    }


def alert_to_dict(a) -> dict[str, Any]:
    return {
        "id": a.id,
        "message": a.message,
        "type": a.type,
        "severity": a.severity,
        "timestamp": a.timestamp,
        "habitationId": a.habitation_id,
        "read": a.read,
    }


def ingestion_run_to_dict(run) -> dict[str, Any]:
    return {
        "id": run.id,
        "source_id": run.source_id,
        "ingestion_type": run.ingestion_type,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "records_received": run.records_received,
        "records_inserted": run.records_inserted,
        "records_updated": run.records_updated,
        "records_skipped": run.records_skipped,
        "records_rejected": run.records_rejected,
        "error_message": run.error_message,
        "data_mode": run.data_mode,
        "ingestion_metadata": run.ingestion_metadata or {},
    }


def environmental_observation_to_dict(obs) -> dict[str, Any]:
    return {
        "id": obs.id,
        "habitation_id": obs.habitation_id,
        "district_id": obs.district_id,
        "source_id": obs.source_id,
        "observation_type": obs.observation_type,
        "value": obs.value,
        "unit": obs.unit,
        "observed_at": obs.observed_at.isoformat(),
        "fetched_at": obs.fetched_at.isoformat(),
        "data_mode": obs.data_mode,
        "raw_metadata": obs.raw_metadata or {},
    }


def risk_assessment_to_dict(ra) -> dict[str, Any]:
    return {
        "id": ra.id,
        "habitation_id": ra.habitation_id,
        "habitation_name": ra.habitation.name if getattr(ra, "habitation", None) else None,
        "analysis_version": ra.analysis_version,
        "config_version": ra.config_version,
        "baseline_hazard_score": ra.baseline_hazard_score,
        "dynamic_hazard_score": ra.dynamic_hazard_score,
        "hazard_score": ra.hazard_score,
        "exposure_score": ra.exposure_score,
        "vulnerability_score": ra.vulnerability_score,
        "adaptive_capacity_score": ra.adaptive_capacity_score,
        "adaptive_capacity_deficit_score": ra.adaptive_capacity_deficit_score,
        "history_score": ra.history_score,
        "trend_score": ra.trend_score,
        "compound_hazard_adjustment": ra.compound_hazard_adjustment,
        "baseline_structural_risk": ra.baseline_structural_risk,
        "current_dynamic_risk": ra.current_dynamic_risk,
        "composite_risk_score": ra.composite_risk_score,
        "risk_classification": ra.risk_classification,
        "confidence_score": ra.confidence_score,
        "dominant_hazard": ra.dominant_hazard,
        "sustainability_index": ra.sustainability_index,
        "reason_codes": ra.reason_codes or [],
        "explanation": ra.explanation,
        "calculated_at": ra.calculated_at.isoformat(),
    }


def relocation_assessment_to_dict(ra) -> dict[str, Any]:
    return {
        "id": ra.id,
        "habitation_id": ra.habitation_id,
        "habitation_name": ra.habitation.name if getattr(ra, "habitation", None) else None,
        "risk_assessment_id": ra.risk_assessment_id,
        "analysis_version": ra.analysis_version,
        "config_version": ra.config_version,
        "need_score": ra.need_score,
        "urgency": ra.urgency,
        "readiness_score": ra.readiness_score,
        "readiness_level": ra.readiness_level,
        "need_components": ra.need_components or {},
        "readiness_components": ra.readiness_components or {},
        "readiness_gaps": ra.readiness_gaps or [],
        "reason_codes": ra.reason_codes or [],
        "explanation": ra.explanation,
        "confidence_score": ra.confidence_score,
        "calculated_at": ra.calculated_at.isoformat(),
    }


# ── GeoJSON Feature Serializers (RFC 7946: [lng, lat] coordinate order) ──

def habitation_to_geojson_feature(h) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": h.id,
        "geometry": to_geojson_point(h.geom),
        "properties": {
            "name": h.name,
            "district": h.district,
            "state": h.state,
            "riskScore": h.risk_score,
            "riskCategory": h.risk_category,
            "urgency": h.urgency,
            "population": h.population,
            "households": h.households,
            "elevation": h.elevation,
            "verificationStatus": h.verification_status,
        },
    }


def hazard_zone_to_geojson_feature(hz) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": hz.id,
        "geometry": to_geojson_polygon(hz.geom),
        "properties": {
            "name": hz.name,
            "compositeRiskScore": hz.composite_risk_score,
            "hazardTypes": hz.hazard_types or [],
            "habitationCount": hz.habitation_count,
            "populationAffected": hz.population_affected,
            "areaKmSq": hz.area_km_sq,
            "computedAreaSqKm": getattr(hz, "computed_area_sq_km", None),
            "sourceDeclaredAreaSqKm": getattr(hz, "source_declared_area_sq_km", None),
            "declaredDate": hz.declared_date,
        },
    }


def candidate_site_to_geojson_feature(cs) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": cs.id,
        "geometry": to_geojson_polygon(cs.geom),
        "properties": {
            "name": cs.name,
            "district": cs.district,
            "state": cs.state,
            "suitabilityScore": cs.suitability_score,
            "carryingCapacity": cs.carrying_capacity,
            "currentUtilization": cs.current_utilization,
            "areaHectares": cs.area_hectares,
            "elevation": cs.elevation,
            "distanceFromHazard": cs.distance_from_hazard,
            "status": getattr(cs, "status", "SUITABLE"),
            "verificationStatus": cs.verification_status,
        },
    }


def infrastructure_to_geojson_feature(ia) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": ia.id,
        "geometry": to_geojson_point(ia.geom),
        "properties": {
            "name": ia.name,
            "type": ia.type,
            "status": ia.status,
            "capacity": ia.capacity,
            "district": getattr(ia, "district", None),
        },
    }


def candidate_discovery_run_to_dict(run) -> dict[str, Any]:
    return {
        "id": run.id,
        "origin_habitation_id": run.origin_habitation_id,
        "analysis_version": run.analysis_version,
        "config_version": run.config_version,
        "search_radius_km": run.search_radius_km,
        "status": run.status,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "analysis_resolution_meters": getattr(run, "analysis_resolution_meters", None),
        "effective_source_resolution_meters": getattr(run, "effective_source_resolution_meters", None),
        "cells_evaluated": run.cells_evaluated,
        "cells_excluded": run.cells_excluded,
        "total_aoi_area_sq_km": getattr(run, "total_aoi_area_sq_km", None),
        "excluded_area_sq_km": getattr(run, "excluded_area_sq_km", None),
        "feasible_area_sq_km": getattr(run, "feasible_area_sq_km", None),
        "feasible_percent": getattr(run, "feasible_percent", None),
        "candidate_eligible_cells": getattr(run, "candidate_eligible_cells", None),
        "candidate_eligible_area_sq_km": getattr(run, "candidate_eligible_area_sq_km", None),
        "candidate_count": run.candidate_count,
        "warning_metadata": run.warning_metadata or [],
        "created_at": run.created_at or getattr(run, "started_at", None) or datetime.now(timezone.utc),
    }


def candidate_parcel_to_dict(cp) -> dict[str, Any]:
    return {
        "id": cp.id,
        "discovery_run_id": cp.discovery_run_id,
        "origin_habitation_id": cp.origin_habitation_id,
        "rank": cp.rank,
        "suitability_score": cp.suitability_score,
        "confidence_score": cp.confidence_score,
        "robustness_score": cp.robustness_score,
        "rank_stability": cp.rank_stability,
        "status": cp.status,
        "area_sq_km": cp.area_sq_km,
        "area_hectares": cp.area_hectares,
        "distance_from_origin_km": cp.distance_from_origin_km,
        "mean_slope_degrees": getattr(cp, "mean_slope_degrees", 0.0),
        "exclusion_summary": cp.exclusion_summary or {},
        "criteria_scores": cp.criteria_scores or {},
        "reason_codes": cp.reason_codes or [],
        "limitations": cp.limitations or [],
        "explanation": cp.explanation or {},
        "data_mode": cp.data_mode,
        "centroid": geom_to_point(cp.centroid),
        "created_at": cp.created_at or datetime.now(timezone.utc),
    }


def candidate_parcel_to_geojson_feature(cp) -> dict[str, Any]:
    from app.spatial import to_geojson_geometry
    return {
        "type": "Feature",
        "id": cp.id,
        "geometry": to_geojson_geometry(cp.geom),
        "properties": {
            "id": cp.id,
            "discoveryRunId": cp.discovery_run_id,
            "originHabitationId": cp.origin_habitation_id,
            "rank": cp.rank,
            "suitabilityScore": cp.suitability_score,
            "confidenceScore": cp.confidence_score,
            "robustnessScore": cp.robustness_score,
            "rankStability": cp.rank_stability,
            "status": cp.status,
            "areaSqKm": cp.area_sq_km,
            "areaHectares": cp.area_hectares,
            "distanceKm": cp.distance_from_origin_km,
            "meanSlopeDegrees": getattr(cp, "mean_slope_degrees", 0.0),
            "dataMode": cp.data_mode,
            "reasonCodes": cp.reason_codes or [],
            "limitations": cp.limitations or [],
            "exclusionSummary": cp.exclusion_summary or {},
            "criteriaScores": cp.criteria_scores or {},
            "explanation": cp.explanation or {},
        },
    }

