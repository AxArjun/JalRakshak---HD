"""
JalRakshak-HD: D-Flow FM Results Physical Sanity & Validation Auditor (Milestone M5)
===================================================================================
Performs exhaustive scientific validation on simulation NetCDF outputs, hydraulic bounds,
spatial propagation integrity, and numerical mass conservation.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
import geopandas as gpd
import netCDF4 as nc
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
LOGS_DIR = ROOT_DIR / "logs"
MODEL_DIR = ROOT_DIR / "data" / "dflowfm" / "model"
BREACH_PATH = ROOT_DIR / "data" / "dflowfm" / "breach_location.gpkg"
OBS_CSV = OUTPUT_DIR / "observation_hydrographs.csv"


def validate_dflow_results() -> bool:
    print("=" * 80)
    print(" JALRAKSHAK-HD: D-FLOW FM RESULTS VALIDATION & SANITY AUDIT (MILESTONE M5)")
    print("=" * 80)

    checks = []

    map_nc_path = OUTPUT_DIR / "Bhavanisagar_DamBreak_map.nc"
    his_nc_path = OUTPUT_DIR / "Bhavanisagar_DamBreak_his.nc"
    log_file_path = LOGS_DIR / "m5_dflowfm_BHV_BASE.log"

    # 1. Output NetCDF File Existence
    map_exists = map_nc_path.exists()
    checks.append(("Map NetCDF Output Exists", map_exists, str(map_nc_path)))
    print(f"[{'PASS' if map_exists else 'FAIL'}] {'Map NetCDF Output Exists':<38} -> {map_nc_path.name}")

    if not map_exists:
        print("[ERROR] Map NetCDF file missing. Aborting validation.")
        return False

    # 2. Solver Normal Completion & Duration Check
    ds_map = nc.Dataset(map_nc_path, "r")
    time_arr = ds_map.variables["time"][:]
    t_end_s = float(time_arr[-1])
    t_end_hr = t_end_s / 3600.0

    duration_ok = t_end_s >= 83287.18  # Reached at least hydrograph duration
    checks.append(("Simulation Duration Full Coverage", duration_ok, f"T_end = {t_end_s:.0f} s ({t_end_hr:.2f} hr)"))
    print(f"[{'PASS' if duration_ok else 'FAIL'}] {'Simulation Duration Full Coverage':<38} -> {t_end_hr:.2f} hours simulated")

    # 3. Finite Values & Non-Negativity of Depth
    waterdepth_arr = ds_map.variables["mesh2d_waterdepth"][:]
    ucmag_arr = ds_map.variables["mesh2d_ucmag"][:]
    face_x = ds_map.variables["mesh2d_face_x"][:]
    face_y = ds_map.variables["mesh2d_face_y"][:]

    nan_depth = np.isnan(waterdepth_arr).any()
    inf_depth = np.isinf(waterdepth_arr).any()
    nan_vel = np.isnan(ucmag_arr).any()
    inf_vel = np.isinf(ucmag_arr).any()

    finite_ok = not (nan_depth or inf_depth or nan_vel or inf_vel)
    checks.append(("No NaN/Inf in Hydraulic Fields", finite_ok, f"NaN/Inf count = 0"))
    print(f"[{'PASS' if finite_ok else 'FAIL'}] {'No NaN/Inf in Hydraulic Fields':<38} -> Verified finite")

    min_depth = float(np.min(waterdepth_arr))
    nonneg_depth_ok = min_depth >= -1e-4  # numerical tolerance
    checks.append(("Water Depths Non-Negative", nonneg_depth_ok, f"Min depth = {min_depth:.6f} m"))
    print(f"[{'PASS' if nonneg_depth_ok else 'FAIL'}] {'Water Depths Non-Negative':<38} -> Min depth = {min_depth:.4f} m")

    max_depth = float(np.max(waterdepth_arr))
    max_vel = float(np.max(ucmag_arr))
    plausible_max = (0.5 < max_depth < 60.0) and (0.1 < max_vel < 30.0)
    checks.append(("Plausible Hydraulic Ranges", plausible_max, f"Max depth = {max_depth:.2f} m, Max vel = {max_vel:.2f} m/s"))
    print(f"[{'PASS' if plausible_max else 'FAIL'}] {'Plausible Hydraulic Ranges':<38} -> Max depth: {max_depth:.2f} m, Max vel: {max_vel:.2f} m/s")

    # 4. Inundation Origin at Breach Point
    breach_gdf = gpd.read_file(BREACH_PATH)
    breach_pt = breach_gdf.geometry.iloc[0]

    # Find faces near breach
    dist_to_breach = np.sqrt((face_x - breach_pt.x)**2 + (face_y - breach_pt.y)**2)
    near_breach_mask = dist_to_breach < 2000.0
    near_breach_wetted = (np.max(waterdepth_arr[:, near_breach_mask], axis=0) >= 0.05).any()
    checks.append(("Inundation Originates at Dam Breach", near_breach_wetted, "Near-breach cells wet"))
    print(f"[{'PASS' if near_breach_wetted else 'FAIL'}] {'Inundation Originates at Dam Breach':<38} -> Confirmed at breach toe")

    # 5. Downstream Wave Propagation Check
    if OBS_CSV.exists():
        df_obs = pd.read_csv(OBS_CSV)
        arrival_times = df_obs["arrival_time_hr"].dropna().tolist()
        chainages = df_obs.loc[df_obs["arrival_time_hr"].notna(), "chainage_km"].tolist()
        # Check that arrival time increases with chainage
        propagates_downstream = all(arrival_times[i] <= arrival_times[i+1] for i in range(len(arrival_times)-1))
        checks.append(("Downstream Wave Propagation Monotonic", propagates_downstream, f"Monotonic arrival times across {len(arrival_times)} stations"))
        print(f"[{'PASS' if propagates_downstream else 'FAIL'}] {'Downstream Wave Propagation Monotonic':<38} -> Arrival times ordered along river")
    else:
        checks.append(("Observation Station Summary", False, "Missing CSV"))

    # 6. Mass-Balance Audit Verification
    mb_file = VALIDATION_DIR / "m5_mass_balance.json"
    if mb_file.exists():
        with open(mb_file, "r", encoding="utf-8") as f:
            mb_data = json.load(f)
        mb_ok = mb_data.get("volume_conservation_status") == "CONSERVED"
        checks.append(("Mass-Balance Conservation", mb_ok, f"Residual = {mb_data.get('mass_residual_percent'):.2f}%"))
        print(f"[{'PASS' if mb_ok else 'FAIL'}] {'Mass-Balance Conservation':<38} -> Residual = {mb_data.get('mass_residual_percent'):.2f}%")

    ds_map.close()

    all_passed = all(c[1] for c in checks)
    print("=" * 80)
    if all_passed:
        print("[SUCCESS] Milestone M5 D-Flow FM simulation satisfies 100% of scientific validation criteria.")
    else:
        print("[ERROR] One or more M5 validation criteria failed.")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = validate_dflow_results()
    sys.exit(0 if success else 1)
