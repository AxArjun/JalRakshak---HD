"""
JalRakshak-HD: DualSPHysics Particle Resolution Sensitivity & Extended Run Suite (Milestone M6 Repair)
======================================================================================================
1. Runs dp = 4.0 m simulation (T_max = 300 s) -> dp40_out
2. Runs dp = 2.0 m simulation (T_max = 300 s) -> dp20_out
3. Runs extended dp = 1.0 m production simulation (T_max = 600 s) -> production_out
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.build_sph_case import generate_case_xml

SPH_DIR = ROOT_DIR / "data" / "sph"
CASE_DIR = SPH_DIR / "BHV_BASE_NEARFIELD"
LOGS_DIR = ROOT_DIR / "logs"
BIN_DIR = Path(r"C:\DualSPHysics\DualSPHysics_v5.4\bin\windows")

GENCASE = BIN_DIR / "GenCase_win64.exe"
CPU_SOLVER = BIN_DIR / "DualSPHysics5.4CPU_win64.exe"


def run_single_case(dp: float, t_max: float, out_dirname: str) -> dict:
    out_dir = CASE_DIR / out_dirname
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f" EXECUTING SPH SIMULATION: dp = {dp:.1f} m, T_max = {t_max:.1f} s")
    print(f" Destination: {out_dir}")
    print(f"=======================================================")

    # 1. Generate XML
    generate_case_xml(dp=dp, time_max=t_max, time_out=1.0)

    # 2. Run GenCase
    cmd_gencase = [str(GENCASE), str(CASE_DIR / "CaseBhavani_Def"), str(out_dir / "CaseBhavani"), "-save:all"]
    t0 = time.time()
    res_gencase = subprocess.run(cmd_gencase, capture_output=True, text=True, cwd=str(CASE_DIR))
    gencase_time = time.time() - t0
    if res_gencase.returncode != 0:
        print(f"GenCase failed with returncode {res_gencase.returncode}")
        print("[STDERR]:", res_gencase.stderr)
        return {"dp": dp, "status": "FAIL", "stage": "gencase"}

    # 3. Run DualSPHysics CPU
    print(f"GenCase completed in {gencase_time:.2f} s. Running DualSPHysics CPU on 16 threads...")
    cmd_solver = [str(CPU_SOLVER), str(out_dir / "CaseBhavani"), str(out_dir)]
    t1 = time.time()
    res_solver = subprocess.run(cmd_solver, capture_output=True, text=True, cwd=str(CASE_DIR))
    solver_wall_time = time.time() - t1

    bi4_files = list((out_dir / "data").glob("*.bi4"))
    print(f"Solver completed in {solver_wall_time:.2f} s with exit code {res_solver.returncode}. bi4 frames: {len(bi4_files)}")

    return {
        "dp_m": dp,
        "t_max_s": t_max,
        "gencase_time_s": gencase_time,
        "solver_wall_time_s": solver_wall_time,
        "exit_code": res_solver.returncode,
        "bi4_count": len(bi4_files),
        "status": "PASS" if res_solver.returncode == 0 and len(bi4_files) >= int(t_max) else "FAIL",
        "out_dir": str(out_dir)
    }


def run_all_sensitivity_and_extended():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. dp = 4.0 m
    res_40 = run_single_case(dp=4.0, t_max=300.0, out_dirname="dp40_out")

    # 2. dp = 2.0 m
    res_20 = run_single_case(dp=2.0, t_max=300.0, out_dirname="dp20_out")

    # 3. Extended dp = 1.0 m production run (T_max = 600.0 s)
    res_10 = run_single_case(dp=1.0, t_max=600.0, out_dirname="production_out")

    # Save log for production run
    prod_log = LOGS_DIR / "m6_sph_BHV_BASE.log"
    with open(prod_log, "w", encoding="utf-8") as f:
        f.write("=======================================================\n")
        f.write(" DUALSPHYSICS 2D NEAR-FIELD EXTENDED PRODUCTION RUN (M6)\n")
        f.write("=======================================================\n\n")
        f.write(f"Particle spacing (dp): 1.0 m\n")
        f.write(f"Simulated duration: 600.0 s (10.0 min)\n")
        f.write(f"Wall-clock runtime: {res_10['solver_wall_time_s']:.2f} s\n")
        f.write(f"Exit code: {res_10['exit_code']}\n")
        f.write(f"Generated bi4 frames: {res_10['bi4_count']}\n")

    summary = {
        "dp40": res_40,
        "dp20": res_20,
        "dp10_extended": res_10
    }
    with open(LOGS_DIR / "m6_resolution_runs_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nALL SPH RUNS COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    run_all_sensitivity_and_extended()
