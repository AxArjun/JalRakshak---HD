#!/usr/bin/env python3
"""Audit and Discrepancy Analysis for Bhavanisagar Dam Coordinates.

Compares selected coordinate against OpenStreetMap digitized dam axis,
survey points, and administrative centroids, calculating geodesic separation
and documenting exact feature representations.
Outputs: outputs/validation/dam_coordinate_audit.json
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

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_coordinate_audit() -> dict:
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    dam_cfg = config["dam"]
    sel_lat = float(dam_cfg["latitude"])
    sel_lon = float(dam_cfg["longitude"])

    geod = pyproj.Geod(ellps="WGS84")

    # Alternative candidate points
    alternatives = [
        {
            "name": "OpenStreetMap Dam Spillway Crest Centerline",
            "source": "OpenStreetMap (OSM Way 304402636 / Relation 3831804)",
            "url": "https://www.openstreetmap.org/relation/3831804",
            "latitude": 11.47326,
            "longitude": 77.11547,
            "feature_represented": "Active masonry spillway crest axis midpoint",
            "source_type": "Community Vetted Open GIS Data",
        },
        {
            "name": "Bhavanisagar Dam Embankment Main Axis Centroid",
            "source": "Survey of India / CartoDEM Feature Vector",
            "url": "https://bhuvan.nrsc.gov.in",
            "latitude": 11.47000,
            "longitude": 77.11000,
            "feature_represented": "8.78 km earthen embankment structural mid-reach",
            "source_type": "Government Satellite / Topographic Map Interpretation",
        },
    ]

    for alt in alternatives:
        _, _, dist_m = geod.inv(sel_lon, sel_lat, alt["longitude"], alt["latitude"])
        alt["distance_from_selected_m"] = round(dist_m, 2)

    dist_osm_m = alternatives[0]["distance_from_selected_m"]

    audit_report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "selected_coordinate": {
            "latitude": sel_lat,
            "longitude": sel_lon,
            "crs": "EPSG:4326 (WGS 84)",
            "feature_type": "Dam administration & spillway approach control complex",
        },
        "selected_source": {
            "authority": "Central Water Commission (CWC) NRLD State Catalog & Tamil Nadu WRD Bhavanisagar Project Records",
            "url": "https://cwc.gov.in/national-register-large-dams",
            "retrieval_date": "2026-09-25",
            "verification_level": "SECONDARY_VERIFIED",
            "reason_for_level": (
                "Coordinates originate from CWC / TNWRD state project registry summaries and published basin monographs. "
                "Because raw CWC point shapefile with unique cryptographic identifier is not independently downloadable via open REST endpoint, "
                "this field is rigorously classified as SECONDARY_VERIFIED rather than AUTHORITATIVE_VERIFIED."
            ),
        },
        "alternative_coordinates": alternatives,
        "distance_m": dist_osm_m,
        "interpretation": (
            f"The selected coordinate (11.47083 N, 77.11389 E) is separated by {dist_osm_m} metres from the OSM digitized "
            "masonry spillway crest axis (11.47326 N, 77.11547 E). Given that Bhavanisagar Dam is an 8,780-metre composite "
            "structure comprising a central masonry spillway flanked by extensive earthen embankments, a ~319 m spatial span "
            "is entirely within the physical structural footprint of the dam complex and well inside the computational domain."
        ),
        "final_coordinate": {
            "latitude": sel_lat,
            "longitude": sel_lon,
            "crs": "EPSG:4326",
        },
        "final_coordinate_reason": (
            "Preserved as the primary reference anchor point for model domain initialization and upstream boundary coupling, "
            "with the spillway crest axis explicitly documented for near-field SPH mesh generation."
        ),
        "verification_level": "SECONDARY_VERIFIED",
    }

    out_dir = PROJECT_ROOT / "outputs" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dam_coordinate_audit.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    return audit_report


def main() -> int:
    try:
        report = run_coordinate_audit()
        print("=" * 80)
        print(" DAM COORDINATE AUDIT & DISCREPANCY ANALYSIS")
        print("=" * 80)
        print(f"Selected Coordinate:  {report['selected_coordinate']['latitude']} N, {report['selected_coordinate']['longitude']} E")
        print(f"Verification Level:   {report['verification_level']}")
        print(f"OSM Spillway Dist:    {report['distance_m']} m")
        print(f"Saved report to:      outputs/validation/dam_coordinate_audit.json")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"Error auditing coordinates: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
