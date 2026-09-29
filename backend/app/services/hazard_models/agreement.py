"""Multi-Method Hazard Model Agreement Engine.

Compares independent susceptibility methodologies (e.g. AHP, Frequency Ratio,
Machine Learning, Satellite Evidence) to verify cross-model consensus.

Rules:
- High agreement (spread <= 15 points) confirms consensus.
- Low agreement (spread > 30 points) marks divergent methodologies and triggers
  an assessment confidence deduction.
- Never averages divergent results into false certainty.
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np

from app.models.enums import ModelAgreementLevel


class ModelAgreementEngine:
    """Evaluates cross-methodological consistency among independent hazard models."""

    def __init__(
        self,
        high_spread_threshold: float = 15.0,
        low_spread_threshold: float = 30.0,
        low_agreement_confidence_penalty: float = 15.0,
    ) -> None:
        self.high_spread_threshold = high_spread_threshold
        self.low_spread_threshold = low_spread_threshold
        self.low_agreement_confidence_penalty = low_agreement_confidence_penalty

    def evaluate_agreement(
        self,
        model_scores: dict[str, float | None],
    ) -> dict[str, Any]:
        """Compares available model scores and produces agreement metrics.

        Args:
            model_scores: e.g. {"AHP": 82.0, "Frequency Ratio": 78.0, "ML": 84.0}

        Returns:
            {
                "agreement_level": "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN",
                "agreement_score": float (0-100),
                "spread": float,
                "std_dev": float,
                "confidence_penalty": float,
                "reason_codes": list[str],
                "explanation": str,
                "valid_models_count": int,
            }
        """
        valid_scores = {k: v for k, v in model_scores.items() if v is not None}

        if len(valid_scores) < 2:
            return {
                "agreement_level": ModelAgreementLevel.UNKNOWN.value,
                "agreement_score": 50.0,
                "spread": 0.0,
                "std_dev": 0.0,
                "confidence_penalty": 0.0,
                "reason_codes": ["SINGLE_OR_NO_MODEL_AVAILABLE"],
                "explanation": "Insufficient independent models available to evaluate methodological agreement.",
                "valid_models_count": len(valid_scores),
                "scores": valid_scores,
            }

        scores_list = list(valid_scores.values())
        min_score = min(scores_list)
        max_score = max(scores_list)
        spread = max_score - min_score
        std_dev = float(np.std(scores_list))

        # Agreement score: 100 when spread=0, decays as spread increases
        agreement_score = max(0.0, min(100.0, 100.0 - (spread * 2.0)))

        reason_codes: list[str] = []
        confidence_penalty = 0.0

        if spread <= self.high_spread_threshold:
            agreement_level = ModelAgreementLevel.HIGH.value
            reason_codes.append("MODEL_AGREEMENT_HIGH")
            explanation = (
                f"Independent susceptibility models show strong consensus (spread = {spread:.1f} pts, "
                f"std_dev = {std_dev:.1f})."
            )
        elif spread <= self.low_spread_threshold:
            agreement_level = ModelAgreementLevel.MEDIUM.value
            reason_codes.append("MODEL_AGREEMENT_MODERATE")
            explanation = (
                f"Independent susceptibility models show moderate agreement (spread = {spread:.1f} pts)."
            )
        else:
            agreement_level = ModelAgreementLevel.LOW.value
            confidence_penalty = self.low_agreement_confidence_penalty
            reason_codes.append("MODEL_DISAGREEMENT_HIGH")
            explanation = (
                f"Independent susceptibility methods produced materially different results "
                f"(spread = {spread:.1f} pts across {list(valid_scores.keys())}). Specialist review is recommended."
            )

        return {
            "agreement_level": agreement_level,
            "agreement_score": round(agreement_score, 1),
            "spread": round(spread, 1),
            "std_dev": round(std_dev, 2),
            "confidence_penalty": confidence_penalty,
            "reason_codes": reason_codes,
            "explanation": explanation,
            "valid_models_count": len(valid_scores),
            "scores": valid_scores,
        }

    def evaluate(
        self,
        ahp_score: float | None = None,
        fr_score: float | None = None,
        ml_score: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Convenience method accepting explicit model scores as keyword arguments."""
        scores: dict[str, float | None] = {}
        if ahp_score is not None:
            scores["AHP"] = ahp_score
        if fr_score is not None:
            scores["Frequency Ratio"] = fr_score
        if ml_score is not None:
            scores["ML"] = ml_score
        for k, v in kwargs.items():
            if v is not None:
                scores[k] = v
        return self.evaluate_agreement(scores)

