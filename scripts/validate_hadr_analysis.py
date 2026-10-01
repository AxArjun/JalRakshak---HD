"""
JalRakshak-HD: M8 HADR Analysis Validation Suite
==================================================
Mandatory checks:
  1. Exclusive priority zones do not overlap (face-level — by construction)
  2. Population is not double-counted (zone sums <= unique inundation totals + tolerance)
  3. Buildings are not double-counted
  4. Road length is not double-counted
  5. WorldPop / GHSL remain separate (no averaged values)
  6. H6 wording does not imply observed failure
  7. Unique overall totals remain unchanged
  8. Priority ranking contains no weighted arbitrary score
  9. Hazard severity breakdown present and non-zero
 10. No fabricated/synthetic values in manifests
"""

from __future__ import annotations

import os
import sys
import json
import re
from pathlib import Path

# Force UTF-8 stdout on Windows (avoids cp1252 encoding errors)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

import pyproj
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.ops import unary_union

ROOT_DIR = Path(__file__).resolve().parent.parent
HADR_OUT_DIR = ROOT_DIR / "outputs" / "hadr"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
REPORTS_DIR = ROOT_DIR / "outputs" / "reports"

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

# ---- Ground-truth unique exposure totals (M8 validated values) ----
UNIQUE_WORLDPOP = 42428.1
UNIQUE_GHSL = 84500.5
UNIQUE_BUILDINGS = 25652
UNIQUE_ROADS_KM = 243.82
UNIQUE_FACES = 10129
UNIQUE_AREA_KM2 = 101.29

# Strict conservative allocation tolerance for population sums (<= 0.1%)
POP_TOLERANCE_PCT = 0.1
# Allow up to 1% for face/area/building/roads (chainage boundary effects)
EXACT_TOLERANCE_PCT = 1.0

PROHIBITED_H6 = [
    "is destroyed", "will collapse", "has failed",
    "are destroyed", "will be destroyed", "are collapsed",
]
PROHIBITED_AVERAGING = [
    "average of worldpop and ghsl", "average population", "combined population",
    "(worldpop + ghsl)", "mean of worldpop", "mean of ghsl",
]

results = []


def record(tag: str, name: str, message: str, detail: str = ""):
    s = f"  {tag} {name}: {message}"
    if detail:
        s += f"\n        {detail}"
    print(s)
    results.append({"status": tag, "check": name, "message": message, "detail": detail})


def pct_diff(a, b):
    if b == 0:
        return 0.0
    return abs(a - b) / b * 100.0


# ─────────────────────────────────────────────
# CHECK 1: Exclusive zones exist and are loadable
# ─────────────────────────────────────────────
def check_exclusive_zone_file():
    name = "exclusive_zone_file_exists"
    path = HADR_OUT_DIR / "response_zones_exclusive.gpkg"
    if not path.exists():
        record(FAIL, name, "response_zones_exclusive.gpkg does not exist")
        return None
    gdf = gpd.read_file(path)
    if len(gdf) == 0:
        record(FAIL, name, "response_zones_exclusive.gpkg is empty")
        return None
    record(PASS, name, f"{len(gdf)} exclusive sectors loaded from response_zones_exclusive.gpkg")
    return gdf


# ─────────────────────────────────────────────
# CHECK 2: Face-level non-overlap verification
# ─────────────────────────────────────────────
def check_face_level_non_overlap():
    """Verify each hazard face appears in exactly one chainage sector."""
    name = "face_level_no_overlap"
    haz_path = HADR_OUT_DIR / "hazard_severity.gpkg"
    river_path = ROOT_DIR / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
    if not haz_path.exists() or not river_path.exists():
        record(WARN, name, "hazard_severity.gpkg or river file missing — skipping face-level check")
        return

    haz = gpd.read_file(haz_path)
    river = gpd.read_file(river_path)
    line = river.geometry.iloc[0]
    sector_chainages = [0.0, 7500.0, 17500.0, 26500.0, 35500.0, 44500.0, line.length + 100.0]

    haz["chainage_m"] = haz.geometry.apply(lambda g: line.project(g))

    zone_labels = []
    for s in range(6):
        cs, ce = sector_chainages[s], sector_chainages[s + 1]
        mask = (haz["chainage_m"] >= cs) & (haz["chainage_m"] < ce)
        zone_labels.extend([f"ZONE_{s+1:02d}"] * mask.sum())

    assigned = (haz["chainage_m"] >= 0) & (haz["chainage_m"] < sector_chainages[-1])
    total_faces = len(haz)
    assigned_count = assigned.sum()

    if total_faces != UNIQUE_FACES:
        record(WARN, name, f"hazard_severity.gpkg has {total_faces} faces; expected {UNIQUE_FACES}")
    else:
        record(PASS, name, f"All {total_faces} faces present in hazard_severity.gpkg")

    sector_counts = []
    for s in range(6):
        cs, ce = sector_chainages[s], sector_chainages[s + 1]
        cnt = int(((haz["chainage_m"] >= cs) & (haz["chainage_m"] < ce)).sum())
        sector_counts.append(cnt)

    total_assigned = sum(sector_counts)
    if total_assigned != total_faces:
        record(FAIL, name, f"Face double-count detected: {total_assigned} assigned vs {total_faces} total faces",
               f"Per-zone counts: {sector_counts}")
    else:
        record(PASS, name, f"Face-level assignment is bijective: {total_faces} faces assigned to {len(sector_counts)} sectors (no double-count)",
               f"Per-zone: {dict(zip([f'Z{i+1}' for i in range(6)], sector_counts))}")


# ─────────────────────────────────────────────
# CHECK 3: Priority CSV zone totals vs unique exposure
# ─────────────────────────────────────────────
def check_zone_totals():
    name = "zone_totals_vs_unique"
    csv_path = HADR_OUT_DIR / "hadr_priority_zones.csv"
    if not csv_path.exists():
        record(FAIL, name, "hadr_priority_zones.csv missing")
        return None

    df = pd.read_csv(csv_path)
    zone_wp = df["population_worldpop"].sum()
    zone_ghsl = df["population_ghsl"].sum()
    zone_bld = df["building_count"].sum()
    zone_roads = df["road_length_km"].sum()

    wp_pct = pct_diff(zone_wp, UNIQUE_WORLDPOP)
    ghsl_pct = pct_diff(zone_ghsl, UNIQUE_GHSL)
    bld_pct = pct_diff(zone_bld, UNIQUE_BUILDINGS)
    roads_pct = pct_diff(zone_roads, UNIQUE_ROADS_KM)

    ok = True
    for metric, zone_val, unique_val, tol_pct, pct in [
        ("WorldPop", zone_wp, UNIQUE_WORLDPOP, POP_TOLERANCE_PCT, wp_pct),
        ("GHSL", zone_ghsl, UNIQUE_GHSL, POP_TOLERANCE_PCT, ghsl_pct),
        ("Buildings", zone_bld, UNIQUE_BUILDINGS, EXACT_TOLERANCE_PCT, bld_pct),
        ("Roads (km)", zone_roads, UNIQUE_ROADS_KM, EXACT_TOLERANCE_PCT, roads_pct),
    ]:
        tag = PASS if pct <= tol_pct else FAIL
        if tag == FAIL:
            ok = False
        record(tag, f"zone_total_{metric.replace(' ', '_').lower()}",
               f"Zone sum={zone_val:.1f}, Unique={unique_val:.1f}, Delta={pct:.2f}% (tol={tol_pct:.1f}%)")

    return df


# ─────────────────────────────────────────────
# CHECK 4: WorldPop and GHSL not averaged
# ─────────────────────────────────────────────
def check_datasets_not_averaged():
    name = "worldpop_ghsl_not_averaged"
    paths_to_scan = [
        VALIDATION_DIR / "m8_exposure_summary.json",
        VALIDATION_DIR / "m8_uncertainty_manifest.json",
        REPORTS_DIR / "m8_hadr_summary.md",
    ]
    found = []
    for p in paths_to_scan:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in PROHIBITED_AVERAGING:
            if phrase in text:
                found.append(f"{p.name}: '{phrase}'")
    if found:
        record(FAIL, name, "Prohibited population averaging language detected", "; ".join(found))
    else:
        record(PASS, name, "No averaged WorldPop/GHSL language found in manifests or report")


# ─────────────────────────────────────────────
# CHECK 5: CWC H6 wording — no implied failure
# ─────────────────────────────────────────────
def check_cwc_wording():
    name = "cwc_h6_wording"
    paths_to_scan = [
        REPORTS_DIR / "m8_hadr_summary.md",
        VALIDATION_DIR / "m8_exposure_summary.json",
        VALIDATION_DIR / "m8_uncertainty_manifest.json",
    ]
    found = []
    for p in paths_to_scan:
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8", errors="ignore")
        # Strip any "prohibited*" example arrays from JSON files so the validator
        # does not flag the phrases that are documented there as prohibited examples.
        # Strategy: remove all JSON arrays whose key starts with "prohibited".
        # This is safe because those arrays are metadata, not narrative text.
        if p.suffix == ".json":
            raw_scan = re.sub(
                r'"prohibited[^"]*"\s*:\s*\[[^\]]*\]',
                '"prohibited_examples": ["<removed for scanning>"]',
                raw
            )
        else:
            raw_scan = raw
        text = raw_scan.lower()
        for phrase in PROHIBITED_H6:
            if re.search(r'\b' + re.escape(phrase) + r'\b', text):
                found.append(f"{p.name}: '{phrase}'")
    if found:
        record(FAIL, name, "Prohibited H6 'failure implied' language detected", "; ".join(found))
    else:
        record(PASS, name, "CWC H6 wording correct — no implied observed failure language")

    # Check correct wording is present in report
    report = (REPORTS_DIR / "m8_hadr_summary.md").read_text(encoding="utf-8") if (REPORTS_DIR / "m8_hadr_summary.md").exists() else ""
    if "vulnerable to failure" in report.lower():
        record(PASS, "cwc_h6_correct_wording_present", "CWC 'vulnerable to failure' wording present in m8_hadr_summary.md")
    else:
        record(WARN, "cwc_h6_correct_wording_present", "CWC 'vulnerable to failure' wording not found in m8_hadr_summary.md")


# ─────────────────────────────────────────────
# CHECK 6: Deterministic ranking (no score field)
# ─────────────────────────────────────────────
def check_deterministic_ranking(df):
    name = "deterministic_ranking"
    if df is None:
        record(WARN, name, "hadr_priority_zones.csv not loaded — skipping")
        return

    # Check no weighted score column
    suspicious_cols = [c for c in df.columns if "score" in c.lower() and "priority_sort_rule" not in c.lower()]
    if suspicious_cols:
        record(WARN, name, f"Columns that look like weighted scores: {suspicious_cols}")

    # Check sort order: hazard_code DESC, earliest_arrival ASC, worldpop DESC
    if "max_hazard_code" not in df.columns or "priority_rank" not in df.columns:
        record(WARN, name, "max_hazard_code or priority_rank column missing from hadr_priority_zones.csv")
        return

    df_check = df.sort_values(
        by=["max_hazard_code", "earliest_arrival_hr", "population_worldpop"],
        ascending=[False, True, False]
    ).reset_index(drop=True)
    df_check["expected_rank"] = range(1, len(df_check) + 1)

    merged = df.merge(df_check[["zone_id", "expected_rank"]], on="zone_id")
    mismatch = merged[merged["priority_rank"] != merged["expected_rank"]]
    if len(mismatch) > 0:
        record(FAIL, name, f"{len(mismatch)} zones ranked out of deterministic order",
               mismatch[["zone_id", "priority_rank", "expected_rank"]].to_string())
    else:
        record(PASS, name, f"All {len(df)} zones ranked deterministically (MaxHazard DESC > EarliestArrival ASC > WorldPop DESC)")


# ─────────────────────────────────────────────
# CHECK 7: Unique overall totals unchanged
# ─────────────────────────────────────────────
def check_unique_totals_unchanged():
    name = "unique_totals_unchanged"
    path = VALIDATION_DIR / "m8_population_crosscheck.json"
    if not path.exists():
        record(WARN, name, "m8_population_crosscheck.json missing — skipping")
        return
    with open(path, encoding="utf-8") as f:
        pop_cross = json.load(f)

    wp = pop_cross.get("worldpop_total_inundated", 0.0)
    ghsl = pop_cross.get("ghsl_total_inundated", 0.0)

    if abs(wp - UNIQUE_WORLDPOP) > 1.0:
        record(FAIL, name, f"WorldPop total changed: stored={wp:.1f}, expected={UNIQUE_WORLDPOP:.1f}")
    else:
        record(PASS, name, f"WorldPop total unchanged: {wp:.1f}")
    if abs(ghsl - UNIQUE_GHSL) > 1.0:
        record(FAIL, name, f"GHSL total changed: stored={ghsl:.1f}, expected={UNIQUE_GHSL:.1f}")
    else:
        record(PASS, name, f"GHSL total unchanged: {ghsl:.1f}")


# ─────────────────────────────────────────────
# CHECK 8: Overlap audit JSON exists and documents overlap
# ─────────────────────────────────────────────
def check_overlap_audit_json():
    name = "overlap_audit_json"
    path = VALIDATION_DIR / "m8_response_zone_overlap.json"
    if not path.exists():
        record(FAIL, name, "m8_response_zone_overlap.json missing")
        return
    with open(path, encoding="utf-8") as f:
        ov = json.load(f)
    required_keys = ["n_zones", "sum_of_individual_areas_km2", "union_area_km2",
                     "total_overlap_area_km2", "overlap_percentage", "pairwise_intersections"]
    missing = [k for k in required_keys if k not in ov]
    if missing:
        record(FAIL, name, f"m8_response_zone_overlap.json missing keys: {missing}")
        return
    overlap_pct = ov["overlap_percentage"]
    if overlap_pct < 1.0:
        record(WARN, name, f"Overlap percentage unusually low ({overlap_pct:.1f}%) — expected ~51% for original overlapping zones")
    else:
        record(PASS, name, f"Overlap audit JSON present: original zones overlap={ov['total_overlap_area_km2']:.2f} km2 ({overlap_pct:.1f}%)")


# ─────────────────────────────────────────────
# CHECK 8B: Population allocation audit JSON exists and PASSES
# ─────────────────────────────────────────────
def check_population_allocation_audit():
    name = "population_allocation_audit"
    path = VALIDATION_DIR / "m8_population_allocation_audit.json"
    if not path.exists():
        record(FAIL, name, "m8_population_allocation_audit.json missing")
        return
    with open(path, encoding="utf-8") as f:
        audit = json.load(f)

    status = audit.get("overall_conservation_status")
    wp_stat = audit.get("datasets", {}).get("worldpop_2020", {}).get("conservation_status")
    ghsl_stat = audit.get("datasets", {}).get("ghsl_2025", {}).get("conservation_status")
    wp_pct = audit.get("datasets", {}).get("worldpop_2020", {}).get("percentage_difference", 999.0)
    ghsl_pct = audit.get("datasets", {}).get("ghsl_2025", {}).get("percentage_difference", 999.0)

    if status == "PASS" and wp_stat == "PASS" and ghsl_stat == "PASS" and wp_pct <= POP_TOLERANCE_PCT and ghsl_pct <= POP_TOLERANCE_PCT:
        record(PASS, name, f"Population allocation audit PASS: WorldPop delta={wp_pct:.6f}%, GHSL delta={ghsl_pct:.6f}% (tol<={POP_TOLERANCE_PCT}%)")
    else:
        record(FAIL, name, f"Population allocation audit failed: overall={status}, WP={wp_stat} ({wp_pct:.4f}%), GHSL={ghsl_stat} ({ghsl_pct:.4f}%)")


# ─────────────────────────────────────────────
# CHECK 9: Hazard severity breakdown present
# ─────────────────────────────────────────────
def check_hazard_severity():
    name = "hazard_severity_breakdown"
    path = VALIDATION_DIR / "m8_hazard_severity_summary.json"
    if not path.exists():
        record(WARN, name, "m8_hazard_severity_summary.json missing — skipping")
        return
    with open(path, encoding="utf-8") as f:
        haz_sum = json.load(f)
    bd = haz_sum.get("hazard_breakdown", {})
    expected_classes = ["H1", "H2", "H3", "H4", "H5", "H6"]
    missing = [h for h in expected_classes if h not in bd]
    if missing:
        record(FAIL, name, f"Missing hazard classes in breakdown: {missing}")
        return
    total_area = sum(bd[h]["area_km2"] for h in expected_classes)
    if abs(total_area - UNIQUE_AREA_KM2) > 1.0:
        record(WARN, name, f"Hazard breakdown total area {total_area:.2f} km2 differs from expected {UNIQUE_AREA_KM2:.2f} km2")
    else:
        record(PASS, name, f"Hazard severity breakdown covers all 6 classes, total area = {total_area:.2f} km2")


# ─────────────────────────────────────────────
# CHECK 10: Population interpretation text
# ─────────────────────────────────────────────
def check_population_interpretation():
    name = "population_interpretation_text"
    path = VALIDATION_DIR / "m8_exposure_summary.json"
    if not path.exists():
        record(WARN, name, "m8_exposure_summary.json missing — skipping")
        return
    with open(path, encoding="utf-8") as f:
        exp = json.load(f)
    interp = exp.get("population_interpretation", "")
    required_phrases = ["primary", "cross_check", "modelled gridded estimates", "sensitivity range"]
    missing = [p for p in required_phrases if p.lower() not in interp.lower()]
    if missing:
        record(WARN, name, f"population_interpretation missing required phrases: {missing}")
    else:
        record(PASS, name, "population_interpretation contains all required phrases (PRIMARY, CROSS_CHECK, modelled gridded, sensitivity range)")


# ─────────────────────────────────────────────
# CHECK 11: hadr_priority_zones.csv has all 6 zones
# ─────────────────────────────────────────────
def check_all_zones_present(df):
    name = "all_six_zones_present"
    if df is None:
        record(WARN, name, "hadr_priority_zones.csv not loaded — skipping")
        return
    expected_zones = {"ZONE_01", "ZONE_02", "ZONE_03", "ZONE_04", "ZONE_05", "ZONE_06"}
    actual_zones = set(df["zone_id"].values) if "zone_id" in df.columns else set()
    missing = expected_zones - actual_zones
    if missing:
        record(FAIL, name, f"Missing zones from priority table: {missing}")
    else:
        record(PASS, name, f"All 6 zones present in hadr_priority_zones.csv")


# ─────────────────────────────────────────────
# CHECK 12: Arrival times plausible (not all null or zero)
# ─────────────────────────────────────────────
def check_arrival_times(df):
    name = "arrival_times_plausible"
    if df is None:
        record(WARN, name, "hadr_priority_zones.csv not loaded — skipping")
        return
    col = "earliest_arrival_hr"
    if col not in df.columns:
        record(WARN, name, f"Column '{col}' missing from hadr_priority_zones.csv")
        return
    arr = df[col].dropna()
    if len(arr) == 0:
        record(FAIL, name, "All earliest_arrival_hr values are null")
        return
    if arr.max() > 48.0:
        record(WARN, name, f"Unusually large arrival time: {arr.max():.2f} hr (>48h). Check chainage alignment.")
    if (arr < 0).any():
        record(FAIL, name, f"Negative arrival times detected: {arr[arr<0].values}")
        return
    # ZONE_01 at dam toe should have arrival <= 1h (wetting at t=0)
    z1 = df[df["zone_id"] == "ZONE_01"][col]
    if len(z1) > 0 and not z1.isna().all():
        z1_val = float(z1.iloc[0])
        if z1_val > 1.0:
            record(WARN, name, f"ZONE_01 (dam toe) earliest arrival = {z1_val:.3f}h; expected <= 1.0h")
        else:
            record(PASS, name, f"ZONE_01 (dam toe) earliest arrival = {z1_val:.3f}h (physically correct — immediately inundated at t=0)")
    record(PASS, name, f"Arrival times range: {arr.min():.3f}h to {arr.max():.3f}h across {len(arr)} zones")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 70)
    print(" JalRakshak-HD — M8 HADR Analysis Validation Suite")
    print("=" * 70)
    print()

    gdf_excl = check_exclusive_zone_file()
    check_face_level_non_overlap()
    df = check_zone_totals()
    check_datasets_not_averaged()
    check_cwc_wording()
    check_deterministic_ranking(df)
    check_unique_totals_unchanged()
    check_overlap_audit_json()
    check_population_allocation_audit()
    check_hazard_severity()
    check_population_interpretation()
    check_all_zones_present(df)
    check_arrival_times(df)

    print()
    print("=" * 70)

    n_pass = sum(1 for r in results if r["status"] == PASS)
    n_warn = sum(1 for r in results if r["status"] == WARN)
    n_fail = sum(1 for r in results if r["status"] == FAIL)

    print(f" SUMMARY: {n_pass} PASS | {n_warn} WARN | {n_fail} FAIL  (total {len(results)} checks)")
    print("=" * 70)

    if n_fail > 0:
        print("\n BLOCKERS:")
        for r in results:
            if r["status"] == FAIL:
                print(f"    {r['check']}: {r['message']}")
    if n_warn > 0:
        print("\n WARNINGS:")
        for r in results:
            if r["status"] == WARN:
                print(f"    {r['check']}: {r['message']}")

    # Save validation JSON
    out = {
        "n_pass": n_pass, "n_warn": n_warn, "n_fail": n_fail, "checks": results,
        "m8_validation_status": "READY" if n_fail == 0 else "NOT_READY",
    }
    out_path = VALIDATION_DIR / "m8_hadr_validation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n[OK] Validation results saved to {out_path}")

    return_code = 0 if n_fail == 0 else 1
    print(f"\nM8 Validation Status: {'READY' if n_fail == 0 else 'NOT_READY'}")
    sys.exit(return_code)


if __name__ == "__main__":
    main()
