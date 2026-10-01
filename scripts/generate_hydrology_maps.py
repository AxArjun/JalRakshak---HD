"""
Generate Scientific Hydrologic Diagnostic Maps for JalRakshak-HD.
SIH PS 26161 - JalRakshak-HD Milestone M2 Repair.

Renders:
  - outputs/maps/m2_hydrology_overview.png
  - outputs/maps/m2_flow_accumulation.png
  - outputs/maps/m2_river_profile.png
  - outputs/maps/m2_reservoir_geometry.png
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import pyproj
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import rasterio

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def draw_map_decorations(ax, x_min, x_max, y_min, y_max, scale_len_km=10.0):
    arrow_x = x_max - (x_max - x_min) * 0.07
    arrow_y = y_max - (y_max - y_min) * 0.12
    arrow_len = (y_max - y_min) * 0.08

    ax.annotate(
        "N",
        xy=(arrow_x, arrow_y + arrow_len),
        xytext=(arrow_x, arrow_y),
        arrowprops=dict(facecolor="white", edgecolor="black", width=2, headwidth=8),
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="circle,pad=0.2", facecolor="white", edgecolor="black", alpha=0.9),
    )

    sb_x0 = x_min + (x_max - x_min) * 0.05
    sb_y0 = y_min + (y_max - y_min) * 0.06
    sb_len_m = scale_len_km * 1000.0

    ax.plot([sb_x0, sb_x0 + sb_len_m], [sb_y0, sb_y0], color="black", linewidth=4, solid_capstyle="butt")
    ax.plot([sb_x0, sb_x0 + sb_len_m], [sb_y0, sb_y0], color="white", linewidth=2, solid_capstyle="butt")
    ax.text(
        sb_x0 + sb_len_m / 2.0,
        sb_y0 + (y_max - y_min) * 0.025,
        f"{int(scale_len_km)} km",
        color="black",
        fontsize=8,
        fontweight="bold",
        ha="center",
        bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85),
    )


def generate_hydrology_overview():
    hs_path = PROJECT_ROOT / "data" / "terrain" / "hillshade.tif"
    network_gpkg = PROJECT_ROOT / "data" / "hydrology" / "bhavani_river_centerline.gpkg"
    mainstem_gpkg = PROJECT_ROOT / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
    res_gpkg = PROJECT_ROOT / "data" / "hydrology" / "reservoir_surface.gpkg"
    dam_gpkg = PROJECT_ROOT / "data" / "processed" / "study_area" / "dam_point_projected.gpkg"
    pour_gpkg = PROJECT_ROOT / "data" / "hydrology" / "hydrologic_pour_point.gpkg"
    catch_gpkg = PROJECT_ROOT / "data" / "hydrology" / "local_catchment.gpkg"
    basin_gpkg = PROJECT_ROOT / "data" / "hydrology" / "upstream_basin.gpkg"
    aoi_gpkg = PROJECT_ROOT / "data" / "processed" / "study_area" / "aoi_projected.gpkg"

    out_png = PROJECT_ROOT / "outputs" / "maps" / "m2_hydrology_overview.png"
    out_png.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(hs_path) as src:
        hs = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

    fig, ax = plt.subplots(figsize=(11, 7), dpi=200)
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#e9ecef")

    # Hillshade background
    ax.imshow(hs, extent=extent, cmap="gray", origin="upper", alpha=0.6)

    # HydroBASINS upstream basin outline
    if basin_gpkg.is_file():
        gpd.read_file(basin_gpkg).boundary.plot(ax=ax, color="#7b2cbf", linestyle=":", linewidth=1.5, label="HydroBASINS L12 Boundary")

    # AOI boundary
    if aoi_gpkg.is_file():
        gpd.read_file(aoi_gpkg).boundary.plot(ax=ax, color="#495057", linestyle="--", linewidth=1.5, label="Study AOI")

    # Local Catchment
    if catch_gpkg.is_file():
        gpd.read_file(catch_gpkg).plot(ax=ax, color="#4cc9f0", alpha=0.25, edgecolor="#4361ee", linewidth=1.2, label="Local D8 Catchment (361 km2, Truncated)")

    # Reservoir Polygon
    if res_gpkg.is_file():
        gpd.read_file(res_gpkg).plot(ax=ax, color="#0077b6", alpha=0.8, edgecolor="#03045e", linewidth=1.0, label="Observed Reservoir Extent (JRC GSW)")

    # Inflow River Network
    if network_gpkg.is_file():
        gpd.read_file(network_gpkg).plot(ax=ax, color="#00b4d8", linewidth=1.2, label="Bhavani & Moyar Inflows (OSM)")

    # Downstream Mainstem
    if mainstem_gpkg.is_file():
        gpd.read_file(mainstem_gpkg).plot(ax=ax, color="#d90429", linewidth=2.4, label="Downstream Bhavani Mainstem (51.7 km)")

    # Snapped Pour Point
    if pour_gpkg.is_file():
        gpd.read_file(pour_gpkg).plot(ax=ax, color="#ffb703", markersize=80, edgecolor="black", zorder=7, label="Snapped Pour Point (Acc: 401k cells)")

    # Dam Metadata Point
    if dam_gpkg.is_file():
        gpd.read_file(dam_gpkg).plot(ax=ax, color="#9d0208", markersize=100, edgecolor="white", linewidth=1.5, zorder=8, label="Dam Point (11.4708° N, 77.1139° E)")

    draw_map_decorations(ax, extent[0], extent[1], extent[2], extent[3], scale_len_km=10.0)

    ax.set_title("JalRakshak-HD — Bhavanisagar Hydrology & River Network Overview (M2 Repaired)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Easting (m) — UTM Zone 43N (EPSG:32643)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle=":", alpha=0.4, color="gray")

    ax.legend(loc="lower right", fontsize=7.5, framealpha=0.92, facecolor="white", edgecolor="#ced4da")

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved Hydrology Overview Map: {out_png.relative_to(PROJECT_ROOT)}")


def generate_flow_accumulation_map():
    facc_path = PROJECT_ROOT / "data" / "hydrology" / "flow_accumulation.tif"
    dam_gpkg = PROJECT_ROOT / "data" / "processed" / "study_area" / "dam_point_projected.gpkg"
    pour_gpkg = PROJECT_ROOT / "data" / "hydrology" / "hydrologic_pour_point.gpkg"
    out_png = PROJECT_ROOT / "outputs" / "maps" / "m2_flow_accumulation.png"

    with rasterio.open(facc_path) as src:
        acc = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        nodata = src.nodata

    acc_clean = np.where((acc > 0) & (acc != nodata), acc, 1)
    acc_log = np.log10(acc_clean)

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    fig.patch.set_facecolor("#f8f9fa")

    im = ax.imshow(acc_log, extent=extent, cmap="viridis", origin="upper", vmin=0, vmax=float(np.percentile(acc_log, 99.8)))

    if pour_gpkg.is_file():
        gpd.read_file(pour_gpkg).plot(ax=ax, color="#ffb703", markersize=80, edgecolor="black", zorder=6, label="Snapped Pour Point")

    if dam_gpkg.is_file():
        gpd.read_file(dam_gpkg).plot(ax=ax, color="#d90429", markersize=90, edgecolor="white", linewidth=1.5, zorder=5, label="Dam Coordinate")

    draw_map_decorations(ax, extent[0], extent[1], extent[2], extent[3], scale_len_km=10.0)

    ax.set_title("JalRakshak-HD — D8 Flow Accumulation Grid (Log10 Contributing Cells)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Easting (m) — UTM Zone 43N (EPSG:32643)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle=":", alpha=0.3, color="white")

    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("Log10(Upstream Contributing Cells)", fontsize=9, fontweight="bold")
    cbar.ax.tick_params(labelsize=8)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved Flow Accumulation Map: {out_png.relative_to(PROJECT_ROOT)}")


def generate_river_profile_chart():
    csv_path = PROJECT_ROOT / "data" / "hydrology" / "river_profile.csv"
    out_png = PROJECT_ROOT / "outputs" / "maps" / "m2_river_profile.png"

    chainage_km = []
    elevations = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["dem_elevation_m"]:
                chainage_km.append(float(row["chainage_m"]) / 1000.0)
                elevations.append(float(row["dem_elevation_m"]))

    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#ffffff")

    ax.plot(chainage_km, elevations, color="#0077b6", linewidth=2.0, label="Bhavani River Thalweg (Downstream Reach)")
    ax.fill_between(chainage_km, elevations, min(elevations) - 10, color="#caf0f8", alpha=0.6)

    # Reference levels
    ax.axhline(280.42, color="#d90429", linestyle="--", linewidth=1.5, label="CWC FRL (280.42 m MSL)")

    ax.set_title("JalRakshak-HD — Downstream Bhavani River Longitudinal Elevation Profile", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Downstream Distance / Chainage from Dam Outlet (km)", fontsize=9, fontweight="bold")
    ax.set_ylabel("Elevation (metres MSL)", fontsize=9, fontweight="bold")
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved River Profile Chart: {out_png.relative_to(PROJECT_ROOT)}")


def generate_reservoir_geometry_map():
    res_gpkg = PROJECT_ROOT / "data" / "hydrology" / "reservoir_surface.gpkg"
    dam_gpkg = PROJECT_ROOT / "data" / "processed" / "study_area" / "dam_point_projected.gpkg"
    mainstem_gpkg = PROJECT_ROOT / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
    hs_path = PROJECT_ROOT / "data" / "terrain" / "hillshade.tif"
    out_png = PROJECT_ROOT / "outputs" / "maps" / "m2_reservoir_geometry.png"

    with rasterio.open(hs_path) as src:
        hs = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    fig.patch.set_facecolor("#f8f9fa")

    ax.imshow(hs, extent=extent, cmap="gray", origin="upper", alpha=0.5)

    if res_gpkg.is_file():
        gdf_res = gpd.read_file(res_gpkg)
        gdf_res.plot(ax=ax, color="#0096c7", edgecolor="#023e8a", linewidth=1.5, alpha=0.85, label="JRC GSW Observed Water Frequency Extents")

    if mainstem_gpkg.is_file():
        gpd.read_file(mainstem_gpkg).plot(ax=ax, color="#d90429", linewidth=2.0, label="Downstream Bhavani Mainstem")

    if dam_gpkg.is_file():
        gpd.read_file(dam_gpkg).plot(ax=ax, color="#ffb703", markersize=110, edgecolor="black", linewidth=1.5, zorder=6, label="Dam Reference Point")

    draw_map_decorations(ax, extent[0], extent[1], extent[2], extent[3], scale_len_km=10.0)

    ax.set_title("JalRakshak-HD — Satellite-Observed Bhavanisagar Reservoir Geometry (JRC GSW)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Easting (m) — UTM Zone 43N (EPSG:32643)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved Reservoir Geometry Map: {out_png.relative_to(PROJECT_ROOT)}")


def main():
    generate_hydrology_overview()
    generate_flow_accumulation_map()
    generate_river_profile_chart()
    generate_reservoir_geometry_map()


if __name__ == "__main__":
    main()
