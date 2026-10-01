"""
Acquire and Standardize Real Bhavani River Geometry for JalRakshak-HD.
SIH PS 26161 - JalRakshak-HD Milestone M2 Repair.

Separates:
  A. Total river-network features in AOI (data/hydrology/bhavani_river_centerline.gpkg)
  B. Connected downstream Bhavani mainstem only (data/hydrology/bhavani_mainstem_downstream.gpkg)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pyproj
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
import httpx
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import LineString, MultiLineString, Point, box, shape
from shapely.ops import linemerge, unary_union
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def fetch_river_osm(bbox_dict: dict) -> gpd.GeoDataFrame | None:
    min_lon, min_lat = bbox_dict["min_lon"], bbox_dict["min_lat"]
    max_lon, max_lat = bbox_dict["max_lon"], bbox_dict["max_lat"]

    query = f"""[out:json][timeout:30];
(
  way["waterway"="river"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out body geom;"""

    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]

    for ep in endpoints:
        try:
            print(f"Querying OpenStreetMap river geometry from {ep}...")
            resp = httpx.post(ep, data={"data": query}, timeout=25.0)
            if resp.status_code == 200 and resp.text.strip().startswith("{"):
                data = resp.json()
                elements = data.get("elements", [])
                if not elements:
                    continue

                records = []
                for el in elements:
                    geom_pts = el.get("geometry", [])
                    if len(geom_pts) >= 2:
                        coords = [(pt["lon"], pt["lat"]) for pt in geom_pts]
                        line = LineString(coords)
                        tags = el.get("tags", {})
                        records.append({
                            "osm_id": el.get("id"),
                            "name": tags.get("name", "Bhavani River"),
                            "name_en": tags.get("name:en", "Bhavani River"),
                            "waterway": tags.get("waterway", "river"),
                            "geometry": line,
                        })

                if records:
                    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
                    print(f"Successfully retrieved {len(gdf)} river segments from OpenStreetMap.")
                    return gdf
        except Exception as e:
            print(f"Overpass mirror {ep} failed: {e}")

    return None

def acquire_river_centerline():
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    bbox = config["aoi"]["bbox_wgs84"]
    proj_crs = config["aoi"]["projected_crs"]

    raw_dir = PROJECT_ROOT / "data" / "raw" / "hydrology"
    proc_dir = PROJECT_ROOT / "data" / "hydrology"
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    raw_geojson_path = raw_dir / "bhavani_river_raw.geojson"
    network_gpkg_path = proc_dir / "bhavani_river_centerline.gpkg"
    mainstem_gpkg_path = proc_dir / "bhavani_mainstem_downstream.gpkg"

    # Delete existing GPKG to avoid duplicate layer warnings
    if network_gpkg_path.exists():
        network_gpkg_path.unlink()
    if mainstem_gpkg_path.exists():
        mainstem_gpkg_path.unlink()

    # Step 1: Query or load raw GeoJSON
    if raw_geojson_path.exists():
        river_gdf = gpd.read_file(raw_geojson_path)
    else:
        river_gdf = fetch_river_osm(bbox)
        if river_gdf is not None:
            river_gdf.to_file(raw_geojson_path, driver="GeoJSON")

    # Project to EPSG:32643
    gdf_proj = river_gdf.to_crs(proj_crs)

    # Step 2: Extract valid DEM footprint for boundary clipping
    dem_path = PROJECT_ROOT / "data" / "terrain" / "dem_projected.tif"
    with rasterio.open(dem_path) as src:
        dem_arr = src.read(1)
        nodata = src.nodata
        valid_mask = (dem_arr != nodata) & (~np.isnan(dem_arr))
        polys = [shape(s) for s, val in shapes(valid_mask.astype(np.uint8), transform=src.transform) if val == 1]
        dem_footprint = unary_union(polys)

    # Save A: Full River Network in AOI
    gdf_network = gdf_proj.copy()
    gdf_network["geometry"] = gdf_network.geometry.intersection(dem_footprint)
    gdf_network = gdf_network[~gdf_network.geometry.is_empty].copy()
    gdf_network["length_km"] = gdf_network.geometry.length / 1000.0
    total_network_km = float(gdf_network["length_km"].sum())

    gdf_network.to_file(network_gpkg_path, driver="GPKG", layer="river_network")
    print(f"Saved total river network: {network_gpkg_path.relative_to(PROJECT_ROOT)} ({total_network_km:.2f} km total)")

    # Save B: Bhavani Mainstem Downstream of Dam (osm_id: 70237216)
    f2 = gdf_proj[gdf_proj["osm_id"] == 70237216].geometry.iloc[0]
    f2_clipped = f2.intersection(dem_footprint)

    # Ensure orientation is West to East (downstream)
    coords = list(f2_clipped.coords)
    if coords[0][0] > coords[-1][0]:
        coords = coords[::-1]
    f2_oriented = LineString(coords)

    dam_pt = Point(config["dam"]["longitude"], config["dam"]["latitude"])
    dam_pt_proj = gpd.GeoSeries([dam_pt], crs="EPSG:4326").to_crs(proj_crs).iloc[0]
    start_dist_from_dam = float(Point(coords[0]).distance(dam_pt_proj))
    mainstem_km = float(f2_oriented.length / 1000.0)

    gdf_mainstem = gpd.GeoDataFrame(
        [
            {
                "river_name": "Bhavani River Mainstem",
                "reach_type": "DOWNSTREAM_MAINSTEM",
                "source_osm_id": 70237216,
                "flow_direction": "WEST_TO_EAST_DOWNSTREAM",
                "length_km": round(mainstem_km, 3),
                "start_distance_from_dam_m": round(start_dist_from_dam, 2),
                "verification_level": "SECONDARY_VERIFIED"
            }
        ],
        geometry=[f2_oriented],
        crs=proj_crs
    )

    gdf_mainstem.to_file(mainstem_gpkg_path, driver="GPKG", layer="mainstem_downstream")
    print(f"Saved downstream Bhavani mainstem: {mainstem_gpkg_path.relative_to(PROJECT_ROOT)}")
    print(f"  Mainstem length: {mainstem_km:.2f} km")
    print(f"  Start distance from dam: {start_dist_from_dam:.2f} m")

    return network_gpkg_path, mainstem_gpkg_path, total_network_km, mainstem_km

if __name__ == "__main__":
    acquire_river_centerline()
