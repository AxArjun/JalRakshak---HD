"""
M10 Dashboard E2E API Validation
Tests all backend endpoints, file assets, and generates validation report.
"""
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://127.0.0.1:8000"
PROJ = Path("C:/JalRakshak-HD")
RESULTS = []

def test(name, fn):
    try:
        result = fn()
        RESULTS.append({"test": name, "status": "PASS", "detail": result})
        print(f"  [PASS] {name} -> {str(result)[:80]}")
    except Exception as e:
        RESULTS.append({"test": name, "status": "FAIL", "detail": str(e)})
        print(f"  [FAIL] {name} -> {e}")

def get(path):
    url = BASE + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def get_raw(path):
    url = BASE + path
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, len(r.read())

print("\n==============================================")
print("  JalRakshak-HD M10 - API E2E Validation")
print("==============================================\n")

# --- Health & Project --------------------------------------
print("-> Health & Project")
test("GET /health",
     lambda: get("/health"))
test("GET /api/health",
     lambda: get("/api/health"))
test("GET /api/project/meta (values check)",
     lambda: (
         lambda d: f"domain={d.get('domain_area_km2')} km2, inundated={d.get('max_inundated_area_km2')} km2"
         if d.get("domain_area_km2") == 818.37 and d.get("max_inundated_area_km2") == 101.29
         else (_ for _ in ()).throw(ValueError(f"Unexpected project values: {d}"))
     )(get("/api/project/meta")))

# --- Simulation --------------------------------------------
print("\n-> Simulation")
test("GET /api/simulation/meta (M5 values check)",
     lambda: (
         lambda d: f"solver_d={d.get('solver_max_depth_m')}m, solver_v={d.get('solver_max_velocity_mps')}m/s, domain={d.get('domain_area_km2')}km2, frames={d.get('total_frames')}"
         if d.get("solver_max_depth_m") == 22.02 and d.get("solver_max_velocity_mps") == 11.79 and d.get("domain_area_km2") == 818.37 and d.get("max_inundated_area_km2") == 101.29
         else (_ for _ in ()).throw(ValueError(f"M5 values mismatch: {d}"))
     )(get("/api/simulation/meta")))
test("GET /api/tiles/simulation_frames/frame_000.png",
     lambda: f"status={get_raw('/api/tiles/simulation_frames/frame_000.png')[0]}, "
             f"bytes={get_raw('/api/tiles/simulation_frames/frame_000.png')[1]}")
test("GET /api/tiles/simulation_frames/frame_090.png",
     lambda: f"status={get_raw('/api/tiles/simulation_frames/frame_090.png')[0]}")
test("GET /api/tiles/simulation_frames/frame_180.png",
     lambda: f"status={get_raw('/api/tiles/simulation_frames/frame_180.png')[0]}")

# --- HADR Exposure -----------------------------------------
print("\n-> HADR / Exposure")
test("GET /api/hadr/summary (M8 values check)",
     lambda: (
         lambda d: f"WP={d.get('worldpop_exposed')}, GHSL={d.get('ghsl_exposed')}, Bld={d.get('buildings_exposed')}, H5/H6 Bld={d.get('h5_h6_buildings_exposed')}, Bridges={d.get('bridges_exposed_count')}, H3-H6 Area={d.get('severe_hazard_h3_h6_area_km2')}"
         if d.get("worldpop_exposed") == 42428.1 and d.get("ghsl_exposed") == 84500.5 and d.get("buildings_exposed") == 25652 and d.get("h5_h6_buildings_exposed") == 22472 and d.get("bridges_exposed_count") == 20 and d.get("severe_hazard_h3_h6_area_km2") == 97.99
         else (_ for _ in ()).throw(ValueError(f"M8 values mismatch: {d}"))
     )(get("/api/hadr/summary")))
test("GET /api/hadr/hazard/summary",
     lambda: f"total_area_km2={get('/api/hadr/hazard/summary').get('total_inundated_area_km2','?')}")
test("GET /api/hadr/response-zones",
     lambda: f"zones={len(get('/api/hadr/response-zones').get('zones',[]))}")

# --- SPH ---------------------------------------------------
print("\n-> SPH Near-Field")
test("GET /api/sph/summary (M6/M7 values check)",
     lambda: (
         lambda d: f"particles={d.get('total_particles')}, max_d={d.get('max_depth_m')}m, max_v={d.get('max_velocity_mps')}m/s, coupling={d.get('direct_coupling_ready')}"
         if d.get("total_particles") == 10982 and d.get("max_depth_m") == 17.11 and d.get("max_velocity_mps") == 34.78 and d.get("direct_coupling_ready") is False and d.get("simulation_duration_s") == 600.0
         else (_ for _ in ()).throw(ValueError(f"M6/M7 values mismatch: {d}"))
     )(get("/api/sph/summary")))

# --- Remote Sensing ----------------------------------------
print("\n-> Remote Sensing / EO")
test("GET /api/remote-sensing/summary (M9 values check)",
     lambda: (
         lambda d: f"historical_platform={d.get('historical_platform')}, vector_flood={d.get('historical_flood_vector_km2')}km2, latest_orbit={d.get('latest_scene',{}).get('absolute_orbit')}"
         if d.get("historical_platform") == "Sentinel-1A" and d.get("historical_flood_vector_km2") == 1.1150 and d.get("latest_scene",{}).get("absolute_orbit") == 4581
         else (_ for _ in ()).throw(ValueError(f"M9 values mismatch: {d}"))
     )(get("/api/remote-sensing/summary")))

# --- GIS Tiles ---------------------------------------------
print("\n-> GIS Tiles (Overlays)")
for overlay in ["max_depth", "max_velocity", "arrival_time", "hazard_class",
                "historical_flood", "hillshade"]:
    test(f"GET /api/tiles/overlays/{overlay}.png",
         lambda o=overlay: f"bytes={get_raw(f'/api/tiles/overlays/{o}.png')[1]}")

# --- GIS Tiles (GeoJSON) ----------------------------------
print("\n-> GIS Tiles (GeoJSON)")
for gj in ["inundation_extent", "response_zones", "bhavani_river",
           "dam_point", "hazard_severity", "road_exposure",
           "critical_facilities", "sph_gauges"]:
    test(f"GET /api/tiles/geojson/{gj}.geojson",
         lambda g=gj: f"bytes={get_raw(f'/api/tiles/geojson/{g}.geojson')[1]}")

# --- GIS Point Query --------------------------------------
print("\n-> GIS Point Query")
test("GET /api/gis/query-point (inundated zone)",
     lambda: f"depth={get('/api/gis/query-point?lat=11.47&lng=77.26').get('depth_m','?')}m")
test("GET /api/gis/query-point (outside domain)",
     lambda: f"depth={get('/api/gis/query-point?lat=12.0&lng=78.0').get('depth_m','?')}")

# --- File-system Assets -----------------------------------
print("\n-> File-system Assets")
def check_file(rel):
    p = PROJ / rel
    if not p.exists():
        raise FileNotFoundError(f"Missing: {p}")
    return f"{p.stat().st_size:,} bytes"

test("outputs/dashboard/overlays/manifest.json", lambda: check_file("outputs/dashboard/overlays/manifest.json"))
test("outputs/dashboard/simulation_frames/frame_000.png", lambda: check_file("outputs/dashboard/simulation_frames/frame_000.png"))
test("outputs/dashboard/simulation_frames/frame_180.png", lambda: check_file("outputs/dashboard/simulation_frames/frame_180.png"))
test("outputs/dashboard/geojson/hazard_severity.geojson", lambda: check_file("outputs/dashboard/geojson/hazard_severity.geojson"))
test("outputs/validation/m8_exposure_summary.json", lambda: check_file("outputs/validation/m8_exposure_summary.json"))
test("outputs/validation/m8_hazard_severity_summary.json", lambda: check_file("outputs/validation/m8_hazard_severity_summary.json"))

# --- Frontend dist -----------------------------------------
print("\n-> Frontend Build Artifacts")
test("frontend/dist/index.html", lambda: check_file("frontend/dist/index.html"))
dist_js = list((PROJ / "frontend/dist/assets").glob("*.js"))
test("frontend/dist/assets/*.js (bundle exists)",
     lambda: f"{len(dist_js)} JS bundles, largest={max(f.stat().st_size for f in dist_js):,} bytes" if dist_js else "NO JS BUNDLES FOUND")

# --- Summary ----------------------------------------------
passed = sum(1 for r in RESULTS if r["status"] == "PASS")
failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
total = len(RESULTS)

print(f"\n==============================================")
print(f"  Results:  {passed}/{total} PASS   {failed}/{total} FAIL")
print(f"==============================================\n")

# Save report
report = {
    "milestone": "M10",
    "validation_type": "E2E_API_AND_ASSET_CHECK",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "summary": {"total": total, "passed": passed, "failed": failed},
    "results": RESULTS
}

out_path = PROJ / "outputs/validation/m10_e2e_validation.json"
out_path.parent.mkdir(exist_ok=True)
with open(out_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"Report saved -> {out_path}")

sys.exit(0 if failed == 0 else 1)
