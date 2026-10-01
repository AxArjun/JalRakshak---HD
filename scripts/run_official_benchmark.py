"""
JalRakshak-HD: Task 2 - Re-run Official DualSPHysics 2D Dam-Break Baseline Benchmark
"""
import subprocess
import time
import sys
from pathlib import Path

def run_benchmark():
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "m6_official_dambreak_validation.log"

    bin_dir = Path(r"C:\DualSPHysics\DualSPHysics_v5.4\bin\windows")
    example_dir = Path(r"C:\DualSPHysics\DualSPHysics_v5.4\examples\main\01_DamBreak")
    out_dir = example_dir / "CaseDambreakVal2D_out"

    gencase = bin_dir / "GenCase_win64.exe"
    solver = bin_dir / "DualSPHysics5.4CPU_win64.exe"

    print("Running official GenCase 2D DamBreak benchmark...")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=======================================================\n")
        f.write(" DUALSPHYSICS OFFICIAL 2D DAM-BREAK BENCHMARK (TASK 2)\n")
        f.write("=======================================================\n\n")

        # 1. GenCase
        f.write("--- STEP 1: RUNNING GENCASE ---\n")
        cmd1 = [str(gencase), str(example_dir / "CaseDambreakVal2D_Def"), str(out_dir / "CaseDambreakVal2D"), "-save:all"]
        f.write(f"Command: {' '.join(cmd1)}\n\n")
        t0 = time.time()
        res1 = subprocess.run(cmd1, capture_output=True, text=True, cwd=str(example_dir))
        f.write(res1.stdout)
        if res1.stderr:
            f.write("\n[STDERR]:\n" + res1.stderr)
        f.write(f"\nGenCase Exit Code: {res1.returncode} (Elapsed: {time.time()-t0:.3f} s)\n\n")

        if res1.returncode != 0:
            print(f"GenCase failed with code {res1.returncode}")
            sys.exit(1)

        print("GenCase finished successfully. Running DualSPHysics CPU...")

        # 2. DualSPHysics CPU
        f.write("--- STEP 2: RUNNING DUALSPHYSICS CPU SOLVER ---\n")
        cmd2 = [str(solver), str(out_dir / "CaseDambreakVal2D"), str(out_dir)]
        f.write(f"Command: {' '.join(cmd2)}\n\n")
        t1 = time.time()
        res2 = subprocess.run(cmd2, capture_output=True, text=True, cwd=str(example_dir))
        f.write(res2.stdout)
        if res2.stderr:
            f.write("\n[STDERR]:\n" + res2.stderr)
        wall_time = time.time() - t1
        f.write(f"\nDualSPHysics Exit Code: {res2.returncode} (Wall-clock Time: {wall_time:.3f} s)\n\n")

        if res2.returncode != 0:
            print(f"DualSPHysics failed with code {res2.returncode}")
            sys.exit(1)

        print(f"Official 2D dam-break validation benchmark SUCCESS in {wall_time:.2f} s. Exit code: 0")

if __name__ == "__main__":
    run_benchmark()
