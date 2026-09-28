"""Deterministic Relocation Need and Readiness Engine implementing PRAYAAS-RELOCATION-1.0."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.candidate_site import CandidateSite
from app.models.enums import DataMode, ReadinessLevel, RelocationUrgency, VerificationStatus
from app.models.habitation import Habitation
from app.models.relocation import RelocationAssessment
from app.models.relocation_priority import RelocationPriority
from app.models.risk import RiskAssessment
from app.services.relocation.config import DEFAULT_RELOCATION_CONFIG, RelocationEngineConfig
from app.services.risk.engine import RiskEngine


class RelocationEngine:
    """Calculates Relocation Need and Institutional Readiness strictly decoupled."""

    def __init__(self, db: Session, config: RelocationEngineConfig = DEFAULT_RELOCATION_CONFIG) -> None:
        self.db = db
        self.config = config

    def assess_habitation(self, habitation_id: str, risk_assessment_id: str | None = None) -> RelocationAssessment:
        hab = self.db.query(Habitation).filter(Habitation.id == habitation_id).first()
        if not hab:
            raise ValueError(f"Habitation with id {habitation_id} not found")

        # 1. Fetch or compute RiskAssessment
        risk_assessment: RiskAssessment | None = None
        if risk_assessment_id:
            risk_assessment = (
                self.db.query(RiskAssessment)
                .filter(RiskAssessment.id == risk_assessment_id)
                .first()
            )
        if not risk_assessment:
            risk_assessment = (
                self.db.query(RiskAssessment)
                .filter(RiskAssessment.habitation_id == habitation_id)
                .order_by(RiskAssessment.calculated_at.desc())
                .first()
            )
        if not risk_assessment:
            risk_engine = RiskEngine(self.db)
            risk_assessment = risk_engine.assess_habitation(habitation_id)

        # ── 2. Calculate NEED SCORE (Candidate sites NEVER reduce this!) ──
        structural_risk = risk_assessment.baseline_structural_risk
        vulnerability = risk_assessment.vulnerability_score
        history = risk_assessment.history_score
        trend = risk_assessment.trend_score
        isolation = risk_assessment.adaptive_capacity_deficit_score
        sustainability_deficit = max(0.0, 100.0 - risk_assessment.sustainability_index)

        need_components = {
            "baseline_structural_risk": structural_risk,
            "vulnerability": vulnerability,
            "history": history,
            "trend": trend,
            "isolation_deficit": isolation,
            "sustainability_deficit": sustainability_deficit,
        }

        need_raw = (
            (self.config.NEED_STRUCTURAL_RISK_WEIGHT * structural_risk)
            + (self.config.NEED_VULNERABILITY_WEIGHT * vulnerability)
            + (self.config.NEED_DISASTER_HISTORY_WEIGHT * history)
            + (self.config.NEED_TREND_WEIGHT * trend)
            + (self.config.NEED_ISOLATION_WEIGHT * isolation)
            + (self.config.NEED_SUSTAINABILITY_DEFICIT_WEIGHT * sustainability_deficit)
        )
        need_score = round(max(5.0, min(100.0, need_raw)), 1)

        # ── 3. Calculate READINESS SCORE & Apply Strict Caps ──
        candidate_sites = (
            self.db.query(CandidateSite)
            .filter(CandidateSite.district == hab.district)
            .all()
        )

        readiness_gaps: list[str] = []
        reason_codes: list[str] = []
        readiness_components: dict[str, Any] = {}
        assigned_site: CandidateSite | None = None

        if not candidate_sites:
            readiness_score = self.config.CAP_NO_CANDIDATE_SITES
            readiness_gaps.append("NO_CANDIDATE_SITES_IDENTIFIED_IN_DISTRICT")
            reason_codes.append("READINESS_CRITICAL_NO_SITES")
            readiness_components = {
                "site_availability": 0.0,
                "infrastructure_access": 0.0,
                "land_clearance": 0.0,
                "carrying_capacity_coverage": 0.0,
            }
        else:
            # Sort by suitability
            candidate_sites_sorted = sorted(candidate_sites, key=lambda s: s.suitability_score, reverse=True)
            assigned_site = candidate_sites_sorted[0]

            # Average site attributes
            avg_suitability = sum(s.suitability_score for s in candidate_sites) / len(candidate_sites)
            road_score = (sum(1 for s in candidate_sites if s.road_access) / len(candidate_sites)) * 100.0
            water_score = (sum(1 for s in candidate_sites if s.water_access) / len(candidate_sites)) * 100.0
            power_score = (sum(1 for s in candidate_sites if s.electricity_access) / len(candidate_sites)) * 100.0
            infra_score = (road_score + water_score + power_score) / 3.0

            total_capacity = sum(s.carrying_capacity for s in candidate_sites)
            capacity_coverage = min(100.0, (total_capacity / max(1, hab.population)) * 100.0)

            readiness_components = {
                "site_availability": round(avg_suitability, 1),
                "infrastructure_access": round(infra_score, 1),
                "carrying_capacity_coverage": round(capacity_coverage, 1),
                "candidate_sites_count": len(candidate_sites),
                "top_site_name": assigned_site.name,
            }

            raw_readiness = (avg_suitability * 0.40) + (infra_score * 0.35) + (capacity_coverage * 0.25)
            readiness_score = raw_readiness

            # ── APPLY STRICT READINESS CAPS ──
            # Cap 1: All sites are DEMO only
            all_demo = all(s.data_mode == DataMode.DEMO.value for s in candidate_sites)
            if all_demo and readiness_score > self.config.CAP_DEMO_ONLY_SITES:
                readiness_score = self.config.CAP_DEMO_ONLY_SITES
                readiness_gaps.append("CANDIDATE_SITES_SYNTHETIC_BENCHMARK_ONLY")
                reason_codes.append("CAP_APPLIED_DEMO_ONLY_SITES")

            # Cap 2: Sites are unverified (PENDING)
            all_unverified = all(s.verification_status == VerificationStatus.PENDING.value for s in candidate_sites)
            if all_unverified and readiness_score > self.config.CAP_UNVERIFIED_SITES:
                readiness_score = self.config.CAP_UNVERIFIED_SITES
                readiness_gaps.append("FIELD_VERIFICATION_PENDING_ON_RECEPTION_SITES")
                reason_codes.append("CAP_APPLIED_UNVERIFIED_SITES")

            # Cap 3: Carrying capacity unassessed or zero
            if total_capacity <= 0 and readiness_score > self.config.CAP_NO_CARRYING_CAPACITY:
                readiness_score = self.config.CAP_NO_CARRYING_CAPACITY
                readiness_gaps.append("CARRYING_CAPACITY_ASSESSMENT_REQUIRED")
                reason_codes.append("CAP_APPLIED_CARRYING_CAPACITY_MISSING")

            readiness_score = round(max(5.0, min(100.0, readiness_score)), 1)

        # ── 4. Readiness Level ──
        if readiness_score >= self.config.READINESS_HIGH_THRESHOLD:
            readiness_level = ReadinessLevel.HIGH_READINESS.value
        elif readiness_score >= self.config.READINESS_MODERATE_THRESHOLD:
            readiness_level = ReadinessLevel.MODERATE_READINESS.value
        elif readiness_score >= self.config.READINESS_LOW_THRESHOLD:
            readiness_level = ReadinessLevel.LOW_READINESS.value
        else:
            readiness_level = ReadinessLevel.NOT_READY.value

        # ── 5. Urgency Classification with Dynamic Red Safety Rule ──
        # Dynamic Red safety rule: dynamic surge escalates to IMMEDIATE alert without falsifying structural need
        if risk_assessment.risk_classification == "DYNAMIC_RED":
            urgency = RelocationUrgency.IMMEDIATE.value
            reason_codes.append("DYNAMIC_RED_SURGE_IMMEDIATE_REVIEW")
        elif need_score >= self.config.URGENCY_IMMEDIATE_THRESHOLD:
            urgency = RelocationUrgency.IMMEDIATE.value
            reason_codes.append("IMMEDIATE_STRUCTURAL_RELOCATION_REQUIRED")
        elif need_score >= self.config.URGENCY_SHORT_TERM_THRESHOLD:
            urgency = RelocationUrgency.SHORT_TERM.value
            reason_codes.append("SHORT_TERM_RELOCATION_PLANNING")
        elif need_score >= self.config.URGENCY_MEDIUM_TERM_THRESHOLD:
            urgency = RelocationUrgency.MEDIUM_TERM.value
            reason_codes.append("MEDIUM_TERM_RELOCATION_MONITORING")
        else:
            urgency = RelocationUrgency.MONITOR.value
            reason_codes.append("MONITOR_IN_SITU")

        # Need-Readiness Matrix Positioning
        if need_score >= 55.0 and readiness_score < 50.0:
            matrix_position = "ACUTE_RISK_READINESS_BOTTLENECK"
            reason_codes.append("ACUTE_RISK_READINESS_BOTTLENECK")
        elif need_score >= 55.0 and readiness_score >= 50.0:
            matrix_position = "READY_FOR_EXECUTION"
            reason_codes.append("READY_FOR_EXECUTION")
        elif need_score < 55.0 and readiness_score >= 50.0:
            matrix_position = "RESERVE_CAPACITY"
        else:
            matrix_position = "ROUTINE_MONITORING"

        # ── 6. Deterministic Explanation ──
        explanation = (
            f"PRAYAAS-RELOCATION-1.0: Relocation Need Score = {need_score:.1f}/100 ({urgency}). "
            f"Readiness Score = {readiness_score:.1f}/100 ({readiness_level}). Matrix Position: {matrix_position}. "
            f"Structural relocation need is driven by baseline structural risk ({structural_risk:.1f}) and "
            f"social vulnerability ({vulnerability:.1f}). Candidate sites NEVER decrease relocation need. "
            f"Identified readiness gaps: {', '.join(readiness_gaps) if readiness_gaps else 'None'}."
        )

        now = datetime.now(timezone.utc)
        rel_assessment = RelocationAssessment(
            id=str(uuid4()),
            habitation_id=habitation_id,
            risk_assessment_id=risk_assessment.id,
            analysis_version=self.config.ANALYSIS_VERSION,
            config_version=self.config.CONFIG_VERSION,
            need_score=need_score,
            urgency=urgency,
            readiness_score=readiness_score,
            readiness_level=readiness_level,
            need_components=need_components,
            readiness_components=readiness_components,
            readiness_gaps=readiness_gaps,
            reason_codes=list(set(reason_codes)),
            explanation=explanation,
            confidence_score=risk_assessment.confidence_score,
            calculated_at=now,
        )

        self.db.add(rel_assessment)

        # Update Habitation urgency
        hab.urgency = urgency

        # Update or create RelocationPriority record
        priority = (
            self.db.query(RelocationPriority)
            .filter(RelocationPriority.habitation_id == habitation_id)
            .first()
        )
        if not priority:
            priority = RelocationPriority(
                id=str(uuid4()),
                habitation_id=habitation_id,
                habitation_name=hab.name,
                urgency=urgency,
                risk_score=int(round(risk_assessment.composite_risk_score)),
                population=hab.population,
                district=hab.district,
                assigned_site_id=assigned_site.id if assigned_site else None,
                assigned_site_name=assigned_site.name if assigned_site else None,
                estimated_cost=round(hab.population * 12.5, 1) if hab.population else 50.0,
                timeline_months=6 if urgency == RelocationUrgency.IMMEDIATE.value else 18,
            )
            self.db.add(priority)
        else:
            priority.urgency = urgency
            priority.risk_score = int(round(risk_assessment.composite_risk_score))
            if assigned_site:
                priority.assigned_site_id = assigned_site.id
                priority.assigned_site_name = assigned_site.name

        self.db.commit()
        self.db.refresh(rel_assessment)
        return rel_assessment
