"""MCDA Sensitivity and Robustness Engine.

Tests ranking stability under systematic weight perturbation (e.g. ±10%, ±20%)
using a deterministic random seed for 100% reproducible Monte Carlo simulation.
"""

from __future__ import annotations

from typing import Any
import numpy as np


class MCDASensitivityEngine:
    """Simulates weight sensitivity and evaluates MCDA ranking robustness."""

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed

    def evaluate_robustness(
        self,
        candidate_scores: dict[str, dict[str, float]],
        base_weights: dict[str, float],
        perturbation_pct: float = 0.20,
        n_iterations: int = 200,
    ) -> dict[str, Any]:
        """Runs reproducible Monte Carlo weight perturbation.

        Args:
            candidate_scores: {candidate_id: {criterion_name: score_0_to_100, ...}, ...}
            base_weights: {criterion_name: weight, ...}
            perturbation_pct: fraction to perturb, e.g. 0.20 for ±20%
            n_iterations: number of simulation runs

        Returns:
            {
                "robustness_score": float (0-100),
                "top_candidate": str,
                "rank_stability": float (% iterations top candidate stayed #1),
                "candidate_metrics": {
                    candidate_id: {
                        "base_score": float,
                        "mean_score": float,
                        "score_min": float,
                        "score_max": float,
                        "rank_1_freq": float,
                        "mean_rank": float,
                    }
                }
            }
        """
        rng = np.random.default_rng(self.random_seed)

        candidates = list(candidate_scores.keys())
        criteria = list(base_weights.keys())
        w_vec = np.array([base_weights[c] for c in criteria], dtype=np.float64)
        w_vec = w_vec / np.sum(w_vec)  # Base normalized

        # Build matrix: shape (n_candidates, n_criteria)
        score_matrix = np.array([
            [candidate_scores[cand].get(crit, 0.0) for crit in criteria]
            for cand in candidates
        ], dtype=np.float64)

        # Baseline scores & baseline top candidate
        base_composite = score_matrix @ w_vec
        base_top_idx = int(np.argmax(base_composite))
        base_top_candidate = candidates[base_top_idx]

        # Iteration tracking
        scores_history = np.zeros((n_iterations, len(candidates)), dtype=np.float64)
        ranks_history = np.zeros((n_iterations, len(candidates)), dtype=np.int32)

        for it in range(n_iterations):
            # Perturb weights: w_i * (1 + uniform(-pct, +pct))
            noise = rng.uniform(-perturbation_pct, perturbation_pct, size=len(w_vec))
            perturbed_w = np.maximum(0.001, w_vec * (1.0 + noise))
            perturbed_w /= np.sum(perturbed_w)  # Re-normalize to 1.0

            iter_scores = score_matrix @ perturbed_w
            scores_history[it, :] = iter_scores

            # Compute ranks (rank 1 = highest score)
            order = np.argsort(-iter_scores)
            ranks = np.empty_like(order)
            ranks[order] = np.arange(1, len(candidates) + 1)
            ranks_history[it, :] = ranks

        # Summarize candidate metrics
        cand_metrics: dict[str, Any] = {}
        for idx, cand in enumerate(candidates):
            c_scores = scores_history[:, idx]
            c_ranks = ranks_history[:, idx]
            rank_1_count = np.sum(c_ranks == 1)

            cand_metrics[cand] = {
                "base_score": round(float(base_composite[idx]), 2),
                "mean_score": round(float(np.mean(c_scores)), 2),
                "score_min": round(float(np.min(c_scores)), 2),
                "score_max": round(float(np.max(c_scores)), 2),
                "score_range": round(float(np.max(c_scores) - np.min(c_scores)), 2),
                "rank_1_freq": round(float(rank_1_count / n_iterations) * 100.0, 1),
                "mean_rank": round(float(np.mean(c_ranks)), 2),
                "rank_range": [int(np.min(c_ranks)), int(np.max(c_ranks))],
            }

        top_rank_1_freq = cand_metrics[base_top_candidate]["rank_1_freq"]
        rank_stability = top_rank_1_freq  # % of times top candidate remained #1

        # Robustness score (0-100): combinations of rank stability and score variance
        mean_score_range = float(np.mean([m["score_range"] for m in cand_metrics.values()]))
        score_stability_penalty = min(30.0, mean_score_range * 1.5)
        robustness_score = max(10.0, min(100.0, (rank_stability * 0.70) + (100.0 - score_stability_penalty) * 0.30))

        return {
            "robustness_score": round(robustness_score, 1),
            "rank_stability": round(rank_stability, 1),
            "top_candidate": base_top_candidate,
            "perturbation_pct": perturbation_pct,
            "n_iterations": n_iterations,
            "random_seed": self.random_seed,
            "candidate_metrics": cand_metrics,
        }


def run_monte_carlo_sensitivity(
    candidate_items: list[dict[str, Any]] | dict[str, dict[str, float]],
    base_weights: dict[str, float],
    iterations: int = 200,
    perturbation_pct: float = 0.20,
    seed: int = 42,
) -> dict[str, Any]:
    """Helper running reproducible Monte Carlo sensitivity simulation."""
    engine = MCDASensitivityEngine(random_seed=seed)
    if isinstance(candidate_items, list):
        scores_dict = {
            item["id"]: item.get("criteria", {})
            for item in candidate_items
        }
    else:
        scores_dict = candidate_items

    result = engine.evaluate_robustness(
        candidate_scores=scores_dict,
        base_weights=base_weights,
        perturbation_pct=perturbation_pct,
        n_iterations=iterations,
    )
    result["overall_robustness_score"] = result["robustness_score"]
    result["item_stability"] = result["candidate_metrics"]
    return result
