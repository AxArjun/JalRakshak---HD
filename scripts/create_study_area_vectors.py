#!/usr/bin/env python3
"""Create and project study area and dam vector files for JalRakshak-HD.

Generates:
  - data/raw/study_area/dam_point.geojson
  - data/raw/study_area/aoi_wgs84.geojson
  - data/processed/study_area/dam_point_projected.gpkg
  - data/processed/study_area/aoi_projected.gpkg
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pyproj
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
from shapely.geometry import Point, box
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_vectors() -> None:
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    dam_cfg = config["dam"]
    bbox_cfg = config["aoi"]["bbox_wgs84"]
    proj_crs = config["aoi"]["projected_crs"]

    raw_dir = PROJECT_ROOT / "data" / "raw" / "study_area"
    proc_dir = PROJECT_ROOT / "data" / "processed" / "study_area"
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    # 1. Dam Point GeoDataFrame
    dam_geom = Point(dam_cfg["longitude"], dam_cfg["latitude"])
    dam_gdf = gpd.GeoDataFrame(
        [
            {
                "name": dam_cfg["name"],
                "dam_type": dam_cfg["dam_type"],
                "river": config["river"]["name"],
                "state": config["study_area"]["state"],
                "district": config["study_area"]["district"],
                "lat": dam_cfg["latitude"],
                "lon": dam_cfg["longitude"],
            }
        ],
        geometry=[dam_geom],
        crs="EPSG:4326",
    )

    # 2. AOI Polygon GeoDataFrame
    aoi_geom = box(
        bbox_cfg["min_lon"],
        bbox_cfg["min_lat"],
        bbox_cfg["max_lon"],
        bbox_cfg["max_lat"],
    )
    aoi_gdf = gpd.GeoDataFrame(
        [
            {
                "study_area_id": config["study_area"]["id"],
                "name": config["study_area"]["name"],
                "min_lon": bbox_cfg["min_lon"],
                "min_lat": bbox_cfg["min_lat"],
                "max_lon": bbox_cfg["max_lon"],
                "max_lat": bbox_cfg["max_lat"],
            }
        ],
        geometry=[aoi_geom],
        crs="EPSG:4326",
    )

    # Save WGS84 GeoJSONs
    dam_point_raw = raw_dir / "dam_point.geojson"
    aoi_raw = raw_dir / "aoi_wgs84.geojson"

    dam_gdf.to_file(dam_point_raw, driver="GeoJSON")
    aoi_gdf.to_file(aoi_raw, driver="GeoJSON")

    # Reproject to UTM Zone 43N (EPSG:32643)
    dam_gdf_proj = dam_gdf.to_crs(proj_crs)
    aoi_gdf_proj = aoi_gdf.to_crs(proj_crs)

    dam_point_proc = proc_dir / "dam_point_projected.gpkg"
    aoi_proc = proc_dir / "aoi_projected.gpkg"

    dam_gdf_proj.to_file(dam_point_proc, driver="GPKG", layer="dam_point")
    aoi_gdf_proj.to_file(aoi_proc, driver="GPKG", layer="aoi")

    print(f"Saved: {dam_point_raw.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {aoi_raw.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {dam_point_proc.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {aoi_proc.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    create_vectors()
