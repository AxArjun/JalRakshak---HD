import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

root = Path("C:/JalRakshak-HD")

depth_tif = root / "outputs/simulations/dflowfm/BHV_BASE/max_water_depth.tif"
vel_tif = root / "outputs/simulations/dflowfm/BHV_BASE/max_velocity.tif"
arr_tif = root / "outputs/simulations/dflowfm/BHV_BASE/arrival_time.tif"
haz_tif = root / "outputs/hadr/hazard_class.tif"
zones_gpkg = root / "outputs/hadr/response_zones_exclusive.gpkg"
zones_csv = root / "outputs/hadr/hadr_priority_zones.csv"

zg_df = gpd.read_file(zones_gpkg)
zc_df = pd.read_csv(zones_csv)

print("Authoritative Response Zones:")
for idx, row in zc_df.iterrows():
    print(f"  {row['zone_id']}: {row['sector_name']} | Locality: {row['locality_name']} | Chainage: {row['chainage_start_km']} - {row['chainage_end_km']} km | Arrival: {row['earliest_arrival_hr']}h | Max Haz: {row['max_hazard_class']}")

# Let's perform zonal sampling of the hydraulic rasters within each zone geometry
import rasterio.mask

r_depth = rasterio.open(depth_tif)
r_vel = rasterio.open(vel_tif)
r_arr = rasterio.open(arr_tif)
r_haz = rasterio.open(haz_tif)

print("\nZonal statistics per authoritative response zone polygon:")
for idx, row in zg_df.iterrows():
    zid = row['zone_id']
    loc = row.get('locality', row.get('sector_name', ''))
    geom = [row.geometry]
    
    out_d, _ = rasterio.mask.mask(r_depth, geom, crop=True, nodata=-9999.0)
    out_v, _ = rasterio.mask.mask(r_vel, geom, crop=True, nodata=-9999.0)
    out_a, _ = rasterio.mask.mask(r_arr, geom, crop=True, nodata=-9999.0)
    out_h, _ = rasterio.mask.mask(r_haz, geom, crop=True, nodata=0)
    
    d_valid = out_d[out_d > 0]
    v_valid = out_v[out_v > 0]
    a_valid = out_a[out_a >= 0]
    h_valid = out_h[out_h > 0]
    
    d_max = float(np.max(d_valid)) if len(d_valid) > 0 else None
    d_mean = float(np.mean(d_valid)) if len(d_valid) > 0 else None
    v_max = float(np.max(v_valid)) if len(v_valid) > 0 else None
    v_mean = float(np.mean(v_valid)) if len(v_valid) > 0 else None
    a_min = float(np.min(a_valid)) if len(a_valid) > 0 else None
    h_max = int(np.max(h_valid)) if len(h_valid) > 0 else None
    
    print(f"  {zid} ({loc}):")
    print(f"    Arrival min: {a_min:.2f}h, Depth max: {d_max:.2f}m (mean: {d_mean:.2f}m), Vel max: {v_max:.2f}m/s (mean: {v_mean:.2f}m/s), Hazard max: H{h_max}")
