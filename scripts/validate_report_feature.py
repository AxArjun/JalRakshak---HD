import json
import sys
import requests
from pathlib import Path

def validate_reports():
    base_url = "http://127.0.0.1:8000/api/reports"
    
    # 1. Test impact report at frame 0 and frame 90 and frame 180
    for idx in [0, 90, 180]:
        try:
            r = requests.get(f"{base_url}/impact/{idx}", timeout=5)
            if r.status_code != 200:
                print(f"[FAIL] Impact report endpoint failed for frame {idx}: {r.status_code}")
                return 1
            data = r.json()
            if data["frame_index"] != idx:
                print(f"[FAIL] Mismatched frame index: {data['frame_index']}")
                return 1
            if "research screening prototype" not in data["disclaimer"].lower():
                print(f"[FAIL] Missing hypothetical disclaimer in impact report")
                return 1
            if data["current_impact"]["worldpop_exposed"] > 42428.2:
                print(f"[FAIL] WorldPop exceeded envelope: {data['current_impact']['worldpop_exposed']}")
                return 1
            print(f"[PASS] Impact report frame {idx} verified: Area={data['current_impact']['inundated_area_km2']} km2, WP={data['current_impact']['worldpop_exposed']}")
        except Exception as e:
            print(f"[FAIL] Error connecting to impact report endpoint: {e}")
            return 1
            
    # 2. Test final report endpoint
    try:
        r = requests.get(f"{base_url}/final", timeout=5)
        if r.status_code != 200:
            print(f"[FAIL] Final report endpoint failed: {r.status_code}")
            return 1
        final_rep = r.json()
        if final_rep["hydraulics"]["maximum_inundated_area_km2"] != 101.29:
            print(f"[FAIL] Final report inundated area mismatch: {final_rep['hydraulics']['maximum_inundated_area_km2']}")
            return 1
        if final_rep["exposure"]["worldpop_exposed"] != 42428.1:
            print(f"[FAIL] Final report WorldPop mismatch: {final_rep['exposure']['worldpop_exposed']}")
            return 1
        if final_rep["exposure"]["ghsl_exposed"] != 84500.5:
            print(f"[FAIL] Final report GHSL mismatch: {final_rep['exposure']['ghsl_exposed']}")
            return 1
        print("[PASS] Final report endpoint verified against locked scientific metrics")
    except Exception as e:
        print(f"[FAIL] Error connecting to final report endpoint: {e}")
        return 1
        
    # 3. Test HTML generation endpoints
    try:
        r_html_impact = requests.get(f"{base_url}/impact/30/html", timeout=5)
        if r_html_impact.status_code != 200 or "<html" not in r_html_impact.text:
            print(f"[FAIL] HTML impact report failed")
            return 1
            
        r_html_final = requests.get(f"{base_url}/final/html", timeout=5)
        if r_html_final.status_code != 200 or "<html" not in r_html_final.text:
            print(f"[FAIL] HTML final report failed")
            return 1
        print("[PASS] Print-ready HTML report generation endpoints verified")
    except Exception as e:
        print(f"[FAIL] Error testing HTML endpoints: {e}")
        return 1
        
    print("[PASS] ALL REPORT FEATURE VALIDATIONS PASSED (100.0%)")
    return 0

if __name__ == "__main__":
    sys.exit(validate_reports())
