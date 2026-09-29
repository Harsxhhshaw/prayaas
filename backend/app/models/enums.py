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


class AnalyticalStatus(str, Enum):
    """Three-state analytical semantics: VALUE, UNKNOWN, NOT_APPLICABLE."""

    VALUE = "VALUE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RepresentationType(str, Enum):
    """Spatial and data representation format."""

    RASTER = "RASTER"
    VECTOR = "VECTOR"
    TABULAR = "TABULAR"
    TIMESERIES = "TIMESERIES"


class EvidenceType(str, Enum):
    """Extensible analytical evidence types."""

    ELEVATION = "ELEVATION"
    SLOPE = "SLOPE"
    ASPECT = "ASPECT"
    PLAN_CURVATURE = "PLAN_CURVATURE"
    PROFILE_CURVATURE = "PROFILE_CURVATURE"
    RAINFALL = "RAINFALL"
    SOIL_MOISTURE = "SOIL_MOISTURE"
    NDVI = "NDVI"
    LULC = "LULC"
    ROAD_DISTANCE = "ROAD_DISTANCE"
    DRAINAGE_DISTANCE = "DRAINAGE_DISTANCE"
    FAULT_DISTANCE = "FAULT_DISTANCE"
    GEOLOGY = "GEOLOGY"
    LANDSLIDE_INVENTORY = "LANDSLIDE_INVENTORY"
    FLOOD_HAZARD = "FLOOD_HAZARD"
    GROUND_DISPLACEMENT = "GROUND_DISPLACEMENT"
    LANDSLIDE_CHANGE = "LANDSLIDE_CHANGE"
    NDVI_CHANGE = "NDVI_CHANGE"
    LAND_COVER_CHANGE = "LAND_COVER_CHANGE"
    RIVER_CHANNEL_CHANGE = "RIVER_CHANNEL_CHANGE"
    SURFACE_DISTURBANCE = "SURFACE_DISTURBANCE"


class HazardModelType(str, Enum):
    """Susceptibility and hazard modeling methodology."""

    AHP = "AHP"
    FREQUENCY_RATIO = "FREQUENCY_RATIO"
    ML = "ML"
    SATELLITE_EVIDENCE = "SATELLITE_EVIDENCE"
    OTHER = "OTHER"


class HazardModelStatus(str, Enum):
    """Operational lifecycle status of a hazard model."""

    CONFIGURED = "CONFIGURED"
    TRAINED = "TRAINED"
    UNTRAINED = "UNTRAINED"
    INCONSISTENT = "INCONSISTENT"
    DEMO = "DEMO"
    NOT_VALIDATED = "NOT_VALIDATED"
    OPERATIONAL = "OPERATIONAL"


class ModelAgreementLevel(str, Enum):
    """Multi-method agreement classification."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class InventoryVerificationStatus(str, Enum):
    """Ground-truth verification for hazard inventory events."""

    UNVERIFIED = "UNVERIFIED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    FIELD_VERIFIED = "FIELD_VERIFIED"


class ValidationType(str, Enum):
    """Methodology used for model evaluation and validation."""

    SPATIAL_BLOCK_SPLIT = "SPATIAL_BLOCK_SPLIT"
    RANDOM_SPLIT = "RANDOM_SPLIT"
    HOLDOUT_AREA = "HOLDOUT_AREA"
    CROSS_VALIDATION = "CROSS_VALIDATION"


class CandidateDiscoveryStatus(str, Enum):
    """Execution status of an automated candidate discovery run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ParcelStatus(str, Enum):
    """Screening lifecycle status of a discovered candidate parcel."""

    PRELIMINARY = "PRELIMINARY"
    SHORTLISTED = "SHORTLISTED"
    REQUIRES_FIELD_REVIEW = "REQUIRES_FIELD_REVIEW"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class ExclusionCheckStatus(str, Enum):
    """Outcome of a hard exclusion safety evaluation."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RobustnessLevel(str, Enum):
    """Categorical robustness rating derived from Monte Carlo weight perturbation."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DistanceUtilityCurveType(str, Enum):
    """Mathematical utility curve applied to spatial accessibility distances."""

    MONOTONIC_DECREASING = "MONOTONIC_DECREASING"
    MONOTONIC_INCREASING = "MONOTONIC_INCREASING"
    OPTIMAL_RANGE = "OPTIMAL_RANGE"
    CUSTOM_PIECEWISE = "CUSTOM_PIECEWISE"


class VerificationLevel(str, Enum):
    """Progressive evidence verification levels."""

    FIELD_OBSERVED = "FIELD_OBSERVED"
    TECHNICALLY_VERIFIED = "TECHNICALLY_VERIFIED"
    AUTHORITY_REVIEWED = "AUTHORITY_REVIEWED"


class FieldObservationType(str, Enum):
    """Taxonomy of ground-level field observations."""

    SLOPE_INSTABILITY = "SLOPE_INSTABILITY"
    GROUND_CRACK = "GROUND_CRACK"
    WATER_SEEPAGE = "WATER_SEEPAGE"
    LANDSLIDE_SCAR = "LANDSLIDE_SCAR"
    ROAD_DAMAGE = "ROAD_DAMAGE"
    WATER_SOURCE = "WATER_SOURCE"
    SETTLEMENT_CONDITION = "SETTLEMENT_CONDITION"
    INFRASTRUCTURE_CONDITION = "INFRASTRUCTURE_CONDITION"
    CANDIDATE_SITE_INSPECTION = "CANDIDATE_SITE_INSPECTION"
    OTHER = "OTHER"


class LandCategory(str, Enum):
    """Statutory legal and tenure verification gates."""

    FOREST_STATUS = "FOREST_STATUS"
    PROTECTED_AREA_STATUS = "PROTECTED_AREA_STATUS"
    LAND_OWNERSHIP = "LAND_OWNERSHIP"
    LAND_USE_RESTRICTION = "LAND_USE_RESTRICTION"
    ACQUISITION_STATUS = "ACQUISITION_STATUS"


class LandStatus(str, Enum):
    """Cadastral and revenue availability status."""

    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"
    PUBLIC_RECORD_AVAILABLE = "PUBLIC_RECORD_AVAILABLE"
    RESTRICTED = "RESTRICTED"
    POTENTIALLY_AVAILABLE = "POTENTIALLY_AVAILABLE"
    REQUIRES_REVENUE_VERIFICATION = "REQUIRES_REVENUE_VERIFICATION"


class GovernanceReviewStage(str, Enum):
    """Institutional review workflow stages."""

    DRAFT = "DRAFT"
    ANALYTICAL_REVIEW = "ANALYTICAL_REVIEW"
    FIELD_REVIEW_REQUIRED = "FIELD_REVIEW_REQUIRED"
    TECHNICAL_REVIEW_REQUIRED = "TECHNICAL_REVIEW_REQUIRED"
    AUTHORITY_REVIEW_REQUIRED = "AUTHORITY_REVIEW_REQUIRED"
    REVIEW_COMPLETE = "REVIEW_COMPLETE"


