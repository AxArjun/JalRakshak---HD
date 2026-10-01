import os
import shutil
from pathlib import Path

def create_demo_package():
    root = Path("C:/JalRakshak-HD")
    pkg = root / "demo_package"
    pkg.mkdir(exist_ok=True)
    
    # 1. Copy essential docs and manifests
    (pkg / "docs").mkdir(exist_ok=True)
    for doc in (root / "docs").glob("*.md"):
        shutil.copy2(doc, pkg / "docs" / doc.name)
        
    (pkg / "outputs" / "validation").mkdir(parents=True, exist_ok=True)
    for v in (root / "outputs" / "validation").glob("*.*"):
        shutil.copy2(v, pkg / "outputs" / "validation" / v.name)
        
    (pkg / "outputs" / "reports").mkdir(parents=True, exist_ok=True)
    for r in (root / "outputs" / "reports").glob("*.md"):
        shutil.copy2(r, pkg / "outputs" / "reports" / r.name)
        
    # 2. Copy sites config
    (pkg / "sites").mkdir(exist_ok=True)
    shutil.copytree(root / "sites", pkg / "sites", dirs_exist_ok=True)
    
    # 3. Copy VERSION and launch scripts
    shutil.copy2(root / "VERSION", pkg / "VERSION")
    shutil.copy2(root / "START_DEMO.bat", pkg / "START_DEMO.bat")
    shutil.copy2(root / "start_jalrakshak.ps1", pkg / "start_jalrakshak.ps1")
    shutil.copy2(root / "README.md", pkg / "README.md")
    
    # 4. Write README_DEMO.md
    readme_demo = """# JalRakshak-HD Portable Demo Package

This package contains all pre-computed scientific assets, dashboard frames, and configuration definitions necessary to demonstrate JalRakshak-HD without requiring Delft3D FM or DualSPHysics HPC solvers.

## Instructions
1. Run `START_DEMO.bat` or `powershell -File start_jalrakshak.ps1`
2. Open browser at `http://localhost:5173`
3. Refer to `docs/SIH_DEMO_SCRIPT.md` for the presentation flow and `docs/SIH_JURY_QA.md` for technical defense.
"""
    with open(pkg / "README_DEMO.md", "w", encoding="utf-8") as f:
        f.write(readme_demo)
        
    print(f"[OK] Demo package generated successfully at {pkg}")

if __name__ == "__main__":
    create_demo_package()
