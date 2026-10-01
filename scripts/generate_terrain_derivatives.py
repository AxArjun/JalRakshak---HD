#!/usr/bin/env python3
"""Generate Scientific Terrain Derivatives for JalRakshak-HD.

Computes Slope (degrees) and Hillshade from the real projected DEM
using standard finite-difference terrain morphometry algorithms.
Outputs:
  - data/terrain/slope.tif
  - data/terrain/hillshade.tif
"""


from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import rasterio

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def compute_slope_and_hillshade(
    dem_array: np.ndarray,
    res_x: float,
    res_y: float,
    azimuth_deg: float = 315.0,
    altitude_deg: float = 45.0,
    z_factor: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute slope (degrees) and hillshade (0-255) using 3x3 Horn finite-difference kernel."""
    # Compute gradients (dz/dx and dz/dy) using central difference
    # Horn's 1981 weighting method
    dz_dx = (
        (np.roll(dem_array, -1, axis=1) + 2 * dem_array + np.roll(dem_array, 1, axis=1)) -
        (np.roll(dem_array, -1, axis=1) + 2 * dem_array + np.roll(dem_array, 1, axis=1))
    )  # Initialize shape

    # Interior calculations (avoiding edge wrap)
    padded = np.pad(dem_array, 1, mode="edge")

    # 3x3 neighborhood slices
    z1 = padded[:-2, :-2]
    z2 = padded[:-2, 1:-1]
    z3 = padded[:-2, 2:]
    z4 = padded[1:-1, :-2]
    z6 = padded[1:-1, 2:]
    z7 = padded[2:, :-2]
    z8 = padded[2:, 1:-1]
    z9 = padded[2:, 2:]

    # Rate of change in x (east-west) and y (north-south) direction
    p = ((z3 + 2 * z6 + z9) - (z1 + 2 * z4 + z7)) / (8.0 * res_x) * z_factor
    q = ((z1 + 2 * z2 + z3) - (z7 + 2 * z8 + z9)) / (8.0 * res_y) * z_factor

    # Slope in radians and degrees
    slope_rad = np.arctan(np.sqrt(p**2 + q**2))
    slope_deg = np.degrees(slope_rad).astype(np.float32)

    # Aspect in radians
    aspect_rad = np.arctan2(p, q)
    # Map aspect into 0 to 2*pi range clockwise from North
    aspect_rad = np.where(aspect_rad < 0, 2 * np.pi + aspect_rad, aspect_rad)

    # Hillshade
    zenith_rad = np.radians(90.0 - altitude_deg)
    azimuth_rad = np.radians(360.0 - azimuth_deg + 90.0)

    hillshade = 255.0 * (
        (np.cos(zenith_rad) * np.cos(slope_rad)) +
        (np.sin(zenith_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad))
    )
    hillshade = np.clip(hillshade, 0, 255).astype(np.uint8)

    return slope_deg, hillshade


def generate_derivatives() -> None:
    dem_path = PROJECT_ROOT / "data" / "terrain" / "dem_projected.tif"
    if not dem_path.is_file():
        raise FileNotFoundError(f"Projected DEM not found at {dem_path}. Run acquire_dem.py first.")

    out_slope = PROJECT_ROOT / "data" / "terrain" / "slope.tif"
    out_hillshade = PROJECT_ROOT / "data" / "terrain" / "hillshade.tif"

    print("Reading projected DEM...")
    with rasterio.open(dem_path) as src:
        meta = src.meta.copy()
        res_x = float(src.res[0])
        res_y = float(src.res[1])
        dem = src.read(1)
        nodata = src.nodata

    # Replace nodata for gradient calculation
    valid_mask = (dem != nodata) if nodata is not None else np.ones_like(dem, dtype=bool)
    dem_clean = dem.copy()
    if nodata is not None:
        dem_clean[~valid_mask] = np.nanmean(dem[valid_mask])

    print("Computing terrain slope and hillshade matrices...")
    slope_deg, hillshade = compute_slope_and_hillshade(dem_clean, res_x, res_y)

    # Apply nodata back to slope
    if nodata is not None:
        slope_deg[~valid_mask] = -9999.0

    # Write slope.tif
    slope_meta = meta.copy()
    slope_meta.update(dtype=rasterio.float32, nodata=-9999.0)
    with rasterio.open(out_slope, "w", **slope_meta) as dst:
        dst.write(slope_deg, 1)
    print(f"Saved: {out_slope.relative_to(PROJECT_ROOT)}")

    # Write hillshade.tif
    hillshade_meta = meta.copy()
    hillshade_meta.update(dtype=rasterio.uint8, nodata=0)
    with rasterio.open(out_hillshade, "w", **hillshade_meta) as dst:
        dst.write(hillshade, 1)
    print(f"Saved: {out_hillshade.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    generate_derivatives()
