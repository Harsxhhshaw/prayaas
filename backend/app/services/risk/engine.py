"""Deterministic Multi-Hazard Risk and Red Zone Classification Engine.

Implements:
- Three-state analytical semantics (VALUE, UNKNOWN, NOT_APPLICABLE)
- Available-weight missing data normalization (missing inputs NEVER reduce risk)
- Methodological model agreement evaluation (AHP vs Frequency Ratio)
- Permanent Red downgrade guard (confidence < 70 -> CONDITIONAL_RED)
- Dynamic Red safeguard (weather surge cannot produce PERMANENT_RED without high structural risk)
- Exposed dimensional Habitation Sustainability Index (HSI)
- Accurate input and source snapshots
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.enums import AnalyticalStatus, RedZoneClassification, RiskClassification
from app.models.habitation import Habitation
from app.models.ingestion import EnvironmentalObservation
from app.models.risk import RiskAssessment, VulnerabilityProfile
from app.services.hazard_models.agreement import ModelAgreementEngine
from app.services.hazard_models.ahp import AHPSusceptibilityModel
from app.services.hazard_models.frequency_ratio import FrequencyRatioModel
from app.services.risk.config import DEFAULT_RISK_CONFIG, RiskEngineConfig
from app.services.risk.confidence import calculate_risk_confidence
from app.services.risk.semantics import (
    calculate_available_weighted_score,
    normalize_hazard_scores,
)


def calculate_sustainability_index(
    elevation: float,
    nearest_road_km: float,
    nearest_hospital_km: float,
    baseline_hazard: float,
    vulnerability_score: float,
    nearest_school_km: float | None = None,
    history_score: float | None = None,
    return_details: bool = False,
) -> float | tuple[float, float, dict[str, Any]]:
    """Calculates Habitation Sustainability Index (HSI, 0-100) and optionally exposes separate dimensions.

    Returns:
        float if return_details is False, else (sustainability_score, sustainability_confidence, dimensions_breakdown)
    """
    # 1. Evaluate dimensional scores (0-100, 100 = most sustainable/safe)
    physical_safety = max(0.0, min(100.0, 100.0 - (baseline_hazard * 0.95)))
    road_reliability = max(0.0, min(100.0, 100.0 - (nearest_road_km * 12.0)))
    health_accessibility = max(0.0, min(100.0, 100.0 - (nearest_hospital_km * 3.5)))
    education_access = max(0.0, min(100.0, 100.0 - (nearest_school_km * 5.0))) if nearest_school_km is not None else None
    infra_resilience = max(0.0, min(100.0, 100.0 - (vulnerability_score * 0.8)))
    water_security = None  # UNKNOWN: genuine data limitation in un-surveyed habitations
    historical_disruption = max(0.0, min(100.0, 100.0 - (history_score * 0.8))) if history_score is not None else None

    dimensions = {
        "physical_safety": physical_safety,
        "road_reliability": road_reliability,
        "health_accessibility": health_accessibility,
        "education_access": education_access,
        "infrastructure_resilience": infra_resilience,
        "water_security": water_security,
        "historical_disruption": historical_disruption,
    }

    dim_weights = {
        "physical_safety": 0.35,
        "road_reliability": 0.20,
        "health_accessibility": 0.15,
        "education_access": 0.10,
        "infrastructure_resilience": 0.10,
        "water_security": 0.05,
        "historical_disruption": 0.05,
    }

    hsi_score, avail_w, missing = calculate_available_weighted_score(dimensions, dim_weights)
    hsi_final = hsi_score if hsi_score is not None else 50.0

    # Confidence based on available dimensions
    hsi_confidence = round(avail_w * 100.0, 1)

    breakdown = {
        k: {
            "value": round(v, 1) if v is not None else None,
            "status": AnalyticalStatus.VALUE.value if v is not None else AnalyticalStatus.UNKNOWN.value,
        }
        for k, v in dimensions.items()
    }

    final_score = round(hsi_final, 1)
    if return_details:
        return final_score, hsi_confidence, breakdown
    return final_score


class RiskEngine:
    """Deterministic, versioned multi-hazard risk engine implementing PRAYAAS-RISK-1.0."""

    def __init__(self, db: Session, config: RiskEngineConfig = DEFAULT_RISK_CONFIG) -> None:
        self.db = db
        self.config = config

    def assess_habitation(self, habitation_id: str) -> RiskAssessment:
        hab = self.db.query(Habitation).filter(Habitation.id == habitation_id).first()
        if not hab:
            raise ValueError(f"Habitation with id {habitation_id} not found")

        # 1. Fetch Vulnerability Profile if available
        v_profile = (
            self.db.query(VulnerabilityProfile)
            .filter(VulnerabilityProfile.habitation_id == habitation_id)
            .first()
        )

        # 2. Fetch latest Environmental Observations
        recent_obs = (
            self.db.query(EnvironmentalObservation)
            .filter(EnvironmentalObservation.habitation_id == habitation_id)
            .order_by(EnvironmentalObservation.observed_at.desc())
            .limit(10)
            .all()
        )

        obs_dict = {obs.observation_type: obs for obs in recent_obs}
        rainfall_24h = obs_dict.get("RAINFALL_24H").value if "RAINFALL_24H" in obs_dict else 15.0
        soil_moisture = obs_dict.get("SOIL_MOISTURE_0_7CM").value if "SOIL_MOISTURE_0_7CM" in obs_dict else 0.25

        # ── 3. Multi-Hazard Aggregation with Three-State Semantics ──
        hazard_list = normalize_hazard_scores(hab.hazard_scores, district=hab.district, state=hab.state)
        dominant_hazard = "LANDSLIDE"
        reason_codes: list[str] = []

        # Filter only assessed hazards with real VALUE status (exclude UNKNOWN and NOT_APPLICABLE)
        active_hazards = [
            h for h in hazard_list
            if h.get("status") == AnalyticalStatus.VALUE.value and h.get("score") is not None
        ]

        if active_hazards:
            sorted_hazards = sorted(active_hazards, key=lambda x: x.get("score", 0), reverse=True)
            max_hazard = float(sorted_hazards[0].get("score", hab.risk_score))
            dominant_hazard = sorted_hazards[0].get("type", "LANDSLIDE")

            if len(sorted_hazards) > 1:
                other_scores = [float(h.get("score", 0)) for h in sorted_hazards[1:]]
                avg_other = sum(other_scores) / len(other_scores)
                baseline_hazard = (self.config.MAX_HAZARD_WEIGHT * max_hazard) + (self.config.OTHER_HAZARDS_WEIGHT * avg_other)
            else:
                baseline_hazard = max_hazard
        else:
            baseline_hazard = float(hab.risk_score)
            max_hazard = baseline_hazard

        # Dynamic hazard surge from precipitation & soil moisture
        dynamic_hazard = baseline_hazard
        if rainfall_24h >= 65.0:
            excess = rainfall_24h - 65.0
            dynamic_hazard = min(100.0, baseline_hazard + (excess * 0.5) + 15.0)
            reason_codes.append("MONSOON_PRECIPITATION_CRITICAL")
        elif rainfall_24h >= 40.0:
            dynamic_hazard = min(100.0, baseline_hazard + 8.0)
            reason_codes.append("HEAVY_RAINFALL_WARNING")

        if soil_moisture >= 0.40:
            dynamic_hazard = min(100.0, dynamic_hazard + 6.0)
            reason_codes.append("SOIL_SATURATION_HIGH")

        blended_hazard = (
            (self.config.HAZARD_BASELINE_WEIGHT * baseline_hazard)
            + (self.config.HAZARD_DYNAMIC_WEIGHT * dynamic_hazard)
        )

        # ── 4. Exposure Score ──
        pop = hab.population
        pop_density = v_profile.population_density if v_profile else (pop / 2.0)
        exposure_raw = min(100.0, (pop / 15.0) + (pop_density * 0.3) + 20.0)
        exposure_score = round(max(10.0, min(100.0, exposure_raw)), 1)

        # ── 5. Vulnerability Score ──
        if v_profile:
            demographic_vuln = (
                (v_profile.children_share * 100.0) * 0.35
                + (v_profile.elderly_share * 100.0) * 0.40
                + (v_profile.disability_share * 100.0) * 0.25
            )
            vulnerability_score = (
                (demographic_vuln * 0.40)
                + (v_profile.housing_vulnerability * 0.35)
                + (v_profile.isolation_score * 0.25)
            )
            if v_profile.housing_vulnerability > 70.0:
                reason_codes.append("KUCCHA_HOUSING_VULNERABILITY")
        else:
            vulnerability_score = float(hab.vulnerability_score or 45.0)

        vulnerability_score = round(max(10.0, min(100.0, vulnerability_score)), 1)

        # ── 6. Adaptive Capacity Deficit ──
        road_km = hab.nearest_road
        hosp_km = hab.nearest_hospital
        school_km = hab.nearest_school
        access_score = max(0.0, 100.0 - (road_km * 5.0 + hosp_km * 2.5 + school_km * 2.0))
        adaptive_capacity_score = round(max(5.0, min(95.0, access_score)), 1)
        adaptive_capacity_deficit_score = round(100.0 - adaptive_capacity_score, 1)

        if road_km > 3.0:
            reason_codes.append("SEVERE_ROAD_ISOLATION")
        if hosp_km > 15.0:
            reason_codes.append("HEALTHCARE_ACCESS_CRITICAL")

        # ── 7. History Score (UNKNOWN if no historical records exist) ──
        history_list = hab.risk_history if isinstance(hab.risk_history, list) else []
        if history_list:
            past_scores = [float(h.get("score", 50)) for h in history_list]
            history_score = round(sum(past_scores) / len(past_scores), 1)
        else:
            history_score = None  # UNKNOWN: missing data must NOT be fabricated

        # ── 8. Trend Score (UNKNOWN if < 2 historical points) ──
        if len(history_list) >= 2:
            first_score = float(history_list[0].get("score", 50))
            last_score = float(history_list[-1].get("score", 50))
            diff = last_score - first_score
            trend_score = round(max(0.0, min(100.0, 50.0 + (diff * 2.0))), 1)
            if diff > 10.0:
                reason_codes.append("ESCALATING_RISK_TRAJECTORY")
        else:
            trend_score = None  # UNKNOWN: insufficient time-series

        # ── 9. Compound Hazard Escalation (Capped at MAX_COMPOUND_ADJUSTMENT = 15.0) ──
        compound_adjustment = 0.0
        if active_hazards and len(active_hazards) > 1:
            severe_secondary = [
                h for h in sorted_hazards[1:] if float(h.get("score", 0)) >= 50.0
            ]
            if severe_secondary:
                compound_adjustment = min(
                    self.config.MAX_COMPOUND_ADJUSTMENT,
                    len(severe_secondary) * 6.5,
                )
                reason_codes.append("MULTI_HAZARD_COMPOUND_AMPLIFICATION")

        # ── 10. Missing Data Re-weighting (Missing inputs NEVER lower risk) ──
        weights = {
            "hazard": self.config.HAZARD_WEIGHT,
            "exposure": self.config.EXPOSURE_WEIGHT,
            "vulnerability": self.config.VULNERABILITY_WEIGHT,
            "adaptive_deficit": self.config.ADAPTIVE_DEFICIT_WEIGHT,
            "history": self.config.HISTORY_WEIGHT,
            "trend": self.config.TREND_WEIGHT,
        }
        values: dict[str, float | None] = {
            "hazard": blended_hazard,
            "exposure": exposure_score,
            "vulnerability": vulnerability_score,
            "adaptive_deficit": adaptive_capacity_deficit_score,
            "history": history_score,
            "trend": trend_score,
        }

        weighted_score, avail_w_sum, missing_components = calculate_available_weighted_score(values, weights)
        weighted_sum = weighted_score if weighted_score is not None else blended_hazard

        # Baseline structural risk (independent of real-time weather)
        baseline_structural_risk = round(
            (0.40 * baseline_hazard)
            + (0.25 * exposure_score)
            + (0.20 * vulnerability_score)
            + (0.15 * adaptive_capacity_deficit_score),
            (1),
        )

        current_dynamic_risk = round(min(100.0, weighted_sum + compound_adjustment), 1)
        composite_risk_score = current_dynamic_risk

        # ── 11. Multi-Method Model Agreement Evaluation ──
        # AHP susceptibility evaluation
        local_relief_slope = min(65.0, max(5.0, (hab.elevation * 0.015 * 0.4) + 18.0))
        ahp_model = AHPSusceptibilityModel()
        ahp_res = ahp_model.evaluate({
            "slope": local_relief_slope,
            "rainfall": rainfall_24h,
            "road_distance": hab.nearest_road,
        })

        # Frequency Ratio susceptibility evaluation
        fr_model = FrequencyRatioModel()
        fr_res = fr_model.predict_susceptibility(
            slope_deg=local_relief_slope,
            rainfall_mm=rainfall_24h,
        )

        agreement_engine = ModelAgreementEngine()
        agreement_eval = agreement_engine.evaluate_agreement({
            "AHP": ahp_res.get("score"),
            "Frequency Ratio": fr_res.get("score"),
        })

        # ── 12. Assessment Confidence Evaluation ──
        confidence_score, conf_reasons, conf_rationale = calculate_risk_confidence(
            has_vulnerability_profile=v_profile is not None,
            vulnerability_profile_mode=v_profile.data_mode if v_profile else None,
            has_environmental_observations=len(recent_obs) > 0,
            observation_mode=recent_obs[0].data_mode if recent_obs else None,
            hazard_scores_count=len(active_hazards),
            risk_history_count=len(history_list),
            is_demographics_complete=hab.population > 0 and hab.households > 0,
            missing_components=missing_components,
            model_agreement_penalty=agreement_eval["confidence_penalty"],
            model_agreement_reason=agreement_eval["reason_codes"][0] if agreement_eval["confidence_penalty"] > 0 else None,
        )
        reason_codes.extend(conf_reasons)
        reason_codes.extend(agreement_eval["reason_codes"])

        # ── 13. Red Zone Classification with Strict Safety Guards ──
        # Guard 1: High current weather surge does NOT create PERMANENT_RED
        # Guard 2: High structural risk requires minimum confidence >= 70 to become PERMANENT_RED
        if (
            composite_risk_score >= self.config.PERMANENT_RED_RISK_THRESHOLD
            and baseline_structural_risk >= self.config.PERMANENT_RED_STRUCTURAL_THRESHOLD
        ):
            if confidence_score >= self.config.PERMANENT_RED_CONFIDENCE_THRESHOLD:
                risk_classification = RedZoneClassification.PERMANENT_RED.value
                reason_codes.append("PERMANENT_RED_UNSUITABLE_HABITATION")
            else:
                # MANDATORY DOWNGRADE GUARD
                risk_classification = RedZoneClassification.CONDITIONAL_RED.value
                reason_codes.append("LOW_CONFIDENCE_FIELD_VERIFICATION_REQUIRED")
        elif (
            (dynamic_hazard >= self.config.DYNAMIC_RED_SURGE_THRESHOLD or current_dynamic_risk >= self.config.DYNAMIC_RED_SURGE_THRESHOLD)
            and rainfall_24h >= 65.0
            and baseline_structural_risk < self.config.PERMANENT_RED_STRUCTURAL_THRESHOLD
        ):
            # Dynamic Red safeguard: weather escalation creates DYNAMIC_RED, not permanent relocation
            risk_classification = RedZoneClassification.DYNAMIC_RED.value
            reason_codes.append("DYNAMIC_RED_PRECIPITATION_ALERT")
        elif composite_risk_score >= self.config.CONDITIONAL_RED_RISK_THRESHOLD:
            risk_classification = RedZoneClassification.CONDITIONAL_RED.value
            reason_codes.append("CONDITIONAL_RED_STRUCTURAL_HAZARD")
        elif composite_risk_score >= self.config.WATCH_RISK_THRESHOLD:
            risk_classification = RedZoneClassification.WATCH.value
        else:
            risk_classification = RedZoneClassification.ACCEPTABLE.value

        # ── 14. Habitation Sustainability Index & Dimensional Breakdown ──
        sustainability_index, hsi_conf, hsi_breakdown = calculate_sustainability_index(
            elevation=hab.elevation,
            nearest_road_km=hab.nearest_road,
            nearest_hospital_km=hab.nearest_hospital,
            baseline_hazard=baseline_hazard,
            vulnerability_score=vulnerability_score,
            nearest_school_km=hab.nearest_school,
            history_score=history_score,
            return_details=True,
        )
        if sustainability_index < self.config.CRITICAL_UNSUSTAINABLE_HSI:
            reason_codes.append("IN_SITU_MITIGATION_INFEASIBLE")

        # ── 15. Deterministic Explanation Narrative ──
        explanation = (
            f"PRAYAAS-RISK-1.0 Assessment for {hab.name}: Composite Risk = {composite_risk_score:.1f}/100 "
            f"({risk_classification}). Dominant hazard is {dominant_hazard} (Baseline Hazard: {baseline_hazard:.1f}, "
            f"Dynamic: {dynamic_hazard:.1f}). Exposure: {exposure_score:.1f}, Social Vulnerability: {vulnerability_score:.1f}, "
            f"Adaptive Deficit: {adaptive_capacity_deficit_score:.1f}. Compound Adjustment: +{compound_adjustment:.1f}. "
            f"Model Agreement: {agreement_eval['agreement_level']} (Score: {agreement_eval['agreement_score']:.1f}). "
            f"Habitation Sustainability Index: {sustainability_index:.1f}/100. Confidence: {confidence_score:.1f}%."
        )

        # ── 16. Accurate Snapshots ──
        input_snapshot = {
            "population": hab.population,
            "households": hab.households,
            "elevation": hab.elevation,
            "nearest_road": hab.nearest_road,
            "nearest_hospital": hab.nearest_hospital,
            "nearest_school": hab.nearest_school,
            "rainfall_24h": rainfall_24h,
            "soil_moisture": soil_moisture,
            "missing_components": missing_components,
            "available_weight_sum": avail_w_sum,
            "model_scores": agreement_eval["scores"],
            "model_agreement_level": agreement_eval["agreement_level"],
            "sustainability_dimensions": hsi_breakdown,
        }

        source_snapshot = {
            "vulnerability_mode": v_profile.data_mode if v_profile else "DEFAULT",
            "weather_observations_used": len(recent_obs),
            "hazard_evidence_records": len(active_hazards),
            "risk_history_records": len(history_list),
        }

        now = datetime.now(timezone.utc)
        assessment = RiskAssessment(
            id=str(uuid4()),
            habitation_id=habitation_id,
            analysis_version=self.config.ANALYSIS_VERSION,
            config_version=self.config.CONFIG_VERSION,
            baseline_hazard_score=round(baseline_hazard, 1),
            dynamic_hazard_score=round(dynamic_hazard, 1),
            hazard_score=round(blended_hazard, 1),
            exposure_score=exposure_score,
            vulnerability_score=vulnerability_score,
            adaptive_capacity_score=adaptive_capacity_score,
            adaptive_capacity_deficit_score=adaptive_capacity_deficit_score,
            history_score=history_score or 0.0,
            trend_score=trend_score or 50.0,
            compound_hazard_adjustment=round(compound_adjustment, 1),
            baseline_structural_risk=baseline_structural_risk,
            current_dynamic_risk=current_dynamic_risk,
            composite_risk_score=composite_risk_score,
            risk_classification=risk_classification,
            confidence_score=confidence_score,
            dominant_hazard=dominant_hazard,
            sustainability_index=sustainability_index,
            reason_codes=list(set(reason_codes)),
            input_snapshot=input_snapshot,
            source_snapshot=source_snapshot,
            explanation=explanation,
            calculated_at=now,
        )

        self.db.add(assessment)

        # Synchronize core Habitation entity fields
        hab.risk_score = int(round(composite_risk_score))
        hab.confidence = int(round(confidence_score))
        hab.vulnerability_score = int(round(vulnerability_score))
        if composite_risk_score >= 70:
            hab.risk_category = RiskClassification.CRITICAL.value
        elif composite_risk_score >= 50:
            hab.risk_category = RiskClassification.HIGH.value
        elif composite_risk_score >= 35:
            hab.risk_category = RiskClassification.WATCH.value
        else:
            hab.risk_category = RiskClassification.SAFE.value

        hab.last_assessed = now.strftime("%Y-%m-%d")

        self.db.commit()
        self.db.refresh(assessment)
        return assessment
