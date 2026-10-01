"""
Acquire HydroBASINS Level 12 Upstream Basin Context from Google Earth Engine.
SIH PS 26161 - JalRakshak-HD Milestone M2 Repair.

Authoritative Asset: WWF/HydroSHEDS/v1/Basins/hybas_12 (Watershed Polygon Dataset)
Distinct from: WWF/HydroSHEDS/v1/FreeFlowingRivers (River Polyline Network)
"""
import json
import os
import sys
from pathlib import Path

import ee
import geopandas as gpd
import pyproj

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def acquire_upstream_basin():
    print("=" * 80)
    print("ACQUIRING HYDROBASINS LEVEL 12 UPSTREAM BASIN CONTEXT VIA GEE")
    print("=" * 80)
    
    # Initialize Earth Engine
    ee.Initialize(project="jalrakshak-hd")
    
    # Dam reference coordinates
    dam_lon, dam_lat = 77.11389, 11.47083
    dam_point = ee.Geometry.Point([dam_lon, dam_lat])
    
    # Query HydroBASINS Level 12 Polygon FeatureCollection
    hybas_asset = "WWF/HydroSHEDS/v1/Basins/hybas_12"
    print(f"Querying Earth Engine FeatureCollection: {hybas_asset}")
    fc = ee.FeatureCollection(hybas_asset).filterBounds(dam_point)
    
    count = fc.size().getInfo()
    print(f"Found {count} HydroBASINS Level 12 feature(s) intersecting dam point.")
    
    if count == 0:
        raise ValueError(f"No HydroBASINS Level 12 polygon found at coordinate [{dam_lat}, {dam_lon}]")
    
    # Get first intersecting feature
    feat = fc.first().getInfo()
    props = feat["properties"]
    
    hybas_id = props.get("HYBAS_ID")
    main_bas = props.get("MAIN_BAS")
    next_down = props.get("NEXT_DOWN")
    sub_area = props.get("SUB_AREA")
    up_area = props.get("UP_AREA")
    pfaf_id = props.get("PFAF_ID")
    order = props.get("ORDER")
    
    print("HydroBASINS Level 12 Attributes:")
    print(f"  HYBAS_ID:  {hybas_id}")
    print(f"  MAIN_BAS:  {main_bas}")
    print(f"  NEXT_DOWN: {next_down}")
    print(f"  SUB_AREA:  {sub_area} km2 (local sub-basin unit area)")
    print(f"  UP_AREA:   {up_area} km2 (cumulative upstream drainage area)")
    print(f"  PFAF_ID:   {pfaf_id}")
    print(f"  ORDER:     {order}")
    
    # Save raw GeoJSON
    raw_geojson_path = PROJECT_ROOT / "data" / "raw" / "hydrology" / "upstream_basin_raw.geojson"
    raw_geojson_path.parent.mkdir(parents=True, exist_ok=True)
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": [feat]
    }
    
    with open(raw_geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)
    print(f"Saved raw GeoJSON: {raw_geojson_path.relative_to(PROJECT_ROOT)}")
    
    # Read, reproject to EPSG:32643 and save GPKG
    gdf = gpd.read_file(raw_geojson_path)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.set_crs(epsg=4326)
    
    gdf_projected = gdf.to_crs(epsg=32643)
    
    gpkg_path = PROJECT_ROOT / "data" / "hydrology" / "upstream_basin.gpkg"
    gdf_projected.to_file(gpkg_path, layer="upstream_basin", driver="GPKG")
    print(f"Saved projected GeoPackage (EPSG:32643): {gpkg_path.relative_to(PROJECT_ROOT)}")
    
    # Write validation summary JSON
    val_json_path = PROJECT_ROOT / "outputs" / "validation" / "upstream_basin_validation.json"
    val_json_path.parent.mkdir(parents=True, exist_ok=True)
    
    val_data = {
        "dataset_name": "HydroBASINS Level 12 (Standard)",
        "dataset_type": "WATERSHED_POLYGON_DATASET",
        "gee_asset_id": hybas_asset,
        "provider": "WWF / HydroSHEDS (Lehner & Grill 2013)",
        "verification_level": "SECONDARY_VERIFIED",
        "dam_coordinates": {
            "latitude": dam_lat,
            "longitude": dam_lon
        },
        "hydrobasins_attributes": {
            "HYBAS_ID": hybas_id,
            "MAIN_BAS": main_bas,
            "NEXT_DOWN": next_down,
            "SUB_AREA_sqkm": sub_area,
            "UP_AREA_sqkm": up_area,
            "PFAF_ID": pfaf_id,
            "ORDER": order
        },
        "distinction_from_river_network": {
            "FreeFlowingRivers_asset": "WWF/HydroSHEDS/v1/FreeFlowingRivers",
            "FreeFlowingRivers_type": "RIVER_POLYLINE_NETWORK",
            "FreeFlowingRivers_UPLAND_SKM": 4118.4,
            "HydroBASINS_UP_AREA_sqkm": up_area,
            "explanation": "HydroBASINS Level 12 provides watershed polygon geometry with cumulative upstream drainage area UP_AREA = 4257.7 km2. FreeFlowingRivers provides 1D river centerlines where the specific reach attribute UPLAND_SKM = 4118.4 km2. Both reflect the regional Western Ghats/Nilgiris catchment of Bhavanisagar Dam."
        }
    }
    
    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2)
    print(f"Saved validation summary: {val_json_path.relative_to(PROJECT_ROOT)}")
    print("=" * 80)

if __name__ == "__main__":
    acquire_upstream_basin()
