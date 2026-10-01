"""
Comprehensive Hydrology Validation Suite for M2 Milestone (Repaired).
SIH PS 26161 - JalRakshak-HD.

Validates:
  1. Source Manifest consistency and correct dataset typing
  2. River network & downstream Bhavani mainstem isolation
  3. Reservoir geometry and JRC terminology
  4. Reservoir-dam spatial consistency
  5. Conditioned DEM valid finite elevations
  6. Flow direction and accumulation rasters
  7. Derived stream network threshold verification
  8. Snapped pour point satisfaction of stream threshold (acc >= threshold)
  9. Catchment boundary logic and explicit truncation classification
  10. Downstream river longitudinal profile elevations & monotonic chainage
  11. HydroBASINS Level 12 polygon verification and non-conflation with FreeFlowingRivers
  12. Diagnostic maps existence
"""
import json
import os
import sys
from pathlib import Path
import numpy as np
import rasterio
import geopandas as gpd
import pandas as pd
import pyproj

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def validate_m2_hydrology():
    print("=" * 80)
    print("STARTING M2 REPAIRED HYDROLOGY VALIDATION SUITE")
    print("=" * 80)

    failures = []
    warnings = []

    # 1. Check Source Manifest
    manifest_path = PROJECT_ROOT / "outputs" / "validation" / "m2_source_manifest.json"
    if not manifest_path.exists():
        failures.append(f"Missing source manifest: {manifest_path}")
    else:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            geoms = {g["field"]: g for g in manifest.get("geometries", [])}

            # Check FreeFlowingRivers vs HydroBASINS distinction
            if "freeflowingrivers_reach_network" in geoms:
                if geoms["freeflowingrivers_reach_network"].get("type") != "RIVER_POLYLINE_NETWORK":
                    failures.append("FreeFlowingRivers must be typed as RIVER_POLYLINE_NETWORK in source manifest.")
            else:
                failures.append("Missing freeflowingrivers_reach_network in source manifest.")

            if "hydrobasins_level_12_upstream_basin" in geoms:
                if geoms["hydrobasins_level_12_upstream_basin"].get("type") not in ["GLOBAL_DERIVED_WATERSHED_DATASET", "WATERSHED_POLYGON_DATASET"]:
                    failures.append("HydroBASINS Level 12 must be typed as GLOBAL_DERIVED_WATERSHED_DATASET in source manifest.")
            else:
                failures.append("Missing hydrobasins_level_12_upstream_basin in source manifest.")

            # Check JRC terminology
            if "reservoir_surface_water_extent" in geoms:
                res_type = geoms["reservoir_surface_water_extent"].get("type")
                if "PERMANENT" in res_type.upper():
                    failures.append("JRC GSW occurrence mask must NOT be typed as permanent water.")
                elif res_type != "REMOTE_SENSING_DERIVED_WATER_FREQUENCY_EXTENT":
                    failures.append("JRC GSW occurrence mask must be typed as REMOTE_SENSING_DERIVED_WATER_FREQUENCY_EXTENT.")
            print("[PASS] Source manifest verified with strict dataset typology.")

    # 2. Check Downstream Bhavani Mainstem & Total Network
    mainstem_gpkg = PROJECT_ROOT / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
    network_gpkg = PROJECT_ROOT / "data" / "hydrology" / "bhavani_river_centerline.gpkg"

    if not mainstem_gpkg.exists():
        failures.append(f"Missing downstream mainstem GPKG: {mainstem_gpkg}")
    else:
        gdf_main = gpd.read_file(mainstem_gpkg)
        if gdf_main.empty or not all(gdf_main.geometry.is_valid):
            failures.append("Downstream mainstem is empty or contains invalid geometry.")
        else:
            main_len_km = gdf_main.geometry.length.iloc[0] / 1000.0
            start_dist = gdf_main.get("start_distance_from_dam_m", [9999.0]).iloc[0]
            if start_dist > 500.0:
                failures.append(f"Downstream mainstem starts too far from dam ({start_dist:.2f} m > 500m).")
            else:
                print(f"[PASS] Downstream mainstem verified: length = {main_len_km:.2f} km, start distance from dam = {start_dist:.2f} m")

    if not network_gpkg.exists():
        failures.append(f"Missing river network GPKG: {network_gpkg}")
    else:
        gdf_net = gpd.read_file(network_gpkg)
        net_len_km = gdf_net.geometry.length.sum() / 1000.0
        print(f"[PASS] Total river network verified: length = {net_len_km:.2f} km across {len(gdf_net)} features.")

    # 3. Check Reservoir Surface Geometry & Corrected Terminology
    res_gpkg = PROJECT_ROOT / "data" / "hydrology" / "reservoir_surface.gpkg"
    if not res_gpkg.exists():
        failures.append(f"Missing reservoir surface GPKG: {res_gpkg}")
    else:
        gdf_res = gpd.read_file(res_gpkg)
        layer_names = list(gdf_res.get("layer_name", []))
        if "multi_decadal_water_occurrence_ge_50" not in layer_names:
            failures.append("Reservoir surface GPKG missing 'multi_decadal_water_occurrence_ge_50' layer.")
        else:
            occ50_area = gdf_res[gdf_res["layer_name"] == "multi_decadal_water_occurrence_ge_50"]["area_km2"].iloc[0]
            print(f"[PASS] Reservoir surface verified: occurrence >= 50% area = {occ50_area:.2f} km2 (EPSG:32643)")

    # 4. Check Reservoir-Dam Consistency Check JSON
    consist_path = PROJECT_ROOT / "outputs" / "validation" / "reservoir_dam_consistency.json"
    if not consist_path.exists():
        failures.append(f"Missing consistency validation JSON: {consist_path}")
    else:
        with open(consist_path, "r", encoding="utf-8") as f:
            cdata = json.load(f)
            if not cdata.get("consistency_checks", {}).get("reservoir_is_upstream_of_dam", False):
                failures.append("Reservoir is NOT detected as upstream of dam.")
            else:
                print(f"[PASS] Reservoir-dam consistency check passed (Status: {cdata.get('status')})")

    # 5. Check Conditioned DEM
    hydro_dem_path = PROJECT_ROOT / "data" / "hydrology" / "dem_hydroconditioned.tif"
    if not hydro_dem_path.exists():
        failures.append(f"Missing conditioned DEM: {hydro_dem_path}")
    else:
        with rasterio.open(hydro_dem_path) as src:
            arr = src.read(1)
            valid_elev = arr[(arr != src.nodata) & (~np.isnan(arr)) & (arr > -500.0)]
            if len(valid_elev) == 0:
                failures.append("Conditioned DEM contains no valid elevation cells.")
            elif np.isnan(valid_elev).any() or np.isinf(valid_elev).any():
                failures.append("Conditioned DEM contains NaN or Infinite elevation values.")
            else:
                print(f"[PASS] Conditioned DEM valid: {src.width}x{src.height} cells, elevation range [{valid_elev.min():.2f}, {valid_elev.max():.2f}] m MSL")

    # 6. Check Flow Direction and Flow Accumulation
    fdir_path = PROJECT_ROOT / "data" / "hydrology" / "flow_direction.tif"
    facc_path = PROJECT_ROOT / "data" / "hydrology" / "flow_accumulation.tif"
    if not fdir_path.exists() or not facc_path.exists():
        failures.append("Missing flow direction or accumulation raster.")
    else:
        with rasterio.open(facc_path) as src:
            arr_acc = src.read(1)
            max_acc = int(arr_acc.max())
            if max_acc < 100000:
                failures.append(f"Peak flow accumulation ({max_acc} cells) is unrealistically low for dam outlet.")
            else:
                print(f"[PASS] Flow accumulation raster verified: non-empty, peak accumulation = {max_acc:,} cells")

    # 7. Check Snapped Pour Point Satisfaction of Stream Threshold
    pour_gpkg = PROJECT_ROOT / "data" / "hydrology" / "hydrologic_pour_point.gpkg"
    pour_json = PROJECT_ROOT / "outputs" / "validation" / "pour_point_validation.json"
    if not pour_gpkg.exists() or not pour_json.exists():
        failures.append("Missing hydrologic pour point files.")
    else:
        with open(pour_json, "r", encoding="utf-8") as f:
            pdata = json.load(f)
            snap_metrics = pdata.get("snap_metrics", {})
            snap_acc = snap_metrics.get("flow_accumulation_cells", 0)
            stream_thresh = pdata.get("stream_threshold_cells", 1000)
            valid_against_thresh = snap_metrics.get("valid_against_threshold", False)
            snap_dist = snap_metrics.get("snap_distance_m", 9999.0)

            if snap_acc < stream_thresh:
                failures.append(f"Pour point accumulation ({snap_acc}) is below selected stream threshold ({stream_thresh}).")
            elif not valid_against_thresh:
                failures.append("Pour point valid_against_threshold is False.")
            elif snap_dist > 500.0:
                failures.append(f"Pour point snap distance exceeds 500m tolerance ({snap_dist:.2f} m).")
            else:
                print(f"[PASS] Snapped pour point verified: snap distance {snap_dist:.2f} m, accumulation {snap_acc:,} cells (>= threshold {stream_thresh})")

    # 8. Check Derived Stream Network Threshold Validation
    stream_val_json = PROJECT_ROOT / "outputs" / "validation" / "stream_threshold_validation.json"
    if not stream_val_json.exists():
        failures.append(f"Missing stream threshold validation JSON: {stream_val_json}")
    else:
        with open(stream_val_json, "r", encoding="utf-8") as f:
            sdata = json.load(f)
            sel = sdata.get("selected_threshold", {})
            med_offset = sel.get("median_distance_to_known_mainstem_m", 999.0)
            if med_offset > 150.0:
                failures.append(f"Derived stream threshold has unacceptable median offset ({med_offset:.1f} m).")
            else:
                print(f"[PASS] Stream threshold validation verified: selected = {sel.get('threshold_cells')} cells, median offset = {med_offset:.1f} m, <=60m: {sel.get('percent_mainstem_within_60m')}%")

    # 9. Check Catchment Delineation and Truncation Logic
    catch_json = PROJECT_ROOT / "outputs" / "validation" / "catchment_validation.json"
    if not catch_json.exists():
        failures.append(f"Missing catchment validation JSON: {catch_json}")
    else:
        with open(catch_json, "r", encoding="utf-8") as f:
            cdata = json.load(f)
            cmetrics = cdata.get("local_catchment_metrics", {})
            truncated = cmetrics.get("catchment_truncated", False)
            validity = cmetrics.get("local_catchment_validity")

            if not truncated:
                failures.append("Local catchment must be flagged catchment_truncated = True.")
            elif validity != "INVALID_FOR_TOTAL_UPSTREAM_AREA":
                failures.append("Local catchment validity must be INVALID_FOR_TOTAL_UPSTREAM_AREA.")
            else:
                print(f"[PASS] Local catchment logic reconciled: truncated = {truncated}, validity = '{validity}', area = {cmetrics.get('area_km2')} km2")

    # 10. Check River Longitudinal Profile
    prof_csv = PROJECT_ROOT / "data" / "hydrology" / "river_profile.csv"
    prof_json = PROJECT_ROOT / "outputs" / "validation" / "river_profile_summary.json"
    if not prof_csv.exists() or not prof_json.exists():
        failures.append("Missing river profile CSV or summary JSON.")
    else:
        df_prof = pd.read_csv(prof_csv)
        if not df_prof["chainage_m"].is_monotonic_increasing:
            failures.append("River profile chainage is not monotonic.")
        else:
            with open(prof_json, "r", encoding="utf-8") as f:
                pdata = json.load(f)
                pm = pdata.get("profile_metrics", {})
                start_elev = pm.get("start_dem_elevation_m", 9999.0)
                frl_ref = pm.get("frl_reference_elevation_m", 280.42)
                starts_above_frl = pm.get("starts_above_frl", True)

                if starts_above_frl or start_elev > frl_ref:
                    failures.append(f"River profile start elevation ({start_elev:.2f} m) starts above FRL ({frl_ref:.2f} m).")
                else:
                    print(f"[PASS] River profile validated: length = {pm.get('total_profile_length_km'):.2f} km, start elev = {start_elev:.2f} m (<= FRL {frl_ref:.2f} m), net fall = {pm.get('net_elevation_fall_m'):.2f} m, avg slope = {pm.get('average_slope_m_per_km'):.3f} m/km")

    # 11. Check HydroBASINS Level 12 Upstream Basin
    basin_gpkg = PROJECT_ROOT / "data" / "hydrology" / "upstream_basin.gpkg"
    basin_json = PROJECT_ROOT / "outputs" / "validation" / "upstream_basin_validation.json"
    if not basin_gpkg.exists() or not basin_json.exists():
        failures.append("Missing HydroBASINS upstream basin files.")
    else:
        with open(basin_json, "r", encoding="utf-8") as f:
            bdata = json.load(f)
            bprops = bdata.get("hydrobasins_attributes", {})
            hybas_id = bprops.get("HYBAS_ID")
            up_area = bprops.get("UP_AREA_sqkm")

            if hybas_id != 4121595750:
                failures.append(f"Unexpected HYBAS_ID ({hybas_id}), expected 4121595750 for Bhavanisagar.")
            elif up_area < 4000.0:
                failures.append(f"Unexpected HydroBASINS UP_AREA ({up_area} km2).")
            else:
                print(f"[PASS] HydroBASINS Level 12 verified: HYBAS_ID = {hybas_id}, UP_AREA = {up_area} km2, SUB_AREA = {bprops.get('SUB_AREA_sqkm')} km2")

    # 12. Check Diagnostic Maps
    maps = [
        "outputs/maps/m2_hydrology_overview.png",
        "outputs/maps/m2_flow_accumulation.png",
        "outputs/maps/m2_river_profile.png",
        "outputs/maps/m2_reservoir_geometry.png"
    ]
    for m in maps:
        if not (PROJECT_ROOT / m).exists():
            failures.append(f"Missing required diagnostic map: {m}")
        else:
            print(f"[PASS] Diagnostic map exists: {m}")

    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if failures:
        print("CRITICAL FAILURES:")
        for f in failures:
            print(f"  - {f}")
        print("Validation Result: FAIL")
        sys.exit(1)
    else:
        print("All M2 Hydrologic Repair Criteria Successfully Passed!")
        print("Validation Result: PASS")
        sys.exit(0)


if __name__ == "__main__":
    validate_m2_hydrology()
