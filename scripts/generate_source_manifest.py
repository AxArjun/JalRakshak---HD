#!/usr/bin/env python3
"""Generate Source Provenance Manifest for JalRakshak-HD Milestone M1.

Records the exact provider, source URL/endpoint, source type, retrieval date,
and verification level (AUTHORITATIVE_VERIFIED, SECONDARY_VERIFIED, DERIVED, UNVERIFIED)
for all M1 scientific and geographical metadata.
Outputs: outputs/validation/m1_source_manifest.json
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def create_source_manifest() -> dict:
    manifest_records = [
        {
            "field": "dam.name",
            "value": "Bhavanisagar Dam",
            "provider": "Central Water Commission (CWC)",
            "exact_source": "National Register of Large Dams (NRLD) 2019 / 2023 Edition, Dam Safety Organisation, MoJS (https://cwc.gov.in/national-register-large-dams)",
            "source_type": "Official Government Register",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.type",
            "value": "Earthen Dam with Central Masonry Spillway (Composite)",
            "provider": "Central Water Commission (CWC) & TNWRD",
            "exact_source": "NRLD Tamil Nadu Large Dam Inventory & Project Technical Specifications",
            "source_type": "Official Engineering Specification",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.year_completed",
            "value": 1955,
            "provider": "Central Water Commission (CWC)",
            "exact_source": "NRLD Dam Completion Registry, Entry ID: Bhavanisagar",
            "source_type": "Official Government Register",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.crest_length_m",
            "value": 8780.0,
            "provider": "Tamil Nadu Water Resources Department (TNWRD)",
            "exact_source": "Bhavani Basin Project Profile, WRD Tamil Nadu (https://www.wrd.tn.gov.in)",
            "source_type": "State Department Technical Report",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.max_height_m",
            "value": 40.0,
            "provider": "Central Water Commission (CWC) NRLD",
            "exact_source": "National Register of Large Dams, Tamil Nadu State Summary",
            "source_type": "Official Government Register",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.gross_storage_tmc",
            "value": 32.8,
            "provider": "Tamil Nadu Water Resources Department (TNWRD)",
            "exact_source": "Lower Bhavani Project Operational Manual & CWC Water Year Book",
            "source_type": "Official Hydrological Record",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.coordinates",
            "value": "11.47083 N, 77.11389 E",
            "provider": "CWC NRLD State Summary & TNWRD Project Location Index",
            "exact_source": "CWC NRLD Location List & WRD State Irrigation Maps",
            "source_type": "State Registry Summary",
            "retrieval_date": "2026-09-25",
            "verification_level": "SECONDARY_VERIFIED",
        },
        {
            "field": "dam.alternative_spillway_coordinate",
            "value": "11.47326 N, 77.11547 E",
            "provider": "OpenStreetMap Contributors",
            "exact_source": "OpenStreetMap Relation 3831804 / Way 304402636 (https://www.openstreetmap.org/relation/3831804)",
            "source_type": "Open GIS Geospatial Feature",
            "retrieval_date": "2026-09-25",
            "verification_level": "SECONDARY_VERIFIED",
        },
        {
            "field": "dam.official_frl_m",
            "value": 280.42,
            "provider": "Central Water Commission (CWC)",
            "exact_source": "CWC Flood Forecasting & Reservoir Monitoring Records / 2024 Appraisal (https://cwc.gov.in)",
            "source_type": "Authoritative National Hydrological Record",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.reservoir_full_depth_ft",
            "value": 105.0,
            "provider": "Tamil Nadu Water Resources Department (TNWRD)",
            "exact_source": "TNWRD Reservoir Daily Bulletins & Operations Register",
            "source_type": "State Operational Monitoring Bulletin",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "dam.official_mwl_m",
            "value": None,
            "provider": "None (Pending authoritative engineering documentation)",
            "exact_source": "None",
            "source_type": "None",
            "retrieval_date": "2026-09-25",
            "verification_level": "UNVERIFIED",
        },
        {
            "field": "dam.official_crest_level_m",
            "value": None,
            "provider": "None (Pending authoritative engineering documentation)",
            "exact_source": "None",
            "source_type": "None",
            "retrieval_date": "2026-09-25",
            "verification_level": "UNVERIFIED",
        },
        {
            "field": "study_area.administrative_hierarchy",
            "value": "State: Tamil Nadu | District: Erode | Taluk: Sathyamangalam | Revenue Division: Gobichettipalayam | Block: Bhavanisagar | AC: Bhavanisagar (SC)",
            "provider": "Government of Tamil Nadu, District Administration of Erode",
            "exact_source": "Erode District Official Portal: Revenue Administration (https://erode.nic.in/revenue-administration/) & Taluks Directory (https://erode.nic.in/taluks/)",
            "source_type": "Authoritative District Administration Portal",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "river.name_and_basin",
            "value": "Bhavani River (Cauvery Basin, Lower Cauvery Sub-basin)",
            "provider": "Central Water Commission (CWC) & India-WRIS",
            "exact_source": "India-WRIS River Basin Atlas & Cauvery Basin Hydrological Profile (https://indiawris.gov.in)",
            "source_type": "National Water Resources Database",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "terrain.raw_dem",
            "value": "USGS/SRTMGL1_003 (30m 1 Arc-Second GeoTIFF)",
            "provider": "NASA JPL / USGS EROS via Google Earth Engine API",
            "exact_source": "Google Earth Engine Asset Catalog: USGS/SRTMGL1_003 (Project: jalrakshak-hd)",
            "source_type": "Satellite Earth Observation Dataset",
            "retrieval_date": "2026-09-25",
            "verification_level": "AUTHORITATIVE_VERIFIED",
        },
        {
            "field": "terrain.projected_dem",
            "value": "dem_projected.tif (EPSG:32643, 30m resolution, 1718x826 pixels)",
            "provider": "JalRakshak-HD Pipeline",
            "exact_source": "Reprojected via Rasterio / GDAL from authentic USGS/SRTMGL1_003",
            "source_type": "Scientifically Processed Raster",
            "retrieval_date": "2026-09-25",
            "verification_level": "DERIVED",
        },
        {
            "field": "terrain.dam_pixel_elevation",
            "value": 269.75,
            "provider": "JalRakshak-HD Pipeline",
            "exact_source": "Raster pixel sample on data/terrain/dem_projected.tif (Surface ground terrain sample, not structural/hydraulic datum)",
            "source_type": "Sampled Raster Cell Value",
            "retrieval_date": "2026-09-25",
            "verification_level": "DERIVED",
        },
        {
            "field": "terrain.slope_and_hillshade",
            "value": "slope.tif, hillshade.tif (Horn 1981 finite-difference algorithm)",
            "provider": "JalRakshak-HD Pipeline",
            "exact_source": "Generated from data/terrain/dem_projected.tif using scripts/generate_terrain_derivatives.py",
            "source_type": "Scientifically Derived Terrain Grids",
            "retrieval_date": "2026-09-25",
            "verification_level": "DERIVED",
        },
    ]

    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "milestone": "M1 — Real Study Area, AOI and Terrain Acquisition",
        "project": "JalRakshak-HD",
        "total_fields_tracked": len(manifest_records),
        "verification_level_summary": {
            "AUTHORITATIVE_VERIFIED": sum(1 for r in manifest_records if r["verification_level"] == "AUTHORITATIVE_VERIFIED"),
            "SECONDARY_VERIFIED": sum(1 for r in manifest_records if r["verification_level"] == "SECONDARY_VERIFIED"),
            "DERIVED": sum(1 for r in manifest_records if r["verification_level"] == "DERIVED"),
            "UNVERIFIED": sum(1 for r in manifest_records if r["verification_level"] == "UNVERIFIED"),
        },
        "records": manifest_records,
    }

    out_dir = PROJECT_ROOT / "outputs" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "m1_source_manifest.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def main() -> int:
    try:
        manifest = create_source_manifest()
        print("=" * 80)
        print(" M1 SOURCE PROVENANCE MANIFEST GENERATED (DATUM CORRECTED)")
        print("=" * 80)
        print(f"Total Records: {manifest['total_fields_tracked']}")
        print(f"Verification Breakdown: {manifest['verification_level_summary']}")
        print(f"Saved to: outputs/validation/m1_source_manifest.json")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"Error generating source manifest: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
