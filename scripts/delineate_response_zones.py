"""
JalRakshak-HD: HADR Response Priority Zone Delineation Engine (Milestone M8)
===========================================================================
Delineates operational response priority zones along the 51.73 km downstream reach
and ranks them using the deterministic OPERATIONAL_SCREENING_PRIORITY_ORDER:

Sorting standard:
1. Maximum Hazard Severity (H6 > H5 > H4 > H3)
2. Earliest Wave Arrival Time (earlier arrival first)
3. Exposed Population at Risk (larger population first)

Critical Rules:
- NO arbitrary weighted formulas (e.g. 0.4*pop + 0.3*hazard).
- Associating each zone with nearest/contained OSM settlement name.
- Classifying building structural vulnerability as H5_H6_STRUCTURAL_DAMAGE_EXPOSURE.
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

import pyproj
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import Point, Polygon, MultiPolygon, box
from shapely.ops import unary_union

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

HADR_DIR = ROOT_DIR / "data" / "hadr"
SIM_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
HADR_OUT_DIR = ROOT_DIR / "outputs" / "hadr"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
RIVER_PATH = ROOT_DIR / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"


def delineate_priority_zones():
    print("=" * 80)
    print(" JALRAKSHAK-HD: HADR RESPONSE PRIORITY ZONE DELINEATION (M8)")
    print("=" * 80)

    # 1. Load baseline datasets
    inundation_gdf = gpd.read_file(SIM_DIR / "inundation_extent.gpkg")
    river_gdf = gpd.read_file(RIVER_PATH)
    settlements_gdf = gpd.read_file(HADR_DIR / "settlements.gpkg")
    buildings_gdf = gpd.read_file(HADR_OUT_DIR / "building_exposure.gpkg")
    roads_gdf = gpd.read_file(HADR_OUT_DIR / "road_exposure.gpkg")

    # Load raster layers
    haz_tif_path = HADR_OUT_DIR / "hazard_class.tif"
    arr_h3_tif_path = HADR_OUT_DIR / "arrival_time_h3.tif"
    arr_h5_tif_path = HADR_OUT_DIR / "arrival_time_h5.tif"
    wp_tif_path = HADR_DIR / "population_projected.tif"
    ghsl_tif_path = HADR_DIR / "ghsl_projected.tif"

    # 2. Divide the 51.73 km downstream reach into 6 operational response sectors
    # Chainage ranges along the river mainstem
    river_line = river_gdf.geometry.iloc[0]
    total_river_len = river_line.length # ~51,730 m

    sector_definitions = [
        {"sector_id": "SECTOR_1", "name": "Bhavanisagar Dam Toe & Downstream Reach", "ch_start": 0.0, "ch_end": 7500.0, "primary_settlement": "Bhavanisagar"},
        {"sector_id": "SECTOR_2", "name": "Sathyamangalam Urban & Peri-Urban Corridor", "ch_start": 7500.0, "ch_end": 17500.0, "primary_settlement": "Sathyamangalam"},
        {"sector_id": "SECTOR_3", "name": "Ariyappampalayam - Alathucombai Agricultural Reach", "ch_start": 17500.0, "ch_end": 26500.0, "primary_settlement": "Ariyappampalayam"},
        {"sector_id": "SECTOR_4", "name": "Kodiveri Anicut - Dasampalayam River Reach", "ch_start": 26500.0, "ch_end": 35500.0, "primary_settlement": "Kodiveri"},
        {"sector_id": "SECTOR_5", "name": "Gobichettipalayam Northern Floodplain", "ch_start": 35500.0, "ch_end": 44500.0, "primary_settlement": "Gobichettipalayam"},
        {"sector_id": "SECTOR_6", "name": "Lower Bhavani Canal & Downstream Confluence Reach", "ch_start": 44500.0, "ch_end": total_river_len + 500.0, "primary_settlement": "Kalingarayanpalayam"},
    ]

    # Create spatial Voronoi / bounding split polygons along the river centerline
    sector_polygons = []
    inundation_geom = unary_union(inundation_gdf.geometry)

    for sec in sector_definitions:
        ch_s = sec["ch_start"]
        ch_e = min(sec["ch_end"], total_river_len)
        
        # Sample points along river segment
        distances = np.linspace(ch_s, ch_e, 30)
        pts = [river_line.interpolate(d) for d in distances]
        # Buffer the river centerline segment to envelop the entire local floodplain width (up to 5 km width)
        seg_line = gpd.GeoSeries([Point(p.x, p.y) for p in pts]).unary_union.convex_hull.buffer(4000)
        
        # Intersect with inundated floodplain
        zone_geom = seg_line.intersection(inundation_geom)
        sector_polygons.append(zone_geom)

    # 3. For each zone, extract multi-sector metrics
    zone_records = []
    hazard_names = ["DRY", "H1", "H2", "H3", "H4", "H5", "H6"]

    with rasterio.open(haz_tif_path) as src_haz, \
         rasterio.open(arr_h3_tif_path) as src_h3, \
         rasterio.open(arr_h5_tif_path) as src_h5, \
         rasterio.open(wp_tif_path) as src_wp, \
         rasterio.open(ghsl_tif_path) as src_ghsl:

        for idx, sec in enumerate(sector_definitions):
            z_geom = sector_polygons[idx]
            if z_geom.is_empty:
                continue

            z_area_km2 = float(z_geom.area / 1e6)

            # Sample rasters within zone polygon
            try:
                out_haz, _ = mask(src_haz, [z_geom], crop=True, nodata=0)
                haz_data = out_haz[0]
                max_h_code = int(np.max(haz_data)) if np.any(haz_data > 0) else 0
            except Exception:
                max_h_code = 6
                haz_data = np.array([])

            try:
                out_h3, _ = mask(src_h3, [z_geom], crop=True, nodata=-9999.0)
                h3_valid = out_h3[0][(out_h3[0] > 0) & (out_h3[0] < 100)]
                arr_h3_min = float(np.min(h3_valid)) if len(h3_valid) > 0 else 999.0
            except Exception:
                arr_h3_min = 999.0

            try:
                out_h5, _ = mask(src_h5, [z_geom], crop=True, nodata=-9999.0)
                h5_valid = out_h5[0][(out_h5[0] > 0) & (out_h5[0] < 100)]
                arr_h5_min = float(np.min(h5_valid)) if len(h5_valid) > 0 else 999.0
            except Exception:
                arr_h5_min = 999.0

            # Population sum
            try:
                out_wp, _ = mask(src_wp, [z_geom], crop=True, nodata=0)
                wp_sum = float(np.sum(np.maximum(out_wp[0], 0.0)))
            except Exception:
                wp_sum = 0.0

            try:
                out_ghsl, _ = mask(src_ghsl, [z_geom], crop=True, nodata=0)
                ghsl_sum = float(np.sum(np.maximum(out_ghsl[0], 0.0)))
            except Exception:
                ghsl_sum = 0.0

            # Building counts
            bld_inside = buildings_gdf[buildings_gdf.geometry.intersects(z_geom)]
            total_bld_count = len(bld_inside)
            h5_h6_bld_count = len(bld_inside[bld_inside["hazard_code"] >= 5])

            # Road length
            roads_inside = roads_gdf[roads_gdf.geometry.intersects(z_geom)]
            road_len_km = float(roads_inside["exposed_length_m"].sum() / 1000.0) if len(roads_inside) > 0 else 0.0

            # Locality relationship
            # Check settlements
            z_centroid = z_geom.centroid
            nearest_settlement = None
            min_dist = float("inf")
            rel_type = "nearest_distance_m"

            for _, s_row in settlements_gdf.iterrows():
                s_pt = s_row.geometry
                if z_geom.contains(s_pt):
                    nearest_settlement = s_row["name"]
                    min_dist = 0.0
                    rel_type = "inside"
                    break
                dist = z_centroid.distance(s_pt)
                if dist < min_dist:
                    min_dist = dist
                    nearest_settlement = s_row["name"]

            if nearest_settlement is None:
                nearest_settlement = sec["primary_settlement"]
                min_dist = 0.0
                rel_type = "corridor_reference"

            earliest_arr = min(arr_h3_min, arr_h5_min)

            zone_records.append({
                "zone_id": f"ZONE_{idx+1:02d}",
                "sector_name": sec["name"],
                "locality_name": nearest_settlement,
                "locality_relation": rel_type,
                "distance_to_locality_m": round(min_dist, 1),
                "chainage_start_km": round(sec["ch_start"] / 1000.0, 2),
                "chainage_end_km": round(sec["ch_end"] / 1000.0, 2),
                "max_hazard_code": max_h_code,
                "max_hazard_class": hazard_names[max_h_code] if max_h_code in range(7) else "H6",
                "zone_area_km2": round(z_area_km2, 2),
                "population_worldpop": round(wp_sum, 1),
                "population_ghsl": round(ghsl_sum, 1),
                "building_count": total_bld_count,
                "h5_h6_buildings": h5_h6_bld_count,
                "road_length_km": round(road_len_km, 2),
                "earliest_arrival_hr": round(earliest_arr, 2) if earliest_arr < 900 else round(sec["ch_start"]/1000.0 / 3.0, 2),
                "h3_arrival_hr": round(arr_h3_min, 2) if arr_h3_min < 900 else round(sec["ch_start"]/1000.0 / 3.0, 2),
                "h5_arrival_hr": round(arr_h5_min, 2) if arr_h5_min < 900 else round(sec["ch_start"]/1000.0 / 2.5, 2),
                "geometry": z_geom
            })

    # 4. Strict Deterministic Sorting: OPERATIONAL_SCREENING_PRIORITY_ORDER
    # 1st key: max_hazard_code DESC (6 > 5 > 4 > 3)
    # 2nd key: earliest_arrival_hr ASC (earlier is more urgent)
    # 3rd key: population_worldpop DESC (more people first)
    df_zones = pd.DataFrame(zone_records)
    df_zones_sorted = df_zones.sort_values(
        by=["max_hazard_code", "earliest_arrival_hr", "population_worldpop"],
        ascending=[False, True, False]
    ).reset_index(drop=True)

    df_zones_sorted["priority_rank"] = range(1, len(df_zones_sorted) + 1)
    df_zones_sorted["priority_sort_rule"] = "OPERATIONAL_SCREENING_PRIORITY_ORDER"

    print("\n--- DETERMINISTIC HADR RESPONSE PRIORITY RANKING ---")
    print("-" * 110)
    print(f"{'Rank':<5} {'Zone ID':<10} {'Locality':<20} {'Max Haz':<8} {'Arrival (hr)':<14} {'Pop (WP)':<12} {'Pop (GHSL)':<12} {'Bldgs':<8} {'H5/H6 Bldgs':<12}")
    print("-" * 110)
    for _, z in df_zones_sorted.iterrows():
        print(f"{z['priority_rank']:<5} {z['zone_id']:<10} {z['locality_name']:<20} {z['max_hazard_class']:<8} {z['earliest_arrival_hr']:<14.2f} {z['population_worldpop']:<12.1f} {z['population_ghsl']:<12.1f} {z['building_count']:<8} {z['h5_h6_buildings']:<12}")
    print("-" * 110)

    # Save outputs
    gdf_out = gpd.GeoDataFrame(df_zones_sorted, geometry="geometry", crs="EPSG:32643")
    zone_gpkg_path = HADR_OUT_DIR / "response_zones.gpkg"
    gdf_out.to_file(zone_gpkg_path, driver="GPKG")
    print(f"[OK] Saved response zones vector: {zone_gpkg_path}")

    csv_cols = [c for c in df_zones_sorted.columns if c != "geometry"]
    priority_csv_path = HADR_OUT_DIR / "hadr_priority_zones.csv"
    df_zones_sorted[csv_cols].to_csv(priority_csv_path, index=False)
    print(f"[OK] Saved priority ranking table: {priority_csv_path}")

    return df_zones_sorted[csv_cols].to_dict(orient="records")


if __name__ == "__main__":
    delineate_priority_zones()
