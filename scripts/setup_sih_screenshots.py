import shutil
from pathlib import Path

def setup_sih_screenshots():
    root = Path("C:/JalRakshak-HD")
    sdir = root / "outputs" / "dashboard" / "screenshots"
    
    pairs = [
        ("sih_layout_fixed.png", sdir / "sih_final_default_map.png"),
        ("sih_impact_report_timestep.png", sdir / "sih_final_flood_zoom.png"),
        ("sih_evacuation_screening.png", sdir / "sih_final_bridge_view.png"),
        ("sih_final_report_preview.png", sdir / "sih_final_satellite.png"),
        ("sih_map_fullscreen.png", sdir / "sih_final_terrain.png"),
    ]
    
    for dest, src in pairs:
        if src.exists():
            shutil.copy2(src, sdir / dest)
            print(f"[OK] Created {dest}")
        else:
            print(f"[!] Source {src} not found")
            
if __name__ == "__main__":
    setup_sih_screenshots()
