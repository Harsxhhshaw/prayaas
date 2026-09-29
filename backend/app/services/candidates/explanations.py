"""Deterministic Explanation Engine for Discovered Candidate Relocation Parcels.

Generates transparent, auditable rationales for parcel inclusion, limitations,
robustness, and land rejection reasons without using black-box or non-deterministic LLMs.
"""

from __future__ import annotations

from typing import Any
from app.models.enums import RobustnessLevel


class CandidateExplanationEngine:
    """Produces deterministic rule-based explanations for candidate parcels and rejections."""

    @staticmethod
    def generate_parcel_explanation(
        parcel_rank: int,
        suitability_score: float,
        confidence_score: float,
        robustness_score: float,
        rank_stability: float,
        robustness_level: str,
        area_ha: float,
        dist_from_origin_km: float,
        criteria_scores: dict[str, float],
        exclusion_summary: dict[str, str],
        data_mode: str,
    ) -> dict[str, Any]:
        """Generates structured, deterministic reasons for why a parcel survived and its limitations."""
        why_selected: list[str] = []
        limitations: list[str] = []
        reason_codes: list[str] = []

        # ── Why Selected ──
        if exclusion_summary.get("CRITICAL_LANDSLIDE_RISK") == "PASS":
            why_selected.append("Parcel boundary is outside mapped high landslide susceptibility zones.")
            reason_codes.append("OUTSIDE_MAPPED_HAZARD_ZONES")

        if exclusion_summary.get("EXCESSIVE_SLOPE") == "PASS":
            why_selected.append("Terrain slope is within safe Himalayan resettlement threshold (<= 25.0°).")
            reason_codes.append("ACCEPTABLE_TERRAIN_SLOPE")

        if exclusion_summary.get("DENSE_EXISTING_SETTLEMENT") == "PASS":
            why_selected.append("No direct conflict with dense existing village core footprints.")
            reason_codes.append("NO_BUILTUP_CONFLICT")

        if "ROAD_ACCESS" in criteria_scores and criteria_scores["ROAD_ACCESS"] >= 60.0:
            why_selected.append("Favorable road accessibility supporting emergency access and logistical connectivity.")
            reason_codes.append("FAVORABLE_ROAD_ACCESS")

        if "HEALTHCARE_ACCESS" in criteria_scores and criteria_scores["HEALTHCARE_ACCESS"] >= 50.0:
            why_selected.append("Accessible to regional healthcare facilities.")
            reason_codes.append("HEALTHCARE_PROXIMITY")

        if area_ha >= 2.0:
            why_selected.append(f"Contiguous parcel area ({area_ha:.1f} ha) satisfies minimum community resettlement threshold.")
            reason_codes.append("VIABLE_CONTIGUOUS_PARCEL_SIZE")

        if dist_from_origin_km <= 15.0:
            why_selected.append(f"Relocation distance ({dist_from_origin_km:.1f} km) mitigates acute socio-cultural disruption.")
            reason_codes.append("OPTIMAL_RELOCATION_DISTANCE")

        # ── Limitations ──
        if exclusion_summary.get("PROTECTED_AREA") == "UNKNOWN":
            limitations.append("Protected forest / sanctuary cadastral dataset unavailable; requires forestry clearance.")
            reason_codes.append("LIMITATION_FOREST_CLEARANCE_UNKNOWN")

        if exclusion_summary.get("CRITICAL_FLOOD_RISK") == "UNKNOWN":
            limitations.append("Spatial flood inundation modeling layer pending regional hydrological verification.")
            reason_codes.append("LIMITATION_FLOOD_LAYER_UNVERIFIED")

        if exclusion_summary.get("WATER_BODY") == "UNKNOWN":
            limitations.append("Local micro-drainage channels require on-ground engineering survey.")
            reason_codes.append("LIMITATION_DRAINAGE_SURVEY_REQUIRED")

        limitations.append("Land tenure, revenue ownership records, and private rights unconfirmed (statutory authority gate required).")
        reason_codes.append("LIMITATION_LAND_TENURE_UNCONFIRMED")

        limitations.append("Preliminary GIS discovery parcel; ground-truth field inspection is mandatory.")
        reason_codes.append("LIMITATION_FIELD_VERIFICATION_PENDING")


        if data_mode == "DEMO":
            limitations.append("Derived using prototype/benchmark elevation and boundary evidence.")
            reason_codes.append("LIMITATION_DEMO_DATA_DEPENDENCY")

        # ── Robustness Summary ──
        robustness_summary = (
            f"Rank #{parcel_rank} with composite suitability {suitability_score:.1f}/100. "
            f"Robustness rated {robustness_level} ({robustness_score:.1f}/100) under ±20% MCDA weight perturbations; "
            f"maintained #1 ranking in {rank_stability:.1f}% of simulation runs."
        )

        return {
            "why_selected": why_selected,
            "limitations": limitations,
            "robustness_summary": robustness_summary,
            "reason_codes": reason_codes,
            "summary_narrative": (
                f"Candidate Parcel #{parcel_rank} encompasses {area_ha:.1f} hectares of contiguous feasible land "
                f"located {dist_from_origin_km:.1f} km from origin. It survived hard slope and landslide safety screening "
                f"with {suitability_score:.1f}/100 suitability and {confidence_score:.1f}/100 confidence."
            ),
        }

    @staticmethod
    def generate_rejection_summary(
        cells_excluded: int,
        exclusion_reasons: dict[str, int],
        parcels_rejected_by_area: int,
        parcels_rejected_by_geometry: int = 0,
    ) -> dict[str, Any]:
        """Summarizes cell and parcel rejections across exclusion categories."""
        return {
            "total_cells_excluded": cells_excluded,
            "rejections_by_category": exclusion_reasons,
            "parcels_rejected_below_min_area": parcels_rejected_by_area,
            "parcels_rejected_by_geometry_quality": parcels_rejected_by_geometry,
            "explanation": (
                f"A total of {cells_excluded} candidate cells were screened out by safety masks. "
                f"An additional {parcels_rejected_by_area} contiguous land fragments were rejected "
                f"for failing the minimum viable community parcel area threshold, and "
                f"{parcels_rejected_by_geometry} regions were rejected for poor geometric quality (slivers/fragmentation)."
            ),
        }

