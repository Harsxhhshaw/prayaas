"""Terrain geomorphometry analysis and metric DEM derivative pipeline.

Calculates metric slope, aspect, and curvature from elevation grids using
correct latitude-adjusted metric spacing rather than unprojected angular degrees.
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np

from app.models.enums import DataMode, DatasetType, EvidenceType, RepresentationType


def degree_cell_size_to_meters(lat_deg: float, res_deg_x: float, res_deg_y: float) -> tuple[float, float]:
    """Converts angular degree grid spacing to metric meters at a specific latitude.

    At Chamoli (lat ~30.43°N):
        1 deg lat  ≈ 110,850 m
        1 deg lon  ≈ 111,320 * cos(lat) ≈ 96,080 m
    """
    lat_rad = math.radians(lat_deg)
    meters_per_deg_lat = 111132.954 - 559.822 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
    meters_per_deg_lon = (111412.84 * math.cos(lat_rad)) - (93.5 * math.cos(3 * lat_rad))

    dx_m = abs(res_deg_x * meters_per_deg_lon)
    dy_m = abs(res_deg_y * meters_per_deg_lat)
    return max(0.1, dx_m), max(0.1, dy_m)


def compute_metric_slope(
    elevation: np.ndarray,
    dx_m: float,
    dy_m: float,
    nodata: float = -9999.0,
) -> np.ndarray:
    """Computes terrain slope in degrees using Horn's metric finite-difference algorithm.

    Guarantees:
    - Uses metric cell spacing (dx_m, dy_m in meters), NOT degrees.
    - Preserves nodata cells as nodata.
    - Returns slopes bounded in [0.0, 90.0] degrees.
    """
    rows, cols = elevation.shape
    slope = np.full((rows, cols), nodata, dtype=np.float32)

    valid_mask = (elevation != nodata) & ~np.isnan(elevation)

    # 3x3 kernel calculation for interior cells
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            window = elevation[r - 1 : r + 2, c - 1 : c + 2]
            if not np.all(valid_mask[r - 1 : r + 2, c - 1 : c + 2]):
                continue

            # Horn (1981) weighted gradient:
            # dz/dx = ((z_ne + 2*z_e + z_se) - (z_nw + 2*z_w + z_sw)) / (8 * dx)
            # dz/dy = ((z_sw + 2*z_s + z_se) - (z_nw + 2*z_n + z_ne)) / (8 * dy)
            dz_dx = (
                (window[0, 2] + 2 * window[1, 2] + window[2, 2])
                - (window[0, 0] + 2 * window[1, 0] + window[2, 0])
            ) / (8.0 * dx_m)

            dz_dy = (
                (window[2, 0] + 2 * window[2, 1] + window[2, 2])
                - (window[0, 0] + 2 * window[0, 1] + window[0, 2])
            ) / (8.0 * dy_m)

            gradient = math.sqrt(dz_dx**2 + dz_dy**2)
            slope_deg = math.degrees(math.atan(gradient))
            slope[r, c] = max(0.0, min(90.0, slope_deg))

    return slope


def compute_metric_aspect(
    elevation: np.ndarray,
    dx_m: float,
    dy_m: float,
    nodata: float = -9999.0,
) -> np.ndarray:
    """Computes compass aspect in degrees [0, 360) clockwise from North.

    Convention:
    - 0° = North, 90° = East, 180° = South, 270° = West
    - Flat areas (gradient = 0) = -1.0
    - Nodata cells preserved.
    """
    rows, cols = elevation.shape
    aspect = np.full((rows, cols), nodata, dtype=np.float32)

    valid_mask = (elevation != nodata) & ~np.isnan(elevation)

    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            window = elevation[r - 1 : r + 2, c - 1 : c + 2]
            if not np.all(valid_mask[r - 1 : r + 2, c - 1 : c + 2]):
                continue

            dz_dx = (
                (window[0, 2] + 2 * window[1, 2] + window[2, 2])
                - (window[0, 0] + 2 * window[1, 0] + window[2, 0])
            ) / (8.0 * dx_m)

            dz_dy = (
                (window[2, 0] + 2 * window[2, 1] + window[2, 2])
                - (window[0, 0] + 2 * window[0, 1] + window[0, 2])
            ) / (8.0 * dy_m)

            if abs(dz_dx) < 1e-7 and abs(dz_dy) < 1e-7:
                aspect[r, c] = -1.0  # Flat
                continue

            # Standard mathematical atan2 to compass bearing
            deg = math.degrees(math.atan2(dz_dy, -dz_dx))
            compass = 90.0 - deg
            if compass < 0.0:
                compass += 360.0
            aspect[r, c] = compass % 360.0

    return aspect


def compute_curvatures(
    elevation: np.ndarray,
    dx_m: float,
    dy_m: float,
    nodata: float = -9999.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Computes plan and profile curvature using Zevenbergen & Thorne (1987) 3x3 polynomial.

    Note on limitation:
    Curvature derived from satellite DEMs (e.g. 12.5m / 30m) without sub-meter LiDAR
    is sensitive to interpolation noise and represents modeled meso-relief tendency only.
    """
    rows, cols = elevation.shape
    plan_curv = np.full((rows, cols), nodata, dtype=np.float32)
    prof_curv = np.full((rows, cols), nodata, dtype=np.float32)

    valid_mask = (elevation != nodata) & ~np.isnan(elevation)

    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            w = elevation[r - 1 : r + 2, c - 1 : c + 2]
            if not np.all(valid_mask[r - 1 : r + 2, c - 1 : c + 2]):
                continue

            # Zevenbergen & Thorne coefficients:
            # z = D*x^2 + E*y^2 + F*x*y + G*x + H*y + I
            D = ((w[1, 0] + w[1, 2]) / 2.0 - w[1, 1]) / (dx_m**2)
            E = ((w[0, 1] + w[2, 1]) / 2.0 - w[1, 1]) / (dy_m**2)
            F = (w[0, 0] - w[0, 2] - w[2, 0] + w[2, 2]) / (4.0 * dx_m * dy_m)
            G = (w[1, 2] - w[1, 0]) / (2.0 * dx_m)
            H = (w[0, 1] - w[2, 1]) / (2.0 * dy_m)

            p = G**2 + H**2
            if p > 1e-6:
                # Plan curvature (contour curvature)
                plan = -2.0 * (D * (H**2) + E * (G**2) - F * G * H) / (p**1.5)
                # Profile curvature (maximum slope curvature)
                prof = -2.0 * (D * (G**2) + E * (H**2) + F * G * H) / (p * (1.0 + p)**1.5)
                plan_curv[r, c] = float(plan * 100.0)  # Standard m^-1 scaled by 100
                prof_curv[r, c] = float(prof * 100.0)
            else:
                plan_curv[r, c] = 0.0
                prof_curv[r, c] = 0.0

    return plan_curv, prof_curv


def extract_polygon_terrain_stats(
    raster: np.ndarray,
    nodata: float = -9999.0,
) -> dict[str, float]:
    """Computes robust statistical summary for raster cell values."""
    valid = raster[(raster != nodata) & ~np.isnan(raster)]
    if len(valid) == 0:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0, "median": 0.0}

    return {
        "min": round(float(np.min(valid)), 2),
        "max": round(float(np.max(valid)), 2),
        "mean": round(float(np.mean(valid)), 2),
        "std": round(float(np.std(valid)), 2),
        "median": round(float(np.median(valid)), 2),
    }


def calculate_metric_slope(elevation: np.ndarray, cell_size_x: float = 30.0, cell_size_y: float = 30.0, nodata: float = -9999.0) -> np.ndarray:
    return compute_metric_slope(elevation, dx_m=cell_size_x, dy_m=cell_size_y, nodata=nodata)


def calculate_aspect(elevation: np.ndarray, cell_size_x: float = 30.0, cell_size_y: float = 30.0, nodata: float = -9999.0) -> np.ndarray:
    return compute_metric_aspect(elevation, dx_m=cell_size_x, dy_m=cell_size_y, nodata=nodata)


def calculate_curvature(elevation: np.ndarray, cell_size_x: float = 30.0, cell_size_y: float = 30.0, nodata: float = -9999.0) -> tuple[np.ndarray, np.ndarray]:
    return compute_curvatures(elevation, dx_m=cell_size_x, dy_m=cell_size_y, nodata=nodata)
