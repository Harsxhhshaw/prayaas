"""Three-state analytical semantics and missing-data normalization for PRAYAAS.

PRAYAAS strictly distinguishes:
- VALUE: Evidence was assessed and produced a real score (including 0 = minimal evaluated risk).
- UNKNOWN: Insufficient or missing evidence exists (must NOT be treated as 0 risk).
- NOT_APPLICABLE: Hazard physically does not apply to the geographic context
  (e.g., COASTAL_EROSION in inland Himalayan Chamoli).

Missing data NEVER lowers risk; missing components are omitted from weighted normalization
and instead penalize assessment confidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from app.models.enums import AnalyticalStatus

T = TypeVar("T")


@dataclass(frozen=True)
class AnalyticalValue(Generic[T]):
    """Encapsulates a metric value with explicit three-state semantics."""

    value: T | None
    status: AnalyticalStatus
    confidence: float | None = None
    reason: str | None = None

    @classmethod
    def from_value(cls, val: T, confidence: float | None = None) -> AnalyticalValue[T]:
        return cls(value=val, status=AnalyticalStatus.VALUE, confidence=confidence)

    @classmethod
    def unknown(cls, reason: str = "Insufficient evidence") -> AnalyticalValue[T]:
        return cls(value=None, status=AnalyticalStatus.UNKNOWN, reason=reason)

    @classmethod
    def not_applicable(cls, reason: str = "Not applicable to geographic setting") -> AnalyticalValue[T]:
        return cls(value=None, status=AnalyticalStatus.NOT_APPLICABLE, reason=reason)

    @property
    def is_available(self) -> bool:
        return self.status == AnalyticalStatus.VALUE and self.value is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "reason": self.reason,
        }


def normalize_hazard_scores(
    hazard_scores: list[dict[str, Any]] | None,
    district: str | None = None,
    state: str | None = None,
) -> list[dict[str, Any]]:
    """Normalizes a habitation's hazard scores to adhere to three-state semantics.

    Guarantees:
    - Zero (score=0) is kept as VALUE (evaluated minimal risk).
    - UNKNOWN items have score=None and status="UNKNOWN".
    - NOT_APPLICABLE items have score=None and status="NOT_APPLICABLE".
    - For Chamoli (and Uttarakhand inland districts), COASTAL_EROSION is strictly NOT_APPLICABLE.
    """
    scores_in = hazard_scores or []
    out: list[dict[str, Any]] = []
    seen_types: set[str] = set()

    is_inland_chamoli = (
        (district and "chamoli" in district.lower())
        or (state and "uttarakhand" in state.lower())
    )

    for item in scores_in:
        h_type = str(item.get("type", "")).upper()
        seen_types.add(h_type)
        label = item.get("label") or h_type.replace("_", " ").title()

        # Chamoli / Himalayan rule: Coastal Erosion is never applicable
        if is_inland_chamoli and h_type == "COASTAL_EROSION":
            out.append({
                "type": h_type,
                "score": None,
                "label": label,
                "status": AnalyticalStatus.NOT_APPLICABLE.value,
            })
            continue

        raw_status = item.get("status")
        raw_score = item.get("score")

        if raw_status == AnalyticalStatus.NOT_APPLICABLE.value:
            out.append({
                "type": h_type,
                "score": None,
                "label": label,
                "status": AnalyticalStatus.NOT_APPLICABLE.value,
            })
        elif raw_status == AnalyticalStatus.UNKNOWN.value or raw_score is None:
            out.append({
                "type": h_type,
                "score": None,
                "label": label,
                "status": AnalyticalStatus.UNKNOWN.value,
            })
        else:
            # Score is present (even if 0)
            score_int = int(round(float(raw_score)))
            out.append({
                "type": h_type,
                "score": max(0, min(100, score_int)),
                "label": label,
                "status": AnalyticalStatus.VALUE.value,
            })

    # Ensure COASTAL_EROSION is explicitly represented for Chamoli habitations
    if is_inland_chamoli and "COASTAL_EROSION" not in seen_types:
        out.append({
            "type": "COASTAL_EROSION",
            "score": None,
            "label": "Coastal Erosion",
            "status": AnalyticalStatus.NOT_APPLICABLE.value,
        })

    return out


def calculate_available_weighted_score(
    components: dict[str, float | None],
    weights: dict[str, float],
) -> tuple[float | None, float, list[str]]:
    """Calculates weighted aggregation across available components only.

    Missing components (None or NaN) are excluded from the denominator so missing data
    does NOT reduce the computed risk score.

    Formula:
        available_weight_sum = sum(weights[k] for available components)
        weighted_score = sum(weight_i * score_i) / available_weight_sum
        clamped to [0.0, 100.0]

    Returns:
        (weighted_score, available_weight_sum, missing_components)
    """
    available_sum = 0.0
    weighted_val_sum = 0.0
    missing: list[str] = []

    for name, weight in weights.items():
        val = components.get(name)
        if val is None:
            missing.append(name)
            continue
        try:
            val_f = float(val)
            import math
            if math.isnan(val_f):
                missing.append(name)
                continue
            available_sum += weight
            weighted_val_sum += weight * val_f
        except (ValueError, TypeError):
            missing.append(name)

    if available_sum <= 0.0:
        return None, 0.0, missing

    normalized_score = weighted_val_sum / available_sum
    clamped = max(0.0, min(100.0, normalized_score))
    return round(clamped, 2), round(available_sum, 4), missing
