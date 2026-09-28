"""Domain enums for PRAYAAS."""

from __future__ import annotations

from enum import Enum


class DataMode(str, Enum):
    """Operational mode of the data record."""

    DEMO = "DEMO"
    REALTIME = "REALTIME"
    HISTORICAL = "HISTORICAL"
    SIMULATED = "SIMULATED"
    PUBLIC = "PUBLIC"
    LIVE = "LIVE"
    MODELED = "MODELED"
    FIELD = "FIELD"


class RiskClassification(str, Enum):
    """Risk severity categorization."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    WATCH = "WATCH"
    SAFE = "SAFE"


class RelocationUrgency(str, Enum):
    """Planning urgency for habitation relocation."""

    IMMEDIATE = "IMMEDIATE"
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    MONITOR = "MONITOR"


class CandidateStatus(str, Enum):
    """Suitability and vetting status of candidate relocation site."""

    SUITABLE = "SUITABLE"
    PROVISIONAL = "PROVISIONAL"
    UNSUITABLE = "UNSUITABLE"
    PENDING = "PENDING"


class VerificationStatus(str, Enum):
    """Ground-truth verification lifecycle status."""

    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FLAGGED = "FLAGGED"


class HazardType(str, Enum):
    """Types of natural hazards evaluated in multi-hazard risk engine."""

    LANDSLIDE = "LANDSLIDE"
    FLOOD = "FLOOD"
    CLOUDBURST = "CLOUDBURST"
    COASTAL_EROSION = "COASTAL_EROSION"
    EARTHQUAKE = "EARTHQUAKE"
    AVALANCHE = "AVALANCHE"
    SUBSIDENCE = "SUBSIDENCE"


class InfrastructureType(str, Enum):
    """Asset classification for critical infrastructure."""

    HOSPITAL = "HOSPITAL"
    SCHOOL = "SCHOOL"
    ROAD_JUNCTION = "ROAD_JUNCTION"
    BRIDGE = "BRIDGE"
    HELIPAD = "HELIPAD"
    SHELTER = "SHELTER"
    CLINIC = "CLINIC"
    WATER_SOURCE = "WATER_SOURCE"


class IngestionStatus(str, Enum):
    """Status of an ingestion run."""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class ObservationType(str, Enum):
    """Environmental sensor observation type."""

    RAINFALL_24H = "RAINFALL_24H"
    RAINFALL_7D = "RAINFALL_7D"
    TEMPERATURE = "TEMPERATURE"
    SOIL_MOISTURE_0_7CM = "SOIL_MOISTURE_0_7CM"
    WEATHER_CODE = "WEATHER_CODE"
    WIND_SPEED = "WIND_SPEED"


class DatasetType(str, Enum):
    """Raster and geospatial dataset type."""

    DEM = "DEM"
    SLOPE = "SLOPE"
    ASPECT = "ASPECT"
    LANDCOVER = "LANDCOVER"
    SATELLITE = "SATELLITE"


class RedZoneClassification(str, Enum):
    """Statutory Red Zone planning categorization."""

    PERMANENT_RED = "PERMANENT_RED"
    CONDITIONAL_RED = "CONDITIONAL_RED"
    DYNAMIC_RED = "DYNAMIC_RED"
    WATCH = "WATCH"
    ACCEPTABLE = "ACCEPTABLE"


class ReadinessLevel(str, Enum):
    """Institutional readiness classification."""

    NOT_READY = "NOT_READY"
    LOW_READINESS = "LOW_READINESS"
    MODERATE_READINESS = "MODERATE_READINESS"
    HIGH_READINESS = "HIGH_READINESS"


class SourceFreshness(str, Enum):
    """Evaluation of data source freshness."""

    CURRENT = "CURRENT"
    AGING = "AGING"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
