"""
M12 Claim Audit Script for JalRakshak-HD.
Scans source code, docs, reports, and manifests for forbidden marketing/unsupported scientific claims.
"""

from __future__ import annotations

import os
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_CLAIMS = [
    r"\bgovernment certified\b",
    r"\b100% accurate\b",
    r"\bfully validated operational\b",
    r"\blive dam failure\b",
    r"\boperational flood warning system\b",
    r"\bdirectly coupled 3D SPH\b",
    r"\bworks for every dam on earth\b",
    r"\bproven real flood simulation\b",
]

ALLOWED_PHRASES = [
    "research screening prototype",
    "hypothetical breach simulation",
    "screening model",
    "real GIS data",
    "actual D-Flow solver output",
    "configuration-driven multi-site architecture",
    "second-site portability validated",
    "direct coupling not implemented",
    "mapped/screened bridge crossings",
    "mapped critical facilities"
]

SCAN_DIRS = ["frontend/src", "backend", "docs", "outputs/reports"]

def run_claim_audit():
    print("=" * 68)
    print("  JalRakshak-HD: M12 Scientific & Marketing Claim Audit")
    print("=" * 68)

    flagged_issues = []
    files_scanned = 0

    for sdir in SCAN_DIRS:
        dir_path = PROJECT_ROOT / sdir
        if not dir_path.exists():
            continue
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith((".ts", ".tsx", ".py", ".md", ".json")):
                    continue
                files_scanned += 1
                fpath = Path(root) / file
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue

                for pattern in FORBIDDEN_CLAIMS:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for m in matches:
                        # Find line number
                        line_num = content[:m.start()].count("\n") + 1
                        flagged_issues.append({
                            "file": str(fpath.relative_to(PROJECT_ROOT)),
                            "line": line_num,
                            "match": m.group(0),
                            "pattern": pattern
                        })

    audit_result = {
        "audit_name": "M12_FINAL_CLAIM_AUDIT",
        "project": "JalRakshak-HD",
        "files_scanned": files_scanned,
        "violations_found": len(flagged_issues),
        "status": "PASS" if len(flagged_issues) == 0 else "FAIL",
        "flagged_issues": flagged_issues,
        "enforced_disclaimers": {
            "primary_disclaimer": "Research screening prototype. The breach scenario is hypothetical; hydraulic results are model outputs and not an official warning.",
            "hirakud_notice": "Production hydraulic simulation not executed for this site. Displaying real GIS terrain, river & reservoir boundaries."
        }
    }

    out_file = PROJECT_ROOT / "outputs" / "validation" / "m12_claim_audit.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_result, f, indent=2)

    print(f"Scanned {files_scanned} files across project.")
    if len(flagged_issues) == 0:
        print("[PASS] 0 unsupported claims or marketing exaggerations detected.")
    else:
        print(f"[FAIL] {len(flagged_issues)} unsupported claims detected.")
        for issue in flagged_issues:
            print(f"  - {issue['file']}:{issue['line']} -> {issue['match']}")

    print(f"Audit report saved to: {out_file}")
    print("=" * 68)
    return len(flagged_issues) == 0

if __name__ == "__main__":
    success = run_claim_audit()
    exit(0 if success else 1)
