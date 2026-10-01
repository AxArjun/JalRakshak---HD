"""
JalRakshak-HD: Multi-Sector HADR Consequence & Exposure Overlay Engine (Milestone M8)
====================================================================================
Computes rigorous spatial overlays between validated hydraulic hazard severity (CWC H1–H6)
and multi-sector exposure layers:
1. Gridded Population: WorldPop 2020 (Primary) + GHSL 2025 (Cross-check) with arrival-time context.
2. Building Footprints: Google Open Buildings v3 (confidence >= 0.75), identifying H5/H6 structural exposure.
3. Land Cover Consequences: ESA WorldCover 2021 (Cropland Class 40, Built-up Class 50).
4. Transportation Infrastructure: OSM Road network (by highway class) & Bridge screening.
5. Critical Facilities: OSM Healthcare, Education, Emergency Services, Government, Community Assembly.

Adheres strictly to scientific rules:
- NO casual/fabricated numbers; every metric traces to real data layers.
- NO arbitrary casualty/monetary loss formulas.
- Buildings in H5/H6 classified as H5_H6_STRUCTURAL_DAMAGE_EXPOSURE.
- Roads classified as HYDRAULICALLY_EXPOSED_ROAD_SEGMENT.
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
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from shapely.geometry import Point, box

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.hazard_classification import HazardClass, HAZARD_METADATA

HADR_DIR = ROOT_DIR / "data" / "hadr"
SIM_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
HADR_OUT_DIR = ROOT_DIR / "outputs" / "hadr"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
REPORTS_DIR = ROOT_DIR / "outputs" / "reports"

HADR_OUT_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_population_exposure():
    print("\n--- 1. Population Exposure Analysis (WorldPop & GHSL) ---")
    
    haz_tif_path = HADR_OUT_DIR / "hazard_class.tif"
    arr_h3_tif_path = HADR_OUT_DIR / "arrival_time_h3.tif"
    wp_path = HADR_DIR / "population_projected.tif"
    ghsl_path = HADR_DIR / "ghsl_projected.tif"

    with rasterio.open(haz_tif_path) as src_haz:
        haz_arr = src_haz.read(1)
        haz_meta = src_haz.meta.copy()
        haz_bounds = src_haz.bounds
        haz_transform = src_haz.transform
        haz_crs = src_haz.crs
        out_shape = haz_arr.shape

    # Reproject WorldPop onto exact hazard grid (preserving density/sum)
    wp_grid = np.zeros(out_shape, dtype=np.float32)
    with rasterio.open(wp_path) as src_wp:
        reproject(
            source=rasterio.band(src_wp, 1),
            destination=wp_grid,
            src_transform=src_wp.transform,
            src_crs=src_wp.crs,
            dst_transform=haz_transform,
            dst_crs=haz_crs,
            resampling=Resampling.bilinear
        )
    wp_grid = np.maximum(wp_grid, 0.0)

    # Reproject GHSL onto exact hazard grid
    ghsl_grid = np.zeros(out_shape, dtype=np.float32)
    with rasterio.open(ghsl_path) as src_ghsl:
        reproject(
            source=rasterio.band(src_ghsl, 1),
            destination=ghsl_grid,
            src_transform=src_ghsl.transform,
            src_crs=src_ghsl.crs,
            dst_transform=haz_transform,
            dst_crs=haz_crs,
            resampling=Resampling.bilinear
        )
    ghsl_grid = np.maximum(ghsl_grid, 0.0)

    # Read arrival times
    with rasterio.open(arr_h3_tif_path) as src_arr:
        arr_h3_grid = src_arr.read(1)

    hazard_names = ["DRY", "H1", "H2", "H3", "H4", "H5", "H6"]
    pop_records = []
    
    total_wp_inundated = float(np.sum(wp_grid[haz_arr > 0]))
    total_ghsl_inundated = float(np.sum(ghsl_grid[haz_arr > 0]))

    wp_by_class = {}
    ghsl_by_class = {}

    for c in range(1, 7):
        c_mask = haz_arr == c
        wp_c = float(np.sum(wp_grid[c_mask]))
        ghsl_c = float(np.sum(ghsl_grid[c_mask]))
        c_name = hazard_names[c]
        wp_by_class[c_name] = round(wp_c, 1)
        ghsl_by_class[c_name] = round(ghsl_c, 1)

        pop_records.append({
            "hazard_code": c,
            "hazard_class": c_name,
            "description": HAZARD_METADATA[HazardClass(c)]["description"],
            "worldpop_population": round(wp_c, 1),
            "worldpop_percentage": round((wp_c / total_wp_inundated * 100), 2) if total_wp_inundated > 0 else 0.0,
            "ghsl_population": round(ghsl_c, 1),
            "ghsl_percentage": round((ghsl_c / total_ghsl_inundated * 100), 2) if total_ghsl_inundated > 0 else 0.0,
            "dataset_spread": round(abs(ghsl_c - wp_c), 1)
        })

    df_pop = pd.DataFrame(pop_records)
    pop_csv_path = HADR_OUT_DIR / "population_exposure_by_hazard.csv"
    df_pop.to_csv(pop_csv_path, index=False)
    print(f"[OK] Saved: {pop_csv_path}")

    # Severe & Extreme summaries
    wp_severe = float(np.sum(wp_grid[haz_arr >= 3]))
    ghsl_severe = float(np.sum(ghsl_grid[haz_arr >= 3]))
    wp_extreme = float(np.sum(wp_grid[haz_arr >= 5]))
    ghsl_extreme = float(np.sum(ghsl_grid[haz_arr >= 5]))

    spread_total = abs(total_ghsl_inundated - total_wp_inundated)
    ratio_ghsl_wp = (total_ghsl_inundated / total_wp_inundated) if total_wp_inundated > 0 else 1.0

    print(f"  WorldPop Total Inundated: {total_wp_inundated:,.1f} | Severe (H3-H6): {wp_severe:,.1f} | Extreme (H5-H6): {wp_extreme:,.1f}")
    print(f"  GHSL Total Inundated:     {total_ghsl_inundated:,.1f} | Severe (H3-H6): {ghsl_severe:,.1f} | Extreme (H5-H6): {ghsl_extreme:,.1f}")
    print(f"  Cross-Check Spread:       {spread_total:,.1f} people (Ratio GHSL/WorldPop = {ratio_ghsl_wp:.2f})")

    # Cross-check JSON
    pop_crosscheck = {
        "milestone": "M8",
        "primary_dataset": "WorldPop 2020 UN-Adjusted (100m)",
        "crosscheck_dataset": "GHSL GHS-POP R2023A (100m)",
        "worldpop_total_inundated": round(total_wp_inundated, 1),
        "worldpop_severe_h3_h6": round(wp_severe, 1),
        "worldpop_extreme_h5_h6": round(wp_extreme, 1),
        "worldpop_by_hazard": wp_by_class,
        "ghsl_total_inundated": round(total_ghsl_inundated, 1),
        "ghsl_severe_h3_h6": round(ghsl_severe, 1),
        "ghsl_extreme_h5_h6": round(ghsl_extreme, 1),
        "ghsl_by_hazard": ghsl_by_class,
        "absolute_dataset_spread": round(spread_total, 1),
        "ratio_ghsl_to_worldpop": round(ratio_ghsl_wp, 3),
        "notes": "Population numbers represent gridded screening estimates. The divergence between WorldPop and GHSL is documented as DATASET_SPREAD."
    }
    with open(VALIDATION_DIR / "m8_population_crosscheck.json", "w", encoding="utf-8") as f:
        json.dump(pop_crosscheck, f, indent=2)
    print(f"[OK] Saved: {VALIDATION_DIR / 'm8_population_crosscheck.json'}")

    # Arrival-time exposure context
    arrival_windows = [
        (0.0, 1.0, "< 1 hour", 60),
        (1.0, 2.0, "1 - 2 hours", 120),
        (2.0, 3.0, "2 - 3 hours", 180),
        (3.0, 4.0, "3 - 4 hours", 240),
        (4.0, 6.0, "4 - 6 hours", 360),
        (6.0, 8.0, "6 - 8 hours", 480),
        (8.0, 12.0, "8 - 12 hours", 720),
        (12.0, 24.0, "12 - 24 hours", 1440),
        (24.0, 48.0, "> 24 hours", 2880),
    ]

    arr_records = []
    cum_wp = 0.0
    for t_min, t_max, w_label, w_min in arrival_windows:
        win_mask = (arr_h3_grid >= t_min) & (arr_h3_grid < t_max) & (haz_arr >= 3)
        wp_win = float(np.sum(wp_grid[win_mask]))
        ghsl_win = float(np.sum(ghsl_grid[win_mask]))
        cum_wp += wp_win
        cum_pct = (cum_wp / wp_severe * 100) if wp_severe > 0 else 0.0

        arr_records.append({
            "time_window_hr": w_label,
            "arrival_window_min": w_min,
            "population_exposed_worldpop": round(wp_win, 1),
            "population_exposed_ghsl": round(ghsl_win, 1),
            "cumulative_worldpop": round(cum_wp, 1),
            "cumulative_pct": round(cum_pct, 2)
        })

    df_arr = pd.DataFrame(arr_records)
    arr_csv_path = HADR_OUT_DIR / "population_arrival_context.csv"
    df_arr.to_csv(arr_csv_path, index=False)
    print(f"[OK] Saved: {arr_csv_path}")

    return {
        "worldpop_total_inundated": round(total_wp_inundated, 1),
        "worldpop_severe_h3_h6": round(wp_severe, 1),
        "worldpop_extreme_h5_h6": round(wp_extreme, 1),
        "worldpop_by_hazard_class": wp_by_class,
        "ghsl_total_inundated": round(total_ghsl_inundated, 1),
        "ghsl_severe_h3_h6": round(ghsl_severe, 1),
        "ghsl_extreme_h5_h6": round(ghsl_extreme, 1),
        "ghsl_by_hazard_class": ghsl_by_class,
        "population_crosscheck_dataset_spread": round(spread_total, 1),
        "population_crosscheck_ratio_ghsl_to_worldpop": round(ratio_ghsl_wp, 3),
        "population_arrival_context": arr_records,
        "potential_loss_of_life_model": "NOT_IMPLEMENTED",
        "potential_loss_of_life_status": "SCREENING_EXPOSURE_ONLY_NO_CASUALTY_ESTIMATION"
    }


def compute_building_exposure():
    print("\n--- 2. Building Footprint Exposure Analysis (Google Open Buildings v3) ---")
    bld_path = HADR_DIR / "buildings.gpkg"
    haz_tif_path = HADR_OUT_DIR / "hazard_class.tif"
    depth_tif_path = SIM_DIR / "max_water_depth.tif"
    vel_tif_path = SIM_DIR / "max_velocity.tif"

    if not bld_path.exists():
        print("WARNING: buildings.gpkg not found!")
        return {}

    gdf_bld = gpd.read_file(bld_path)
    print(f"Loaded {len(gdf_bld)} building footprints in study area.")

    # Sample raster values at building centroids
    centroids = gdf_bld.geometry.centroid
    coords = [(p.x, p.y) for p in centroids]

    with rasterio.open(haz_tif_path) as src_haz:
        haz_samples = np.array([val[0] for val in src_haz.sample(coords)])

    with rasterio.open(depth_tif_path) as src_depth:
        depth_samples = np.array([val[0] for val in src_depth.sample(coords)])

    with rasterio.open(vel_tif_path) as src_vel:
        vel_samples = np.array([val[0] for val in src_vel.sample(coords)])

    gdf_bld["hazard_code"] = haz_samples
    gdf_bld["max_water_depth_m"] = np.maximum(depth_samples, 0.0)
    gdf_bld["max_velocity_mps"] = np.maximum(vel_samples, 0.0)

    hazard_names = ["DRY", "H1", "H2", "H3", "H4", "H5", "H6"]
    gdf_bld["hazard_class"] = [hazard_names[int(c)] if c in range(7) else "DRY" for c in haz_samples]

    # Filter exposed buildings (hazard_code >= 1)
    gdf_exposed = gdf_bld[gdf_bld["hazard_code"] >= 1].copy()
    
    # Classify structural damage exposure for H5 and H6
    gdf_exposed["structural_vulnerability"] = "EXPOSURE_LOW_TO_MODERATE"
    gdf_exposed.loc[gdf_exposed["hazard_code"] == 3, "structural_vulnerability"] = "EXPOSURE_SIGNIFICANT"
    gdf_exposed.loc[gdf_exposed["hazard_code"] == 4, "structural_vulnerability"] = "EXPOSURE_SEVERE"
    gdf_exposed.loc[gdf_exposed["hazard_code"].isin([5, 6]), "structural_vulnerability"] = "H5_H6_STRUCTURAL_DAMAGE_EXPOSURE"

    # Save exposed buildings GeoPackage
    bld_out_gpkg = HADR_OUT_DIR / "building_exposure.gpkg"
    gdf_exposed.to_file(bld_out_gpkg, driver="GPKG")
    print(f"[OK] Saved {len(gdf_exposed)} exposed buildings to {bld_out_gpkg}")

    # Summary table by hazard class
    bld_by_class = {}
    bld_records = []
    total_bld = len(gdf_exposed)
    total_footprint_m2 = float(gdf_exposed["footprint_area_m2"].sum()) if "footprint_area_m2" in gdf_exposed else 0.0

    for c in range(1, 7):
        c_name = hazard_names[c]
        sub = gdf_exposed[gdf_exposed["hazard_code"] == c]
        c_count = len(sub)
        c_area = float(sub["footprint_area_m2"].sum()) if "footprint_area_m2" in sub else 0.0
        bld_by_class[c_name] = c_count
        bld_records.append({
            "hazard_code": c,
            "hazard_class": c_name,
            "building_count": c_count,
            "pct_of_exposed": round((c_count / total_bld * 100), 2) if total_bld > 0 else 0.0,
            "total_footprint_area_m2": round(c_area, 1),
            "structural_classification": "H5_H6_STRUCTURAL_DAMAGE_EXPOSURE" if c in [5, 6] else "EXPOSURE_ONLY"
        })

    df_bld_summary = pd.DataFrame(bld_records)
    bld_csv_path = HADR_OUT_DIR / "building_exposure_by_hazard.csv"
    df_bld_summary.to_csv(bld_csv_path, index=False)
    print(f"[OK] Saved: {bld_csv_path}")

    severe_bld = int(len(gdf_exposed[gdf_exposed["hazard_code"] >= 3]))
    h5_h6_bld = int(len(gdf_exposed[gdf_exposed["hazard_code"] >= 5]))

    print(f"  Total Inundated Buildings: {total_bld} ({total_footprint_m2/1e6:.2f} km2 footprint)")
    print(f"  Severe Hazard Buildings (H3-H6): {severe_bld} ({(severe_bld/total_bld*100):.1f}%)")
    print(f"  Structural Vulnerability (H5-H6): {h5_h6_bld} ({(h5_h6_bld/total_bld*100):.1f}%) [H5_H6_STRUCTURAL_DAMAGE_EXPOSURE]")

    return {
        "dataset": "Google Open Buildings v3 (confidence >= 0.75)",
        "total_buildings_inundated": total_bld,
        "total_footprint_area_m2": round(total_footprint_m2, 1),
        "severe_h3_h6_buildings": severe_bld,
        "h5_h6_structural_damage_exposure": h5_h6_bld,
        "buildings_by_hazard_class": bld_by_class,
        "building_damage_state": "EXPOSURE_ONLY_NO_FRAGILITY_CURVES",
        "damage_classification_note": "Buildings in H5/H6 classified as H5_H6_STRUCTURAL_DAMAGE_EXPOSURE, NOT assumed destroyed"
    }


def compute_landcover_exposure():
    print("\n--- 3. Land Cover Consequence Screening (ESA WorldCover 2021) ---")
    haz_tif_path = HADR_OUT_DIR / "hazard_class.tif"
    wc_path = HADR_DIR / "worldcover_projected.tif"

    with rasterio.open(haz_tif_path) as src_haz:
        haz_arr = src_haz.read(1)
        haz_transform = src_haz.transform
        haz_crs = src_haz.crs
        out_shape = haz_arr.shape

    # Reproject WorldCover onto hazard grid using nearest neighbor
    wc_grid = np.zeros(out_shape, dtype=np.uint8)
    with rasterio.open(wc_path) as src_wc:
        reproject(
            source=rasterio.band(src_wc, 1),
            destination=wc_grid,
            src_transform=src_wc.transform,
            src_crs=src_wc.crs,
            dst_transform=haz_transform,
            dst_crs=haz_crs,
            resampling=Resampling.nearest
        )

    # Pixel area = 100m x 100m = 10,000 m2 = 0.01 km2
    pixel_area_km2 = (abs(haz_transform[0]) * abs(haz_transform[4])) / 1e6

    hazard_names = ["DRY", "H1", "H2", "H3", "H4", "H5", "H6"]
    
    # Classes: 10=Tree, 20=Shrub, 30=Grass, 40=Cropland, 50=Built-up, 60=Bare, 80=Water, 90=Wetland
    lc_classes = {
        10: "Tree cover",
        20: "Shrubland",
        30: "Grassland",
        40: "Cropland",
        50: "Built-up",
        60: "Bare / sparse vegetation",
        80: "Permanent water bodies",
        90: "Herbaceous wetland",
    }

    inundated_mask = haz_arr > 0
    total_cropland_km2 = float(np.sum((wc_grid == 40) & inundated_mask) * pixel_area_km2)
    severe_cropland_km2 = float(np.sum((wc_grid == 40) & (haz_arr >= 3)) * pixel_area_km2)
    
    total_builtup_km2 = float(np.sum((wc_grid == 50) & inundated_mask) * pixel_area_km2)
    severe_builtup_km2 = float(np.sum((wc_grid == 50) & (haz_arr >= 3)) * pixel_area_km2)

    cropland_by_haz = {}
    builtup_by_haz = {}
    lc_matrix = []

    for c in range(1, 7):
        c_name = hazard_names[c]
        c_mask = haz_arr == c
        crop_c = float(np.sum((wc_grid == 40) & c_mask) * pixel_area_km2)
        built_c = float(np.sum((wc_grid == 50) & c_mask) * pixel_area_km2)
        cropland_by_haz[c_name] = round(crop_c, 3)
        builtup_by_haz[c_name] = round(built_c, 3)

        rec = {
            "hazard_code": c,
            "hazard_class": c_name,
            "cropland_km2": round(crop_c, 3),
            "builtup_km2": round(built_c, 3),
        }
        for code, label in lc_classes.items():
            if code not in [40, 50]:
                val = float(np.sum((wc_grid == code) & c_mask) * pixel_area_km2)
                rec[f"{label.lower().replace(' ', '_')}_km2"] = round(val, 3)
        lc_matrix.append(rec)

    df_lc = pd.DataFrame(lc_matrix)
    lc_csv_path = HADR_OUT_DIR / "landcover_exposure_by_hazard.csv"
    df_lc.to_csv(lc_csv_path, index=False)
    print(f"[OK] Saved: {lc_csv_path}")

    other_km2 = float(np.sum((wc_grid != 40) & (wc_grid != 50) & inundated_mask) * pixel_area_km2)

    print(f"  Cropland Inundated (Class 40): {total_cropland_km2:.2f} km2 (Severe H3-H6: {severe_cropland_km2:.2f} km2)")
    print(f"  Built-up Inundated (Class 50): {total_builtup_km2:.2f} km2 (Severe H3-H6: {severe_builtup_km2:.2f} km2)")
    print(f"  Other Classes Inundated:       {other_km2:.2f} km2")

    return {
        "dataset": "ESA WorldCover 2021 v200 (10m categorical, nearest-neighbor reprojected)",
        "cropland_class_40_inundated_km2": round(total_cropland_km2, 3),
        "cropland_severe_h3_h6_km2": round(severe_cropland_km2, 3),
        "cropland_by_hazard_class_km2": cropland_by_haz,
        "builtup_class_50_inundated_km2": round(total_builtup_km2, 3),
        "builtup_severe_h3_h6_km2": round(severe_builtup_km2, 3),
        "builtup_by_hazard_class_km2": builtup_by_haz,
        "other_classes_inundated_km2": round(other_km2, 3),
        "cropland_loss_model": "NOT_IMPLEMENTED",
        "monetary_damage_status": "NOT_IMPLEMENTED_IN_M8"
    }


def compute_infrastructure_exposure():
    print("\n--- 4. Infrastructure & Critical Facilities Exposure Analysis (OSM) ---")
    roads_path = HADR_DIR / "roads.gpkg"
    fac_path = HADR_DIR / "critical_facilities.gpkg"
    haz_tif_path = HADR_OUT_DIR / "hazard_class.tif"
    inundation_path = SIM_DIR / "inundation_extent.gpkg"

    hazard_names = ["DRY", "H1", "H2", "H3", "H4", "H5", "H6"]

    # 1. Roads
    road_exp_summary = {}
    bridge_summary = {}
    if roads_path.exists():
        gdf_roads = gpd.read_file(roads_path)
        gdf_inundation = gpd.read_file(inundation_path)
        
        # Spatial clip to inundation extent
        gdf_roads_inundated = gpd.clip(gdf_roads, gdf_inundation)
        gdf_roads_inundated["exposed_length_m"] = gdf_roads_inundated.geometry.length
        
        # Sample hazard class at midpoints
        midpoints = gdf_roads_inundated.geometry.interpolate(0.5, normalized=True)
        mid_coords = [(p.x, p.y) for p in midpoints]
        with rasterio.open(haz_tif_path) as src_haz:
            haz_road_samples = np.array([val[0] for val in src_haz.sample(mid_coords)])
        
        gdf_roads_inundated["hazard_code"] = haz_road_samples
        gdf_roads_inundated["hazard_class"] = [hazard_names[int(c)] if c in range(7) else "H1" for c in haz_road_samples]
        gdf_roads_inundated["road_exposure_status"] = "HYDRAULICALLY_EXPOSED_ROAD_SEGMENT"

        road_out_gpkg = HADR_OUT_DIR / "road_exposure.gpkg"
        gdf_roads_inundated.to_file(road_out_gpkg, driver="GPKG")
        print(f"[OK] Saved {len(gdf_roads_inundated)} exposed road segments to {road_out_gpkg}")

        total_road_km = float(gdf_roads_inundated["exposed_length_m"].sum() / 1000.0)
        severe_road_km = float(gdf_roads_inundated[gdf_roads_inundated["hazard_code"] >= 3]["exposed_length_m"].sum() / 1000.0)

        # By hazard class
        road_by_haz = {}
        for c in range(1, 7):
            c_name = hazard_names[c]
            c_len = float(gdf_roads_inundated[gdf_roads_inundated["hazard_code"] == c]["exposed_length_m"].sum() / 1000.0)
            road_by_haz[c_name] = round(c_len, 2)

        # By highway type
        road_by_type = {}
        for hw_type, grp in gdf_roads_inundated.groupby("highway"):
            road_by_type[str(hw_type)] = round(float(grp["exposed_length_m"].sum() / 1000.0), 2)

        # Save summary CSV
        road_summary_records = [{"hazard_class": k, "length_km": v} for k, v in road_by_haz.items()]
        pd.DataFrame(road_summary_records).to_csv(HADR_OUT_DIR / "road_exposure_by_hazard.csv", index=False)

        print(f"  Total Inundated Roads: {total_road_km:.2f} km (Severe H3-H6: {severe_road_km:.2f} km)")

        # Bridges
        bridges = gdf_roads_inundated[gdf_roads_inundated["bridge"].isin(["yes", "true", "viaduct"]) | gdf_roads_inundated["name"].str.contains("Bridge|Palam", case=False, na=False)].copy()
        bridge_csv_path = HADR_OUT_DIR / "bridge_exposure.csv"
        
        bridge_records = []
        for _, b_row in bridges.iterrows():
            bridge_records.append({
                "osm_id": b_row.get("osm_id", "unknown"),
                "name": b_row.get("name", "Unnamed Bridge"),
                "highway": b_row.get("highway", "unknown"),
                "hazard_class": b_row.get("hazard_class", "unknown"),
                "hazard_code": b_row.get("hazard_code", 0),
                "exposed_length_m": round(b_row.get("exposed_length_m", 0.0), 1),
                "screening_classification": "BRIDGE_HYDRAULIC_EXPOSURE_SCREENING",
                "notes": "Hydraulic exposure identified; detailed scour/submergence rating requires surveyed deck elevation"
            })
        
        df_bridges = pd.DataFrame(bridge_records)
        df_bridges.to_csv(bridge_csv_path, index=False)
        print(f"[OK] Saved {len(bridges)} screened bridges to {bridge_csv_path}")

        road_exp_summary = {
            "dataset": "OpenStreetMap (OSM) Overpass API",
            "total_roads_inundated_km": round(total_road_km, 2),
            "severe_h3_h6_roads_km": round(severe_road_km, 2),
            "roads_by_hazard_class_km": road_by_haz,
            "roads_by_highway_type_km": road_by_type,
            "road_status_classification": "HYDRAULICALLY_EXPOSED_ROAD_SEGMENT",
            "road_status_note": "Exposed road segments are NOT assumed closed/washed out"
        }

        bridge_summary = {
            "dataset": "OpenStreetMap (OSM) Bridge Attributes & River Intersections",
            "total_bridges_in_study_area": len(gdf_roads[gdf_roads["bridge"].isin(["yes", "true", "viaduct"])]),
            "bridges_hydraulically_exposed": len(bridges),
            "bridges_severe_h3_h6": len(bridges[bridges["hazard_code"] >= 3]),
            "bridge_screening_classification": "BRIDGE_HYDRAULIC_EXPOSURE_SCREENING",
            "bridge_screening_note": "Bridges NOT assumed collapsed; detailed structural/scour rating requires bridge deck elevation surveys"
        }

    # 2. Critical Facilities
    fac_exp_summary = {}
    if fac_path.exists():
        gdf_fac = gpd.read_file(fac_path)
        coords = [(p.x, p.y) for p in gdf_fac.geometry]
        with rasterio.open(haz_tif_path) as src_haz:
            haz_fac_samples = np.array([val[0] for val in src_haz.sample(coords)])

        gdf_fac["hazard_code"] = haz_fac_samples
        gdf_fac["hazard_class"] = [hazard_names[int(c)] if c in range(7) else "DRY" for c in haz_fac_samples]

        gdf_fac_exposed = gdf_fac[gdf_fac["hazard_code"] >= 1].copy()
        
        fac_csv_path = HADR_OUT_DIR / "critical_facility_exposure.csv"
        fac_records = []
        for _, f_row in gdf_fac_exposed.iterrows():
            fac_records.append({
                "osm_id": f_row.get("osm_id", "unknown"),
                "name": f_row.get("name", "Unnamed Facility"),
                "category": f_row.get("category", "other"),
                "facility_type": f_row.get("facility_type", "unknown"),
                "hazard_class": f_row.get("hazard_class", "unknown"),
                "hazard_code": int(f_row.get("hazard_code", 0)),
                "x_utm": round(f_row.geometry.x, 1),
                "y_utm": round(f_row.geometry.y, 1),
            })
        
        df_fac_out = pd.DataFrame(fac_records)
        df_fac_out.to_csv(fac_csv_path, index=False)
        print(f"[OK] Saved {len(gdf_fac_exposed)} exposed critical facilities to {fac_csv_path}")

        fac_by_cat = {}
        for cat, grp in gdf_fac_exposed.groupby("category"):
            fac_by_cat[str(cat)] = int(len(grp))

        fac_by_haz = {}
        for c in range(1, 7):
            c_name = hazard_names[c]
            fac_by_haz[c_name] = int(len(gdf_fac_exposed[gdf_fac_exposed["hazard_code"] == c]))

        print(f"  Total Inundated Facilities: {len(gdf_fac_exposed)} (Severe H3-H6: {len(gdf_fac_exposed[gdf_fac_exposed['hazard_code'] >= 3])})")
        for cat, count in fac_by_cat.items():
            print(f"    - {cat}: {count}")

        fac_exp_summary = {
            "dataset": "OpenStreetMap (OSM) Healthcare, Education, Emergency & Government",
            "total_facilities_inundated": len(gdf_fac_exposed),
            "severe_h3_h6_facilities": int(len(gdf_fac_exposed[gdf_fac_exposed["hazard_code"] >= 3])),
            "facilities_by_category": fac_by_cat,
            "facilities_by_hazard_class": fac_by_haz,
            "facilities_details": fac_records
        }

    return road_exp_summary, bridge_summary, fac_exp_summary


def main():
    print("=" * 80)
    print(" JALRAKSHAK-HD: MULTI-SECTOR HADR EXPOSURE ENGINE (M8)")
    print("=" * 80)

    pop_summary = compute_population_exposure()
    bld_summary = compute_building_exposure()
    lc_summary = compute_landcover_exposure()
    road_summary, bridge_summary, fac_summary = compute_infrastructure_exposure()

    print("\n=== All Multi-Sector Exposure Overlays Computed Successfully ===")


if __name__ == "__main__":
    main()
