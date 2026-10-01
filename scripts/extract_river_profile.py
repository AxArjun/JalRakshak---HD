"""
Extract Downstream Bhavani River Longitudinal Elevation Profile.
SIH PS 26161 - JalRakshak-HD Milestone M2 Repair.

Samples 100m cross-section chainage stations along the verified downstream
Bhavani mainstem over the conditioned DEM.
Saves:
  - data/hydrology/river_profile.csv
  - outputs/validation/river_profile_summary.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import rasterio
from shapely.geometry import Point
import yaml

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLING_INTERVAL_M = 100.0


def extract_river_profile():
    mainstem_gpkg = PROJECT_ROOT / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
    dem_path = PROJECT_ROOT / "data" / "hydrology" / "dem_hydroconditioned.tif"
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"

    if not mainstem_gpkg.exists() or not dem_path.exists():
        raise FileNotFoundError("Downstream mainstem GPKG or conditioned DEM missing.")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    frl_elev = config["dam"]["hydraulic_levels_msl"]["official_frl_m"]
    proj_crs = config["aoi"]["projected_crs"]

    dam_pt = Point(config["dam"]["longitude"], config["dam"]["latitude"])
    dam_pt_proj = gpd.GeoSeries([dam_pt], crs="EPSG:4326").to_crs(proj_crs).iloc[0]

    gdf_mainstem = gpd.read_file(mainstem_gpkg)
    main_line = gdf_mainstem.geometry.iloc[0]

    total_len_m = float(main_line.length)
    chainages = np.arange(0, total_len_m, SAMPLING_INTERVAL_M)

    print(f"Sampling longitudinal profile at {SAMPLING_INTERVAL_M}m intervals along {total_len_m/1000.0:.2f} km reach...")

    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        trans = src.transform
        nodata = src.nodata

    records = []
    for ch in chainages:
        pt_proj = main_line.interpolate(ch)
        pt_wgs = gpd.GeoSeries([pt_proj], crs=proj_crs).to_crs("EPSG:4326").iloc[0]
        r, c = src.index(pt_proj.x, pt_proj.y)

        if 0 <= r < dem.shape[0] and 0 <= c < dem.shape[1]:
            val = float(dem[r, c])
            elev = val if (val != nodata and not np.isnan(val) and val > -500.0) else np.nan
        else:
            elev = np.nan

        records.append({
            "chainage_m": round(float(ch), 2),
            "x": round(float(pt_proj.x), 2),
            "y": round(float(pt_proj.y), 2),
            "longitude": round(float(pt_wgs.x), 6),
            "latitude": round(float(pt_wgs.y), 6),
            "dem_elevation_m": round(elev, 2) if not np.isnan(elev) else None
        })

    df = pd.DataFrame(records)

    # Filter out any tail NaN values if reached edge
    df_valid = df.dropna(subset=["dem_elevation_m"]).copy()

    csv_path = PROJECT_ROOT / "data" / "hydrology" / "river_profile.csv"
    df_valid.to_csv(csv_path, index=False)
    print(f"Saved river profile CSV: {csv_path.relative_to(PROJECT_ROOT)} ({len(df_valid)} stations)")

    elevations = df_valid["dem_elevation_m"].values
    start_elev = float(elevations[0])
    end_elev = float(elevations[-1])
    net_fall = float(start_elev - end_elev)
    valid_len_m = float(df_valid["chainage_m"].iloc[-1] - df_valid["chainage_m"].iloc[0])
    avg_slope = float(net_fall / (valid_len_m / 1000.0))

    start_pt = Point(df_valid["x"].iloc[0], df_valid["y"].iloc[0])
    start_dist_dam = float(start_pt.distance(dam_pt_proj))

    elev_diffs = np.diff(elevations)
    uphills = elev_diffs[elev_diffs > 0]
    num_uphills = int(len(uphills))
    max_uphill = float(uphills.max()) if len(uphills) > 0 else 0.0

    starts_above_frl = bool(start_elev > frl_elev)

    val_json_path = PROJECT_ROOT / "outputs" / "validation" / "river_profile_summary.json"
    val_json_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "status": "PASS" if not starts_above_frl and net_fall > 0 else "FAIL",
        "river_name": "Bhavani River Mainstem (Downstream Reach)",
        "profile_metrics": {
            "total_profile_length_m": round(valid_len_m, 2),
            "total_profile_length_km": round(valid_len_m / 1000.0, 3),
            "sampling_interval_m": SAMPLING_INTERVAL_M,
            "total_sample_points": len(df_valid),
            "start_distance_from_dam_m": round(start_dist_dam, 2),
            "start_coordinate": {
                "latitude": float(df_valid["latitude"].iloc[0]),
                "longitude": float(df_valid["longitude"].iloc[0]),
                "x_projected": float(df_valid["x"].iloc[0]),
                "y_projected": float(df_valid["y"].iloc[0])
            },
            "start_dem_elevation_m": round(start_elev, 2),
            "end_dem_elevation_m": round(end_elev, 2),
            "net_elevation_fall_m": round(net_fall, 2),
            "average_slope_m_per_km": round(avg_slope, 3),
            "average_longitudinal_slope": round(avg_slope / 1000.0, 6),
            "number_of_uphill_steps": num_uphills,
            "max_uphill_step_m": round(max_uphill, 2),
            "frl_reference_elevation_m": frl_elev,
            "starts_above_frl": starts_above_frl
        },
        "output_files": {
            "profile_csv": str(csv_path.relative_to(PROJECT_ROOT)),
            "summary_json": str(val_json_path.relative_to(PROJECT_ROOT))
        }
    }

    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 80)
    print(f"River Profile Summary:")
    print(f"  Start Station:  {df_valid['latitude'].iloc[0]:.6f} N, {df_valid['longitude'].iloc[0]:.6f} E (Distance to dam: {start_dist_dam:.2f} m)")
    print(f"  Start Elev:     {start_elev:.2f} m MSL (FRL: {frl_elev:.2f} m MSL, Starts above FRL: {starts_above_frl})")
    print(f"  End Elev:       {end_elev:.2f} m MSL")
    print(f"  Net Fall:       {net_fall:.2f} m over {valid_len_m/1000.0:.2f} km")
    print(f"  Average Slope:  {avg_slope:.3f} m/km")
    print(f"  Max Uphill:     {max_uphill:.2f} m (Local noise steps: {num_uphills}/{len(elev_diffs)})")
    print("=" * 80)


if __name__ == "__main__":
    extract_river_profile()
