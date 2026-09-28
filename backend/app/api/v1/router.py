"""API router — aggregates all domain endpoints."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.states import states_router, districts_router
from app.api.v1.habitations import router as habitations_router
from app.api.v1.hazard_zones import router as hazard_zones_router
from app.api.v1.candidate_sites import router as candidate_sites_router
from app.api.v1.infrastructure import router as infrastructure_router
from app.api.v1.relocation_priorities import router as priorities_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.data_sources import router as data_sources_router
from app.api.v1.disaster_events import router as disaster_events_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.analysis import router as analysis_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(states_router)
api_router.include_router(districts_router)
api_router.include_router(habitations_router)
api_router.include_router(hazard_zones_router)
api_router.include_router(candidate_sites_router)
api_router.include_router(infrastructure_router)
api_router.include_router(priorities_router)
api_router.include_router(alerts_router)
api_router.include_router(metrics_router)
api_router.include_router(data_sources_router)
api_router.include_router(disaster_events_router)
api_router.include_router(ingestion_router)
api_router.include_router(analysis_router)

# Compatibility alias
v1_router = api_router
