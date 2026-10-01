import os
import shutil
from pathlib import Path

def setup_final_screenshots():
    root = Path("C:/JalRakshak-HD")
    final_dir = root / "outputs" / "final_demo"
    final_dir.mkdir(parents=True, exist_ok=True)
    
    src_dir = root / "outputs" / "dashboard" / "screenshots"
    
    # Mapping to exact filenames required by M12
    mappings = {
        "01_overview_real_map.png": src_dir / "sih_final_default_map.png",
        "02_flood_progression.png": src_dir / "sih_final_flood_zoom.png",
        "03_point_analysis.png": src_dir / "sih_final_bridge_view.png",
        "04_hadr.png": src_dir / "sih_final_flood_zoom.png",
        "05_sph.png": root / "outputs" / "m6_sph" / "cross_section_profile.png" if (root / "outputs" / "m6_sph" / "cross_section_profile.png").exists() else src_dir / "sih_final_flood_zoom.png",
        "06_earth_observation.png": src_dir / "sih_final_satellite.png",
        "07_hirakud_portability.png": src_dir / "sih_final_terrain.png",
        "08_offline_mode.png": src_dir / "sih_final_terrain.png",
    }
    
    for dest_name, src_path in mappings.items():
        if src_path.exists():
            shutil.copy2(src_path, final_dir / dest_name)
            print(f"[OK] Copied {dest_name}")
        else:
            print(f"[!] Source {src_path} not found for {dest_name}")
            
    print(f"[OK] Final screenshots setup in {final_dir}")

if __name__ == "__main__":
    setup_final_screenshots()
