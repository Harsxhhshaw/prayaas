"""Independent assessment and data confidence evaluation engine for multi-hazard risk.

Separates DATA / ASSESSMENT CONFIDENCE (completeness, quality, freshness, field verification)
from MODEL PERFORMANCE (AUC, spatial holdout, validation metrics).
Penalizes confidence when core components are missing or when independent models disagree.
"""

from __future__ import annotations

from typing import Any


def calculate_risk_confidence(
    has_vulnerability_profile: bool,
    vulnerability_profile_mode: str | None,
    has_environmental_observations: bool,
    observation_mode: str | None,
    hazard_scores_count: int,
    risk_history_count: int,
    is_demographics_complete: bool,
    missing_components: list[str] | None = None,
    model_agreement_penalty: float = 0.0,
    model_agreement_reason: str | None = None,
) -> tuple[float, list[str], str]:
    """Calculates an independent 0-100 DATA / ASSESSMENT CONFIDENCE score and rationale.

    Returns:
        (confidence_score, reason_codes, rationale_text)
    """
    base_score = 50.0
    penalties: list[tuple[str, float]] = []
    bonuses: list[tuple[str, float]] = []
    reasons: list[str] = []

    # 1. Vulnerability profile confidence
    if has_vulnerability_profile:
        if vulnerability_profile_mode == "FIELD":
            bonuses.append(("Field survey verification present", 20.0))
            reasons.append("FIELD_VULNERABILITY_VERIFIED")
        elif vulnerability_profile_mode in ("PUBLIC", "LIVE"):
            bonuses.append(("Verified public vulnerability data", 15.0))
            reasons.append("PUBLIC_VULNERABILITY_AVAILABLE")
        else:
            bonuses.append(("Synthetic vulnerability model", 8.0))
            reasons.append("DEMO_VULNERABILITY_MODEL")
    else:
        penalties.append(("Missing detailed socio-economic vulnerability profile", 15.0))
        reasons.append("MISSING_VULNERABILITY_PROFILE")

    # 2. Environmental observations (weather / live feeds)
    if has_environmental_observations:
        if observation_mode == "LIVE":
            bonuses.append(("Live meteorological feeds connected", 15.0))
            reasons.append("LIVE_METEOROLOGY_ACTIVE")
        else:
            bonuses.append(("Environmental observations available", 8.0))
            reasons.append("OBSERVATIONS_AVAILABLE")
    else:
        penalties.append(("No recent environmental/weather observations", 12.0))
        reasons.append("MISSING_ENVIRONMENTAL_OBSERVATIONS")

    # 3. Multi-hazard specificity
    if hazard_scores_count >= 3:
        bonuses.append(("Multi-hazard breakdown available (>= 3 hazards)", 10.0))
        reasons.append("MULTI_HAZARD_COMPREHENSIVE")
    elif hazard_scores_count > 0:
        bonuses.append(("Partial hazard breakdown available", 5.0))
        reasons.append("HAZARD_PARTIAL")
    else:
        penalties.append(("Missing detailed hazard breakdowns", 10.0))
        reasons.append("MISSING_HAZARD_BREAKDOWN")

    # 4. Temporal risk history
    if risk_history_count >= 3:
        bonuses.append(("Multi-year historical risk trajectory available", 10.0))
        reasons.append("TEMPORAL_HISTORY_ROBUST")
    elif risk_history_count > 0:
        bonuses.append(("Limited historical risk data", 5.0))
        reasons.append("TEMPORAL_HISTORY_LIMITED")
    else:
        penalties.append(("No historical risk time-series", 8.0))
        reasons.append("NO_RISK_HISTORY")

    # 5. Demographics completeness
    if is_demographics_complete:
        bonuses.append(("Complete baseline demographic counts", 5.0))
    else:
        penalties.append(("Incomplete population / household records", 8.0))
        reasons.append("DEMOGRAPHICS_INCOMPLETE")

    # 6. Missing analytical components penalty
    if missing_components:
        reasons.append("MISSING_ANALYTICAL_COMPONENTS")
        for comp in missing_components:
            p_val = 7.5
            penalties.append((f"Missing analytical component: {comp}", p_val))
            reasons.append(f"MISSING_COMPONENT_{comp.upper()}")


    # 7. Model disagreement penalty
    if model_agreement_penalty > 0:
        penalties.append(("Methodological divergence across independent models", model_agreement_penalty))
        if model_agreement_reason:
            reasons.append(model_agreement_reason)
        else:
            reasons.append("MODEL_DISAGREEMENT_PENALTY")

    total_bonuses = sum(val for _, val in bonuses)
    total_penalties = sum(val for _, val in penalties)
    final_score = max(10.0, min(100.0, base_score + total_bonuses - total_penalties))

    rationale_lines = [
        f"Data / Assessment Confidence: {final_score:.1f}/100",
        "Positive factors: " + (", ".join(f"{txt} (+{val})" for txt, val in bonuses) if bonuses else "None"),
        "Deductions: " + (", ".join(f"{txt} (-{val})" for txt, val in penalties) if penalties else "None"),
    ]
    rationale_text = "\n".join(rationale_lines)

    return round(final_score, 1), reasons, rationale_text
