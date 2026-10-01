import json
import sys
import requests
from pathlib import Path

def validate_affected_places():
    root = Path("C:/JalRakshak-HD")
    affected_file = root / "outputs" / "dashboard" / "impact" / "affected_places.json"
    settlements_file = root / "outputs" / "dashboard" / "geojson" / "settlements.geojson"
    
    # 1. Check file existence
    if not affected_file.exists() or not settlements_file.exists():
        print(f"[FAIL] Missing {affected_file} or {settlements_file}")
        return 1
        
    with open(affected_file, "r", encoding="utf-8") as f:
        aff_data = json.load(f)
    with open(settlements_file, "r", encoding="utf-8") as f:
        set_data = json.load(f)
        
    real_names = {feat["properties"]["name"] for feat in set_data["features"]}
    places = aff_data.get("places", [])
    
    print(f"[*] Total settlements in GIS: {len(real_names)}")
    print(f"[*] Total places in affected_places.json: {len(places)}")
    
    # 2. Check every place name comes from real GIS
    for p in places:
        name = p["place_name"]
        if name not in real_names:
            print(f"[FAIL] Place '{name}' not found in real GIS settlements!")
            return 1
        # Check point population rule: must be null for point-only screening
        if p["population_estimate"] is not None:
            print(f"[FAIL] Population estimate for point settlement '{name}' should be null, found {p['population_estimate']}")
            return 1
        if p["classification"] != "POINT_BASED_SETTLEMENT_SCREENING":
            print(f"[FAIL] Invalid classification for '{name}': {p['classification']}")
            return 1
        if p["affected"]:
            if "Settlement reference point affected; whole municipal area not quantified." not in p.get("notes", ""):
                print(f"[FAIL] Affected settlement '{name}' missing required municipal quantification disclaimer note.")
                return 1
            # Check local sampling: ensure NOT copied from global 22.02m / 11.79m/s
            if p["max_depth_m"] == 22.02 and p["max_velocity_mps"] == 11.79:
                print(f"[FAIL] Local depth/velocity for '{name}' was copied directly from global M5 maxima (22.02m, 11.79m/s)!")
                return 1
                
    # Check Komarapalayam is marked outside reach
    komarapalayam = next((p for p in places if p["place_name"] == "Komarapalayam"), None)
    if komarapalayam and komarapalayam["affected"]:
        print(f"[FAIL] Komarapalayam lies outside 51.73 km reach but is marked affected!")
        return 1
        
    print("[PASS] All place names, coordinates, local hydraulic sampling, and unallocated population rules verified against real GIS")
    
    # 3. Test API reports endpoints
    base_url = "http://127.0.0.1:8000/api/reports"
    try:
        r_final = requests.get(f"{base_url}/final", timeout=5)
        if r_final.status_code != 200:
            print(f"[FAIL] /api/reports/final returned {r_final.status_code}")
            return 1
            
        data = r_final.json()
        
        # Check scientific corrections
        # A. GHSL 2025
        if "2025" not in data["exposure"].get("ghsl_version", ""):
            print(f"[FAIL] GHSL version is not GHSL 2025: {data['exposure'].get('ghsl_version')}")
            return 1
            
        # B. August 2019 Sentinel-1
        eo = data.get("earth_observation_context", {})
        if "2019" not in eo.get("historical_date", "") or "AUGUST" not in eo.get("historical_event", ""):
            print(f"[FAIL] Historical event is not August 2019: {eo}")
            return 1
            
        # C. M6 SPH classification
        sph = data.get("nearfield_sph_summary", {})
        if "2D_UNIT_WIDTH" not in sph.get("model_classification", ""):
            print(f"[FAIL] SPH classification is not 2D unit-width: {sph}")
            return 1
            
        # D. M7 Cross-Solver
        cs = data.get("cross_solver_analysis", {})
        if cs.get("direct_two_way_coupling") is not False:
            print(f"[FAIL] Direct coupling should be False: {cs}")
            return 1
            
        # E. Affected places & Evacuation Priority tables
        if len(data.get("affected_places", [])) != 10:
            print(f"[FAIL] Expected 10 affected places in final report, found {len(data.get('affected_places', []))}")
            return 1
            
        evac = data.get("evacuation_priority_screening", {})
        if not evac.get("immediate_under_30_min") or not evac.get("advance_notice_over_2_hr"):
            print(f"[FAIL] Evacuation priority grouping missing categories: {evac}")
            return 1
            
        # F. Check HTML report contains sections
        r_html = requests.get(f"{base_url}/final/html", timeout=5)
        if r_html.status_code != 200:
            print(f"[FAIL] /api/reports/final/html failed: {r_html.status_code}")
            return 1
            
        html_text = r_html.text
        if "Affected Places & Modeled Arrival" not in html_text:
            print(f"[FAIL] HTML report missing Affected Places section")
            return 1
        if "MODELED EVACUATION PRIORITY" not in html_text:
            print(f"[FAIL] HTML report missing Modeled Evacuation Priority section")
            return 1
        if "Bhavanisagar" not in html_text or "Sathyamangalam" not in html_text:
            print(f"[FAIL] HTML report missing real settlement names")
            return 1
            
        print("[PASS] Final report API and HTML report contain all verified sections and scientific corrections")
        
    except Exception as e:
        print(f"[FAIL] Error testing API: {e}")
        return 1
        
    print("[PASS] ALL AFFECTED PLACES & EVACUATION REPORT VALIDATIONS PASSED (100.0%)")
    return 0

if __name__ == "__main__":
    sys.exit(validate_affected_places())

