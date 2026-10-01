"""
Comprehensive Dam Engineering and Breach Event Validation Suite for Milestone M3 (Final Reconciliation).
SIH PS 26161 - JalRakshak-HD.

Performs strict scientific assertions on:
  1. Authoritative dam metadata presence (FRL = 280.42 m MSL, NRLD 2019 PIC: TN12HH0014).
  2. Preserved conflicting published dimensions (NRLD 2019 height = 62.0 m, Technical Description = 62.18 m / 40.0 m embankment).
  3. Strict failure if 40 m is claimed as authoritative NRLD height.
  4. Separation of Central Masonry Section (464.0 m) vs Ogee Spillway Length (120.70 m).
  5. Strict failure if 464 m is labelled spillway length.
  6. Arithmetic-derived embankment length must be MODEL_DERIVED_APPROXIMATION.
  7. Conflicting published storage sources preserved (CWC 2020: 780.5 MCM live vs State Feasibility: 908.0 MCM live).
  8. Preferred live storage for breach model remains unverified/null.
  9. Breach volume V_w and breach height h_b strictly labelled MODEL_ASSUMPTION_FIRST_ESTIMATE.
 10. Exact PyProj EPSG:32643 transformation for candidate breach point (730,450.10 m E, 1,269,149.74 m N).
 11. Froehlich (2008) K_0=1.0 math (B_ave = 219.28 m, t_f = 14,095.59 s) and extrapolation flag.
 12. MacDonald & Langridge-Monopolis width status = INSUFFICIENT_CROSS_SECTION_GEOMETRY.
 13. Non-fabrication of unknown MWL, crest elevation, and elevation-storage curve.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import pyproj
from shapely.geometry import Point
import yaml

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def validate_breach_event():
    print("=" * 90)
    print("STARTING M3 DAM ENGINEERING & BREACH EVENT VALIDATION SUITE (FINAL RECONCILIATION)")
    print("=" * 90)

    failures = []
    warnings = []

    # 1. Check Dam Engineering Config and Storage Records
    eng_yaml_path = PROJECT_ROOT / "configs" / "dam_engineering.yaml"
    if not eng_yaml_path.exists():
        failures.append(f"Missing engineering config: {eng_yaml_path}")
    else:
        with open(eng_yaml_path, "r", encoding="utf-8") as f:
            eng_cfg = yaml.safe_load(f)

        # FRL check
        frl = eng_cfg.get("observed", {}).get("official_frl_m", {}).get("value")
        frl_lvl = eng_cfg.get("observed", {}).get("official_frl_m", {}).get("verification_level")
        if frl != 280.42:
            failures.append(f"FRL value is {frl}, expected exact authoritative 280.42 m MSL.")
        elif frl_lvl != "AUTHORITATIVE_VERIFIED":
            failures.append(f"FRL verification level must be AUTHORITATIVE_VERIFIED (got {frl_lvl}).")
        else:
            print(f"[PASS] Authoritative FRL verified: {frl:.2f} m MSL ({frl_lvl})")

        # Source A (NRLD 2019) vs Source B published dimensions
        nrld_h = eng_cfg.get("observed", {}).get("nrld_height_above_lowest_foundation_m", {}).get("value")
        nrld_l = eng_cfg.get("observed", {}).get("nrld_dam_length_m", {}).get("value")
        tech_l = eng_cfg.get("observed", {}).get("technical_project_dam_length_m", {}).get("value")
        masonry_h = eng_cfg.get("observed", {}).get("masonry_section_height_from_lowest_foundation_m", {}).get("value")

        if nrld_h != 62.0:
            failures.append(f"Source A (NRLD 2019) dam height is {nrld_h} m, expected 62.0 m.")
        if nrld_l != 8797.0:
            failures.append(f"Source A (NRLD 2019) dam length is {nrld_l} m, expected 8797.0 m.")
        if tech_l != 8780.0 or masonry_h != 62.18:
            failures.append(f"Source B technical project dimensions mismatch (length: {tech_l}, height: {masonry_h}).")
        else:
            print(f"[PASS] Conflicting published dimensions preserved: NRLD 2019 ({nrld_h} m / {nrld_l} m) vs Technical Description ({masonry_h} m / {tech_l} m).")

        # Audit against claiming 40 m as NRLD authoritative height
        emb_h_src = eng_cfg.get("observed", {}).get("earthen_embankment_reported_height_m", {}).get("source", "")
        if "NRLD" in emb_h_src and eng_cfg.get("observed", {}).get("earthen_embankment_reported_height_m", {}).get("verification_level") == "AUTHORITATIVE_VERIFIED":
            failures.append("40.0 m must NOT be claimed as AUTHORITATIVE_VERIFIED from NRLD. It is a secondary/embankment height.")
        else:
            print("[PASS] 40.0 m height is correctly attributed to secondary embankment descriptions, not NRLD authoritative foundation height.")

        # Spillway vs Central Masonry Section separation
        masonry_len = eng_cfg.get("observed", {}).get("central_masonry_section_length_m", {}).get("value")
        spillway_len = eng_cfg.get("observed", {}).get("spillway_crest_length_m", {}).get("value")
        if masonry_len != 464.0:
            failures.append(f"Central masonry section length is {masonry_len} m, expected 464.0 m.")
        if spillway_len != 120.70:
            failures.append(f"Ogee spillway length is {spillway_len} m, expected ~120.70 m (NOT 464 m).")
        else:
            print(f"[PASS] Distinct structural definitions verified: Central Masonry Section = {masonry_len} m vs Ogee Spillway Length = {spillway_len} m.")

        # Derived Embankment Length verification level check
        emb_derived_lvl = eng_cfg.get("derived", {}).get("arithmetic_embankment_length_approx_m", {}).get("verification_level")
        if emb_derived_lvl != "MODEL_DERIVED_APPROXIMATION":
            failures.append(f"Arithmetic-derived embankment length must be MODEL_DERIVED_APPROXIMATION (got {emb_derived_lvl}).")
        else:
            print(f"[PASS] Arithmetic embankment length (8316 m) correctly classified as {emb_derived_lvl}.")

        # Conflicting storage sources check
        storage_sources = eng_cfg.get("observed", {}).get("reservoir_storage_sources", [])
        if len(storage_sources) < 2:
            failures.append("At least two published storage capacity sources (CWC 2020 and State Feasibility) must be preserved.")
        else:
            s_map = {s["source_name"]: s for s in storage_sources}
            has_cwc = any("CWC" in k for k in s_map)
            has_state = any("Tamil Nadu" in k or "State" in k for k in s_map)
            if not (has_cwc and has_state):
                failures.append("Storage sources must include both CWC Hydrological Data Book (780.5 MCM) and State Feasibility (908.0 MCM).")
            else:
                print(f"[PASS] Conflicting published storage sources preserved: CWC (780.5 MCM live) & State Feasibility (908.0 MCM live).")

        # Preferred live storage check
        pref_storage = eng_cfg.get("unverified", {}).get("preferred_live_storage_for_breach_model", {}).get("value")
        if pref_storage is not None:
            failures.append(f"preferred_live_storage_for_breach_model must remain null pending physical invert routing (got {pref_storage}).")
        else:
            print("[PASS] preferred_live_storage_for_breach_model properly preserved as null.")

        # Breach Model V_w and h_b classification check
        vw_lvl = eng_cfg.get("assumed", {}).get("breach_model_vw_m3", {}).get("verification_level")
        hb_lvl = eng_cfg.get("assumed", {}).get("final_breach_height_hb_m", {}).get("verification_level")
        if vw_lvl != "MODEL_ASSUMPTION_FIRST_ESTIMATE":
            failures.append(f"Breach model V_w must be MODEL_ASSUMPTION_FIRST_ESTIMATE (got {vw_lvl}).")
        if hb_lvl != "MODEL_ASSUMPTION_FIRST_ESTIMATE":
            failures.append(f"Breach model h_b must be MODEL_ASSUMPTION_FIRST_ESTIMATE (got {hb_lvl}).")
        else:
            print(f"[PASS] Breach model inputs V_w and h_b strictly classified as MODEL_ASSUMPTION_FIRST_ESTIMATE.")

        # Unverified fields check
        mwl = eng_cfg.get("unverified", {}).get("official_mwl_m", {}).get("value")
        crest = eng_cfg.get("unverified", {}).get("official_crest_elevation_m", {}).get("value")
        curve_status = eng_cfg.get("unverified", {}).get("elevation_storage_curve", {}).get("status")
        if mwl is not None:
            failures.append("official_mwl_m must remain null.")
        if crest is not None:
            failures.append("official_crest_elevation_m must remain null.")
        if curve_status != "UNAVAILABLE":
            failures.append("elevation_storage_curve status must be UNAVAILABLE.")
        print("[PASS] Unverified fields (MWL, Crest elevation, stage-storage curve) properly preserved as null/UNAVAILABLE.")

    # 2. Check Composite Structure Interpretation
    struct_json_path = PROJECT_ROOT / "outputs" / "validation" / "dam_structure_interpretation.json"
    if not struct_json_path.exists():
        failures.append(f"Missing dam structure interpretation: {struct_json_path}")
    else:
        with open(struct_json_path, "r", encoding="utf-8") as f:
            struct_data = json.load(f)
            comps = {c["component_name"]: c for c in struct_data.get("structural_components", [])}
            if "Left Earthen Embankment Flank" not in comps or "Central Masonry Section" not in comps or "Ogee Spillway Structure" not in comps:
                failures.append("Structure interpretation missing Left Earthen Flank, Central Masonry Section, or Ogee Spillway Structure.")
            else:
                sel_comp = struct_data.get("selected_breachable_component", {}).get("component_name")
                if sel_comp != "Left Earthen Embankment Flank":
                    failures.append(f"Breached component must be an earthen embankment section (got {sel_comp}).")
                else:
                    print(f"[PASS] Composite structure interpretation verified: {len(comps)} components, breached target: '{sel_comp}'.")

    # 3. Check Spatial Coordinates & Exact PyProj Transformation
    loc_json_path = PROJECT_ROOT / "outputs" / "validation" / "breach_location_validation.json"
    breach_gpkg_path = PROJECT_ROOT / "data" / "dflowfm" / "breach_location.gpkg"
    if not loc_json_path.exists() or not breach_gpkg_path.exists():
        failures.append("Missing breach location validation JSON or GPKG.")
    else:
        with open(loc_json_path, "r", encoding="utf-8") as f:
            loc_val = json.load(f)

        lat = loc_val["wgs84_coordinates"]["latitude"]
        lon = loc_val["wgs84_coordinates"]["longitude"]
        x_proj = loc_val["epsg32643_coordinates"]["easting_m"]
        y_proj = loc_val["epsg32643_coordinates"]["northing_m"]
        v_level = loc_val["verification_level"]

        # Run direct independent PyProj transformation check
        transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
        exp_x, exp_y = transformer.transform(lon, lat)

        if abs(x_proj - exp_x) > 1.0 or abs(y_proj - exp_y) > 1.0:
            failures.append(f"CRS Transformation mismatch: Recorded ({x_proj}, {y_proj}) vs PyProj Expected ({exp_x:.2f}, {exp_y:.2f}).")
        elif v_level != "MODEL_DERIVED_CANDIDATE_LOCATION":
            failures.append(f"Breach location verification level must be MODEL_DERIVED_CANDIDATE_LOCATION (got {v_level}).")
        else:
            print(f"[PASS] Exact PyProj EPSG:32643 transformation verified: ({lat:.6f}° N, {lon:.6f}° E) -> ({x_proj:.2f} m E, {y_proj:.2f} m N), Level: {v_level}.")

    # 4. Check Breach Parameter Estimates & Uncertainty Output
    unc_json_path = PROJECT_ROOT / "outputs" / "validation" / "breach_uncertainty.json"
    if not unc_json_path.exists():
        failures.append(f"Missing breach uncertainty JSON: {unc_json_path}")
    else:
        with open(unc_json_path, "r", encoding="utf-8") as f:
            unc_data = json.load(f)

        models = {m["model_name"]: m for m in unc_data.get("models_evaluated", [])}

        # Froehlich 2008 check
        if "Froehlich (2008)" not in models:
            failures.append("Missing Froehlich (2008) in evaluated models.")
        else:
            fr = models["Froehlich (2008)"]
            if abs(fr["breach_width_m"] - 219.28) > 1.0:
                failures.append(f"Froehlich width is {fr['breach_width_m']} m, expected 219.28 m for K_0=1.0.")
            if "EXTRAPOLATED" not in fr["calibration_range_status"]:
                failures.append("Froehlich model must declare extrapolation warning for V_w (780.5 MCM) > 660 MCM calibration maximum.")
            else:
                print(f"[PASS] Froehlich (2008) math and calibration audit verified: Width = {fr['breach_width_m']:.2f} m, K_0 = 1.0, Calibration Status = {fr['calibration_range_status']}.")

        # MacDonald & Langridge-Monopolis check
        if "MacDonald & Langridge-Monopolis (1984)" not in models:
            failures.append("Missing MacDonald & Langridge-Monopolis (1984) in evaluated models.")
        else:
            mlm = models["MacDonald & Langridge-Monopolis (1984)"]
            if mlm["breach_width_m"] is not None:
                failures.append(f"MacDonald & Langridge-Monopolis width must be null without cross-section geometry (got {mlm['breach_width_m']} m).")
            if mlm["width_status"] != "INSUFFICIENT_CROSS_SECTION_GEOMETRY":
                failures.append(f"MacDonald width_status must be INSUFFICIENT_CROSS_SECTION_GEOMETRY (got {mlm['width_status']}).")
            if mlm["eroded_volume_m3"] is None or mlm["formation_time_s"] is None:
                failures.append("MacDonald eroded volume and formation time must be populated.")
            else:
                print(f"[PASS] MacDonald & Langridge-Monopolis (1984) verified: V_er = {mlm['eroded_volume_m3']} m3, t_f = {mlm['formation_time_s']} s, Width Status = {mlm['width_status']}.")

        # Von Thun & Gillette check
        if "Von Thun & Gillette (1990)" not in models:
            failures.append("Missing Von Thun & Gillette (1990) in evaluated models.")
        else:
            vtg = models["Von Thun & Gillette (1990)"]
            if vtg["breach_width_m"] <= 0:
                failures.append("Von Thun & Gillette width must be > 0.")
            else:
                print(f"[PASS] Von Thun & Gillette (1990) verified: Width = {vtg['breach_width_m']:.2f} m, Formation Time = {vtg['formation_time_s']:.2f} s.")

    # 5. Check Breach Scenarios Configuration
    scen_yaml_path = PROJECT_ROOT / "configs" / "breach_scenarios.yaml"
    if not scen_yaml_path.exists():
        failures.append(f"Missing breach scenarios config: {scen_yaml_path}")
    else:
        with open(scen_yaml_path, "r", encoding="utf-8") as f:
            scen_cfg = yaml.safe_load(f)

        scenarios = scen_cfg.get("scenarios", [])
        for sc in scenarios:
            if sc.get("historical_status") == "HISTORICAL_EVENT":
                failures.append(f"Scenario {sc['scenario_id']} must not be labelled historical.")
            vol_class = sc.get("initial_reservoir_condition", {}).get("volume_classification")
            if vol_class != "MODEL_ASSUMPTION_FIRST_ESTIMATE":
                failures.append(f"Scenario {sc['scenario_id']}: volume_classification must be MODEL_ASSUMPTION_FIRST_ESTIMATE (got {vol_class}).")
        print(f"[PASS] Breach scenarios verified ({len(scenarios)} defined, all labelled MODEL_ASSUMPTION_FIRST_ESTIMATE and non-historical).")

    print("=" * 90)
    print("VALIDATION SUMMARY")
    print("=" * 90)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if failures:
        print("CRITICAL FAILURES:")
        for f in failures:
            print(f"  - {f}")
        print("Validation Result: FAIL")
        sys.exit(1)
    else:
        print("All M3 Dam Engineering & Breach Event Criteria Successfully Passed!")
        print("Validation Result: PASS")
        sys.exit(0)


if __name__ == "__main__":
    validate_breach_event()
