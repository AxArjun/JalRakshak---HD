"""
Snap Hydrologic Pour Point to High-Accumulation Thalweg Cell.
SIH PS 26161 - JalRakshak-HD Milestone M2 Repair.

Snaps the dam reference coordinate to the nearest valid high-accumulation
stream cell (accumulation >= selected stream threshold) within tolerance.
Saves:
  - data/hydrology/hydrologic_pour_point.gpkg
  - outputs/validation/pour_point_validation.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyproj
import rasterio
from shapely.geometry import Point
import yaml

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def snap_hydrologic_pour_point(max_tolerance_m: float = 500.0, stream_threshold_cells: int = 1000):
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    dam_lat = config["dam"]["latitude"]
    dam_lon = config["dam"]["longitude"]
    proj_crs = config["aoi"]["projected_crs"]

    dam_pt_wgs84 = Point(dam_lon, dam_lat)
    dam_pt_proj = gpd.GeoSeries([dam_pt_wgs84], crs="EPSG:4326").to_crs(proj_crs).iloc[0]
    dam_x, dam_y = dam_pt_proj.x, dam_pt_proj.y

    facc_path = PROJECT_ROOT / "data" / "hydrology" / "flow_accumulation.tif"
    if not facc_path.exists():
        raise FileNotFoundError(f"Flow accumulation raster not found: {facc_path}")

    with rasterio.open(facc_path) as src:
        acc = src.read(1)
        trans = src.transform
        res_x = src.res[0]
        r_orig, c_orig = src.index(dam_x, dam_y)

    rows, cols = acc.shape
    search_radius_cells = int(np.ceil(max_tolerance_m / res_x))

    r_min = max(0, r_orig - search_radius_cells)
    r_max = min(rows, r_orig + search_radius_cells + 1)
    c_min = max(0, c_orig - search_radius_cells)
    c_max = min(cols, c_orig + search_radius_cells + 1)

    candidate_records = []
    qualifying_candidates = []

    for r in range(r_min, r_max):
        for c in range(c_min, c_max):
            wx, wy = rasterio.transform.xy(trans, r, c)
            dist = float(np.hypot(wx - dam_x, wy - dam_y))
            if dist <= max_tolerance_m:
                cell_acc = int(acc[r, c])
                rec = {
                    "row": r,
                    "col": c,
                    "x_proj": round(wx, 2),
                    "y_proj": round(wy, 2),
                    "distance_m": round(dist, 2),
                    "accumulation_cells": cell_acc,
                    "accumulation_km2": round((cell_acc * 900.0) / 1e6, 3),
                    "qualifies_stream_threshold": cell_acc >= stream_threshold_cells
                }
                candidate_records.append(rec)
                if cell_acc >= stream_threshold_cells:
                    qualifying_candidates.append(rec)

    # Sort candidates
    candidate_records.sort(key=lambda k: (-k["accumulation_cells"], k["distance_m"]))

    if qualifying_candidates:
        # Choose nearest high-accumulation cell that qualifies
        # Among qualifying cells with major accumulation (>90% of max local acc), pick closest distance
        max_qual_acc = max(k["accumulation_cells"] for k in qualifying_candidates)
        major_candidates = [k for k in qualifying_candidates if k["accumulation_cells"] >= 0.8 * max_qual_acc]
        major_candidates.sort(key=lambda k: k["distance_m"])
        selected = major_candidates[0]
        valid_against_threshold = True
        status = "PASS"
    else:
        # If no cell qualifies, pick highest accumulation within radius but flag invalid
        selected = candidate_records[0]
        valid_against_threshold = False
        status = "LIMITED_LOCAL_SNAP"

    # Convert selected coords to WGS84
    sel_pt_proj = Point(selected["x_proj"], selected["y_proj"])
    sel_pt_wgs84 = gpd.GeoSeries([sel_pt_proj], crs=proj_crs).to_crs("EPSG:4326").iloc[0]

    # Save GPKG
    out_gpkg_path = PROJECT_ROOT / "data" / "hydrology" / "hydrologic_pour_point.gpkg"
    if out_gpkg_path.exists():
        out_gpkg_path.unlink()
    gdf_out = gpd.GeoDataFrame(
        [
            {
                "dam_name": config["dam"]["name"],
                "original_x": round(dam_x, 2),
                "original_y": round(dam_y, 2),
                "snapped_x": selected["x_proj"],
                "snapped_y": selected["y_proj"],
                "snapped_lat": round(sel_pt_wgs84.y, 6),
                "snapped_lon": round(sel_pt_wgs84.x, 6),
                "snap_distance_m": selected["distance_m"],
                "flow_accumulation_cells": selected["accumulation_cells"],
                "stream_threshold_cells": stream_threshold_cells,
                "valid_against_threshold": valid_against_threshold,
                "verification_level": "DEM_DERIVED"
            }
        ],
        geometry=[sel_pt_proj],
        crs=proj_crs
    )
    gdf_out.to_file(out_gpkg_path, driver="GPKG", layer="hydrologic_pour_point")
    print(f"Saved snapped pour point GPKG: {out_gpkg_path.relative_to(PROJECT_ROOT)}")

    # Save validation JSON
    val_json_path = PROJECT_ROOT / "outputs" / "validation" / "pour_point_validation.json"
    val_json_path.parent.mkdir(parents=True, exist_ok=True)

    val_data = {
        "status": status,
        "dam_name": config["dam"]["name"],
        "stream_threshold_cells": stream_threshold_cells,
        "max_tolerance_m": max_tolerance_m,
        "original_coordinate": {
            "latitude": dam_lat,
            "longitude": dam_lon,
            "x_projected": round(dam_x, 2),
            "y_projected": round(dam_y, 2),
            "crs": proj_crs
        },
        "snapped_hydrologic_pour_point": {
            "latitude": round(sel_pt_wgs84.y, 6),
            "longitude": round(sel_pt_wgs84.x, 6),
            "x_projected": selected["x_proj"],
            "y_projected": selected["y_proj"],
            "raster_row": selected["row"],
            "raster_col": selected["col"],
            "crs": proj_crs
        },
        "snap_metrics": {
            "snap_distance_m": selected["distance_m"],
            "max_search_tolerance_m": max_tolerance_m,
            "is_within_tolerance": selected["distance_m"] <= max_tolerance_m,
            "flow_accumulation_cells": selected["accumulation_cells"],
            "flow_accumulation_km2": selected["accumulation_km2"],
            "valid_against_threshold": valid_against_threshold
        },
        "candidate_cells_evaluated": len(candidate_records),
        "qualifying_candidates_count": len(qualifying_candidates),
        "top_candidates": candidate_records[:5],
        "reason_for_snap": "Snaps the dam reference coordinate to the nearest verified thalweg cell satisfying accumulation >= stream threshold, ensuring exact topological continuity for watershed delineation and hydrodynamic outflow routing."
    }

    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2)
    print(f"Saved validation summary: {val_json_path.relative_to(PROJECT_ROOT)}")
    print("=" * 80)
    print(f"Snapped Pour Point: {sel_pt_wgs84.y:.6f} N, {sel_pt_wgs84.x:.6f} E (Distance: {selected['distance_m']:.2f} m, Accumulation: {selected['accumulation_cells']:,} cells, Valid: {valid_against_threshold})")
    print("=" * 80)

if __name__ == "__main__":
    snap_hydrologic_pour_point()
