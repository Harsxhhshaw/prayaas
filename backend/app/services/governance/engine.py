"""Governance, Field Evidence, Land Status, and Audit Engine for Task 10."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.candidate_discovery import CandidateParcel
from app.models.enums import (
    DataMode,
    GovernanceReviewStage,
    LandCategory,
    LandStatus,
    VerificationLevel,
    VerificationStatus,
)
from app.models.governance import (
    AnalyticalOverrideRecord,
    ConsultationRecord,
    FieldObservation,
    GovernanceReview,
    LandStatusRecord,
)
from app.models.habitation import Habitation
from app.schemas.governance import (
    AnalyticalOverrideCreate,
    ConsultationCreate,
    FieldObservationCreate,
    FieldObservationVerifyRequest,
    GovernanceReviewCreate,
    LandStatusCreate,
)


class GovernanceEngine:
    """Handles field observation ingestion, progressive verification, land status, community consultations, human overrides, and audit trails."""

    def __init__(self, db: Session):
        self.db = db

    # ── Audit Trail ──

    def log_audit_event(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: str = "SYSTEM",
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Appends an immutable audit log entry."""
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            details=details or {},
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ── Field Observations ──

    def record_field_observation(
        self,
        req: FieldObservationCreate,
        user_id: str = "FIELD_OFFICER",
    ) -> FieldObservation:
        """Records ground-level field observation. Always starts at FIELD_OBSERVED verification level."""
        geom = None
        if req.latitude is not None and req.longitude is not None:
            geom = from_shape(Point(req.longitude, req.latitude), srid=4326)

        obs = FieldObservation(
            id=f"OBS-{uuid.uuid4().hex[:12].upper()}",
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            observation_type=req.observation_type,
            geom=geom,
            observed_at=datetime.now(timezone.utc),
            observer_name=req.observer_name,
            observer_role=req.observer_role,
            notes=req.notes,
            evidence_values=req.evidence_values,
            data_mode=DataMode.FIELD.value,
            verification_level=VerificationLevel.FIELD_OBSERVED.value,
            attachments_metadata=req.attachments_metadata,
            source_metadata=req.source_metadata,
        )
        self.db.add(obs)
        self.db.commit()
        self.db.refresh(obs)

        # Audit log
        self.log_audit_event(
            action="FIELD_OBSERVATION_RECORDED",
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            user_id=user_id,
            details={
                "observation_id": obs.id,
                "observation_type": obs.observation_type,
                "verification_level": obs.verification_level,
            },
        )

        return obs

    def verify_field_observation(
        self,
        observation_id: str,
        req: FieldObservationVerifyRequest,
    ) -> FieldObservation:
        """Upgrades a field observation to TECHNICALLY_VERIFIED or AUTHORITY_REVIEWED."""
        obs = self.db.query(FieldObservation).filter(FieldObservation.id == observation_id).first()
        if not obs:
            raise ValueError(f"FieldObservation '{observation_id}' not found.")

        old_level = obs.verification_level
        obs.verification_level = req.verification_level
        obs.verified_by = req.verified_by
        obs.verified_at = datetime.now(timezone.utc)
        obs.technical_notes = req.technical_notes

        self.db.commit()
        self.db.refresh(obs)

        # Incrementally update Candidate Parcel verification if applicable
        if obs.entity_type == "CANDIDATE_PARCEL" and obs.verification_level == VerificationLevel.TECHNICALLY_VERIFIED.value:
            parcel = self.db.query(CandidateParcel).filter(CandidateParcel.id == obs.entity_id).first()
            if parcel:
                # Modestly improve parcel confidence without exceeding realistic mountain field cap (80.0)
                parcel.confidence_score = min(80.0, parcel.confidence_score + 5.0)
                self.db.commit()

        # Audit log
        self.log_audit_event(
            action="FIELD_OBSERVATION_VERIFIED",
            entity_type=obs.entity_type,
            entity_id=obs.entity_id,
            user_id=req.verified_by,
            details={
                "observation_id": obs.id,
                "old_level": old_level,
                "new_level": obs.verification_level,
                "technical_notes": req.technical_notes,
            },
        )

        return obs

    def get_observations_for_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[FieldObservation]:
        """Retrieves all field observations for an entity ordered by observation date."""
        return (
            self.db.query(FieldObservation)
            .filter(
                FieldObservation.entity_type == entity_type,
                FieldObservation.entity_id == entity_id,
            )
            .order_by(FieldObservation.observed_at.desc())
            .all()
        )

    # ── Land Status Verification Gates ──

    def record_land_status(
        self,
        req: LandStatusCreate,
        user_id: str = "REVENUE_ANALYST",
    ) -> LandStatusRecord:
        """Records or updates land tenure, forest status, or acquisition status."""
        rec = LandStatusRecord(
            id=f"LND-{uuid.uuid4().hex[:12].upper()}",
            parcel_candidate_id=req.parcel_candidate_id,
            category=req.category,
            status=req.status,
            source_reference=req.source_reference,
            document_reference=req.document_reference,
            reviewed_by=req.reviewed_by or user_id,
            reviewed_at=datetime.now(timezone.utc),
            notes=req.notes,
            data_mode=req.data_mode,
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)

        self.log_audit_event(
            action="LAND_STATUS_RECORDED",
            entity_type="CANDIDATE_PARCEL",
            entity_id=req.parcel_candidate_id,
            user_id=user_id,
            details={
                "land_status_id": rec.id,
                "category": rec.category,
                "status": rec.status,
            },
        )

        return rec

    def get_land_status_for_parcel(
        self,
        parcel_candidate_id: str,
    ) -> list[LandStatusRecord]:
        """Retrieves legal and cadastral records for a candidate parcel."""
        return (
            self.db.query(LandStatusRecord)
            .filter(LandStatusRecord.parcel_candidate_id == parcel_candidate_id)
            .order_by(LandStatusRecord.created_at.desc())
            .all()
        )

    # ── Community Consultations ──

    def record_consultation(
        self,
        req: ConsultationCreate,
        user_id: str = "COMMUNITY_FACILITATOR",
    ) -> ConsultationRecord:
        """Records community consultation or Gram Sabha hearing.
        Strictly affects readiness and governance, NEVER modifies geological hazard risk!
        """
        cns = ConsultationRecord(
            id=f"CNS-{uuid.uuid4().hex[:12].upper()}",
            habitation_id=req.habitation_id,
            consultation_date=datetime.now(timezone.utc),
            participant_count=req.participant_count,
            method=req.method,
            questions_responses=req.questions_responses,
            concerns=req.concerns,
            preferences=req.preferences,
            source_attachment=req.source_attachment,
            verification_status=VerificationStatus.VERIFIED.value if req.data_mode == "FIELD" else VerificationStatus.PENDING.value,
            data_mode=req.data_mode,
        )
        self.db.add(cns)
        self.db.commit()
        self.db.refresh(cns)

        self.log_audit_event(
            action="COMMUNITY_CONSULTATION_RECORDED",
            entity_type="HABITATION",
            entity_id=req.habitation_id,
            user_id=user_id,
            details={
                "consultation_id": cns.id,
                "participants": cns.participant_count,
                "method": cns.method,
            },
        )

        return cns

    def get_consultations_for_habitation(
        self,
        habitation_id: str,
    ) -> list[ConsultationRecord]:
        """Returns all recorded consultations for a habitation."""
        return (
            self.db.query(ConsultationRecord)
            .filter(ConsultationRecord.habitation_id == habitation_id)
            .order_by(ConsultationRecord.consultation_date.desc())
            .all()
        )

    # ── Governance Review Workflow ──

    def record_governance_review(
        self,
        req: GovernanceReviewCreate,
        user_id: str = "ADMINISTRATOR",
    ) -> GovernanceReview:
        """Transitions an entity through governance review stages."""
        rev = GovernanceReview(
            id=f"GOV-{uuid.uuid4().hex[:12].upper()}",
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            review_stage=req.review_stage,
            assigned_to=req.assigned_to,
            reviewer_role=req.reviewer_role,
            review_notes=req.review_notes,
            action_taken=req.action_taken,
        )
        self.db.add(rev)
        self.db.commit()
        self.db.refresh(rev)

        self.log_audit_event(
            action="GOVERNANCE_REVIEW_STAGE_UPDATED",
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            user_id=user_id,
            details={
                "review_id": rev.id,
                "stage": rev.review_stage,
                "action": rev.action_taken,
            },
        )

        return rev

    def get_governance_reviews(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[GovernanceReview]:
        """Returns governance review history."""
        return (
            self.db.query(GovernanceReview)
            .filter(
                GovernanceReview.entity_type == entity_type,
                GovernanceReview.entity_id == entity_id,
            )
            .order_by(GovernanceReview.created_at.desc())
            .all()
        )

    # ── Human Analytical Override ──

    def apply_analytical_override(
        self,
        req: AnalyticalOverrideCreate,
    ) -> AnalyticalOverrideRecord:
        """Logs an auditable human analytical override. Never deletes or mutates original historical analytical records."""
        override = AnalyticalOverrideRecord(
            id=f"OVR-{uuid.uuid4().hex[:12].upper()}",
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            field_name=req.field_name,
            original_value=req.original_value,
            override_value=req.override_value,
            reason=req.reason,
            reviewer=req.reviewer,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(override)
        self.db.commit()
        self.db.refresh(override)

        self.log_audit_event(
            action="ANALYTICAL_OVERRIDE_APPLIED",
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            user_id=req.reviewer,
            details={
                "override_id": override.id,
                "field_name": req.field_name,
                "original_value": req.original_value,
                "override_value": req.override_value,
                "reason": req.reason,
            },
        )

        return override

    def get_overrides_for_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[AnalyticalOverrideRecord]:
        """Returns all applied analytical overrides for an entity."""
        return (
            self.db.query(AnalyticalOverrideRecord)
            .filter(
                AnalyticalOverrideRecord.entity_type == entity_type,
                AnalyticalOverrideRecord.entity_id == entity_id,
            )
            .order_by(AnalyticalOverrideRecord.timestamp.desc())
            .all()
        )
