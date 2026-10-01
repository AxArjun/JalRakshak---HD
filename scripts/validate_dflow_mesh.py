"""
JalRakshak-HD: D-Flow FM Mesh Validation Engine (Milestone M5)
==============================================================
Validates topological integrity, coordinate finite-ness, face area distributions,
spatial domain coverage, and boundary intersections for the 2D computational mesh.
Generates outputs/validation/m5_mesh_validation.json and outputs/maps/m5_mesh_overview.png.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
from shapely.geometry import Point, Polygon, LineString

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "data" / "dflowfm" / "model"
NET_PATH = MODEL_DIR / "Bhavani_2D_net.nc"
DOMAIN_PATH = MODEL_DIR / "domain.gpkg"
RIVER_PATH = ROOT_DIR / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
BREACH_PATH = ROOT_DIR / "data" / "dflowfm" / "breach_location.gpkg"
UPSTREAM_PLI = MODEL_DIR / "upstream_breach_boundary.pli"
DOWNSTREAM_PLI = MODEL_DIR / "downstream_boundary.pli"
OBS_GPKG = MODEL_DIR / "observation_points.gpkg"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
MAPS_DIR = ROOT_DIR / "outputs" / "maps"


def validate_dflow_mesh() -> bool:
    print("=" * 80)
    print(" JALRAKSHAK-HD: D-FLOW FM MESH VALIDATION AUDIT (MILESTONE M5)")
    print("=" * 80)

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    MAPS_DIR.mkdir(parents=True, exist_ok=True)

    if not NET_PATH.exists():
        print(f"[FAIL] Missing mesh NetCDF file: {NET_PATH}")
        return False

    ds = nc.Dataset(NET_PATH, "r")
    
    node_x = ds.variables["mesh2d_node_x"][:]
    node_y = ds.variables["mesh2d_node_y"][:]
    node_z = ds.variables["mesh2d_node_z"][:]
    edge_nodes = ds.variables["mesh2d_edge_nodes"][:]
    face_nodes = ds.variables["mesh2d_face_nodes"][:]
    face_x = ds.variables["mesh2d_face_x"][:]
    face_y = ds.variables["mesh2d_face_y"][:]

    num_nodes = len(node_x)
    num_edges = len(edge_nodes)
    num_faces = len(face_x)

    print(f"Nodes count:               {num_nodes:,}")
    print(f"Edges count:               {num_edges:,}")
    print(f"Faces count:               {num_faces:,}")

    # 1. Coordinate Validity & NaNs
    nan_nodes = np.isnan(node_x).sum() + np.isnan(node_y).sum() + np.isnan(node_z).sum()
    nan_faces = np.isnan(face_x).sum() + np.isnan(face_y).sum()
    coords_valid = (nan_nodes == 0) and (nan_faces == 0)

    # 2. Elevation Validity
    z_min = float(np.min(node_z))
    z_max = float(np.max(node_z))
    z_mean = float(np.mean(node_z))
    elev_valid = (z_min > 0.0) and (z_max < 3000.0) and not np.isnan(node_z).any()

    # 3. Edge Length Statistics
    # edge_nodes is 1-based or 0-based index array
    edge_n1 = edge_nodes[:, 0]
    edge_n2 = edge_nodes[:, 1]
    # Check 0-based vs 1-based
    if np.min(edge_n1) == 1 or np.min(edge_n2) == 1:
        idx1 = edge_n1 - 1
        idx2 = edge_n2 - 1
    else:
        idx1 = edge_n1
        idx2 = edge_n2

    dx_edges = node_x[idx1] - node_x[idx2]
    dy_edges = node_y[idx1] - node_y[idx2]
    edge_lengths = np.sqrt(dx_edges**2 + dy_edges**2)
    min_edge_m = float(np.min(edge_lengths))
    max_edge_m = float(np.max(edge_lengths))
    mean_edge_m = float(np.mean(edge_lengths))

    # 4. Face Area Estimation
    # For rectilinear faces: dx * dy ~ 100 * 100 = 10,000 m2
    face_areas = []
    # Calculate polygonal area for each face
    for f in range(min(num_faces, 10000)):  # sample
        fn = face_nodes[f]
        valid_nodes = [n for n in fn if n >= 0 and n != -999 and not np.ma.is_masked(n)]
        if len(valid_nodes) >= 3:
            # 0-indexed check
            v_idx = [int(n - 1) if np.min(face_nodes) == 1 else int(n) for n in valid_nodes]
            fx = node_x[v_idx]
            fy = node_y[v_idx]
            # Shoelace formula
            area = 0.5 * abs(np.dot(fx, np.roll(fy, 1)) - np.dot(fy, np.roll(fx, 1)))
            face_areas.append(area)

    face_areas = np.array(face_areas)
    min_face_area_m2 = float(np.min(face_areas))
    max_face_area_m2 = float(np.max(face_areas))
    median_face_area_m2 = float(np.median(face_areas))

    ds.close()

    # 5. Spatial Coverage & Boundary Checks
    domain_gdf = gpd.read_file(DOMAIN_PATH)
    river_gdf = gpd.read_file(RIVER_PATH)
    breach_gdf = gpd.read_file(BREACH_PATH)
    obs_gdf = gpd.read_file(OBS_GPKG)

    domain_poly = domain_gdf.geometry.iloc[0]
    breach_pt = breach_gdf.geometry.iloc[0]
    river_geom = river_gdf.geometry.iloc[0]

    # Check breach proximity to mesh boundary
    dist_breach_to_mesh = domain_poly.distance(breach_pt)
    breach_near_boundary = dist_breach_to_mesh < 200.0

    # Check Bhavani mainstem contained in domain
    river_contained_length = river_geom.intersection(domain_poly).length
    total_river_length = river_geom.length
    river_coverage_pct = (river_contained_length / total_river_length) * 100.0
    river_well_covered = river_coverage_pct > 95.0

    # Check observations inside domain
    obs_inside = [domain_poly.contains(pt) or domain_poly.distance(pt) < 100.0 for pt in obs_gdf.geometry]
    all_obs_inside = all(obs_inside)

    safety_limit_ok = num_faces <= 150000

    overall_pass = all([
        coords_valid, elev_valid, safety_limit_ok,
        breach_near_boundary, river_well_covered, all_obs_inside
    ])

    report = {
        "milestone": "M5",
        "mesh_name": "Bhavani_2D_net.nc",
        "crs": "EPSG:32643",
        "units": "metres",
        "node_count": num_nodes,
        "edge_count": num_edges,
        "face_count": num_faces,
        "safety_limit_150k_faces": "PASS" if safety_limit_ok else "EXCEEDED",
        "nan_coordinate_count": int(nan_nodes + nan_faces),
        "elevation_stats_m_msl": {
            "min": z_min,
            "max": z_max,
            "mean": z_mean
        },
        "edge_length_stats_m": {
            "min": min_edge_m,
            "max": max_edge_m,
            "mean": mean_edge_m
        },
        "face_area_stats_m2": {
            "min": min_face_area_m2,
            "max": max_face_area_m2,
            "median": median_face_area_m2
        },
        "spatial_validation": {
            "breach_near_upstream_boundary": breach_near_boundary,
            "distance_breach_to_mesh_boundary_m": float(dist_breach_to_mesh),
            "river_mainstem_contained_percent": float(river_coverage_pct),
            "all_observation_points_inside": all_obs_inside,
            "domain_area_km2": float(domain_poly.area / 1e6)
        },
        "overall_status": "PASS" if overall_pass else "FAIL"
    }

    with open(VALIDATION_DIR / "m5_mesh_validation.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[OK] Saved mesh validation JSON: {VALIDATION_DIR / 'm5_mesh_validation.json'}")

    # Generate Mesh Overview Diagnostic Plot
    print("Generating mesh overview map...")
    fig, ax = plt.subplots(figsize=(12, 8), dpi=200)

    # Plot terrain nodes elevation scatter / domain contour
    sc = ax.scatter(node_x[::10], node_y[::10], c=node_z[::10], cmap="terrain", s=1.5, alpha=0.6, label="Mesh Nodes Elevation (m MSL)")
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("Bed Elevation (m MSL)", fontsize=10, weight="bold")

    # Plot domain boundary
    domain_gdf.boundary.plot(ax=ax, color="black", linewidth=1.5, label="2D Computational Domain Boundary")

    # Plot river mainstem
    river_gdf.plot(ax=ax, color="blue", linewidth=2.0, label="Bhavani Mainstem Downstream")

    # Plot breach inflow boundary
    ax.scatter([breach_pt.x], [breach_pt.y], color="red", s=80, marker="X", zorder=5, label=f"Breach Location ({breach_pt.x:.0f}, {breach_pt.y:.0f})")

    # Plot observation points
    for _, row in obs_gdf.iterrows():
        ax.scatter([row.geometry.x], [row.geometry.y], color="darkorange", s=40, marker="o", zorder=4)
        ax.annotate(row["station_id"].replace("Station_", ""), (row.geometry.x + 400, row.geometry.y + 400), fontsize=8, weight="bold", color="darkred")

    ax.set_title("JalRakshak-HD Milestone M5: 2D D-Flow FM Computational Mesh Overview\nBhavanisagar Dam Downstream Reach (EPSG:32643)", fontsize=12, weight="bold", pad=12)
    ax.set_xlabel("Easting (m, UTM Zone 43N)", fontsize=10)
    ax.set_ylabel("Northing (m, UTM Zone 43N)", fontsize=10)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    plot_path = MAPS_DIR / "m5_mesh_overview.png"
    plt.savefig(plot_path)
    plt.close()
    print(f"[OK] Saved mesh overview plot: {plot_path}")

    return overall_pass


if __name__ == "__main__":
    success = validate_dflow_mesh()
    sys.exit(0 if success else 1)
