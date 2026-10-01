"""
JalRakshak-HD: D-Flow FM Results Extraction & Post-Processing Engine (Milestone M5)
===================================================================================
Ingests raw D-Flow FM NetCDF solver outputs (*_map.nc and *_his.nc) and computes:
1. Maximum water depth (GeoTIFF + PNG map)
2. Maximum flow velocity (GeoTIFF + PNG map)
3. Flood wave arrival time (GeoTIFF + PNG map)
4. Inundation extent polygon (GPKG)
5. Diagnostic station hydrographs (CSV + PNG comparison)
6. Comprehensive NetCDF inventory & mass-balance audit (JSON)
"""

from __future__ import annotations

import os
import json
import math
from pathlib import Path

import pyproj
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import griddata
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
MAPS_DIR = ROOT_DIR / "outputs" / "maps"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
MODEL_DIR = ROOT_DIR / "data" / "dflowfm" / "model"
RIVER_PATH = ROOT_DIR / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
BREACH_PATH = ROOT_DIR / "data" / "dflowfm" / "breach_location.gpkg"
OBS_GPKG = MODEL_DIR / "observation_points.gpkg"
DOMAIN_PATH = MODEL_DIR / "domain.gpkg"


def extract_dflow_results() -> dict:
    print("=" * 80)
    print(" JALRAKSHAK-HD: D-FLOW FM RESULTS EXTRACTION & HYDRAULIC AUDIT (M5)")
    print("=" * 80)

    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    map_nc_path = OUTPUT_DIR / "Bhavanisagar_DamBreak_map.nc"
    his_nc_path = OUTPUT_DIR / "Bhavanisagar_DamBreak_his.nc"

    if not map_nc_path.exists():
        raise FileNotFoundError(f"Missing map NetCDF output: {map_nc_path}")

    # 1. NetCDF Inventory (Task 18)
    ds_map = nc.Dataset(map_nc_path, "r")
    map_vars = list(ds_map.variables.keys())
    map_dims = {d: len(ds_map.dimensions[d]) for d in ds_map.dimensions}
    time_arr = ds_map.variables["time"][:]
    num_timesteps = len(time_arr)
    t_end_hr = float(time_arr[-1] / 3600.0)

    print(f"Loaded Map NetCDF: {map_nc_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"Simulated duration: {time_arr[-1]:.1f} s ({t_end_hr:.2f} hr) | Time steps: {num_timesteps}")

    netcdf_inventory = {
        "milestone": "M5",
        "map_netcdf": {
            "file_path": str(map_nc_path),
            "file_size_mb": float(map_nc_path.stat().st_size / (1024 * 1024)),
            "dimensions": map_dims,
            "variables_count": len(map_vars),
            "variables": map_vars,
            "time_steps_count": num_timesteps,
            "simulation_start_s": float(time_arr[0]),
            "simulation_end_s": float(time_arr[-1]),
            "simulation_end_hr": t_end_hr
        }
    }

    if his_nc_path.exists():
        ds_his = nc.Dataset(his_nc_path, "r")
        netcdf_inventory["history_netcdf"] = {
            "file_path": str(his_nc_path),
            "file_size_mb": float(his_nc_path.stat().st_size / (1024 * 1024)),
            "variables_count": len(ds_his.variables.keys()),
            "variables": list(ds_his.variables.keys())
        }
        ds_his.close()

    with open(VALIDATION_DIR / "m5_netcdf_inventory.json", "w", encoding="utf-8") as f:
        json.dump(netcdf_inventory, f, indent=2)
    print(f"[OK] Saved NetCDF inventory: {VALIDATION_DIR / 'm5_netcdf_inventory.json'}")

    # Load spatial coordinates
    face_x = ds_map.variables["mesh2d_face_x"][:]
    face_y = ds_map.variables["mesh2d_face_y"][:]
    face_area = ds_map.variables["mesh2d_flowelem_ba"][:]
    bed_level = ds_map.variables["mesh2d_flowelem_bl"][:]
    num_faces = len(face_x)

    # Water depth and velocity time series arrays: shape (nTimes, nFaces)
    waterdepth_arr = ds_map.variables["mesh2d_waterdepth"][:]
    ucmag_arr = ds_map.variables["mesh2d_ucmag"][:]

    # 2. Maximum Water Depth Calculation (Task 19)
    print("Computing maximum water depth across 2D faces...")
    max_depth_face = np.max(waterdepth_arr, axis=0)
    # Threshold for wetted faces = 0.05 m
    wet_mask = max_depth_face >= 0.05
    num_wetted_faces = np.sum(wet_mask)

    max_depth_val = float(np.max(max_depth_face))
    median_depth_val = float(np.median(max_depth_face[wet_mask])) if num_wetted_faces > 0 else 0.0
    p95_depth_val = float(np.percentile(max_depth_face[wet_mask], 95)) if num_wetted_faces > 0 else 0.0
    wetted_area_km2 = float(np.sum(face_area[wet_mask]) / 1e6)

    print(f"Max Depth: {max_depth_val:.3f} m | Median (Wet): {median_depth_val:.3f} m | P95: {p95_depth_val:.3f} m | Wetted Area: {wetted_area_km2:.2f} km2")

    # 3. Maximum Velocity Calculation (Task 20)
    print("Computing maximum velocity across 2D faces...")
    max_vel_face = np.max(ucmag_arr, axis=0)
    max_vel_val = float(np.max(max_vel_face))
    median_vel_val = float(np.median(max_vel_face[wet_mask])) if num_wetted_faces > 0 else 0.0
    p95_vel_val = float(np.percentile(max_vel_face[wet_mask], 95)) if num_wetted_faces > 0 else 0.0

    print(f"Max Velocity: {max_vel_val:.3f} m/s | Median (Wet): {median_vel_val:.3f} m/s | P95: {p95_vel_val:.3f} m/s")

    # 4. Arrival Time Calculation (Task 21)
    print("Computing flood wave arrival time (first wetting depth >= 0.05 m)...")
    arrival_time_hr_face = np.full(num_faces, np.nan, dtype=np.float64)

    for t_idx, t_sec in enumerate(time_arr):
        d_step = waterdepth_arr[t_idx]
        wet_step = (d_step >= 0.05) & np.isnan(arrival_time_hr_face)
        arrival_time_hr_face[wet_step] = t_sec / 3600.0

    # 5. Rasterization onto 100m Regular Grid for GeoTIFF Products
    print("Generating regular GeoTIFF rasters (EPSG:32643)...")
    domain_gdf = gpd.read_file(DOMAIN_PATH)
    river_gdf = gpd.read_file(RIVER_PATH)
    breach_gdf = gpd.read_file(BREACH_PATH)
    obs_gdf = gpd.read_file(OBS_GPKG)

    bounds = domain_gdf.total_bounds
    grid_res = 100.0
    grid_x = np.arange(bounds[0], bounds[2] + grid_res, grid_res)
    grid_y = np.arange(bounds[3], bounds[1] - grid_res, -grid_res)
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)

    # Interpolate face variables onto grid
    grid_points = np.column_stack((face_x, face_y))
    raster_depth = griddata(grid_points, max_depth_face, (grid_xx, grid_yy), method="linear", fill_value=0.0)
    raster_vel = griddata(grid_points, max_vel_face, (grid_xx, grid_yy), method="linear", fill_value=0.0)
    raster_arrival = griddata(grid_points, arrival_time_hr_face, (grid_xx, grid_yy), method="nearest", fill_value=np.nan)

    # Set non-wetted cells to 0 / nodata
    raster_depth[raster_depth < 0.05] = 0.0
    raster_vel[raster_depth < 0.05] = 0.0
    raster_arrival[raster_depth < 0.05] = np.nan

    transform = from_origin(bounds[0], bounds[3], grid_res, grid_res)

    # Save max_water_depth.tif
    depth_tif_path = OUTPUT_DIR / "max_water_depth.tif"
    with rasterio.open(
        depth_tif_path, "w", driver="GTiff", height=raster_depth.shape[0], width=raster_depth.shape[1],
        count=1, dtype=np.float32, crs="EPSG:32643", transform=transform, nodata=-9999.0
    ) as dst:
        d_out = raster_depth.astype(np.float32)
        d_out[d_out == 0.0] = -9999.0
        dst.write(d_out, 1)
    print(f"[OK] Saved depth GeoTIFF: {depth_tif_path}")

    # Save max_velocity.tif
    vel_tif_path = OUTPUT_DIR / "max_velocity.tif"
    with rasterio.open(
        vel_tif_path, "w", driver="GTiff", height=raster_vel.shape[0], width=raster_vel.shape[1],
        count=1, dtype=np.float32, crs="EPSG:32643", transform=transform, nodata=-9999.0
    ) as dst:
        v_out = raster_vel.astype(np.float32)
        v_out[v_out == 0.0] = -9999.0
        dst.write(v_out, 1)
    print(f"[OK] Saved velocity GeoTIFF: {vel_tif_path}")

    # Save arrival_time.tif
    arrival_tif_path = OUTPUT_DIR / "arrival_time.tif"
    with rasterio.open(
        arrival_tif_path, "w", driver="GTiff", height=raster_arrival.shape[0], width=raster_arrival.shape[1],
        count=1, dtype=np.float32, crs="EPSG:32643", transform=transform, nodata=-9999.0
    ) as dst:
        a_out = np.nan_to_num(raster_arrival, nan=-9999.0).astype(np.float32)
        dst.write(a_out, 1)
    print(f"[OK] Saved arrival time GeoTIFF: {arrival_tif_path}")

    # 6. Inundation Extent Polygon (Task 22)
    print("Generating Inundation Extent GPKG vector...")
    wet_polys = []
    # Build square polygons for wetted faces
    half_dx = 50.0
    for idx in np.where(wet_mask)[0]:
        fx = face_x[idx]
        fy = face_y[idx]
        poly = Polygon([
            (fx - half_dx, fy - half_dx),
            (fx + half_dx, fy - half_dx),
            (fx + half_dx, fy + half_dx),
            (fx - half_dx, fy + half_dx)
        ])
        wet_polys.append(poly)

    if wet_polys:
        inundated_union = unary_union(wet_polys)
        extent_gdf = gpd.GeoDataFrame(
            [{
                "scenario_id": "BHV_BASE",
                "inundated_area_km2": wetted_area_km2,
                "max_depth_m": max_depth_val,
                "median_depth_m": median_depth_val,
                "max_velocity_ms": max_vel_val,
                "classification": "2D_DFLOWFM_SCREENING_INUNDATION_MODEL"
            }],
            geometry=[inundated_union],
            crs="EPSG:32643"
        )
    else:
        extent_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:32643")

    extent_gpkg_path = OUTPUT_DIR / "inundation_extent.gpkg"
    extent_gdf.to_file(extent_gpkg_path, driver="GPKG")
    print(f"[OK] Saved inundation extent GPKG: {extent_gpkg_path}")

    # 7. Extract Observation Hydrographs (Task 23)
    print("Extracting hydrographs at diagnostic observation stations along Bhavani mainstem...")
    obs_records = []
    obs_ts_dict = {}

    for _, row in obs_gdf.iterrows():
        st_id = row["station_id"]
        st_x = row["x_utm"]
        st_y = row["y_utm"]
        chainage_km = row["chainage_km"]

        # Find nearest 2D face
        dists = np.sqrt((face_x - st_x)**2 + (face_y - st_y)**2)
        nearest_face_idx = int(np.argmin(dists))

        st_depth_series = waterdepth_arr[:, nearest_face_idx]
        st_vel_series = ucmag_arr[:, nearest_face_idx]

        st_peak_depth = float(np.max(st_depth_series))
        st_peak_depth_time_hr = float(time_arr[np.argmax(st_depth_series)] / 3600.0)

        st_peak_vel = float(np.max(st_vel_series))
        st_peak_vel_time_hr = float(time_arr[np.argmax(st_vel_series)] / 3600.0)

        # Arrival time (depth >= 0.05m)
        wet_indices = np.where(st_depth_series >= 0.05)[0]
        st_arrival_hr = float(time_arr[wet_indices[0]] / 3600.0) if len(wet_indices) > 0 else np.nan

        obs_records.append({
            "station_id": st_id,
            "chainage_km": chainage_km,
            "x_utm": st_x,
            "y_utm": st_y,
            "arrival_time_hr": st_arrival_hr,
            "peak_depth_m": st_peak_depth,
            "time_of_peak_depth_hr": st_peak_depth_time_hr,
            "peak_velocity_ms": st_peak_vel,
            "time_of_peak_velocity_hr": st_peak_vel_time_hr
        })

        obs_ts_dict[st_id] = {
            "time_hr": (time_arr / 3600.0).tolist(),
            "depth_m": st_depth_series.tolist(),
            "velocity_ms": st_vel_series.tolist()
        }

    df_obs = pd.DataFrame(obs_records)
    obs_csv_path = OUTPUT_DIR / "observation_hydrographs.csv"
    df_obs.to_csv(obs_csv_path, index=False)
    print(f"[OK] Saved observation summary CSV: {obs_csv_path}")

    # 8. Mass-Balance Audit (Task 24)
    print("Performing mass-balance audit from solver outputs...")
    # Calculate stored volume at final timestep: sum(h * Area)
    final_depths = waterdepth_arr[-1]
    final_stored_volume_m3 = float(np.sum(final_depths * face_area))
    final_stored_volume_mcm = final_stored_volume_m3 / 1e6

    target_inflow_volume_m3 = 780500000.0
    target_inflow_volume_mcm = 780.50

    # From his_nc if available
    downstream_outflow_mcm = 0.0
    mass_balance_status = "PASS"
    if his_nc_path.exists():
        try:
            ds_his = nc.Dataset(his_nc_path, "r")
            if "water_balance_boundaries_in" in ds_his.variables:
                bnd_in = float(ds_his.variables["water_balance_boundaries_in"][-1]) / 1e6
                bnd_out = float(ds_his.variables["water_balance_boundaries_out"][-1]) / 1e6
                downstream_outflow_mcm = abs(bnd_out)
            ds_his.close()
        except Exception:
            pass

    # Residual mass in domain vs inflow + outflow
    mass_residual_mcm = abs(target_inflow_volume_mcm - (final_stored_volume_mcm + downstream_outflow_mcm))
    mass_residual_pct = (mass_residual_mcm / target_inflow_volume_mcm) * 100.0

    mass_balance_manifest = {
        "milestone": "M5",
        "scenario_id": "BHV_BASE",
        "target_breach_volume_mcm": target_inflow_volume_mcm,
        "final_stored_volume_mcm": final_stored_volume_mcm,
        "downstream_outflow_volume_mcm": downstream_outflow_mcm,
        "mass_residual_mcm": mass_residual_mcm,
        "mass_residual_percent": mass_residual_pct,
        "volume_conservation_status": "CONSERVED" if mass_residual_pct < 10.0 else "REVIEW_REQUIRED",
        "classification": "MODEL_MASS_BALANCE_AUDIT"
    }

    with open(VALIDATION_DIR / "m5_mass_balance.json", "w", encoding="utf-8") as f:
        json.dump(mass_balance_manifest, f, indent=2)
    print(f"[OK] Saved mass-balance manifest: {VALIDATION_DIR / 'm5_mass_balance.json'}")

    # 9. Diagnostic Map Visualizations (Tasks 26)
    print("Generating diagnostic maps (Domain, Max Depth, Max Velocity, Arrival Time, Station Hydrographs)...")
    breach_pt = breach_gdf.geometry.iloc[0]

    # Map 1: Domain Overview (m5_domain.png)
    fig, ax = plt.subplots(figsize=(12, 8), dpi=200)
    domain_gdf.plot(ax=ax, color="#eef2f7", edgecolor="#2c3e50", linewidth=1.5, label="2D Simulation Domain")
    river_gdf.plot(ax=ax, color="#2980b9", linewidth=2.5, label="Bhavani River Mainstem")
    ax.scatter([breach_pt.x], [breach_pt.y], color="#c0392b", s=120, marker="X", zorder=5, label=f"Breach Inflow Boundary ({breach_pt.x:.0f}, {breach_pt.y:.0f})")
    for _, row in obs_gdf.iterrows():
        ax.scatter([row.geometry.x], [row.geometry.y], color="#d35400", s=60, marker="o", zorder=4)
        ax.annotate(row["station_id"].replace("Station_", ""), (row.geometry.x + 300, row.geometry.y + 300), fontsize=9, weight="bold", color="#78281f")
    ax.set_title("JalRakshak-HD Milestone M5: Downstream 2D Hydrodynamic Domain & Monitoring Stations\nBhavanisagar Dam Downstream (EPSG:32643)", fontsize=12, weight="bold", pad=12)
    ax.set_xlabel("Easting (m, UTM Zone 43N)", fontsize=10)
    ax.set_ylabel("Northing (m, UTM Zone 43N)", fontsize=10)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m5_domain.png")
    plt.close()

    # Map 2: Maximum Water Depth (m5_max_depth.png)
    fig, ax = plt.subplots(figsize=(12, 8), dpi=200)
    d_masked = np.ma.masked_where(raster_depth < 0.05, raster_depth)
    im = ax.imshow(d_masked, extent=[bounds[0], bounds[2], bounds[1], bounds[3]], cmap="Blues", vmin=0, vmax=min(max_depth_val, 25.0), origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("Maximum Inundation Depth (m)", fontsize=10, weight="bold")
    river_gdf.plot(ax=ax, color="darkblue", linewidth=1.0, alpha=0.5, label="Bhavani Mainstem")
    domain_gdf.boundary.plot(ax=ax, color="black", linewidth=1.2)
    ax.scatter([breach_pt.x], [breach_pt.y], color="red", s=100, marker="X", zorder=5, label="Breach Origin")
    ax.set_title(f"JalRakshak-HD Milestone M5: Maximum Inundation Depth (2D D-Flow FM)\nPeak Discharge = 18,742 m³/s | Max Depth = {max_depth_val:.2f} m | Inundated Area = {wetted_area_km2:.1f} km²", fontsize=12, weight="bold", pad=12)
    ax.set_xlabel("Easting (m, UTM Zone 43N)", fontsize=10)
    ax.set_ylabel("Northing (m, UTM Zone 43N)", fontsize=10)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m5_max_depth.png")
    plt.close()

    # Map 3: Maximum Velocity (m5_max_velocity.png)
    fig, ax = plt.subplots(figsize=(12, 8), dpi=200)
    v_masked = np.ma.masked_where(raster_depth < 0.05, raster_vel)
    im = ax.imshow(v_masked, extent=[bounds[0], bounds[2], bounds[1], bounds[3]], cmap="YlOrRd", vmin=0, vmax=min(max_vel_val, 8.0), origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("Maximum Flow Velocity (m/s)", fontsize=10, weight="bold")
    domain_gdf.boundary.plot(ax=ax, color="black", linewidth=1.2)
    ax.scatter([breach_pt.x], [breach_pt.y], color="black", s=100, marker="X", zorder=5, label="Breach Origin")
    ax.set_title(f"JalRakshak-HD Milestone M5: Maximum Flow Velocity Magnitude (2D D-Flow FM)\nPeak Discharge = 18,742 m³/s | Max Velocity = {max_vel_val:.2f} m/s | 95th Percentile = {p95_vel_val:.2f} m/s", fontsize=12, weight="bold", pad=12)
    ax.set_xlabel("Easting (m, UTM Zone 43N)", fontsize=10)
    ax.set_ylabel("Northing (m, UTM Zone 43N)", fontsize=10)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m5_max_velocity.png")
    plt.close()

    # Map 4: Flood Wave Arrival Time (m5_arrival_time.png)
    fig, ax = plt.subplots(figsize=(12, 8), dpi=200)
    im = ax.imshow(raster_arrival, extent=[bounds[0], bounds[2], bounds[1], bounds[3]], cmap="viridis_r", vmin=0, vmax=min(t_end_hr, 30.0), origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("Wave Arrival Time (Hours from Breach)", fontsize=10, weight="bold")
    domain_gdf.boundary.plot(ax=ax, color="black", linewidth=1.2)
    river_gdf.plot(ax=ax, color="white", linewidth=1.0, alpha=0.6)
    ax.scatter([breach_pt.x], [breach_pt.y], color="red", s=100, marker="X", zorder=5, label="Breach Origin (t=0 hr)")
    for _, row in obs_gdf.iterrows():
        ax.scatter([row.geometry.x], [row.geometry.y], color="white", s=40, marker="o", edgecolors="black", zorder=4)
    ax.set_title("JalRakshak-HD Milestone M5: Flood Wave Arrival Time Isochrones (2D D-Flow FM)\nThreshold Depth = 0.05 m | Downstream Wave Propagation Across Bhavani Basin", fontsize=12, weight="bold", pad=12)
    ax.set_xlabel("Easting (m, UTM Zone 43N)", fontsize=10)
    ax.set_ylabel("Northing (m, UTM Zone 43N)", fontsize=10)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m5_arrival_time.png")
    plt.close()

    # Map 5: Observation Station Hydrographs (m5_station_hydrographs.png)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), dpi=200, sharex=True)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

    for idx, (st_id, data) in enumerate(obs_ts_dict.items()):
        c = colors[idx % len(colors)]
        lbl = f"{st_id.replace('Station_', '')} (Peak {max(data['depth_m']):.1f}m)"
        ax1.plot(data["time_hr"], data["depth_m"], label=lbl, color=c, linewidth=2.0)

        lbl_v = f"{st_id.replace('Station_', '')} (Peak {max(data['velocity_ms']):.1f}m/s)"
        ax2.plot(data["time_hr"], data["velocity_ms"], label=lbl_v, color=c, linewidth=2.0)

    ax1.set_title("JalRakshak-HD Milestone M5: Inundation Stage & Velocity Hydrographs Along Bhavani Mainstem\nChainages from 1 km to 50 km Downstream of Bhavanisagar Dam", fontsize=12, weight="bold", pad=10)
    ax1.set_ylabel("Water Depth (m)", fontsize=10, weight="bold")
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="upper right", fontsize=8, ncol=2)

    ax2.set_xlabel("Time from Breach Initiation (Hours)", fontsize=10, weight="bold")
    ax2.set_ylabel("Flow Velocity Magnitude (m/s)", fontsize=10, weight="bold")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="upper right", fontsize=8, ncol=2)

    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m5_station_hydrographs.png")
    plt.close()
    print("[OK] Generated all diagnostic maps successfully.")

    ds_map.close()

    results_summary = {
        "max_depth_m": max_depth_val,
        "median_depth_m": median_depth_val,
        "p95_depth_m": p95_depth_val,
        "max_velocity_ms": max_vel_val,
        "median_velocity_ms": median_vel_val,
        "p95_velocity_ms": p95_vel_val,
        "inundated_area_km2": wetted_area_km2,
        "simulated_duration_hr": t_end_hr,
        "num_timesteps": num_timesteps,
        "mass_residual_mcm": mass_residual_mcm,
        "mass_residual_percent": mass_residual_pct
    }
    return results_summary


if __name__ == "__main__":
    extract_dflow_results()
