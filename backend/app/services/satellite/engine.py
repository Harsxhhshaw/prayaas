"""Satellite & Change Evidence Ingestion and Analysis Engine for Task 10."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import DataMode, EvidenceType
from app.models.evidence import EvidenceLayer
from app.models.ingestion import RasterDataset


class SatelliteEvidenceEngine:
    """Ingests and evaluates externally processed satellite and change detection datasets.
    Supports GeoTIFF, COG, GeoJSON, and vector/raster change products with honest provenance.
    """

    def __init__(self, db: Session):
        self.db = db

    def register_satellite_change_layer(
        self,
        name: str,
        evidence_type: str,
        provider: str,
        product: str,
        acquisition_date_start: datetime,
        acquisition_date_end: datetime,
        processing_method: str,
        resolution_meters: float,
        data_mode: str = DataMode.PUBLIC.value,
        coverage_bbox: dict[str, float] | None = None,
        source_metadata: dict[str, Any] | None = None,
        confidence_score: float = 85.0,
    ) -> EvidenceLayer:
        """Registers an externally processed satellite change layer with full scientific provenance."""
        # Validate evidence type
        valid_types = {
            EvidenceType.GROUND_DISPLACEMENT.value,
            EvidenceType.LANDSLIDE_CHANGE.value,
            EvidenceType.NDVI_CHANGE.value,
            EvidenceType.LAND_COVER_CHANGE.value,
            EvidenceType.RIVER_CHANNEL_CHANGE.value,
            EvidenceType.SURFACE_DISTURBANCE.value,
        }
        if evidence_type not in valid_types:
            raise ValueError(f"Invalid satellite change evidence type '{evidence_type}'. Must be one of {valid_types}.")

        quality_metrics = {
            "provider": provider,
            "product": product,
            "acquisition_dates": {
                "start": acquisition_date_start.isoformat(),
                "end": acquisition_date_end.isoformat(),
            },
            "processing_method": processing_method,
            "resolution_meters": resolution_meters,
            "coverage_bbox": coverage_bbox,
            "source_metadata": source_metadata or {},
        }

        layer = EvidenceLayer(
            id=f"EV-{uuid.uuid4().hex[:12].upper()}",
            name=name,
            evidence_type=evidence_type,
            data_mode=data_mode,
            spatial_resolution=resolution_meters,
            derivation_method=processing_method,
            quality_score=confidence_score / 100.0 if confidence_score else None,
            coverage_metadata=quality_metrics,
            metadata_json={
                "provider": provider,
                "product": product,
                "source_attribution": f"{provider} - {product}",
                "confidence_score": confidence_score,
                "is_active": True,
                "quality_metrics": quality_metrics,
            },
        )
        self.db.add(layer)
        self.db.commit()
        self.db.refresh(layer)
        return layer

    def compute_deterministic_raster_change(
        self,
        before_values: list[float],
        after_values: list[float],
        change_type: str = "DIFFERENCE",
        displacement_threshold_mm: float = 15.0,
    ) -> dict[str, Any]:
        """Calculates deterministic raster difference without labeling basic mathematics as AI."""
        if len(before_values) != len(after_values):
            raise ValueError("Before and after arrays must have equal length.")

        n = len(before_values)
        if n == 0:
            return {"mean_change": 0.0, "max_change": 0.0, "exceedance_count": 0, "change_mask": []}

        diffs = [after - before for before, after in zip(before_values, after_values)]
        mean_diff = round(sum(diffs) / n, 3)
        max_diff = round(max(diffs), 3)
        min_diff = round(min(diffs), 3)

        # Flag exceedance based on threshold (e.g. InSAR line-of-sight displacement in mm)
        exceedance_mask = [abs(d) >= displacement_threshold_mm for d in diffs]
        exceedance_count = sum(1 for m in exceedance_mask if m)

        return {
            "change_type": change_type,
            "sample_size": n,
            "mean_change": mean_diff,
            "max_change": max_diff,
            "min_change": min_diff,
            "threshold_used": displacement_threshold_mm,
            "exceedance_count": exceedance_count,
            "exceedance_ratio": round(exceedance_count / n, 3),
            "methodology": "DETERMINISTIC_GRID_DIFFERENCE (Non-ML)",
        }

    def evaluate_red_zone_satellite_safeguard(
        self,
        current_classification: str,
        satellite_change_detected: bool,
        mean_displacement_mm: float,
    ) -> dict[str, Any]:
        """Enforces statutory Red Zone safeguard:
        Satellite change evidence may contribute to DYNAMIC_RED or WATCH alerts,
        but can NEVER silently escalate a zone to PERMANENT_RED without field structural validation.
        """
        escalated_classification = current_classification
        safeguard_applied = False
        alert_reason = "No significant satellite change detected."

        if satellite_change_detected and abs(mean_displacement_mm) > 25.0:
            if current_classification not in ("PERMANENT_RED", "DYNAMIC_RED"):
                escalated_classification = "DYNAMIC_RED"
                safeguard_applied = True
                alert_reason = (
                    f"Satellite ground displacement of {mean_displacement_mm:.1f} mm detected. "
                    "Escalated to DYNAMIC_RED for field inspection. "
                    "Safeguard enforced: PERMANENT_RED requires geological field verification."
                )
        elif satellite_change_detected and abs(mean_displacement_mm) > 10.0:
            if current_classification == "ACCEPTABLE":
                escalated_classification = "WATCH"
                safeguard_applied = True
                alert_reason = f"Mild satellite ground displacement of {mean_displacement_mm:.1f} mm detected. Placed on WATCH."

        return {
            "current_classification": current_classification,
            "recommended_classification": escalated_classification,
            "safeguard_enforced": safeguard_applied,
            "explanation": alert_reason,
            "permanent_red_prevented": (current_classification != "PERMANENT_RED" and escalated_classification != "PERMANENT_RED"),
        }
