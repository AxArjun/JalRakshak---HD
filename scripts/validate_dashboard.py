"""
JalRakshak-HD: Milestone M10 Comprehensive Dashboard Validation Script
======================================================================
Validates all scientific dashboard metrics against locked M5–M9 outputs:
- M5 domain (818.37 km2), inundation (101.29 km2), depth (22.02 m), velocity (11.79 m/s)
- M6 particle counts (10982), depth (17.11 m), velocity (34.78 m/s), front (1280.41 m)
- M7 cross-solver audit (direct coupling = False, depth partially consistent, velocity divergent)
- M8 population (42428.1 / 84500.5), buildings (25652), H5/H6 (22472), roads (243.82 km), bridges (20)
- M9 historical scene (Sentinel-1A S1A_...041D, 1.1150 km2 vector), latest scene (orbit 4581)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
from backend.app.main import app

client = TestClient(app)

def run_validation():
    print("\n==================================================================")
    print("  JalRakshak-HD M10: Full Dashboard Scientific Validation")
    print("==================================================================\n")

    checks = []

    def check(desc, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        checks.append({"description": desc, "status": status, "detail": detail})
        print(f"  [{status}] {desc} {('-> ' + str(detail)) if detail else ''}")

    # 1. Manifest file check
    manifest_path = ROOT_DIR / "outputs" / "dashboard" / "final_dashboard_metrics.json"
    check("final_dashboard_metrics.json exists", manifest_path.exists(), f"{manifest_path.stat().st_size} bytes" if manifest_path.exists() else "")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # 2. M5 checks
    m5 = metrics.get("m5_dflowfm", {})
    check("M5 Domain == 818.37 km2", m5.get("model_domain_area_km2", {}).get("value") == 818.37)
    check("M5 Inundated Area == 101.29 km2", m5.get("max_inundated_area_km2", {}).get("value") == 101.29)
    check("M5 Solver Max Depth == 22.02 m", m5.get("solver_max_depth_m", {}).get("value") == 22.02)
    check("M5 Solver Max Velocity == 11.79 m/s", m5.get("solver_max_velocity_mps", {}).get("value") == 11.79)
    check("M5 Simulation Duration == 108000 s (30 hr)", m5.get("simulation_duration_s", {}).get("value") == 108000.0)

    # 3. M6 checks
    m6 = metrics.get("m6_dualsphysics", {})
    check("M6 Total Particles == 10982", m6.get("total_particles", {}).get("value") == 10982)
    check("M6 Fluid Particles == 6800", m6.get("initial_fluid_particles", {}).get("value") == 6800)
    check("M6 Boundary Particles == 4182", m6.get("boundary_particles", {}).get("value") == 4182)
    check("M6 Max Depth == 17.11 m", m6.get("max_depth_m", {}).get("value") == 17.11)
    check("M6 Max Velocity == 34.78 m/s", m6.get("max_velocity_mps", {}).get("value") == 34.78)
    check("M6 Front at 600s == 1280.41 m", m6.get("front_position_at_600s_m", {}).get("value") == 1280.41)
    check("M6 1500m status == NOT_REACHED_WITHIN_600_S", m6.get("station_1500m_status", {}).get("value") == "NOT_REACHED_WITHIN_600_S")

    # 4. M7 checks
    m7 = metrics.get("m7_cross_solver_analysis", {})
    check("M7 Depth Trend == PARTIALLY_CONSISTENT", m7.get("depth_trend", {}).get("value") == "PARTIALLY_CONSISTENT")
    check("M7 Velocity Trend == DIVERGENT_TREND", m7.get("velocity_trend", {}).get("value") == "DIVERGENT_TREND")
    check("M7 Recommended Handoff == 500 m", m7.get("recommended_future_handoff_candidate", {}).get("value") == "500 m")
    check("M7 Direct Coupling Ready == False", m7.get("direct_coupling_ready", {}).get("value") is False)

    # 5. M8 checks
    m8 = metrics.get("m8_hadr_consequences", {})
    check("M8 WorldPop == 42428.1", m8.get("worldpop_2020_exposed", {}).get("value") == 42428.1)
    check("M8 GHSL == 84500.5", m8.get("ghsl_2025_exposed", {}).get("value") == 84500.5)
    check("M8 Buildings == 25652", m8.get("buildings_exposed", {}).get("value") == 25652)
    check("M8 H5/H6 Buildings == 22472", m8.get("h5_h6_buildings_exposed", {}).get("value") == 22472)
    check("M8 Severe H3-H6 Area == 97.99 km2", m8.get("severe_hazard_h3_h6_area_km2", {}).get("value") == 97.99)
    check("M8 Extreme H5-H6 Area == 87.29 km2", m8.get("extreme_hazard_h5_h6_area_km2", {}).get("value") == 87.29)
    check("M8 Roads == 243.82 km", m8.get("roads_exposed_km", {}).get("value") == 243.82)
    check("M8 Bridges == 20", m8.get("bridges_screened", {}).get("value") == 20)
    check("M8 Critical Facilities == 13", m8.get("critical_facilities_exposed", {}).get("value") == 13)

    # 6. M9 checks
    m9 = metrics.get("m9_earth_observation", {})
    m9_hist = m9.get("historical_event", {})
    check("M9 Historical Platform == Sentinel-1A", m9_hist.get("platform") == "Sentinel-1A")
    check("M9 Historical Scene contains S1A", "S1A" in m9_hist.get("scene_id", ""))
    check("M9 Historical Vector Flood == 1.1150 km2", m9_hist.get("observed_new_flood_vector_km2") == 1.1150)
    m9_latest = m9.get("latest_scene", {})
    check("M9 Latest Platform == Sentinel-1D", m9_latest.get("platform") == "Sentinel-1D")
    check("M9 Latest Absolute Orbit == 4581", m9_latest.get("absolute_orbit") == 4581)

    # 7. Live API endpoint validation via TestClient
    r_sim = client.get("/api/simulation/meta").json()
    check("API /api/simulation/meta matches domain 818.37", r_sim.get("domain_area_km2") == 818.37)
    check("API /api/simulation/meta matches depth 22.02", r_sim.get("solver_max_depth_m") == 22.02)
    
    r_hadr = client.get("/api/hadr/summary").json()
    check("API /api/hadr/summary matches WorldPop 42428.1", r_hadr.get("worldpop_exposed") == 42428.1)
    check("API /api/hadr/summary matches H5/H6 Buildings 22472", r_hadr.get("h5_h6_buildings_exposed") == 22472)
    check("API /api/hadr/summary matches Bridges 20", r_hadr.get("bridges_exposed_count") == 20)

    r_sph = client.get("/api/sph/summary").json()
    check("API /api/sph/summary matches total particles 10982", r_sph.get("total_particles") == 10982)
    check("API /api/sph/summary matches max depth 17.11", r_sph.get("max_depth_m") == 17.11)

    r_eo = client.get("/api/remote-sensing/summary").json()
    check("API /api/remote-sensing/summary matches S1A platform", r_eo.get("historical_platform") == "Sentinel-1A")
    check("API /api/remote-sensing/summary matches latest orbit 4581", r_eo.get("latest_scene", {}).get("absolute_orbit") == 4581)

    # Summary
    passed = sum(1 for c in checks if c["status"] == "PASS")
    total = len(checks)
    print(f"\n==================================================================")
    print(f"  Validation Summary: {passed}/{total} Checks Passed ({passed/total*100:.1f}%)")
    print(f"==================================================================\n")

    return passed == total

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
