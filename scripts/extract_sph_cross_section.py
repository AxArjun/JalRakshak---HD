"""
JalRakshak-HD: Extract Near-Field SPH Longitudinal Cross-Section & Coordinate Transformation
Milestone M6 — Task 3, 4, 5
=============================================================================================
1. Defines near-field centerline along Bhavani mainstem from breach (s = 0) to s = 1.5 km.
2. Samples projected DEM (data/terrain/dem_projected.tif) at <= 30 m resolution.
3. Exports:
   - data/sph/nearfield_centerline.gpkg
   - data/sph/nearfield_bed_profile.csv
   - data/sph/local_coordinate_transform.json
   - outputs/maps/m6_nearfield_profile.png
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import rasterio
from shapely.geometry import LineString, Point

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_SPH = ROOT_DIR / "data" / "sph"
MAPS_DIR = ROOT_DIR / "outputs" / "maps"

BREACH_PATH = ROOT_DIR / "data" / "dflowfm" / "breach_location.gpkg"
RIVER_PATH = ROOT_DIR / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
DEM_PATH = ROOT_DIR / "data" / "terrain" / "dem_projected.tif"


def extract_nearfield_profile(target_length_m: float = 1500.0, step_m: float = 10.0):
    print("=" * 80)
    print(" JALRAKSHAK-HD: EXTRACTING NEAR-FIELD SPH PROFILE (M6 TASK 3-5)")
    print("=" * 80)

    DATA_SPH.mkdir(parents=True, exist_ok=True)
    MAPS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Read input geometries
    breach_gdf = gpd.read_file(BREACH_PATH)
    breach_pt = breach_gdf.geometry.iloc[0]
    breach_x, breach_y = breach_pt.x, breach_pt.y
    print(f"Breach Point (EPSG:32643): ({breach_x:.2f}, {breach_y:.2f})")

    river_gdf = gpd.read_file(RIVER_PATH)
    river_geom = river_gdf.geometry.iloc[0]

    # Find closest point on river and snap / connect from breach
    proj_dist = river_geom.project(breach_pt)
    snapped_pt = river_geom.interpolate(proj_dist)
    print(f"Snapped River Point: ({snapped_pt.x:.2f}, {snapped_pt.y:.2f}) at chainage {proj_dist:.2f} m")

    # Generate points along the downstream centerline starting from breach to snapped point,
    # then advancing along the river geometry for target_length_m
    coords = []
    chainages = []
    
    # Connection segment from breach to snapped point
    d_breach_to_snap = math.hypot(snapped_pt.x - breach_x, snapped_pt.y - breach_y)
    
    # We construct the 1.5 km near-field polyline directly starting at breach (s=0)
    # Sampling at step_m along river
    n_pts = int(math.ceil(target_length_m / step_m)) + 1
    
    # Coordinate transformer to lat/lon (EPSG:4326)
    transformer = pyproj.Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

    with rasterio.open(DEM_PATH) as dem_src:
        dem_data = dem_src.read(1)
        dem_transform = dem_src.transform
        nodata = dem_src.nodata

        profile_records = []
        sampled_points = []

        for i in range(n_pts):
            s = min(i * step_m, target_length_m)
            
            if s <= d_breach_to_snap and d_breach_to_snap > 0:
                # Linear interpolation from breach to snapped river entry point
                frac = s / d_breach_to_snap
                cur_x = breach_x + frac * (snapped_pt.x - breach_x)
                cur_y = breach_y + frac * (snapped_pt.y - breach_y)
            else:
                # Advancing along the river mainstem
                cur_river_dist = proj_dist + (s - d_breach_to_snap)
                pt = river_geom.interpolate(cur_river_dist)
                cur_x = pt.x
                cur_y = pt.y

            lon, lat = transformer.transform(cur_x, cur_y)
            
            # Sample DEM elevation
            row, col = dem_src.index(cur_x, cur_y)
            if 0 <= row < dem_data.shape[0] and 0 <= col < dem_data.shape[1]:
                elev = float(dem_data[row, col])
                if nodata is not None and elev == nodata:
                    elev = np.nan
            else:
                elev = np.nan

            sampled_points.append(Point(cur_x, cur_y))
            profile_records.append({
                "chainage_m": round(s, 2),
                "easting": round(cur_x, 3),
                "northing": round(cur_y, 3),
                "longitude": round(lon, 6),
                "latitude": round(lat, 6),
                "dem_elevation_m": round(elev, 3)
            })

    df_profile = pd.DataFrame(profile_records)
    
    # Clean any NaNs by linear interpolation if present
    df_profile["dem_elevation_m"] = df_profile["dem_elevation_m"].interpolate(method="linear")

    # Save nearfield bed profile CSV
    csv_path = DATA_SPH / "nearfield_bed_profile.csv"
    df_profile.to_csv(csv_path, index=False)
    print(f"Saved near-field bed profile CSV: {csv_path} ({len(df_profile)} points, s in [0, {target_length_m:.1f}] m)")

    # 2. Create Near-field Centerline GPKG
    centerline_geom = LineString([(p.x, p.y) for p in sampled_points])
    start_pt = sampled_points[0]
    end_pt = sampled_points[-1]
    
    dx = end_pt.x - start_pt.x
    dy = end_pt.y - start_pt.y
    mean_angle_deg = math.degrees(math.atan2(dy, dx)) % 360

    gdf_centerline = gpd.GeoDataFrame(
        [{
            "name": "Bhavani Near-Field Centerline",
            "reach_type": "NEAR_FIELD_MAINSTEM",
            "start_easting": round(start_pt.x, 2),
            "start_northing": round(start_pt.y, 2),
            "end_easting": round(end_pt.x, 2),
            "end_northing": round(end_pt.y, 2),
            "length_m": round(centerline_geom.length, 2),
            "mean_orientation_deg": round(mean_angle_deg, 2),
            "terrain_source": "NASA SRTM 30m Projected DEM (EPSG:32643)",
            "sampling_interval_m": step_m,
            "classification": "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL"
        }],
        geometry=[centerline_geom],
        crs="EPSG:32643"
    )
    gpkg_path = DATA_SPH / "nearfield_centerline.gpkg"
    gdf_centerline.to_file(gpkg_path, driver="GPKG")
    print(f"Saved near-field centerline GPKG: {gpkg_path}")

    # 3. Create Local Coordinate Transformation Manifest
    transform_manifest = {
        "milestone": "M6",
        "title": "DualSPHysics Near-Field Local Coordinate Transform Specification",
        "model_classification": "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL",
        "global_crs": "EPSG:32643",
        "global_datum": "WGS 84 / UTM Zone 43N",
        "units": "metres",
        "local_origin": {
            "chainage_m": 0.0,
            "easting_m": round(start_pt.x, 3),
            "northing_m": round(start_pt.y, 3),
            "elevation_ref_m_msl": 0.0,
            "description": "Breach origin at dam toe (s = 0.0 m)"
        },
        "downstream_extent_m": target_length_m,
        "sampling_step_m": step_m,
        "total_profile_nodes": len(df_profile),
        "vertical_reference": {
            "datum": "MSL (Mean Sea Level)",
            "z_min_bed_msl": float(df_profile["dem_elevation_m"].min()),
            "z_max_bed_msl": float(df_profile["dem_elevation_m"].max()),
            "reservoir_frl_msl": 280.42,
            "breach_invert_est_msl": float(df_profile["dem_elevation_m"].iloc[0])
        },
        "transform_equations": {
            "x_sph": "downstream_chainage_m (s)",
            "y_sph": "0.0 (2D unit-width simulation plane)",
            "z_sph": "z_elevation_m_msl",
            "inverse_mapping": "Interpolate (easting, northing) from chainage_m in nearfield_bed_profile.csv"
        }
    }

    json_path = DATA_SPH / "local_coordinate_transform.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(transform_manifest, f, indent=2)
    print(f"Saved local coordinate transform manifest: {json_path}")

    # 4. Generate Diagnostic Visualization (m6_nearfield_profile.png)
    plt.figure(figsize=(12, 6), dpi=300)
    plt.plot(df_profile["chainage_m"], df_profile["dem_elevation_m"], color="#2c3e50", lw=2.5, label="Riverbed Elevation (SRTM 30m DEM)")
    plt.fill_between(df_profile["chainage_m"], df_profile["dem_elevation_m"].min() - 5, df_profile["dem_elevation_m"], color="#d5dbdb", alpha=0.6)

    # Key lines
    frl = 280.42
    plt.axhline(frl, color="#e74c3c", ls="--", lw=1.8, label=f"Reservoir FRL = {frl:.2f} m MSL (CWC Verified)")
    
    # Station markers
    stations = [100, 250, 500, 1000, 1500]
    for st in stations:
        if st <= target_length_m:
            st_elev = float(df_profile.loc[(df_profile["chainage_m"] - st).abs().idxmin(), "dem_elevation_m"])
            plt.plot(st, st_elev, "o", color="#2980b9", markersize=6)
            plt.annotate(f"{st} m\n({st_elev:.1f} m)", xy=(st, st_elev), xytext=(st, st_elev + 4),
                         ha="center", fontsize=8, fontweight="bold",
                         arrowprops=dict(arrowstyle="->", color="#2980b9", lw=1))

    plt.title("JalRakshak-HD: DualSPHysics 2D Near-Field Bed Profile (M6)\nBhavani River Mainstem Reach [0 to 1.5 km] | EPSG:32643", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Downstream Chainage from Breach (m)", fontsize=11, fontweight="bold")
    plt.ylabel("Elevation (m MSL)", fontsize=11, fontweight="bold")
    plt.ylim(df_profile["dem_elevation_m"].min() - 5, frl + 10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right", frameon=True, fontsize=10)

    # Disclaimer note
    plt.figtext(0.13, 0.02, "Screening Model Disclaimer: Bed topography derived from NASA SRTM 30m projected DEM. No underwater bathymetry surveyed.",
                fontsize=8, style="italic", color="#7f8c8d")

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    map_png = MAPS_DIR / "m6_nearfield_profile.png"
    plt.savefig(map_png)
    plt.close()
    print(f"Saved profile visualization: {map_png}")

    print("Profile extraction complete.")
    return df_profile


if __name__ == "__main__":
    extract_nearfield_profile()
