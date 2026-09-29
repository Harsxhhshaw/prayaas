"""MCDA Criteria correlation and collinearity diagnostics (Pearson, Spearman, VIF).

Helps prevent multi-criteria redundancy and double-counting in spatial suitability models.
"""

from __future__ import annotations

from typing import Any
import numpy as np
from scipy import stats


def calculate_vif_values(corr_matrix: np.ndarray, feature_names: list[str]) -> dict[str, float]:
    """Calculates Variance Inflation Factor (VIF) from the correlation matrix.

    VIF_i = diag(R^-1)_i. VIF > 5.0 or 10.0 indicates significant multicollinearity.
    """
    n = corr_matrix.shape[0]
    vif_dict: dict[str, float] = {}

    try:
        # Invert correlation matrix
        inv_r = np.linalg.pinv(corr_matrix)
        for i in range(n):
            vif_val = float(inv_r[i, i])
            vif_dict[feature_names[i]] = round(max(1.0, vif_val), 2)
    except Exception:
        for name in feature_names:
            vif_dict[name] = 1.0

    return vif_dict


def calculate_criteria_correlation(
    criteria_matrix: dict[str, list[float]] | np.ndarray,
    criterion_names: list[str] | None = None,
    redundancy_threshold: float = 0.85,
) -> dict[str, Any]:
    """Computes Pearson and Spearman correlation matrices and flags potential redundancy.

    Does NOT remove criteria automatically; flags warnings for expert/configuration review.
    """
    if isinstance(criteria_matrix, dict):
        names = list(criteria_matrix.keys())
        data = np.array([criteria_matrix[k] for k in names], dtype=np.float64).T
    else:
        data = np.asarray(criteria_matrix, dtype=np.float64)
        names = criterion_names or [f"C{i+1}" for i in range(data.shape[1])]

    n_samples, n_criteria = data.shape
    if n_samples < 3 or n_criteria < 2:
        return {
            "pearson": {},
            "spearman": {},
            "vif": {name: 1.0 for name in names},
            "redundancy_warnings": [],
            "high_correlation_pairs": [],
        }

    # 1. Pearson correlation
    pearson_mat = np.corrcoef(data, rowvar=False)

    # 2. Spearman rank correlation
    spearman_res = stats.spearmanr(data, axis=0)
    if n_criteria == 2:
        spearman_mat = np.array([
            [1.0, spearman_res.statistic],
            [spearman_res.statistic, 1.0],
        ])
    else:
        spearman_mat = np.asarray(spearman_res.statistic)

    # 3. VIF
    vif_dict = calculate_vif_values(pearson_mat, names)

    # 4. Search for high correlation pairs & generate warnings
    high_pairs: list[dict[str, Any]] = []
    warnings: list[str] = []

    for i in range(n_criteria):
        for j in range(i + 1, n_criteria):
            s_val = float(spearman_mat[i, j])
            p_val = float(pearson_mat[i, j])

            if abs(s_val) >= redundancy_threshold or abs(p_val) >= redundancy_threshold:
                c1, c2 = names[i], names[j]
                high_pairs.append({
                    "criterion_1": c1,
                    "criterion_2": c2,
                    "spearman": round(s_val, 3),
                    "pearson": round(p_val, 3),
                })
                warnings.append(
                    f"POTENTIAL_REDUNDANCY: High correlation between {c1} and {c2} (Spearman={s_val:.2f}, Pearson={p_val:.2f})"
                )

    # Format matrices as nested dicts
    pearson_dict = {
        names[i]: {names[j]: round(float(pearson_mat[i, j]), 3) for j in range(n_criteria)}
        for i in range(n_criteria)
    }
    spearman_dict = {
        names[i]: {names[j]: round(float(spearman_mat[i, j]), 3) for j in range(n_criteria)}
        for i in range(n_criteria)
    }

    return {
        "criteria": names,
        "pearson": pearson_dict,
        "spearman": spearman_dict,
        "vif": vif_dict,
        "high_correlation_pairs": high_pairs,
        "redundancy_warnings": warnings,
        "redundancy_threshold": redundancy_threshold,
    }


# Compatibility aliases
calculate_correlation_matrix = calculate_criteria_correlation
calculate_vif = calculate_vif_values
