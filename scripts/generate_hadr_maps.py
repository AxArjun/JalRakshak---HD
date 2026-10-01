"""
JalRakshak-HD: HADR Diagnostic Cartography Engine (Milestone M8)
==============================================================
Generates publication-quality diagnostic visualizations:
1. m8_hazard_classes.png: CWC / AIDR Guideline 7-3 Combined Hazard Severity (H1–H6)
2. m8_population_exposure.png: Gridded Population Density (WorldPop) & Severe Hazard Overlay
3. m8_building_exposure.png: Building Footprints (Google Open Buildings v3) & H5/H6 Structural Vulnerability
4. m8_critical_facilities.png: Critical Infrastructure (Healthcare, Education, Emergency) Exposure
5. m8_road_exposure.png: Transportation Network & Screened Bridge Exposure
6. m8_hadr_priority_zones.png: Delineated HADR Response Priority Zones (Ranks 1 to 6)

All maps strictly display:
- CRS: EPSG:32643 (WGS 84 / UTM Zone 43N)
- Title, Scale, North Arrow, Colorbar/Legend, and HYPOTHETICAL_BREACH_SCREENING classification banner.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pyproj
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import rasterio

ROOT_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = ROOT_DIR / "outputs" / "maps"
HADR_OUT_DIR = ROOT_DIR / "outputs" / "hadr"
HADR_DIR = ROOT_DIR / "data" / "hadr"
SIM_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
RIVER_PATH = ROOT_DIR / "data" / "hydrology" / "bhavani_mainstem_downstream.gpkg"
BREACH_PATH = ROOT_DIR / "data" / "dflowfm" / "breach_location.gpkg"

MAPS_DIR.mkdir(parents=True, exist_ok=True)

# Standard CWC / AIDR Guideline 7-3 Colors
# H1: Light Cyan/Green, H2: Greenish-Yellow, H3: Yellow, H4: Orange, H5: Red, H6: Dark Purple/Maroon
HAZ_COLORS = ["#ffffff00", "#7fc97f", "#beaed4", "#fdc086", "#ffff99", "#f0027f", "#386cb0"]
CWC_PALETTE = {
    1: ("#66c2a4", "H1: Generally Safe (D*V<=0.3, D<=0.3, V<=2.0)"),
    2: ("#b2df8a", "H2: Unsafe for Small Vehicles (D*V<=0.6, D<=0.5)"),
    3: ("#fee08b", "H3: Unsafe for Vehicles & Elderly (D*V<=0.6, D<=1.2)"),
    4: ("#fdae61", "H4: Unsafe for People & Vehicles (D*V<=1.0, D<=2.0)"),
    5: ("#f46d43", "H5: Structural Damage to Buildings (D*V<=4.0, D<=4.0)"),
    6: ("#a50026", "H6: Complete Building Failure Vulnerability (D*V>4.0)"),
}


def add_map_decorations(ax, title: str):
    """Add standard North Arrow, Title, Subtitle, and Banner."""
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("UTM Easting [m] (EPSG:32643)", fontsize=10)
    ax.set_ylabel("UTM Northing [m] (EPSG:32643)", fontsize=10)
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.grid(True, linestyle="--", alpha=0.4, color="gray")

    # North Arrow
    ax.annotate("N", xy=(0.04, 0.92), xytext=(0.04, 0.84),
                xycoords="axes fraction",
                ha="center", va="center", fontsize=12, fontweight="bold",
                arrowprops=dict(facecolor="black", width=2.5, headwidth=8))

    # Banner
    plt.figtext(0.5, 0.015,
                "CLASSIFICATION: HYPOTHETICAL_BREACH_SCREENING | JALRAKSHAK-HD M8 (AIDR 7-3 / CWC STANDARD) | NOT FOR DIRECT RESCUE DISPATCH",
                ha="center", fontsize=8.5, fontweight="bold", color="darkred",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff2f2", edgecolor="darkred", lw=1.2))


def generate_hazard_classes_map():
    print("Generating Map 1: CWC Hazard Severity Classes...")
    fig, ax = plt.subplots(figsize=(13, 8), dpi=250)

    # Load river & breach
    river_gdf = gpd.read_file(RIVER_PATH)
    breach_gdf = gpd.read_file(BREACH_PATH)

    # Load hazard raster
    with rasterio.open(HADR_OUT_DIR / "hazard_class.tif") as src:
        haz_arr = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

    # Colormap for H1 to H6
    colors = ["#ffffff00", "#66c2a4", "#b2df8a", "#fee08b", "#fdae61", "#f46d43", "#a50026"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5], cmap.N)

    im = ax.imshow(haz_arr, extent=extent, cmap=cmap, norm=norm, origin="upper", zorder=2)
    river_gdf.plot(ax=ax, color="#1f78b4", linewidth=1.2, linestyle="--", label="Bhavani Mainstem", zorder=3)
    breach_gdf.plot(ax=ax, color="black", marker="X", markersize=120, label="Bhavanisagar Breach Location", zorder=4)

    # Custom Legend
    legend_patches = [
        mpatches.Patch(color=c_info[0], label=f"{k}: {c_info[1]}")
        for k, c_info in CWC_PALETTE.items()
    ]
    legend_patches.append(mpatches.Patch(color="#1f78b4", label="Bhavani River Mainstem"))
    ax.legend(handles=legend_patches, loc="lower right", fontsize=8, framealpha=0.92, title="CWC / AIDR Hazard Vulnerability Classes")

    add_map_decorations(ax, "JalRakshak-HD: Hydraulic Hazard Severity (CWC / AIDR Guideline 7-3)")
    out_path = MAPS_DIR / "m8_hazard_classes.png"
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    plt.savefig(out_path)
    plt.close()
    print(f"[OK] Saved: {out_path}")


def generate_population_exposure_map():
    print("Generating Map 2: Population Exposure Overlay...")
    fig, ax = plt.subplots(figsize=(13, 8), dpi=250)

    river_gdf = gpd.read_file(RIVER_PATH)
    inundation_gdf = gpd.read_file(SIM_DIR / "inundation_extent.gpkg")

    # Load WorldPop raster
    with rasterio.open(HADR_DIR / "population_projected.tif") as src_wp:
        wp_arr = np.maximum(src_wp.read(1), 0.0)
        extent_wp = [src_wp.bounds.left, src_wp.bounds.right, src_wp.bounds.bottom, src_wp.bounds.top]

    wp_masked = np.ma.masked_where(wp_arr < 0.5, wp_arr)
    im = ax.imshow(wp_masked, extent=extent_wp, cmap="YlOrRd", origin="upper", zorder=2, alpha=0.85)
    
    inundation_gdf.boundary.plot(ax=ax, color="#08519c", linewidth=1.5, label="Flood Inundation Extent (M5)", zorder=3)
    river_gdf.plot(ax=ax, color="#2171b5", linewidth=1.0, linestyle=":", zorder=3)

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("WorldPop 2020 Density [people / 100m cell]", fontsize=9)

    add_map_decorations(ax, "JalRakshak-HD: Gridded Population Exposure Overlay (WorldPop 2020)")
    out_path = MAPS_DIR / "m8_population_exposure.png"
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    plt.savefig(out_path)
    plt.close()
    print(f"[OK] Saved: {out_path}")


def generate_building_exposure_map():
    print("Generating Map 3: Building Footprints Exposure...")
    fig, ax = plt.subplots(figsize=(13, 8), dpi=250)

    inundation_gdf = gpd.read_file(SIM_DIR / "inundation_extent.gpkg")
    buildings_gdf = gpd.read_file(HADR_OUT_DIR / "building_exposure.gpkg")
    river_gdf = gpd.read_file(RIVER_PATH)

    inundation_gdf.plot(ax=ax, color="#deebf7", edgecolor="#9ecae1", linewidth=0.8, alpha=0.6, zorder=1)
    river_gdf.plot(ax=ax, color="#3182bd", linewidth=1.0, linestyle="--", zorder=2)

    # Plot buildings by structural vulnerability
    bld_h1_h4 = buildings_gdf[buildings_gdf["hazard_code"] < 5]
    bld_h5_h6 = buildings_gdf[buildings_gdf["hazard_code"] >= 5]

    if len(bld_h1_h4) > 0:
        bld_h1_h4.plot(ax=ax, color="#feb24c", edgecolor="none", markersize=1.5, label=f"H1–H4 Exposure ({len(bld_h1_h4):,} bldgs)", zorder=3)
    if len(bld_h5_h6) > 0:
        bld_h5_h6.plot(ax=ax, color="#cb181d", edgecolor="none", markersize=2.0, label=f"H5/H6 Structural Vulnerability ({len(bld_h5_h6):,} bldgs)", zorder=4)

    ax.legend(loc="lower right", fontsize=9, framealpha=0.92, title="Google Open Buildings v3 (conf>=0.75)")
    add_map_decorations(ax, "JalRakshak-HD: Building Exposure & Structural Damage Vulnerability")
    out_path = MAPS_DIR / "m8_building_exposure.png"
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    plt.savefig(out_path)
    plt.close()
    print(f"[OK] Saved: {out_path}")


def generate_critical_facilities_map():
    print("Generating Map 4: Critical Facilities Exposure...")
    fig, ax = plt.subplots(figsize=(13, 8), dpi=250)

    inundation_gdf = gpd.read_file(SIM_DIR / "inundation_extent.gpkg")
    river_gdf = gpd.read_file(RIVER_PATH)
    fac_gdf = gpd.read_file(HADR_DIR / "critical_facilities.gpkg")

    inundation_gdf.plot(ax=ax, color="#eff3ff", edgecolor="#bdd7e7", linewidth=0.8, zorder=1)
    river_gdf.plot(ax=ax, color="#2b8cbe", linewidth=1.2, linestyle="--", zorder=2)

    # Categories
    cat_markers = {
        "healthcare": ("#d73027", "s", "Healthcare Facility"),
        "education": ("#7570b3", "^", "Educational Institution"),
        "emergency_service": ("#e7298a", "D", "Emergency Services / Police / Fire"),
        "government": ("#1b9e77", "o", "Government / Townhall"),
        "community_assembly": ("#d95f02", "P", "Community Assembly"),
        "other": ("#666666", "*", "Other Facility"),
    }

    for cat, (col, mkr, lbl) in cat_markers.items():
        sub = fac_gdf[fac_gdf["category"] == cat]
        if len(sub) > 0:
            sub.plot(ax=ax, color=col, marker=mkr, markersize=65, edgecolor="black", linewidth=0.6, label=f"{lbl} ({len(sub)})", zorder=4)

    ax.legend(loc="lower right", fontsize=9, framealpha=0.92, title="OSM Critical Infrastructure")
    add_map_decorations(ax, "JalRakshak-HD: Critical Infrastructure & Public Facility Exposure")
    out_path = MAPS_DIR / "m8_critical_facilities.png"
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    plt.savefig(out_path)
    plt.close()
    print(f"[OK] Saved: {out_path}")


def generate_road_exposure_map():
    print("Generating Map 5: Transportation & Bridge Exposure...")
    fig, ax = plt.subplots(figsize=(13, 8), dpi=250)

    inundation_gdf = gpd.read_file(SIM_DIR / "inundation_extent.gpkg")
    river_gdf = gpd.read_file(RIVER_PATH)
    roads_gdf = gpd.read_file(HADR_OUT_DIR / "road_exposure.gpkg")

    inundation_gdf.plot(ax=ax, color="#f7fbff", edgecolor="#c6dbef", linewidth=0.8, zorder=1)
    river_gdf.plot(ax=ax, color="#08519c", linewidth=1.5, zorder=2)

    # Roads by hazard
    roads_gdf.plot(ax=ax, column="hazard_class", cmap="magma", linewidth=1.4, legend=True,
                   legend_kwds={"loc": "lower right", "title": "Road Hazard Severity (AIDR 7-3)", "fontsize": 8}, zorder=3)

    # Screened bridges
    bridges = roads_gdf[roads_gdf["bridge"].isin(["yes", "true", "viaduct"]) | roads_gdf["name"].str.contains("Bridge|Palam", case=False, na=False)]
    if len(bridges) > 0:
        bridge_pts = bridges.geometry.interpolate(0.5, normalized=True)
        gpd.GeoSeries(bridge_pts).plot(ax=ax, color="cyan", marker="o", markersize=50, edgecolor="black", label=f"Screened Bridges ({len(bridges)})", zorder=4)

    add_map_decorations(ax, "JalRakshak-HD: Hydraulically Exposed Road Segments & Bridges")
    out_path = MAPS_DIR / "m8_road_exposure.png"
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    plt.savefig(out_path)
    plt.close()
    print(f"[OK] Saved: {out_path}")


def generate_priority_zones_map():
    print("Generating Map 6: HADR Response Priority Zones...")
    fig, ax = plt.subplots(figsize=(13, 8), dpi=250)

    river_gdf = gpd.read_file(RIVER_PATH)
    zones_gdf = gpd.read_file(HADR_OUT_DIR / "response_zones.gpkg")
    settlements_gdf = gpd.read_file(HADR_DIR / "settlements.gpkg")

    # Plot zones with distinct qualitative palette
    zone_colors = ["#e41a1c", "#ff7f00", "#ffff33", "#4daf4a", "#377eb8", "#984ea3"]
    for idx, row in zones_gdf.iterrows():
        col = zone_colors[idx % len(zone_colors)]
        gpd.GeoSeries([row.geometry]).plot(ax=ax, color=col, alpha=0.55, edgecolor="black", linewidth=1.5, zorder=2)
        
        # Add label for priority rank
        centroid = row.geometry.centroid
        ax.annotate(
            f"RANK {row['priority_rank']}\n{row['locality_name']}\nArr: {row['earliest_arrival_hr']:.1f}h | Pop: {row['population_worldpop']:,.0f}",
            xy=(centroid.x, centroid.y),
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.88, edgecolor="black", lw=0.8),
            zorder=5
        )

    river_gdf.plot(ax=ax, color="#08519c", linewidth=1.5, linestyle="--", label="Bhavani River Mainstem", zorder=3)
    settlements_gdf.plot(ax=ax, color="black", marker="*", markersize=90, label="Key Settlements", zorder=4)

    ax.legend(loc="lower right", fontsize=9, framealpha=0.92)
    add_map_decorations(ax, "JalRakshak-HD: Operational HADR Response Priority Zones (Ranks 1 to 6)")
    out_path = MAPS_DIR / "m8_hadr_priority_zones.png"
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    plt.savefig(out_path)
    plt.close()
    print(f"[OK] Saved: {out_path}")


def main():
    print("=" * 80)
    print(" JALRAKSHAK-HD: DIAGNOSTIC CARTOGRAPHY SUITE (M8)")
    print("=" * 80)

    generate_hazard_classes_map()
    generate_population_exposure_map()
    generate_building_exposure_map()
    generate_critical_facilities_map()
    generate_road_exposure_map()
    generate_priority_zones_map()

    print("\n=== All 6 Diagnostic Maps Generated Successfully ===")


if __name__ == "__main__":
    main()
