import netCDF4 as nc
import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import Polygon
import time
from pathlib import Path

root = Path("C:/JalRakshak-HD")
nc_path = root / "outputs/simulations/dflowfm/BHV_BASE/Bhavanisagar_DamBreak_map.nc"
ref_tif = root / "outputs/simulations/dflowfm/BHV_BASE/max_water_depth.tif"

with rasterio.open(ref_tif) as src:
    height = src.height
    width = src.width
    transform = src.transform
    crs = src.crs

ds = nc.Dataset(str(nc_path))
face_x_bnd = ds.variables["mesh2d_face_x_bnd"][:]
face_y_bnd = ds.variables["mesh2d_face_y_bnd"][:]
waterdepth = ds.variables["mesh2d_waterdepth"]

print(f"Raster dimensions: {width} x {height}")

# Build all face polygons
t0 = time.time()
polygons = []
for i in range(len(face_x_bnd)):
    xb = face_x_bnd[i]
    yb = face_y_bnd[i]
    # Filter out NaNs / masked values
    valid = ~np.isnan(xb) & ~np.isnan(yb) & (xb > 0)
    if np.sum(valid) >= 3:
        coords = list(zip(xb[valid], yb[valid]))
        coords.append(coords[0]) # close polygon
        polygons.append(Polygon(coords))
    else:
        polygons.append(None)

print(f"Built {len(polygons)} polygons in {time.time() - t0:.2f}s")

# Test rasterizing timestep 72
t1 = time.time()
d_72 = waterdepth[72, :]
wet_mask = (d_72 >= 0.05) & (d_72 < 100.0)

shapes = [(polygons[i], float(d_72[i])) for i in np.where(wet_mask)[0] if polygons[i] is not None]
rasterized = rasterize(
    shapes,
    out_shape=(height, width),
    transform=transform,
    fill=0.0,
    dtype=np.float32
)
t_end = time.time()

wet_px = np.sum(rasterized >= 0.05)
print(f"Rasterized T+12h (10,016 wet faces) into {wet_px} filled raster pixels in {t_end - t1:.3f}s")
print(f"Max depth in rasterized: {np.max(rasterized):.2f}m")

ds.close()
