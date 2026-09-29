"""Automated GIS Relocation Candidate Discovery Service Package."""

from app.services.candidates.config import (
    CandidateDiscoveryConfig,
    DEFAULT_CANDIDATE_CONFIG,
    DistanceUtilityCurve,
)
from app.services.candidates.exclusions import HardExclusionEngine
from app.services.candidates.suitability import SoftSuitabilityEngine
from app.services.candidates.polygons import ContiguousParcelExtractor
from app.services.candidates.explanations import CandidateExplanationEngine
from app.services.candidates.engine import CandidateDiscoveryEngine

__all__ = [
    "CandidateDiscoveryConfig",
    "DEFAULT_CANDIDATE_CONFIG",
    "DistanceUtilityCurve",
    "HardExclusionEngine",
    "SoftSuitabilityEngine",
    "ContiguousParcelExtractor",
    "CandidateExplanationEngine",
    "CandidateDiscoveryEngine",
]
