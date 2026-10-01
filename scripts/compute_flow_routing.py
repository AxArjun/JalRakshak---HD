"""
Compute D8 Flow Direction and Flow Accumulation for JalRakshak-HD.
SIH PS 26161 - JalRakshak-HD Milestone M2 Repair.

Calculates deterministic 8-direction (D8) gradient-enforced Priority-Flood DAG routing
and exact upstream contributing area (cell count & km2) from the DEM.
Saves:
  - data/hydrology/dem_hydroconditioned.tif
  - data/hydrology/flow_direction.tif
  - data/hydrology/flow_accumulation.tif
"""
from __future__ import annotations

from collections import deque
import heapq
import os
import sys
from pathlib import Path

import numpy as np
import pyproj
import rasterio

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# D8 Direction encoding (ESRI Standard):
# 32  64  128
# 16   0    1
#  8   4    2
NEIGHBORS = [
    (0, 1, 1),        # East
    (1, 1, 2),        # SE
    (1, 0, 4),        # South
    (1, -1, 8),       # SW
    (0, -1, 16),      # West
    (-1, -1, 32),     # NW
    (-1, 0, 64),      # North
    (-1, 1, 128)      # NE
]
REV_CODES = {1: 16, 2: 32, 4: 64, 8: 128, 16: 1, 32: 2, 64: 4, 128: 8}
D8_OFFSETS = {
    1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
    16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
}


def compute_priority_flood_routing():
    raw_dem_path = PROJECT_ROOT / "data" / "terrain" / "dem_projected.tif"
    if not raw_dem_path.is_file():
        raise FileNotFoundError(f"Projected DEM not found at: {raw_dem_path}")

    out_dir = PROJECT_ROOT / "data" / "hydrology"
    out_dir.mkdir(parents=True, exist_ok=True)

    cond_dem_path = out_dir / "dem_hydroconditioned.tif"
    fdir_path = out_dir / "flow_direction.tif"
    facc_path = out_dir / "flow_accumulation.tif"

    print("Loading projected DEM for hydrologic conditioning and flow routing...")
    with rasterio.open(raw_dem_path) as src:
        meta = src.meta.copy()
        dem = src.read(1).astype(np.float64)
        nodata = src.nodata
        res_x, res_y = src.res[0], src.res[1]

    rows, cols = dem.shape
    valid_mask = (dem != nodata) & (~np.isnan(dem)) & (dem > -500.0)

    print("Executing Priority-Flood depression filling and D8 flow direction assignment...")
    filled = np.copy(dem)
    fdir = np.zeros((rows, cols), dtype=np.uint8)
    visited = np.zeros((rows, cols), dtype=bool)

    heap = []
    for r in range(rows):
        for c in range(cols):
            if not valid_mask[r, c]:
                visited[r, c] = True
                continue
            is_edge = (r == 0 or r == rows - 1 or c == 0 or c == cols - 1)
            if not is_edge:
                for dr, dc, _ in NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < rows and 0 <= nc < cols and valid_mask[nr, nc]):
                        is_edge = True
                        break
            if is_edge:
                visited[r, c] = True
                heapq.heappush(heap, (dem[r, c], r, c))

    while heap:
        elev, r, c = heapq.heappop(heap)
        for dr, dc, code in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and valid_mask[nr, nc] and not visited[nr, nc]:
                visited[nr, nc] = True
                fdir[nr, nc] = REV_CODES[code]
                if dem[nr, nc] < elev:
                    filled[nr, nc] = elev
                heapq.heappush(heap, (filled[nr, nc], nr, nc))

    # Save hydrologically conditioned DEM
    meta_dem = meta.copy()
    meta_dem.update(dtype=rasterio.float32, nodata=nodata)
    filled_out = filled.astype(np.float32)
    filled_out[~valid_mask] = nodata
    with rasterio.open(cond_dem_path, "w", **meta_dem) as dst:
        dst.write(filled_out, 1)
    print(f"Saved conditioned DEM: {cond_dem_path.relative_to(PROJECT_ROOT)}")

    # Compute exact topological upstream accumulation
    print("Computing topological flow accumulation (cell counts)...")
    in_deg = np.zeros((rows, cols), dtype=np.int32)
    for r in range(rows):
        for c in range(cols):
            if valid_mask[r, c] and fdir[r, c] in D8_OFFSETS:
                dr, dc = D8_OFFSETS[fdir[r, c]]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and valid_mask[nr, nc]:
                    in_deg[nr, nc] += 1

    acc = np.ones((rows, cols), dtype=np.int32)
    q = deque([(r, c) for r in range(rows) for c in range(cols) if valid_mask[r, c] and in_deg[r, c] == 0])

    while q:
        r, c = q.popleft()
        if fdir[r, c] in D8_OFFSETS:
            dr, dc = D8_OFFSETS[fdir[r, c]]
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and valid_mask[nr, nc]:
                acc[nr, nc] += acc[r, c]
                in_deg[nr, nc] -= 1
                if in_deg[nr, nc] == 0:
                    q.append((nr, nc))

    acc[~valid_mask] = 0

    # Save flow direction
    meta_fdir = meta.copy()
    meta_fdir.update(dtype=rasterio.uint8, nodata=0)
    with rasterio.open(fdir_path, "w", **meta_fdir) as dst:
        dst.write(fdir, 1)
    print(f"Saved flow direction: {fdir_path.relative_to(PROJECT_ROOT)}")

    # Save flow accumulation
    meta_facc = meta.copy()
    meta_facc.update(dtype=rasterio.int32, nodata=-1)
    with rasterio.open(facc_path, "w", **meta_facc) as dst:
        dst.write(acc, 1)
    print(f"Saved flow accumulation: {facc_path.relative_to(PROJECT_ROOT)}")

    max_acc = int(acc.max())
    max_acc_km2 = (max_acc * res_x * res_y) / 1e6
    print("=" * 80)
    print(f"Flow routing completed: Max Accumulation = {max_acc:,} cells ({max_acc_km2:.2f} km2)")
    print("=" * 80)

    return cond_dem_path, fdir_path, facc_path

if __name__ == "__main__":
    compute_priority_flood_routing()
