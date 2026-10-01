"""JalRakshak-HD Unified Pipeline & Multi-Site Management CLI.

Provides command-line interfaces for site registration, schema validation,
workflow preflight checking, data inventory, and milestone status reporting.
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.site_registry import list_sites, load_site, get_active_site
from backend.app.services.site_validator import validate_site_config
from backend.app.services.workflow_gates import evaluate_workflow_gates
from backend.app.core.site_paths import get_site_paths


def cmd_sites(args):
    """List registered sites."""
    sites = list_sites(project_root)
    active = get_active_site(project_root)
    print("\n" + "=" * 65)
    print(f"  JalRakshak-HD: Registered Study Sites ({len(sites)})")
    print("=" * 65)
    for s in sites:
        is_active = " [ACTIVE]" if s["site_id"] == active else ""
        print(f" * {s['site_id']:<15} : {s['display_name']} ({s.get('state')}, {s.get('river')} River){is_active}")
        print(f"   Status: {s.get('status', 'REGISTERED')} | Enabled: {s.get('enabled')}")
    print("=" * 65 + "\n")


def cmd_validate_site(args):
    """Validate site configuration."""
    site_id = args.site_id
    try:
        site_cfg = load_site(site_id, project_root)
    except Exception as e:
        print(f"[ERROR] Failed to load site '{site_id}': {e}")
        sys.exit(1)

    report = validate_site_config(site_cfg)
    print("\n" + "=" * 65)
    print(f"  Validation Report for Site: {site_cfg.site_id.upper()}")
    print("=" * 65)
    print(f"Status: {'VALID [PASS]' if report.is_valid else 'INVALID [FAIL]'}")
    print(f"Errors: {len(report.errors)} | Warnings: {len(report.warnings)} | Info: {len(report.infos)}")
    print("-" * 65)

    if report.errors:
        print("\nERRORS:")
        for err in report.errors:
            print(f"  [X] {err.category}: {err.message} ({err.field_name})")

    if report.warnings:
        print("\nWARNINGS:")
        for w in report.warnings:
            print(f"  [!] {w.category}: {w.message}")

    if report.infos:
        print("\nINFORMATIONAL:")
        for info in report.infos:
            print(f"  [i] {info.category}: {info.message}")

    print("=" * 65 + "\n")
    if not report.is_valid:
        sys.exit(1)


def cmd_preflight(args):
    """Evaluate workflow readiness gates for a site."""
    site_id = args.site_id
    try:
        site_cfg = load_site(site_id, project_root)
    except Exception as e:
        print(f"[ERROR] Failed to load site '{site_id}': {e}")
        sys.exit(1)

    status = evaluate_workflow_gates(site_cfg, project_root)
    print("\n" + "=" * 65)
    print(f"  Workflow Preflight Gates: {site_cfg.display_name}")
    print("=" * 65)
    print(f"  GATE A - LOCATION            : {status.gate_a_location.value}")
    print(f"  GATE B - TERRAIN             : {status.gate_b_terrain.value}")
    print(f"  GATE C - HYDROLOGY           : {status.gate_c_hydrology.value}")
    print(f"  GATE D - ENGINEERING         : {status.gate_d_engineering.value}")
    print(f"  GATE E - BREACH              : {status.gate_e_breach.value}")
    print(f"  GATE F - HYDRAULIC SOLVER    : {status.gate_f_hydraulic.value}")
    print(f"  GATE G - CONSEQUENCE / HADR  : {status.gate_g_consequence.value}")
    print(f"  GATE H - EARTH OBSERVATION   : {status.gate_h_earth_observation.value}")
    print("-" * 65)
    print(f"  Overall Readiness: {status.overall_readiness}")
    if status.blocking_reasons:
        print("\n  Blocking Reasons:")
        for r in status.blocking_reasons:
            print(f"   - {r}")
    print("=" * 65 + "\n")


def cmd_inventory(args):
    """List site artifacts and datasets."""
    site_id = args.site_id
    paths = get_site_paths(site_id, project_root)
    print("\n" + "=" * 65)
    print(f"  Data Inventory for Site: {site_id.upper()}")
    print("=" * 65)
    dirs_to_check = [
        ("Config Root", paths.config_root),
        ("Terrain Data", paths.terrain),
        ("Hydrology Data", paths.hydrology),
        ("D-Flow FM", paths.dflowfm_data),
        ("DualSPHysics", paths.sph_data),
        ("HADR Exposure", paths.hadr_data),
        ("Earth Observation", paths.gee_data),
        ("Outputs", paths.outputs),
    ]
    for label, dpath in dirs_to_check:
        if dpath.is_dir():
            files = list(dpath.glob("*"))
            print(f"  [{label}] {str(dpath.relative_to(project_root))}")
            for f in files[:5]:
                if f.is_file():
                    print(f"    - {f.name} ({f.stat().st_size:,} bytes)")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more files")
        else:
            print(f"  [{label}] NOT CREATED")
    print("=" * 65 + "\n")


def cmd_status(args):
    """Show comprehensive site status."""
    cmd_validate_site(args)
    cmd_preflight(args)


def main():
    parser = argparse.ArgumentParser(description="JalRakshak-HD Generalized Multi-Site CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # sites
    p_sites = subparsers.add_parser("sites", help="List all registered sites")
    p_sites.set_defaults(func=cmd_sites)

    # validate-site
    p_val = subparsers.add_parser("validate-site", help="Validate a site package configuration")
    p_val.add_argument("site_id", help="Site identifier (e.g. bhavanisagar, hirakud)")
    p_val.set_defaults(func=cmd_validate_site)

    # preflight
    p_pre = subparsers.add_parser("preflight", help="Evaluate workflow readiness gates")
    p_pre.add_argument("site_id", help="Site identifier")
    p_pre.set_defaults(func=cmd_preflight)

    # inventory
    p_inv = subparsers.add_parser("inventory", help="List data assets and directory inventory")
    p_inv.add_argument("site_id", help="Site identifier")
    p_inv.set_defaults(func=cmd_inventory)

    # status
    p_stat = subparsers.add_parser("status", help="Display full validation and gate status")
    p_stat.add_argument("site_id", help="Site identifier")
    p_stat.set_defaults(func=cmd_status)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)


if __name__ == "__main__":
    main()
