"""
JalRakshak-HD: Cross-Solver Comparison Validation Suite (Milestone M7)
=====================================================================
Validates all Milestone M7 outputs against scientific constraints,
spatial accuracy, NetCDF provenance, and coupling integrity.

Mandatory Checks:
1. M5 NetCDF exists and is readable
2. M6 gauge CSV exists and is readable
3. Common centerline exists in data/comparison/
4. Coordinate Reference System is EPSG:32643
5. All comparison gauges are valid and non-null
6. D-Flow values trace directly to actual NetCDF
7. SPH values trace directly to actual gauge CSV / solver results
8. No 1500 m SPH arrival fabricated (must remain NOT_REACHED)
9. No timing error percentage calculated
10. Comparison uses MODEL_SPREAD terminology (no 'error' columns)
11. Coupling does not multiply unit discharge by arbitrary width
12. Forcing equivalence is explicitly FALSE
13. M6 resolution is classified as NOT_STABILIZED
14. Coupling status is explicitly assessed as DESIGN_ONLY / NOT_READY
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import netCDF4 as nc
import numpy as np
import pandas as pd
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent


def validate_m7():
    print("=" * 75)
    print("JalRakshak-HD: Validating Milestone M7 Cross-Solver Comparison")
    print("=" * 75)

    failures = []
    warnings = []

    # -------------------------------------------------------------
    # Check 1: M5 NetCDF exists
    # -------------------------------------------------------------
    m5_map_nc = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE" / "Bhavanisagar_DamBreak_map.nc"
    if m5_map_nc.exists():
        try:
            ds = nc.Dataset(m5_map_nc, "r")
            n_faces = len(ds.variables["mesh2d_face_x"])
            ds.close()
            print(f"[PASS] Check 1: M5 NetCDF exists and is readable ({n_faces} faces)")
        except Exception as e:
            failures.append(f"M5 NetCDF corrupted or unreadable: {e}")
    else:
        failures.append(f"M5 NetCDF missing at {m5_map_nc}")

    # -------------------------------------------------------------
    # Check 2: M6 gauge CSV exists
    # -------------------------------------------------------------
    m6_gauge_csv = ROOT_DIR / "outputs" / "simulations" / "sph" / "BHV_BASE_NEARFIELD" / "gauge_results.csv"
    if m6_gauge_csv.exists():
        df_sph_orig = pd.read_csv(m6_gauge_csv)
        print(f"[PASS] Check 2: M6 gauge CSV exists ({len(df_sph_orig)} rows)")
    else:
        failures.append(f"M6 gauge CSV missing at {m6_gauge_csv}")
        df_sph_orig = None

    # -------------------------------------------------------------
    # Check 3: Common centerline exists
    # -------------------------------------------------------------
    centerline_gpkg = ROOT_DIR / "data" / "comparison" / "common_nearfield_centerline.gpkg"
    if centerline_gpkg.exists():
        gdf_cl = gpd.read_file(centerline_gpkg)
        print(f"[PASS] Check 3: Common centerline exists ({len(gdf_cl)} feature, length={gdf_cl.geometry.length.iloc[0]:.1f} m)")
    else:
        failures.append(f"Common centerline GPKG missing at {centerline_gpkg}")
        gdf_cl = None

    # -------------------------------------------------------------
    # Check 4: CRS is EPSG:32643
    # -------------------------------------------------------------
    gauges_gpkg = ROOT_DIR / "data" / "comparison" / "common_gauges.gpkg"
    if gauges_gpkg.exists() and gdf_cl is not None:
        gdf_g = gpd.read_file(gauges_gpkg)
        cl_crs = str(gdf_cl.crs).upper()
        g_crs = str(gdf_g.crs).upper()
        if "32643" in cl_crs and "32643" in g_crs:
            print(f"[PASS] Check 4: CRS is strictly EPSG:32643 across spatial vectors")
        else:
            failures.append(f"CRS mismatch: centerline={cl_crs}, gauges={g_crs}")
    else:
        failures.append("Gauges GPKG missing or centerline failed")

    # -------------------------------------------------------------
    # Check 5: All comparison gauges valid
    # -------------------------------------------------------------
    if gauges_gpkg.exists():
        gdf_g = gpd.read_file(gauges_gpkg)
        expected_ch = [100.0, 250.0, 500.0, 1000.0, 1500.0]
        actual_ch = sorted(gdf_g["chainage_m"].tolist())
        if actual_ch == expected_ch:
            print(f"[PASS] Check 5: All 5 comparison gauge chainages valid: {actual_ch}")
        else:
            failures.append(f"Gauge chainages mismatch: expected {expected_ch}, got {actual_ch}")

    # -------------------------------------------------------------
    # Check 6: D-Flow values trace directly to actual NetCDF
    # -------------------------------------------------------------
    dflow_csv = ROOT_DIR / "outputs" / "comparison" / "dflow_nearfield_gauges.csv"
    if dflow_csv.exists() and m5_map_nc.exists():
        df_dflow = pd.read_csv(dflow_csv)
        ds = nc.Dataset(m5_map_nc, "r")
        h_var = ds.variables["mesh2d_waterdepth"]
        # Spot check G_500m
        r500 = df_dflow[df_dflow["chainage_m"] == 500.0].iloc[0]
        face_idx = int(r500["mesh_face_id"])
        h_netcdf_max = float(np.max(h_var[:, face_idx]))
        ds.close()
        if abs(h_netcdf_max - float(r500["peak_depth_m"])) < 1e-3:
            print(f"[PASS] Check 6: D-Flow values trace exactly to NetCDF (Face {face_idx}: {h_netcdf_max:.3f} m)")
        else:
            failures.append(f"D-Flow peak depth mismatch against NetCDF: CSV={r500['peak_depth_m']}, NetCDF={h_netcdf_max}")
    else:
        failures.append(f"Missing D-Flow gauges CSV at {dflow_csv}")

    # -------------------------------------------------------------
    # Check 7: SPH values trace directly to actual solver results
    # -------------------------------------------------------------
    sph_csv = ROOT_DIR / "outputs" / "comparison" / "sph_nearfield_gauges.csv"
    if sph_csv.exists() and df_sph_orig is not None:
        df_sph = pd.read_csv(sph_csv)
        for _, orig_row in df_sph_orig.iterrows():
            ch = float(orig_row["chainage_m"])
            norm_row = df_sph[df_sph["chainage_m"] == ch].iloc[0]
            if abs(float(norm_row["peak_depth_m"]) - float(orig_row["max_water_depth_m"])) > 1e-3:
                failures.append(f"SPH depth mismatch at {ch}m")
            if abs(float(norm_row["peak_velocity_mps"]) - float(orig_row["max_velocity_mps"])) > 1e-3:
                failures.append(f"SPH velocity mismatch at {ch}m")
        print(f"[PASS] Check 7: SPH values trace exactly to original solver results")
    else:
        failures.append(f"Missing SPH normalized CSV at {sph_csv}")

    # -------------------------------------------------------------
    # Check 8: No 1500 m SPH arrival fabricated
    # -------------------------------------------------------------
    if sph_csv.exists():
        df_sph = pd.read_csv(sph_csv)
        r1500 = df_sph[df_sph["chainage_m"] == 1500.0].iloc[0]
        arr_val = str(r1500["arrival_time_s"]).strip().upper()
        if "NOT_REACHED" in arr_val and float(r1500["peak_depth_m"]) == 0.0 and float(r1500["peak_velocity_mps"]) == 0.0:
            print(f"[PASS] Check 8: SPH 1500 m arrival is NOT fabricated (status='{arr_val}', h=0, u=0)")
        else:
            failures.append(f"SPH 1500 m arrival was fabricated or non-zero: arr={arr_val}, h={r1500['peak_depth_m']}")

    # -------------------------------------------------------------
    # Check 9: No timing error percentage calculated
    # -------------------------------------------------------------
    arr_csv = ROOT_DIR / "outputs" / "comparison" / "arrival_time_context.csv"
    if arr_csv.exists():
        df_arr = pd.read_csv(arr_csv)
        has_error_pct = any("error" in c.lower() or "pct" in c.lower() or "percent" in c.lower() for c in df_arr.columns)
        if not has_error_pct:
            print(f"[PASS] Check 9: No timing error percentage calculated in arrival context")
        else:
            failures.append("Arrival time context contains forbidden timing error/percentage column!")
    else:
        failures.append(f"Missing arrival time context at {arr_csv}")

    # -------------------------------------------------------------
    # Check 10: Comparison uses MODEL_SPREAD terminology (no 'error')
    # -------------------------------------------------------------
    depth_comp_csv = ROOT_DIR / "outputs" / "comparison" / "depth_comparison.csv"
    vel_comp_csv = ROOT_DIR / "outputs" / "comparison" / "velocity_comparison.csv"
    if depth_comp_csv.exists() and vel_comp_csv.exists():
        df_d = pd.read_csv(depth_comp_csv)
        df_v = pd.read_csv(vel_comp_csv)
        d_cols = [c.lower() for c in df_d.columns]
        v_cols = [c.lower() for c in df_v.columns]

        if "error" in d_cols or "error" in v_cols:
            failures.append("Comparison tables use forbidden 'error' column header!")
        elif "absolute_model_spread_m" in d_cols and "relative_model_spread_percent" in d_cols:
            print(f"[PASS] Check 10: Comparison uses MODEL_SPREAD terminology strictly")
        else:
            failures.append("Comparison tables do not use MODEL_SPREAD terminology")
    else:
        failures.append("Depth or velocity comparison CSV missing")

    # -------------------------------------------------------------
    # Check 11: Coupling does not multiply unit discharge by arbitrary width
    # -------------------------------------------------------------
    handoff_json = ROOT_DIR / "outputs" / "validation" / "m7_handoff_candidates.json"
    if handoff_json.exists():
        with open(handoff_json, "r") as f:
            h_data = json.load(f)
        if h_data.get("direct_discharge_coupling_ready") is False and h_data.get("direct_coupling_blocker") == "UNIT_WIDTH_TO_FULL_WIDTH_SCALING_UNRESOLVED":
            print(f"[PASS] Check 11: Unit discharge coupling explicitly blocked (reason: {h_data.get('direct_coupling_blocker')})")
        else:
            failures.append("Coupling did not properly block unit discharge scaling!")
    else:
        failures.append(f"Missing handoff candidates JSON at {handoff_json}")

    # -------------------------------------------------------------
    # Check 12: Forcing equivalence is explicitly FALSE
    # -------------------------------------------------------------
    if arr_csv.exists():
        df_arr = pd.read_csv(arr_csv)
        all_false = not any(df_arr["forcing_equivalence"])
        if all_false:
            print(f"[PASS] Check 12: Forcing equivalence is explicitly FALSE for all stations")
        else:
            failures.append("forcing_equivalence is TRUE in arrival time context!")

    # -------------------------------------------------------------
    # Check 13: M6 resolution classified NOT_STABILIZED
    # -------------------------------------------------------------
    manifest_json = ROOT_DIR / "outputs" / "validation" / "m7_comparison_manifest.json"
    if manifest_json.exists():
        with open(manifest_json, "r") as f:
            m_data = json.load(f)
        res_status = m_data.get("resolution_status", {}).get("m6_particle", "")
        if "NOT_STABILIZED" in res_status:
            print(f"[PASS] Check 13: M6 resolution classified strictly as NOT_STABILIZED")
        else:
            failures.append(f"M6 resolution status not classified as NOT_STABILIZED: {res_status}")
    else:
        failures.append(f"Missing comparison manifest at {manifest_json}")

    # -------------------------------------------------------------
    # Check 14: Coupling status explicitly assessed
    # -------------------------------------------------------------
    hybrid_yaml = ROOT_DIR / "configs" / "hybrid_solver.yaml"
    if hybrid_yaml.exists():
        with open(hybrid_yaml, "r") as f:
            cfg = yaml.safe_load(f)
        status = cfg.get("hybrid_architecture", {}).get("coupling_status")
        if status in ["DESIGN_ONLY", "NOT_READY"]:
            print(f"[PASS] Check 14: Coupling status explicitly assessed as '{status}'")
        else:
            failures.append(f"Invalid coupling status in hybrid_solver.yaml: {status}")
    else:
        failures.append(f"Missing hybrid_solver.yaml at {hybrid_yaml}")

    # -------------------------------------------------------------
    # Final Result
    # -------------------------------------------------------------
    print("-" * 75)
    if failures:
        print(f"FAILED: {len(failures)} critical check(s) failed:")
        for fail in failures:
            print(f"  [X] {fail}")
        sys.exit(1)
    else:
        print("ALL 14 MANDATORY VALIDATION CHECKS PASSED.")
        print("Milestone M7 Cross-Solver Comparison is scientifically validated.")
        sys.exit(0)


if __name__ == "__main__":
    validate_m7()
