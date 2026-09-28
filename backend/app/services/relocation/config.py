"""Versioned configuration for PRAYAAS Relocation Need & Readiness Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class RelocationEngineConfig:
    """Immutable, auditable configuration for PRAYAAS-RELOCATION-1.0."""

    ANALYSIS_VERSION: ClassVar[str] = "PRAYAAS-RELOCATION-1.0"
    CONFIG_VERSION: ClassVar[str] = "1.0.0"

    # ── Need Component Weights (Sum = 1.00) ──
    NEED_STRUCTURAL_RISK_WEIGHT: float = 0.35
    NEED_VULNERABILITY_WEIGHT: float = 0.20
    NEED_DISASTER_HISTORY_WEIGHT: float = 0.15
    NEED_TREND_WEIGHT: float = 0.10
    NEED_ISOLATION_WEIGHT: float = 0.10
    NEED_SUSTAINABILITY_DEFICIT_WEIGHT: float = 0.10

    # ── Strict Readiness Caps ──
    CAP_NO_CANDIDATE_SITES: float = 20.0
    CAP_DEMO_ONLY_SITES: float = 40.0
    CAP_UNVERIFIED_SITES: float = 55.0
    CAP_NO_CARRYING_CAPACITY: float = 70.0

    # ── Urgency Thresholds (Need Score) ──
    URGENCY_IMMEDIATE_THRESHOLD: float = 75.0
    URGENCY_SHORT_TERM_THRESHOLD: float = 55.0
    URGENCY_MEDIUM_TERM_THRESHOLD: float = 35.0

    # ── Readiness Level Thresholds ──
    READINESS_HIGH_THRESHOLD: float = 70.0
    READINESS_MODERATE_THRESHOLD: float = 50.0
    READINESS_LOW_THRESHOLD: float = 25.0


DEFAULT_RELOCATION_CONFIG = RelocationEngineConfig()
