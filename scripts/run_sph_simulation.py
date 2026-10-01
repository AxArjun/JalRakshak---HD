"""
JalRakshak-HD: Execute DualSPHysics 2D Near-Field Dam-Break Simulation (Milestone M6)
Tasks 14 & 15: Smoke Test and Full Near-Field Production Run
=====================================================================================
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
SPH_DIR = ROOT_DIR / "data" / "sph"
CASE_DIR = SPH_DIR / "BHV_BASE_NEARFIELD"
LOGS_DIR = ROOT_DIR / "logs"
BIN_DIR = Path(r"C:\DualSPHysics\DualSPHysics_v5.4\bin\windows")

GENCASE = BIN_DIR / "GenCase_win64.exe"
CPU_SOLVER = BIN_DIR / "DualSPHysics5.4CPU_win64.exe"


def run_smoke_test(dp: float = 1.0, t_max: float = 30.0, t_out: float = 1.0) -> bool:
    print("=" * 80)
    print(" JALRAKSHAK-HD: RUNNING SPH SMOKE TEST (M6 TASK 14)")
    print("=" * 80)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    smoke_log = LOGS_DIR / "m6_sph_smoke_test.log"

    # Setup XML for smoke test
    from scripts.build_sph_case import generate_case_xml
    generate_case_xml(dp=dp, time_max=t_max, time_out=t_out)

    smoke_out_dir = CASE_DIR / "smoke_out"
    if smoke_out_dir.exists():
        shutil.rmtree(smoke_out_dir, ignore_errors=True)
    smoke_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. GenCase
    print(f"Generating smoke test initial condition (dp={dp} m, t_max={t_max} s)...")
    cmd_gencase = [str(GENCASE), str(CASE_DIR / "CaseBhavani_Def"), str(smoke_out_dir / "CaseBhavani"), "-save:all"]
    t0 = time.time()
    res_gencase = subprocess.run(cmd_gencase, capture_output=True, text=True, cwd=str(CASE_DIR))
    gencase_time = time.time() - t0

    if res_gencase.returncode != 0:
        print(f"GenCase failed with returncode {res_gencase.returncode}")
        return False

    # 2. DualSPHysics CPU
    print(f"Launching DualSPHysics CPU solver for {t_max} simulated seconds...")
    cmd_solver = [str(CPU_SOLVER), str(smoke_out_dir / "CaseBhavani"), str(smoke_out_dir)]
    t1 = time.time()
    res_solver = subprocess.run(cmd_solver, capture_output=True, text=True, cwd=str(CASE_DIR))
    solver_wall_time = time.time() - t1

    with open(smoke_log, "w", encoding="utf-8") as f:
        f.write("=======================================================\n")
        f.write(" DUALSPHYSICS 2D NEAR-FIELD SMOKE TEST (TASK 14)\n")
        f.write("=======================================================\n\n")
        f.write("--- GENCASE EXECUTION ---\n")
        f.write(res_gencase.stdout + "\n")
        if res_gencase.stderr:
            f.write("[STDERR]: " + res_gencase.stderr + "\n")
        f.write(f"GenCase Exit Code: {res_gencase.returncode} (Elapsed: {gencase_time:.3f} s)\n\n")
        f.write("--- DUALSPHYSICS CPU SOLVER EXECUTION ---\n")
        f.write(res_solver.stdout + "\n")
        if res_solver.stderr:
            f.write("[STDERR]: " + res_solver.stderr + "\n")
        f.write(f"Solver Exit Code: {res_solver.returncode} (Wall-clock Time: {solver_wall_time:.3f} s)\n")

    print(f"Smoke test execution log written to: {smoke_log}")
    print(f"Solver Exit Code: {res_solver.returncode} in {solver_wall_time:.2f} s")

    # Check bi4 files generated
    bi4_files = list((smoke_out_dir / "data").glob("*.bi4"))
    print(f"Smoke test output bi4 frames: {len(bi4_files)}")

    if res_solver.returncode == 0 and len(bi4_files) >= int(t_max / t_out):
        print(">>> SPH SMOKE TEST STATUS: PASS\n")
        return True
    else:
        print(">>> SPH SMOKE TEST STATUS: FAIL\n")
        return False


def run_production_simulation(dp: float = 1.0, t_max: float = 300.0, t_out: float = 1.0) -> bool:
    print("=" * 80)
    print(" JALRAKSHAK-HD: RUNNING FULL SPH NEAR-FIELD SIMULATION (M6 TASK 15)")
    print("=" * 80)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    prod_log = LOGS_DIR / "m6_sph_BHV_BASE.log"

    from scripts.build_sph_case import generate_case_xml
    generate_case_xml(dp=dp, time_max=t_max, time_out=t_out)

    prod_out_dir = CASE_DIR / "production_out"
    if prod_out_dir.exists():
        shutil.rmtree(prod_out_dir, ignore_errors=True)
    prod_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. GenCase
    print(f"Generating production initial condition (dp={dp} m, t_max={t_max} s)...")
    cmd_gencase = [str(GENCASE), str(CASE_DIR / "CaseBhavani_Def"), str(prod_out_dir / "CaseBhavani"), "-save:all"]
    t0 = time.time()
    res_gencase = subprocess.run(cmd_gencase, capture_output=True, text=True, cwd=str(CASE_DIR))
    gencase_time = time.time() - t0

    if res_gencase.returncode != 0:
        print(f"GenCase failed with returncode {res_gencase.returncode}")
        return False

    # 2. DualSPHysics CPU Solver
    print(f"Executing DualSPHysics CPU for {t_max:.1f} s ({int(t_max/60):.0f} min) across 16 threads...")
    cmd_solver = [str(CPU_SOLVER), str(prod_out_dir / "CaseBhavani"), str(prod_out_dir)]
    t1 = time.time()
    res_solver = subprocess.run(cmd_solver, capture_output=True, text=True, cwd=str(CASE_DIR))
    solver_wall_time = time.time() - t1

    with open(prod_log, "w", encoding="utf-8") as f:
        f.write("=======================================================\n")
        f.write(" DUALSPHYSICS 2D NEAR-FIELD PRODUCTION RUN (TASK 15)\n")
        f.write("=======================================================\n\n")
        f.write("--- GENCASE EXECUTION ---\n")
        f.write(res_gencase.stdout + "\n")
        if res_gencase.stderr:
            f.write("[STDERR]: " + res_gencase.stderr + "\n")
        f.write(f"GenCase Exit Code: {res_gencase.returncode} (Elapsed: {gencase_time:.3f} s)\n\n")
        f.write("--- DUALSPHYSICS CPU SOLVER EXECUTION ---\n")
        f.write(res_solver.stdout + "\n")
        if res_solver.stderr:
            f.write("[STDERR]: " + res_solver.stderr + "\n")
        f.write(f"Solver Exit Code: {res_solver.returncode} (Wall-clock Time: {solver_wall_time:.3f} s)\n")

    print(f"Production run log written to: {prod_log}")
    print(f"DualSPHysics Exit Code: {res_solver.returncode} in {solver_wall_time:.2f} s")

    bi4_files = list((prod_out_dir / "data").glob("*.bi4"))
    print(f"Production output bi4 frames: {len(bi4_files)}")

    if res_solver.returncode == 0 and len(bi4_files) >= int(t_max / t_out):
        print(">>> SPH PRODUCTION RUN STATUS: SUCCESS\n")
        return True
    else:
        print(">>> SPH PRODUCTION RUN STATUS: FAIL\n")
        return False


if __name__ == "__main__":
    smoke_ok = run_smoke_test()
    if not smoke_ok:
        sys.exit(1)
    prod_ok = run_production_simulation()
    if not prod_ok:
        sys.exit(1)
