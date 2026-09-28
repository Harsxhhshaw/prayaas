"""Deterministic Multi-Hazard Risk and Red Zone Classification Engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.enums import RedZoneClassification, RiskClassification
from app.models.habitation import Habitation
from app.models.ingestion import EnvironmentalObservation
from app.models.risk import RiskAssessment, VulnerabilityProfile
from app.services.risk.config import DEFAULT_RISK_CONFIG, RiskEngineConfig
from app.services.risk.confidence import calculate_risk_confidence


def calculate_sustainability_index(
    elevation: float,
    nearest_road_km: float,
    nearest_hospital_km: float,
    baseline_hazard: float,
    vulnerability_score: float,
) -> float:
    """Calculates Habitation Sustainability Index (HSI, 0-100).

    Low HSI (< 35) indicates that in-situ engineering stabilization is economically/physically infeasible.
    """
    # Terrain & isolation penalty
    terrain_penalty = min(30.0, (elevation / 3000.0) * 20.0 + (nearest_road_km * 2.0))
    hazard_penalty = (baseline_hazard / 100.0) * 45.0
    isolation_penalty = min(25.0, (nearest_hospital_km / 20.0) * 25.0)

    hsi = 100.0 - (terrain_penalty + hazard_penalty + isolation_penalty)
    return max(5.0, min(95.0, round(hsi, 1)))


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

        # ── 3. Multi-Hazard Aggregation ──
        hazard_list = hab.hazard_scores if isinstance(hab.hazard_scores, list) else []
        dominant_hazard = "LANDSLIDE"
        reason_codes: list[str] = []

        if hazard_list:
            sorted_hazards = sorted(hazard_list, key=lambda x: x.get("score", 0), reverse=True)
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
            # Extreme monsoon / cloudburst precipitation surge
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
        # Factors: population size, household density, elevation relief
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
            # Demographics fallback
            vulnerability_score = float(hab.vulnerability_score or 45.0)

        vulnerability_score = round(max(10.0, min(100.0, vulnerability_score)), 1)

        # ── 6. Adaptive Capacity Deficit ──
        # Road access, hospital distance, school
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

        # ── 7. History Score ──
        history_list = hab.risk_history if isinstance(hab.risk_history, list) else []
        if history_list:
            past_scores = [float(h.get("score", 50)) for h in history_list]
            history_score = round(sum(past_scores) / len(past_scores), 1)
        else:
            history_score = round(baseline_hazard * 0.8, 1)

        # ── 8. Trend Score ──
        if len(history_list) >= 2:
            first_score = float(history_list[0].get("score", 50))
            last_score = float(history_list[-1].get("score", 50))
            diff = last_score - first_score
            trend_score = round(max(0.0, min(100.0, 50.0 + (diff * 2.0))), 1)
            if diff > 10.0:
                reason_codes.append("ESCALATING_RISK_TRAJECTORY")
        else:
            trend_score = 50.0

        # ── 9. Compound Hazard Escalation ──
        compound_adjustment = 0.0
        if hazard_list and len(hazard_list) > 1:
            severe_secondary = [
                h for h in sorted_hazards[1:] if float(h.get("score", 0)) >= 50.0
            ]
            if severe_secondary:
                compound_adjustment = min(
                    self.config.MAX_COMPOUND_ADJUSTMENT,
                    len(severe_secondary) * 6.5,
                )
                reason_codes.append("MULTI_HAZARD_COMPOUND_AMPLIFICATION")

        # ── 10. Missing Data Re-weighting ──
        weights = {
            "hazard": self.config.HAZARD_WEIGHT,
            "exposure": self.config.EXPOSURE_WEIGHT,
            "vulnerability": self.config.VULNERABILITY_WEIGHT,
            "adaptive_deficit": self.config.ADAPTIVE_DEFICIT_WEIGHT,
            "history": self.config.HISTORY_WEIGHT,
            "trend": self.config.TREND_WEIGHT,
        }
        values = {
            "hazard": blended_hazard,
            "exposure": exposure_score,
            "vulnerability": vulnerability_score,
            "adaptive_deficit": adaptive_capacity_deficit_score,
            "history": history_score,
            "trend": trend_score,
        }

        # Normalize weights
        total_w = sum(weights.values())
        weighted_sum = sum((w / total_w) * values[k] for k, w in weights.items())

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

        # ── 11. Confidence Evaluation ──
        confidence_score, conf_reasons, conf_rationale = calculate_risk_confidence(
            has_vulnerability_profile=v_profile is not None,
            vulnerability_profile_mode=v_profile.data_mode if v_profile else None,
            has_environmental_observations=len(recent_obs) > 0,
            observation_mode=recent_obs[0].data_mode if recent_obs else None,
            hazard_scores_count=len(hazard_list),
            risk_history_count=len(history_list),
            is_demographics_complete=hab.population > 0 and hab.households > 0,
        )
        reason_codes.extend(conf_reasons)

        # ── 12. Red Zone Classification with Downgrade Guard ──
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
                reason_codes.append("LOW_CONFIDENCE_VERIFICATION_REQUIRED")
        elif (
            dynamic_hazard >= self.config.DYNAMIC_RED_SURGE_THRESHOLD
            and rainfall_24h >= 65.0
        ):
            risk_classification = RedZoneClassification.DYNAMIC_RED.value
            reason_codes.append("DYNAMIC_RED_PRECIPITATION_ALERT")
        elif composite_risk_score >= self.config.CONDITIONAL_RED_RISK_THRESHOLD:
            risk_classification = RedZoneClassification.CONDITIONAL_RED.value
            reason_codes.append("CONDITIONAL_RED_STRUCTURAL_HAZARD")
        elif composite_risk_score >= self.config.WATCH_RISK_THRESHOLD:
            risk_classification = RedZoneClassification.WATCH.value
        else:
            risk_classification = RedZoneClassification.ACCEPTABLE.value

        # ── 13. Habitation Sustainability Index ──
        sustainability_index = calculate_sustainability_index(
            elevation=hab.elevation,
            nearest_road_km=hab.nearest_road,
            nearest_hospital_km=hab.nearest_hospital,
            baseline_hazard=baseline_hazard,
            vulnerability_score=vulnerability_score,
        )
        if sustainability_index < self.config.CRITICAL_UNSUSTAINABLE_HSI:
            reason_codes.append("IN_SITU_MITIGATION_INFEASIBLE")

        # ── 14. Deterministic Explanation Narrative ──
        explanation = (
            f"PRAYAAS-RISK-1.0 Assessment for {hab.name}: Composite Risk = {composite_risk_score:.1f}/100 "
            f"({risk_classification}). Dominant hazard is {dominant_hazard} (Baseline Hazard: {baseline_hazard:.1f}, "
            f"Dynamic: {dynamic_hazard:.1f}). Exposure: {exposure_score:.1f}, Social Vulnerability: {vulnerability_score:.1f}, "
            f"Adaptive Deficit: {adaptive_capacity_deficit_score:.1f}. Compound Adjustment: +{compound_adjustment:.1f}. "
            f"Habitation Sustainability Index: {sustainability_index:.1f}/100. Confidence: {confidence_score:.1f}%."
        )

        # ── 15. Create and persist RiskAssessment ──
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
            history_score=history_score,
            trend_score=trend_score,
            compound_hazard_adjustment=round(compound_adjustment, 1),
            baseline_structural_risk=baseline_structural_risk,
            current_dynamic_risk=current_dynamic_risk,
            composite_risk_score=composite_risk_score,
            risk_classification=risk_classification,
            confidence_score=confidence_score,
            dominant_hazard=dominant_hazard,
            sustainability_index=sustainability_index,
            reason_codes=list(set(reason_codes)),
            input_snapshot={
                "population": hab.population,
                "households": hab.households,
                "elevation": hab.elevation,
                "nearest_road": hab.nearest_road,
                "nearest_hospital": hab.nearest_hospital,
                "rainfall_24h": rainfall_24h,
                "soil_moisture": soil_moisture,
            },
            source_snapshot={
                "vulnerability_mode": v_profile.data_mode if v_profile else "DEFAULT",
                "weather_observations": len(recent_obs),
            },
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
