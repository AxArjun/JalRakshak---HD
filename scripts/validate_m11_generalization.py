"""Validation script for Milestone M11: Any-Dam / Any-River Generalization & Multi-Site Portability.

Performs all mandatory verification checks required for M11 acceptance.
"""

from __future__ import annotations

import os
import sys
import json
import math
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.site_registry import list_sites, load_site
from backend.app.services.site_validator import validate_site_config
from backend.app.services.workflow_gates import evaluate_workflow_gates
from backend.app.core.crs import derive_project_crs
from backend.app.services.hydrograph import generate_site_hydrograph, compute_breach_parameters
from backend.app.schemas.site import GateStatus, ImpoundmentType


def run_m11_validation():
    print("\n" + "=" * 66)
    print("  JalRakshak-HD M11: Generalization & Multi-Site Validation")
    print("=" * 66)

    checks = []

    # 1. Site registry >= 2 real sites
    sites = list_sites()
    site_ids = [s["site_id"] for s in sites]
    chk_reg = len(sites) >= 2 and "bhavanisagar" in site_ids and "hirakud" in site_ids
    checks.append(("Site registry contains >= 2 sites (bhavanisagar, hirakud)", chk_reg))

    # 2. Bhavanisagar site loading & validation
    bhv_cfg = load_site("bhavanisagar")
    bhv_rep = validate_site_config(bhv_cfg)
    checks.append(("Bhavanisagar configuration schema valid", bhv_rep.is_valid))

    # 3. Hirakud site loading & validation
    hrk_cfg = load_site("hirakud")
    hrk_rep = validate_site_config(hrk_cfg)
    checks.append(("Hirakud second-site configuration schema valid", hrk_rep.is_valid))

    # 4. Automatic CRS derivation for different UTM zones
    crs_bhv = derive_project_crs(11.47083, 77.11389)
    crs_hrk = derive_project_crs(21.5700, 83.8694)
    chk_crs = (crs_bhv.project_crs == "EPSG:32643") and (crs_hrk.project_crs == "EPSG:32644")
    checks.append(("Automatic CRS derived correctly (Bhavani: UTM 43N, Hirakud: UTM 44N)", chk_crs))

    # 5. Real DEM & Terrain assets for Hirakud
    hrk_dem = project_root / "data" / "hirakud" / "terrain" / "srtm_dem_30m.tif"
    chk_dem = hrk_dem.is_file() and hrk_dem.stat().st_size > 100000
    checks.append(("Hirakud real DEM raster generated (SRTM 30m)", chk_dem))

    # 6. Real River & Dam vectors for Hirakud
    hrk_river = project_root / "data" / "hirakud" / "hydrology" / "mahanadi_river.geojson"
    hrk_dam = project_root / "data" / "hirakud" / "dam_point.geojson"
    chk_vec = hrk_river.is_file() and hrk_dam.is_file()
    checks.append(("Hirakud river and dam point GeoJSON assets exist", chk_vec))

    # 7. Second-site authoritative sources and engineering matrix
    src_json = project_root / "outputs" / "validation" / "m11_second_site_sources.json"
    mat_csv = project_root / "outputs" / "validation" / "m11_second_site_engineering_matrix.csv"
    chk_src = src_json.is_file() and mat_csv.is_file()
    checks.append(("Hirakud authoritative sources and engineering matrix exist", chk_src))

    # 8. Bhavanisagar M3/M4 Regression
    bhv_breach = compute_breach_parameters(780.5, 40.0, 32.0, "PRESCRIBED_BREACH")
    chk_reg_m3 = (
        math.isclose(bhv_breach["average_breach_width_m"], 219.28, abs_tol=0.1) and
        math.isclose(bhv_breach["formation_time_s"], 14095.59, abs_tol=1.0) and
        math.isclose(bhv_breach["peak_discharge_m3s"], 18742.38, abs_tol=1.0)
    )
    checks.append(("Bhavanisagar breach regression preserved (219.28m, 14095.59s, 18742.38m3/s)", chk_reg_m3))

    # 9. Workflow gates evaluation
    bhv_gates = evaluate_workflow_gates(bhv_cfg)
    hrk_gates = evaluate_workflow_gates(hrk_cfg)
    chk_gates = (
        bhv_gates.gate_a_location == GateStatus.READY and
        bhv_gates.gate_g_consequence == GateStatus.READY and
        hrk_gates.gate_a_location == GateStatus.READY and
        hrk_gates.gate_b_terrain == GateStatus.READY and
        hrk_gates.gate_e_breach == GateStatus.READY and
        hrk_gates.gate_g_consequence == GateStatus.BLOCKED
    )
    checks.append(("Workflow gates correctly distinguish verified from unrun stages", chk_gates))

    # 10. Natural blockage extensibility hook verified
    chk_imp = ImpoundmentType.ENGINEERED_DAM.value == "ENGINEERED_DAM" and \
              ImpoundmentType.LANDSLIDE_DAM.value == "LANDSLIDE_DAM" and \
              ImpoundmentType.GLACIAL_BLOCKAGE.value == "GLACIAL_BLOCKAGE"
    checks.append(("ImpoundmentType extensible enum covers natural blockages", chk_imp))

    # 11. Screenshot generated
    s_shot = project_root / "outputs" / "dashboard" / "screenshots" / "m11_second_site.png"
    checks.append(("Second-site dashboard screenshot generated", s_shot.is_file()))

    # Print results
    passed = 0
    for label, status in checks:
        mark = "[PASS]" if status else "[FAIL]"
        print(f"  {mark} {label}")
        if status:
            passed += 1

    total = len(checks)
    pct = (passed / total) * 100.0
    print("-" * 66)
    print(f"  Validation Summary: {passed}/{total} Checks Passed ({pct:.1f}%)")
    print("=" * 66 + "\n")

    report_data = {
        "milestone": "M11",
        "total_checks": total,
        "passed_checks": passed,
        "pass_rate_pct": pct,
        "checks": [{"description": l, "passed": s} for l, s in checks],
    }
    with open(project_root / "outputs" / "validation" / "m11_generalization_validation.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    return passed == total


if __name__ == "__main__":
    success = run_m11_validation()
    sys.exit(0 if success else 1)
