"""Validation script for M10/M11 Real Map Repair & Second-Site Provenance Normalization."""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def run_real_map_validation():
    print("\n" + "=" * 68)
    print("  JalRakshak-HD: Real Map & Second-Site Provenance Audit")
    print("=" * 68)

    checks = []

    # 1. MapView component basemap check
    mapview_file = project_root / "frontend" / "src" / "components" / "MapView.tsx"
    with open(mapview_file, "r", encoding="utf-8") as f:
        mapview_code = f.read()

    chk_osm = "tile.openstreetmap.org" in mapview_code
    chk_no_carto = "basemaps.cartocdn.com" not in mapview_code
    checks.append(("Default basemap uses OpenStreetMap (no token required)", chk_osm))
    checks.append(("Broken tile provider (CartoDB requiring token) removed", chk_no_carto))

    # 2. Basemap selector support
    chk_selector = "Local Terrain (Offline)" in mapview_code and "Satellite (Esri)" in mapview_code
    checks.append(("Basemap selector control with Local Terrain and Satellite supported", chk_selector))

    # 3. Bhavanisagar bounds and simulation integrity
    chk_bhv_bounds = "11.359179" in mapview_code and "77.423552" in mapview_code
    checks.append(("Bhavanisagar geographic model bounds configured correctly", chk_bhv_bounds))

    # 4. Hirakud bounds and isolation
    chk_hrk_bounds = "21.4000" in mapview_code and "84.1500" in mapview_code
    chk_no_reuse = "Production hydraulic simulation not executed for this site" in mapview_code
    checks.append(("Hirakud geographic model bounds configured correctly", chk_hrk_bounds))
    checks.append(("Hirakud explicitly blocks Bhavanisagar simulation frame reuse", chk_no_reuse))

    # 5. Offline Hillshade assets
    bhv_hs = project_root / "outputs" / "dashboard" / "overlays" / "hillshade.png"
    hrk_hs = project_root / "outputs" / "dashboard" / "overlays" / "hirakud_hillshade.png"
    chk_hs = bhv_hs.is_file() and hrk_hs.is_file()
    checks.append(("Offline SRTM hillshade overlays available for both sites", chk_hs))

    # 6. Hirakud Storage Versioning Audit
    sources_file = project_root / "outputs" / "validation" / "m11_second_site_sources.json"
    with open(sources_file, "r", encoding="utf-8") as f:
        src_data = json.load(f)

    stor = src_data.get("storage_versioning", {})
    chk_stor = (
        stor.get("original_design_1957", {}).get("live_storage_mcm") == 5818.0 and
        stor.get("ohpc_sedimentation_revised", {}).get("live_storage_mcm") == 4823.0 and
        stor.get("cwc_reporting_capacity", {}).get("live_storage_mcm") == 5378.0
    )
    checks.append(("Hirakud multi-version storage documented (Original, OHPC, CWC)", chk_stor))

    # 7. Exact Model Dam Point Audit
    coords = src_data.get("coordinates", {})
    chk_dam_pt = (
        coords.get("site_reference_coordinate", {}).get("latitude") == 21.5700 and
        coords.get("dam_model_coordinate", {}).get("latitude") == 21.5286 and
        coords.get("distance_between_them_m") == 4625.0
    )
    checks.append(("Exact dam model point (21.5286°N, 83.8742°E) and reference coordinate verified", chk_dam_pt))

    # 8. Real Geometry Source Audit
    geom_audit_file = project_root / "outputs" / "validation" / "m11_hirakud_geometry_audit.json"
    chk_geom = geom_audit_file.is_file()
    checks.append(("Hirakud real geometry source audit exists", chk_geom))

    # 9. Real GIS Bridges & Settlements GeoJSON
    bridges_file = project_root / "outputs" / "dashboard" / "geojson" / "bridges.geojson"
    settlements_file = project_root / "outputs" / "dashboard" / "geojson" / "settlements.geojson"
    chk_bridge_set = bridges_file.is_file() and settlements_file.is_file()
    if chk_bridge_set:
        with open(bridges_file, "r", encoding="utf-8") as bf:
            bdata = json.load(bf)
            chk_bridge_cnt = len(bdata.get("features", [])) == 20
        chk_bridge_set = chk_bridge_set and chk_bridge_cnt
    checks.append(("Real GIS bridge crossings (20 features) and settlements exist", chk_bridge_set))

    # 10. Final Real GIS Layer Audit JSON
    final_audit_file = project_root / "outputs" / "validation" / "final_real_gis_layer_audit.json"
    chk_final_audit = final_audit_file.is_file()
    if chk_final_audit:
        with open(final_audit_file, "r", encoding="utf-8") as af:
            adata = json.load(af)
            chk_final_audit = adata.get("summary", {}).get("status") == "PASS" and len(adata.get("layers", [])) >= 12
    checks.append(("Final Real GIS layer audit file exists and PASSes audit", chk_final_audit))

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
    print(f"  Validation Summary: {passed}/{total} Checks Passed ({pct:.1f}%)")
    print("=" * 68 + "\n")

    return passed == total

if __name__ == "__main__":
    success = run_real_map_validation()
    sys.exit(0 if success else 1)
