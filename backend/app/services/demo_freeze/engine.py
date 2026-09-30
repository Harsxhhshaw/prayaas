"""Demo Snapshot and Data Honesty Audit Engine for Task 10."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.candidate_discovery import CandidateParcel
from app.models.candidate_site import CandidateSite
from app.models.evidence import EvidenceLayer, HazardInventoryEvent
from app.models.governance import (
    ConsultationRecord,
    DemoSnapshot,
    FieldObservation,
    LandStatusRecord,
)
from app.models.habitation import Habitation
from app.models.hazard_zone import HazardZone
from app.models.infrastructure import InfrastructureAsset
from app.models.relocation import RelocationAssessment
from app.schemas.governance import DataHonestyAuditResponse


class DemoFreezeEngine:
    """Provides frozen deterministic demo snapshots and system-wide data honesty audits."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_raini_demo_snapshot(self) -> dict[str, Any]:
        """Retrieves or creates the stable, frozen demo snapshot for Raini HAB-002."""
        SNAPSHOT_ID = "DEMO-RAINI-HAB002-FINAL"

        record = self.db.query(DemoSnapshot).filter(DemoSnapshot.snapshot_id == SNAPSHOT_ID).first()
        if record:
            return record.data

        # Build clean deterministic snapshot
        snapshot_data = {
            "snapshot_id": SNAPSHOT_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_version": "PRAYAAS-1.0-PRODUCTION",
            "config_version": "1.0.0",
            "habitation": {
                "id": "HAB-002",
                "name": "Raini",
                "district": "Chamoli",
                "state": "Uttarakhand",
                "population": 1256,
                "households": 240,
                "need_score": 71.9,
                "urgency": "SHORT_TERM",
                "readiness_score": 55.0,
                "readiness_level": "MODERATE_READINESS",
                "matrix_position": "MODERATE_READINESS_REVIEW",
            },
            "risk": {
                "structural_risk": 80.0,
                "dynamic_risk": 65.0,
                "confidence_score": 68.0,
                "red_zone_classification": "DYNAMIC_RED",
            },
            "candidate_parcels": {
                "count": 182,
                "total_area_ha": 28754.5,
                "selected_candidate": {
                    "id": "PARCEL-E3247A11E0EC",
                    "rank": 1,
                    "area_hectares": 2.0,
                    "distance_km": 9.35,
                    "mean_slope_degrees": 9.9,
                    "suitability_score": 91.2,
                    "candidate_confidence": 37.8,
                    "robustness_score": 61.5,
                    "status": "REQUIRES_FIELD_REVIEW",
                },
            },
            "carrying_capacity": {
                "housing": "1500 persons capacity (MODELED bench density @ 75 persons/ha)",
                "water": "1500 persons baseline (JJM 55 lpcd PLANNING_ASSUMPTION)",
                "sanitation": "UNKNOWN (No percolation or DEWATS telemetry)",
                "healthcare": "UNKNOWN (PHC Pipalkoti headroom unmeasured)",
                "education": "1500 persons (RTE intake benchmark)",
                "transport": "OK (OSM arterial connection)",
                "utilities": "UNKNOWN (Substation loading unmeasured)",
                "environment": "OK (Slope stability setback compliance)",
                "overall_status": "UNKNOWN (KNOWN_DIMENSIONS_FEASIBLE)",
            },
            "optimization_alternatives": [
                {
                    "name": "ALTERNATIVE A (MIN_DISTANCE)",
                    "strategy": "MIN_DISTANCE",
                    "allocated_population": 1256,
                    "unallocated_population": 0,
                    "site_count": 1,
                    "avg_distance_km": 0.46,
                    "capacity_utilization_pct": 83.7,
                    "candidate_ids": ["PARCEL-5958B764DA60"],
                },
                {
                    "name": "ALTERNATIVE B (MIN_SITE_COUNT)",
                    "strategy": "MIN_SITE_COUNT",
                    "allocated_population": 1256,
                    "unallocated_population": 0,
                    "site_count": 1,
                    "avg_distance_km": 0.46,
                    "capacity_utilization_pct": 83.7,
                    "candidate_ids": ["PARCEL-5958B764DA60"],
                },
                {
                    "name": "ALTERNATIVE C (BALANCED)",
                    "strategy": "BALANCED",
                    "allocated_population": 1256,
                    "unallocated_population": 0,
                    "site_count": 2,
                    "avg_distance_km": 8.89,
                    "capacity_utilization_pct": 76.1,
                    "candidate_ids": ["PARCEL-E3247A11E0EC", "PARCEL-287BBE825053"],
                },
            ],
            "selected_plan": {
                "name": "ALTERNATIVE A (MIN_DISTANCE)",
                "strategy": "MIN_DISTANCE",
                "candidate_ids": ["PARCEL-5958B764DA60"],
                "assumption_dependence": "EXPLORATORY / ASSUMPTION-DEPENDENT",
                "binding_constraints": [],
            },
            "scenarios": {
                "BASELINE": "UNKNOWN (KNOWN_DIMENSIONS_FEASIBLE)",
                "WATER_STRESS": "FAIL (Water utilization 104.7% EXCEEDED)",
                "POPULATION_SURGE": "UNKNOWN (KNOWN_DIMENSIONS_FEASIBLE)",
                "ROAD_OUTAGE": "FAIL (Arterial transport severed)",
                "CANDIDATE_OUTAGE": "FAIL (1256 unallocated population)",
                "INFRA_UPGRADE": "UNKNOWN (KNOWN_DIMENSIONS_FEASIBLE)",
            },
            "plan_robustness": {
                "tested_scenarios": 6,
                "passed_scenarios": 0,
                "degraded_scenarios": 0,
                "failed_scenarios": 3,
                "unknown_scenarios": 3,
                "robustness_score": 0.0,
                "raw_count_report": "0 of 3 evaluable scenarios passed, 3 additional scenarios unresolved",
            },
            "remaining_blockers": [
                "FIELD_VERIFICATION_PENDING_ON_RECEPTION_SITES",
                "CARRYING_CAPACITY_INSUFFICIENT_EVIDENCE",
            ],
        }

        snapshot_record = DemoSnapshot(
            snapshot_id=SNAPSHOT_ID,
            habitation_id="HAB-002",
            title="Raini HAB-002 Production Freeze Snapshot",
            description="Frozen deterministic analysis for SIH presentation, demo video, and judging.",
            data=snapshot_data,
        )
        self.db.add(snapshot_record)
        self.db.commit()

        return snapshot_data

    def perform_data_honesty_audit(self) -> DataHonestyAuditResponse:
        """Audits database records across all primary models by data mode: PUBLIC, LIVE, MODELED, DEMO, FIELD."""
        table_counts: dict[str, dict[str, int]] = {}
        total_by_mode: dict[str, int] = {
            "PUBLIC": 0,
            "LIVE": 0,
            "MODELED": 0,
            "DEMO": 0,
            "FIELD": 0,
        }

        # 1. HazardInventoryEvent
        hie_counts = dict(
            self.db.query(HazardInventoryEvent.data_mode, func.count(HazardInventoryEvent.id))
            .group_by(HazardInventoryEvent.data_mode)
            .all()
        )
        table_counts["HazardInventoryEvent"] = hie_counts

        # 2. HazardZone
        hz_counts = dict(
            self.db.query(HazardZone.data_mode, func.count(HazardZone.id))
            .group_by(HazardZone.data_mode)
            .all()
        )
        table_counts["HazardZone"] = hz_counts

        # 3. EvidenceLayer
        el_counts = dict(
            self.db.query(EvidenceLayer.data_mode, func.count(EvidenceLayer.id))
            .group_by(EvidenceLayer.data_mode)
            .all()
        )
        table_counts["EvidenceLayer"] = el_counts

        # 4. CandidateParcel
        cp_counts = dict(
            self.db.query(CandidateParcel.data_mode, func.count(CandidateParcel.id))
            .group_by(CandidateParcel.data_mode)
            .all()
        )
        table_counts["CandidateParcel"] = cp_counts

        # 5. InfrastructureAsset
        ia_counts = dict(
            self.db.query(InfrastructureAsset.data_mode, func.count(InfrastructureAsset.id))
            .group_by(InfrastructureAsset.data_mode)
            .all()
        )
        table_counts["InfrastructureAsset"] = ia_counts

        # 6. CandidateSite
        cs_counts = dict(
            self.db.query(CandidateSite.data_mode, func.count(CandidateSite.id))
            .group_by(CandidateSite.data_mode)
            .all()
        )
        table_counts["CandidateSite"] = cs_counts

        # 7. FieldObservation
        fo_counts = dict(
            self.db.query(FieldObservation.data_mode, func.count(FieldObservation.id))
            .group_by(FieldObservation.data_mode)
            .all()
        )
        table_counts["FieldObservation"] = fo_counts

        # 8. ConsultationRecord
        cn_counts = dict(
            self.db.query(ConsultationRecord.data_mode, func.count(ConsultationRecord.id))
            .group_by(ConsultationRecord.data_mode)
            .all()
        )
        table_counts["ConsultationRecord"] = cn_counts

        # 9. LandStatusRecord
        ls_counts = dict(
            self.db.query(LandStatusRecord.data_mode, func.count(LandStatusRecord.id))
            .group_by(LandStatusRecord.data_mode)
            .all()
        )
        table_counts["LandStatusRecord"] = ls_counts

        # Aggregate total counts and sanitize keys
        sanitized_table_counts: dict[str, dict[str, int]] = {}
        for tbl, counts in table_counts.items():
            sanitized_table_counts[tbl] = {}
            for mode, count in counts.items():
                mode_str = str(mode) if mode is not None else "DEMO"
                sanitized_table_counts[tbl][mode_str] = sanitized_table_counts[tbl].get(mode_str, 0) + count
                if mode_str in total_by_mode:
                    total_by_mode[mode_str] += count
                else:
                    total_by_mode[mode_str] = count

        # Honest ML Status
        ml_status = {
            "Random Forest": "UNTRAINED / INSUFFICIENT_REAL_DATA",
            "FR": "DEMO / NOT VALIDATED",
            "AHP": "CONFIGURED / CONSISTENT",
            "Agreement": "UNKNOWN",
        }

        return DataHonestyAuditResponse(
            counts_by_mode=total_by_mode,
            table_breakdown=sanitized_table_counts,
            ml_status=ml_status,
            timestamp=datetime.now(timezone.utc),
        )
