"""
JalRakshak-HD: D-Flow FM Near-Field Gauge Extraction Engine (Milestone M7)
==========================================================================
Extracts hydrodynamic time series and peak metrics from actual D-Flow FM
NetCDF solver outputs (Bhavanisagar_DamBreak_map.nc) at the exact M6 SPH
common gauge chainages (100 m, 250 m, 500 m, 1000 m, 1500 m).

Produces:
1. outputs/comparison/dflow_nearfield_gauges.csv
2. outputs/validation/m7_dflow_sampling_validation.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd
import netCDF4 as nc
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon

ROOT_DIR = Path(__file__).resolve().parent.parent
MAP_NC_PATH = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE" / "Bhavanisagar_DamBreak_map.nc"
COMMON_GAUGES_PATH = ROOT_DIR / "data" / "comparison" / "common_gauges.gpkg"
OUTPUT_COMPARISON_DIR = ROOT_DIR / "outputs" / "comparison"
OUTPUT_VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"


def extract_dflow_nearfield():
    print("=" * 70)
    print("JalRakshak-HD: Extracting D-Flow FM Near-Field Gauge Metrics (M7)")
    print("=" * 70)

    OUTPUT_COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    if not MAP_NC_PATH.exists():
        raise FileNotFoundError(f"Missing D-Flow map output: {MAP_NC_PATH}")

    if not COMMON_GAUGES_PATH.exists():
        raise FileNotFoundError(f"Missing common gauges GPKG: {COMMON_GAUGES_PATH}")

    gdf_gauges = gpd.read_file(COMMON_GAUGES_PATH)
    print(f"Loaded {len(gdf_gauges)} common gauges from {COMMON_GAUGES_PATH}")

    print(f"Opening D-Flow NetCDF dataset: {MAP_NC_PATH}")
    ds = nc.Dataset(MAP_NC_PATH, "r")

    times = ds.variables["time"][:]  # 181 time steps (0 to 108,000 s)
    face_x = ds.variables["mesh2d_face_x"][:]
    face_y = ds.variables["mesh2d_face_y"][:]
    face_bl = ds.variables["mesh2d_flowelem_bl"][:]
    face_ba = ds.variables["mesh2d_flowelem_ba"][:]
    face_xbnd = ds.variables["mesh2d_face_x_bnd"]
    face_ybnd = ds.variables["mesh2d_face_y_bnd"]

    h_var = ds.variables["mesh2d_waterdepth"]
    u_var = ds.variables["mesh2d_ucmag"]

    mesh_centroids = np.column_stack([face_x, face_y])
    kdtree = cKDTree(mesh_centroids)

    gauge_results = []
    sampling_validation = {
        "dataset": str(MAP_NC_PATH),
        "total_mesh_faces": len(face_x),
        "nominal_resolution_m": 100.0,
        "crs": "EPSG:32643",
        "arrival_wetting_threshold_m": 0.05,
        "stations": {}
    }

    for _, row in gdf_gauges.iterrows():
        st_id = str(row["station_id"])
        ch_m = float(row["chainage_m"])
        gx = float(row["easting"])
        gy = float(row["northing"])
        pt = Point(gx, gy)

        # Nearest face query
        dist, face_idx = kdtree.query([gx, gy])
        face_idx = int(face_idx)
        dist = float(dist)

        # Check point in face polygon
        xb = face_xbnd[face_idx]
        yb = face_ybnd[face_idx]
        poly_coords = list(zip(xb, yb))
        poly = Polygon(poly_coords)
        is_inside = bool(poly.contains(pt))

        # Cell dimensions from bounds
        minx, miny, maxx, maxy = poly.bounds
        cell_dx = round(maxx - minx, 2)
        cell_dy = round(maxy - miny, 2)
        cell_area = float(face_ba[face_idx])
        bed_elev = float(face_bl[face_idx])

        # Extract hydrodynamic time series
        h_series = h_var[:, face_idx]
        u_series = u_var[:, face_idx]

        # First wetting arrival (threshold >= 0.05m)
        wet_indices = np.where(h_series >= 0.05)[0]
        if len(wet_indices) > 0:
            arrival_time_s = float(times[wet_indices[0]])
        else:
            arrival_time_s = float("nan")

        # Peak depth
        peak_d_idx = int(np.argmax(h_series))
        peak_depth_m = float(h_series[peak_d_idx])
        peak_depth_time_s = float(times[peak_d_idx])

        # Peak velocity
        peak_u_idx = int(np.argmax(u_series))
        peak_vel_mps = float(u_series[peak_u_idx])
        peak_vel_time_s = float(times[peak_u_idx])

        # Depth at time of peak velocity
        depth_at_peak_vel_m = float(h_series[peak_u_idx])

        gauge_results.append({
            "station_id": st_id,
            "chainage_m": ch_m,
            "mesh_face_id": face_idx,
            "sampling_distance_m": round(dist, 2),
            "bed_elevation_m": round(bed_elev, 3),
            "arrival_time_s": arrival_time_s,
            "peak_depth_m": round(peak_depth_m, 3),
            "peak_depth_time_s": peak_depth_time_s,
            "peak_velocity_mps": round(peak_vel_mps, 3),
            "peak_velocity_time_s": peak_vel_time_s,
            "depth_at_peak_velocity_m": round(depth_at_peak_vel_m, 3)
        })

        sampling_validation["stations"][st_id] = {
            "chainage_m": ch_m,
            "gauge_easting": gx,
            "gauge_northing": gy,
            "mesh_face_id": face_idx,
            "face_centroid_x": round(float(face_x[face_idx]), 2),
            "face_centroid_y": round(float(face_y[face_idx]), 2),
            "sampling_distance_m": round(dist, 2),
            "cell_dimensions_m": f"{cell_dx} x {cell_dy}",
            "cell_area_m2": round(cell_area, 1),
            "point_inside_face_polygon": is_inside,
            "spatial_precision_limitation": "D-Flow FM operates on a nominal ~100m grid; sub-grid hydraulic features and narrow jet contraction are depth-averaged across the cell."
        }

        print(f"Station {st_id} (ch={ch_m} m): Face {face_idx}, dist={dist:.2f} m, inside={is_inside}, "
              f"bed={bed_elev:.2f} m, arr={arrival_time_s:.0f} s, peak_d={peak_depth_m:.3f} m, peak_u={peak_vel_mps:.3f} m/s")

    ds.close()

    # Save CSV
    df_out = pd.DataFrame(gauge_results)
    out_csv = OUTPUT_COMPARISON_DIR / "dflow_nearfield_gauges.csv"
    # Ensure specified columns are present
    cols = [
        "station_id", "chainage_m", "mesh_face_id", "sampling_distance_m",
        "bed_elevation_m", "arrival_time_s", "peak_depth_m", "peak_depth_time_s",
        "peak_velocity_mps", "peak_velocity_time_s", "depth_at_peak_velocity_m"
    ]
    df_out[cols].to_csv(out_csv, index=False)
    print(f"[OK] Saved D-Flow nearfield gauges to {out_csv}")

    # Save validation JSON
    out_json = OUTPUT_VALIDATION_DIR / "m7_dflow_sampling_validation.json"
    with open(out_json, "w") as f:
        json.dump(sampling_validation, f, indent=2)
    print(f"[OK] Saved sampling validation to {out_json}")


if __name__ == "__main__":
    extract_dflow_nearfield()
