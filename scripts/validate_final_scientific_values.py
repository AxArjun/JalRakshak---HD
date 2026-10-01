"""
Final Scientific Numerical Regression & Validation Script (M12).
Verifies all locked scientific metrics across Bhavanisagar and Hirakud against final truth manifests.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_scientific_validation():
    print("=" * 68)
    print("  JalRakshak-HD: M12 Final Scientific Numerical Regression")
    print("=" * 68)

    truth_file = PROJECT_ROOT / "outputs" / "validation" / "final_scientific_truth_manifest.json"
    if not truth_file.is_file():
        print("[FAIL] final_scientific_truth_manifest.json not found!")
        return False

    with open(truth_file, "r", encoding="utf-8") as f:
        truth = json.load(f)

    bhv = truth.get("bhavanisagar", {})
    hrk = truth.get("hirakud", {})

    checks = []

    # 1. Breach Parameters (M3)
    b_params = bhv.get("breach_scenario_bhv_base", {})
    checks.append(("Breach average width == 219.28 m", abs(b_params.get("average_breach_width_b_avg_m", 0) - 219.28) < 0.01))
    checks.append(("Breach formation time == 14095.59 s", abs(b_params.get("breach_formation_time_tf_seconds", 0) - 14095.59) < 0.1))
    checks.append(("Peak discharge Qpeak == 18742.38 m3/s", abs(b_params.get("peak_breach_discharge_qpeak_m3s", 0) - 18742.38) < 0.1))
    checks.append(("Hydrograph volume == 780.50 MCM", abs(b_params.get("hydrograph_volume_mcm", 0) - 780.50) < 0.1))

    # 2. D-Flow 2D Hydrodynamics (M5)
    dflow = bhv.get("dflow_fm_simulation", {})
    checks.append(("D-Flow computational domain == 818.37 km2", abs(dflow.get("computational_domain_area_km2", 0) - 818.37) < 0.01))
    checks.append(("D-Flow maximum inundated area == 101.29 km2", abs(dflow.get("maximum_inundated_area_km2", 0) - 101.29) < 0.01))
    checks.append(("D-Flow solver max depth == 22.02 m", abs(dflow.get("solver_maximum_depth_m", 0) - 22.02) < 0.01))
    checks.append(("D-Flow P95 depth == 12.72 m", abs(dflow.get("p95_water_depth_m", 0) - 12.72) < 0.01))
    checks.append(("D-Flow solver max velocity == 11.79 m/s", abs(dflow.get("solver_maximum_velocity_mps", 0) - 11.79) < 0.01))
    checks.append(("D-Flow P95 velocity == 4.27 m/s", abs(dflow.get("p95_flow_velocity_mps", 0) - 4.27) < 0.01))
    checks.append(("D-Flow simulation duration == 108000 s (30 hr)", dflow.get("simulation_duration_seconds") == 108000))
    checks.append(("D-Flow frame count == 181 frames", dflow.get("solver_frame_count") == 181))
    checks.append(("D-Flow mass conservation error < 0.01%", dflow.get("mass_balance", {}).get("relative_error_pct", 1.0) < 0.01))

    # 3. DualSPHysics Near-Field (M6)
    sph = bhv.get("dualsphysics_nearfield", {})
    checks.append(("SPH total particle count == 10982", sph.get("particle_count_total") == 10982))
    checks.append(("SPH physical simulation duration == 600 s", sph.get("simulation_physical_time_s") == 600.0))
    checks.append(("SPH solver max depth == 17.11 m", abs(sph.get("solver_maximum_depth_m", 0) - 17.11) < 0.01))
    checks.append(("SPH solver max velocity == 34.78 m/s", abs(sph.get("solver_maximum_velocity_mps", 0) - 34.78) < 0.01))
    checks.append(("SPH front arrival at 600s == 1280.41 m", abs(sph.get("front_position_at_600s_m", 0) - 1280.41) < 0.01))

    # 4. HADR Consequence Exposure (M8)
    hadr = bhv.get("hadr_exposure", {})
    checks.append(("WorldPop exposed population == 42428.1", abs(hadr.get("worldpop_exposed_count", 0) - 42428.1) < 0.1))
    checks.append(("GHSL exposed population == 84500.5", abs(hadr.get("ghsl_exposed_count", 0) - 84500.5) < 0.1))
    checks.append(("Total buildings inundated == 25652", hadr.get("buildings_inundated_total") == 25652))
    checks.append(("H5/H6 severe damage buildings == 22472", hadr.get("h5_h6_severe_damage_buildings") == 22472))
    checks.append(("Severe hazard H3-H6 area == 97.99 km2", abs(hadr.get("severe_hazard_h3_h6_area_km2", 0) - 97.99) < 0.01))
    checks.append(("Exposed road network == 243.82 km", abs(hadr.get("roads_exposed_total_km", 0) - 243.82) < 0.01))
    checks.append(("Screened bridge crossings == 20", hadr.get("screened_bridge_crossings_count") == 20))
    checks.append(("Critical healthcare facilities == 13", hadr.get("critical_facilities_count") == 13))

    # 5. Earth Observation Sentinel-1 (M9)
    eo = bhv.get("earth_observation", {})
    checks.append(("Historical Sentinel-1A scene verified (041D)", "041D" in eo.get("historical_scene_id", "")))
    checks.append(("Historical vector flood area == 1.1150 km2", abs(eo.get("historical_vector_flood_area_km2", 0) - 1.1150) < 0.001))
    checks.append(("Latest Sentinel-1 scene absolute orbit == 4581", eo.get("latest_absolute_orbit") == 4581))
    checks.append(("Latest Sentinel-1 scene relative orbit == 165", eo.get("latest_relative_orbit") == 165))

    # 6. Hirakud Second-Site Portability (M11)
    checks.append(("Hirakud dam model coordinate == 21.5286°N, 83.8742°E", hrk.get("location", {}).get("dam_model_coordinate", {}).get("lat") == 21.5286))
    checks.append(("Hirakud derived CRS == EPSG:32644 (UTM Zone 44N)", hrk.get("location", {}).get("derived_crs") == "EPSG:32644 (UTM Zone 44N)"))
    checks.append(("Hirakud D-Flow execution state == INPUT_READY_NOT_EXECUTED", hrk.get("workflow_execution_gates", {}).get("production_dflow_fm") == "INPUT_READY_NOT_EXECUTED"))

    # Print summary
    passed = 0
    for label, status in checks:
        mark = "[PASS]" if status else "[FAIL]"
        print(f"  {mark} {label}")
        if status:
            passed += 1

    total = len(checks)
    pct = (passed / total) * 100.0
    print("-" * 68)
    print(f"  Scientific Validation: {passed}/{total} Checks Passed ({pct:.1f}%)")
    print("=" * 68)
    return passed == total

if __name__ == "__main__":
    success = run_scientific_validation()
    exit(0 if success else 1)
