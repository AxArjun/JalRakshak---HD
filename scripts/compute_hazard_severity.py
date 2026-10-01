"""
JalRakshak-HD: Time-Synchronous Hydraulic Hazard Severity Engine (Milestone M8)
==============================================================================
Evaluates CWC / AIDR Guideline 7-3 / Smith et al. (2014) combined depth-velocity
hazard vulnerability classes (H1–H6) synchronously across all 181 time steps of
the validated M5 D-Flow FM 2D simulation (Bhavanisagar_DamBreak_map.nc).

Critical Standard:
- MUST NOT evaluate hazard using max(D) * max(V) across different time steps.
- Evaluates D(t), V(t), and D(t)*V(t) at each identical timestep t.
- Computes maximum hazard class, arrival times for severity thresholds (wetting, H3, H4, H5, H6),
  and time of peak hazard per computational face.
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

import pyproj
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
import netCDF4 as nc
import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import griddata
from shapely.geometry import Point, Polygon

# Add repo root to path for backend services
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.hazard_classification import (
    classify_hazard_vectorized,
    HazardClass,
    HAZARD_METADATA,
)

OUTPUT_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
HADR_OUT_DIR = ROOT_DIR / "outputs" / "hadr"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
MODEL_DIR = ROOT_DIR / "data" / "dflowfm" / "model"
DOMAIN_PATH = MODEL_DIR / "domain.gpkg"

HADR_OUT_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


def compute_hazard_severity():
    print("=" * 80)
    print(" JALRAKSHAK-HD: TIME-SYNCHRONOUS HAZARD SEVERITY ENGINE (M8)")
    print("=" * 80)

    map_nc_path = OUTPUT_DIR / "Bhavanisagar_DamBreak_map.nc"
    if not map_nc_path.exists():
        raise FileNotFoundError(f"Missing map NetCDF output: {map_nc_path}")

    ds_map = nc.Dataset(map_nc_path, "r")
    time_arr = ds_map.variables["time"][:] # seconds
    num_timesteps = len(time_arr)
    
    face_x = ds_map.variables["mesh2d_face_x"][:]
    face_y = ds_map.variables["mesh2d_face_y"][:]
    face_area = ds_map.variables["mesh2d_flowelem_ba"][:]
    num_faces = len(face_x)

    print(f"Loaded Map NetCDF with {num_faces} faces across {num_timesteps} timesteps ({time_arr[-1]/3600.0:.2f} hr).")

    # Arrays to track temporal evolution across 181 timesteps
    max_hazard_code = np.zeros(num_faces, dtype=np.int32) # 0=DRY, 1..6 = H1..H6
    time_of_max_hazard_s = np.full(num_faces, np.nan, dtype=np.float64)
    depth_at_max_hazard_m = np.zeros(num_faces, dtype=np.float64)
    vel_at_max_hazard_mps = np.zeros(num_faces, dtype=np.float64)
    dv_at_max_hazard = np.zeros(num_faces, dtype=np.float64)

    max_dv_product = np.zeros(num_faces, dtype=np.float64)
    time_of_max_dv_s = np.full(num_faces, np.nan, dtype=np.float64)

    arrival_time_wetting_s = np.full(num_faces, np.nan, dtype=np.float64)
    arrival_time_h3_s = np.full(num_faces, np.nan, dtype=np.float64)
    arrival_time_h4_s = np.full(num_faces, np.nan, dtype=np.float64)
    arrival_time_h5_s = np.full(num_faces, np.nan, dtype=np.float64)
    arrival_time_h6_s = np.full(num_faces, np.nan, dtype=np.float64)

    print("Executing time-synchronous hazard classification loop...")
    for t_idx in range(num_timesteps):
        t_sec = float(time_arr[t_idx])
        d_step = np.maximum(ds_map.variables["mesh2d_waterdepth"][t_idx, :], 0.0)
        v_step = np.maximum(ds_map.variables["mesh2d_ucmag"][t_idx, :], 0.0)
        dv_step = d_step * v_step

        # Vectorized CWC / AIDR Guideline 7-3 classification
        haz_step = classify_hazard_vectorized(d_step, v_step)

        # 1. Arrival Times (first instance where threshold is crossed)
        wet_mask = (d_step >= 0.05) & np.isnan(arrival_time_wetting_s)
        arrival_time_wetting_s[wet_mask] = t_sec

        h3_mask = (haz_step >= 3) & np.isnan(arrival_time_h3_s)
        arrival_time_h3_s[h3_mask] = t_sec

        h4_mask = (haz_step >= 4) & np.isnan(arrival_time_h4_s)
        arrival_time_h4_s[h4_mask] = t_sec

        h5_mask = (haz_step >= 5) & np.isnan(arrival_time_h5_s)
        arrival_time_h5_s[h5_mask] = t_sec

        h6_mask = (haz_step >= 6) & np.isnan(arrival_time_h6_s)
        arrival_time_h6_s[h6_mask] = t_sec

        # 2. Maximum DV product
        dv_higher = dv_step > max_dv_product
        max_dv_product[dv_higher] = dv_step[dv_higher]
        time_of_max_dv_s[dv_higher] = t_sec

        # 3. Maximum Hazard Code (strictly prioritized by severity: H6 > H5 > H4 > H3 > H2 > H1)
        haz_higher = haz_step > max_hazard_code
        max_hazard_code[haz_higher] = haz_step[haz_higher]
        time_of_max_hazard_s[haz_higher] = t_sec
        depth_at_max_hazard_m[haz_higher] = d_step[haz_higher]
        vel_at_max_hazard_mps[haz_higher] = v_step[haz_higher]
        dv_at_max_hazard[haz_higher] = dv_step[haz_higher]

        # For equal hazard code, if DV product is higher, update representative depth and velocity
        haz_equal = (haz_step == max_hazard_code) & (haz_step > 0) & (dv_step > dv_at_max_hazard)
        depth_at_max_hazard_m[haz_equal] = d_step[haz_equal]
        vel_at_max_hazard_mps[haz_equal] = v_step[haz_equal]
        dv_at_max_hazard[haz_equal] = dv_step[haz_equal]
        time_of_max_hazard_s[haz_equal] = t_sec

    ds_map.close()
    print("Time-synchronous loop complete.")

    # Hazard Class Names mapping
    hazard_names = ["DRY", "H1", "H2", "H3", "H4", "H5", "H6"]
    hazard_class_str = [hazard_names[c] for c in max_hazard_code]

    # Calculate inundated area per hazard class
    inundated_mask = max_hazard_code > 0
    num_inundated_faces = int(np.sum(inundated_mask))
    total_inundated_area_km2 = float(np.sum(face_area[inundated_mask]) / 1e6)

    print(f"\nTotal Inundated Faces: {num_inundated_faces} / {num_faces} ({total_inundated_area_km2:.2f} km2)")
    print("-" * 60)
    print(f"{'Hazard Class':<15} {'Face Count':<12} {'Area (km2)':<12} {'% of Inundated':<15}")
    print("-" * 60)
    
    hazard_breakdown = {}
    for c in range(1, 7):
        c_mask = max_hazard_code == c
        c_count = int(np.sum(c_mask))
        c_area = float(np.sum(face_area[c_mask]) / 1e6)
        c_pct = (c_area / total_inundated_area_km2 * 100) if total_inundated_area_km2 > 0 else 0.0
        c_name = hazard_names[c]
        print(f"{c_name:<15} {c_count:<12} {c_area:<12.2f} {c_pct:<15.2f}%")
        hazard_breakdown[c_name] = {
            "hazard_code": c,
            "description": HAZARD_METADATA[HazardClass(c)]["description"],
            "face_count": c_count,
            "area_km2": round(c_area, 3),
            "area_percentage_inundated": round(c_pct, 2)
        }

    # Severe hazard summary (H3–H6)
    h3_plus_mask = max_hazard_code >= 3
    h3_plus_count = int(np.sum(h3_plus_mask))
    h3_plus_area = float(np.sum(face_area[h3_plus_mask]) / 1e6)
    h3_plus_pct = (h3_plus_area / total_inundated_area_km2 * 100) if total_inundated_area_km2 > 0 else 0.0

    h5_h6_mask = max_hazard_code >= 5
    h5_h6_count = int(np.sum(h5_h6_mask))
    h5_h6_area = float(np.sum(face_area[h5_h6_mask]) / 1e6)

    print("-" * 60)
    print(f"Severe Hazard (H3–H6): {h3_plus_count} faces | {h3_plus_area:.2f} km2 ({h3_plus_pct:.1f}%)")
    print(f"Extreme Hazard (H5–H6): {h5_h6_count} faces | {h5_h6_area:.2f} km2 ({(h5_h6_area/total_inundated_area_km2*100):.1f}%)")
    print("-" * 60)

    # 4. Save Vector Products
    print("\nGenerating GeoPackage vector products...")
    # Create GeoDataFrame for wetted faces
    points = [Point(face_x[i], face_y[i]) for i in range(num_faces) if inundated_mask[i]]
    inundated_indices = np.where(inundated_mask)[0]

    gdf_severity = gpd.GeoDataFrame({
        "face_id": inundated_indices,
        "x_utm": face_x[inundated_indices],
        "y_utm": face_y[inundated_indices],
        "face_area_m2": face_area[inundated_indices],
        "hazard_code": max_hazard_code[inundated_indices],
        "hazard_class": [hazard_names[c] for c in max_hazard_code[inundated_indices]],
        "time_of_max_hazard_hr": time_of_max_hazard_s[inundated_indices] / 3600.0,
        "depth_at_max_m": depth_at_max_hazard_m[inundated_indices],
        "vel_at_max_mps": vel_at_max_hazard_mps[inundated_indices],
        "max_dv_product_m2ps": max_dv_product[inundated_indices],
        "arrival_time_wetting_hr": arrival_time_wetting_s[inundated_indices] / 3600.0,
        "arrival_time_h3_hr": arrival_time_h3_s[inundated_indices] / 3600.0,
        "arrival_time_h4_hr": arrival_time_h4_s[inundated_indices] / 3600.0,
        "arrival_time_h5_hr": arrival_time_h5_s[inundated_indices] / 3600.0,
        "arrival_time_h6_hr": arrival_time_h6_s[inundated_indices] / 3600.0,
    }, geometry=points, crs="EPSG:32643")

    severity_gpkg_path = HADR_OUT_DIR / "hazard_severity.gpkg"
    gdf_severity.to_file(severity_gpkg_path, driver="GPKG")
    print(f"[OK] Saved hazard severity vector: {severity_gpkg_path} ({len(gdf_severity)} faces)")

    # Save severity arrival times subset
    severity_arrival_gpkg = HADR_OUT_DIR / "severity_arrival_times.gpkg"
    gdf_severity[gdf_severity["hazard_code"] >= 3].to_file(severity_arrival_gpkg, driver="GPKG")
    print(f"[OK] Saved severity arrival times: {severity_arrival_gpkg}")

    # 5. Rasterization onto 100m Regular Grid for GeoTIFF Products
    print("\nGenerating regular GeoTIFF rasters (EPSG:32643)...")
    domain_gdf = gpd.read_file(DOMAIN_PATH)
    bounds = domain_gdf.total_bounds
    grid_res = 100.0
    grid_x = np.arange(bounds[0], bounds[2] + grid_res, grid_res)
    grid_y = np.arange(bounds[3], bounds[1] - grid_res, -grid_res)
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)

    grid_points = np.column_stack((face_x, face_y))
    
    # Hazard class raster (nearest neighbor interpolation)
    raster_haz = griddata(grid_points, max_hazard_code.astype(float), (grid_xx, grid_yy), method="nearest", fill_value=0.0).astype(np.uint8)
    
    # Max DV product raster (linear interpolation)
    raster_dv = griddata(grid_points, max_dv_product, (grid_xx, grid_yy), method="linear", fill_value=0.0).astype(np.float32)
    raster_dv[raster_haz == 0] = 0.0

    # Arrival time H3 raster
    arr_h3_hr = arrival_time_h3_s / 3600.0
    raster_arr_h3 = griddata(grid_points, arr_h3_hr, (grid_xx, grid_yy), method="nearest", fill_value=np.nan).astype(np.float32)
    raster_arr_h3[raster_haz < 3] = np.nan

    # Arrival time H5 raster
    arr_h5_hr = arrival_time_h5_s / 3600.0
    raster_arr_h5 = griddata(grid_points, arr_h5_hr, (grid_xx, grid_yy), method="nearest", fill_value=np.nan).astype(np.float32)
    raster_arr_h5[raster_haz < 5] = np.nan

    transform = from_origin(bounds[0], bounds[3], grid_res, grid_res)
    profile_base = {
        "driver": "GTiff",
        "height": grid_xx.shape[0],
        "width": grid_xx.shape[1],
        "count": 1,
        "crs": "EPSG:32643",
        "transform": transform,
        "compress": "deflate",
    }

    # Write Hazard Class GeoTIFF
    profile_haz = profile_base.copy()
    profile_haz.update({"dtype": "uint8", "nodata": 0})
    with rasterio.open(HADR_OUT_DIR / "hazard_class.tif", "w", **profile_haz) as dst:
        dst.write(raster_haz, 1)
    print(f"[OK] Saved GeoTIFF: {HADR_OUT_DIR / 'hazard_class.tif'}")

    # Write Max DV GeoTIFF
    profile_dv = profile_base.copy()
    profile_dv.update({"dtype": "float32", "nodata": -9999.0})
    raster_dv_out = raster_dv.copy()
    raster_dv_out[raster_haz == 0] = -9999.0
    with rasterio.open(HADR_OUT_DIR / "max_depth_velocity_product.tif", "w", **profile_dv) as dst:
        dst.write(raster_dv_out, 1)
    print(f"[OK] Saved GeoTIFF: {HADR_OUT_DIR / 'max_depth_velocity_product.tif'}")

    # Write Arrival H3 GeoTIFF
    profile_arr = profile_base.copy()
    profile_arr.update({"dtype": "float32", "nodata": -9999.0})
    raster_arr_h3_out = np.nan_to_num(raster_arr_h3, nan=-9999.0)
    with rasterio.open(HADR_OUT_DIR / "arrival_time_h3.tif", "w", **profile_arr) as dst:
        dst.write(raster_arr_h3_out, 1)
    print(f"[OK] Saved GeoTIFF: {HADR_OUT_DIR / 'arrival_time_h3.tif'}")

    # Write Arrival H5 GeoTIFF
    raster_arr_h5_out = np.nan_to_num(raster_arr_h5, nan=-9999.0)
    with rasterio.open(HADR_OUT_DIR / "arrival_time_h5.tif", "w", **profile_arr) as dst:
        dst.write(raster_arr_h5_out, 1)
    print(f"[OK] Saved GeoTIFF: {HADR_OUT_DIR / 'arrival_time_h5.tif'}")

    # 6. Save JSON Summary
    severity_summary = {
        "milestone": "M8",
        "standard": "CWC_AIDR_GUIDELINE_7_3_SMITH_2014",
        "classification_method": "TIME_SYNCHRONOUS_STEPWISE_EVALUATION",
        "total_domain_faces": num_faces,
        "total_inundated_faces": num_inundated_faces,
        "total_inundated_area_km2": round(total_inundated_area_km2, 3),
        "severe_hazard_h3_h6_area_km2": round(h3_plus_area, 3),
        "severe_hazard_h3_h6_pct": round(h3_plus_pct, 2),
        "extreme_hazard_h5_h6_area_km2": round(h5_h6_area, 3),
        "hazard_breakdown": hazard_breakdown,
        "max_observed_dv_product_m2ps": float(np.max(max_dv_product)),
        "max_observed_depth_m": float(np.max(depth_at_max_hazard_m)),
        "max_observed_velocity_mps": float(np.max(vel_at_max_hazard_mps))
    }

    summary_path = VALIDATION_DIR / "m8_hazard_severity_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(severity_summary, f, indent=2)
    print(f"[OK] Saved hazard severity summary: {summary_path}")

    return severity_summary


if __name__ == "__main__":
    compute_hazard_severity()
