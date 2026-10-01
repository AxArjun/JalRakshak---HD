#!/usr/bin/env python3
"""Generate Scientific Diagnostic Quicklook Maps for JalRakshak-HD.

Renders:
  - outputs/maps/m1_dem_overview.png
  - outputs/maps/m1_hillshade.png
  - outputs/maps/m1_slope.png
"""

from __future__ import annotations

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
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def draw_north_arrow_and_scale(ax, x_min, x_max, y_min, y_max, scale_len_km=10.0):
    """Draw a clean scientific North arrow and scale bar in map coordinates."""
    # North Arrow (top right)
    arrow_x = x_max - (x_max - x_min) * 0.08
    arrow_y = y_max - (y_max - y_min) * 0.12
    arrow_len = (y_max - y_min) * 0.08

    ax.annotate(
        "N",
        xy=(arrow_x, arrow_y + arrow_len),
        xytext=(arrow_x, arrow_y),
        arrowprops=dict(facecolor="white", edgecolor="black", width=2, headwidth=8),
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="black",
        bbox=dict(boxstyle="circle,pad=0.2", facecolor="white", edgecolor="black", alpha=0.9),
    )

    # Scale Bar (bottom left)
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
        fontsize=9,
        fontweight="bold",
        ha="center",
        bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none", alpha=0.8),
    )


def generate_dem_overview():
    dem_path = PROJECT_ROOT / "data" / "terrain" / "dem_projected.tif"
    dam_gpkg = PROJECT_ROOT / "data" / "processed" / "study_area" / "dam_point_projected.gpkg"
    out_png = PROJECT_ROOT / "outputs" / "maps" / "m1_dem_overview.png"
    out_png.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        nodata = src.nodata

    dem_masked = np.ma.masked_where((dem == nodata) | (dem < -100), dem)

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#e9ecef")

    im = ax.imshow(
        dem_masked,
        extent=extent,
        cmap="terrain",
        origin="upper",
        vmin=float(np.percentile(dem_masked.compressed(), 1)),
        vmax=float(np.percentile(dem_masked.compressed(), 99)),
    )

    # Plot dam point
    if dam_gpkg.is_file():
        dam_gdf = gpd.read_file(dam_gpkg)
        dam_gdf.plot(ax=ax, color="#d90429", markersize=90, edgecolor="white", linewidth=1.5, zorder=5)
        pt = dam_gdf.geometry.iloc[0]
        ax.text(
            pt.x + 800,
            pt.y + 600,
            f"Bhavanisagar Dam\n(11.4708° N, 77.1139° E)",
            color="#1b263b",
            fontweight="bold",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9, edgecolor="#d90429"),
            zorder=6,
        )

    # Draw North Arrow & Scale Bar
    draw_north_arrow_and_scale(ax, extent[0], extent[1], extent[2], extent[3], scale_len_km=10.0)

    # Title & Metadata
    ax.set_title("JalRakshak-HD — Bhavanisagar Study Area: Projected SRTM DEM Overview", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Easting (m) — UTM Zone 43N (EPSG:32643)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle="--", alpha=0.4, color="gray")

    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("Elevation (metres MSL)", fontsize=9, fontweight="bold")
    cbar.ax.tick_params(labelsize=8)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved DEM Overview map: {out_png.relative_to(PROJECT_ROOT)}")


def generate_hillshade_map():
    hs_path = PROJECT_ROOT / "data" / "terrain" / "hillshade.tif"
    dam_gpkg = PROJECT_ROOT / "data" / "processed" / "study_area" / "dam_point_projected.gpkg"
    out_png = PROJECT_ROOT / "outputs" / "maps" / "m1_hillshade.png"

    with rasterio.open(hs_path) as src:
        hs = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    fig.patch.set_facecolor("#f8f9fa")

    im = ax.imshow(hs, extent=extent, cmap="gray", origin="upper", vmin=0, vmax=255)

    if dam_gpkg.is_file():
        dam_gdf = gpd.read_file(dam_gpkg)
        dam_gdf.plot(ax=ax, color="#e63946", markersize=90, edgecolor="white", linewidth=1.5, zorder=5)

    draw_north_arrow_and_scale(ax, extent[0], extent[1], extent[2], extent[3], scale_len_km=10.0)

    ax.set_title("JalRakshak-HD — Bhavanisagar Study Area: Terrain Hillshade (Az: 315°, Alt: 45°)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Easting (m) — UTM Zone 43N (EPSG:32643)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle="--", alpha=0.3, color="yellow")

    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("Illumination Intensity (0-255)", fontsize=9, fontweight="bold")
    cbar.ax.tick_params(labelsize=8)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved Hillshade map: {out_png.relative_to(PROJECT_ROOT)}")


def generate_slope_map():
    slope_path = PROJECT_ROOT / "data" / "terrain" / "slope.tif"
    dam_gpkg = PROJECT_ROOT / "data" / "processed" / "study_area" / "dam_point_projected.gpkg"
    out_png = PROJECT_ROOT / "outputs" / "maps" / "m1_slope.png"

    with rasterio.open(slope_path) as src:
        slope = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        nodata = src.nodata

    slope_masked = np.ma.masked_where((slope == nodata) | (slope < 0), slope)

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    fig.patch.set_facecolor("#f8f9fa")

    im = ax.imshow(slope_masked, extent=extent, cmap="magma", origin="upper", vmin=0, vmax=35)

    if dam_gpkg.is_file():
        dam_gdf = gpd.read_file(dam_gpkg)
        dam_gdf.plot(ax=ax, color="#00f5d4", markersize=90, edgecolor="black", linewidth=1.5, zorder=5)

    draw_north_arrow_and_scale(ax, extent[0], extent[1], extent[2], extent[3], scale_len_km=10.0)

    ax.set_title("JalRakshak-HD — Bhavanisagar Study Area: Terrain Slope (Degrees)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Easting (m) — UTM Zone 43N (EPSG:32643)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle="--", alpha=0.3, color="white")

    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("Slope Angle (Degrees)", fontsize=9, fontweight="bold")
    cbar.ax.tick_params(labelsize=8)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved Slope map: {out_png.relative_to(PROJECT_ROOT)}")


def main() -> None:
    generate_dem_overview()
    generate_hillshade_map()
    generate_slope_map()


if __name__ == "__main__":
    main()
