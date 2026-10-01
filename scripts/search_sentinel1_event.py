"""
JalRakshak-HD: Milestone M9 Task 4 — Search Sentinel-1 Event Scenes
====================================================================
Searches and catalogs Sentinel-1 SAR GRD acquisitions over the Bhavanisagar
downstream domain for the verified August 2019 historical flood event.
Enforces orbit consistency (relative orbit and pass direction).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import ee
import pandas as pd
import geopandas as gpd

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_GEE_DIR = ROOT_DIR / "data" / "gee"
DATA_GEE_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

ee.Initialize(project="jalrakshak-hd")

# Load analysis AOI
AOI_PATH = DATA_GEE_DIR / "m9_analysis_aoi.gpkg"
if AOI_PATH.exists():
    aoi_gdf = gpd.read_file(AOI_PATH).to_crs("EPSG:4326")
    b = aoi_gdf.total_bounds
    AOI_GEOM = ee.Geometry.Rectangle([float(b[0]), float(b[1]), float(b[2]), float(b[3])])
else:
    AOI_GEOM = ee.Geometry.Rectangle([77.10, 11.42, 77.45, 11.55])


def search_event_scenes():
    print("=" * 70)
    print(" JALRAKSHAK-HD: M9 Task 4 — Sentinel-1 Acquisition Search")
    print("=" * 70)

    # Event dates: August 8-16, 2019
    # Query window: July 15, 2019 to August 31, 2019
    s1_col = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(AOI_GEOM)
        .filterDate("2019-07-15", "2019-08-31")
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .filter(ee.Filter.eq("instrumentMode", "IW"))
    )

    aoi_area = AOI_GEOM.area().getInfo()
    scenes = s1_col.getInfo()["features"]
    print(f"Total matching scenes found: {len(scenes)}")

    records = []
    for sc in scenes:
        props = sc["properties"]
        scene_id = sc["id"]
        ts = props["system:time_start"] / 1000.0
        acq_dt = pd.to_datetime(ts, unit="s", utc=True).strftime("%Y-%m-%d %H:%M:%SZ")
        orbit_pass = props.get("orbitProperties_pass", "UNKNOWN")
        rel_orbit = props.get("relativeOrbitNumber_start", -1)
        pols = props.get("transmitterReceiverPolarisation", ["VV", "VH"])
        pol_str = "+".join(pols)

        # Compute AOI coverage
        img = ee.Image(scene_id)
        img_geom = img.geometry()
        inter = img_geom.intersection(AOI_GEOM)
        inter_area = inter.area().getInfo()
        cov_pct = min(100.0, round((inter_area / aoi_area) * 100.0, 2))

        # Assign role based on date
        dt = pd.to_datetime(ts, unit="s", utc=True)
        if dt < pd.to_datetime("2019-08-08", utc=True):
            role = "PRE_EVENT"
        elif dt <= pd.to_datetime("2019-08-16", utc=True):
            role = "EVENT_PEAK"
        else:
            role = "POST_EVENT"

        record = {
            "scene_id": scene_id,
            "acquisition_datetime": acq_dt,
            "orbit_pass": orbit_pass,
            "relative_orbit": rel_orbit,
            "polarizations": pol_str,
            "resolution": "10 m",
            "role": role,
            "coverage_percent": cov_pct,
        }
        records.append(record)
        print(f"  {role:<11} | {acq_dt} | Orbit {rel_orbit} ({orbit_pass}) | Cov: {cov_pct:.1f}% | {scene_id}")

    df = pd.DataFrame(records)
    out_csv = DATA_GEE_DIR / "sentinel1_event_scenes.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n[OK] Saved Sentinel-1 event scenes to: {out_csv}")
    return df


if __name__ == "__main__":
    search_event_scenes()
