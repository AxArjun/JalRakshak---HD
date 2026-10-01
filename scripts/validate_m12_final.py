import os
import sys
import json
import subprocess
from pathlib import Path

def run_check(name: str, command: list) -> bool:
    print(f"[*] Running check: {name}...")
    res = subprocess.run(command, capture_output=True, text=True, cwd="C:/JalRakshak-HD")
    if res.returncode == 0:
        print(f"    [PASS] {name}")
        return True
    else:
        print(f"    [FAIL] {name}")
        print(res.stdout)
        print(res.stderr)
        return False

def main():
    root = Path("C:/JalRakshak-HD")
    print("========================================================")
    print("  JalRakshak-HD: Master Milestone 12 Release Gate Validator")
    print("========================================================")
    
    checks = []
    
    # 1. Manifest existence
    required_files = [
        "VERSION",
        "README.md",
        "START_DEMO.bat",
        "start_jalrakshak.ps1",
        "docs/SIH_DEMO_SCRIPT.md",
        "docs/SIH_JURY_QA.md",
        "docs/final_architecture.md",
        "docs/final_data_lineage.md",
        "docs/final_project_structure.md",
        "outputs/reports/final_benchmark_table.md",
        "outputs/reports/final_ps_compliance.md",
        "outputs/reports/final_differentiators.md",
        "outputs/reports/JalRakshak_HD_Final_Technical_Report.md",
        "outputs/validation/final_scientific_truth_manifest.json",
        "outputs/validation/m12_release_manifest.json",
        "outputs/validation/m12_validation_matrix.csv",
        "outputs/validation/m12_source_traceability.csv",
        "outputs/validation/m12_claim_audit.json",
        "outputs/validation/m12_gis_alignment.json",
        "outputs/validation/m12_offline_demo_validation.json",
        "outputs/validation/m12_storage_manifest.json",
        "outputs/validation/m12_secret_audit.json",
        "outputs/validation/m12_no_fake_final.json",
        "outputs/validation/m12_performance.json",
        "demo_package/README_DEMO.md"
    ]
    
    manifests_ok = True
    for f in required_files:
        p = root / f
        if not p.exists():
            print(f"    [MISSING] {f}")
            manifests_ok = False
            
    if manifests_ok:
        print("    [PASS] All Required Release Files and Manifests Present")
    checks.append(manifests_ok)
    
    # 2. Run Preflight
    checks.append(run_check("Preflight Demo Check", [sys.executable, "scripts/preflight_demo.py"]))
    
    # 3. Scientific Values Regression
    checks.append(run_check("Scientific Values Regression (33 Checks)", [sys.executable, "scripts/validate_final_scientific_values.py"]))
    
    # 4. Claim Audit
    checks.append(run_check("Final Scientific Claim Audit", [sys.executable, "scripts/audit_final_claims.py"]))
    
    # 5. Real Map Validation
    checks.append(run_check("Real GIS Map Validation", [sys.executable, "scripts/validate_real_map.py"]))
    
    # 6. Dashboard API Validation
    checks.append(run_check("Dashboard API Integration", [sys.executable, "scripts/validate_dashboard.py"]))
    
    # 7. M11 Generalization
    checks.append(run_check("M11 Multi-Site Portability", [sys.executable, "scripts/validate_m11_generalization.py"]))
    
    # 8. M5 Mass Conservation & Hydrograph checks
    with open(root / "outputs" / "validation" / "final_scientific_truth_manifest.json", "r", encoding="utf-8") as f:
        truth = json.load(f)
        
    bhv = truth.get("bhavanisagar", {})
    breach = bhv.get("breach_scenario_bhv_base", {})
    dflow = bhv.get("dflow_fm_simulation", {})
    mass_bal = dflow.get("mass_balance", {})
    
    mass_ok = (
        breach.get("hydrograph_volume_mcm") == 780.5 and
        mass_bal.get("status") == "MASS_CONSERVATION_PASS" and
        round(mass_bal.get("residual_error_mcm", 0), 3) == 0.041 and
        dflow.get("solver_frame_count") == 181
    )
    if mass_ok:
        print("    [PASS] Hydraulic Mass Balance & Hydrograph Integrity Verified")
    else:
        print("    [FAIL] Hydraulic Mass Balance Verification Failed")
    checks.append(mass_ok)
    
    # 9. Frame count
    frames = list((root / "outputs" / "dashboard" / "simulation_frames").glob("frame_*.png"))
    frames_ok = len(frames) == 181
    if frames_ok:
        print(f"    [PASS] 181 D-Flow PNG Frames Verified ({len(frames)} found)")
    else:
        print(f"    [FAIL] Expected 181 frames, found {len(frames)}")
    checks.append(frames_ok)
    
    print("========================================================")
    all_passed = all(checks)
    if all_passed:
        print("  ALL M12 FINAL RELEASE GATES PASSED (100.0%)")
        print("========================================================")
        return 0
    else:
        print("  SOME GATES FAILED")
        print("========================================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())
