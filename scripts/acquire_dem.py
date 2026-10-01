#!/usr/bin/env python3
"""Acquire and Reproject Real SRTM Elevation Data from Google Earth Engine.

Milestone: M1 — Real Study Area, AOI and Terrain Acquisition
Pulls authentic USGS/SRTMGL1_003 30m DEM for the Bhavanisagar study area AOI,
saves original WGS84 GeoTIFF, and reprojects to UTM Zone 43N (EPSG:32643).
"""

from __future__ import annotations

import io
import os
import sys
import zipfile
from pathlib import Path

# Safe PROJ directory configuration for Windows
import pyproj
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

import ee
import httpx
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def acquire_srtm_dem() -> Path:
    """Download authentic USGS/SRTMGL1_003 DEM via Google Earth Engine."""
    config = load_config()
    bbox = config["aoi"]["bbox_wgs84"]
    project_id = "jalrakshak-hd"

    raw_terrain_dir = PROJECT_ROOT / "data" / "raw" / "terrain"
    raw_terrain_dir.mkdir(parents=True, exist_ok=True)
    raw_dem_path = raw_terrain_dir / "srtm_dem_wgs84.tif"

    # If already downloaded and valid, reuse
    if raw_dem_path.is_file() and raw_dem_path.stat().st_size > 10000:
        print(f"Using already downloaded raw DEM: {raw_dem_path} ({raw_dem_path.stat().st_size / (1024*1024):.2f} MB)")
        return raw_dem_path

    print(f"Initializing Google Earth Engine with project: '{project_id}'...")
    ee.Initialize(project=project_id)

    region = ee.Geometry.Rectangle(
        [bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"]],
        proj="EPSG:4326",
        geodesic=False,
    )

    dataset_id = config["terrain"]["dataset_id"]
    print(f"Querying Earth Engine asset: {dataset_id}...")
    srtm_img = ee.Image(dataset_id).select("elevation")

    # Clip to bounding geometry
    clipped_dem = srtm_img.clip(region)

    print("Generating secure download URL from Earth Engine API...")
    url = clipped_dem.getDownloadURL(
        {
            "name": "srtm_dem_wgs84",
            "scale": 30,
            "crs": "EPSG:4326",
            "region": region,
            "format": "GEO_TIFF",
        }
    )

    print(f"Downloading authentic SRTM GeoTIFF from Earth Engine...")
    response = httpx.get(url, timeout=120.0, follow_redirects=True)
    response.raise_for_status()

    # If Earth Engine returns a ZIP archive containing the GeoTIFF
    content = response.content
    if content[:2] == b"PK":  # Zip file magic bytes
        print("Unpacking GeoTIFF from Earth Engine ZIP container...")
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            tif_names = [n for n in z.namelist() if n.endswith(".tif")]
            if not tif_names:
                raise RuntimeError("No GeoTIFF found inside downloaded ZIP archive.")
            with open(raw_dem_path, "wb") as f_out:
                f_out.write(z.read(tif_names[0]))
    else:
        with open(raw_dem_path, "wb") as f_out:
            f_out.write(content)

    file_size_mb = raw_dem_path.stat().st_size / (1024 * 1024)
    print(f"Successfully saved authentic raw DEM: {raw_dem_path} ({file_size_mb:.2f} MB)")
    return raw_dem_path


def reproject_dem(input_wgs84_tif: Path) -> Path:
    """Reproject WGS84 DEM to target projected CRS (EPSG:32643) at 30.0m native resolution."""
    config = load_config()
    target_crs = config["aoi"]["projected_crs"]  # e.g., "EPSG:32643"
    target_res = float(config["terrain"]["output_resolution_m"])  # 30.0 m

    out_terrain_dir = PROJECT_ROOT / "data" / "terrain"
    out_terrain_dir.mkdir(parents=True, exist_ok=True)
    out_proj_path = out_terrain_dir / "dem_projected.tif"

    print(f"Reprojecting DEM from EPSG:4326 to {target_crs} with {target_res}m resolution...")

    with rasterio.open(input_wgs84_tif) as src:
        src_crs = src.crs
        transform, width, height = calculate_default_transform(
            src_crs, target_crs, src.width, src.height, *src.bounds, resolution=(target_res, target_res)
        )

        kwargs = src.meta.copy()
        kwargs.update(
            {
                "crs": target_crs,
                "transform": transform,
                "width": width,
                "height": height,
                "nodata": src.nodata if src.nodata is not None else -9999.0,
                "dtype": rasterio.float32,
            }
        )

        with rasterio.open(out_proj_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.bilinear,
                )

    file_size_mb = out_proj_path.stat().st_size / (1024 * 1024)
    print(f"Successfully saved projected DEM: {out_proj_path} ({file_size_mb:.2f} MB)")
    return out_proj_path


def main() -> int:
    try:
        # Step 1: Create AOI vectors first
        from scripts.create_study_area_vectors import create_vectors
        print("Generating study area vector geometries...")
        create_vectors()

        # Step 2: Download DEM from Earth Engine
        raw_tif = acquire_srtm_dem()

        # Step 3: Reproject to UTM Zone 43N
        reproject_dem(raw_tif)
        print("DEM acquisition and reprojection completed successfully.")
        return 0
    except Exception as e:
        print(f"Error acquiring DEM: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
