"""
Acquire and Validate Real Bhavanisagar Reservoir Surface Geometry.
SIH PS 26161 - JalRakshak-HD Milestone M2 Repair.

Extracts multi-decadal satellite-observed water body polygons from
EC JRC / Google Global Surface Water (JRC/GSW1_4/GlobalSurfaceWater) via Earth Engine:
  1. Multi-decadal Water Occurrence >= 50% (multi_decadal_water_occurrence_ge_50)
  2. Persistent Water Core (seasonality >= 10 months)
Saves:
  - data/raw/hydrology/reservoir_surface_raw.geojson
  - data/hydrology/reservoir_surface.gpkg (EPSG:32643)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pyproj
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

import ee
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.validation import make_valid
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def acquire_reservoir_surface():
    config_path = PROJECT_ROOT / "configs" / "study_area.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    proj_crs = config["aoi"]["projected_crs"]

    raw_dir = PROJECT_ROOT / "data" / "raw" / "hydrology"
    proc_dir = PROJECT_ROOT / "data" / "hydrology"
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    raw_geojson_path = raw_dir / "reservoir_surface_raw.geojson"
    proc_gpkg_path = proc_dir / "reservoir_surface.gpkg"

    print("Initializing Google Earth Engine for JRC Global Surface Water extraction...")
    ee.Initialize(project="jalrakshak-hd")

    res_box = ee.Geometry.Rectangle([76.98, 11.42, 77.13, 11.53])
    gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")

    # Layer 1: multi_decadal_water_occurrence_ge_50
    occ_mask = gsw.select("occurrence").gte(50).selfMask().clip(res_box)
    occ_vectors = occ_mask.reduceToVectors(
        geometry=res_box,
        scale=30,
        geometryType="polygon",
        eightConnected=True,
        maxPixels=1e7,
    )
    occ_largest = occ_vectors.filter(ee.Filter.gt("count", 1000)).first().getInfo()
    occ_geom = shape(occ_largest["geometry"])
    if not occ_geom.is_valid:
        occ_geom = make_valid(occ_geom)

    # Layer 2: persistent_water_core (seasonality >= 10 months)
    seas_mask = gsw.select("seasonality").gte(10).selfMask().clip(res_box)
    seas_vectors = seas_mask.reduceToVectors(
        geometry=res_box,
        scale=30,
        geometryType="polygon",
        eightConnected=True,
        maxPixels=1e7,
    )
    seas_largest = seas_vectors.filter(ee.Filter.gt("count", 1000)).first().getInfo()
    seas_geom = shape(seas_largest["geometry"])
    if not seas_geom.is_valid:
        seas_geom = make_valid(seas_geom)

    features = [
        {
            "layer_name": "multi_decadal_water_occurrence_ge_50",
            "reservoir_name": "Bhavanisagar Reservoir",
            "source_dataset": "JRC/GSW1_4/GlobalSurfaceWater",
            "band_used": "occurrence",
            "threshold_criterion": "occurrence >= 50%",
            "scientific_meaning": "Multi-decadal historical surface water occurrence frequency >= 50% (1984-2021 Landsat archive). Represents median water surface presence, NOT legal boundary or FRL design boundary.",
            "observation_period": "1984–2021 Multi-Decadal Historical Record",
            "geometry_type": "REMOTE_SENSING_DERIVED_WATER_FREQUENCY_EXTENT",
            "verification_level": "REMOTE_SENSING_DERIVED",
            "geometry": occ_geom
        },
        {
            "layer_name": "persistent_water_core_seasonality_ge_10",
            "reservoir_name": "Bhavanisagar Reservoir",
            "source_dataset": "JRC/GSW1_4/GlobalSurfaceWater",
            "band_used": "seasonality",
            "threshold_criterion": "seasonality >= 10 months",
            "scientific_meaning": "Persistent reservoir water body present for >= 10 months per year across satellite record.",
            "observation_period": "1984–2021 Multi-Decadal Historical Record",
            "geometry_type": "REMOTE_SENSING_DERIVED_WATER_FREQUENCY_EXTENT",
            "verification_level": "REMOTE_SENSING_DERIVED",
            "geometry": seas_geom
        }
    ]

    gdf_wgs84 = gpd.GeoDataFrame(
        [
            {k: v for k, v in f.items() if k != "geometry"}
            for f in features
        ],
        geometry=[f["geometry"] for f in features],
        crs="EPSG:4326"
    )

    gdf_wgs84.to_file(raw_geojson_path, driver="GeoJSON")
    print(f"Saved raw reservoir surface GeoJSON: {raw_geojson_path.relative_to(PROJECT_ROOT)}")

    # Project to EPSG:32643
    gdf_proj = gdf_wgs84.to_crs(proj_crs)
    gdf_proj["area_km2"] = gdf_proj.geometry.area / 1e6
    gdf_proj["perimeter_km"] = gdf_proj.geometry.length / 1e3

    occ50_area = float(gdf_proj[gdf_proj["layer_name"] == "multi_decadal_water_occurrence_ge_50"]["area_km2"].iloc[0])
    seas10_area = float(gdf_proj[gdf_proj["layer_name"] == "persistent_water_core_seasonality_ge_10"]["area_km2"].iloc[0])

    gdf_proj.to_file(proc_gpkg_path, driver="GPKG", layer="reservoir_surface")
    print(f"Saved projected reservoir surface GeoPackage: {proc_gpkg_path.relative_to(PROJECT_ROOT)}")
    print(f"  Occurrence >= 50% Area: {occ50_area:.2f} km2")
    print(f"  Seasonality >= 10mo Area: {seas10_area:.2f} km2")

    return raw_geojson_path, proc_gpkg_path, occ50_area, seas10_area

if __name__ == "__main__":
    acquire_reservoir_surface()
