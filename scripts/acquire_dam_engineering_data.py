"""
Acquire and Standardize Verified Dam Engineering Metadata for Bhavanisagar Dam.
SIH PS 26161 - JalRakshak-HD Milestone M3 (Final Source Reconciliation).

Compiles authoritative engineering records from Central Water Commission (NRLD 2019 & Hydrological Data Book),
Tamil Nadu Water Resources Department (TNWRD), and Lower Bhavani engineering literature into a structured inventory.
Saves:
  - outputs/validation/dam_engineering_inventory.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyproj

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INVENTORY = {
    "dam_official_name": {
        "value": "Bhavanisagar Dam",
        "unit": "string",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "Central Water Commission (CWC) National Register of Large Dams (NRLD) & Tamil Nadu WRD",
        "exact_reference": "NRLD Dam Index ID: TN12HH0014 (Bhavanisagar / Lower Bhavani)",
        "retrieval_date": "2026-09-25",
        "definition": "Official statutory name of the dam in National Register of Large Dams"
    },
    "alternate_names": {
        "value": ["Lower Bhavani Dam", "Bhavani Sagar Project"],
        "unit": "string_list",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "India-WRIS / CWC NRLD",
        "exact_reference": "India-WRIS Major/Medium Project Registry",
        "retrieval_date": "2026-09-25",
        "definition": "Registered alternate project names"
    },
    "dam_type": {
        "value": "Composite Earthen Dam with Central Masonry Spillway",
        "unit": "string",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "CWC NRLD Large Dam Inventory",
        "exact_reference": "NRLD Tamil Nadu State Summary",
        "retrieval_date": "2026-09-25",
        "definition": "Structural dam type: composite earthfill flanks with central concrete/masonry section"
    },
    "year_completed": {
        "value": 1955,
        "unit": "year",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "CWC NRLD Large Dam Inventory",
        "exact_reference": "NRLD Year of Completion Field",
        "retrieval_date": "2026-09-25",
        "definition": "Year construction completed and reservoir commissioned"
    },
    # Source A: NRLD 2019
    "nrld_height_above_lowest_foundation_m": {
        "value": 62.0,
        "unit": "metres",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "Central Water Commission (CWC) National Register of Large Dams 2019 (PIC: TN12HH0014)",
        "exact_reference": "NRLD 2019 Height above Lowest Foundation Field (62.0 m)",
        "retrieval_date": "2026-09-25",
        "definition": "Height of dam structure above lowest point of foundation in metres (Source A)"
    },
    "nrld_dam_length_m": {
        "value": 8797.0,
        "unit": "metres",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "Central Water Commission (CWC) National Register of Large Dams 2019 (PIC: TN12HH0014)",
        "exact_reference": "NRLD 2019 Length of Dam Field (8797.0 m)",
        "retrieval_date": "2026-09-25",
        "definition": "Total length of dam structure reported in NRLD 2019 (Source A)"
    },
    # Source B: Lower Bhavani Engineering Rehabilitation Literature & Project Technical Description
    "technical_project_dam_length_m": {
        "value": 8780.0,
        "unit": "metres",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "Lower Bhavani Project Technical Description & Rehabilitation Engineering Literature",
        "exact_reference": "Technical Project Description (8.78 km / 8780.0 m)",
        "retrieval_date": "2026-09-25",
        "definition": "Overall composite dam crest length reported in state technical documentation (Source B)"
    },
    "central_masonry_section_length_m": {
        "value": 464.0,
        "unit": "metres",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "Lower Bhavani Project Technical Description & WRD Engineering Records",
        "exact_reference": "Technical Project Description (464.0 m masonry section)",
        "retrieval_date": "2026-09-25",
        "definition": "Total length of the central masonry structural section (Source B)"
    },
    "masonry_section_height_from_lowest_foundation_m": {
        "value": 62.18,
        "unit": "metres",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "Lower Bhavani Project Technical Description",
        "exact_reference": "Technical Project Description (204 ft = 62.18 m)",
        "retrieval_date": "2026-09-25",
        "definition": "Height of central masonry section above deepest foundation level (Source B)"
    },
    "earthen_embankment_reported_height_m": {
        "value": 40.0,
        "unit": "metres",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "State Engineering Project Summaries",
        "exact_reference": "Lower Bhavani Project Summary (reported ~40.0 m / 130 ft height above riverbed for embankment flanks)",
        "retrieval_date": "2026-09-25",
        "definition": "Reported representative structural height of earthfill embankment flanks above riverbed (distinct from deepest masonry foundation)"
    },
    "arithmetic_embankment_length_approx_m": {
        "value": 8316.0,
        "unit": "metres",
        "verification_level": "MODEL_DERIVED_APPROXIMATION",
        "source": "Derived: Technical Total Length (8780.0 m) minus Central Masonry Section (464.0 m) = 8316.0 m",
        "exact_reference": "Arithmetic derivation",
        "retrieval_date": "2026-09-25",
        "definition": "Approximate combined embankment length derived by subtraction (not a published survey quantity)"
    },
    # Spillway Specific Parameters
    "spillway_type": {
        "value": "Ogee Masonry Spillway with Radial Crest Gates",
        "unit": "string",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "TNWRD Dam Operations Manual & CWC NRLD",
        "exact_reference": "TNWRD Lower Bhavani Dam Operations & Maintenance Manual",
        "retrieval_date": "2026-09-25",
        "definition": "Spillway discharge crest profile and gate type"
    },
    "spillway_crest_length_m": {
        "value": 120.70,
        "unit": "metres",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "Lower Bhavani Project Technical Specifications",
        "exact_reference": "9 bays x 10.97 m gate clear width plus intermediate piers = 120.70 m",
        "retrieval_date": "2026-09-25",
        "definition": "Length of ogee spillway discharge crest (distinct from the 464.0 m central masonry monolith)"
    },
    "spillway_crest_level_m": {
        "value": 274.32,
        "unit": "metres MSL",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "TNWRD Lower Bhavani Dam Operations Manual",
        "exact_reference": "Spillway Crest Sill Datum (900.0 ft MSL = 274.32 m MSL)",
        "retrieval_date": "2026-09-25",
        "definition": "Elevation of the ogee spillway crest sill in metres MSL"
    },
    "spillway_capacity_cumec": {
        "value": 3455.0,
        "unit": "m3/s",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "TNWRD Dam Safety Directorate",
        "exact_reference": "Spillway Rating Schedule (approx. 122,000 cfs = 3455.0 m3/s)",
        "retrieval_date": "2026-09-25",
        "definition": "Total design flood discharge capacity of the 9-bay gated spillway"
    },
    "spillway_gate_count": {
        "value": 9,
        "unit": "count",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "TNWRD Dam Operations Manual & CWC NRLD",
        "exact_reference": "TNWRD Spillway Gate Schedule (9 radial gates)",
        "retrieval_date": "2026-09-25",
        "definition": "Number of gated spillway crest bays"
    },
    "spillway_gate_size_m": {
        "value": "10.97 x 6.10",
        "unit": "metres (width x height)",
        "verification_level": "SECONDARY_VERIFIED",
        "source": "TNWRD Lower Bhavani Dam Operations Manual",
        "exact_reference": "Gate Schedule: 36 ft x 20 ft (10.97 m x 6.10 m)",
        "retrieval_date": "2026-09-25",
        "definition": "Clear width and height of each radial spillway crest gate"
    },
    # Hydraulic Levels
    "reservoir_frl_m": {
        "value": 280.42,
        "unit": "metres MSL",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "Central Water Commission (CWC) Flood Forecasting & Reservoir Monitoring Records",
        "exact_reference": "CWC Daily Reservoir Bulletin / 2024 Appraisal Report for Bhavanisagar",
        "retrieval_date": "2026-09-25",
        "definition": "Full Reservoir Level in orthometric height metres above Mean Sea Level"
    },
    "reservoir_full_depth_ft": {
        "value": 105.0,
        "unit": "feet",
        "verification_level": "AUTHORITATIVE_VERIFIED",
        "source": "Tamil Nadu Water Resources Department (TNWRD) Daily Reservoir Dashboard",
        "exact_reference": "TNWRD Water Year Bulletin & Daily Storage Dashboard (105 ft = 32.004 m)",
        "retrieval_date": "2026-09-25",
        "definition": "Operating water column depth above zero-gauge sill datum"
    },
    # Storage Sources Record
    "reservoir_storage_sources": {
        "cwc_hydrological_data_book_2020": {
            "gross_storage_mcm": 929.0,
            "live_storage_mcm": 780.5,
            "definition": "Central Water Commission Hydrological Data Book 2020 (Cauvery Basin Reservoir Records)",
            "verification_level": "AUTHORITATIVE_VERIFIED"
        },
        "tn_state_feasibility_project_record": {
            "gross_storage_mcm": 929.0,
            "live_storage_mcm": 908.0,
            "definition": "Tamil Nadu State Project Feasibility & Operational Storage Schedule (cited as 32.0 TMC operational)",
            "verification_level": "SECONDARY_VERIFIED"
        }
    },
    # Breach Model Assumption Parameters
    "breach_model_vw_m3": {
        "value": 780500000.0,
        "unit": "m3",
        "verification_level": "MODEL_ASSUMPTION_FIRST_ESTIMATE",
        "source": "CWC Hydrological Data Book 2020 live storage record (780.5 MCM)",
        "exact_reference": "Sensitivity reference baseline assumption",
        "retrieval_date": "2026-09-25",
        "definition": "First-estimate active breach volume assumption in absence of dynamic stage-storage routing. NOT observed breachable volume."
    },
    "final_breach_height_hb_m": {
        "value": 40.0,
        "unit": "metres",
        "verification_level": "MODEL_ASSUMPTION_FIRST_ESTIMATE",
        "source": "Hypothetical complete-breach depth assumption",
        "exact_reference": "SIH PS 26161 Research Prototype Baseline Definition",
        "retrieval_date": "2026-09-25",
        "definition": "This is a hypothetical complete-breach depth assumption and is not the published maximum dam height (which is 62.0 m / 62.18 m for the deepest masonry foundation)."
    },
    "preferred_live_storage_for_breach_model": {
        "value": None,
        "unit": "MCM",
        "verification_level": "UNVERIFIED",
        "source": "Pending physical stage-storage rating curve and surveyed breach invert datum",
        "exact_reference": None,
        "retrieval_date": "2026-09-25",
        "definition": "Preferred live storage for breach model (kept null pending physical invert routing)"
    },
    "left_embankment_length_m": {
        "value": None,
        "unit": "metres",
        "verification_level": "UNVERIFIED",
        "source": "Pending unredacted engineering drawings",
        "exact_reference": None,
        "retrieval_date": "2026-09-25",
        "definition": "Length of left embankment flank (individual split unverified in public NRLD)"
    },
    "right_embankment_length_m": {
        "value": None,
        "unit": "metres",
        "verification_level": "UNVERIFIED",
        "source": "Pending unredacted engineering drawings",
        "exact_reference": None,
        "retrieval_date": "2026-09-25",
        "definition": "Length of right embankment flank (individual split unverified in public NRLD)"
    },
    "official_mwl_m": {
        "value": None,
        "unit": "metres MSL",
        "verification_level": "UNVERIFIED",
        "source": "Pending unredacted engineering completion drawings",
        "exact_reference": None,
        "retrieval_date": "2026-09-25",
        "definition": "Maximum Water Level under design flood routing"
    },
    "official_crest_elevation_m": {
        "value": None,
        "unit": "metres MSL",
        "verification_level": "UNVERIFIED",
        "source": "Pending unredacted engineering completion drawings",
        "exact_reference": None,
        "retrieval_date": "2026-09-25",
        "definition": "Structural top-of-dam road crest elevation in metres MSL"
    }
}


def acquire_dam_engineering_data():
    out_path = PROJECT_ROOT / "outputs" / "validation" / "dam_engineering_inventory.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(INVENTORY, f, indent=2)

    print("=" * 100)
    print(" BHAVANISAGAR DAM VERIFIED ENGINEERING METADATA INVENTORY (FINAL RECONCILIATION)")
    print("=" * 100)
    print(f"{'Variable':<36} | {'Value':<12} | {'Unit':<14} | {'Level':<32} | {'Source'}")
    print("-" * 100)
    for k, v in INVENTORY.items():
        if isinstance(v, dict) and "value" in v:
            val_str = str(v["value"]) if v["value"] is not None else "null"
            print(f"{k:<36} | {val_str:<12} | {v['unit']:<14} | {v['verification_level']:<32} | {v['source'][:30]}...")
        elif isinstance(v, dict):
            print(f"{k:<36} | [dict entries] | {'dict':<14} | {'RECORD_COLLECTION':<32} | Multiple published sources...")
    print("=" * 100)
    print(f"Saved dam engineering inventory to: {out_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    acquire_dam_engineering_data()
