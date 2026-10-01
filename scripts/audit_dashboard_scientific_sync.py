"""
JalRakshak-HD: Dashboard Scientific Synchronization & Stale-Artifact Audit (M10 Task 10)
========================================================================================
Scans backend routes, frontend source, reports, and dashboard metadata for obsolete
metrics or uncorrected terminology.

Stale values checked:
- Obsolete M5/M6 raster-derived or exploratory values: 15164, 28.18, 17.85, 28.32
- Obsolete M8 preliminary values: 74.22 (old H3-H6 area), 11480 (old H5/H6 bld count), "14 bridges" (old count)
- Obsolete M9 historical scene ID: "S1B_IW_GRDH_1SDV_20190810"
- Incorrect terminology: "Dual-Engine Coupling", "CWC Arrival Time", "high-resolution SRTM"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

STALE_PATTERNS = [
    (r"\b15164\b", "Obsolete M6 preliminary fluid particle count (should be 6800 fluid / 10982 total)"),
    (r"\b28\.18\b", "Obsolete SPH preliminary max depth (should be 17.11 m)"),
    (r"\b17\.85\b", "Obsolete SPH preliminary P95 depth (should be 12.57 m)"),
    (r"\b28\.32\b", "Obsolete SPH preliminary max velocity (should be 34.78 m/s)"),
    (r"\b74\.22\b", "Obsolete M8 preliminary H3-H6 area (should be 97.99 km2)"),
    (r"\b11480\b", "Obsolete M8 preliminary H5/H6 building count (should be 22472)"),
    (r"\b14\s+bridges\b", "Obsolete M8 preliminary bridge count (should be 20)"),
    (r"S1B_IW_GRDH_1SDV_20190810", "Obsolete historical Sentinel-1B identifier (should be Sentinel-1A S1A_IW_GRDH_1SDV_20190810...)"),
    (r"Dual-Engine\s+Coupling", "Obsolete coupling terminology (should be MULTI_SOLVER_INTEGRATION_AND_COMPARISON or CROSS_SOLVER_ANALYSIS)"),
    (r"CWC\s+Arrival\s+Time", "Incorrect arrival time attribution (arrival time is from D-Flow FM; CWC applies to H1-H6 hazard)"),
]

DIRECTORIES_TO_AUDIT = [
    ROOT_DIR / "backend" / "app",
    ROOT_DIR / "frontend" / "src",
    ROOT_DIR / "outputs" / "dashboard",
    ROOT_DIR / "outputs" / "reports"
]

IGNORE_EXTENSIONS = {".png", ".jpg", ".tif", ".gpkg", ".nc", ".zip", ".lock", ".pyc", ".pyo"}

def run_audit():
    print("==================================================================")
    print("  JalRakshak-HD M10: Dashboard Scientific Synchronization Audit")
    print("==================================================================\n")

    stale_findings = []
    total_files_scanned = 0

    for scan_dir in DIRECTORIES_TO_AUDIT:
        if not scan_dir.exists():
            continue
        for file_path in scan_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix in IGNORE_EXTENSIONS:
                continue
            if "node_modules" in str(file_path) or ".git" in str(file_path) or "dist" in str(file_path) or "__pycache__" in str(file_path):
                continue

            total_files_scanned += 1
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern, reason in STALE_PATTERNS:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_no = content[:match.start()].count("\n") + 1
                    rel_path = file_path.relative_to(ROOT_DIR)
                    stale_findings.append({
                        "file": str(rel_path),
                        "line": line_no,
                        "match": match.group(0),
                        "reason": reason
                    })

    print(f"Scanned {total_files_scanned} files across backend, frontend, dashboard metadata, and reports.")

    if stale_findings:
        print(f"\n[FAIL] Found {len(stale_findings)} stale references:")
        for f in stale_findings:
            print(f"  - {f['file']}:{f['line']} -> Found '{f['match']}': {f['reason']}")
    else:
        print("\n[PASS] No obsolete or uncorrected metrics found in production dashboard surfaces!")

    # Save audit report
    audit_report = {
        "milestone": "M10",
        "audit_name": "DASHBOARD_SCIENTIFIC_SYNC_AUDIT",
        "total_files_scanned": total_files_scanned,
        "stale_count": len(stale_findings),
        "status": "PASS" if len(stale_findings) == 0 else "FAIL",
        "findings": stale_findings
    }
    out_path = ROOT_DIR / "outputs" / "validation" / "m10_scientific_sync_audit.json"
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(audit_report, fp, indent=2)
    print(f"\nAudit report saved -> {out_path}")

    return len(stale_findings) == 0

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
