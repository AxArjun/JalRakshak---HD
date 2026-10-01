import json
import sys
from pathlib import Path

def validate_timestep_impacts():
    root = Path("C:/JalRakshak-HD")
    impact_file = root / "outputs" / "dashboard" / "impact" / "timestep_impacts.json"
    
    if not impact_file.exists():
        print(f"[FAIL] Missing {impact_file}")
        return 1
        
    with open(impact_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    frames = data.get("frames", [])
    if len(frames) != 181:
        print(f"[FAIL] Expected 181 frames, found {len(frames)}")
        return 1
    print(f"[PASS] 181 frames present (frame 0 to {len(frames)-1})")
    
    # Check monotonic timestamps
    for i, frame in enumerate(frames):
        if frame['frame_index'] != i:
            print(f"[FAIL] Frame index mismatch at {i}: {frame['frame_index']}")
            return 1
        if frame['time_s'] != i * 600:
            print(f"[FAIL] Frame time mismatch at {i}: {frame['time_s']}")
            return 1
            
    print("[PASS] Time sequence verified: 0s to 108,000s monotonically")
    
    # Final frame check
    last_frame = frames[-1]['current_impact']
    
    tol = 0.5
    checks = [
        ("Inundated Area (101.29 km2)", abs(last_frame['inundated_area_km2'] - 101.29) <= tol),
        ("WorldPop (42428.1)", abs(last_frame['worldpop_exposed'] - 42428.1) <= tol),
        ("GHSL (84500.5)", abs(last_frame['ghsl_exposed'] - 84500.5) <= tol),
        ("Buildings (25652)", last_frame['buildings_exposed'] <= 25652),
        ("Roads (243.82 km)", abs(last_frame['roads_exposed_km'] - 243.82) <= tol),
        ("Bridges (20)", last_frame['bridges_exposed'] <= 20),
        ("Critical Facilities (13)", last_frame['critical_facilities_exposed'] <= 13),
    ]
    
    for name, ok in checks:
        if ok:
            print(f"[PASS] Maximum envelope check: {name}")
        else:
            print(f"[FAIL] Maximum envelope check failed: {name}")
            return 1
            
    print("[PASS] ALL TIMESTEP IMPACT CHECKS PASSED (100.0%)")
    return 0

if __name__ == "__main__":
    sys.exit(validate_timestep_impacts())
