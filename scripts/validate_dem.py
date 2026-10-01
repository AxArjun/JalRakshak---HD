#!/usr/bin/env python3
"""Validate Real Projected DEM for JalRakshak-HD.

Computes statistical distribution, checks spatial bounds against verified dam location,
computes SHA-256 checksum, verifies projected coordinate reference system, and saves
validation report to outputs/validation/dem_validation.json.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pyproj
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

import numpy as np
import rasterio
from pyproj import Transformer
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def compute_sha256(file_path: Path) -> str:
    """Calculate SHA-256 cryptographic hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_dem() -> Dict[str, Any]:
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    dem_path = PROJECT_ROOT / "data" / "terrain" / "dem_projected.tif"
    if not dem_path.is_file():
        raise FileNotFoundError(f"Projected DEM not found at: {dem_path}")

    file_size_bytes = dem_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    sha256_hash = compute_sha256(dem_path)

    with rasterio.open(dem_path) as src:
        width = src.width
        height = src.height
        crs = src.crs.to_string() if src.crs else "UNKNOWN"
        is_projected = src.crs.is_projected if src.crs else False
        bounds = {
            "left": float(src.bounds.left),
            "bottom": float(src.bounds.bottom),
            "right": float(src.bounds.right),
            "top": float(src.bounds.top),
        }
        res_x = float(src.res[0])
        res_y = float(src.res[1])
        nodata = src.nodata

        # Read elevation data as a numpy array safely
        elevation_data = src.read(1)

        # Mask nodata
        if nodata is not None:
            valid_mask = (elevation_data != nodata) & (~np.isnan(elevation_data)) & (elevation_data > -500.0)
        else:
            valid_mask = (~np.isnan(elevation_data)) & (elevation_data > -500.0)

        total_pixels = int(width * height)
        valid_pixels = int(np.count_nonzero(valid_mask))
        nodata_pixels = total_pixels - valid_pixels
        nodata_percentage = float((nodata_pixels / total_pixels) * 100.0)

        if valid_pixels == 0:
            raise ValueError("DEM contains zero valid pixels (entire raster is NoData).")

        valid_elevations = elevation_data[valid_mask]
        min_elev = float(np.min(valid_elevations))
        max_elev = float(np.max(valid_elevations))
        mean_elev = float(np.mean(valid_elevations))
        median_elev = float(np.median(valid_elevations))
        std_elev = float(np.std(valid_elevations))

        # Check dam point intersection with raster in projected coordinates
        dam_lat = config["dam"]["latitude"]
        dam_lon = config["dam"]["longitude"]

        transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        dam_x, dam_y = transformer.transform(dam_lon, dam_lat)

        dam_inside_raster = (
            bounds["left"] <= dam_x <= bounds["right"] and
            bounds["bottom"] <= dam_y <= bounds["top"]
        )

        # Sample elevation at dam coordinate
        row, col = src.index(dam_x, dam_y)
        dam_pixel_valid = (0 <= row < height) and (0 <= col < width)
        dam_elevation = float(elevation_data[row, col]) if dam_pixel_valid else None

    # Scientific validation checks
    checks = {
        "is_not_empty": total_pixels > 0,
        "is_projected_crs": is_projected,
        "nodata_percentage_acceptable": nodata_percentage < 20.0,
        "has_meaningful_variation": (max_elev - min_elev) > 20.0,
        "dam_inside_bounds": dam_inside_raster,
        "elevation_physically_plausible": (150.0 <= min_elev <= 350.0) and (250.0 <= max_elev <= 2500.0),
    }

    all_passed = all(checks.values())

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all_passed else "FAIL",
        "file_path": str(dem_path.relative_to(PROJECT_ROOT)),
        "file_size_mb": round(file_size_mb, 3),
        "file_size_bytes": file_size_bytes,
        "sha256": sha256_hash,
        "raster_properties": {
            "width": width,
            "height": height,
            "crs": crs,
            "is_projected": is_projected,
            "pixel_size_x_m": round(res_x, 2),
            "pixel_size_y_m": round(res_y, 2),
            "bounds": bounds,
            "nodata_value": nodata,
        },
        "elevation_statistics_metres": {
            "min_elevation": round(min_elev, 2),
            "max_elevation": round(max_elev, 2),
            "mean_elevation": round(mean_elev, 2),
            "median_elevation": round(median_elev, 2),
            "std_deviation": round(std_elev, 2),
            "total_pixels": total_pixels,
            "valid_pixels": valid_pixels,
            "nodata_percentage": round(nodata_percentage, 3),
        },
        "dam_spatial_check": {
            "dam_name": config["dam"]["name"],
            "dam_lat_wgs84": dam_lat,
            "dam_lon_wgs84": dam_lon,
            "dam_x_projected": round(dam_x, 2),
            "dam_y_projected": round(dam_y, 2),
            "dam_inside_raster": dam_inside_raster,
            "dam_pixel_elevation_m": round(dam_elevation, 2) if dam_elevation else None,
        },
        "validation_checks": checks,
    }

    out_dir = PROJECT_ROOT / "outputs" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dem_validation.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if not all_passed:
        failed = [k for k, v in checks.items() if not v]
        raise ValueError(f"DEM validation failed for checks: {failed}")

    return report


def main() -> int:
    try:
        report = validate_dem()
        print("=" * 80)
        print(" REAL DEM VALIDATION REPORT (M1)")
        print("=" * 80)
        print(f"File:            {report['file_path']}")
        print(f"Dimensions:      {report['raster_properties']['width']} x {report['raster_properties']['height']} pixels")
        print(f"Resolution:      {report['raster_properties']['pixel_size_x_m']} m x {report['raster_properties']['pixel_size_y_m']} m")
        print(f"CRS:             {report['raster_properties']['crs']} (Projected: {report['raster_properties']['is_projected']})")
        print(f"Elevation Min:   {report['elevation_statistics_metres']['min_elevation']} m")
        print(f"Elevation Max:   {report['elevation_statistics_metres']['max_elevation']} m")
        print(f"Elevation Mean:  {report['elevation_statistics_metres']['mean_elevation']} m")
        print(f"NoData %:        {report['elevation_statistics_metres']['nodata_percentage']} %")
        print(f"Dam Elevation:   {report['dam_spatial_check']['dam_pixel_elevation_m']} m (inside raster: {report['dam_spatial_check']['dam_inside_raster']})")
        print(f"SHA-256:         {report['sha256']}")
        print(f"Validation:      {report['status']}")
        print("=" * 80)
        print(f"Report saved to: outputs/validation/dem_validation.json")
        return 0
    except Exception as e:
        print(f"Error validating DEM: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
