"""Compound Hazard Interaction Analysis.

Calculates multi-hazard interaction adjustments (e.g., rainfall/cloudburst + landslide).
Strictly enforces a maximum adjustment cap (15.0 points) to prevent uncalibrated runaway scores.
"""

from __future__ import annotations

from typing import Sequence


def calculate_compound_hazard_adjustment(
    baseline_hazard: float,
    dynamic_hazard: float,
    active_hazard_types: Sequence[str] | None = None,
    rainfall_24h: float = 0.0,
    max_cap: float = 15.0,
) -> float:
    """Calculates non-negative compound hazard adjustment strictly capped at max_cap."""
    if not active_hazard_types or len(active_hazard_types) <= 1:
        return 0.0

    count = len(active_hazard_types)
    # Base interaction factor for co-occurring hazards
    interaction_bonus = (count - 1) * 3.0

    # Rainfall amplification if triggering thresholds reached
    rainfall_bonus = 0.0
    if rainfall_24h > 100.0:
        rainfall_bonus = min(6.0, (rainfall_24h - 100.0) * 0.05)

    # Dynamic vs baseline surge interaction
    surge_bonus = max(0.0, (dynamic_hazard - baseline_hazard) * 0.1)

    raw_adjustment = interaction_bonus + rainfall_bonus + surge_bonus
    # Strictly non-negative and capped at max_cap
    clamped_adjustment = max(0.0, min(max_cap, round(raw_adjustment, 2)))
    return clamped_adjustment
