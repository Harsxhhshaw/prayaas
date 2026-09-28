"""Versioned configuration for PRAYAAS Multi-Hazard Risk Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class RiskEngineConfig:
    """Immutable, auditable risk algorithm configuration PRAYAAS-RISK-1.0."""

    ANALYSIS_VERSION: ClassVar[str] = "PRAYAAS-RISK-1.0"
    CONFIG_VERSION: ClassVar[str] = "1.0.0"

    # ── Weights (Sum = 1.00) ──
    HAZARD_WEIGHT: float = 0.35
    EXPOSURE_WEIGHT: float = 0.20
    VULNERABILITY_WEIGHT: float = 0.20
    ADAPTIVE_DEFICIT_WEIGHT: float = 0.10
    HISTORY_WEIGHT: float = 0.10
    TREND_WEIGHT: float = 0.05

    # ── Multi-Hazard Blend ──
    MAX_HAZARD_WEIGHT: float = 0.60
    OTHER_HAZARDS_WEIGHT: float = 0.40

    # ── Baseline vs Dynamic Hazard Blend ──
    HAZARD_BASELINE_WEIGHT: float = 0.70
    HAZARD_DYNAMIC_WEIGHT: float = 0.30

    # ── Compound Hazard Escalation Cap ──
    MAX_COMPOUND_ADJUSTMENT: float = 15.0

    # ── Thresholds ──
    PERMANENT_RED_RISK_THRESHOLD: float = 75.0
    PERMANENT_RED_STRUCTURAL_THRESHOLD: float = 70.0
    PERMANENT_RED_CONFIDENCE_THRESHOLD: float = 70.0  # Downgrade guard

    CONDITIONAL_RED_RISK_THRESHOLD: float = 65.0
    WATCH_RISK_THRESHOLD: float = 40.0
    DYNAMIC_RED_SURGE_THRESHOLD: float = 75.0

    # ── Sustainability Thresholds ──
    CRITICAL_UNSUSTAINABLE_HSI: float = 35.0


DEFAULT_RISK_CONFIG = RiskEngineConfig()
