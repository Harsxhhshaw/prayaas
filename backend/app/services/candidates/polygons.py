"""Contiguous Region Extraction, Minimum Parcel Sizing, and Polygon Cleaning.

Converts discrete feasible raster/grid cells into contiguous metric land parcels.
Enforces minimum contiguous parcel area thresholds (e.g. >= 2.0 hectares).
Provides polygon validation, topology preservation, and centroid generation.
"""

from __future__ import annotations

import math
from typing import Any
from dataclasses import dataclass, field
import numpy as np
from scipy import ndimage
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union
from shapely.validation import make_valid

from app.services.candidates.config import CandidateDiscoveryConfig, DEFAULT_CANDIDATE_CONFIG
from app.services.terrain.pipeline import degree_cell_size_to_meters


@dataclass
class FeasibleCell:
    """A spatial grid cell that survived hard exclusion screening."""

    row: int
    col: int
    lat: float
    lng: float
    slope_deg: float
    suitability_score: float
    confidence_score: float
    criterion_scores: dict[str, float]
    exclusion_summary: dict[str, str]
    dist_to_origin_km: float


@dataclass
class ExtractedParcel:
    """A contiguous candidate land parcel formed by clustering neighboring feasible cells."""

    geom_wkt: str
    centroid_lat: float
    centroid_lng: float
    area_sq_km: float
    area_hectares: float
    cell_count: int
    suitability_score: float
    confidence_score: float
    criteria_scores: dict[str, float]
    exclusion_summary: dict[str, str]
    distance_from_origin_km: float
    effective_width_m: float = 0.0
    aspect_ratio: float = 1.0
    compactness: float = 1.0
    mean_slope_degrees: float = 0.0
    is_rejected: bool = False
    rejection_reason: str | None = None


# Orthogonal 4-connectivity structure (shared edges only; prevents diagonal-only corner connections)
STRUCTURE_4_CONNECTIVITY = np.array([
    [0, 1, 0],
    [1, 1, 1],
    [0, 1, 0],
], dtype=np.int32)

STRUCTURE_8_CONNECTIVITY = np.ones((3, 3), dtype=np.int32)


def compute_polygon_quality_metrics(
    geom: Any,
    cell_dx_m: float,
    cell_dy_m: float,
    res_deg_x: float,
    res_deg_y: float,
) -> tuple[float, float, float]:
    """Computes effective width (m), aspect ratio, and compactness for sliver detection.

    Returns:
        (effective_width_m, aspect_ratio, compactness)
    """
    if geom.is_empty or not geom.is_valid:
        return 0.0, 999.0, 0.0

    rect = geom.minimum_rotated_rectangle
    if rect.geom_type != "Polygon":
        return 0.0, 999.0, 0.0

    coords = list(rect.exterior.coords)
    if len(coords) < 4:
        return 0.0, 999.0, 0.0

    m_per_deg_x = cell_dx_m / max(1e-7, res_deg_x)
    m_per_deg_y = cell_dy_m / max(1e-7, res_deg_y)

    p0 = coords[0]
    p1 = coords[1]
    p2 = coords[2]

    len1 = math.hypot((p1[0] - p0[0]) * m_per_deg_x, (p1[1] - p0[1]) * m_per_deg_y)
    len2 = math.hypot((p2[0] - p1[0]) * m_per_deg_x, (p2[1] - p1[1]) * m_per_deg_y)

    length_m = max(len1, len2)
    width_m = min(len1, len2)
    aspect_ratio = length_m / max(1.0, width_m)

    # Polsby-Popper compactness (4 * pi * Area / Perimeter^2)
    metric_perimeter = geom.length * ((m_per_deg_x + m_per_deg_y) / 2.0)
    metric_area = (geom.area / (res_deg_x * res_deg_y)) * (cell_dx_m * cell_dy_m)
    compactness = (4.0 * math.pi * metric_area) / max(1.0, metric_perimeter ** 2)

    return round(width_m, 1), round(aspect_ratio, 2), round(compactness, 4)


class ContiguousParcelExtractor:
    """Groups feasible cells into contiguous land polygons and enforces geometric feasibility constraints."""

    def __init__(self, config: CandidateDiscoveryConfig = DEFAULT_CANDIDATE_CONFIG) -> None:
        self.config = config

    def extract_parcels(
        self,
        feasible_cells: list[FeasibleCell],
        grid_rows: int,
        grid_cols: int,
        res_deg_x: float,
        res_deg_y: float,
        origin_lat: float,
        origin_lng: float,
        segmented_regions: list[list[FeasibleCell]] | None = None,
        apply_segmentation: bool = False,
    ) -> tuple[list[ExtractedParcel], list[ExtractedParcel]]:
        """Extracts contiguous parcels from feasible cells using edge connectivity and geometric screening.

        Returns:
            (valid_parcels, rejected_parcels)
        """
        if not feasible_cells:
            return [], []

        # 1. Build binary grid matrix of feasible cells
        grid = np.zeros((grid_rows, grid_cols), dtype=np.int32)
        cell_map: dict[tuple[int, int], FeasibleCell] = {}
        for c in feasible_cells:
            grid[c.row, c.col] = 1
            cell_map[(c.row, c.col)] = c

        # Compute metric cell dimensions at origin latitude
        dx_m, dy_m = degree_cell_size_to_meters(origin_lat, res_deg_x, res_deg_y)
        cell_area_sq_m = dx_m * dy_m
        cell_area_ha = cell_area_sq_m / 10000.0

        valid_parcels: list[ExtractedParcel] = []
        rejected_parcels: list[ExtractedParcel] = []

        half_dx = res_deg_x / 2.0
        half_dy = res_deg_y / 2.0

        # 2. Determine region clusters (either segmented regions or 4-connected components)
        if segmented_regions is not None:
            region_list = segmented_regions
        elif apply_segmentation:
            from app.services.candidates.segmentation import SuitabilitySurfaceSegmenter
            segmenter = SuitabilitySurfaceSegmenter(self.config)
            region_list, _, _ = segmenter.segment(
                feasible_cells=feasible_cells,
                grid_rows=grid_rows,
                grid_cols=grid_cols,
                cell_area_ha=cell_area_ha,
            )
        else:
            structure = STRUCTURE_4_CONNECTIVITY if self.config.connectivity == 4 else STRUCTURE_8_CONNECTIVITY
            labeled_grid, num_features = ndimage.label(grid, structure=structure)
            region_list = []
            for region_id in range(1, num_features + 1):
                coords = np.argwhere(labeled_grid == region_id)
                if len(coords) == 0:
                    continue
                r_cells = [cell_map[(int(r), int(c))] for r, c in coords if (int(r), int(c)) in cell_map]
                if r_cells:
                    region_list.append(r_cells)

        for region_cells in region_list:
            if not region_cells:
                continue

            n_cells = len(region_cells)
            total_ha = round(n_cells * cell_area_ha, 2)
            total_sq_km = round(total_ha / 100.0, 4)

            # Build cell bounding boxes and union into contiguous polygon
            cell_boxes = [
                box(c.lng - half_dx, c.lat - half_dy, c.lng + half_dx, c.lat + half_dy)
                for c in region_cells
            ]
            dissolved = unary_union(cell_boxes)
            clean_geom = make_valid(dissolved)

            # Slight topology-preserving simplification to eliminate jagged raster staircase edges
            simplified = clean_geom.simplify(min(res_deg_x, res_deg_y) * 0.25, preserve_topology=True)
            if not simplified.is_valid or simplified.is_empty:
                simplified = clean_geom

            # Ensure MultiPolygon or Polygon representation
            if isinstance(simplified, Polygon):
                canonical_geom = MultiPolygon([simplified])
            elif isinstance(simplified, MultiPolygon):
                canonical_geom = simplified
            else:
                canonical_geom = clean_geom

            # Check polygon topology validity
            is_valid_topology = canonical_geom.is_valid and not canonical_geom.is_empty and canonical_geom.area > 0

            # Calculate centroid
            centroid = canonical_geom.representative_point() if is_valid_topology else Point(origin_lng, origin_lat)

            # Aggregate scores across cells
            mean_suitability = round(float(np.mean([c.suitability_score for c in region_cells])), 1)
            mean_confidence = round(float(np.mean([c.confidence_score for c in region_cells])), 1)
            mean_slope = round(float(np.mean([c.slope_deg for c in region_cells])), 1)

            # Aggregate criteria scores
            all_criteria = set()
            for c in region_cells:
                all_criteria.update(c.criterion_scores.keys())

            agg_criteria: dict[str, float] = {}
            for crit in all_criteria:
                vals = [c.criterion_scores[crit] for c in region_cells if crit in c.criterion_scores]
                if vals:
                    agg_criteria[crit] = round(float(np.mean(vals)), 1)

            # Aggregate exclusion summary (preserve UNKNOWN if any constituent cell is UNKNOWN)
            agg_exclusions: dict[str, str] = {}
            for c in region_cells:
                for k, v in c.exclusion_summary.items():
                    if k not in agg_exclusions or agg_exclusions[k] == "PASS":
                        agg_exclusions[k] = v

            from app.services.spatial.distance import haversine_distance_km
            dist_from_origin = haversine_distance_km(origin_lat, origin_lng, centroid.y, centroid.x)

            # Calculate polygon quality metrics (effective width, aspect ratio, compactness)
            eff_width_m, aspect_ratio, compactness = compute_polygon_quality_metrics(
                canonical_geom, dx_m, dy_m, res_deg_x, res_deg_y
            )

            parcel = ExtractedParcel(
                geom_wkt=canonical_geom.wkt,
                centroid_lat=round(centroid.y, 6),
                centroid_lng=round(centroid.x, 6),
                area_sq_km=total_sq_km,
                area_hectares=total_ha,
                cell_count=n_cells,
                suitability_score=mean_suitability,
                confidence_score=mean_confidence,
                criteria_scores=agg_criteria,
                exclusion_summary=agg_exclusions,
                distance_from_origin_km=dist_from_origin,
                effective_width_m=eff_width_m,
                aspect_ratio=aspect_ratio,
                compactness=compactness,
                mean_slope_degrees=mean_slope,
            )

            # ── GEOMETRIC FEASIBILITY SCREENING ──
            if not is_valid_topology:
                parcel.is_rejected = True
                parcel.rejection_reason = "INVALID_GEOMETRY"
                rejected_parcels.append(parcel)
            elif total_ha < self.config.min_parcel_area_hectares:
                parcel.is_rejected = True
                parcel.rejection_reason = "INSUFFICIENT_CONTIGUOUS_AREA"
                rejected_parcels.append(parcel)
            elif eff_width_m < self.config.min_effective_width_meters:
                parcel.is_rejected = True
                parcel.rejection_reason = "INSUFFICIENT_WIDTH"
                rejected_parcels.append(parcel)
            elif (
                aspect_ratio > self.config.max_aspect_ratio
                or compactness < self.config.min_compactness_ratio
            ):
                parcel.is_rejected = True
                parcel.rejection_reason = "EXTREME_FRAGMENTATION"
                rejected_parcels.append(parcel)
            else:
                valid_parcels.append(parcel)

        return valid_parcels, rejected_parcels
