"""Configuration and parameters for Candidate Relocation Discovery (PRAYAAS-CANDIDATE-1.0).

Encapsulates hard exclusion criteria, soft suitability weights, distance utility curves,
and robustness evaluation thresholds. Ensures zero scattered constants.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.models.enums import DistanceUtilityCurveType, RobustnessLevel
from app.services.hazard_models.ahp import check_ahp_consistency


class DistanceUtilityCurve(BaseModel):
    """Configuration for piecewise or monotonic distance utility functions."""

    curve_type: DistanceUtilityCurveType
    min_dist_km: float = 0.0
    optimal_min_km: float = 0.0
    optimal_max_km: float = 5.0
    max_acceptable_km: float = 15.0

    def evaluate(self, dist_km: float) -> float:
        """Evaluates distance to a normalized 0-100 utility score."""
        d = max(0.0, dist_km)
        if self.curve_type == DistanceUtilityCurveType.MONOTONIC_DECREASING:
            # Closer is better (e.g. road access, health center)
            if d <= self.optimal_min_km:
                return 100.0
            if d >= self.max_acceptable_km:
                return 0.0
            span = self.max_acceptable_km - self.optimal_min_km
            fraction = (self.max_acceptable_km - d) / max(0.001, span)
            return round(fraction * 100.0, 1)

        elif self.curve_type == DistanceUtilityCurveType.OPTIMAL_RANGE:
            # Too close may be dangerous or disruptive; too far causes socio-economic alienation
            if self.optimal_min_km <= d <= self.optimal_max_km:
                return 100.0
            elif d < self.optimal_min_km:
                # Penalty for being too close to the disaster-stricken origin
                score = (d / max(0.001, self.optimal_min_km)) * 100.0
                return round(max(20.0, score), 1)
            else:
                # Penalty for excessive relocation displacement distance
                if d >= self.max_acceptable_km:
                    return 15.0
                span = self.max_acceptable_km - self.optimal_max_km
                fraction = (self.max_acceptable_km - d) / max(0.001, span)
                return round(max(15.0, fraction * 100.0), 1)

        elif self.curve_type == DistanceUtilityCurveType.MONOTONIC_INCREASING:
            # Farther is safer (e.g. distance from active fault or river)
            if d >= self.optimal_max_km:
                return 100.0
            if d <= self.min_dist_km:
                return 0.0
            span = self.optimal_max_km - self.min_dist_km
            return round(((d - self.min_dist_km) / max(0.001, span)) * 100.0, 1)

        return 50.0


class CandidateDiscoveryConfig(BaseModel):
    """Versioned configuration for candidate relocation land discovery."""

    analysis_version: str = "PRAYAAS-CANDIDATE-1.0"
    config_version: str = "1.0.0"

    # Search & Grid Area
    default_search_radius_km: float = 15.0
    min_search_radius_km: float = 5.0
    max_search_radius_km: float = 50.0
    grid_resolution_meters: float = 100.0  # Reproducible analysis metric grid cell size (1 cell = 1.0 ha)
    default_analysis_resolution_meters: float = 100.0
    effective_source_resolution_meters: float = 30.0  # Coarsest critical source layer (e.g. SRTM 30m DEM)
    min_analysis_resolution_meters: float = 30.0
    max_analysis_resolution_meters: float = 250.0
    min_parcel_area_hectares: float = 2.0  # Minimum 2 ha contiguous parcel size (at 100m res, requires >= 2 cells)
    min_parcel_area_sq_km: float = 0.02

    # Contiguity & Geometry Feasibility Thresholds (Task 6 Realism)
    connectivity: int = 4  # Edge/shared-side 4-connectivity (orthogonal only; corner-only diagonal rejected)
    min_effective_width_meters: float = 30.0  # Minimum buildable width for community resettlement
    max_aspect_ratio: float = 6.0  # Maximum length-to-width ratio (prevents extreme slivers)
    min_compactness_ratio: float = 0.08  # Polsby-Popper 4*pi*Area/Perimeter^2 threshold

    # Candidate Eligibility & Suitability Segmentation (Task 6 Parcelization)
    minimum_candidate_suitability: float = 60.0  # Configurable eligibility threshold; cells below remain FEASIBLE
    candidate_core_threshold: float = 70.0  # Score threshold for candidate seed cores
    candidate_growth_threshold: float = 55.0  # Minimum neighbor score to join expanding candidate parcel
    max_planning_scale_parcel_ha: float = 250.0  # PRAYAAS planning-scale segmentation parameter (not statutory max)

    # Hard Exclusion Thresholds
    max_slope_degrees: float = 25.0  # Himalayan resettlement guideline: slope > 25 deg is excluded
    river_buffer_meters: float = 100.0  # Planning buffer from major drainage channels
    dense_builtup_overlap_buffer_meters: float = 0.0  # Hard exclusion strictly applies to built-up OVERLAP
    configured_settlement_buffer_meters: float | None = None  # Non-statutory authority planning buffer (if explicitly configured)
    hazard_buffer_meters: float = 150.0  # Buffer around mapped high/critical hazard polygons

    # Critical UNKNOWN Promotion Guard
    critical_exclusion_types: list[str] = Field(
        default_factory=lambda: [
            "CRITICAL_FLOOD_RISK",
            "PROTECTED_AREA",
            "RESTRICTED_LAND",
            "RIVER_BUFFER",
        ]
    )
    unresolved_unknown_status: str = "REQUIRES_FIELD_REVIEW"

    def determine_analysis_resolution(
        self,
        effective_source_resolution_m: float = 30.0,
        requested_resolution_m: float | None = None,
    ) -> tuple[float, float]:
        """Determines a defensible analysis resolution that never claims precision finer than the coarsest critical layer.

        Returns:
            (analysis_resolution_meters, effective_source_resolution_meters)
        """
        effective_source = max(10.0, effective_source_resolution_m)
        target = requested_resolution_m or self.default_analysis_resolution_meters
        # Analysis resolution must be >= effective source resolution and <= max allowed
        chosen = max(effective_source, min(self.max_analysis_resolution_meters, target))
        return round(chosen, 1), round(effective_source, 1)

    # Soft Criteria Weights (sum to 1.0)
    criteria_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "SAFETY_MARGIN": 0.35,
            "SLOPE_PREFERENCE": 0.20,
            "ROAD_ACCESS": 0.15,
            "HEALTHCARE_ACCESS": 0.10,
            "EDUCATION_ACCESS": 0.05,
            "WATER_ACCESS": 0.10,
            "DISTANCE_FROM_ORIGIN": 0.05,
        }
    )

    # Pairwise AHP Matrix for criteria weights (Consistent with CR <= 0.10)
    ahp_pairwise_matrix: list[list[float]] = Field(
        default_factory=lambda: [
            # SAFETY, SLOPE, ROAD, HEALTH, EDU, WATER, ORIGIN_DIST
            [1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 5.0],
            [0.5, 1.0, 2.0, 2.0, 3.0, 2.0, 3.0],
            [0.333, 0.5, 1.0, 2.0, 2.0, 2.0, 3.0],
            [0.25, 0.5, 0.5, 1.0, 2.0, 1.0, 2.0],
            [0.2, 0.333, 0.5, 0.5, 1.0, 0.5, 1.0],
            [0.25, 0.5, 0.5, 1.0, 2.0, 1.0, 2.0],
            [0.2, 0.333, 0.333, 0.5, 1.0, 0.5, 1.0],
        ]
    )

    # Distance Utility Curves
    distance_curves: dict[str, DistanceUtilityCurve] = Field(
        default_factory=lambda: {
            "ROAD_ACCESS": DistanceUtilityCurve(
                curve_type=DistanceUtilityCurveType.MONOTONIC_DECREASING,
                optimal_min_km=0.5,
                max_acceptable_km=5.0,
            ),
            "HEALTHCARE_ACCESS": DistanceUtilityCurve(
                curve_type=DistanceUtilityCurveType.MONOTONIC_DECREASING,
                optimal_min_km=2.0,
                max_acceptable_km=15.0,
            ),
            "EDUCATION_ACCESS": DistanceUtilityCurve(
                curve_type=DistanceUtilityCurveType.MONOTONIC_DECREASING,
                optimal_min_km=1.0,
                max_acceptable_km=10.0,
            ),
            "WATER_ACCESS": DistanceUtilityCurve(
                curve_type=DistanceUtilityCurveType.MONOTONIC_DECREASING,
                optimal_min_km=0.5,
                max_acceptable_km=4.0,
            ),
            "DISTANCE_FROM_ORIGIN": DistanceUtilityCurve(
                curve_type=DistanceUtilityCurveType.OPTIMAL_RANGE,
                optimal_min_km=2.0,
                optimal_max_km=10.0,
                max_acceptable_km=25.0,
            ),
        }
    )

    # Collinearity & Sensitivity
    redundancy_correlation_threshold: float = 0.85
    sensitivity_perturbation_pct: float = 0.20  # ±20%
    sensitivity_iterations: int = 150
    sensitivity_seed: int = 42

    # Robustness thresholds
    robustness_high_threshold: float = 75.0
    robustness_medium_threshold: float = 50.0

    def validate_ahp_consistency(self) -> dict[str, Any]:
        """Validates that criteria AHP pairwise comparison matrix has CR <= 0.10."""
        res = check_ahp_consistency(self.ahp_pairwise_matrix)
        return {
            "consistency_ratio": res["cr"],
            "lambda_max": res["lambda_max"],
            "is_consistent": res["is_consistent"],
            "status": "CONFIGURED · CONSISTENT" if res["is_consistent"] else "INCONSISTENT",
        }



DEFAULT_CANDIDATE_CONFIG = CandidateDiscoveryConfig()
