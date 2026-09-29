"""Suitability-Surface Segmentation Engine for Relocation Candidate Discovery.

Implements deterministic local-maxima seeded region growing and analytical
watershed/basin subdivision over the MCDA suitability surface.
Prevents entire landscapes hundreds of square kilometres in size from collapsing into a single
candidate parcel, while strictly separating the continuous Feasible Land Mask from discrete,
viable, planning-scale relocation candidate polygons.
"""

from __future__ import annotations

import heapq
import math
from typing import Any
import numpy as np
from scipy import ndimage
from scipy.ndimage import maximum_filter

from app.services.candidates.config import CandidateDiscoveryConfig, DEFAULT_CANDIDATE_CONFIG
from app.services.candidates.polygons import FeasibleCell, STRUCTURE_4_CONNECTIVITY


class SuitabilitySurfaceSegmenter:
    """Segments feasible land into distinct planning-scale candidate regions using
    deterministic suitability topology, natural local-maxima seeded region growing,
    and topology-driven subdivision of oversized regions.
    """

    def __init__(self, config: CandidateDiscoveryConfig = DEFAULT_CANDIDATE_CONFIG) -> None:
        self.config = config

    def segment(
        self,
        feasible_cells: list[FeasibleCell],
        grid_rows: int,
        grid_cols: int,
        cell_area_ha: float,
    ) -> tuple[list[list[FeasibleCell]], list[FeasibleCell], dict[str, Any]]:
        """Segments feasible cells into candidate parcel clusters.

        Returns:
            (candidate_regions, candidate_eligible_cells, metadata)
        """
        if not feasible_cells:
            return [], [], {
                "candidate_cores_found": 0,
                "pre_filter_candidate_regions": 0,
                "candidate_eligible_cells": 0,
            }

        # 1. Build lookup and 2D suitability surface (hard exclusions remain 0.0)
        cell_map: dict[tuple[int, int], FeasibleCell] = {}
        suit_grid = np.zeros((grid_rows, grid_cols), dtype=np.float64)

        for c in feasible_cells:
            cell_map[(c.row, c.col)] = c
            suit_grid[c.row, c.col] = c.suitability_score

        # 2. Filter Candidate-Eligible Cells (cells below threshold remain FEASIBLE, not candidates)
        candidate_eligible_cells = [
            c for c in feasible_cells
            if c.suitability_score >= self.config.minimum_candidate_suitability
        ]

        if not candidate_eligible_cells:
            return [], [], {
                "candidate_cores_found": 0,
                "pre_filter_candidate_regions": 0,
                "candidate_eligible_cells": 0,
            }

        # 3. Identify Candidate Seed Cores (Suitability Peaks)
        # Find local peaks of suitability above candidate_core_threshold
        max_filtered = maximum_filter(suit_grid, size=5, mode="constant", cval=0.0)
        core_mask = (suit_grid == max_filtered) & (suit_grid >= self.config.candidate_core_threshold)

        # Fallback 1: if no local peak at candidate_core_threshold, check local peaks above minimum_candidate_suitability
        if np.count_nonzero(core_mask) == 0:
            core_mask = (suit_grid == max_filtered) & (suit_grid >= self.config.minimum_candidate_suitability)

        # Fallback 2: if no peak detected by 5x5 window (e.g. very small or 1D array), try 3x3 window
        if np.count_nonzero(core_mask) == 0:
            max_filtered_3 = maximum_filter(suit_grid, size=3, mode="constant", cval=0.0)
            core_mask = (suit_grid == max_filtered_3) & (suit_grid >= self.config.minimum_candidate_suitability)

        # Fallback 3: any candidate-eligible cells
        if np.count_nonzero(core_mask) == 0:
            core_mask = (suit_grid >= self.config.minimum_candidate_suitability)

        if np.count_nonzero(core_mask) == 0:
            return [], candidate_eligible_cells, {
                "candidate_cores_found": 0,
                "pre_filter_candidate_regions": 0,
                "candidate_eligible_cells": len(candidate_eligible_cells),
            }

        # Label connected seed core components with orthogonal 4-connectivity
        labeled_cores, num_initial_cores = ndimage.label(core_mask, structure=STRUCTURE_4_CONNECTIVITY)

        seed_coords_map: dict[int, list[tuple[int, int]]] = {}
        for init_id in range(1, num_initial_cores + 1):
            coords = [tuple(x) for x in np.argwhere(labeled_cores == init_id)]
            if coords:
                seed_coords_map[init_id] = coords

        total_cores = len(seed_coords_map)
        if total_cores == 0:
            return [], candidate_eligible_cells, {
                "candidate_cores_found": 0,
                "pre_filter_candidate_regions": 0,
                "candidate_eligible_cells": len(candidate_eligible_cells),
            }

        # 4. Natural Region Growing via Priority Queue (WITHOUT area truncation)
        # Seeds expand naturally according to suitability topology.
        # Fronts compete and meet at suitability valleys / saddles.
        # Expansion stops when score < candidate_growth_threshold or hits hard exclusions.
        segmented_grid = np.zeros((grid_rows, grid_cols), dtype=np.int32)
        pq: list[tuple[float, int, int, int]] = []  # (-score, r, c, seed_id)

        for sid, coords in seed_coords_map.items():
            for r, c in coords:
                if segmented_grid[r, c] == 0:
                    segmented_grid[r, c] = sid
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < grid_rows and 0 <= nc < grid_cols:
                            if (nr, nc) in cell_map and segmented_grid[nr, nc] == 0:
                                n_score = suit_grid[nr, nc]
                                if n_score >= self.config.candidate_growth_threshold:
                                    heapq.heappush(pq, (-n_score, nr, nc, sid))

        while pq:
            neg_score, r, c, sid = heapq.heappop(pq)
            score = -neg_score

            if segmented_grid[r, c] != 0:
                continue  # Already assigned to a competing candidate core
            if score < self.config.candidate_growth_threshold:
                continue  # Stopped at suitability valley

            segmented_grid[r, c] = sid

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid_rows and 0 <= nc < grid_cols:
                    if (nr, nc) in cell_map and segmented_grid[nr, nc] == 0:
                        n_score = suit_grid[nr, nc]
                        if n_score >= self.config.candidate_growth_threshold:
                            heapq.heappush(pq, (-n_score, nr, nc, sid))

        # 5. Extract Natural Candidate Regions
        natural_regions: list[list[FeasibleCell]] = []
        for sid in range(1, total_cores + 1):
            coords = np.argwhere(segmented_grid == sid)
            if len(coords) == 0:
                continue
            region_cells = [cell_map[(int(r), int(c))] for r, c in coords if (int(r), int(c)) in cell_map]
            if region_cells:
                natural_regions.append(region_cells)

        # 6. Planning-Scale Guard: Analytically Subdivide Oversized Regions
        # max_planning_scale_parcel_ha is a subdivision trigger, NOT a cookie-cutter limit.
        # Natural regions <= max_planning_scale_parcel_ha are kept 100% intact.
        # Oversized regions are subdivided using internal suitability peaks and watershed partitioning.
        max_cells = max(1, int(self.config.max_planning_scale_parcel_ha / max(0.01, cell_area_ha)))
        final_candidate_regions: list[list[FeasibleCell]] = []

        for region_cells in natural_regions:
            if len(region_cells) <= max_cells:
                final_candidate_regions.append(region_cells)
            else:
                subdivided = self._subdivide_oversized_region(
                    region_cells=region_cells,
                    suit_grid=suit_grid,
                    cell_area_ha=cell_area_ha,
                    max_cells=max_cells,
                )
                final_candidate_regions.extend(subdivided)

        metadata = {
            "candidate_cores_found": total_cores,
            "pre_filter_candidate_regions": len(final_candidate_regions),
            "candidate_eligible_cells": len(candidate_eligible_cells),
        }

        return final_candidate_regions, candidate_eligible_cells, metadata

    def _subdivide_oversized_region(
        self,
        region_cells: list[FeasibleCell],
        suit_grid: np.ndarray,
        cell_area_ha: float,
        max_cells: int,
        depth: int = 0,
    ) -> list[list[FeasibleCell]]:
        """Subdivides an oversized natural region using suitability topology and watershed partitioning."""
        if len(region_cells) <= max_cells or depth >= 6:
            return [region_cells]

        # 1. Determine target number of sub-parcels K
        K = max(2, int(math.ceil(len(region_cells) / max_cells)))

        # 2. Select K seeds distributed across suitability peaks via suitability-weighted Farthest Point Sampling
        sorted_cells = sorted(
            region_cells,
            key=lambda c: (c.suitability_score, c.row, c.col),
            reverse=True,
        )
        seeds: list[FeasibleCell] = [sorted_cells[0]]

        for _ in range(1, K):
            def score_cand(c: FeasibleCell) -> tuple[float, float]:
                min_d = min(math.hypot(c.row - s.row, c.col - s.col) for s in seeds)
                return (min_d * (c.suitability_score / 100.0), c.suitability_score)

            next_seed = max(region_cells, key=score_cand)
            if any((next_seed.row, next_seed.col) == (s.row, s.col) for s in seeds):
                break
            seeds.append(next_seed)

        actual_k = len(seeds)
        if actual_k < 2:
            return [region_cells]

        # 3. Simultaneous watershed / basin partitioning among all K seeds
        # Cost step: 1.0 + max(0.0, (100.0 - s) / 50.0)
        # Boundaries naturally form along suitability saddles/valleys between seeds
        cell_lookup = {(c.row, c.col): c for c in region_cells}
        assigned: dict[tuple[int, int], int] = {}
        pq: list[tuple[float, int, int, int]] = []

        for sid, s in enumerate(seeds, 1):
            assigned[(s.row, s.col)] = sid
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = s.row + dr, s.col + dc
                if (nr, nc) in cell_lookup and (nr, nc) not in assigned:
                    sc = suit_grid[nr, nc]
                    step_cost = 1.0 + max(0.0, (100.0 - sc) / 50.0)
                    heapq.heappush(pq, (step_cost, nr, nc, sid))

        while pq:
            cost, r, c, sid = heapq.heappop(pq)
            if (r, c) in assigned:
                continue
            assigned[(r, c)] = sid

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in cell_lookup and (nr, nc) not in assigned:
                    sc = suit_grid[nr, nc]
                    step_cost = 1.0 + max(0.0, (100.0 - sc) / 50.0)
                    heapq.heappush(pq, (cost + step_cost, nr, nc, sid))

        sub_regions: list[list[FeasibleCell]] = []
        for sid in range(1, actual_k + 1):
            sub = [cell_lookup[(r, c)] for (r, c), s_val in assigned.items() if s_val == sid]
            if sub:
                if len(sub) > max_cells and len(sub) < len(region_cells):
                    sub_regions.extend(self._subdivide_oversized_region(sub, suit_grid, cell_area_ha, max_cells, depth + 1))
                else:
                    sub_regions.append(sub)

        return sub_regions
