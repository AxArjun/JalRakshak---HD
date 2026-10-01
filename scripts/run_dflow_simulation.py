"""
JalRakshak-HD: D-Flow FM Simulation Runner (Milestone M5)
=========================================================
Manages smoke testing and full production execution of the 2D hydrodynamic simulation
using the validated Delft3D FM / DIMR toolchain.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import netCDF4 as nc
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "data" / "dflowfm" / "model"
OUTPUT_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
LOGS_DIR = ROOT_DIR / "logs"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"

RUN_DIMR_BAT = r"C:\Program Files\Deltares\Delft3D FM Suite 2026.02 OpenHMWQ\plugins\DeltaShell.Dimr\kernels\x64\bin\run_dimr.bat"


def run_smoke_test() -> bool:
    print("=" * 80)
    print(" JALRAKSHAK-HD: D-FLOW FM SHORT SMOKE TEST (15 SIMULATED MINUTES)")
    print("=" * 80)

    # 1. Create temporary smoke test directory
    smoke_dir = ROOT_DIR / "scratch" / "dflow_smoke"
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)
    smoke_dir.mkdir(parents=True, exist_ok=True)

    # Copy model files to smoke dir
    for f in MODEL_DIR.glob("*"):
        if f.is_file():
            shutil.copy(f, smoke_dir / f.name)

    # Modify MDU for smoke test: Tstop = 900 s (15 min), MapInterval = 180 s (3 min)
    smoke_mdu = smoke_dir / "Bhavanisagar_DamBreak.mdu"
    with open(smoke_mdu, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("Tstop = 108000.0", "Tstop = 900.0")
    content = content.replace("MapInterval = 600.0", "MapInterval = 180.0")
    content = content.replace("HisInterval = 120.0", "HisInterval = 60.0")

    with open(smoke_mdu, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Executing D-Flow FM smoke test in: {smoke_dir} ...")
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "8"

    t0 = time.time()
    proc = subprocess.run(
        f'call "{RUN_DIMR_BAT}" dimr_config.xml',
        cwd=smoke_dir,
        shell=True,
        capture_output=True,
        text=True,
        env=env
    )
    wall_time = time.time() - t0

    print(f"Smoke test exit code: {proc.returncode} (Wall time: {wall_time:.2f} s)")

    # Save smoke log
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOGS_DIR / "m5_dflowfm_smoke_test.log", "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n" + proc.stdout + "\n=== STDERR ===\n" + proc.stderr)

    if proc.returncode != 0:
        print("[FAIL] Smoke test process exited with error!")
        print(proc.stderr[:1000])
        return False

    # Check that output NetCDF files exist and have valid hydraulic data
    output_sub = smoke_dir / "DFM_OUTPUT_Bhavanisagar_DamBreak"
    map_file = output_sub / "Bhavanisagar_DamBreak_map.nc"
    his_file = output_sub / "Bhavanisagar_DamBreak_his.nc"

    if not map_file.exists():
        print(f"[FAIL] Missing smoke test map output: {map_file}")
        return False

    ds_map = nc.Dataset(map_file, "r")
    times = ds_map.variables["time"][:]
    depths = ds_map.variables["mesh2d_waterdepth"][:]
    max_depth = np.max(depths)
    has_nan = np.isnan(depths).any()
    ds_map.close()

    print(f"Smoke test NetCDF verified:")
    print(f"  Simulated times: {times} s")
    print(f"  Max water depth: {max_depth:.3f} m")
    print(f"  NaN count:       {0 if not has_nan else 'PRESENT'}")

    smoke_ok = (len(times) > 1) and (max_depth > 0.0) and (not has_nan)
    if smoke_ok:
        print("[PASS] D-Flow FM short smoke test passed 100% of physical and numerical criteria.")
    else:
        print("[FAIL] Smoke test criteria not satisfied.")

    return smoke_ok


def run_full_simulation():
    print("=" * 80)
    print(" JALRAKSHAK-HD: D-FLOW FM FULL 30-HOUR PRODUCTION SIMULATION")
    print("=" * 80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Simulation Model Dir:   {MODEL_DIR}")
    print(f"Output Destination:     {OUTPUT_DIR}")
    print(f"Target Duration:        30.0 hours (108,000 s)")
    print(f"OpenMP Thread Count:    8 threads")

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "8"

    t_start = time.time()
    log_file_path = LOGS_DIR / "m5_dflowfm_BHV_BASE.log"

    print("Launching D-Flow FM via DIMR ...")
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            f'call "{RUN_DIMR_BAT}" dimr_config.xml',
            cwd=MODEL_DIR,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )

        for line in proc.stdout:
            sys.stdout.write(line)
            log_file.write(line)
            log_file.flush()

        proc.wait()

    wall_time = time.time() - t_start
    print("=" * 80)
    print(f"D-Flow FM Simulation Finished. Exit Code: {proc.returncode} | Wall Time: {wall_time:.2f} s ({wall_time/60:.2f} min)")
    print("=" * 80)

    if proc.returncode != 0:
        print("[ERROR] Simulation run exited with non-zero code!")
        return False

    # Copy output files from DFM_OUTPUT_Bhavanisagar_DamBreak to OUTPUT_DIR
    dfm_output_dir = MODEL_DIR / "DFM_OUTPUT_Bhavanisagar_DamBreak"
    if dfm_output_dir.exists():
        for item in dfm_output_dir.glob("*"):
            shutil.copy(item, OUTPUT_DIR / item.name)
        print(f"[OK] Copied solver outputs to: {OUTPUT_DIR}")

    return True


if __name__ == "__main__":
    smoke_success = run_smoke_test()
    if not smoke_success:
        print("[ERROR] Smoke test failed. Full simulation aborted.")
        sys.exit(1)

    full_success = run_full_simulation()
    sys.exit(0 if full_success else 1)
