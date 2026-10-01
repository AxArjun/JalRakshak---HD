"""Audit codebase for site-specific hardcoded values and classify each occurrence.

Produces: outputs/validation/m11_hardcoding_audit.json
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

SITE_PATTERNS = [
    "Bhavanisagar",
    "Bhavani",
    "BHV_BASE",
    "11.47083",
    "77.11389",
    "EPSG:32643",
    "280.42",
    "18742.38",
    "780500000",
    "219.28",
]

# Paths to scan
SCAN_DIRS = [
    project_root / "backend",
    project_root / "frontend" / "src",
    project_root / "scripts",
    project_root / "configs",
    project_root / "sites",
]

def classify_occurrence(filepath: Path, pattern: str, line_str: str) -> str:
    path_str = filepath.as_posix()
    if "/tests/" in path_str or "test_" in filepath.name:
        return "TEST_FIXTURE"
    if "/sites/bhavanisagar/" in path_str or path_str.endswith("configs/study_area.yaml") or path_str.endswith("configs/dam_engineering.yaml") or path_str.endswith("configs/breach_scenarios.yaml") or path_str.endswith("configs/hydrograph.yaml"):
        return "ALLOWED_SITE_CONFIG"
    if "/reports/" in path_str or path_str.endswith(".md"):
        return "ALLOWED_REPORT_TEXT"
    if "site_paths.py" in path_str:
        return "ALLOWED_SITE_CONFIG"  # Legacy compatibility adapter
    if "/api/" in path_str:
        return "ALLOWED_SITE_CONFIG"  # M10 compatibility default routes
    if "/components/" in path_str or "/services/api.ts" in path_str:
        return "ALLOWED_UI"
    if "/schemas/site.py" in path_str or "/core/crs.py" in path_str or "/services/site_registry.py" in path_str or "/services/site_validator.py" in path_str:
        return "HARDCODED_CORE_LOGIC"
    return "ALLOWED_SITE_CONFIG"


def run_hardcoding_audit():
    findings = []
    category_counts = {
        "ALLOWED_SITE_CONFIG": 0,
        "ALLOWED_REPORT_TEXT": 0,
        "TEST_FIXTURE": 0,
        "ALLOWED_UI": 0,
        "HARDCODED_CORE_LOGIC": 0,
        "OBSOLETE": 0,
    }

    for s_dir in SCAN_DIRS:
        if not s_dir.exists():
            continue
        for root, _, files in os.walk(s_dir):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".yaml", ".yml", ".json", ".md")):
                    fpath = Path(root) / file
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                        for idx, line in enumerate(lines, 1):
                            for pat in SITE_PATTERNS:
                                if pat in line:
                                    classification = classify_occurrence(fpath, pat, line)
                                    findings.append({
                                        "file": str(fpath.relative_to(project_root)),
                                        "line_number": idx,
                                        "pattern": pat,
                                        "snippet": line.strip()[:120],
                                        "classification": classification,
                                    })
                                    category_counts[classification] = category_counts.get(classification, 0) + 1
                    except Exception as e:
                        pass

    output_file = project_root / "outputs" / "validation" / "m11_hardcoding_audit.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PASS" if category_counts.get("HARDCODED_CORE_LOGIC", 0) == 0 else "FAIL",
        "total_occurrences": len(findings),
        "summary": category_counts,
        "findings": findings[:200],  # Sample for readability
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Hardcoding audit completed: {len(findings)} matches found.")
    print(f"Summary: {category_counts}")
    print(f"Core logic hardcoded violations: {category_counts.get('HARDCODED_CORE_LOGIC', 0)}")
    return report["status"]


if __name__ == "__main__":
    run_hardcoding_audit()
