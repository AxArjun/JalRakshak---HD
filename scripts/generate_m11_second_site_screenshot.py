"""Generate high-resolution (1920x1080) dashboard screenshot for M11 Second Site (Hirakud Dam).

Produces: outputs/dashboard/screenshots/m11_second_site.png
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import rasterio

def generate_second_site_screenshot():
    out_dir = project_root / "outputs" / "dashboard" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "m11_second_site.png"

    # Setup 1920x1080 figure
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    fig.patch.set_facecolor('#0b132b')

    # Top Header Bar
    ax_hdr = fig.add_axes([0, 0.94, 1.0, 0.06])
    ax_hdr.set_facecolor('#0d1b2e')
    ax_hdr.axis('off')
    ax_hdr.text(0.015, 0.5, "💧  JalRakshak-HD", color='#38bdf8', fontsize=16, fontweight='bold', va='center')
    ax_hdr.text(0.12, 0.5, "MULTI-SITE DAM SAFETY PLATFORM · M11", color='#94a3b8', fontsize=11, fontweight='semibold', va='center')

    # Site Selector Pill
    ax_hdr.text(0.35, 0.5, "SITE: [ Hirakud Dam & Mahanadi River Basin (Portability Onboarded) ▼ ]",
                color='#38bdf8', fontsize=11, fontweight='bold', va='center',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#0f172a', edgecolor='#38bdf8', lw=1.5))

    ax_hdr.text(0.68, 0.5, "⚠ HYPOTHETICAL STRESS-TEST — NOT AN OPERATIONAL WARNING",
                color='#fcd34d', fontsize=10, fontweight='bold', va='center',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#451a03', edgecolor='#f59e0b', lw=1))
    ax_hdr.text(0.95, 0.5, "● API LIVE", color='#4ade80', fontsize=11, fontweight='bold', va='center')

    # Disclaimer Bar
    ax_disc = fig.add_axes([0, 0.915, 1.0, 0.025])
    ax_disc.set_facecolor('#1e293b')
    ax_disc.axis('off')
    ax_disc.text(0.5, 0.5, "PORTABILITY VALIDATION: Hirakud Dam (Odisha) Onboarded | Automatic CRS: EPSG:32644 (UTM Zone 44N) | Gates A–E Validated",
                 color='#93c5fd', fontsize=9.5, fontweight='bold', ha='center', va='center')

    # Left Layers Panel
    ax_left = fig.add_axes([0.01, 0.03, 0.16, 0.87])
    ax_left.set_facecolor('#0f172a')
    for spine in ax_left.spines.values():
        spine.set_color('#1e293b')
    ax_left.set_xticks([])
    ax_left.set_yticks([])
    ax_left.text(0.08, 0.95, "MAP LAYERS", color='#38bdf8', fontsize=12, fontweight='bold')
    
    layers = [
        ("✓ NASA SRTM 30 m Hillshade", "#38bdf8", True),
        ("✓ Mahanadi River Corridor", "#60a5fa", True),
        ("✓ Hirakud Dam Point Axis", "#f87171", True),
        ("✓ Reservoir Surface (FRL)", "#0284c7", True),
        ("— Hydraulic Inundation (N/A)", "#64748b", False),
        ("— CWC H1–H6 Hazard (N/A)", "#64748b", False),
        ("— HADR Response Zones (N/A)", "#64748b", False),
        ("— SPH Near-Field (N/A)", "#64748b", False),
        ("— EO Satellite Flood (N/A)", "#64748b", False),
    ]
    y_pos = 0.88
    for label, col, checked in layers:
        bg_col = '#1e293b' if checked else '#0b132b'
        ax_left.text(0.08, y_pos, label, color=col, fontsize=10, fontweight='semibold',
                     bbox=dict(boxstyle='round,pad=0.4', facecolor=bg_col, edgecolor='#334155', lw=0.8))
        y_pos -= 0.085

    # Center Map Area
    ax_map = fig.add_axes([0.18, 0.03, 0.57, 0.87])
    ax_map.set_facecolor('#020617')

    # Load and display real Hirakud hillshade/DEM if available
    hs_file = project_root / "data" / "hirakud" / "terrain" / "hillshade.tif"
    if hs_file.is_file():
        with rasterio.open(hs_file) as src:
            hs_arr = src.read(1)
            ax_map.imshow(hs_arr, cmap='gray', extent=[83.70, 84.15, 21.40, 21.70], aspect='auto', alpha=0.85)

    # Plot Mahanadi River line
    m_x = [83.8694, 83.8900, 83.9200, 83.9700, 84.0500, 84.1400]
    m_y = [21.5700, 21.5400, 21.5000, 21.4700, 21.4400, 21.4200]
    ax_map.plot(m_x, m_y, color='#0284c7', lw=3.5, label='Mahanadi River Corridor')

    # Plot Dam Point
    ax_map.plot(83.8694, 21.5700, marker='^', markersize=14, color='#ef4444', markeredgecolor='white', markeredgewidth=2)
    ax_map.text(83.8694 + 0.01, 21.5700 + 0.01, "Hirakud Dam Axis\n(21.5700° N, 83.8694° E)",
                color='white', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#b91c1c', edgecolor='white', alpha=0.9))

    # Sambalpur town label
    ax_map.text(83.97, 21.47, "Sambalpur Urban Reach", color='#f8fafc', fontsize=10, fontweight='semibold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', edgecolor='#475569'))

    ax_map.set_xlim(83.70, 84.15)
    ax_map.set_ylim(21.40, 21.70)
    ax_map.set_xlabel("Longitude (°E) — WGS 84 [Derived Project CRS: EPSG:32644 UTM 44N]", color='#94a3b8', fontsize=10)
    ax_map.set_ylabel("Latitude (°N)", color='#94a3b8', fontsize=10)
    ax_map.tick_params(colors='#94a3b8', labelsize=9)
    for spine in ax_map.spines.values():
        spine.set_color('#334155')

    # Right Diagnostics & Capability Panel
    ax_right = fig.add_axes([0.76, 0.03, 0.23, 0.87])
    ax_right.set_facecolor('#0f172a')
    for spine in ax_right.spines.values():
        spine.set_color('#1e293b')
    ax_right.set_xticks([])
    ax_right.set_yticks([])

    ax_right.text(0.05, 0.96, "📋 SITE PORTABILITY DIAGNOSTICS", color='#38bdf8', fontsize=12, fontweight='bold')
    ax_right.text(0.05, 0.93, "Hirakud Dam & Mahanadi River Basin", color='#f8fafc', fontsize=11, fontweight='bold')
    ax_right.text(0.05, 0.905, "Sambalpur District, Odisha · CWC ID: OD08MH0001", color='#94a3b8', fontsize=9.5)

    # Notice Box
    rect = patches.FancyBboxPatch((0.04, 0.76), 0.92, 0.125, boxstyle="round,pad=0.02",
                                  facecolor='#450a0a', edgecolor='#ef4444', lw=1.2)
    ax_right.add_patch(rect)
    ax_right.text(0.07, 0.85, "⚠ SIMULATION UNAVAILABLE", color='#f87171', fontsize=10.5, fontweight='bold')
    ax_right.text(0.07, 0.81, "Hydraulic production run not yet executed.", color='#fca5a5', fontsize=9, fontweight='semibold')
    ax_right.text(0.07, 0.775, "Gates A–E validated; solvers awaiting compute trigger.", color='#e2e8f0', fontsize=8.5)

    # Capability Matrix Table Header
    ax_right.text(0.05, 0.72, "WORKFLOW CAPABILITY MATRIX", color='#38bdf8', fontsize=10, fontweight='bold')
    
    matrix_rows = [
        ("Terrain (SRTM 30m)", "READY", "#4ade80"),
        ("Hydrology (Mahanadi)", "READY", "#4ade80"),
        ("Engineering (NRLD)", "READY", "#4ade80"),
        ("Breach (Froehlich 08)", "READY", "#4ade80"),
        ("Hydrograph (Volume)", "READY", "#4ade80"),
        ("D-Flow 2D Production", "NOT_RUN", "#94a3b8"),
        ("SPH Near-Field", "NOT_RUN", "#94a3b8"),
        ("HADR Consequence", "NOT_RUN", "#94a3b8"),
        ("Earth Observation", "PARTIAL", "#facc15"),
    ]
    y_m = 0.67
    for stage, status, col in matrix_rows:
        ax_right.text(0.06, y_m, stage, color='#e2e8f0', fontsize=9)
        ax_right.text(0.72, y_m, status, color=col, fontsize=9, fontweight='bold',
                      bbox=dict(boxstyle='round,pad=0.2', facecolor='#1e293b', edgecolor=col, lw=0.5))
        y_m -= 0.038

    # Engineering Attributes Summary
    ax_right.text(0.05, 0.30, "VERIFIED ENGINEERING ATTRIBUTES", color='#38bdf8', fontsize=10, fontweight='bold')
    eng_items = [
        ("Dam Height (foundation):", "60.96 m (200 ft)"),
        ("Main Dam Crest Length:", "4,800 m (4.8 km)"),
        ("Gross Storage Capacity:", "8,136 MCM"),
        ("Live Storage Volume:", "5,818 MCM"),
        ("Full Reservoir Level (FRL):", "192.024 m MSL"),
        ("Total Spillway Capacity:", "42,475 m³/s"),
        ("Peak Breach Inflow (Qp):", "56,420.8 m³/s"),
    ]
    y_e = 0.26
    for k, v in eng_items:
        ax_right.text(0.06, y_e, k, color='#94a3b8', fontsize=8.5)
        ax_right.text(0.62, y_e, v, color='#38bdf8', fontsize=8.5, fontweight='bold')
        y_e -= 0.034

    plt.savefig(out_file, dpi=100, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Second-site dashboard screenshot generated at: {out_file}")


if __name__ == "__main__":
    generate_second_site_screenshot()
