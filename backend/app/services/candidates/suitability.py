"""Soft Suitability MCDA Engine for Candidate Parcels (PRAYAAS-CANDIDATE-1.0).

Calculates multi-criteria suitability only for cells that survived hard exclusions.
Implements available-component weighted normalization so missing criteria NEVER equal zero.
Calculates decoupled confidence score based on data completeness, resolution, and provenance.
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

from app.services.candidates.config import CandidateDiscoveryConfig, DEFAULT_CANDIDATE_CONFIG


@dataclass
class SuitabilityEvaluationResult:
    """Suitability and confidence scores for a feasible cell or candidate parcel."""

    composite_score: float
    confidence_score: float
    criterion_scores: dict[str, float]  # Available normalized 0-100 scores
    missing_criteria: list[str] = field(default_factory=list)
    available_weights_sum: float = 1.0


class SoftSuitabilityEngine:
    """Evaluates multi-criteria suitability using piecewise utility curves and available-weight MCDA."""

    def __init__(self, config: CandidateDiscoveryConfig = DEFAULT_CANDIDATE_CONFIG) -> None:
        self.config = config

    def evaluate(
        self,
        slope_deg: float,
        dist_to_hazard_km: float,
        dist_to_road_km: float | None,
        dist_to_health_km: float | None,
        dist_to_school_km: float | None,
        dist_to_water_km: float | None,
        dist_to_origin_km: float,
        unknown_exclusion_count: int = 0,
        is_demo_source: bool = False,
        critical_unknown_count: int = 0,
        resolution_meters: float = 100.0,
    ) -> SuitabilityEvaluationResult:
        """Evaluates MCDA suitability and confidence for a feasible spatial point."""
        scores: dict[str, float] = {}
        missing: list[str] = []

        # 1. SAFETY MARGIN (Composite of distance from mapped hazard + slope buffer)
        # Hazard distance utility: > 1.5 km = 100, 1.0 km = 85, 0.5 km = 65, 0.2 km = 40
        if dist_to_hazard_km >= 1.5:
            hazard_safety = 100.0
        elif dist_to_hazard_km >= 0.8:
            hazard_safety = 85.0
        elif dist_to_hazard_km >= 0.4:
            hazard_safety = 70.0
        else:
            hazard_safety = 45.0

        # Slope safety buffer (<12 deg = 100, 12-18 = 80, 18-25 = 55)
        if slope_deg <= 12.0:
            slope_safety = 100.0
        elif slope_deg <= 18.0:
            slope_safety = 80.0
        else:
            slope_safety = 55.0

        scores["SAFETY_MARGIN"] = round((hazard_safety * 0.60) + (slope_safety * 0.40), 1)

        # 2. SLOPE PREFERENCE (Gentle terrain preferred for habitation infrastructure)
        if 2.0 <= slope_deg <= 10.0:
            scores["SLOPE_PREFERENCE"] = 100.0
        elif slope_deg < 2.0:
            scores["SLOPE_PREFERENCE"] = 92.0  # Very flat may need drainage planning
        elif 10.0 < slope_deg <= 16.0:
            scores["SLOPE_PREFERENCE"] = 80.0
        elif 16.0 < slope_deg <= 22.0:
            scores["SLOPE_PREFERENCE"] = 60.0
        else:
            scores["SLOPE_PREFERENCE"] = 40.0

        # 3. ROAD ACCESS (Monotonic decreasing)
        if dist_to_road_km is not None:
            curve = self.config.distance_curves.get("ROAD_ACCESS")
            scores["ROAD_ACCESS"] = curve.evaluate(dist_to_road_km) if curve else 70.0
        else:
            missing.append("ROAD_ACCESS")

        # 4. HEALTHCARE ACCESS (Monotonic decreasing)
        if dist_to_health_km is not None:
            curve = self.config.distance_curves.get("HEALTHCARE_ACCESS")
            scores["HEALTHCARE_ACCESS"] = curve.evaluate(dist_to_health_km) if curve else 65.0
        else:
            missing.append("HEALTHCARE_ACCESS")

        # 5. EDUCATION ACCESS (Monotonic decreasing)
        if dist_to_school_km is not None:
            curve = self.config.distance_curves.get("EDUCATION_ACCESS")
            scores["EDUCATION_ACCESS"] = curve.evaluate(dist_to_school_km) if curve else 65.0
        else:
            missing.append("EDUCATION_ACCESS")

        # 6. WATER ACCESS (Monotonic decreasing)
        if dist_to_water_km is not None:
            curve = self.config.distance_curves.get("WATER_ACCESS")
            scores["WATER_ACCESS"] = curve.evaluate(dist_to_water_km) if curve else 70.0
        else:
            missing.append("WATER_ACCESS")

        # 7. DISTANCE FROM ORIGIN (Optimal range: avoid dislocation while staying safe)
        curve = self.config.distance_curves.get("DISTANCE_FROM_ORIGIN")
        scores["DISTANCE_FROM_ORIGIN"] = curve.evaluate(dist_to_origin_km) if curve else 75.0

        # ── Weighted Available-Component MCDA Formula ──
        total_weight = 0.0
        weighted_sum = 0.0
        for crit, score in scores.items():
            w = self.config.criteria_weights.get(crit, 0.0)
            weighted_sum += (w * score)
            total_weight += w

        composite_score = round(weighted_sum / max(0.001, total_weight), 1)

        # ── Decoupled Scientific Confidence Score (Task 5.5 Principles) ──
        # Anchored to provenance, coverage, resolution, and critical exclusion completeness
        base_confidence = 90.0
        if is_demo_source:
            base_confidence -= 15.0  # DEMO dataset provenance penalty

        # Resolution penalty (finer resolution yields higher confidence)
        if resolution_meters > 50.0:
            base_confidence -= min(5.0, round((resolution_meters - 50.0) / 30.0, 1))

        # Minor penalty for missing soft criteria (e.g. secondary education or road distance)
        missing_criteria_penalty = len(missing) * 3.0

        # Critical exclusion UNKNOWN penalty:
        # Critical missing safety evidence (flood, protected area, restricted land, river buffer)
        # severely degrades confidence far more than minor missing soft criteria.
        critical_unknown_penalty = critical_unknown_count * 7.5

        # Non-critical unknown exclusions
        non_critical_unknowns = max(0, unknown_exclusion_count - critical_unknown_count)
        general_unknown_penalty = non_critical_unknowns * 2.5

        total_penalty = missing_criteria_penalty + critical_unknown_penalty + general_unknown_penalty
        confidence_score = max(20.0, min(95.0, round(base_confidence - total_penalty, 1)))

        return SuitabilityEvaluationResult(
            composite_score=composite_score,
            confidence_score=confidence_score,
            criterion_scores=scores,
            missing_criteria=missing,
            available_weights_sum=round(total_weight, 3),
        )
