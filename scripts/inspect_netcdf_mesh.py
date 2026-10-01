import netCDF4 as nc
import numpy as np
from pathlib import Path

root = Path("C:/JalRakshak-HD")
nc_path = root / "outputs/simulations/dflowfm/BHV_BASE/Bhavanisagar_DamBreak_map.nc"

ds = nc.Dataset(str(nc_path))
print("Variables in NetCDF:")
for v in ds.variables:
    print(f"  {v}: shape={ds.variables[v].shape}, dtype={ds.variables[v].dtype}")

node_x = ds.variables.get("mesh2d_node_x")
node_y = ds.variables.get("mesh2d_node_y")
face_nodes = ds.variables.get("mesh2d_face_nodes")
face_x = ds.variables.get("mesh2d_face_x")
face_y = ds.variables.get("mesh2d_face_y")
depth_var = ds.variables.get("mesh2d_waterdepth")

print(f"\nnode_x: {node_x.shape if node_x is not None else 'None'}")
print(f"face_nodes: {face_nodes.shape if face_nodes is not None else 'None'}")
print(f"face_x: {face_x.shape if face_x is not None else 'None'}")
print(f"waterdepth: {depth_var.shape if depth_var is not None else 'None'}")

# Check timestep 72 (T+12h, 43200s)
t_idx = 72
d_72 = depth_var[t_idx, :]
wet_mask_72 = d_72 >= 0.05
print(f"\nTimestep {t_idx} (T=43200s):")
print(f"  Total faces: {len(d_72)}")
print(f"  Wet faces (>=0.05m): {np.sum(wet_mask_72)}")
print(f"  Min positive depth: {np.min(d_72[wet_mask_72]):.4f} m")
print(f"  Max depth: {np.max(d_72[wet_mask_72]):.4f} m")
print(f"  P95 depth: {np.percentile(d_72[wet_mask_72], 95):.4f} m")

ds.close()
