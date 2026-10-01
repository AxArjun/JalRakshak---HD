"""
JalRakshak-HD: Milestone M10 Task 8 — D-Flow FM Simulation Frame Preprocessing
==============================================================================
Reads the actual 1.15 GB D-Flow map NetCDF (181 frames, 0 to 30 hr at 600s interval),
extracts real solver water depths, builds face polygons from mesh2d_face_x_bnd /
mesh2d_face_y_bnd, rasterizes each timestep into FILLED depth rasters, and generates
georeferenced transparent PNG overlays with solid opaque wet pixels (alpha=255) and
fully transparent dry cells (alpha=0).
Saves frame metadata to outputs/dashboard/simulation_frames/metadata.json.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
import numpy as np
import netCDF4 as nc
import rasterio
from rasterio.features import rasterize
from shapely.geometry import Polygon
from PIL import Image
from pyproj import Transformer

ROOT_DIR = Path(__file__).resolve().parent.parent
MAP_NC_PATH = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE" / "Bhavanisagar_DamBreak_map.nc"
REF_TIF_PATH = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE" / "max_water_depth.tif"
OUTPUT_FRAMES_DIR = ROOT_DIR / "outputs" / "dashboard" / "simulation_frames"
OUTPUT_FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Central Visualization Bins and Colors (Alpha=255 for all wet pixels)
DEPTH_BINS = [
    {"min": 0.05, "max": 0.50, "label": "0.05 – 0.50 m", "color": "#A0E1FF", "rgba": (160, 225, 255, 255)},
    {"min": 0.50, "max": 1.00, "label": "0.50 – 1.00 m", "color": "#46BEFA", "rgba": (70, 190, 250, 255)},
    {"min": 1.00, "max": 2.00, "label": "1.00 – 2.00 m", "color": "#008CEB", "rgba": (0, 140, 235, 255)},
    {"min": 2.00, "max": 5.00, "label": "2.00 – 5.00 m", "color": "#0A50C8", "rgba": (10, 80, 200, 255)},
    {"min": 5.00, "max": 10.0, "label": "5.00 – 10.00 m", "color": "#4B14A0", "rgba": (75, 20, 160, 255)},
    {"min": 10.0, "max": 100.0, "label": "> 10.00 m", "color": "#82006E", "rgba": (130, 0, 110, 255)}
]


def map_depth_to_rgba(depth_array: np.ndarray) -> np.ndarray:
    """
    Map 2D float depth array into (H, W, 4) uint8 RGBA array.
    depth < 0.05m -> alpha = 0
    depth >= 0.05m -> filled color with alpha = 255
    """
    h, w = depth_array.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Apply depth bins
    for b in DEPTH_BINS:
        mask = (depth_array >= b["min"]) & (depth_array < b["max"])
        rgba[mask] = b["rgba"]

    # Special handling for depths >= 10.0m
    max_mask = depth_array >= 10.0
    rgba[max_mask] = (130, 0, 110, 255)

    return rgba


def build_simulation_frames():
    print("=" * 70)
    print(" JALRAKSHAK-HD: D-Flow Simulation Frame Preprocessing (FILLED DEPTH)")
    print("=" * 70)

    if not MAP_NC_PATH.exists():
        raise FileNotFoundError(f"D-Flow map NetCDF missing: {MAP_NC_PATH}")
    if not REF_TIF_PATH.exists():
        raise FileNotFoundError(f"Reference GeoTIFF missing: {REF_TIF_PATH}")

    # 1. Read Reference GeoTIFF geometry
    with rasterio.open(REF_TIF_PATH) as src:
        width = src.width
        height = src.height
        transform = src.transform
        bounds = src.bounds
        crs = src.crs

    # Calculate WGS84 bounding box for Leaflet ImageOverlay
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    min_lon, min_lat = transformer.transform(bounds.left, bounds.bottom)
    max_lon, max_lat = transformer.transform(bounds.right, bounds.top)
    bounds_wgs84 = {
        "south_west": [round(min_lat, 6), round(min_lon, 6)],
        "north_east": [round(max_lat, 6), round(max_lon, 6)],
        "leaflet_bounds": [
            [round(min_lat, 6), round(min_lon, 6)],
            [round(max_lat, 6), round(max_lon, 6)]
        ]
    }

    print(f"Grid dimensions: {width} x {height} | WGS84 bounds: {bounds_wgs84['leaflet_bounds']}")

    # 2. Open NetCDF and build face polygons
    ds = nc.Dataset(str(MAP_NC_PATH))
    face_x_bnd = ds.variables["mesh2d_face_x_bnd"][:]
    face_y_bnd = ds.variables["mesh2d_face_y_bnd"][:]
    face_area = ds.variables["mesh2d_flowelem_ba"][:]
    waterdepth_var = ds.variables["mesh2d_waterdepth"]
    n_frames = waterdepth_var.shape[0]
    n_faces = len(face_x_bnd)

    print(f"Building Shapely polygons for {n_faces:,} mesh faces...")
    t0 = time.time()
    polygons: list[Polygon | None] = []
    for i in range(n_faces):
        xb = face_x_bnd[i]
        yb = face_y_bnd[i]
        valid = ~np.isnan(xb) & ~np.isnan(yb) & (xb > 0)
        if np.sum(valid) >= 3:
            coords = list(zip(xb[valid], yb[valid]))
            coords.append(coords[0])
            polygons.append(Polygon(coords))
        else:
            polygons.append(None)
    print(f"Polygons constructed in {time.time() - t0:.2f}s.")

    frames_metadata = []

    # 3. Process every solver frame
    print(f"Rasterizing {n_frames} timesteps into filled depth PNGs...")
    t_start = time.time()
    for t_idx in range(n_frames):
        solver_time_s = float(t_idx * 600.0)
        solver_time_hr = round(solver_time_s / 3600.0, 2)
        hr_int = int(solver_time_hr)
        min_int = int(round((solver_time_hr - hr_int) * 60))
        label = f"T+{hr_int:02d}h {min_int:02d}m"

        d_raw = waterdepth_var[t_idx, :]
        max_d = float(np.nanmax(d_raw)) if len(d_raw) > 0 else 0.0

        # Calculate exact wet area in km² (threshold >= 0.05m)
        wet_mask = (d_raw >= 0.05) & (d_raw < 100.0)
        wet_face_count = int(np.sum(wet_mask))
        wet_area_m2 = float(np.sum(face_area[wet_mask]))
        wet_area_km2 = round(wet_area_m2 / 1e6, 3)

        if wet_face_count > 0:
            wet_indices = np.where(wet_mask)[0]
            shapes = [(polygons[i], float(d_raw[i])) for i in wet_indices if polygons[i] is not None]
            
            # Rasterize face polygons with actual depth
            grid_depth = rasterize(
                shapes,
                out_shape=(height, width),
                transform=transform,
                fill=0.0,
                dtype=np.float32
            )
        else:
            grid_depth = np.zeros((height, width), dtype=np.float32)

        # Convert to RGBA image with solid wet pixels and transparent dry cells
        rgba = map_depth_to_rgba(grid_depth)
        non_zero_px = int(np.sum(rgba[:, :, 3] > 0))

        img = Image.fromarray(rgba, mode="RGBA")
        frame_filename = f"frame_{t_idx:03d}.png"
        frame_path = OUTPUT_FRAMES_DIR / frame_filename
        img.save(frame_path, format="PNG", optimize=True)

        frames_metadata.append({
            "frame_index": t_idx,
            "solver_time_s": solver_time_s,
            "solver_time_hr": solver_time_hr,
            "timestamp_label": label,
            "max_depth_at_frame": round(max_d, 3),
            "wet_face_count": wet_face_count,
            "wet_area_km2": wet_area_km2,
            "non_transparent_pixels": non_zero_px,
            "image_filename": frame_filename,
            "image_url": f"/api/simulation/frames/{frame_filename}",
            "bounds_wgs84": bounds_wgs84["leaflet_bounds"]
        })

        if t_idx % 30 == 0 or t_idx == n_frames - 1:
            print(f"  Frame {t_idx:03d}/180 ({label}) | Wet faces: {wet_face_count:,} | Pixels: {non_zero_px:,} | Max Depth: {max_d:.2f} m | Wet Area: {wet_area_km2:.2f} km2")

    ds.close()
    print(f"All {n_frames} frames rasterized in {time.time() - t_start:.2f}s.")

    # Save metadata JSON
    meta_json_path = OUTPUT_FRAMES_DIR / "metadata.json"
    full_manifest = {
        "milestone": "M10",
        "scenario_id": "BHV_BASE",
        "total_frames": n_frames,
        "interval_seconds": 600,
        "total_duration_hours": 30.0,
        "grid_shape": [height, width],
        "bounds_wgs84": bounds_wgs84,
        "depth_legend_bins_m": [
            {"min": b["min"], "max": b["max"], "label": b["label"], "color": b["color"], "rgba": list(b["rgba"])}
            for b in DEPTH_BINS
        ],
        "frames": frames_metadata
    }

    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(full_manifest, f, indent=2)

    print(f"\n[OK] Successfully generated {n_frames} filled simulation frame PNGs and metadata in: {OUTPUT_FRAMES_DIR}")
    return full_manifest


if __name__ == "__main__":
    build_simulation_frames()
