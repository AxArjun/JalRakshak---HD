"""
JalRakshak-HD: Cross-Solver Comparison Visualization Engine (Milestone M7)
==========================================================================
Generates high-resolution diagnostic maps and comparative profiles:
1. outputs/maps/m7_common_gauges.png
2. outputs/maps/m7_depth_comparison.png
3. outputs/maps/m7_velocity_comparison.png
4. outputs/maps/m7_normalized_depth.png
5. outputs/maps/m7_normalized_velocity.png
"""

from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import netCDF4 as nc
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = ROOT_DIR / "outputs" / "maps"
COMP_DIR = ROOT_DIR / "outputs" / "comparison"
MAP_NC_PATH = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE" / "Bhavanisagar_DamBreak_map.nc"
CENTERLINE_GPKG = ROOT_DIR / "data" / "comparison" / "common_nearfield_centerline.gpkg"
GAUGES_GPKG = ROOT_DIR / "data" / "comparison" / "common_gauges.gpkg"


def generate_plots():
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#2c3e50"
    plt.rcParams["axes.linewidth"] = 1.2

    # Load data
    df_depth = pd.read_csv(COMP_DIR / "depth_comparison.csv")
    df_vel = pd.read_csv(COMP_DIR / "velocity_comparison.csv")
    df_norm = pd.read_csv(COMP_DIR / "normalized_spatial_profiles.csv")
    gdf_centerline = gpd.read_file(CENTERLINE_GPKG)
    gdf_gauges = gpd.read_file(GAUGES_GPKG)

    # -------------------------------------------------------------
    # 1. Geospatial Comparison Map (m7_common_gauges.png)
    # -------------------------------------------------------------
    print("Generating Map 1: outputs/maps/m7_common_gauges.png...")
    fig, ax = plt.subplots(figsize=(11, 10), dpi=300)

    # Extract D-Flow mesh in near-field reach
    ds = nc.Dataset(MAP_NC_PATH, "r")
    fx = ds.variables["mesh2d_face_x"][:]
    fy = ds.variables["mesh2d_face_y"][:]
    xbnd = ds.variables["mesh2d_face_x_bnd"]
    ybnd = ds.variables["mesh2d_face_y_bnd"]
    fbl = ds.variables["mesh2d_flowelem_bl"][:]

    mask = (fx >= 730000) & (fx <= 731500) & (fy >= 1268600) & (fy <= 1270800)
    indices = np.where(mask)[0]

    polys = []
    bed_vals = []
    for idx in indices:
        poly_coords = np.column_stack([xbnd[idx], ybnd[idx]])
        polys.append(poly_coords)
        bed_vals.append(fbl[idx])
    ds.close()

    poly_col = PolyCollection(polys, edgecolors="#7f8c8d", facecolors="#ecf0f1", linewidths=0.7, alpha=0.65, label="D-Flow FM 2D Mesh (~100 m cells)")
    ax.add_collection(poly_col)

    # Centerline
    gdf_centerline.plot(ax=ax, color="#2980b9", linewidth=2.8, linestyle="-", label="Common Near-Field Centerline (0–1500 m)", zorder=4)

    # SPH unit-width corridor representation (buffer around centerline)
    corridor_geom = gdf_centerline.buffer(30.0)
    corridor_geom.plot(ax=ax, color="#3498db", alpha=0.25, edgecolor="#2980b9", linestyle="--", label="DualSPHysics 2D Domain Reach (1500 m)", zorder=3)

    # Breach location
    breach_x, breach_y = 730450.10, 1269149.74
    ax.scatter(breach_x, breach_y, color="#e74c3c", s=180, marker="*", edgecolor="black", linewidth=1.5, zorder=6, label="Breach Inflow Origin (Chainage 0 m)")

    # Common gauges
    for _, row in gdf_gauges.iterrows():
        gx, gy = row["easting"], row["northing"]
        st = row["station_id"]
        ch = int(row["chainage_m"])
        ax.scatter(gx, gy, color="#f39c12", s=90, marker="o", edgecolor="black", linewidth=1.2, zorder=7)
        offset_x = 25 if ch != 250 else -70
        offset_y = 20 if ch != 100 else -35
        ax.annotate(f"{st}\n({ch} m)", (gx, gy), xytext=(gx + offset_x, gy + offset_y),
                    fontsize=8.5, fontweight="bold", color="#2c3e50",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#bdc3c7", alpha=0.9),
                    arrowprops=dict(arrowstyle="->", color="#7f8c8d", lw=0.8), zorder=8)

    ax.scatter([], [], color="#f39c12", s=90, marker="o", edgecolor="black", label="Common Cross-Solver Gauges (5 Stns)")

    ax.set_xlim(730200, 731200)
    ax.set_ylim(1268800, 1270500)
    ax.set_xlabel("Easting [m] (UTM Zone 43N)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Northing [m] (UTM Zone 43N)", fontsize=11, fontweight="bold")
    ax.set_title("JalRakshak-HD: Cross-Solver Common Comparison Spatial Corridor (M7)\n"
                 "D-Flow FM 2D Mesh vs. DualSPHysics Near-Field Domain | EPSG:32643",
                 fontsize=12, fontweight="bold", pad=12)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", frameon=True, fontsize=9.5)
    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m7_common_gauges.png", dpi=300)
    plt.close()
    print("[OK] Saved m7_common_gauges.png")

    # -------------------------------------------------------------
    # 2. Depth Comparison Plot (m7_depth_comparison.png)
    # -------------------------------------------------------------
    print("Generating Plot 2: outputs/maps/m7_depth_comparison.png...")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    ch_all = df_depth["chainage_m"].values
    d_dflow = df_depth["dflow_peak_depth_m"].values
    
    # SPH is only valid for 100m, 250m, 500m, 1000m
    df_sph_reached = df_depth[df_depth["chainage_m"] < 1500.0]
    ch_sph = df_sph_reached["chainage_m"].values
    d_sph = df_sph_reached["sph_peak_depth_m"].values

    ax.plot(ch_all, d_dflow, color="#2980b9", lw=2.4, marker="s", markersize=8, label="D-Flow FM (2D Shallow-Water, Full Hydrograph)")
    ax.plot(ch_sph, d_sph, color="#e67e22", lw=2.4, marker="o", markersize=8, linestyle="--", label="DualSPHysics (2D SPH, Peak-State Release)")

    # 1500m unreached annotation for SPH
    ax.scatter(1500, 0, color="#e74c3c", marker="x", s=120, lw=2.5, zorder=5)
    ax.annotate("SPH Front Not Reached\nwithin 600 s (h = 0 m)", (1500, 0), xytext=(1260, 2.5),
                fontsize=8.5, fontweight="bold", color="#c0392b",
                bbox=dict(boxstyle="round,pad=0.3", fc="#fadbd8", ec="#e74c3c", alpha=0.9),
                arrowprops=dict(arrowstyle="->", color="#e74c3c", lw=1.2))

    # Station labels
    for ch, hd, hs in zip(ch_sph, d_dflow[:4], d_sph):
        ax.annotate(f"D-Flow: {hd:.2f} m\nSPH: {hs:.2f} m", (ch, max(hd, hs)), xytext=(ch + 15, max(hd, hs) + 0.8),
                    fontsize=8, color="#2c3e50", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#bdc3c7", alpha=0.85))

    ax.set_xlabel("Downstream Chainage from Breach (m)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Peak Water Depth (m)", fontsize=11, fontweight="bold")
    ax.set_title("JalRakshak-HD: Cross-Solver Peak Depth Comparison (Milestone M7)\n"
                 "Non-Equivalent Forcing: D-Flow FM Full Hydrograph vs. DualSPHysics Peak-State Release",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(-0.8, 17.5)
    ax.set_xlim(50, 1600)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", frameon=True, fontsize=10)
    
    # Caption note
    fig.text(0.5, 0.015, "Note: Comparison represents Cross-Solver Consistency Analysis under non-equivalent forcing histories; differences represent model spread, not solver error.",
             ha="center", fontsize=8.5, fontstyle="italic", color="#555")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(MAPS_DIR / "m7_depth_comparison.png", dpi=300)
    plt.close()
    print("[OK] Saved m7_depth_comparison.png")

    # -------------------------------------------------------------
    # 3. Velocity Comparison Plot (m7_velocity_comparison.png)
    # -------------------------------------------------------------
    print("Generating Plot 3: outputs/maps/m7_velocity_comparison.png...")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    u_dflow = df_vel["dflow_peak_velocity_mps"].values
    df_sph_v_reached = df_vel[df_vel["chainage_m"] < 1500.0]
    u_sph = df_sph_v_reached["sph_peak_velocity_mps"].values

    ax.plot(ch_all, u_dflow, color="#2980b9", lw=2.4, marker="s", markersize=8, label="D-Flow FM (Depth-Averaged, 100 m cells)")
    ax.plot(ch_sph, u_sph, color="#d35400", lw=2.4, marker="^", markersize=8, linestyle="--", label="DualSPHysics (Unconfined Particle Plunge Jet)")

    # 1500m unreached annotation for SPH
    ax.scatter(1500, 0, color="#e74c3c", marker="x", s=120, lw=2.5, zorder=5)
    ax.annotate("SPH Front Not Reached\nwithin 600 s (u = 0 m/s)", (1500, 0), xytext=(1250, 4.0),
                fontsize=8.5, fontweight="bold", color="#c0392b",
                bbox=dict(boxstyle="round,pad=0.3", fc="#fadbd8", ec="#e74c3c", alpha=0.9),
                arrowprops=dict(arrowstyle="->", color="#e74c3c", lw=1.2))

    for ch, ud, us in zip(ch_sph, u_dflow[:4], u_sph):
        ax.annotate(f"D-Flow: {ud:.2f} m/s\nSPH: {us:.2f} m/s", (ch, us), xytext=(ch + 20, us - 1.5),
                    fontsize=8, color="#2c3e50", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#bdc3c7", alpha=0.85))

    ax.set_xlabel("Downstream Chainage from Breach (m)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Peak Flow Velocity (m/s)", fontsize=11, fontweight="bold")
    ax.set_title("JalRakshak-HD: Cross-Solver Peak Velocity Comparison (Milestone M7)\n"
                 "High-Energy Dam Toe Plunge Jet (SPH) vs. 2D Shallow-Water Floodplain Routing (D-Flow FM)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(-1.0, 28.0)
    ax.set_xlim(50, 1600)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", frameon=True, fontsize=10)

    fig.text(0.5, 0.015, "CRITICAL: Non-equivalent forcing histories. SPH resolves unconfined toe plunge jetting (Fr ~ 2.2-3.2); D-Flow averages across 100 m cells (Fr ~ 0.5-0.7).",
             ha="center", fontsize=8.5, fontstyle="italic", color="#555")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(MAPS_DIR / "m7_velocity_comparison.png", dpi=300)
    plt.close()
    print("[OK] Saved m7_velocity_comparison.png")

    # -------------------------------------------------------------
    # 4. Normalized Depth Profile (m7_normalized_depth.png)
    # -------------------------------------------------------------
    print("Generating Plot 4: outputs/maps/m7_normalized_depth.png...")
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

    df_norm_sph = df_norm[df_norm["chainage_m"] < 1500.0]

    ax.plot(df_norm["chainage_m"], df_norm["dflow_h_star"], color="#2980b9", lw=2.4, marker="s", markersize=8, label="D-Flow FM: $h^* = h / h_{100m}$ ($h_{100m}=6.22$ m)")
    ax.plot(df_norm_sph["chainage_m"], df_norm_sph["sph_h_star"], color="#e67e22", lw=2.4, marker="o", markersize=8, linestyle="--", label="DualSPHysics: $h^* = h / h_{100m}$ ($h_{100m}=8.06$ m)")

    ax.axhline(1.0, color="#7f8c8d", linestyle=":", lw=1.2, alpha=0.7)
    ax.set_xlabel("Downstream Chainage from Breach (m)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Normalized Depth Ratio $h / h_{100m}$ [-]", fontsize=11, fontweight="bold")
    ax.set_title("JalRakshak-HD: Normalized Water Depth Profiles Along Near-Field Corridor (M7)\n"
                 "Relative Spatial Attenuation / Ponding Independent of Absolute Magnitude",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_xlim(50, 1550)
    ax.set_ylim(0.0, 2.7)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", frameon=True, fontsize=10)

    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m7_normalized_depth.png", dpi=300)
    plt.close()
    print("[OK] Saved m7_normalized_depth.png")

    # -------------------------------------------------------------
    # 5. Normalized Velocity Profile (m7_normalized_velocity.png)
    # -------------------------------------------------------------
    print("Generating Plot 5: outputs/maps/m7_normalized_velocity.png...")
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

    ax.plot(df_norm["chainage_m"], df_norm["dflow_u_star"], color="#2980b9", lw=2.4, marker="s", markersize=8, label="D-Flow FM: $u^* = u / u_{100m}$ ($u_{100m}=2.47$ m/s)")
    ax.plot(df_norm_sph["chainage_m"], df_norm_sph["sph_u_star"], color="#d35400", lw=2.4, marker="^", markersize=8, linestyle="--", label="DualSPHysics: $u^* = u / u_{100m}$ ($u_{100m}=23.16$ m/s)")

    ax.axhline(1.0, color="#7f8c8d", linestyle=":", lw=1.2, alpha=0.7)
    ax.set_xlabel("Downstream Chainage from Breach (m)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Normalized Velocity Ratio $u / u_{100m}$ [-]", fontsize=11, fontweight="bold")
    ax.set_title("JalRakshak-HD: Normalized Velocity Profiles Along Near-Field Corridor (M7)\n"
                 "Near-Field Kinetic Energy Attenuation vs. Downstream Channelization",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_xlim(50, 1550)
    ax.set_ylim(0.0, 2.1)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", frameon=True, fontsize=10)

    plt.tight_layout()
    plt.savefig(MAPS_DIR / "m7_normalized_velocity.png", dpi=300)
    plt.close()
    print("[OK] Saved m7_normalized_velocity.png")


if __name__ == "__main__":
    generate_plots()
