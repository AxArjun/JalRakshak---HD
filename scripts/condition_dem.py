#!/usr/bin/env python3
"""DEM Hydrologic Conditioning via Priority-Flood Depression Filling.

Milestone: M2 — Real Hydrology, River Network, Catchment and Reservoir Geometry
Implements Barnes et al. (2014) Priority-Flood algorithm to remove spurious digital
pits and depressions while strictly preserving natural valley relief and drainage paths.
Saves: data/hydrology/dem_hydroconditioned.tif
"""

from __future__ import annotations

import heapq
import os
import sys
from pathlib import Path

import pyproj
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

import numpy as np
import rasterio

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def priority_flood_fill(dem: np.ndarray, nodata_val: float) -> tuple[np.ndarray, dict]:
    """Execute Barnes et al. (2014) Priority-Flood depression filling on 2D elevation grid."""
    rows, cols = dem.shape
    filled = np.copy(dem)
    closed = np.zeros((rows, cols), dtype=bool)

    valid_mask = (dem != nodata_val) & (~np.isnan(dem)) & (dem > -500.0)

    # Priority queue storing (elevation, row, col)
    pq: list[tuple[float, int, int]] = []

    # 1. Initialize queue with outer raster boundaries and valid edges
    for r in range(rows):
        for c in [0, cols - 1]:
            closed[r, c] = True
            if valid_mask[r, c]:
                heapq.heappush(pq, (float(dem[r, c]), r, c))

    for c in range(cols):
        for r in [0, rows - 1]:
            if not closed[r, c]:
                closed[r, c] = True
                if valid_mask[r, c]:
                    heapq.heappush(pq, (float(dem[r, c]), r, c))

    # Also push any valid cells adjacent to nodata interior cells
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if not valid_mask[r, c] and not closed[r, c]:
                closed[r, c] = True
                # Check 8 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and valid_mask[nr, nc] and not closed[nr, nc]:
                            closed[nr, nc] = True
                            heapq.heappush(pq, (float(dem[nr, nc]), nr, nc))

    # 2. Priority-Flood traversal
    neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    while pq:
        elev, r, c = heapq.heappop(pq)

        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not closed[nr, nc]:
                closed[nr, nc] = True
                if valid_mask[nr, nc]:
                    if dem[nr, nc] <= elev:
                        # Depression detected: fill to spill elevation + small gradient epsilon
                        filled[nr, nc] = elev + 1e-4
                        heapq.heappush(pq, (filled[nr, nc], nr, nc))
                    else:
                        heapq.heappush(pq, (float(dem[nr, nc]), nr, nc))

    # Calculate conditioning diagnostics on valid cells
    diff = filled[valid_mask] - dem[valid_mask]
    changed_cells = np.count_nonzero(diff > 1e-4)
    total_valid = np.count_nonzero(valid_mask)
    pct_changed = (changed_cells / total_valid) * 100.0 if total_valid > 0 else 0.0

    stats = {
        "algorithm": "Priority-Flood Depression Filling (Barnes et al. 2014)",
        "total_valid_cells": int(total_valid),
        "cells_modified": int(changed_cells),
        "percentage_modified": round(float(pct_changed), 3),
        "max_elevation_adjustment_m": round(float(np.max(diff)), 3) if changed_cells > 0 else 0.0,
        "mean_elevation_adjustment_m": round(float(np.mean(diff[diff > 1e-4])), 3) if changed_cells > 0 else 0.0,
    }

    return filled, stats


def condition_dem() -> tuple[Path, dict]:
    dem_path = PROJECT_ROOT / "data" / "terrain" / "dem_projected.tif"
    if not dem_path.is_file():
        raise FileNotFoundError(f"Projected DEM not found at: {dem_path}")

    out_dir = PROJECT_ROOT / "data" / "hydrology"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dem_hydroconditioned.tif"

    print(f"Loading DEM for hydrologic conditioning from {dem_path.relative_to(PROJECT_ROOT)}...")
    with rasterio.open(dem_path) as src:
        meta = src.meta.copy()
        dem = src.read(1)
        nodata = src.nodata if src.nodata is not None else -9999.0

    print("Running Priority-Flood algorithm...")
    filled_dem, stats = priority_flood_fill(dem, nodata)

    meta.update(dtype=rasterio.float32, nodata=nodata)
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(filled_dem.astype(np.float32), 1)

    print("=" * 80)
    print(" DEM HYDROLOGIC CONDITIONING COMPLETED")
    print("=" * 80)
    print(f"Saved:               {out_path.relative_to(PROJECT_ROOT)}")
    print(f"Algorithm:           {stats['algorithm']}")
    print(f"Cells Modified:      {stats['cells_modified']} / {stats['total_valid_cells']} ({stats['percentage_modified']} %)")
    print(f"Max Adjustment:      {stats['max_elevation_adjustment_m']} m")
    print(f"Mean Adjustment:     {stats['mean_elevation_adjustment_m']} m")
    print("=" * 80)

    return out_path, stats


def main() -> int:
    try:
        condition_dem()
        return 0
    except Exception as e:
        print(f"Error conditioning DEM: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
