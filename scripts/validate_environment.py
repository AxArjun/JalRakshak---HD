#!/usr/bin/env python3
"""JalRakshak-HD Environment & Dependency Validation Script.

Non-destructively inspects Python runtime, geospatial packages, Earth Engine API,
database drivers, project directory structure, and external scientific solver executables.
Exits with code 0 on full validation pass, or non-zero on failure.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import List, NamedTuple, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class CheckResult(NamedTuple):
    component: str
    category: str
    status: str  # "PASS", "FAIL", "WARN"
    evidence: str
    mandatory: bool = True


def check_python_version() -> CheckResult:
    """Validate Python version is 3.12.x."""
    major, minor, micro = sys.version_info[:3]
    version_str = f"{major}.{minor}.{micro}"
    if major == 3 and minor == 12:
        return CheckResult(
            component="Python Runtime",
            category="Runtime",
            status="PASS",
            evidence=f"Python {version_str} ({sys.executable})",
            mandatory=True,
        )
    else:
        return CheckResult(
            component="Python Runtime",
            category="Runtime",
            status="FAIL",
            evidence=f"Found Python {version_str}, expected 3.12.x",
            mandatory=True,
        )


def check_python_package(module_name: str, display_name: str, min_version: str | None = None) -> CheckResult:
    """Check whether a Python package can be imported and query its version."""
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, "__version__", "Installed")
        return CheckResult(
            component=display_name,
            category="Python Package",
            status="PASS",
            evidence=f"v{version} (module '{module_name}')",
            mandatory=True,
        )
    except ImportError as e:
        return CheckResult(
            component=display_name,
            category="Python Package",
            status="FAIL",
            evidence=f"ImportError: {e}",
            mandatory=True,
        )


def check_executable(path_str: str, display_name: str) -> CheckResult:
    """Check existence of an external executable without running a heavy simulation."""
    p = Path(path_str)
    if p.is_file():
        size_mb = p.stat().st_size / (1024 * 1024)
        return CheckResult(
            component=display_name,
            category="External Solver",
            status="PASS",
            evidence=f"Found ({size_mb:.2f} MB) at {p}",
            mandatory=True,
        )
    else:
        return CheckResult(
            component=display_name,
            category="External Solver",
            status="FAIL",
            evidence=f"Executable not found at {path_str}",
            mandatory=True,
        )


def check_directory(path: Path, display_name: str) -> CheckResult:
    """Verify that a required project directory exists."""
    if path.is_dir():
        return CheckResult(
            component=display_name,
            category="Directory Structure",
            status="PASS",
            evidence=f"Directory exists: {path}",
            mandatory=True,
        )
    else:
        return CheckResult(
            component=display_name,
            category="Directory Structure",
            status="FAIL",
            evidence=f"Missing directory: {path}",
            mandatory=True,
        )


def run_all_checks() -> Tuple[List[CheckResult], bool]:
    """Execute all system and environment verification checks."""
    results: List[CheckResult] = []

    # 1. Python Runtime
    results.append(check_python_version())

    # 2. Geospatial and Core Python Packages
    packages = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("scipy", "SciPy"),
        ("shapely", "Shapely"),
        ("pyproj", "PyProj"),
        ("geopandas", "GeoPandas"),
        ("rasterio", "Rasterio"),
        ("xarray", "xarray"),
        ("netCDF4", "netCDF4"),
        ("h5py", "h5py"),
        ("matplotlib", "Matplotlib"),
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("yaml", "PyYAML"),
    ]
    for mod_name, disp_name in packages:
        results.append(check_python_package(mod_name, disp_name))

    # 3. Earth Engine API
    results.append(check_python_package("ee", "Google Earth Engine API (ee)"))

    # 4. PostgreSQL Driver
    results.append(check_python_package("psycopg", "PostgreSQL Driver (psycopg 3)"))

    # 5. External Solvers (Delft3D FM & DualSPHysics)
    external_tools = [
        (
            r"C:\Program Files\Deltares\Delft3D FM Suite 2026.02 OpenHMWQ\plugins\DeltaShell.Dimr\kernels\x64\bin\dflowfm-cli.exe",
            "D-Flow FM CLI",
        ),
        (
            r"C:\Program Files\Deltares\Delft3D FM Suite 2026.02 OpenHMWQ\plugins\DeltaShell.Dimr\kernels\x64\bin\dimr.exe",
            "Deltares DIMR Executable",
        ),
        (
            r"C:\DualSPHysics\DualSPHysics_v5.4\bin\windows\DualSPHysics5.4CPU_win64.exe",
            "DualSPHysics 5.4 CPU Solver",
        ),
        (
            r"C:\DualSPHysics\DualSPHysics_v5.4\bin\windows\GenCase_win64.exe",
            "DualSPHysics GenCase Geometry Tool",
        ),
    ]
    for exe_path, disp_name in external_tools:
        results.append(check_executable(exe_path, disp_name))

    # 6. Project Directory Structure
    required_directories = [
        PROJECT_ROOT / "backend" / "app" / "api",
        PROJECT_ROOT / "backend" / "app" / "core",
        PROJECT_ROOT / "backend" / "app" / "models",
        PROJECT_ROOT / "backend" / "app" / "schemas",
        PROJECT_ROOT / "backend" / "app" / "services",
        PROJECT_ROOT / "backend" / "tests",
        PROJECT_ROOT / "frontend",
        PROJECT_ROOT / "configs",
        PROJECT_ROOT / "docs",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "terrain",
        PROJECT_ROOT / "data" / "hydrology",
        PROJECT_ROOT / "data" / "gee",
        PROJECT_ROOT / "data" / "dflowfm",
        PROJECT_ROOT / "data" / "sph",
        PROJECT_ROOT / "data" / "hadr",
        PROJECT_ROOT / "data" / "observations",
        PROJECT_ROOT / "outputs" / "maps",
        PROJECT_ROOT / "outputs" / "hydrographs",
        PROJECT_ROOT / "outputs" / "simulations",
        PROJECT_ROOT / "outputs" / "validation",
        PROJECT_ROOT / "outputs" / "reports",
        PROJECT_ROOT / "logs",
    ]
    for d in required_directories:
        results.append(check_directory(d, f"Dir: {d.relative_to(PROJECT_ROOT)}"))

    all_passed = all(
        r.status == "PASS" or (not r.mandatory and r.status != "FAIL") for r in results
    )
    return results, all_passed


def print_table(results: List[CheckResult]) -> None:
    """Format and print verification summary table."""
    col1_w = 40
    col2_w = 10
    col3_w = 65

    header = f"{'Component':<{col1_w}} | {'Status':<{col2_w}} | {'Evidence':<{col3_w}}"
    divider = f"{'-'*col1_w}-+-{'-'*col2_w}-+-{'-'*col3_w}"

    print("\n" + "=" * len(divider))
    print(" JalRakshak-HD — Milestone M0 Environment Verification")
    print("=" * len(divider))
    print(header)
    print(divider)

    current_cat = ""
    for r in results:
        if r.category != current_cat:
            current_cat = r.category
            print(f"[{current_cat.upper()}]")
        print(f"{r.component:<{col1_w}} | {r.status:<{col2_w}} | {r.evidence:<{col3_w}}")

    print(divider)


def main() -> int:
    results, all_passed = run_all_checks()
    print_table(results)

    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")

    print(f"\nSummary: {passed}/{total} checks passed, {failed} failed.")
    if all_passed:
        print("\n>>> ALL MANDATORY CHECKS PASSED. Environment locked for M0. <<<\n")
        return 0
    else:
        print("\n>>> ENVIRONMENT CHECK FAILED. Missing mandatory components. <<<\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
