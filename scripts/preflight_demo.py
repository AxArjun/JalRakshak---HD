"""
Preflight Demo Diagnostic Script (M12).
Verifies system readiness before live SIH jury demonstration.
"""

from __future__ import annotations

import os
import sys
import socket
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_preflight():
    print("=" * 68)
    print("  JalRakshak-HD: SIH Jury Preflight Demo Checklist")
    print("=" * 68)

    checks = []

    # 1. Python environment and imports
    try:
        import fastapi
        import uvicorn
        import rasterio
        import geopandas
        import shapely
        import pyproj
        import numpy
        import pandas
        checks.append(("Required Python scientific packages installed", True))
    except ImportError as e:
        checks.append((f"Required Python scientific packages installed ({e})", False))

    # 2. Frontend dist build
    dist_dir = PROJECT_ROOT / "frontend" / "dist"
    index_html = dist_dir / "index.html"
    checks.append(("Frontend production build dist/ exists", index_html.is_file()))

    # 3. GeoJSON Assets
    geojson_dir = PROJECT_ROOT / "outputs" / "dashboard" / "geojson"
    required_geojsons = [
        "dam_point.geojson", "reservoir_surface.geojson", "bhavani_river.geojson",
        "bridges.geojson", "settlements.geojson", "critical_facilities.geojson",
        "inundation_extent.geojson", "hazard_severity.geojson", "response_zones.geojson",
        "road_exposure.geojson", "historical_flood.geojson", "latest_water_change.geojson",
        "hirakud_dam_point.geojson", "hirakud_reservoir.geojson", "hirakud_mahanadi_river.geojson"
    ]
    all_geo = all((geojson_dir / g).is_file() for g in required_geojsons)
    checks.append((f"All {len(required_geojsons)} dashboard GeoJSON vector layers present", all_geo))

    # 4. Simulation Frames
    frames_dir = PROJECT_ROOT / "outputs" / "dashboard" / "simulation_frames"
    frame_count = len(list(frames_dir.glob("frame_*.png"))) if frames_dir.exists() else 0
    checks.append(("181 D-Flow FM simulation frames present", frame_count >= 181))

    # 5. Offline Overlays
    overlays_dir = PROJECT_ROOT / "outputs" / "dashboard" / "overlays"
    required_overlays = ["hillshade.png", "max_depth.png", "max_velocity.png", "arrival_time.png", "hazard_class.png"]
    all_overlays = all((overlays_dir / o).is_file() for o in required_overlays)
    checks.append(("All static raster overlays and offline hillshade present", all_overlays))

    # 6. Sites Registered
    sites_dir = PROJECT_ROOT / "sites"
    has_bhv = (sites_dir / "bhavanisagar" / "dam.yaml").is_file()
    has_hrk = (sites_dir / "hirakud" / "dam.yaml").is_file()
    checks.append(("Registered sites (Bhavanisagar & Hirakud) configured", has_bhv and has_hrk))

    # 7. Port availability / Service Status
    be_active = check_port_open(8000)
    fe_active = check_port_open(5173)
    status_str = "Backend port 8000 LIVE" if be_active else "Backend port 8000 available for startup"
    checks.append((status_str, True))
    status_fe = "Frontend port 5173 LIVE" if fe_active else "Frontend port 5173 available for startup"
    checks.append((status_fe, True))

    # Summary
    passed = 0
    for label, status in checks:
        mark = "[PASS]" if status else "[FAIL]"
        print(f"  {mark} {label}")
        if status:
            passed += 1

    total = len(checks)
    pct = (passed / total) * 100.0
    print("-" * 68)
    print(f"  Preflight Summary: {passed}/{total} Checks Passed ({pct:.1f}%)")
    print("  DEMO READINESS: " + ("DEMO_READY" if passed == total else "ACTION_REQUIRED"))
    print("=" * 68)
    return passed == total

if __name__ == "__main__":
    success = run_preflight()
    sys.exit(0 if success else 1)
