"""Deterministic, idempotent seed data loader for Chamoli disaster intelligence demo.

Loads:
- States & Districts (Uttarakhand: Chamoli, Rudraprayag, etc.)
- 13 Habitations in Chamoli & Rudraprayag
- 4 Hazard / Red Zones with Polygon geometry
- 8 Candidate Relocation Sites with Polygon & Centroid geometry
- 12 Infrastructure Assets with Point geometry
- 2 Disaster Events (2021 Chamoli Flood, 2023 Joshimath Subsidence)
- 4 External Data Sources (ISRO, IMD, USGS, Survey of India)
- 13 Relocation Priorities
- 8 Operational Alerts

All geometries use SRID 4326 with strictly (longitude, latitude) coordinates.
The script is strictly idempotent and safe to rerun multiple times.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4
from shapely.geometry import Point, Polygon, MultiPolygon
from geoalchemy2.shape import from_shape
from sqlalchemy import func

from app.database import SessionLocal
from app.models import (
    CandidateSite,
    DataSource,
    DisasterEvent,
    District,
    Habitation,
    HazardZone,
    InfrastructureAsset,
    OperationalAlert,
    RelocationPriority,
    State,
    VulnerabilityProfile,
    RiskAssessment,
    RelocationAssessment,
    EvidenceLayer,
    HazardModel,
)
from app.models.candidate_discovery import CandidateDiscoveryRun, CandidateParcel
from app.models.enums import DataMode
from app.services.risk.engine import RiskEngine
from app.services.relocation.engine import RelocationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prayaas.seed")


# ── Administrative ──

STATES_AND_DISTRICTS = [
    {
        "id": "ST-UK",
        "name": "Uttarakhand",
        "code": "UK",
        "districts": [
            {"id": "DIST-UK-CHAM", "name": "Chamoli", "headquarters": "Gopeshwar"},
            {"id": "DIST-UK-RUDR", "name": "Rudraprayag", "headquarters": "Rudraprayag"},
            {"id": "DIST-UK-PITH", "name": "Pithoragarh", "headquarters": "Pithoragarh"},
            {"id": "DIST-UK-UTTA", "name": "Uttarkashi", "headquarters": "Uttarkashi"},
            {"id": "DIST-UK-TEHR", "name": "Tehri Garhwal", "headquarters": "New Tehri"},
            {"id": "DIST-UK-BAGE", "name": "Bageshwar", "headquarters": "Bageshwar"},
        ],
    },
    {
        "id": "ST-HP",
        "name": "Himachal Pradesh",
        "code": "HP",
        "districts": [
            {"id": "DIST-HP-KINN", "name": "Kinnaur", "headquarters": "Reckong Peo"},
            {"id": "DIST-HP-LAHA", "name": "Lahaul & Spiti", "headquarters": "Keylong"},
            {"id": "DIST-HP-KULL", "name": "Kullu", "headquarters": "Kullu"},
            {"id": "DIST-HP-MAND", "name": "Mandi", "headquarters": "Mandi"},
            {"id": "DIST-HP-SHIM", "name": "Shimla", "headquarters": "Shimla"},
            {"id": "DIST-HP-CHAM", "name": "Chamba", "headquarters": "Chamba"},
        ],
    },
    {
        "id": "ST-SK",
        "name": "Sikkim",
        "code": "SK",
        "districts": [
            {"id": "DIST-SK-NSK", "name": "North Sikkim", "headquarters": "Mangan"},
            {"id": "DIST-SK-ESK", "name": "East Sikkim", "headquarters": "Gangtok"},
            {"id": "DIST-SK-WSK", "name": "West Sikkim", "headquarters": "Geyzing"},
            {"id": "DIST-SK-SSK", "name": "South Sikkim", "headquarters": "Namchi"},
        ],
    },
    {
        "id": "ST-AS",
        "name": "Assam",
        "code": "AS",
        "districts": [
            {"id": "DIST-AS-DHEM", "name": "Dhemaji", "headquarters": "Dhemaji"},
            {"id": "DIST-AS-LAKH", "name": "Lakhimpur", "headquarters": "North Lakhimpur"},
            {"id": "DIST-AS-MAJU", "name": "Majuli", "headquarters": "Garamur"},
            {"id": "DIST-AS-MORI", "name": "Morigaon", "headquarters": "Morigaon"},
            {"id": "DIST-AS-NAGA", "name": "Nagaon", "headquarters": "Nagaon"},
            {"id": "DIST-AS-BARP", "name": "Barpeta", "headquarters": "Barpeta"},
        ],
    },
]


# ── Habitations (13 locations) ──

HABITATIONS_DATA = [
    {
        "id": "HAB-001",
        "name": "Khar Village",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.4983,
        "lng": 79.5603,
        "risk_score": 91,
        "risk_category": "CRITICAL",
        "urgency": "IMMEDIATE",
        "population": 3841,
        "households": 712,
        "confidence": 86,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 94, "label": "Landslide"},
            {"type": "CLOUDBURST", "score": 82, "label": "Cloudburst"},
            {"type": "FLOOD", "score": 67, "label": "Flood"},
        ],
        "vulnerability_score": 76,
        "risk_history": [
            {"year": 2022, "score": 64},
            {"year": 2023, "score": 69},
            {"year": 2024, "score": 74},
            {"year": 2025, "score": 82},
            {"year": 2026, "score": 91},
        ],
        "elevation": 1840.0,
        "nearest_road": 2.3,
        "nearest_hospital": 14.5,
        "nearest_school": 1.8,
        "last_assessed": "2026-09-15",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-002",
        "name": "Raini Settlement",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.4750,
        "lng": 79.5820,
        "risk_score": 87,
        "risk_category": "CRITICAL",
        "urgency": "IMMEDIATE",
        "population": 1256,
        "households": 245,
        "confidence": 82,
        "hazard_scores": [
            {"type": "FLOOD", "score": 91, "label": "Flood"},
            {"type": "LANDSLIDE", "score": 78, "label": "Landslide"},
            {"type": "CLOUDBURST", "score": 73, "label": "Cloudburst"},
        ],
        "vulnerability_score": 69,
        "risk_history": [
            {"year": 2022, "score": 58},
            {"year": 2023, "score": 65},
            {"year": 2024, "score": 72},
            {"year": 2025, "score": 79},
            {"year": 2026, "score": 87},
        ],
        "elevation": 1920.0,
        "nearest_road": 0.8,
        "nearest_hospital": 22.3,
        "nearest_school": 3.2,
        "last_assessed": "2026-09-12",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-003",
        "name": "Dungari Hamlet",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-RUDR",
        "lat": 30.4340,
        "lng": 79.1150,
        "risk_score": 84,
        "risk_category": "CRITICAL",
        "urgency": "IMMEDIATE",
        "population": 892,
        "households": 168,
        "confidence": 79,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 89, "label": "Landslide"},
            {"type": "CLOUDBURST", "score": 76, "label": "Cloudburst"},
            {"type": "FLOOD", "score": 58, "label": "Flood"},
        ],
        "vulnerability_score": 82,
        "risk_history": [
            {"year": 2022, "score": 61},
            {"year": 2023, "score": 68},
            {"year": 2024, "score": 73},
            {"year": 2025, "score": 78},
            {"year": 2026, "score": 84},
        ],
        "elevation": 2150.0,
        "nearest_road": 5.1,
        "nearest_hospital": 28.7,
        "nearest_school": 4.6,
        "last_assessed": "2026-08-28",
        "verification_status": "IN_PROGRESS",
    },
    {
        "id": "HAB-004",
        "name": "Bhandar Village",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-RUDR",
        "lat": 30.3950,
        "lng": 79.0780,
        "risk_score": 78,
        "risk_category": "HIGH",
        "urgency": "SHORT_TERM",
        "population": 2134,
        "households": 412,
        "confidence": 74,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 82, "label": "Landslide"},
            {"type": "FLOOD", "score": 71, "label": "Flood"},
            {"type": "CLOUDBURST", "score": 65, "label": "Cloudburst"},
        ],
        "vulnerability_score": 68,
        "risk_history": [
            {"year": 2022, "score": 55},
            {"year": 2023, "score": 60},
            {"year": 2024, "score": 66},
            {"year": 2025, "score": 72},
            {"year": 2026, "score": 78},
        ],
        "elevation": 1650.0,
        "nearest_road": 1.2,
        "nearest_hospital": 18.9,
        "nearest_school": 2.1,
        "last_assessed": "2026-09-05",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-005",
        "name": "Gopeshwar Outskirts",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.4120,
        "lng": 79.3230,
        "risk_score": 74,
        "risk_category": "HIGH",
        "urgency": "SHORT_TERM",
        "population": 4521,
        "households": 856,
        "confidence": 71,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 76, "label": "Landslide"},
            {"type": "FLOOD", "score": 68, "label": "Flood"},
            {"type": "EARTHQUAKE", "score": 62, "label": "Earthquake"},
        ],
        "vulnerability_score": 58,
        "risk_history": [
            {"year": 2022, "score": 52},
            {"year": 2023, "score": 58},
            {"year": 2024, "score": 63},
            {"year": 2025, "score": 69},
            {"year": 2026, "score": 74},
        ],
        "elevation": 1370.0,
        "nearest_road": 0.3,
        "nearest_hospital": 5.2,
        "nearest_school": 0.6,
        "last_assessed": "2026-09-10",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-006",
        "name": "Tharali Block",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.3480,
        "lng": 79.5950,
        "risk_score": 72,
        "risk_category": "HIGH",
        "urgency": "SHORT_TERM",
        "population": 1876,
        "households": 345,
        "confidence": 68,
        "hazard_scores": [
            {"type": "FLOOD", "score": 79, "label": "Flood"},
            {"type": "LANDSLIDE", "score": 64, "label": "Landslide"},
            {"type": "CLOUDBURST", "score": 59, "label": "Cloudburst"},
        ],
        "vulnerability_score": 63,
        "risk_history": [
            {"year": 2022, "score": 49},
            {"year": 2023, "score": 55},
            {"year": 2024, "score": 61},
            {"year": 2025, "score": 67},
            {"year": 2026, "score": 72},
        ],
        "elevation": 1280.0,
        "nearest_road": 0.5,
        "nearest_hospital": 12.8,
        "nearest_school": 1.4,
        "last_assessed": "2026-08-22",
        "verification_status": "PENDING",
    },
    {
        "id": "HAB-007",
        "name": "Urgam Valley Settlement",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.5530,
        "lng": 79.6240,
        "risk_score": 69,
        "risk_category": "HIGH",
        "urgency": "SHORT_TERM",
        "population": 634,
        "households": 118,
        "confidence": 65,
        "hazard_scores": [
            {"type": "AVALANCHE", "score": 74, "label": "Avalanche"},
            {"type": "LANDSLIDE", "score": 68, "label": "Landslide"},
            {"type": "CLOUDBURST", "score": 54, "label": "Cloudburst"},
        ],
        "vulnerability_score": 71,
        "risk_history": [
            {"year": 2022, "score": 48},
            {"year": 2023, "score": 54},
            {"year": 2024, "score": 59},
            {"year": 2025, "score": 64},
            {"year": 2026, "score": 69},
        ],
        "elevation": 2680.0,
        "nearest_road": 8.4,
        "nearest_hospital": 34.6,
        "nearest_school": 6.2,
        "last_assessed": "2026-08-15",
        "verification_status": "PENDING",
    },
    {
        "id": "HAB-008",
        "name": "Joshimath Ward-7",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.5556,
        "lng": 79.5650,
        "risk_score": 88,
        "risk_category": "CRITICAL",
        "urgency": "IMMEDIATE",
        "population": 5230,
        "households": 1024,
        "confidence": 92,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 96, "label": "Landslide"},
            {"type": "EARTHQUAKE", "score": 74, "label": "Earthquake"},
            {"type": "FLOOD", "score": 62, "label": "Flood"},
        ],
        "vulnerability_score": 72,
        "risk_history": [
            {"year": 2022, "score": 72},
            {"year": 2023, "score": 78},
            {"year": 2024, "score": 82},
            {"year": 2025, "score": 85},
            {"year": 2026, "score": 88},
        ],
        "elevation": 1890.0,
        "nearest_road": 0.1,
        "nearest_hospital": 2.8,
        "nearest_school": 0.4,
        "last_assessed": "2026-09-20",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-009",
        "name": "Pipalkoti Extension",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.4280,
        "lng": 79.4310,
        "risk_score": 62,
        "risk_category": "WATCH",
        "urgency": "MEDIUM_TERM",
        "population": 3120,
        "households": 589,
        "confidence": 72,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 65, "label": "Landslide"},
            {"type": "FLOOD", "score": 58, "label": "Flood"},
            {"type": "CLOUDBURST", "score": 52, "label": "Cloudburst"},
        ],
        "vulnerability_score": 54,
        "risk_history": [
            {"year": 2022, "score": 41},
            {"year": 2023, "score": 46},
            {"year": 2024, "score": 52},
            {"year": 2025, "score": 57},
            {"year": 2026, "score": 62},
        ],
        "elevation": 1310.0,
        "nearest_road": 0.2,
        "nearest_hospital": 8.4,
        "nearest_school": 0.9,
        "last_assessed": "2026-09-01",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-010",
        "name": "Helang Cluster",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.4850,
        "lng": 79.4920,
        "risk_score": 58,
        "risk_category": "WATCH",
        "urgency": "MEDIUM_TERM",
        "population": 1450,
        "households": 268,
        "confidence": 66,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 61, "label": "Landslide"},
            {"type": "FLOOD", "score": 54, "label": "Flood"},
            {"type": "CLOUDBURST", "score": 48, "label": "Cloudburst"},
        ],
        "vulnerability_score": 52,
        "risk_history": [
            {"year": 2022, "score": 38},
            {"year": 2023, "score": 43},
            {"year": 2024, "score": 48},
            {"year": 2025, "score": 53},
            {"year": 2026, "score": 58},
        ],
        "elevation": 1520.0,
        "nearest_road": 0.6,
        "nearest_hospital": 11.2,
        "nearest_school": 1.5,
        "last_assessed": "2026-08-18",
        "verification_status": "PENDING",
    },
    {
        "id": "HAB-011",
        "name": "Nandprayag Riverside",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.3310,
        "lng": 79.3150,
        "risk_score": 66,
        "risk_category": "HIGH",
        "urgency": "MEDIUM_TERM",
        "population": 2780,
        "households": 523,
        "confidence": 70,
        "hazard_scores": [
            {"type": "FLOOD", "score": 74, "label": "Flood"},
            {"type": "LANDSLIDE", "score": 59, "label": "Landslide"},
            {"type": "CLOUDBURST", "score": 55, "label": "Cloudburst"},
        ],
        "vulnerability_score": 60,
        "risk_history": [
            {"year": 2022, "score": 44},
            {"year": 2023, "score": 50},
            {"year": 2024, "score": 55},
            {"year": 2025, "score": 60},
            {"year": 2026, "score": 66},
        ],
        "elevation": 910.0,
        "nearest_road": 0.1,
        "nearest_hospital": 6.8,
        "nearest_school": 0.5,
        "last_assessed": "2026-09-08",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-012",
        "name": "Agastmuni Block",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-RUDR",
        "lat": 30.3810,
        "lng": 79.0340,
        "risk_score": 55,
        "risk_category": "WATCH",
        "urgency": "MEDIUM_TERM",
        "population": 4120,
        "households": 782,
        "confidence": 68,
        "hazard_scores": [
            {"type": "FLOOD", "score": 62, "label": "Flood"},
            {"type": "LANDSLIDE", "score": 51, "label": "Landslide"},
            {"type": "CLOUDBURST", "score": 44, "label": "Cloudburst"},
        ],
        "vulnerability_score": 48,
        "risk_history": [
            {"year": 2022, "score": 35},
            {"year": 2023, "score": 40},
            {"year": 2024, "score": 45},
            {"year": 2025, "score": 50},
            {"year": 2026, "score": 55},
        ],
        "elevation": 780.0,
        "nearest_road": 0.2,
        "nearest_hospital": 4.5,
        "nearest_school": 0.3,
        "last_assessed": "2026-08-25",
        "verification_status": "VERIFIED",
    },
    {
        "id": "HAB-013",
        "name": "Ghat Village",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "district_id": "DIST-UK-CHAM",
        "lat": 30.5190,
        "lng": 79.6580,
        "risk_score": 76,
        "risk_category": "HIGH",
        "urgency": "SHORT_TERM",
        "population": 542,
        "households": 98,
        "confidence": 63,
        "hazard_scores": [
            {"type": "LANDSLIDE", "score": 81, "label": "Landslide"},
            {"type": "AVALANCHE", "score": 68, "label": "Avalanche"},
            {"type": "CLOUDBURST", "score": 62, "label": "Cloudburst"},
        ],
        "vulnerability_score": 74,
        "risk_history": [
            {"year": 2022, "score": 54},
            {"year": 2023, "score": 60},
            {"year": 2024, "score": 65},
            {"year": 2025, "score": 71},
            {"year": 2026, "score": 76},
        ],
        "elevation": 2420.0,
        "nearest_road": 6.8,
        "nearest_hospital": 32.1,
        "nearest_school": 5.4,
        "last_assessed": "2026-08-10",
        "verification_status": "FLAGGED",
    },
]


# ── Hazard / Red Zones (4 polygons) ──

HAZARD_ZONES_DATA = [
    {
        "id": "RZ-001",
        "name": "Khar-Raini Landslide Corridor",
        "polygon_latlng": [
            (30.51, 79.54),
            (30.51, 79.60),
            (30.46, 79.60),
            (30.46, 79.54),
        ],
        "hazard_types": ["LANDSLIDE", "CLOUDBURST", "FLOOD"],
        "composite_risk_score": 92,
        "habitation_count": 3,
        "population_affected": 5097,
        "area_km_sq": 28.4,
        "declared_date": "2024-07-15",
        "last_updated": "2026-09-15",
    },
    {
        "id": "RZ-002",
        "name": "Joshimath Subsidence Zone",
        "polygon_latlng": [
            (30.57, 79.55),
            (30.57, 79.58),
            (30.54, 79.58),
            (30.54, 79.55),
        ],
        "hazard_types": ["LANDSLIDE", "EARTHQUAKE"],
        "composite_risk_score": 89,
        "habitation_count": 2,
        "population_affected": 5864,
        "area_km_sq": 12.6,
        "declared_date": "2023-01-10",
        "last_updated": "2026-09-20",
    },
    {
        "id": "RZ-003",
        "name": "Dungari-Bhandar Flood Plain",
        "polygon_latlng": [
            (30.45, 79.06),
            (30.45, 79.13),
            (30.38, 79.13),
            (30.38, 79.06),
        ],
        "hazard_types": ["FLOOD", "LANDSLIDE", "CLOUDBURST"],
        "composite_risk_score": 81,
        "habitation_count": 2,
        "population_affected": 3026,
        "area_km_sq": 35.2,
        "declared_date": "2025-06-22",
        "last_updated": "2026-09-05",
    },
    {
        "id": "RZ-004",
        "name": "Urgam High-Altitude Risk Zone",
        "polygon_latlng": [
            (30.57, 79.60),
            (30.57, 79.65),
            (30.53, 79.65),
            (30.53, 79.60),
        ],
        "hazard_types": ["AVALANCHE", "LANDSLIDE", "CLOUDBURST"],
        "composite_risk_score": 73,
        "habitation_count": 2,
        "population_affected": 1176,
        "area_km_sq": 18.9,
        "declared_date": "2025-11-08",
        "last_updated": "2026-08-15",
    },
]


# ── Candidate Relocation Sites (8 sites) ──

CANDIDATE_SITES_DATA = [
    {
        "id": "RS-001",
        "name": "Pipalkoti Plateau Site",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "centroid_latlng": (30.4350, 79.4180),
        "bounds_latlng": [(30.440, 79.413), (30.440, 79.423), (30.430, 79.423), (30.430, 79.413)],
        "suitability_score": 82,
        "carrying_capacity": 4500,
        "current_utilization": 0.0,
        "area_hectares": 45.0,
        "elevation": 1280.0,
        "distance_from_hazard": 8.5,
        "road_access": True,
        "water_access": True,
        "electricity_access": True,
        "land_use_type": "Barren / Government",
        "ownership": "State Revenue",
        "status": "SUITABLE",
        "verification_status": "VERIFIED",
        "assigned_habitations": ["HAB-001"],
    },
    {
        "id": "RS-002",
        "name": "Chamoli Town Extension",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "centroid_latlng": (30.4050, 79.3380),
        "bounds_latlng": [(30.410, 79.333), (30.410, 79.343), (30.400, 79.343), (30.400, 79.333)],
        "suitability_score": 78,
        "carrying_capacity": 6200,
        "current_utilization": 12.0,
        "area_hectares": 62.0,
        "elevation": 1050.0,
        "distance_from_hazard": 12.3,
        "road_access": True,
        "water_access": True,
        "electricity_access": True,
        "land_use_type": "Mixed Use",
        "ownership": "Municipal",
        "status": "SUITABLE",
        "verification_status": "VERIFIED",
        "assigned_habitations": ["HAB-002", "HAB-008"],
    },
    {
        "id": "RS-003",
        "name": "Karnprayag South",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "centroid_latlng": (30.2900, 79.2100),
        "bounds_latlng": [(30.295, 79.205), (30.295, 79.215), (30.285, 79.215), (30.285, 79.205)],
        "suitability_score": 74,
        "carrying_capacity": 3200,
        "current_utilization": 0.0,
        "area_hectares": 32.0,
        "elevation": 870.0,
        "distance_from_hazard": 15.8,
        "road_access": True,
        "water_access": True,
        "electricity_access": False,
        "land_use_type": "Agricultural",
        "ownership": "State Revenue",
        "status": "PROVISIONAL",
        "verification_status": "PENDING",
        "assigned_habitations": [],
    },
    {
        "id": "RS-004",
        "name": "Rudraprayag Terrace",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "centroid_latlng": (30.2840, 78.9800),
        "bounds_latlng": [(30.289, 78.975), (30.289, 78.985), (30.279, 78.985), (30.279, 78.975)],
        "suitability_score": 86,
        "carrying_capacity": 5500,
        "current_utilization": 8.0,
        "area_hectares": 55.0,
        "elevation": 610.0,
        "distance_from_hazard": 20.1,
        "road_access": True,
        "water_access": True,
        "electricity_access": True,
        "land_use_type": "Government Reserve",
        "ownership": "State Revenue",
        "status": "SUITABLE",
        "verification_status": "VERIFIED",
        "assigned_habitations": ["HAB-003", "HAB-004"],
    },
    {
        "id": "RS-005",
        "name": "Gopeshwar Bypass Area",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "centroid_latlng": (30.4000, 79.3400),
        "bounds_latlng": [(30.405, 79.335), (30.405, 79.345), (30.395, 79.345), (30.395, 79.335)],
        "suitability_score": 71,
        "carrying_capacity": 2800,
        "current_utilization": 0.0,
        "area_hectares": 28.0,
        "elevation": 1340.0,
        "distance_from_hazard": 6.2,
        "road_access": True,
        "water_access": True,
        "electricity_access": True,
        "land_use_type": "Mixed Use",
        "ownership": "Municipal",
        "status": "PROVISIONAL",
        "verification_status": "IN_PROGRESS",
        "assigned_habitations": [],
    },
    {
        "id": "RS-006",
        "name": "Nandprayag Safe Bench",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "centroid_latlng": (30.3370, 79.3000),
        "bounds_latlng": [(30.342, 79.295), (30.342, 79.305), (30.332, 79.305), (30.332, 79.295)],
        "suitability_score": 68,
        "carrying_capacity": 1800,
        "current_utilization": 0.0,
        "area_hectares": 18.0,
        "elevation": 920.0,
        "distance_from_hazard": 9.7,
        "road_access": True,
        "water_access": False,
        "electricity_access": True,
        "land_use_type": "Agricultural",
        "ownership": "Private / Acquisition Needed",
        "status": "PENDING",
        "verification_status": "PENDING",
        "assigned_habitations": [],
    },
    {
        "id": "RS-007",
        "name": "Agastmuni Heights",
        "district": "Rudraprayag",
        "state": "Uttarakhand",
        "centroid_latlng": (30.3950, 79.0200),
        "bounds_latlng": [(30.400, 79.015), (30.400, 79.025), (30.390, 79.025), (30.390, 79.015)],
        "suitability_score": 76,
        "carrying_capacity": 3800,
        "current_utilization": 5.0,
        "area_hectares": 38.0,
        "elevation": 850.0,
        "distance_from_hazard": 11.4,
        "road_access": True,
        "water_access": True,
        "electricity_access": True,
        "land_use_type": "Barren / Government",
        "ownership": "State Revenue",
        "status": "SUITABLE",
        "verification_status": "VERIFIED",
        "assigned_habitations": ["HAB-012"],
    },
    {
        "id": "RS-008",
        "name": "Tharali Safe Zone",
        "district": "Chamoli",
        "state": "Uttarakhand",
        "centroid_latlng": (30.3580, 79.5780),
        "bounds_latlng": [(30.363, 79.573), (30.363, 79.583), (30.353, 79.583), (30.353, 79.573)],
        "suitability_score": 64,
        "carrying_capacity": 2200,
        "current_utilization": 0.0,
        "area_hectares": 22.0,
        "elevation": 1180.0,
        "distance_from_hazard": 7.3,
        "road_access": True,
        "water_access": True,
        "electricity_access": False,
        "land_use_type": "Agricultural",
        "ownership": "Mixed",
        "status": "PENDING",
        "verification_status": "PENDING",
        "assigned_habitations": [],
    },
]


# ── Infrastructure Assets (12 items) ──

INFRASTRUCTURE_DATA = [
    {"id": "INF-001", "name": "District Hospital Gopeshwar", "type": "HOSPITAL", "lat": 30.4095, "lng": 79.3240, "status": "OPERATIONAL", "capacity": 150, "district": "Chamoli"},
    {"id": "INF-002", "name": "PHC Pipalkoti", "type": "HOSPITAL", "lat": 30.4290, "lng": 79.4280, "status": "OPERATIONAL", "capacity": 30, "district": "Chamoli"},
    {"id": "INF-003", "name": "CHC Joshimath", "type": "HOSPITAL", "lat": 30.5560, "lng": 79.5640, "status": "OPERATIONAL", "capacity": 50, "district": "Chamoli"},
    {"id": "INF-004", "name": "District Hospital Rudraprayag", "type": "HOSPITAL", "lat": 30.2850, "lng": 78.9850, "status": "OPERATIONAL", "capacity": 100, "district": "Rudraprayag"},
    {"id": "INF-005", "name": "GIC Gopeshwar", "type": "SCHOOL", "lat": 30.4110, "lng": 79.3200, "status": "OPERATIONAL", "capacity": 800, "district": "Chamoli"},
    {"id": "INF-006", "name": "GPS Khar", "type": "SCHOOL", "lat": 30.4970, "lng": 79.5580, "status": "OPERATIONAL", "capacity": 120, "district": "Chamoli"},
    {"id": "INF-007", "name": "GHSS Pipalkoti", "type": "SCHOOL", "lat": 30.4300, "lng": 79.4310, "status": "OPERATIONAL", "capacity": 450, "district": "Chamoli"},
    {"id": "INF-008", "name": "GPS Agastmuni", "type": "SCHOOL", "lat": 30.3830, "lng": 79.0380, "status": "OPERATIONAL", "capacity": 280, "district": "Rudraprayag"},
    {"id": "INF-009", "name": "NH-7 Junction Chamoli", "type": "ROAD_JUNCTION", "lat": 30.4040, "lng": 79.3260, "status": "OPERATIONAL", "capacity": None, "district": "Chamoli"},
    {"id": "INF-010", "name": "Joshimath Bypass Junction", "type": "ROAD_JUNCTION", "lat": 30.5520, "lng": 79.5600, "status": "DAMAGED", "capacity": None, "district": "Chamoli"},
    {"id": "INF-011", "name": "Alaknanda Bridge Pipalkoti", "type": "BRIDGE", "lat": 30.4260, "lng": 79.4250, "status": "OPERATIONAL", "capacity": None, "district": "Chamoli"},
    {"id": "INF-012", "name": "Gauchar Airstrip & Helipad", "type": "HELIPAD", "lat": 30.2920, "lng": 79.1550, "status": "OPERATIONAL", "capacity": 12, "district": "Chamoli"},
]


# ── External Data Sources (Synthetic Demo Benchmarks) ──
# Audited: All demo records represent synthetic test feeds modeled on standard agency formats.
# No live production data or fabricated external URLs are implied.

DATA_SOURCES_DATA = [
    {
        "id": "DS-001",
        "name": "CartoSAT Elevation Matrix (10m DEM - Synthetic Benchmark)",
        "provider": "ISRO NRSC (Format Benchmark)",
        "type": "RASTER_DEM",
        "status": "DEMO_ACTIVE",
        "last_sync": "2026-09-28 04:30 IST",
        "records_count": 14200,
        "latency_ms": 42,
        "data_mode": "DEMO",
    },
    {
        "id": "DS-002",
        "name": "Automatic Weather Station Feed (Synthetic Prototype Stream)",
        "provider": "IMD (Format Benchmark)",
        "type": "WEATHER_STATION",
        "status": "DEMO_ACTIVE",
        "last_sync": "2026-09-28 05:45 IST",
        "records_count": 312,
        "latency_ms": 18,
        "data_mode": "DEMO",
    },
    {
        "id": "DS-003",
        "name": "Seismic Telemetry Stream (Synthetic Micro-seismic Simulator)",
        "provider": "USGS (Format Benchmark)",
        "type": "SEISMIC",
        "status": "DEMO_ACTIVE",
        "last_sync": "2026-09-28 05:58 IST",
        "records_count": 1054,
        "latency_ms": 65,
        "data_mode": "DEMO",
    },
    {
        "id": "DS-004",
        "name": "Topographic Basemap Index (Synthetic Survey Grid)",
        "provider": "Survey of India (Format Benchmark)",
        "type": "SATELLITE_OPTICAL",
        "status": "DEMO_ACTIVE",
        "last_sync": "2026-09-27 22:00 IST",
        "records_count": 8900,
        "latency_ms": 55,
        "data_mode": "DEMO",
    },
]


# ── Disaster History Records ──

DISASTER_EVENTS_DATA = [
    {
        "id": "EVT-001",
        "title": "2021 Chamoli Glacial Flash Flood",
        "hazard_type": "FLOOD",
        "severity": "CRITICAL",
        "event_date": "2021-02-07",
        "district": "Chamoli",
        "lat": 30.4850,
        "lng": 79.5850,
        "fatalities": 204,
        "displaced_persons": 1450,
        "description": "Rishi Ganga and Dhauli Ganga gorge flash flood triggered by a massive rock and ice avalanche from Ronti peak.",
    },
    {
        "id": "EVT-002",
        "title": "2023 Joshimath Land Subsidence Crisis",
        "hazard_type": "LANDSLIDE",
        "severity": "CRITICAL",
        "event_date": "2023-01-05",
        "district": "Chamoli",
        "lat": 30.5556,
        "lng": 79.5650,
        "fatalities": 0,
        "displaced_persons": 870,
        "description": "Severe differential subsidence causing deep structural fissures across 9 municipal wards, mandating evacuation.",
    },
]

# ── Detailed Socio-Economic Vulnerability Profiles ──

VULNERABILITY_PROFILES_DATA = [
    {"habitation_id": "HAB-001", "population": 420, "households": 88, "children_share": 0.22, "elderly_share": 0.18, "disability_share": 0.05, "housing_vulnerability": 78.0, "population_density": 210.0, "healthcare_access_score": 25.0, "road_access_score": 30.0, "isolation_score": 75.0, "data_confidence": 75.0},
    {"habitation_id": "HAB-002", "population": 310, "households": 64, "children_share": 0.24, "elderly_share": 0.16, "disability_share": 0.04, "housing_vulnerability": 82.0, "population_density": 180.0, "healthcare_access_score": 20.0, "road_access_score": 20.0, "isolation_score": 82.0, "data_confidence": 70.0},
    {"habitation_id": "HAB-003", "population": 190, "households": 42, "children_share": 0.19, "elderly_share": 0.21, "disability_share": 0.06, "housing_vulnerability": 68.0, "population_density": 140.0, "healthcare_access_score": 35.0, "road_access_score": 40.0, "isolation_score": 65.0, "data_confidence": 65.0},
    {"habitation_id": "HAB-004", "population": 580, "households": 120, "children_share": 0.15, "elderly_share": 0.12, "disability_share": 0.03, "housing_vulnerability": 55.0, "population_density": 290.0, "healthcare_access_score": 40.0, "road_access_score": 50.0, "isolation_score": 60.0, "data_confidence": 80.0},
    {"habitation_id": "HAB-005", "population": 260, "households": 52, "children_share": 0.20, "elderly_share": 0.15, "disability_share": 0.04, "housing_vulnerability": 74.0, "population_density": 130.0, "healthcare_access_score": 25.0, "road_access_score": 25.0, "isolation_score": 78.0, "data_confidence": 70.0},
    {"habitation_id": "HAB-006", "population": 850, "households": 175, "children_share": 0.18, "elderly_share": 0.14, "disability_share": 0.03, "housing_vulnerability": 42.0, "population_density": 420.0, "healthcare_access_score": 70.0, "road_access_score": 75.0, "isolation_score": 30.0, "data_confidence": 85.0},
    {"habitation_id": "HAB-007", "population": 1420, "households": 310, "children_share": 0.17, "elderly_share": 0.13, "disability_share": 0.02, "housing_vulnerability": 38.0, "population_density": 680.0, "healthcare_access_score": 85.0, "road_access_score": 88.0, "isolation_score": 20.0, "data_confidence": 90.0},
    {"habitation_id": "HAB-008", "population": 1120, "households": 245, "children_share": 0.19, "elderly_share": 0.17, "disability_share": 0.04, "housing_vulnerability": 72.0, "population_density": 560.0, "healthcare_access_score": 60.0, "road_access_score": 65.0, "isolation_score": 45.0, "data_confidence": 85.0},
    {"habitation_id": "HAB-009", "population": 480, "households": 105, "children_share": 0.23, "elderly_share": 0.15, "disability_share": 0.05, "housing_vulnerability": 80.0, "population_density": 240.0, "healthcare_access_score": 30.0, "road_access_score": 35.0, "isolation_score": 70.0, "data_confidence": 75.0},
    {"habitation_id": "HAB-010", "population": 390, "households": 82, "children_share": 0.21, "elderly_share": 0.16, "disability_share": 0.04, "housing_vulnerability": 65.0, "population_density": 195.0, "healthcare_access_score": 45.0, "road_access_score": 55.0, "isolation_score": 50.0, "data_confidence": 75.0},
    {"habitation_id": "HAB-011", "population": 670, "households": 148, "children_share": 0.18, "elderly_share": 0.15, "disability_share": 0.03, "housing_vulnerability": 70.0, "population_density": 335.0, "healthcare_access_score": 55.0, "road_access_score": 60.0, "isolation_score": 48.0, "data_confidence": 80.0},
    {"habitation_id": "HAB-012", "population": 520, "households": 115, "children_share": 0.22, "elderly_share": 0.14, "disability_share": 0.04, "housing_vulnerability": 76.0, "population_density": 310.0, "healthcare_access_score": 40.0, "road_access_score": 50.0, "isolation_score": 58.0, "data_confidence": 75.0},
    {"habitation_id": "HAB-013", "population": 730, "households": 160, "children_share": 0.19, "elderly_share": 0.16, "disability_share": 0.03, "housing_vulnerability": 58.0, "population_density": 365.0, "healthcare_access_score": 50.0, "road_access_score": 60.0, "isolation_score": 52.0, "data_confidence": 80.0},
]

EVIDENCE_LAYERS_DATA = [
    {
        "id": "EV-ELEV-SRTM30",
        "name": "CartoSAT / SRTM 30m Digital Elevation Model",
        "evidence_type": "ELEVATION",
        "source_id": "DS-001",
        "data_mode": "PUBLIC",
        "representation_type": "RASTER",
        "spatial_resolution": 30.0,
        "derivation_method": "Direct satellite radar interferometry acquisition via ISRO / USGS",
        "parent_layer_ids": [],
        "quality_score": 92.0,
    },
    {
        "id": "EV-SLOPE-METRIC",
        "name": "Metric Slope Gradient (Degrees)",
        "evidence_type": "SLOPE",
        "source_id": "DS-001",
        "data_mode": "MODELED",
        "representation_type": "RASTER",
        "spatial_resolution": 30.0,
        "derivation_method": "Horn (1981) metric finite-difference gradient with latitude-adjusted cell metric conversion",
        "parent_layer_ids": ["EV-ELEV-SRTM30"],
        "quality_score": 88.0,
    },
    {
        "id": "EV-ASPECT-METRIC",
        "name": "Terrain Aspect (Compass Orientation)",
        "evidence_type": "ASPECT",
        "source_id": "DS-001",
        "data_mode": "MODELED",
        "representation_type": "RASTER",
        "spatial_resolution": 30.0,
        "derivation_method": "Zevenbergen-Thorne / Horn metric compass direction (0-360 degrees)",
        "parent_layer_ids": ["EV-ELEV-SRTM30"],
        "quality_score": 88.0,
    },
    {
        "id": "EV-DIST-ROAD",
        "name": "Proximity to Road Network",
        "evidence_type": "DISTANCE_TO_ROAD",
        "source_id": "DS-004",
        "data_mode": "MODELED",
        "representation_type": "VECTOR",
        "spatial_resolution": 10.0,
        "derivation_method": "PostGIS ST_Distance planar metric calculation from highway lines",
        "parent_layer_ids": [],
        "quality_score": 85.0,
    },
    {
        "id": "EV-DIST-DRAINAGE",
        "name": "Distance to Drainage / River Channels",
        "evidence_type": "DISTANCE_TO_DRAINAGE",
        "source_id": "DS-004",
        "data_mode": "MODELED",
        "representation_type": "VECTOR",
        "spatial_resolution": 15.0,
        "derivation_method": "Hydrological stream network vector buffer and proximity analysis",
        "parent_layer_ids": [],
        "quality_score": 85.0,
    },
    {
        "id": "EV-DIST-FAULT",
        "name": "Distance to Tectonic Fault Lineaments",
        "evidence_type": "DISTANCE_TO_FAULT",
        "source_id": "DS-001",
        "data_mode": "MODELED",
        "representation_type": "VECTOR",
        "spatial_resolution": 50.0,
        "derivation_method": "Geological Survey of India structural fault and thrust zone proximity",
        "parent_layer_ids": [],
        "quality_score": 80.0,
    },
]

HAZARD_MODELS_DATA = [
    {
        "id": "MOD-AHP-001",
        "name": "Analytical Hierarchy Process Multi-Hazard Model",
        "hazard_type": "LANDSLIDE",
        "model_type": "AHP",
        "version": "1.0.0",
        "status": "CONFIGURED",
        "config": {
            "evaluation_status": "CONFIGURED · CONSISTENT",
            "consistency_ratio": 0.042,
            "consistency_acceptable": True,
            "saaty_scale_max": 9,
            "scientific_validation": "UNVALIDATED / PENDING_FIELD_INVENTORY",
            "weights": {
                "slope": 0.35,
                "lithology": 0.25,
                "drainage": 0.15,
                "land_cover": 0.15,
                "aspect": 0.10,
            },
        },
    },
    {
        "id": "MOD-FR-001",
        "name": "Frequency Ratio Landslide Susceptibility Model",
        "hazard_type": "LANDSLIDE",
        "model_type": "FREQUENCY_RATIO",
        "version": "1.0.0",
        "status": "DEMO",
        "config": {
            "framework_status": "FRAMEWORK READY",
            "validation_status": "DEMO / NOT VALIDATED",
            "inventory_source": "Chamoli Historical Landslide Events (DEMO)",
        },
    },
    {
        "id": "MOD-RF-001",
        "name": "Random Forest Susceptibility Pipeline",
        "hazard_type": "LANDSLIDE",
        "model_type": "RANDOM_FOREST",
        "version": "1.0.0",
        "status": "UNTRAINED",
        "config": {
            "production_status": "UNTRAINED / INSUFFICIENT_REAL_DATA",
            "spatial_split": "BLOCK_HOLDOUT",
            "validation_status": "UNTRAINED / INSUFFICIENT_REAL_DATA",
        },
    },
]



def seed_database(db=None) -> dict[str, int]:
    """Run idempotent seed data insertion."""
    owns_db = False
    if db is None:
        db = SessionLocal()
        owns_db = True

    counts = {
        "states": 0,
        "districts": 0,
        "habitations": 0,
        "hazard_zones": 0,
        "candidate_sites": 0,
        "infrastructure": 0,
        "data_sources": 0,
        "disaster_events": 0,
        "relocation_priorities": 0,
        "operational_alerts": 0,
        "vulnerability_profiles": 0,
        "risk_assessments": 0,
        "relocation_assessments": 0,
    }

    try:
        # 1. States & Districts
        for s_data in STATES_AND_DISTRICTS:
            existing_s = db.query(State).filter(State.id == s_data["id"]).first()
            if not existing_s:
                state_obj = State(id=s_data["id"], name=s_data["name"], code=s_data["code"])
                db.add(state_obj)
                db.flush()
                counts["states"] += 1

            for d_data in s_data["districts"]:
                existing_d = db.query(District).filter(District.id == d_data["id"]).first()
                if not existing_d:
                    dist_obj = District(
                        id=d_data["id"],
                        state_id=s_data["id"],
                        name=d_data["name"],
                        headquarters=d_data.get("headquarters"),
                    )
                    db.add(dist_obj)
                    counts["districts"] += 1

        db.flush()

        # 2. Habitations
        for h in HABITATIONS_DATA:
            existing_h = db.query(Habitation).filter(Habitation.id == h["id"]).first()
            pt_geom = from_shape(Point(h["lng"], h["lat"]), srid=4326)
            if not existing_h:
                hab_obj = Habitation(
                    id=h["id"],
                    name=h["name"],
                    district=h["district"],
                    state=h["state"],
                    district_id=h.get("district_id"),
                    geom=pt_geom,
                    risk_score=h["risk_score"],
                    risk_category=h["risk_category"],
                    urgency=h["urgency"],
                    population=h["population"],
                    households=h["households"],
                    confidence=h["confidence"],
                    hazard_scores=h["hazard_scores"],
                    vulnerability_score=h["vulnerability_score"],
                    risk_history=h["risk_history"],
                    elevation=h["elevation"],
                    nearest_road=h["nearest_road"],
                    nearest_hospital=h["nearest_hospital"],
                    nearest_school=h["nearest_school"],
                    last_assessed=h["last_assessed"],
                    verification_status=h["verification_status"],
                )
                db.add(hab_obj)
                counts["habitations"] += 1

        db.flush()

        # 3. Hazard Zones
        for rz in HAZARD_ZONES_DATA:
            existing_rz = db.query(HazardZone).filter(HazardZone.id == rz["id"]).first()
            # Shapely Polygon requires coordinates as (x, y) = (lng, lat)
            coords = [(lng, lat) for lat, lng in rz["polygon_latlng"]]
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            poly_geom = from_shape(Polygon(coords), srid=4326)

            if not existing_rz:
                hz_obj = HazardZone(
                    id=rz["id"],
                    name=rz["name"],
                    geom=poly_geom,
                    hazard_types=rz["hazard_types"],
                    composite_risk_score=rz["composite_risk_score"],
                    habitation_count=rz["habitation_count"],
                    population_affected=rz["population_affected"],
                    area_km_sq=rz["area_km_sq"],
                    source_declared_area_sq_km=rz["area_km_sq"],
                    declared_date=rz["declared_date"],
                    last_updated=rz["last_updated"],
                )
                db.add(hz_obj)
                db.flush()
                area_m2 = db.query(func.ST_Area(func.ST_GeogFromWKB(poly_geom))).scalar()
                if area_m2:
                    hz_obj.computed_area_sq_km = round(area_m2 / 1_000_000.0, 2)
                counts["hazard_zones"] += 1
            else:
                if existing_rz.computed_area_sq_km is None:
                    area_m2 = db.query(func.ST_Area(func.ST_GeogFromWKB(poly_geom))).scalar()
                    if area_m2:
                        existing_rz.computed_area_sq_km = round(area_m2 / 1_000_000.0, 2)
                if existing_rz.source_declared_area_sq_km is None:
                    existing_rz.source_declared_area_sq_km = rz["area_km_sq"]

        db.flush()

        # 4. Candidate Relocation Sites
        for cs in CANDIDATE_SITES_DATA:
            existing_cs = db.query(CandidateSite).filter(CandidateSite.id == cs["id"]).first()
            # Boundary polygon (lng, lat)
            b_coords = [(lng, lat) for lat, lng in cs["bounds_latlng"]]
            if b_coords[0] != b_coords[-1]:
                b_coords.append(b_coords[0])
            poly_geom = from_shape(Polygon(b_coords), srid=4326)
            c_lat, c_lng = cs["centroid_latlng"]
            centroid_geom = from_shape(Point(c_lng, c_lat), srid=4326)

            if not existing_cs:
                cs_obj = CandidateSite(
                    id=cs["id"],
                    name=cs["name"],
                    district=cs["district"],
                    state=cs["state"],
                    geom=poly_geom,
                    centroid=centroid_geom,
                    suitability_score=cs["suitability_score"],
                    carrying_capacity=cs["carrying_capacity"],
                    current_utilization=cs["current_utilization"],
                    area_hectares=cs["area_hectares"],
                    elevation=cs["elevation"],
                    distance_from_hazard=cs["distance_from_hazard"],
                    road_access=cs["road_access"],
                    water_access=cs["water_access"],
                    electricity_access=cs["electricity_access"],
                    land_use_type=cs["land_use_type"],
                    ownership=cs["ownership"],
                    status=cs["status"],
                    verification_status=cs["verification_status"],
                    assigned_habitations=cs["assigned_habitations"],
                )
                db.add(cs_obj)
                counts["candidate_sites"] += 1

        db.flush()

        # 5. Infrastructure Assets
        for inf in INFRASTRUCTURE_DATA:
            existing_inf = db.query(InfrastructureAsset).filter(InfrastructureAsset.id == inf["id"]).first()
            pt_geom = from_shape(Point(inf["lng"], inf["lat"]), srid=4326)
            if not existing_inf:
                inf_obj = InfrastructureAsset(
                    id=inf["id"],
                    name=inf["name"],
                    type=inf["type"],
                    geom=pt_geom,
                    status=inf["status"],
                    capacity=inf["capacity"],
                    district=inf.get("district"),
                )
                db.add(inf_obj)
                counts["infrastructure"] += 1

        db.flush()

        # 6. Data Sources
        for ds in DATA_SOURCES_DATA:
            existing_ds = db.query(DataSource).filter(DataSource.id == ds["id"]).first()
            if not existing_ds:
                ds_obj = DataSource(
                    id=ds["id"],
                    name=ds["name"],
                    provider=ds["provider"],
                    type=ds["type"],
                    status=ds["status"],
                    last_sync=ds["last_sync"],
                    records_count=ds["records_count"],
                    latency_ms=ds["latency_ms"],
                    data_mode=ds.get("data_mode", "DEMO"),
                )
                db.add(ds_obj)
                counts["data_sources"] += 1

        db.flush()

        # 7. Disaster Events
        for de in DISASTER_EVENTS_DATA:
            existing_de = db.query(DisasterEvent).filter(DisasterEvent.id == de["id"]).first()
            pt_geom = from_shape(Point(de["lng"], de["lat"]), srid=4326) if "lat" in de else None
            if not existing_de:
                de_obj = DisasterEvent(
                    id=de["id"],
                    title=de["title"],
                    hazard_type=de["hazard_type"],
                    severity=de["severity"],
                    event_date=de["event_date"],
                    district=de["district"],
                    geom=pt_geom,
                    fatalities=de["fatalities"],
                    displaced_persons=de["displaced_persons"],
                    description=de["description"],
                )
                db.add(de_obj)
                counts["disaster_events"] += 1

        # 8. Relocation Priorities (auto-populate from habitations and candidate sites)
        for h in HABITATIONS_DATA:
            existing_rp = db.query(RelocationPriority).filter(RelocationPriority.habitation_id == h["id"]).first()
            if not existing_rp:
                assigned_site = None
                for cs in CANDIDATE_SITES_DATA:
                    if h["id"] in cs["assigned_habitations"]:
                        assigned_site = cs
                        break

                rp_obj = RelocationPriority(
                    habitation_id=h["id"],
                    habitation_name=h["name"],
                    urgency=h["urgency"],
                    risk_score=h["risk_score"],
                    population=h["population"],
                    district=h["district"],
                    assigned_site_id=assigned_site["id"] if assigned_site else None,
                    assigned_site_name=assigned_site["name"] if assigned_site else None,
                    estimated_cost=round(h["population"] * 0.45, 1),
                    timeline_months=6 if h["urgency"] == "IMMEDIATE" else 18 if h["urgency"] == "SHORT_TERM" else 36,
                )
                db.add(rp_obj)
                counts["relocation_priorities"] += 1

        # 9. Operational Alerts
        alerts_seed = [
            ("ALERT-001", "Khar Village landslide sensor alert: Inclinometer threshold exceeded by 14%", "ESCALATION", "CRITICAL", "2026-09-28T05:30:00Z", "HAB-001"),
            ("ALERT-002", "Raini Settlement flood warning: Dhauliganga river discharge +35% above normal", "WEATHER", "CRITICAL", "2026-09-28T04:45:00Z", "HAB-002"),
            ("ALERT-003", "Joshimath Ward-7 ground subsidence telemetry updated: +4mm movement in 48h", "ESCALATION", "CRITICAL", "2026-09-28T03:15:00Z", "HAB-008"),
            ("ALERT-004", "Pipalkoti Plateau candidate site clearance verified by PWD survey team", "VERIFICATION", "SAFE", "2026-09-27T18:00:00Z", None),
            ("ALERT-005", "Dungari Hamlet road access partially blocked by minor debris flow at KM 14", "FIELD_UPDATE", "HIGH", "2026-09-27T14:20:00Z", "HAB-003"),
            ("ALERT-006", "Relocation plan batch #4 approved by District Collector Chamoli", "PRIORITY_CHANGE", "SAFE", "2026-09-27T11:00:00Z", None),
            ("ALERT-007", "IMD issues Orange Alert for Chamoli, Rudraprayag, and Pithoragarh districts", "WEATHER", "HIGH", "2026-09-27T08:30:00Z", None),
            ("ALERT-008", "Helang cluster geotechnical survey report uploaded by CBRI Roorkee", "FIELD_UPDATE", "WATCH", "2026-09-26T16:45:00Z", "HAB-010"),
        ]
        for aid, msg, atype, asev, atime, ahab in alerts_seed:
            existing_al = db.query(OperationalAlert).filter(OperationalAlert.id == aid).first()
            if not existing_al:
                al_obj = OperationalAlert(
                    id=aid,
                    message=msg,
                    type=atype,
                    severity=asev,
                    timestamp=atime,
                    habitation_id=ahab,
                    read=False,
                )
                db.add(al_obj)
                counts["operational_alerts"] += 1

        # 10. Socio-Economic Vulnerability Profiles
        for vp_data in VULNERABILITY_PROFILES_DATA:
            existing_vp = db.query(VulnerabilityProfile).filter(VulnerabilityProfile.habitation_id == vp_data["habitation_id"]).first()
            if not existing_vp:
                vp_obj = VulnerabilityProfile(
                    id=str(uuid4()),
                    habitation_id=vp_data["habitation_id"],
                    population=vp_data["population"],
                    households=vp_data["households"],
                    children_share=vp_data["children_share"],
                    elderly_share=vp_data["elderly_share"],
                    disability_share=vp_data["disability_share"],
                    housing_vulnerability=vp_data["housing_vulnerability"],
                    population_density=vp_data["population_density"],
                    healthcare_access_score=vp_data["healthcare_access_score"],
                    road_access_score=vp_data["road_access_score"],
                    isolation_score=vp_data["isolation_score"],
                    data_confidence=vp_data["data_confidence"],
                    data_mode="DEMO",
                    raw_attributes={"survey_type": "CENSUS_SDMA_SAMPLE", "year": 2025},
                )
                db.add(vp_obj)
                counts["vulnerability_profiles"] += 1

        db.flush()

        # 10.5. Frozen Candidate Discovery Run & Parcels for Raini (HAB-002)
        # Real discovered parcel count across 706.86 km² AOI is 182 candidate parcels (28,754.5 ha feasible area)
        existing_run = db.query(CandidateDiscoveryRun).filter(CandidateDiscoveryRun.id == "CDR-8E12008ADCC0").first()
        if not existing_run:
            now_freeze = datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc)
            cd_run = CandidateDiscoveryRun(
                id="CDR-8E12008ADCC0",
                origin_habitation_id="HAB-002",
                analysis_version="PRAYAAS-CANDIDATE-1.0",
                config_version="1.0.0",
                search_radius_km=15.0,
                status="COMPLETED",
                started_at=now_freeze,
                finished_at=now_freeze,
                created_at=now_freeze,
                updated_at=now_freeze,
                cells_evaluated=70686,
                cells_excluded=41932,
                total_aoi_area_sq_km=706.86,
                excluded_area_sq_km=419.32,
                feasible_area_sq_km=287.54,
                feasible_percent=40.7,
                candidate_count=182,
            )
            db.add(cd_run)
            counts["candidate_discovery_runs"] = counts.get("candidate_discovery_runs", 0) + 1

            p_poly = MultiPolygon([Polygon([(79.55, 30.50), (79.56, 30.50), (79.56, 30.51), (79.55, 30.51), (79.55, 30.50)])])
            p_geom = from_shape(p_poly, srid=4326)
            c_geom = from_shape(Point(79.555, 30.505), srid=4326)

            parcels_data = [
                {
                    "id": "PARCEL-5958B764DA60",
                    "rank": 1,
                    "area_hectares": 20.0,
                    "area_sq_km": 0.20,
                    "distance_km": 0.46,
                    "mean_slope_degrees": 8.5,
                    "suitability_score": 88.5,
                    "robustness_score": 75.0,
                    "rank_stability": 95.0,
                    "confidence_score": 75.0,
                    "criteria_scores": {"ROAD_ACCESS": 85.0, "WATER_ACCESS": 80.0},
                    "reason_codes": ["OPTIMAL_DISTANCE", "SAFE_SLOPE"],
                    "limitations": ["ROAD_CONNECTIVITY_GAP"],
                },
                {
                    "id": "PARCEL-E3247A11E0EC",
                    "rank": 2,
                    "area_hectares": 2.0,
                    "area_sq_km": 0.02,
                    "distance_km": 9.35,
                    "mean_slope_degrees": 9.9,
                    "suitability_score": 91.2,
                    "robustness_score": 61.5,
                    "rank_stability": 85.0,
                    "confidence_score": 37.8,
                    "criteria_scores": {"ROAD_ACCESS": 70.0, "WATER_ACCESS": 75.0},
                    "reason_codes": ["HIGH_SUITABILITY"],
                    "limitations": ["LIMITED_AREA"],
                },
                {
                    "id": "PARCEL-287BBE825053",
                    "rank": 3,
                    "area_hectares": 18.0,
                    "area_sq_km": 0.18,
                    "distance_km": 8.85,
                    "mean_slope_degrees": 11.0,
                    "suitability_score": 85.0,
                    "robustness_score": 68.0,
                    "rank_stability": 88.0,
                    "confidence_score": 60.0,
                    "criteria_scores": {"ROAD_ACCESS": 65.0, "WATER_ACCESS": 70.0},
                    "reason_codes": ["EXPANSION_CAPACITY"],
                    "limitations": ["MODERATE_SLOPE"],
                },
            ]

            for pd in parcels_data:
                existing_p = db.query(CandidateParcel).filter(CandidateParcel.id == pd["id"]).first()
                if not existing_p:
                    cp_obj = CandidateParcel(
                        id=pd["id"],
                        discovery_run_id="CDR-8E12008ADCC0",
                        origin_habitation_id="HAB-002",
                        geom=p_geom,
                        centroid=c_geom,
                        area_sq_km=pd["area_sq_km"],
                        area_hectares=pd["area_hectares"],
                        distance_from_origin_km=pd["distance_km"],
                        mean_slope_degrees=pd["mean_slope_degrees"],
                        suitability_score=pd["suitability_score"],
                        robustness_score=pd["robustness_score"],
                        rank_stability=pd["rank_stability"],
                        rank=pd["rank"],
                        status="REQUIRES_FIELD_REVIEW",
                        confidence_score=pd["confidence_score"],
                        exclusion_summary={"SLOPE": "PASS", "HAZARD": "PASS", "SETTLEMENT": "PASS"},
                        criteria_scores=pd["criteria_scores"],
                        reason_codes=pd["reason_codes"],
                        limitations=pd["limitations"],
                        explanation={},
                        data_mode=DataMode.MODELED.value,
                        created_at=now_freeze,
                        updated_at=now_freeze,
                    )
                    db.add(cp_obj)
                    counts["candidate_parcels"] = counts.get("candidate_parcels", 0) + 1

        db.flush()

        # 11. Initial Risk and Relocation Assessments
        risk_engine = RiskEngine(db)
        relocation_engine = RelocationEngine(db)
        for h in HABITATIONS_DATA:
            existing_ra = db.query(RiskAssessment).filter(RiskAssessment.habitation_id == h["id"]).first()
            if not existing_ra:
                risk_engine.assess_habitation(h["id"])
                counts["risk_assessments"] += 1

            existing_rel = db.query(RelocationAssessment).filter(RelocationAssessment.habitation_id == h["id"]).first()
            if not existing_rel:
                relocation_engine.assess_habitation(h["id"])
                counts["relocation_assessments"] += 1

        # 12. Evidence Layers (Provenance & Derivative Layers)
        for el_data in EVIDENCE_LAYERS_DATA:
            existing_el = db.query(EvidenceLayer).filter(EvidenceLayer.id == el_data["id"]).first()
            if not existing_el:
                el_obj = EvidenceLayer(
                    id=el_data["id"],
                    name=el_data["name"],
                    evidence_type=el_data["evidence_type"],
                    source_id=el_data.get("source_id"),
                    data_mode=el_data["data_mode"],
                    representation_type=el_data["representation_type"],
                    spatial_resolution=el_data.get("spatial_resolution"),
                    derivation_method=el_data.get("derivation_method"),
                    parent_layer_ids=el_data.get("parent_layer_ids", []),
                    quality_score=el_data.get("quality_score"),
                )
                db.add(el_obj)
                counts["evidence_layers"] = counts.get("evidence_layers", 0) + 1

        # 13. Hazard Models Registry
        for hm_data in HAZARD_MODELS_DATA:
            existing_hm = db.query(HazardModel).filter(HazardModel.id == hm_data["id"]).first()
            if not existing_hm:
                hm_obj = HazardModel(
                    id=hm_data["id"],
                    name=hm_data["name"],
                    hazard_type=hm_data["hazard_type"],
                    model_type=hm_data["model_type"],
                    version=hm_data["version"],
                    status=hm_data["status"],
                    config=hm_data["config"],
                )
                db.add(hm_obj)
                counts["hazard_models"] = counts.get("hazard_models", 0) + 1

        db.commit()
        logger.info(f"Seed completed successfully: {counts}")
        return counts
    except Exception as exc:
        db.rollback()
        logger.error(f"Error seeding database: {exc}")
        raise
    finally:
        if owns_db:
            db.close()


if __name__ == "__main__":
    res = seed_database()
    print("Deterministic Chamoli Seed Results:", res)
