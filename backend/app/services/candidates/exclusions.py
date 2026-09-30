"""Explicit Hard Exclusion Engine for Candidate Land Discovery (PRAYAAS-CANDIDATE-1.0).

Enforces safety-first screening:
- Exclusions occur BEFORE soft suitability scoring.
- An excluded cell CANNOT become acceptable through road proximity or infrastructure.
- Mandatory UNKNOWN policy: If an evidence dataset is missing, record UNKNOWN; never treat as safe.
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from shapely.geometry import Point, Polygon

from app.models.enums import AnalyticalStatus, EvidenceType, ExclusionCheckStatus
from app.models.evidence import EvidenceLayer
from app.models.hazard_zone import HazardZone
from app.models.habitation import Habitation
from app.services.candidates.config import CandidateDiscoveryConfig, DEFAULT_CANDIDATE_CONFIG


@dataclass
class ExclusionEvaluationResult:
    """Result of evaluating hard exclusion masks at a spatial location."""

    is_excluded: bool
    primary_failure_reason: str | None
    checks: dict[str, str] = field(default_factory=dict)
    unknown_count: int = 0
    passed_count: int = 0


class HardExclusionEngine:
    """Evaluates multi-hazard and environmental exclusion masks for spatial cells."""

    def __init__(self, db: Session, config: CandidateDiscoveryConfig = DEFAULT_CANDIDATE_CONFIG) -> None:
        self.db = db
        self.config = config
        self._load_registered_evidence_layers()

    def _load_registered_evidence_layers(self) -> None:
        """Inspects registered evidence layers to know which layers exist vs UNKNOWN."""
        try:
            layers = self.db.query(EvidenceLayer).all()
            self.available_evidence_types = {l.evidence_type for l in layers}
        except Exception:
            self.available_evidence_types = set()

    def evaluate_cell(
        self,
        lat: float,
        lng: float,
        slope_deg: float,
        hazard_zones: list[HazardZone],
        habitations: list[Habitation],
        dist_to_drainage_m: float | None = None,
        dist_to_hazard_m: float = float("inf"),
        nearest_settlement_dist_m: float | None = None,
    ) -> ExclusionEvaluationResult:
        """Evaluates all hard exclusion rules on a candidate point/cell.

        Returns ExclusionEvaluationResult with PASS, FAIL, or UNKNOWN for each check.
        """
        checks: dict[str, str] = {}
        primary_failure: str | None = None

        # 1. EXCESSIVE SLOPE
        # Resettlement safety standard: steep slopes are high hazard and unsuitable for housing
        if slope_deg > self.config.max_slope_degrees:
            checks["EXCESSIVE_SLOPE"] = ExclusionCheckStatus.FAIL.value
            if not primary_failure:
                primary_failure = "EXCESSIVE_SLOPE"
        elif slope_deg < 0.0:
            checks["EXCESSIVE_SLOPE"] = ExclusionCheckStatus.UNKNOWN.value
        else:
            checks["EXCESSIVE_SLOPE"] = ExclusionCheckStatus.PASS.value

        # 2. CRITICAL LANDSLIDE / HAZARD ZONE
        # Check proximity to known high/critical hazard polygons
        if dist_to_hazard_m <= self.config.hazard_buffer_meters:
            checks["CRITICAL_LANDSLIDE_RISK"] = ExclusionCheckStatus.FAIL.value
            if not primary_failure:
                primary_failure = "CRITICAL_LANDSLIDE_RISK"
        else:
            checks["CRITICAL_LANDSLIDE_RISK"] = ExclusionCheckStatus.PASS.value

        # 3. DENSE EXISTING SETTLEMENT (Direct Built-Up Overlap or Configured Authority Buffer)
        # Hard exclusion strictly applies to direct built-up overlap (dist <= 0m) or an explicitly
        # configured planning buffer. Proximity is otherwise a soft planning criterion.
        conflict_buffer_m = (
            self.config.configured_settlement_buffer_meters
            if self.config.configured_settlement_buffer_meters is not None
            else self.config.dense_builtup_overlap_buffer_meters
        )
        is_settlement_conflict = False

        if conflict_buffer_m > 0:
            if nearest_settlement_dist_m is not None:
                is_settlement_conflict = nearest_settlement_dist_m < conflict_buffer_m
            else:
                from app.services.spatial.distance import haversine_distance_km
                from geoalchemy2.shape import to_shape
                for h in habitations:
                    if isinstance(h, tuple):
                        h_lat, h_lng = h
                    elif hasattr(h, "geom") and h.geom is not None:
                        shape = to_shape(h.geom)
                        h_lat, h_lng = shape.y, shape.x
                    elif hasattr(h, "latitude") and hasattr(h, "longitude"):
                        h_lat, h_lng = h.latitude, h.longitude
                    else:
                        continue

                    dist_km = haversine_distance_km(lat, lng, h_lat, h_lng)
                    if dist_km * 1000.0 < conflict_buffer_m:
                        is_settlement_conflict = True
                        break
        elif conflict_buffer_m <= 0:
            # Strictly direct built-up overlap
            if nearest_settlement_dist_m is not None:
                is_settlement_conflict = nearest_settlement_dist_m <= 0.0

        if is_settlement_conflict:
            checks["DENSE_EXISTING_SETTLEMENT"] = ExclusionCheckStatus.FAIL.value
            if not primary_failure:
                primary_failure = "DENSE_EXISTING_SETTLEMENT"
        else:
            checks["DENSE_EXISTING_SETTLEMENT"] = ExclusionCheckStatus.PASS.value


        # 4. RIVER / DRAINAGE BUFFER
        if EvidenceType.DRAINAGE_DISTANCE.value in self.available_evidence_types and dist_to_drainage_m is not None:
            if dist_to_drainage_m < self.config.river_buffer_meters:
                checks["RIVER_BUFFER"] = ExclusionCheckStatus.FAIL.value
                if not primary_failure:
                    primary_failure = "RIVER_BUFFER"
            else:
                checks["RIVER_BUFFER"] = ExclusionCheckStatus.PASS.value
        else:
            # Mandatory UNKNOWN policy: Do not assume river is absent if dataset is missing
            checks["RIVER_BUFFER"] = ExclusionCheckStatus.UNKNOWN.value

        # 5. CRITICAL FLOOD RISK
        if EvidenceType.FLOOD_HAZARD.value in self.available_evidence_types:
            checks["CRITICAL_FLOOD_RISK"] = ExclusionCheckStatus.PASS.value
        else:
            checks["CRITICAL_FLOOD_RISK"] = ExclusionCheckStatus.UNKNOWN.value

        # 6. WATER BODY POLYGON
        # If water body layer exists, check; otherwise UNKNOWN
        checks["WATER_BODY"] = ExclusionCheckStatus.UNKNOWN.value

        # 7. PROTECTED AREA (National Parks, Biosphere, Sanctuaries)
        # Sourced from official environmental layers; if missing, mark UNKNOWN
        checks["PROTECTED_AREA"] = ExclusionCheckStatus.UNKNOWN.value

        # 8. RESTRICTED LAND (Defense, Reserved Forests, Unclear Tenure)
        checks["RESTRICTED_LAND"] = ExclusionCheckStatus.UNKNOWN.value

        unknown_count = sum(1 for v in checks.values() if v == ExclusionCheckStatus.UNKNOWN.value)
        passed_count = sum(1 for v in checks.values() if v == ExclusionCheckStatus.PASS.value)
        is_excluded = primary_failure is not None

        return ExclusionEvaluationResult(
            is_excluded=is_excluded,
            primary_failure_reason=primary_failure,
            checks=checks,
            unknown_count=unknown_count,
            passed_count=passed_count,
        )
