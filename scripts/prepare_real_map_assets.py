"""Prepare and synchronize GIS rasters and GeoJSON vectors for both Bhavanisagar and Hirakud sites."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from PIL import Image
import numpy as np
import rasterio

project_root = Path(__file__).resolve().parent.parent

def prepare_assets():
    hirakud_data = project_root / "data" / "hirakud"
    geojson_dir = project_root / "outputs" / "dashboard" / "geojson"
    overlays_dir = project_root / "outputs" / "dashboard" / "overlays"

    geojson_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy Hirakud GeoJSON layers to dashboard/geojson/
    files_to_copy = [
        (hirakud_data / "dam_point.geojson", geojson_dir / "hirakud_dam_point.geojson"),
        (hirakud_data / "study_area.geojson", geojson_dir / "hirakud_study_area.geojson"),
        (hirakud_data / "hydrology" / "mahanadi_river.geojson", geojson_dir / "hirakud_mahanadi_river.geojson"),
        (hirakud_data / "hydrology" / "hirakud_reservoir.geojson", geojson_dir / "hirakud_reservoir.geojson"),
    ]
    for src, dst in files_to_copy:
        if src.is_file():
            shutil.copy2(src, dst)
            print(f"Copied {src.name} -> {dst.name}")

    # 2. Render Hirakud Hillshade to PNG
    hs_tif = hirakud_data / "terrain" / "hillshade.tif"
    if hs_tif.is_file():
        with rasterio.open(hs_tif) as src:
            arr = src.read(1)
            # Create RGBA
            rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
            rgba[:, :, 0] = arr
            rgba[:, :, 1] = arr
            rgba[:, :, 2] = arr
            rgba[:, :, 3] = np.where(arr > 0, 210, 0).astype(np.uint8)

            img = Image.fromarray(rgba, mode="RGBA")
            img_out = overlays_dir / "hirakud_hillshade.png"
            img.save(img_out, format="PNG")
            print(f"Generated {img_out} ({img.size})")

    # 3. Update overlay manifest
    manifest_file = overlays_dir / "manifest.json"
    if manifest_file.is_file():
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["layers"]["hirakud_hillshade"] = {
            "file": "hirakud_hillshade.png",
            "url": "/api/tiles/overlays/hirakud_hillshade.png",
            "label": "NASA SRTM 30m Topographic Hillshade (Hirakud)",
            "unit": "grayscale",
            "bounds_wgs84": [
                [21.4000, 83.7000],
                [21.7000, 84.1500]
            ]
        }
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Updated manifest.json with Hirakud hillshade overlay.")

if __name__ == "__main__":
    prepare_assets()
