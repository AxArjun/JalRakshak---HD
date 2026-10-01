"""
JalRakshak-HD: D-Flow FM Model Builder (Milestone M5)
=====================================================
Constructs the complete downstream 2D D-Flow FM hydrodynamic model:
1. Downstream domain geometry from M1 AOI & Bhavani river mainstem
2. Mesh generation with meshkernel / hydrolib-core (uniform 100m grid, ~82,300 faces)
3. Direct interpolation of real SRTM-derived projected DEM (EPSG:32643)
4. Upstream breach inflow boundary (PLI + exact ExtForceFileNew BC)
5. Downstream non-reflective outflow boundary (PLI + riemannbnd BC)
6. Observation points at key chainages (1, 5, 10, 20, 30, 40, 50 km)
7. Model definition file (Bhavanisagar_DamBreak.mdu) & DIMR config
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.interpolate import NearestNDInterpolator
from shapely.geometry import LineString, Point
from shapely.ops import split

import meshkernel as mk
from hydrolib.core.dflowfm.net.models import Network

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "data" / "dflowfm" / "model"
HYDROGRAPH_DIR = ROOT_DIR / "data" / "dflowfm" / "hydrographs"
TERRAIN_PATH = ROOT_DIR / "data" / "terrain" / "dem_projected.tif"
AOI_PATH = ROOT_DIR / "data" / "processed" / "study_area" / "aoi_projected.gpkg"
RIVER_PATH = ROOT_DIR / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
BREACH_PATH = ROOT_DIR / "data" / "dflowfm" / "breach_location.gpkg"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"


def build_dflow_model():
    print("=" * 80)
    print(" JALRAKSHAK-HD: D-FLOW FM 2D MODEL GENERATION ENGINE (MILESTONE M5)")
    print("=" * 80)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load spatial inputs
    aoi_gdf = gpd.read_file(AOI_PATH)
    river_gdf = gpd.read_file(RIVER_PATH)
    breach_gdf = gpd.read_file(BREACH_PATH)

    aoi_poly = aoi_gdf.geometry.iloc[0]
    river_geom = river_gdf.geometry.iloc[0]
    breach_pt = breach_gdf.geometry.iloc[0]

    river_start = Point(river_geom.coords[0])
    river_end = Point(river_geom.coords[-1])

    print(f"Breach location:           ({breach_pt.x:.2f} m E, {breach_pt.y:.2f} m N)")
    print(f"Downstream mainstem start: ({river_start.x:.2f} m E, {river_start.y:.2f} m N)")
    print(f"Downstream mainstem end:   ({river_end.x:.2f} m E, {river_end.y:.2f} m N)")

    # 2. Construct upstream cutting line immediately below dam axis
    cut_x = 730400.0
    cut_line = LineString([(cut_x, 1255000.0), (cut_x, 1283000.0)])
    split_result = split(aoi_poly, cut_line)

    downstream_poly = None
    for geom in split_result.geoms:
        if geom.bounds[0] >= 730000.0:
            downstream_poly = geom
            break

    if downstream_poly is None:
        raise ValueError("Could not extract downstream polygon from AOI split!")

    domain_gdf = gpd.GeoDataFrame(
        [{"name": "Bhavani_Downstream_Domain", "description": "Downstream 2D hydrodynamic simulation domain for Bhavanisagar Dam breach"}],
        geometry=[downstream_poly],
        crs="EPSG:32643"
    )
    domain_path = MODEL_DIR / "domain.gpkg"
    domain_gdf.to_file(domain_path, driver="GPKG")
    print(f"[OK] Saved domain polygon: {domain_path}")
    print(f"     Domain Area: {downstream_poly.area / 1e6:.2f} km2 | Bounds: {downstream_poly.bounds}")

    # 3. Create Upstream Breach Boundary PLI
    upstream_pli_path = MODEL_DIR / "upstream_breach_boundary.pli"
    y_inflow_start = 1268400.0
    y_inflow_end = 1269600.0
    with open(upstream_pli_path, "w", encoding="utf-8") as f:
        f.write("upstream_breach_boundary\n")
        f.write("2 2\n")
        f.write(f"{cut_x:.2f} {y_inflow_start:.2f}\n")
        f.write(f"{cut_x:.2f} {y_inflow_end:.2f}\n")
    print(f"[OK] Created upstream boundary PLI: {upstream_pli_path}")

    # 4. Create Downstream Outflow Boundary PLI at Eastern Border
    downstream_pli_path = MODEL_DIR / "downstream_boundary.pli"
    outflow_x = 764100.0
    y_outflow_start = 1271000.0
    y_outflow_end = 1274000.0
    with open(downstream_pli_path, "w", encoding="utf-8") as f:
        f.write("downstream_boundary\n")
        f.write("2 2\n")
        f.write(f"{outflow_x:.2f} {y_outflow_start:.2f}\n")
        f.write(f"{outflow_x:.2f} {y_outflow_end:.2f}\n")
    print(f"[OK] Created downstream boundary PLI: {downstream_pli_path}")

    # 5. Build Computational 2D Mesh with Real Terrain
    dx = 100.0
    dy = 100.0
    bounds = downstream_poly.bounds
    x_min = math.floor(bounds[0] / dx) * dx
    y_min = math.floor(bounds[1] / dy) * dy
    x_max = math.ceil(bounds[2] / dx) * dx
    y_max = math.ceil(bounds[3] / dy) * dy

    print(f"Creating 2D grid: Extent ({x_min}, {y_min}, {x_max}, {y_max}), dx={dx}m, dy={dy}m ...")
    netw = Network()
    netw.mesh2d_create_rectilinear_within_extent(
        extent=(x_min, y_min, x_max, y_max),
        dx=dx,
        dy=dy
    )

    ext_coords = np.array(downstream_poly.exterior.coords)
    geom_list = mk.GeometryList(
        x_coordinates=ext_coords[:, 0],
        y_coordinates=ext_coords[:, 1]
    )

    netw.mesh2d_clip_mesh(
        geometrylist=geom_list,
        deletemeshoption=mk.DeleteMeshOption.INSIDE_AND_INTERSECTED,
        inside=False
    )

    mesh2d = netw._mesh2d
    node_xs = np.array(mesh2d.mesh2d_node_x, dtype=np.float64)
    node_ys = np.array(mesh2d.mesh2d_node_y, dtype=np.float64)
    num_nodes = len(node_xs)
    num_faces = len(mesh2d.mesh2d_face_x)
    num_edges = len(mesh2d.mesh2d_edge_x)
    print(f"Mesh generated: {num_nodes} nodes, {num_edges} edges, {num_faces} faces.")

    if num_faces > 150000:
        raise ValueError(f"Mesh face count ({num_faces}) exceeds safety limit of 150,000!")

    # Sample real DEM elevations onto mesh nodes
    print(f"Interpolating elevations from real DEM: {TERRAIN_PATH} ...")
    with rasterio.open(TERRAIN_PATH) as dem_src:
        dem_data = dem_src.read(1)
        dem_transform = dem_src.transform
        dem_nodata = dem_src.nodata

        coords = list(zip(node_xs, node_ys))
        raw_elevs = np.array([val[0] for val in dem_src.sample(coords)], dtype=np.float64)

        invalid_mask = (raw_elevs == dem_nodata) | (raw_elevs < -100.0) | np.isnan(raw_elevs)
        invalid_count = np.sum(invalid_mask)
        print(f"Direct valid samples: {num_nodes - invalid_count} / {num_nodes} (Nodata edge count: {invalid_count})")

        if invalid_count > 0:
            rows, cols = np.where((dem_data != dem_nodata) & (dem_data > -100.0) & (~np.isnan(dem_data)))
            step = 5
            sub_rows = rows[::step]
            sub_cols = cols[::step]
            sub_xs, sub_ys = rasterio.transform.xy(dem_transform, sub_rows, sub_cols)
            sub_zs = dem_data[sub_rows, sub_cols]

            interpolator = NearestNDInterpolator(np.column_stack((sub_xs, sub_ys)), sub_zs)
            filled_elevs = interpolator(node_xs[invalid_mask], node_ys[invalid_mask])
            raw_elevs[invalid_mask] = filled_elevs
            print(f"Filled {invalid_count} edge cells via NearestNDInterpolator from valid DEM surface.")

    mesh2d.mesh2d_node_z = raw_elevs
    net_path = MODEL_DIR / "Bhavani_2D_net.nc"
    netw.to_file(net_path)
    print(f"[OK] Saved 2D UGRID Mesh to: {net_path}")
    print(f"     Mesh Elevation Range: min={np.min(raw_elevs):.2f} m, max={np.max(raw_elevs):.2f} m, mean={np.mean(raw_elevs):.2f} m MSL")

    # 6. Convert M4 Hydrograph to D-Flow FM 2026.02 .bc file with exact node signal headers
    csv_hydrograph_path = HYDROGRAPH_DIR / "BHV_BASE.csv"
    if not csv_hydrograph_path.exists():
        raise FileNotFoundError(f"Missing M4 hydrograph: {csv_hydrograph_path}")

    df_hyd = pd.read_csv(csv_hydrograph_path)
    bc_path = MODEL_DIR / "BHV_BASE.bc"
    with open(bc_path, "w", encoding="utf-8") as f:
        for node_id in ["upstream_breach_boundary_0001", "upstream_breach_boundary_0002"]:
            f.write("[Forcing]\n")
            f.write(f"Name = {node_id}\n")
            f.write("Function = timeseries\n")
            f.write("Time-interpolation = linear\n")
            f.write("Quantity = time\n")
            f.write("Unit = minutes since 2026-01-01 00:00:00\n")
            f.write("Quantity = dischargebnd\n")
            f.write("Unit = m3/s\n")
            for _, row in df_hyd.iterrows():
                t_min = row["time_s"] / 60.0
                q_val = row["discharge_m3s"]
                f.write(f"{t_min:.4f} {q_val:.4f}\n")
            # Extend zero discharge to the end of the 30-hour simulation window (1800.0 minutes)
            f.write("1800.0000 0.0000\n\n")
    print(f"[OK] Generated D-Flow FM forcing file: {bc_path}")

    # Downstream boundary BC (riemannbnd non-reflective condition)
    outflow_bc_path = MODEL_DIR / "downstream_boundary.bc"
    with open(outflow_bc_path, "w", encoding="utf-8") as f:
        for node_id in ["downstream_boundary_0001", "downstream_boundary_0002"]:
            f.write("[Forcing]\n")
            f.write(f"Name = {node_id}\n")
            f.write("Function = constant\n")
            f.write("Quantity = riemannbnd\n")
            f.write("Unit = m/s\n")
            f.write("0.0\n\n")
    print(f"[OK] Generated downstream forcing file: {outflow_bc_path}")

    # 7. Create model.ext (Modern external forcing file with exact casing)
    ext_path = MODEL_DIR / "model.ext"
    with open(ext_path, "w", encoding="utf-8") as f:
        f.write("[Boundary]\n")
        f.write("quantity = dischargebnd\n")
        f.write("locationFile = upstream_breach_boundary.pli\n")
        f.write("forcingFile = BHV_BASE.bc\n\n")
        f.write("[Boundary]\n")
        f.write("quantity = riemannbnd\n")
        f.write("locationFile = downstream_boundary.pli\n")
        f.write("forcingFile = downstream_boundary.bc\n")
    print(f"[OK] Generated external forcing manifest: {ext_path}")

    # 8. Create Observation Points along Bhavani Mainstem
    target_chainages_m = [1000.0, 5000.0, 10000.0, 20000.0, 30000.0, 40000.0, 50000.0]
    station_records = []
    xyn_lines = []

    for dist_m in target_chainages_m:
        pt = river_geom.interpolate(dist_m)
        st_name = f"Station_{int(dist_m/1000)}km"
        station_records.append({
            "station_id": st_name,
            "chainage_km": dist_m / 1000.0,
            "chainage_m": dist_m,
            "x_utm": pt.x,
            "y_utm": pt.y,
            "description": f"Diagnostic observation point at {dist_m/1000:.1f} km along Bhavani mainstem"
        })
        xyn_lines.append(f"{pt.x:.3f} {pt.y:.3f} '{st_name}'\n")

    xyn_path = MODEL_DIR / "observation_points.xyn"
    with open(xyn_path, "w", encoding="utf-8") as f:
        f.writelines(xyn_lines)
    print(f"[OK] Saved observation points XYN: {xyn_path}")

    obs_gdf = gpd.GeoDataFrame(
        station_records,
        geometry=[Point(r["x_utm"], r["y_utm"]) for r in station_records],
        crs="EPSG:32643"
    )
    obs_gpkg_path = MODEL_DIR / "observation_points.gpkg"
    obs_gdf.to_file(obs_gpkg_path, driver="GPKG")
    print(f"[OK] Saved observation points GPKG: {obs_gpkg_path}")

    # 9. Create D-Flow FM MDU Configuration File
    # Full simulation duration = 30 hours = 108,000 s
    # Map interval = 600 s (10 min), His interval = 120 s (2 min)
    mdu_path = MODEL_DIR / "Bhavanisagar_DamBreak.mdu"
    mdu_content = f"""[general]
fileVersion = 1.09
fileType = modelDef
program = D-Flow FM
version = 1.2.184

[geometry]
NetFile = Bhavani_2D_net.nc
BedlevType = 3

[physics]
UnifFrictType = Manning
UnifFrictCoef = 0.035

[numerics]
CFLMax = 0.70
AdvecType = 3
Limtypmom = 4

[time]
RefDate = 20260101
Tstart = 0.0
Tstop = 108000.0
DtUser = 30.0
DtMax = 30.0
AutoTimestep = 1

[external forcing]
ExtForceFileNew = model.ext

[output]
ObsFile = observation_points.xyn
HisInterval = 120.0
MapInterval = 600.0
RstInterval = 0.0
WaqInterval = 0.0
FlowGeomFile = 0
"""
    with open(mdu_path, "w", encoding="utf-8") as f:
        f.write(mdu_content)
    print(f"[OK] Created D-Flow FM model definition: {mdu_path}")

    # 10. Create dimr_config.xml
    dimr_path = MODEL_DIR / "dimr_config.xml"
    dimr_xml = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<dimrConfig xmlns="http://schemas.deltares.nl/dimr" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schemas.deltares.nl/dimr http://schemas.deltares.nl/dimr/dimr_config.xsd">
  <documentation>
    <fileVersion>1.3</fileVersion>
    <createdBy>Deltares, DIMR-FM</createdBy>
    <creationDate>2026-09-25T14:30:00Z</creationDate>
  </documentation>
  <control>
    <parallel>
      <start name="DFlowFM" />
    </parallel>
  </control>
  <component name="DFlowFM">
    <library>dflowfm</library>
    <workingDir>.</workingDir>
    <inputFile>Bhavanisagar_DamBreak.mdu</inputFile>
  </component>
</dimrConfig>
"""
    with open(dimr_path, "w", encoding="utf-8") as f:
        f.write(dimr_xml)
    print(f"[OK] Created DIMR configuration: {dimr_path}")

    # 11. Create Roughness Manifest
    roughness_manifest = {
        "milestone": "M5",
        "hydraulic_roughness": {
            "friction_type": "Manning",
            "uniform_manning_n_s_m_third": 0.035,
            "classification": "MODEL_ASSUMPTION",
            "literature_reference": "Chow, V. T. (1959). Open-Channel Hydraulics, McGraw-Hill, Table 5-6 (Natural channels and agricultural floodplains: n = 0.030 - 0.040 s/m^(1/3)); Barnes, H. H. (1967) USGS WSP 1849.",
            "justification": "Standard baseline Manning roughness for natural alluvial river beds and agricultural floodplain terrain without synthetic micro-parameterization.",
            "limitations": "Spatially uniform roughness assumption; land-cover-specific spatial roughness refinement reserved for sensitivity studies."
        }
    }
    with open(VALIDATION_DIR / "m5_roughness_manifest.json", "w", encoding="utf-8") as f:
        json.dump(roughness_manifest, f, indent=2)
    print(f"[OK] Saved roughness manifest: {VALIDATION_DIR / 'm5_roughness_manifest.json'}")

    print("=" * 80)
    print(" D-FLOW FM 2D MODEL SETUP COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    build_dflow_model()
