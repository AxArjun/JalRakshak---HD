"""
JalRakshak-HD: Milestone M10 Task 1 & 48 — Dashboard Asset Builder & Data Inventory
===================================================================================
1. Inventories all M0-M9 data layers and outputs (outputs/validation/m10_dashboard_data_inventory.json).
2. Generates optimized GeoJSON layers in EPSG:4326 for Leaflet map loading.
3. Renders georeferenced transparent PNG overlays for static raster layers (max depth, max velocity, arrival time, hazard, hillshade, satellite).
4. Generates SPH near-field 1.5 km reach and gauge GeoJSON layers.
"""

from __future__ import annotations

import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pyproj import Transformer
from shapely.geometry import Point, LineString

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DASHBOARD_DIR = ROOT_DIR / "outputs" / "dashboard"
OUTPUT_DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_GEOJSON_DIR = OUTPUT_DASHBOARD_DIR / "geojson"
OUTPUT_GEOJSON_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_OVERLAYS_DIR = OUTPUT_DASHBOARD_DIR / "overlays"
OUTPUT_OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


def build_data_inventory():
    print("=" * 70)
    print("STEP 1: Building M10 Dashboard Data Inventory")
    print("=" * 70)

    raw_inventory = [
        # Study Area & Hydrology
        {"id": "study_area_config", "path": "configs/study_area.yaml", "milestone": "M1", "classification": "CONFIGURATION", "frontend_role": "Project bounds and dam parameters"},
        {"id": "dam_point", "path": "data/processed/study_area/dam_point_projected.gpkg", "milestone": "M1", "classification": "VECTOR_DAM_LOCATION", "frontend_role": "Dam marker on GIS map"},
        {"id": "bhavani_mainstem", "path": "data/hydrology/bhavani_mainstem_downstream.gpkg", "milestone": "M2", "classification": "VECTOR_RIVER_NETWORK", "frontend_role": "Bhavani River vector overlay"},
        {"id": "reservoir_surface", "path": "data/hydrology/reservoir_surface.gpkg", "milestone": "M2", "classification": "VECTOR_RESERVOIR_POLYGON", "frontend_role": "Bhavanisagar reservoir surface water"},
        {"id": "dem_terrain", "path": "data/terrain/dem_projected.tif", "milestone": "M1", "classification": "RASTER_DEM", "frontend_role": "SRTM 30m elevation context"},
        {"id": "hillshade_terrain", "path": "data/terrain/hillshade.tif", "milestone": "M1", "classification": "RASTER_HILLSHADE", "frontend_role": "3D Topographic hillshade basemap"},

        # M4 Inflow Hydrograph
        {"id": "inflow_hydrograph", "path": "data/dflowfm/hydrographs/BHV_BASE.csv", "milestone": "M4", "classification": "HYDROGRAPH_TIME_SERIES", "frontend_role": "Dam breach hydrograph chart"},

        # M5 2D Hydraulic Simulation
        {"id": "dflow_map_nc", "path": "outputs/simulations/dflowfm/BHV_BASE/Bhavanisagar_DamBreak_map.nc", "milestone": "M5", "classification": "SIMULATION_2D_MAP_NETCDF", "frontend_role": "Source for 181 solver animation frames"},
        {"id": "dflow_his_nc", "path": "outputs/simulations/dflowfm/BHV_BASE/Bhavanisagar_DamBreak_his.nc", "milestone": "M5", "classification": "SIMULATION_2D_HISTORY_NETCDF", "frontend_role": "History time series stations"},
        {"id": "max_depth_raster", "path": "outputs/simulations/dflowfm/BHV_BASE/max_water_depth.tif", "milestone": "M5", "classification": "SIMULATION_MAX_DEPTH", "frontend_role": "Maximum water depth raster layer and point query"},
        {"id": "max_velocity_raster", "path": "outputs/simulations/dflowfm/BHV_BASE/max_velocity.tif", "milestone": "M5", "classification": "SIMULATION_MAX_VELOCITY", "frontend_role": "Maximum flow velocity raster layer and point query"},
        {"id": "arrival_time_raster", "path": "outputs/simulations/dflowfm/BHV_BASE/arrival_time.tif", "milestone": "M5", "classification": "SIMULATION_ARRIVAL_TIME", "frontend_role": "Flood wave arrival time raster layer and point query"},
        {"id": "inundation_extent_vector", "path": "outputs/simulations/dflowfm/BHV_BASE/inundation_extent.gpkg", "milestone": "M5", "classification": "SIMULATION_INUNDATION_EXTENT", "frontend_role": "Maximum flood envelope polygon"},
        {"id": "observation_hydrographs_csv", "path": "outputs/simulations/dflowfm/BHV_BASE/observation_hydrographs.csv", "milestone": "M5", "classification": "SIMULATION_STATION_HYDROGRAPHS", "frontend_role": "Station hydrograph points"},

        # M6 SPH Near-Field
        {"id": "sph_gauges_csv", "path": "outputs/simulations/sph/BHV_BASE_NEARFIELD/gauge_results.csv", "milestone": "M6", "classification": "SPH_NUMERICAL_GAUGES", "frontend_role": "Near-field numerical gauge table and inspector"},
        {"id": "sph_front_csv", "path": "outputs/simulations/sph/BHV_BASE_NEARFIELD/front_propagation.csv", "milestone": "M6", "classification": "SPH_FRONT_PROPAGATION", "frontend_role": "Near-field wave front advancement chart"},

        # M7 Cross-Solver
        {"id": "depth_comparison_csv", "path": "outputs/comparison/depth_comparison.csv", "milestone": "M7", "classification": "CROSS_SOLVER_COMPARISON", "frontend_role": "D-Flow vs SPH water depth comparison chart"},
        {"id": "velocity_comparison_csv", "path": "outputs/comparison/velocity_comparison.csv", "milestone": "M7", "classification": "CROSS_SOLVER_COMPARISON", "frontend_role": "D-Flow vs SPH velocity comparison chart"},

        # M8 HADR Consequence & Exposure
        {"id": "hazard_severity_vector", "path": "outputs/hadr/hazard_severity.gpkg", "milestone": "M8", "classification": "HADR_HAZARD_SEVERITY_ZONES", "frontend_role": "CWC H1–H6 hazard polygons on map"},
        {"id": "hazard_class_raster", "path": "outputs/hadr/hazard_class.tif", "milestone": "M8", "classification": "HADR_HAZARD_CLASS_RASTER", "frontend_role": "Hazard class raster layer and point query"},
        {"id": "population_exposure_csv", "path": "outputs/hadr/population_exposure_by_hazard.csv", "milestone": "M8", "classification": "HADR_POPULATION_EXPOSURE", "frontend_role": "WorldPop & GHSL population exposure summary"},
        {"id": "building_exposure_vector", "path": "outputs/hadr/building_exposure.gpkg", "milestone": "M8", "classification": "HADR_BUILDING_EXPOSURE", "frontend_role": "Inundated building footprints with bbox query"},
        {"id": "road_exposure_vector", "path": "outputs/hadr/road_exposure.gpkg", "milestone": "M8", "classification": "HADR_ROAD_EXPOSURE", "frontend_role": "Inundated road network lines"},
        {"id": "critical_facilities_csv", "path": "outputs/hadr/critical_facility_exposure.csv", "milestone": "M8", "classification": "HADR_CRITICAL_FACILITIES", "frontend_role": "Exposed hospitals, schools, police, power stations"},
        {"id": "response_zones_vector", "path": "outputs/hadr/response_zones_exclusive.gpkg", "milestone": "M8", "classification": "HADR_RESPONSE_ZONES", "frontend_role": "Exclusive non-overlapping response sector polygons"},
        {"id": "hadr_priority_csv", "path": "outputs/hadr/hadr_priority_zones.csv", "milestone": "M8", "classification": "HADR_PRIORITY_RANKING", "frontend_role": "HADR priority sector ranking table"},
        {"id": "m8_exposure_summary_json", "path": "outputs/validation/m8_exposure_summary.json", "milestone": "M8", "classification": "HADR_EXPOSURE_SUMMARY", "frontend_role": "HADR summary statistics panel"},

        # M9 Earth Observation & Near-Real-Time
        {"id": "observed_flood_raster", "path": "data/gee/observed_new_flood.tif", "milestone": "M9", "classification": "SATELLITE_HISTORICAL_FLOOD_RASTER", "frontend_role": "Sentinel-1 historical flood raster overlay"},
        {"id": "observed_flood_vector", "path": "outputs/gee/observed_new_flood_extent.gpkg", "milestone": "M9", "classification": "SATELLITE_HISTORICAL_FLOOD_VECTOR", "frontend_role": "Sentinel-1 historical flood vector overlay"},
        {"id": "latest_water_vector", "path": "outputs/gee/latest/latest_candidate_flood.gpkg", "milestone": "M9", "classification": "SATELLITE_NRT_WATER_CHANGE", "frontend_role": "Latest Sentinel-1 water change anomaly vector"},
        {"id": "latest_monitoring_json", "path": "outputs/gee/latest/latest_monitoring_metadata.json", "milestone": "M9", "classification": "SATELLITE_NRT_METADATA", "frontend_role": "Latest satellite monitoring status and quality panel"},
        {"id": "m9_spatial_context_json", "path": "outputs/validation/m9_model_observation_spatial_context.json", "milestone": "M9", "classification": "SATELLITE_SPATIAL_CONTEXT", "frontend_role": "Model vs satellite spatial context comparison"}
    ]

    inventory_records = []
    missing_count = 0

    for item in raw_inventory:
        p = ROOT_DIR / item["path"]
        exists = p.exists()
        size = p.stat().st_size if exists else 0
        crs = "N/A"
        if exists:
            if p.suffix in [".gpkg", ".shp"]:
                try:
                    gdf = gpd.read_file(p, rows=1)
                    crs = str(gdf.crs)
                except Exception:
                    pass
            elif p.suffix in [".tif"]:
                try:
                    with rasterio.open(p) as src:
                        crs = str(src.crs)
                except Exception:
                    pass

        rec = {
            "id": item["id"],
            "path": item["path"],
            "exists": exists,
            "file_size_bytes": size,
            "crs": crs,
            "source_milestone": item["milestone"],
            "classification": item["classification"],
            "frontend_role": item["frontend_role"]
        }
        inventory_records.append(rec)
        status_str = "[OK]" if exists else "[MISSING]"
        print(f"  {status_str:9s} {item['milestone']:4s} | {item['id']:30s} | {size:10,d} bytes | {item['path']}")
        if not exists:
            missing_count += 1

    manifest = {
        "milestone": "M10",
        "manifest_type": "DASHBOARD_DATA_INVENTORY",
        "total_sources_inventoried": len(inventory_records),
        "available_sources_count": len(inventory_records) - missing_count,
        "missing_sources_count": missing_count,
        "inventory_status": "READY" if missing_count == 0 else "INCOMPLETE",
        "sources": inventory_records
    }

    out_json = VALIDATION_DIR / "m10_dashboard_data_inventory.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[OK] Saved data inventory: {out_json}")
    if missing_count > 0:
        raise FileNotFoundError(f"Missing {missing_count} required data layers for M10 dashboard!")
    return manifest


def build_optimized_vector_layers():
    print("\n" + "=" * 70)
    print("STEP 2: Building Optimized GeoJSON Vector Layers (EPSG:4326)")
    print("=" * 70)

    vector_tasks = [
        ("dam_point", ROOT_DIR / "data/processed/study_area/dam_point_projected.gpkg", OUTPUT_GEOJSON_DIR / "dam_point.geojson"),
        ("bhavani_river", ROOT_DIR / "data/hydrology/bhavani_mainstem_downstream.gpkg", OUTPUT_GEOJSON_DIR / "bhavani_river.geojson"),
        ("reservoir", ROOT_DIR / "data/hydrology/reservoir_surface.gpkg", OUTPUT_GEOJSON_DIR / "reservoir_surface.geojson"),
        ("inundation_extent", ROOT_DIR / "outputs/simulations/dflowfm/BHV_BASE/inundation_extent.gpkg", OUTPUT_GEOJSON_DIR / "inundation_extent.geojson"),
        ("hazard_severity", ROOT_DIR / "outputs/hadr/hazard_severity.gpkg", OUTPUT_GEOJSON_DIR / "hazard_severity.geojson"),
        ("response_zones", ROOT_DIR / "outputs/hadr/response_zones_exclusive.gpkg", OUTPUT_GEOJSON_DIR / "response_zones.geojson"),
        ("road_exposure", ROOT_DIR / "outputs/hadr/road_exposure.gpkg", OUTPUT_GEOJSON_DIR / "road_exposure.geojson"),
        ("historical_flood", ROOT_DIR / "outputs/gee/observed_new_flood_extent.gpkg", OUTPUT_GEOJSON_DIR / "historical_flood.geojson"),
        ("latest_water", ROOT_DIR / "outputs/gee/latest/latest_candidate_flood.gpkg", OUTPUT_GEOJSON_DIR / "latest_water_change.geojson"),
    ]

    for name, src_p, dst_p in vector_tasks:
        if src_p.exists():
            gdf = gpd.read_file(src_p)
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            # Save GeoJSON
            gdf.to_file(dst_p, driver="GeoJSON")
            print(f"  [EXPORTED] {name:20s} -> {dst_p.name} ({len(gdf)} features, {dst_p.stat().st_size:,} bytes)")

    # Critical facilities GeoJSON
    cf_csv = ROOT_DIR / "outputs/hadr/critical_facility_exposure.csv"
    if cf_csv.exists():
        df_cf = pd.read_csv(cf_csv)
        if "longitude" in df_cf.columns and "latitude" in df_cf.columns:
            gdf_cf = gpd.GeoDataFrame(
                df_cf,
                geometry=gpd.points_from_xy(df_cf["longitude"], df_cf["latitude"]),
                crs="EPSG:4326"
            )
        elif "x_utm" in df_cf.columns and "y_utm" in df_cf.columns:
            gdf_cf = gpd.GeoDataFrame(
                df_cf,
                geometry=gpd.points_from_xy(df_cf["x_utm"], df_cf["y_utm"]),
                crs="EPSG:32643"
            ).to_crs("EPSG:4326")
            gdf_cf["longitude"] = gdf_cf.geometry.x
            gdf_cf["latitude"] = gdf_cf.geometry.y
        else:
            gdf_cf = gpd.GeoDataFrame(df_cf)

        cf_dst = OUTPUT_GEOJSON_DIR / "critical_facilities.geojson"
        gdf_cf.to_file(cf_dst, driver="GeoJSON")
        print(f"  [EXPORTED] critical_facilities  -> {cf_dst.name} ({len(gdf_cf)} features)")

    # SPH 1.5 km reach centerline and numerical gauges
    sph_gauges_csv = ROOT_DIR / "outputs/simulations/sph/BHV_BASE_NEARFIELD/gauge_results.csv"
    if sph_gauges_csv.exists():
        df_g = pd.read_csv(sph_gauges_csv)
        gdf_g = gpd.GeoDataFrame(
            df_g,
            geometry=gpd.points_from_xy(df_g["longitude"], df_g["latitude"]),
            crs="EPSG:4326"
        )
        g_dst = OUTPUT_GEOJSON_DIR / "sph_gauges.geojson"
        gdf_g.to_file(g_dst, driver="GeoJSON")
        print(f"  [EXPORTED] sph_gauges          -> {g_dst.name} ({len(gdf_g)} features)")

        # Create 1.5 km reach line from gauge coordinates
        coords = list(zip(df_g["longitude"], df_g["latitude"]))
        line = LineString(coords)
        gdf_line = gpd.GeoDataFrame([{"name": "SPH 1.5 km Near-Field Domain Centerline", "geometry": line}], crs="EPSG:4326")
        reach_dst = OUTPUT_GEOJSON_DIR / "sph_reach.geojson"
        gdf_line.to_file(reach_dst, driver="GeoJSON")
        print(f"  [EXPORTED] sph_reach           -> {reach_dst.name}")


def build_raster_overlay_images():
    print("\n" + "=" * 70)
    print("STEP 3: Generating Georeferenced Transparent PNG Overlays")
    print("=" * 70)

    overlays_metadata = {}

    def get_wgs84_bounds(src):
        transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
        min_lon, min_lat = transformer.transform(src.bounds.left, src.bounds.bottom)
        max_lon, max_lat = transformer.transform(src.bounds.right, src.bounds.top)
        return [[round(min_lat, 6), round(min_lon, 6)], [round(max_lat, 6), round(max_lon, 6)]]

    # 1. Max Depth Overlay
    with rasterio.open(ROOT_DIR / "outputs/simulations/dflowfm/BHV_BASE/max_water_depth.tif") as src:
        d_arr = src.read(1)
        h, w = d_arr.shape
        bounds_d = get_wgs84_bounds(src)
        rgba_d = np.zeros((h, w, 4), dtype=np.uint8)
        mask = d_arr >= 0.05
        rgba_d[mask & (d_arr < 0.5)] = [160, 225, 255, 180]
        rgba_d[mask & (d_arr >= 0.5) & (d_arr < 1.0)] = [70, 190, 250, 200]
        rgba_d[mask & (d_arr >= 1.0) & (d_arr < 2.0)] = [0, 140, 235, 220]
        rgba_d[mask & (d_arr >= 2.0) & (d_arr < 5.0)] = [10, 80, 200, 235]
        rgba_d[mask & (d_arr >= 5.0) & (d_arr < 10.0)] = [75, 20, 160, 245]
        rgba_d[mask & (d_arr >= 10.0)] = [130, 0, 110, 255]

        Image.fromarray(rgba_d, mode="RGBA").save(OUTPUT_OVERLAYS_DIR / "max_depth.png", format="PNG")
        overlays_metadata["max_depth"] = {
            "file": "max_depth.png", "url": "/api/tiles/overlays/max_depth.png",
            "label": "Maximum Water Depth", "unit": "m", "bounds_wgs84": bounds_d, "max_val": round(float(np.nanmax(d_arr)), 2)
        }
        print(f"  [OVERLAY] max_depth.png generated (Max: {np.nanmax(d_arr):.2f} m)")

    # 2. Max Velocity Overlay
    with rasterio.open(ROOT_DIR / "outputs/simulations/dflowfm/BHV_BASE/max_velocity.tif") as src:
        v_arr = src.read(1)
        h, w = v_arr.shape
        bounds_v = get_wgs84_bounds(src)
        rgba_v = np.zeros((h, w, 4), dtype=np.uint8)
        mask = v_arr >= 0.1
        rgba_v[mask & (v_arr < 0.5)] = [255, 255, 180, 160]
        rgba_v[mask & (v_arr >= 0.5) & (v_arr < 1.0)] = [255, 220, 50, 190]
        rgba_v[mask & (v_arr >= 1.0) & (v_arr < 2.0)] = [255, 140, 0, 215]
        rgba_v[mask & (v_arr >= 2.0) & (v_arr < 4.0)] = [230, 40, 0, 235]
        rgba_v[mask & (v_arr >= 4.0)] = [140, 0, 60, 255]

        Image.fromarray(rgba_v, mode="RGBA").save(OUTPUT_OVERLAYS_DIR / "max_velocity.png", format="PNG")
        overlays_metadata["max_velocity"] = {
            "file": "max_velocity.png", "url": "/api/tiles/overlays/max_velocity.png",
            "label": "Maximum Flow Velocity", "unit": "m/s", "bounds_wgs84": bounds_v, "max_val": round(float(np.nanmax(v_arr)), 2)
        }
        print(f"  [OVERLAY] max_velocity.png generated (Max: {np.nanmax(v_arr):.2f} m/s)")

    # 3. Arrival Time Overlay
    with rasterio.open(ROOT_DIR / "outputs/simulations/dflowfm/BHV_BASE/arrival_time.tif") as src:
        arr_t = src.read(1)
        h, w = arr_t.shape
        bounds_t = get_wgs84_bounds(src)
        rgba_t = np.zeros((h, w, 4), dtype=np.uint8)
        t_hrs = arr_t / 3600.0 if np.nanmax(arr_t) > 100 else arr_t
        mask = (t_hrs > 0) & (t_hrs <= 30.0)
        rgba_t[mask & (t_hrs < 1.0)] = [230, 0, 0, 230]
        rgba_t[mask & (t_hrs >= 1.0) & (t_hrs < 3.0)] = [255, 110, 0, 210]
        rgba_t[mask & (t_hrs >= 3.0) & (t_hrs < 6.0)] = [255, 200, 0, 200]
        rgba_t[mask & (t_hrs >= 6.0) & (t_hrs < 12.0)] = [140, 200, 50, 190]
        rgba_t[mask & (t_hrs >= 12.0)] = [0, 160, 180, 180]

        Image.fromarray(rgba_t, mode="RGBA").save(OUTPUT_OVERLAYS_DIR / "arrival_time.png", format="PNG")
        overlays_metadata["arrival_time"] = {
            "file": "arrival_time.png", "url": "/api/tiles/overlays/arrival_time.png",
            "label": "Flood Wave Arrival Time", "unit": "hr", "bounds_wgs84": bounds_t, "max_val": round(float(np.nanmax(t_hrs)), 2)
        }
        print(f"  [OVERLAY] arrival_time.png generated (Range: 0 to {np.nanmax(t_hrs):.1f} hr)")

    # 4. Hazard Class Overlay (H1 to H6)
    with rasterio.open(ROOT_DIR / "outputs/hadr/hazard_class.tif") as src:
        hz_arr = src.read(1)
        h, w = hz_arr.shape
        bounds_hz = get_wgs84_bounds(src)
        rgba_hz = np.zeros((h, w, 4), dtype=np.uint8)
        rgba_hz[hz_arr == 1] = [255, 245, 100, 180]  # H1
        rgba_hz[hz_arr == 2] = [255, 190, 40, 200]   # H2
        rgba_hz[hz_arr == 3] = [255, 125, 0, 215]    # H3
        rgba_hz[hz_arr == 4] = [230, 30, 20, 230]    # H4
        rgba_hz[hz_arr == 5] = [170, 0, 30, 240]     # H5
        rgba_hz[hz_arr == 6] = [100, 0, 90, 255]     # H6

        Image.fromarray(rgba_hz, mode="RGBA").save(OUTPUT_OVERLAYS_DIR / "hazard_class.png", format="PNG")
        overlays_metadata["hazard_class"] = {
            "file": "hazard_class.png", "url": "/api/tiles/overlays/hazard_class.png",
            "label": "CWC H1–H6 Hazard Severity", "unit": "class", "bounds_wgs84": bounds_hz
        }
        print(f"  [OVERLAY] hazard_class.png generated")

    # 5. Historical Satellite Flood Anomaly Overlay
    with rasterio.open(ROOT_DIR / "data/gee/observed_new_flood.tif") as src:
        sat_arr = src.read(1)
        h, w = sat_arr.shape
        bounds_sat = get_wgs84_bounds(src)
        rgba_sat = np.zeros((h, w, 4), dtype=np.uint8)
        rgba_sat[sat_arr > 0] = [0, 220, 220, 220]
        Image.fromarray(rgba_sat, mode="RGBA").save(OUTPUT_OVERLAYS_DIR / "historical_flood.png", format="PNG")
        overlays_metadata["historical_flood"] = {
            "file": "historical_flood.png", "url": "/api/tiles/overlays/historical_flood.png",
            "label": "Sentinel-1 Historical Flood Anomaly (Aug 2019)", "unit": "binary", "bounds_wgs84": bounds_sat
        }
        print(f"  [OVERLAY] historical_flood.png generated")

    # 6. Hillshade Overlay
    hillshade_path = ROOT_DIR / "data/terrain/hillshade.tif"
    if hillshade_path.exists():
        with rasterio.open(hillshade_path) as src:
            hs_arr = src.read(1)
            h, w = hs_arr.shape
            bounds_hs = get_wgs84_bounds(src)
            rgba_hs = np.zeros((h, w, 4), dtype=np.uint8)
            # Render grayscale hillshade with transparency
            rgba_hs[:, :, 0] = hs_arr
            rgba_hs[:, :, 1] = hs_arr
            rgba_hs[:, :, 2] = hs_arr
            rgba_hs[:, :, 3] = 140  # 55% opacity for crisp map blending
            Image.fromarray(rgba_hs, mode="RGBA").save(OUTPUT_OVERLAYS_DIR / "hillshade.png", format="PNG")
            overlays_metadata["hillshade"] = {
                "file": "hillshade.png", "url": "/api/tiles/overlays/hillshade.png",
                "label": "SRTM 30m Topographic Hillshade", "unit": "grayscale", "bounds_wgs84": bounds_hs
            }
            print(f"  [OVERLAY] hillshade.png generated")

    # Overlays manifest
    overlays_manifest = {
        "milestone": "M10",
        "layers": overlays_metadata
    }

    with open(OUTPUT_OVERLAYS_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(overlays_manifest, f, indent=2)
    print(f"[OK] Saved overlay manifest: {OUTPUT_OVERLAYS_DIR / 'manifest.json'}")


def main():
    build_data_inventory()
    build_optimized_vector_layers()
    build_raster_overlay_images()
    print("\n" + "=" * 70)
    print(" >>> DASHBOARD ASSETS BUILD: COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
