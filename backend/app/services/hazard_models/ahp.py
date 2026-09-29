"""Analytic Hierarchy Process (AHP) susceptibility model with Saaty consistency checking.

Implements:
- Saaty (1980) pairwise comparison matrix analysis
- Principal eigenvalue lambda_max estimation
- Consistency Index (CI) and Consistency Ratio (CR) calculation against Random Index (RI)
- Inconsistency rejection guard (CR > 0.10)
- Configurable factor classes and ratings (0-100 output)
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np

# Saaty's empirical Random Consistency Index (RI) for matrix size n=1..15
SAATY_RI: dict[int, float] = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
    11: 1.51,
    12: 1.54,
    13: 1.56,
    14: 1.57,
    15: 1.59,
}


def check_ahp_consistency(
    matrix: np.ndarray | list[list[float]],
    cr_threshold: float = 0.10,
) -> dict[str, Any]:
    """Evaluates the Saaty Consistency Ratio of an n x n pairwise comparison matrix.

    Returns:
        {
            "is_consistent": bool,
            "lambda_max": float,
            "ci": float,
            "cr": float,
            "weights": list[float],
            "cr_threshold": float,
            "status": "CONSISTENT" | "INCONSISTENT"
        }
    """
    mat = np.array(matrix, dtype=float)
    if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
        raise ValueError(f"Pairwise comparison matrix must be square, got {mat.shape}")

    n = mat.shape[0]

    # Verify reciprocity and diagonal
    for i in range(n):
        if not np.isclose(mat[i, i], 1.0, atol=1e-3):
            raise ValueError(f"Diagonal element must be 1.0, got A[{i},{i}]={mat[i, i]}")
        for j in range(i + 1, n):
            if not np.isclose(mat[i, j] * mat[j, i], 1.0, atol=1e-2):
                raise ValueError(f"Matrix must be reciprocal: A[{i},{j}]={mat[i, j]} vs A[{j},{i}]={mat[j, i]}")

    matrix = mat
    if n <= 2:
        weights = [1.0 / n] * n if n > 0 else []
        return {
            "is_consistent": True,
            "lambda_max": float(n),
            "ci": 0.0,
            "cr": 0.0,
            "consistency_ratio": 0.0,
            "weights": weights,
            "cr_threshold": cr_threshold,
            "status": "CONSISTENT",
        }


    # 1. Derive priority vector (weights) using geometric mean method
    geo_means = np.prod(matrix, axis=1) ** (1.0 / n)
    weights = geo_means / np.sum(geo_means)

    # 2. Compute Aw and lambda_max
    aw = np.dot(matrix, weights)
    lambda_max = float(np.mean(aw / weights))

    # 3. Consistency Index
    ci = (lambda_max - n) / (n - 1)

    # 4. Consistency Ratio against Saaty RI
    ri = SAATY_RI.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0
    cr = max(0.0, cr)  # Guard small floating point imprecision

    is_consistent = cr <= cr_threshold
    status = "CONSISTENT" if is_consistent else "INCONSISTENT"

    return {
        "is_consistent": is_consistent,
        "lambda_max": round(lambda_max, 4),
        "ci": round(ci, 4),
        "cr": round(cr, 4),
        "consistency_ratio": round(cr, 4),
        "weights": [round(float(w), 4) for w in weights],
        "cr_threshold": cr_threshold,
        "status": status,
    }



# Standard PRAYAAS prototype AHP configuration for Himalayan landslide susceptibility
DEFAULT_LANDSLIDE_FACTORS = [
    "slope",
    "rainfall",
    "geology",
    "road_distance",
    "drainage_distance",
]

# Pairwise comparison matrix (5x5) satisfying Saaty consistency (CR <= 0.05)
DEFAULT_COMPARISON_MATRIX = np.array([
    [1.0,  2.0,  3.0,  4.0,  5.0],   # slope
    [0.5,  1.0,  2.0,  3.0,  4.0],   # rainfall
    [0.33, 0.5,  1.0,  2.0,  3.0],   # geology
    [0.25, 0.33, 0.5,  1.0,  2.0],   # road_distance
    [0.20, 0.25, 0.33, 0.5,  1.0],   # drainage_distance
], dtype=np.float64)


class AHPSusceptibilityModel:
    """Analytical Hierarchy Process susceptibility evaluator."""

    def __init__(
        self,
        factors: list[str] = DEFAULT_LANDSLIDE_FACTORS,
        matrix: np.ndarray = DEFAULT_COMPARISON_MATRIX,
        cr_threshold: float = 0.10,
    ) -> None:
        self.factors = factors
        self.matrix = matrix
        self.cr_threshold = cr_threshold
        self.consistency = check_ahp_consistency(matrix, cr_threshold=cr_threshold)

        if not self.consistency["is_consistent"]:
            self.status = "INCONSISTENT"
        else:
            self.status = "OPERATIONAL"

        self.weights = dict(zip(self.factors, self.consistency["weights"]))

    def rate_slope(self, slope_deg: float | None) -> float | None:
        """Standard Himalayan slope rating (0-100)."""
        if slope_deg is None:
            return None
        if slope_deg < 15.0:
            return 15.0
        elif slope_deg < 25.0:
            return 40.0
        elif slope_deg < 35.0:
            return 70.0
        elif slope_deg < 50.0:
            return 95.0
        else:
            return 85.0  # Cliff faces often have less loose overburden

    def rate_rainfall(self, rainfall_mm: float | None) -> float | None:
        """24h precipitation rating (0-100)."""
        if rainfall_mm is None:
            return None
        if rainfall_mm < 20.0:
            return 20.0
        elif rainfall_mm < 40.0:
            return 45.0
        elif rainfall_mm < 65.0:
            return 75.0
        else:
            return 95.0

    def rate_road_distance(self, dist_km: float | None) -> float | None:
        """Proximity to cut-slopes and mountain roads (0-100)."""
        if dist_km is None:
            return None
        if dist_km < 0.2:
            return 90.0
        elif dist_km < 0.5:
            return 70.0
        elif dist_km < 1.5:
            return 45.0
        else:
            return 15.0

    def evaluate(self, factor_inputs: dict[str, float | None]) -> dict[str, Any]:
        """Calculates 0-100 susceptibility score using AHP weights.

        If CR > threshold, rejects operational output.
        Uses available-weight logic so missing factors do not artifically zero out susceptibility.
        """
        if not self.consistency["is_consistent"]:
            return {
                "score": None,
                "status": "INCONSISTENT",
                "reason": f"AHP matrix is mathematically inconsistent (CR={self.consistency['cr']} > {self.cr_threshold})",
                "consistency": self.consistency,
            }

        # Map common synonyms
        factor_aliases: dict[str, list[str]] = {
            "geology": ["lithology", "rock_type"],
            "drainage_distance": ["drainage", "dist_drainage"],
            "road_distance": ["road", "dist_road"],
        }

        # Convert raw inputs to 0-100 factor ratings
        ratings: dict[str, float | None] = {}
        for f in self.factors:
            val = factor_inputs.get(f)
            if val is None and f in factor_aliases:
                for alias in factor_aliases[f]:
                    if alias in factor_inputs and factor_inputs[alias] is not None:
                        val = factor_inputs[alias]
                        break

            if f == "slope":
                ratings[f] = self.rate_slope(val)
            elif f == "rainfall":
                ratings[f] = self.rate_rainfall(val)
            elif f == "road_distance":
                ratings[f] = self.rate_road_distance(val)
            else:
                ratings[f] = float(val) if val is not None else None

        from app.services.risk.semantics import calculate_available_weighted_score
        score, avail_w, missing = calculate_available_weighted_score(ratings, self.weights)

        cr_val = self.consistency.get("consistency_ratio", self.consistency["cr"])
        return {
            "score": score,
            "status": "CONFIGURED / CONSISTENT",
            "available_weight_sum": avail_w,
            "missing_factors": missing,
            "weights": self.weights,
            "ratings": ratings,
            "consistency_ratio": cr_val,
            "model_label": "PRAYAAS prototype AHP model (CR acceptable - CONFIGURED · CONSISTENT)",
        }




# Compatibility alias
verify_pairwise_matrix_consistency = check_ahp_consistency
