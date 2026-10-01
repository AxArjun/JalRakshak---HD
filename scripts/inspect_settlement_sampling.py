import rasterio
from rasterio.warp import transform
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import Point

root = Path("C:/JalRakshak-HD")

settlements = gpd.read_file(root / "outputs/dashboard/geojson/settlements.geojson")
zones_gdf = gpd.read_file(root / "outputs/hadr/response_zones_exclusive.gpkg")

depth_tif = root / "outputs/simulations/dflowfm/BHV_BASE/max_water_depth.tif"
vel_tif = root / "outputs/simulations/dflowfm/BHV_BASE/max_velocity.tif"
arr_tif = root / "outputs/simulations/dflowfm/BHV_BASE/arrival_time.tif"
haz_tif = root / "outputs/hadr/hazard_class.tif"

# Open raster datasets
r_depth = rasterio.open(depth_tif)
r_vel = rasterio.open(vel_tif)
r_arr = rasterio.open(arr_tif)
r_haz = rasterio.open(haz_tif)

print(f"Depth raster CRS: {r_depth.crs}, bounds: {r_depth.bounds}")
print(f"Zones GDF CRS: {zones_gdf.crs}")

# Reproject settlements to raster CRS (EPSG:32643) and check exact coordinate values
settlements_utm = settlements.to_crs(r_depth.crs)

results = []
for idx, row in settlements.iterrows():
    name = row['name']
    lat, lon = row['latitude'], row['longitude']
    pt_utm = settlements_utm.geometry.iloc[idx]
    
    # Sample rasters at (pt_utm.x, pt_utm.y)
    coords = [(pt_utm.x, pt_utm.y)]
    
    d_val = list(r_depth.sample(coords))[0][0]
    v_val = list(r_vel.sample(coords))[0][0]
    a_val = list(r_arr.sample(coords))[0][0]
    h_val = list(r_haz.sample(coords))[0][0]
    
    # Check zone intersection
    matched_zone = None
    for z_idx, z_row in zones_gdf.iterrows():
        if z_row.geometry.contains(pt_utm) or z_row.geometry.distance(pt_utm) < 500: # within zone polygon or buffer
            matched_zone = z_row
            break
            
    # Also check if within hydraulic raster bounds and valid non-nodata
    # Note nodata for depth/vel/arr:
    d_nodata = r_depth.nodata
    v_nodata = r_vel.nodata
    a_nodata = r_arr.nodata
    h_nodata = r_haz.nodata
    
    print(f"\nSettlement: {name} (lat={lat}, lon={lon}, UTM_x={pt_utm.x:.1f}, UTM_y={pt_utm.y:.1f})")
    print(f"  Sampled Depth: {d_val} (nodata={d_nodata})")
    print(f"  Sampled Velocity: {v_val} (nodata={v_nodata})")
    print(f"  Sampled Arrival: {a_val} (nodata={a_nodata})")
    print(f"  Sampled Hazard: {h_val} (nodata={h_nodata})")
    if matched_zone is not None:
        print(f"  Matched Zone: {matched_zone['zone_id']} - {matched_zone.get('locality', matched_zone.get('sector_name', ''))}")
    else:
        print(f"  Matched Zone: OUTSIDE")
