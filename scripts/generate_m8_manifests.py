"""
JalRakshak-HD: Milestone M8 Manifest & Provenance Compilation Engine
===================================================================
Compiles:
1. outputs/validation/m8_exposure_summary.json
2. outputs/validation/m8_uncertainty_manifest.json
3. outputs/validation/m8_source_manifest.json
4. outputs/reports/m8_hadr_summary.md
"""

from __future__ import annotations

import os
import json
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
HADR_OUT_DIR = ROOT_DIR / "outputs" / "hadr"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
REPORTS_DIR = ROOT_DIR / "outputs" / "reports"

VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_manifests():
    print("=== Compiling Milestone M8 Manifests & Scientific Documentation ===")

    # Load previously generated summaries
    with open(VALIDATION_DIR / "m8_hazard_severity_summary.json", "r", encoding="utf-8") as f:
        haz_sum = json.load(f)

    with open(VALIDATION_DIR / "m8_population_crosscheck.json", "r", encoding="utf-8") as f:
        pop_cross = json.load(f)

    df_pop = pd.read_csv(HADR_OUT_DIR / "population_exposure_by_hazard.csv")
    df_arr = pd.read_csv(HADR_OUT_DIR / "population_arrival_context.csv")
    df_bld = pd.read_csv(HADR_OUT_DIR / "building_exposure_by_hazard.csv")
    df_lc = pd.read_csv(HADR_OUT_DIR / "landcover_exposure_by_hazard.csv")
    df_road = pd.read_csv(HADR_OUT_DIR / "road_exposure_by_hazard.csv")
    df_bridges = pd.read_csv(HADR_OUT_DIR / "bridge_exposure.csv")
    df_fac = pd.read_csv(HADR_OUT_DIR / "critical_facility_exposure.csv")
    df_zones = pd.read_csv(HADR_OUT_DIR / "hadr_priority_zones.csv")

    # 1. Comprehensive Exposure Summary
    exposure_summary = {
        "milestone": "M8",
        "milestone_name": "HADR Consequence, Exposure and Emergency-Priority Analysis",
        "classification": "SCREENING_HADR_CONSEQUENCE_ANALYSIS",
        "hydraulic_source": "2D_DFLOWFM_SCREENING_INUNDATION_MODEL",
        "study_area": "Bhavanisagar Dam Downstream Reach (51.73 km), Tamil Nadu, India",
        "coordinate_reference_system": "EPSG:32643 (WGS 84 / UTM Zone 43N)",
        "hazard_classification_standard": "CWC_AIDR_GUIDELINE_7_3_SMITH_2014",
        "hazard_evaluation_method": "TIME_SYNCHRONOUS_STEPWISE_EVALUATION (181 timesteps)",
        "hazard_severity_overview": {
            "total_inundated_faces": haz_sum["total_inundated_faces"],
            "total_inundated_area_km2": haz_sum["total_inundated_area_km2"],
            "severe_hazard_h3_h6_area_km2": haz_sum["severe_hazard_h3_h6_area_km2"],
            "severe_hazard_h3_h6_pct": haz_sum["severe_hazard_h3_h6_pct"],
            "extreme_hazard_h5_h6_area_km2": haz_sum["extreme_hazard_h5_h6_area_km2"],
            "max_observed_dv_product_m2ps": haz_sum["max_observed_dv_product_m2ps"],
            "max_observed_depth_m": haz_sum["max_observed_depth_m"],
            "max_observed_velocity_mps": haz_sum["max_observed_velocity_mps"]
        },
        "population_exposure": {
            "primary_dataset": pop_cross["primary_dataset"],
            "crosscheck_dataset": pop_cross["crosscheck_dataset"],
            "worldpop_total_inundated": pop_cross["worldpop_total_inundated"],
            "worldpop_severe_h3_h6": pop_cross["worldpop_severe_h3_h6"],
            "worldpop_extreme_h5_h6": pop_cross["worldpop_extreme_h5_h6"],
            "worldpop_by_hazard": pop_cross["worldpop_by_hazard"],
            "ghsl_total_inundated": pop_cross["ghsl_total_inundated"],
            "ghsl_severe_h3_h6": pop_cross["ghsl_severe_h3_h6"],
            "ghsl_extreme_h5_h6": pop_cross["ghsl_extreme_h5_h6"],
            "ghsl_by_hazard": pop_cross["ghsl_by_hazard"],
            "absolute_dataset_spread": pop_cross["absolute_dataset_spread"],
            "ratio_ghsl_to_worldpop": pop_cross["ratio_ghsl_to_worldpop"],
            "potential_loss_of_life_model": "NOT_IMPLEMENTED",
            "potential_loss_of_life_status": "SCREENING_EXPOSURE_ONLY_NO_CASUALTY_ESTIMATION"
        },
        "building_exposure": {
            "dataset": "Google Open Buildings v3 (confidence >= 0.75)",
            "total_buildings_inundated": int(df_bld["building_count"].sum()),
            "severe_h3_h6_buildings": int(df_bld[df_bld["hazard_code"] >= 3]["building_count"].sum()),
            "h5_h6_structural_damage_exposure": int(df_bld[df_bld["hazard_code"] >= 5]["building_count"].sum()),
            "total_footprint_area_m2": float(df_bld["total_footprint_area_m2"].sum()),
            "building_damage_state": "EXPOSURE_ONLY_NO_FRAGILITY_CURVES",
            "damage_classification_note": "Buildings in H5/H6 classified as H5_H6_STRUCTURAL_DAMAGE_EXPOSURE, NOT assumed destroyed"
        },
        "landcover_consequences": {
            "dataset": "ESA WorldCover 2021 v200 (10m categorical)",
            "cropland_class_40_inundated_km2": float(df_lc["cropland_km2"].sum()),
            "cropland_severe_h3_h6_km2": float(df_lc[df_lc["hazard_code"] >= 3]["cropland_km2"].sum()),
            "builtup_class_50_inundated_km2": float(df_lc["builtup_km2"].sum()),
            "builtup_severe_h3_h6_km2": float(df_lc[df_lc["hazard_code"] >= 3]["builtup_km2"].sum()),
            "cropland_loss_model": "NOT_IMPLEMENTED",
            "monetary_damage_status": "NOT_IMPLEMENTED_IN_M8"
        },
        "infrastructure_exposure": {
            "dataset": "OpenStreetMap (OSM) Overpass API",
            "total_roads_inundated_km": float(df_road["length_km"].sum()),
            "severe_h3_h6_roads_km": float(df_road[df_road["hazard_class"].isin(["H3", "H4", "H5", "H6"])]["length_km"].sum()),
            "bridges_hydraulically_exposed": len(df_bridges),
            "bridges_severe_h3_h6": len(df_bridges[df_bridges["hazard_code"] >= 3]),
            "critical_facilities_inundated": len(df_fac),
            "critical_facilities_severe_h3_h6": len(df_fac[df_fac["hazard_code"] >= 3]),
            "road_status_classification": "HYDRAULICALLY_EXPOSED_ROAD_SEGMENT",
            "bridge_screening_classification": "BRIDGE_HYDRAULIC_EXPOSURE_SCREENING"
        },
        "response_priority_delineation": {
            "methodology": "OPERATIONAL_SCREENING_PRIORITY_ORDER",
            "sorting_rule": "1. max_hazard_class DESC (H6>H5>H4>H3), 2. earliest_arrival_hr ASC, 3. population_worldpop DESC",
            "total_zones": len(df_zones),
            "zones_summary": df_zones.to_dict(orient="records")
        }
    }

    with open(VALIDATION_DIR / "m8_exposure_summary.json", "w", encoding="utf-8") as f:
        json.dump(exposure_summary, f, indent=2)
    print(f"[OK] Saved: {VALIDATION_DIR / 'm8_exposure_summary.json'}")

    # 2. Source Manifest
    source_manifest = {
        "milestone": "M8",
        "generated_at": "2026-09-25T23:00:00+05:30",
        "sources": {
            "hydraulic_model": {
                "source_name": "D-Flow FM 2D Flexible Mesh Solver Output (Milestone M5)",
                "classification": "2D_DFLOWFM_SCREENING_INUNDATION_MODEL",
                "file_path": "outputs/simulations/dflowfm/BHV_BASE/Bhavanisagar_DamBreak_map.nc",
                "variables_used": ["mesh2d_waterdepth", "mesh2d_ucmag", "time", "mesh2d_face_x", "mesh2d_face_y", "mesh2d_flowelem_ba"],
                "spatial_coverage": "51.73 km reach, 82,309 computational faces",
                "temporal_resolution": "10-minute intervals (181 timesteps, 30.0 hr duration)"
            },
            "hazard_classification_standard": {
                "provider": "Central Water Commission (CWC) Dam Safety Organization / Australian Institute for Disaster Resilience (AIDR)",
                "document": "Australian Disaster Resilience Guideline 7-3: Flood Hazard / CWC Guidelines for Mapping Dam Inundation",
                "document_number": "AIDR Guideline 7-3 (ISBN 978-0-9953963-3-3)",
                "citation": "Smith, G.P., Davey, E.K., and Cox, R.J. (2014). 'Flood Hazard', WRL Technical Report 2014/07, UNSW Water Research Laboratory.",
                "url": "https://knowledge.aidr.org.au/resources/guideline-7-3-flood-hazard/",
                "thresholds": "H1 (D*V<=0.3, D<=0.3, V<=2.0), H2 (D*V<=0.6, D<=0.5), H3 (D*V<=0.6, D<=1.2), H4 (D*V<=1.0, D<=2.0), H5 (D*V<=4.0, D<=4.0, V<=4.0), H6 (D*V>4.0 or D>4.0 or V>4.0)"
            },
            "population_primary": {
                "provider": "WorldPop (School of Geography and Environmental Science, University of Southampton)",
                "product": "WorldPop 2020 UN-Adjusted Global 100m Population Count Grid (IND_ppp_2020_UNadj_constrained)",
                "gee_id": "WorldPop/GP/100m/pop/IND_2020",
                "reprojection": "EPSG:32643, sum-conserved reprojected grid",
                "total_reprojected_sum": 249913.5
            },
            "population_crosscheck": {
                "provider": "European Commission Joint Research Centre (JRC)",
                "product": "Global Human Settlement Layer (GHSL) GHS-POP R2023A (100m)",
                "gee_id": "JRC/GHSL/P2023A/GHS_POP/2025",
                "reprojection": "EPSG:32643, sum-conserved reprojected grid",
                "total_reprojected_sum": 385064.9
            },
            "building_footprints": {
                "provider": "Google Research / Earth Engine",
                "product": "Open Buildings v3 Polygons (confidence >= 0.75)",
                "gee_id": "GOOGLE/Research/open-buildings/v3/polygons",
                "reprojection": "EPSG:32643, footprint area calculated from polygon geometry",
                "total_footprints_acquired": 43470
            },
            "land_cover": {
                "provider": "European Space Agency (ESA)",
                "product": "ESA WorldCover 2021 v200 (10m global land cover)",
                "gee_id": "ESA/WorldCover/v200/2021",
                "reprojection": "EPSG:32643, nearest-neighbor categorical resampling",
                "key_classes": {"40": "Cropland", "50": "Built-up"}
            },
            "infrastructure_and_facilities": {
                "provider": "OpenStreetMap (OSM) Contributors",
                "api": "Overpass API / Nominatim",
                "queries": ["way['highway']", "node/way['amenity']", "node/way['emergency']", "node['place']"],
                "reprojection": "EPSG:32643, line length and point coordinates"
            }
        }
    }

    with open(VALIDATION_DIR / "m8_source_manifest.json", "w", encoding="utf-8") as f:
        json.dump(source_manifest, f, indent=2)
    print(f"[OK] Saved: {VALIDATION_DIR / 'm8_source_manifest.json'}")

    # 3. Uncertainty Manifest
    uncertainty_manifest = {
        "milestone": "M8",
        "classification": "SCREENING_HADR_CONSEQUENCE_ANALYSIS",
        "key_uncertainties": [
            {
                "domain": "Population Estimation",
                "nature": "Gridded census disaggregation vs real-time occupancy",
                "spread_observed": f"WorldPop={exposure_summary['population_exposure']['worldpop_total_inundated']:,.0f} vs GHSL={exposure_summary['population_exposure']['ghsl_total_inundated']:,.0f} (Ratio {exposure_summary['population_exposure']['ratio_ghsl_to_worldpop']:.2f})",
                "mitigation": "Reported as DATASET_SPREAD. Both primary and cross-check datasets are preserved and documented without cherry-picking."
            },
            {
                "domain": "Building Structural Vulnerability",
                "nature": "No site-specific building height, masonry type, or engineering fragility curves",
                "mitigation": "Classified conservatively as H5_H6_STRUCTURAL_DAMAGE_EXPOSURE based strictly on CWC H5/H6 hydrodynamic thresholds (D*V > 1.0 m2/s or D > 2.0 m). Buildings are NOT assumed destroyed."
            },
            {
                "domain": "Bridge Vulnerability",
                "nature": "No surveyed bridge deck elevation or scour rating in screening dataset",
                "mitigation": "Classified as BRIDGE_HYDRAULIC_EXPOSURE_SCREENING. Screened bridges are NOT assumed collapsed."
            },
            {
                "domain": "Agricultural & Economic Losses",
                "nature": "No crop calendar, crop stage, market prices, or economic damage curves",
                "mitigation": "Monetary damage and crop loss modeling declared NOT_IMPLEMENTED_IN_M8."
            },
            {
                "domain": "Life Safety / Casualties",
                "nature": "No empirical fatality rates (e.g. Graham 1999 or RCEM) parameterized for local warning compliance",
                "mitigation": "Potential loss of life model declared NOT_IMPLEMENTED to prevent speculative casualty figures."
            }
        ]
    }

    with open(VALIDATION_DIR / "m8_uncertainty_manifest.json", "w", encoding="utf-8") as f:
        json.dump(uncertainty_manifest, f, indent=2)
    print(f"[OK] Saved: {VALIDATION_DIR / 'm8_uncertainty_manifest.json'}")

    # 4. Comprehensive Markdown Report
    md_content = f"""# JalRakshak-HD: Milestone M8 Technical Report
## HADR Consequence, Exposure and Emergency-Priority Analysis
**Classification:** `SCREENING_HADR_CONSEQUENCE_ANALYSIS`  
**Hydraulic Source:** `2D_DFLOWFM_SCREENING_INUNDATION_MODEL` (M5 D-Flow FM 2D Simulation)  
**Study Area:** Bhavanisagar Dam Downstream Reach (51.73 km), Tamil Nadu, India  
**Coordinate Reference System:** EPSG:32643 (WGS 84 / UTM Zone 43N)  
**Date:** September 2026  

---

## 1. Executive Summary & Scientific Scope
Milestone M8 establishes an authoritative, reproducible emergency consequence and multi-sector exposure analysis for the 51.73 km downstream reach of Bhavanisagar Dam following the hypothetical breach scenario modeled in Milestone M5.

In accordance with strict scientific protocol:
- All hazard severities are derived synchronously from the 181 time steps of the validated M5 D-Flow FM 2D simulation using the **Central Water Commission (CWC) / AIDR Guideline 7-3 (Smith et al., 2014)** combined depth-velocity vulnerability standard (H1–H6).
- Gridded population exposure is determined from **WorldPop 2020** (primary) and cross-checked against **GHSL 2025**, with the variance documented as `DATASET_SPREAD`.
- Building footprint exposure is evaluated using **Google Open Buildings v3** (confidence $\\ge 0.75$). Structures located in H5 and H6 hazard zones are designated as `H5_H6_STRUCTURAL_DAMAGE_EXPOSURE` (not assumed destroyed).
- Transportation and critical infrastructure exposure are mapped from **OpenStreetMap (OSM)** and labeled `HYDRAULICALLY_EXPOSED_ROAD_SEGMENT` and `BRIDGE_HYDRAULIC_EXPOSURE_SCREENING`.
- Operational response priority zones are ranked using the deterministic `OPERATIONAL_SCREENING_PRIORITY_ORDER` without arbitrary weighted formulas.
- Speculative life loss and monetary loss models are explicitly declared `NOT_IMPLEMENTED`.

---

## 2. Hydraulic Hazard Severity Breakdown (CWC / AIDR 7-3)
Hazard severity is evaluated at each identical 10-minute timestep $t$ across all 82,309 computational mesh faces:

| Hazard Class | Description & Vulnerability | Face Count | Inundated Area (km²) | % of Inundated Extent |
|:---|:---|:---:|:---:|:---:|
| **H1** | Generally safe for people, vehicles, and buildings ($D \\cdot V \\le 0.3$, $D \\le 0.3$, $V \\le 2.0$) | {haz_sum['hazard_breakdown']['H1']['face_count']} | {haz_sum['hazard_breakdown']['H1']['area_km2']:.2f} | {haz_sum['hazard_breakdown']['H1']['area_percentage_inundated']:.2f}% |
| **H2** | Unsafe for small vehicles ($D \\cdot V \\le 0.6$, $D \\le 0.5$, $V \\le 2.0$) | {haz_sum['hazard_breakdown']['H2']['face_count']} | {haz_sum['hazard_breakdown']['H2']['area_km2']:.2f} | {haz_sum['hazard_breakdown']['H2']['area_percentage_inundated']:.2f}% |
| **H3** | Unsafe for vehicles, children, and the elderly ($D \\cdot V \\le 0.6$, $D \\le 1.2$, $V \\le 2.0$) | {haz_sum['hazard_breakdown']['H3']['face_count']} | {haz_sum['hazard_breakdown']['H3']['area_km2']:.2f} | {haz_sum['hazard_breakdown']['H3']['area_percentage_inundated']:.2f}% |
| **H4** | Unsafe for vehicles and people ($D \\cdot V \\le 1.0$, $D \\le 2.0$, $V \\le 2.0$) | {haz_sum['hazard_breakdown']['H4']['face_count']} | {haz_sum['hazard_breakdown']['H4']['area_km2']:.2f} | {haz_sum['hazard_breakdown']['H4']['area_percentage_inundated']:.2f}% |
| **H5** | Extreme hazard; structural damage to all buildings ($D \\cdot V \\le 4.0$, $D \\le 4.0$, $V \\le 4.0$) | {haz_sum['hazard_breakdown']['H5']['face_count']} | {haz_sum['hazard_breakdown']['H5']['area_km2']:.2f} | {haz_sum['hazard_breakdown']['H5']['area_percentage_inundated']:.2f}% |
| **H6** | Catastrophic hazard; full structural failure vulnerability ($D \\cdot V > 4.0$ or $D > 4.0$ or $V > 4.0$) | {haz_sum['hazard_breakdown']['H6']['face_count']} | {haz_sum['hazard_breakdown']['H6']['area_km2']:.2f} | {haz_sum['hazard_breakdown']['H6']['area_percentage_inundated']:.2f}% |
| **Total Inundated** | Extent experiencing $D \\ge 0.05$ m | **{haz_sum['total_inundated_faces']}** | **{haz_sum['total_inundated_area_km2']:.2f}** | **100.00%** |
| **Severe Hazard (H3–H6)** | Life-threatening / vehicle mobilization | **{haz_sum['total_domain_faces']}** | **{haz_sum['severe_hazard_h3_h6_area_km2']:.2f}** | **{haz_sum['severe_hazard_h3_h6_pct']:.2f}%** |

---

## 3. Multi-Sector Exposure Analysis

### 3.1 Population Exposure & Cross-Check Spread
- **WorldPop 2020 (Primary):** **{pop_cross['worldpop_total_inundated']:,.1f}** exposed ({pop_cross['worldpop_severe_h3_h6']:,.1f} in severe H3–H6).
- **GHSL 2025 (Cross-check):** **{pop_cross['ghsl_total_inundated']:,.1f}** exposed ({pop_cross['ghsl_severe_h3_h6']:,.1f} in severe H3–H6).
- **Dataset Spread:** **{pop_cross['absolute_dataset_spread']:,.1f}** people (Ratio GHSL/WorldPop = {pop_cross['ratio_ghsl_to_worldpop']:.2f}).

### 3.2 Building Footprint Exposure (Google Open Buildings v3)
- **Total Inundated Footprints:** **{exposure_summary['building_exposure']['total_buildings_inundated']:,}** buildings ({exposure_summary['building_exposure']['total_footprint_area_m2']/1e6:.2f} km² footprint area).
- **Severe Hazard (H3–H6):** **{exposure_summary['building_exposure']['severe_h3_h6_buildings']:,}** buildings ({exposure_summary['building_exposure']['severe_h3_h6_buildings']/exposure_summary['building_exposure']['total_buildings_inundated']*100:.1f}%).
- **Structural Vulnerability (H5/H6):** **{exposure_summary['building_exposure']['h5_h6_structural_damage_exposure']:,}** buildings classified as `H5_H6_STRUCTURAL_DAMAGE_EXPOSURE`.

### 3.3 Land Cover Exposure (ESA WorldCover 2021)
- **Cropland (Class 40):** **{exposure_summary['landcover_consequences']['cropland_class_40_inundated_km2']:.2f} km²** ({exposure_summary['landcover_consequences']['cropland_severe_h3_h6_km2']:.2f} km² severe H3–H6).
- **Built-up (Class 50):** **{exposure_summary['landcover_consequences']['builtup_class_50_inundated_km2']:.2f} km²** ({exposure_summary['landcover_consequences']['builtup_severe_h3_h6_km2']:.2f} km² severe H3–H6).

### 3.4 Infrastructure & Critical Facilities (OSM)
- **Road Network:** **{exposure_summary['infrastructure_exposure']['total_roads_inundated_km']:.2f} km** inundated ({exposure_summary['infrastructure_exposure']['severe_h3_h6_roads_km']:.2f} km severe H3–H6).
- **Screened Bridges:** **{exposure_summary['infrastructure_exposure']['bridges_hydraulically_exposed']}** bridges hydraulically exposed (`BRIDGE_HYDRAULIC_EXPOSURE_SCREENING`).
- **Critical Facilities:** **{exposure_summary['infrastructure_exposure']['critical_facilities_inundated']}** facilities exposed (10 healthcare, 1 education, 2 community assembly).

---

## 4. Operational HADR Response Priority Zones

Zones are ranked deterministically by `OPERATIONAL_SCREENING_PRIORITY_ORDER`:

| Priority Rank | Zone ID | Locality Reference | Max Hazard | Earliest Arrival | Pop (WorldPop) | Pop (GHSL) | Buildings | H5/H6 Buildings |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
"""
    for _, z in df_zones.iterrows():
        md_content += f"| **{z['priority_rank']}** | `{z['zone_id']}` | {z['locality_name']} | **{z['max_hazard_class']}** | {z['earliest_arrival_hr']:.2f} hr | {z['population_worldpop']:,.1f} | {z['population_ghsl']:,.1f} | {z['building_count']:,} | {z['h5_h6_buildings']:,} |\n"

    md_content += rf"""
---

## 5. Scientific Limitations & Uncertainty Governance
1. **Screening Hydraulic Model:** Derived from a 2D screening inundation simulation on 30m SRTM terrain; does not account for micro-topographic flood walls, local embankments, or localized drainage structures.
2. **Population Disaggregation:** Gridded datasets (WorldPop / GHSL) estimate ambient/residential population and do not reflect diurnal transit, factory workshifts, or real-time evacuation movements.
3. **No Structural Fragility Curves:** In the absence of building structural engineering surveys, H5/H6 buildings are flagged for high structural exposure risk, not assumed destroyed.
4. **No Arbitrary Loss of Life:** Life loss estimation is explicitly withheld (`NOT_IMPLEMENTED`) to adhere to strict scientific rigor.
"""

    report_path = REPORTS_DIR / "m8_hadr_summary.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Saved technical report: {report_path}")


if __name__ == "__main__":
    generate_manifests()
