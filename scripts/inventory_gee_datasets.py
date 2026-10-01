"""
JalRakshak-HD: Milestone M9 Task 1 — Verify GEE Dataset Inventory
==================================================================
Queries Google Earth Engine to verify availability, schema, band names,
and metadata for all required remote sensing datasets.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import ee

ROOT_DIR = Path(__file__).resolve().parent.parent
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

# Initialize GEE
ee.Initialize(project="jalrakshak-hd")

AOI_GEOM = ee.Geometry.Rectangle([77.10, 11.42, 77.45, 11.55])

DATASET_SPECS = [
    {
        "asset_id": "COPERNICUS/S1_GRD",
        "provider": "European Space Agency (ESA) / Copernicus",
        "type": "ImageCollection",
        "native_resolution": "10 m",
        "temporal_coverage": "2014-10-03 to present",
        "intended_role": "Primary SAR backscatter imagery for pre/post-event flood change detection",
        "test_start": "2019-08-01",
        "test_end": "2019-08-31",
    },
    {
        "asset_id": "COPERNICUS/S2_SR_HARMONIZED",
        "provider": "European Space Agency (ESA) / Copernicus",
        "type": "ImageCollection",
        "native_resolution": "10 m (VNIR) / 20 m (SWIR)",
        "temporal_coverage": "2015-06-23 to present",
        "intended_role": "Multispectral optical cross-check (MNDWI/NDWI) when cloud conditions permit",
        "test_start": "2019-08-01",
        "test_end": "2019-08-31",
    },
    {
        "asset_id": "JRC/GSW1_4/GlobalSurfaceWater",
        "provider": "European Commission, Joint Research Centre (JRC)",
        "type": "Image",
        "native_resolution": "30 m",
        "temporal_coverage": "1984-03-16 to 2021-12-31",
        "intended_role": "Persistent water baseline and historical recurrence classification",
        "test_start": None,
        "test_end": None,
    },
    {
        "asset_id": "JRC/GSW1_4/MonthlyHistory",
        "provider": "European Commission, Joint Research Centre (JRC)",
        "type": "ImageCollection",
        "native_resolution": "30 m",
        "temporal_coverage": "1984-03-01 to 2021-12-31",
        "intended_role": "Historical monthly surface water history context",
        "test_start": "2019-01-01",
        "test_end": "2019-12-31",
    },
    {
        "asset_id": "UCSB-CHG/CHIRPS/DAILY",
        "provider": "Climate Hazards Center, UC Santa Barbara",
        "type": "ImageCollection",
        "native_resolution": "0.05 deg (~5.5 km)",
        "temporal_coverage": "1981-01-01 to near-present",
        "intended_role": "Precipitation accumulation and antecedent moisture context",
        "test_start": "2019-08-01",
        "test_end": "2019-08-31",
    },
]


def verify_datasets():
    print("=" * 70)
    print(" JALRAKSHAK-HD: M9 Task 1 — GEE Dataset Inventory Verification")
    print("=" * 70)

    inventory = []
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

    for spec in DATASET_SPECS:
        asset_id = spec["asset_id"]
        print(f"Checking asset: {asset_id} ...")
        try:
            if spec["type"] == "ImageCollection":
                col = ee.ImageCollection(asset_id)
                if spec["test_start"] and spec["test_end"]:
                    sub = col.filterBounds(AOI_GEOM).filterDate(spec["test_start"], spec["test_end"])
                    count = sub.size().getInfo()
                    sample_img = sub.first()
                    bands = sample_img.bandNames().getInfo() if count > 0 else []
                else:
                    count = col.size().getInfo()
                    bands = col.first().bandNames().getInfo()
            else:
                img = ee.Image(asset_id)
                bands = img.bandNames().getInfo()
                count = 1

            status = "AVAILABLE"
            print(f"  [PASS] Status: {status} | Bands ({len(bands)}): {bands[:6]} | Sample scenes: {count}")
            inventory.append({
                "asset_id": asset_id,
                "provider": spec["provider"],
                "current_availability": status,
                "bands_used": bands,
                "native_resolution": spec["native_resolution"],
                "temporal_coverage": spec["temporal_coverage"],
                "retrieval_date": now_str,
                "intended_role": spec["intended_role"],
                "sample_count_in_test_aoi": count,
            })
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            inventory.append({
                "asset_id": asset_id,
                "provider": spec["provider"],
                "current_availability": "ERROR",
                "error": str(e),
                "intended_role": spec["intended_role"],
            })

    output_data = {
        "milestone": "M9",
        "verification_type": "GEE_DATASET_AVAILABILITY_INVENTORY",
        "project": "jalrakshak-hd",
        "inventory_timestamp": now_str,
        "total_datasets": len(inventory),
        "all_available": all(d.get("current_availability") == "AVAILABLE" for d in inventory),
        "datasets": inventory,
    }

    out_file = VALIDATION_DIR / "m9_gee_dataset_inventory.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n[OK] Saved dataset inventory: {out_file}")
    return output_data


if __name__ == "__main__":
    verify_datasets()
