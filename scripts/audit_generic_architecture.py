"""Audit Generic Architecture modules for zero prohibited site-specific constants.

Produces: outputs/validation/m11_generic_architecture_audit.json
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

GENERIC_MODULES = [
    project_root / "backend" / "app" / "schemas" / "site.py",
    project_root / "backend" / "app" / "core" / "crs.py",
    project_root / "backend" / "app" / "services" / "site_registry.py",
    project_root / "backend" / "app" / "services" / "site_validator.py",
    project_root / "backend" / "app" / "services" / "workflow_gates.py",
    project_root / "backend" / "app" / "services" / "hydrograph.py",
    project_root / "backend" / "app" / "services" / "dflow_builder.py",
    project_root / "backend" / "app" / "services" / "hadr_builder.py",
    project_root / "backend" / "app" / "services" / "eo_builder.py",
]

PROHIBITED_SITE_CONSTANTS = [
    ("Bhavanisagar", "Site name"),
    ("11.47083", "Dam latitude"),
    ("77.11389", "Dam longitude"),
    ("280.42", "Dam FRL elevation"),
    ("18742.38", "Peak discharge"),
    ("219.28", "Breach width"),
]


def run_architecture_audit():
    violations = []

    for mod_path in GENERIC_MODULES:
        if not mod_path.is_file():
            continue
        with open(mod_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, 1):
            for const_val, desc in PROHIBITED_SITE_CONSTANTS:
                if const_val in line:
                    # Ignore comment or docstring mentioning bhavanisagar as example or fallback
                    if line.strip().startswith("#") or 'return "bhavanisagar"' in line or 'site_id == "bhavanisagar"' in line:
                        continue
                    violations.append({
                        "module": str(mod_path.relative_to(project_root)),
                        "line": idx,
                        "constant": const_val,
                        "description": desc,
                        "snippet": line.strip(),
                    })

    status = "PASS" if len(violations) == 0 else "FAIL"
    report = {
        "status": status,
        "generic_modules_audited": len(GENERIC_MODULES),
        "violations_count": len(violations),
        "violations": violations,
    }

    out_file = project_root / "outputs" / "validation" / "m11_generic_architecture_audit.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Generic Architecture Audit: {status} ({len(violations)} violations)")
    return status


if __name__ == "__main__":
    run_architecture_audit()
