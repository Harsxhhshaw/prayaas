"""Frequency Ratio (FR) empirical landslide susceptibility model.

Calculates the spatial correlation between cataloged hazard inventory events
and geo-environmental factor classes:
    FR = (N_events_in_class / N_total_events) / (Area_in_class / Total_area)

If FR > 1.0: Higher probability/density of landslide occurrence.
If FR < 1.0: Lower probability/density.

Strict scientific rule:
If only DEMO/synthetic inventory is provided, status is marked DEMO / NOT VALIDATED.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.models.enums import DataMode, HazardType
from app.models.evidence import HazardInventoryEvent


# Default factor bins for Chamoli terrain
DEFAULT_SLOPE_BINS = [
    {"name": "<15°", "min": 0.0, "max": 15.0, "area_pct": 0.20},
    {"name": "15-25°", "min": 15.0, "max": 25.0, "area_pct": 0.25},
    {"name": "25-35°", "min": 25.0, "max": 35.0, "area_pct": 0.30},
    {"name": "35-50°", "min": 35.0, "max": 50.0, "area_pct": 0.20},
    {"name": ">50°", "min": 50.0, "max": 90.0, "area_pct": 0.05},
]

DEFAULT_RAINFALL_BINS = [
    {"name": "<25mm", "min": 0.0, "max": 25.0, "area_pct": 0.35},
    {"name": "25-50mm", "min": 25.0, "max": 50.0, "area_pct": 0.40},
    {"name": "50-75mm", "min": 50.0, "max": 75.0, "area_pct": 0.20},
    {"name": ">75mm", "min": 75.0, "max": 500.0, "area_pct": 0.05},
]


class FrequencyRatioModel:
    """Frequency Ratio susceptibility model trained on hazard event inventory."""

    def __init__(
        self,
        db: Session | None = None,
        hazard_type: str = HazardType.LANDSLIDE.value,
        data_mode: str = DataMode.DEMO.value,
    ) -> None:
        self.db = db
        self.hazard_type = hazard_type
        self.data_mode = data_mode
        self.fr_table: dict[str, dict[str, float]] = {}
        self.total_events = 0
        self.is_validated = False

        if data_mode == DataMode.DEMO.value:
            self.status = "DEMO / NOT VALIDATED"
        else:
            self.status = "OPERATIONAL"

    def fit_synthetic_baseline(self) -> None:
        """Calibrates empirical frequency ratios using calibrated regional event distributions."""
        # Simulated/historical baseline distribution for Chamoli terrain
        # Most landslides in Garhwal occur between 25° and 45° slopes
        self.fr_table["slope"] = {
            "<15°": 0.35,     # 7% events / 20% area
            "15-25°": 0.68,   # 17% events / 25% area
            "25-35°": 1.53,   # 46% events / 30% area
            "35-50°": 1.30,   # 26% events / 20% area
            ">50°": 0.80,     # 4% events / 5% area
        }

        self.fr_table["rainfall"] = {
            "<25mm": 0.40,
            "25-50mm": 0.85,
            "50-75mm": 1.75,
            ">75mm": 3.20,
        }

        self.total_events = 120
        self.is_validated = False
        self.status = "DEMO / NOT VALIDATED"

    def _get_slope_class(self, slope: float) -> str:
        for b in DEFAULT_SLOPE_BINS:
            if b["min"] <= slope < b["max"]:
                return b["name"]
        return ">50°"

    def _get_rainfall_class(self, rainfall: float) -> str:
        for b in DEFAULT_RAINFALL_BINS:
            if b["min"] <= rainfall < b["max"]:
                return b["name"]
        return ">75mm"

    def _get_aspect_class(self, aspect: float) -> str:
        a = aspect % 360.0
        if a >= 315.0 or a < 45.0:
            return "North"
        elif 45.0 <= a < 135.0:
            return "East"
        elif 135.0 <= a < 225.0:
            return "South"
        else:
            return "West"

    def _get_curvature_class(self, curvature: float) -> str:
        if curvature < -0.5:
            return "Concave"
        elif curvature <= 0.5:
            return "Flat"
        else:
            return "Convex"

    def _get_drainage_class(self, dist: float) -> str:
        if dist < 100.0:
            return "<100m"
        elif dist < 300.0:
            return "100-300m"
        elif dist < 500.0:
            return "300-500m"
        else:
            return ">500m"

    def _get_road_class(self, dist: float) -> str:
        if dist < 100.0:
            return "<100m"
        elif dist < 300.0:
            return "100-300m"
        elif dist < 500.0:
            return "300-500m"
        else:
            return ">500m"

    def evaluate(self, factors: dict[str, Any]) -> dict[str, Any]:
        """Calculates normalized susceptibility (0-100) across all provided factor inputs."""
        factor_fr: dict[str, float] = {}

        if "slope" in factors and factors["slope"] is not None:
            s_class = self._get_slope_class(float(factors["slope"]))
            slope_table = {"<15°": 0.35, "15-25°": 0.68, "25-35°": 1.53, "35-50°": 1.30, ">50°": 0.80}
            factor_fr["slope"] = slope_table.get(s_class, 1.0)

        if "aspect" in factors and factors["aspect"] is not None:
            a_class = self._get_aspect_class(float(factors["aspect"]))
            aspect_table = {"North": 0.75, "East": 0.90, "South": 1.45, "West": 0.90}
            factor_fr["aspect"] = aspect_table.get(a_class, 1.0)

        if "curvature" in factors and factors["curvature"] is not None:
            c_class = self._get_curvature_class(float(factors["curvature"]))
            curv_table = {"Concave": 1.40, "Flat": 0.80, "Convex": 0.85}
            factor_fr["curvature"] = curv_table.get(c_class, 1.0)

        drain_val = factors.get("distance_to_drainage", factors.get("dist_drainage"))
        if drain_val is not None:
            d_class = self._get_drainage_class(float(drain_val))
            drain_table = {"<100m": 1.60, "100-300m": 1.20, "300-500m": 0.90, ">500m": 0.60}
            factor_fr["distance_to_drainage"] = drain_table.get(d_class, 1.0)

        road_val = factors.get("distance_to_road", factors.get("dist_road"))
        if road_val is not None:
            r_class = self._get_road_class(float(road_val))
            road_table = {"<100m": 1.50, "100-300m": 1.20, "300-500m": 0.80, ">500m": 0.50}
            factor_fr["distance_to_road"] = road_table.get(r_class, 1.0)

        if "rainfall" in factors and factors["rainfall"] is not None:
            rf_class = self._get_rainfall_class(float(factors["rainfall"]))
            rf_table = {"<25mm": 0.40, "25-50mm": 0.85, "50-75mm": 1.75, ">75mm": 3.20}
            factor_fr["rainfall"] = rf_table.get(rf_class, 1.0)

        if not factor_fr:
            return {
                "score": None,
                "status": "UNKNOWN",
                "validation_status": self.status,
                "is_validated": self.is_validated,
                "factor_fr_values": {},
            }

        # Normalize FR sum: average FR is ~1.0 per factor
        avg_fr = sum(factor_fr.values()) / len(factor_fr)
        # Map avg_fr to 0-100: 0.3 -> ~15, 1.0 -> 50, 2.5 -> ~95
        score = min(98.0, max(5.0, (avg_fr / 2.0) * 100.0))

        return {
            "score": round(score, 1),
            "status": self.status,
            "validation_status": self.status,
            "is_validated": self.is_validated,
            "factor_fr_values": factor_fr,
            "fr_contributions": factor_fr,
            "sum_fr": round(sum(factor_fr.values()), 2),
            "model_label": "Frequency Ratio Susceptibility Model (DEMO / NOT VALIDATED)",
        }

    def predict_susceptibility(
        self,
        slope_deg: float | None = None,
        rainfall_mm: float | None = None,
    ) -> dict[str, Any]:
        """Calculates normalized susceptibility (0-100) from combined Frequency Ratios."""
        factors: dict[str, Any] = {}
        if slope_deg is not None:
            factors["slope"] = slope_deg
        if rainfall_mm is not None:
            factors["rainfall"] = rainfall_mm
        return self.evaluate(factors)

