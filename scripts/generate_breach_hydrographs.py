"""
Generate Breach Outflow Hydrographs for Hydrodynamic Modeling.
SIH PS 26161 - JalRakshak-HD Milestone M4.

Executes volume-constrained screening hydrograph synthesis across baseline and sensitivity scenarios,
exports time-series CSVs, D-Flow FM boundary files (.tim), validation manifests, and diagnostic plots.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.peak_discharge_models import PeakDischargeModelLibrary
from backend.app.services.hydrograph_generator import HydrographGenerator


def generate_breach_hydrographs():
    config_path = PROJECT_ROOT / "configs" / "hydrograph.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        hyd_cfg = yaml.safe_load(f)

    res_cfg = hyd_cfg["reservoir"]
    vw = float(res_cfg["assumed_breach_volume_m3"])  # 780,500,000 m3 (780.5 MCM)
    hw = float(res_cfg["water_depth_above_invert_hw_m"])  # 32.0 m
    hb = float(res_cfg["dam_breach_height_hb_m"])  # 40.0 m
    dt = float(hyd_cfg["hydrograph"]["timestep_seconds"])  # 60.0 s
    vol_tol = float(hyd_cfg["hydrograph"]["volume_tolerance_percent"])  # 0.5%

    print("=" * 95)
    print(" JALRAKSHAK-HD: BREACH OUTFLOW HYDROGRAPH GENERATION ENGINE (MILESTONE M4)")
    print("=" * 95)
    print(f"Target Volume V_w:         {vw/1e6:.2f} MCM ({vw:,.0f} m3) [MODEL_ASSUMPTION_FIRST_ESTIMATE]")
    print(f"Water Depth h_w:          {hw:.2f} m [MODEL_ASSUMPTION_FIRST_ESTIMATE]")
    print(f"Breach Height h_b:        {hb:.2f} m [MODEL_ASSUMPTION_FIRST_ESTIMATE]")
    print(f"Time-step dt:             {dt:.1f} s")
    print("-" * 95)

    # 1. Compute Peak Flow Regressions
    peak_fr95 = PeakDischargeModelLibrary.calculate_froehlich_1995_peak(water_volume_vw_m3=vw, water_depth_hw_m=hw)
    tf_fr95_s = PeakDischargeModelLibrary.calculate_froehlich_1995_formation_time(water_volume_vw_m3=vw, breach_height_hb_m=hb)
    peak_mlm = PeakDischargeModelLibrary.calculate_macdonald_langridge_monopolis_peak_wahl(water_volume_vw_m3=vw, water_depth_hw_m=hw)

    tf_fr08_s = 14095.59  # M3 Froehlich 2008 locked result
    tf_mlm_s = 13907.39   # M3 MacDonald 1984 locked result

    # 2. Define Scenarios
    scenario_defs = [
        {
            "id": "BHV_BASE",
            "name": "Bhavanisagar Base Case Hybrid (Froehlich 1995 Qp + Froehlich 2008 tf)",
            "peak_qp": peak_fr95.peak_discharge_m3s,
            "rise_time_s": tf_fr08_s,
            "geom_model": "FROEHLICH_2008",
            "peak_model": "FROEHLICH_1995",
            "rise_source": "Froehlich (2008) M3 Result (t_f = 14,095.59 s / 3.915 hr)",
            "limitations": "Empirical volume-constrained screening hydrograph mathematically constrained to 780.5 MCM; not dynamic stage-storage routed",
        },
        {
            "id": "BHV_FROEHLICH95_DIAGNOSTIC",
            "name": "Bhavanisagar Same-Family Diagnostic (Froehlich 1995 Qp + Froehlich 1995 tf)",
            "peak_qp": peak_fr95.peak_discharge_m3s,
            "rise_time_s": tf_fr95_s,
            "geom_model": "FROEHLICH_1995",
            "peak_model": "FROEHLICH_1995",
            "rise_source": f"Froehlich (1995) Formation Time Equation (t_f = {tf_fr95_s:.2f} s / {tf_fr95_s/3600:.3f} hr)",
            "limitations": "Single-family comparison showing sensitivity to formation time formula",
        },
        {
            "id": "BHV_PEAK_SENSITIVITY_MLM",
            "name": "Bhavanisagar Peak Sensitivity (MacDonald 1984 / Wahl 1998 Qp + M3 MLM tf)",
            "peak_qp": peak_mlm.peak_discharge_m3s,
            "rise_time_s": tf_mlm_s,
            "geom_model": "MACDONALD_LANGRIDGE_MONOPOLIS_1984",
            "peak_model": "MACDONALD_LANGRIDGE_MONOPOLIS_1984_WAHL",
            "rise_source": f"MacDonald & Langridge-Monopolis (1984) M3 Result (t_f = {tf_mlm_s:.2f} s / {tf_mlm_s/3600:.3f} hr)",
            "limitations": "Upper-envelope peak outflow sensitivity based on breach formation factor",
        },
    ]

    out_hydro_dir = PROJECT_ROOT / "data" / "dflowfm" / "hydrographs"
    out_hydro_dir.mkdir(parents=True, exist_ok=True)

    generated_scenarios = []
    dataframes = {}

    for s_def in scenario_defs:
        sc_obj, df = HydrographGenerator.generate_triangular_hydrograph(
            scenario_id=s_def["id"],
            scenario_name=s_def["name"],
            peak_discharge_m3s=s_def["peak_qp"],
            rise_time_s=s_def["rise_time_s"],
            target_volume_m3=vw,
            breach_geometry_model=s_def["geom_model"],
            peak_discharge_model=s_def["peak_model"],
            volume_source="CWC Hydrological Data Book 2020 Live Storage (780.5 MCM)",
            rise_time_source=s_def["rise_source"],
            limitations=s_def["limitations"],
            timestep_seconds=dt,
            volume_tolerance_percent=vol_tol,
        )

        # Export CSV
        csv_path = out_hydro_dir / f"{s_def['id']}.csv"
        df.to_csv(csv_path, index=False)

        # Export D-Flow FM boundary .tim file
        tim_path = out_hydro_dir / f"{s_def['id']}_boundary.tim"
        HydrographGenerator.export_boundary_tim_file(df, tim_path)

        generated_scenarios.append(sc_obj)
        dataframes[s_def["id"]] = df

    # 3. Print Formatted Table
    print(f"{'Scenario':<28} | {'Qpeak m3/s':<11} | {'Rise hr':<8} | {'Rec hr':<8} | {'Total hr':<9} | {'Targ MCM':<8} | {'Integ MCM':<9} | {'Err %':<6} | {'Status'}")
    print("-" * 115)
    for sc in generated_scenarios:
        m = sc.metadata
        v = sc.validation
        print(f"{m.scenario_id:<28} | {m.peak_discharge_m3s:<11.2f} | {m.rise_time_hr:<8.3f} | {m.recession_time_hr:<8.3f} | {m.total_duration_hr:<9.3f} | {m.target_volume_m3/1e6:<8.2f} | {m.integrated_volume_m3/1e6:<9.2f} | {m.volume_error_percent:<6.4f} | {v.overall_status}")
    print("=" * 115)

    # 4. Save Validation Manifests
    peak_val_data = {
        "timestamp_utc": "2026-09-25T14:15:00Z",
        "study_site": "Bhavanisagar Dam",
        "models_evaluated": [peak_fr95.model_dump(), peak_mlm.model_dump()],
        "notes": "Both regressions evaluated using exact SI units with V_w = 780.5 MCM and h_w = 32.0 m."
    }
    peak_val_path = PROJECT_ROOT / "outputs" / "validation" / "peak_discharge_validation.json"
    peak_val_path.parent.mkdir(parents=True, exist_ok=True)
    with open(peak_val_path, "w", encoding="utf-8") as f:
        json.dump(peak_val_data, f, indent=2)

    comp_data = {
        "timestamp_utc": "2026-09-25T14:15:00Z",
        "description": "Multi-scenario screening hydrograph comparison across peak and rise time models",
        "scenarios": [sc.model_dump() for sc in generated_scenarios],
        "comparison_metrics": {
            "peak_discharge_range_m3s": [min(s.metadata.peak_discharge_m3s for s in generated_scenarios), max(s.metadata.peak_discharge_m3s for s in generated_scenarios)],
            "total_duration_range_hr": [min(s.metadata.total_duration_hr for s in generated_scenarios), max(s.metadata.total_duration_hr for s in generated_scenarios)],
            "volume_spread_percent": 0.0,  # All volume-constrained to 780.5 MCM
            "derivation_classification": "MODEL_SPREAD_SCENARIOS"
        }
    }
    comp_path = PROJECT_ROOT / "outputs" / "validation" / "hydrograph_comparison.json"
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(comp_data, f, indent=2)

    # 5. Generate Diagnostic Plots (Task 16)
    maps_dir = PROJECT_ROOT / "outputs" / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)

    # Hydrograph plot
    plt.figure(figsize=(10, 6), dpi=300)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    colors = {"BHV_BASE": "#1f77b4", "BHV_FROEHLICH95_DIAGNOSTIC": "#2ca02c", "BHV_PEAK_SENSITIVITY_MLM": "#d62728"}
    for sc in generated_scenarios:
        s_id = sc.metadata.scenario_id
        df = dataframes[s_id]
        lbl = f"{s_id}: Qp={sc.metadata.peak_discharge_m3s:,.0f} m³/s, tr={sc.metadata.rise_time_hr:.2f}h, T={sc.metadata.total_duration_hr:.2f}h"
        plt.plot(df["time_hr"], df["discharge_m3s"], label=lbl, color=colors.get(s_id, "black"), linewidth=2.0)

    plt.title("Bhavanisagar Dam Breach Outflow Screening Hydrographs (M4)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Time from Breach Initiation (hours)", fontsize=12)
    plt.ylabel("Breach Outflow Discharge (m³/s)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper right", frameon=True, fontsize=10)
    plt.tight_layout()

    hydro_plot_path = maps_dir / "m4_breach_hydrograph.png"
    plt.savefig(hydro_plot_path)
    plt.close()
    print(f"Saved breach hydrograph plot to: {hydro_plot_path.relative_to(PROJECT_ROOT)}")

    # Cumulative Volume plot
    plt.figure(figsize=(10, 6), dpi=300)
    for sc in generated_scenarios:
        s_id = sc.metadata.scenario_id
        df = dataframes[s_id]
        lbl = f"{s_id}: Integrated Vol = {sc.metadata.integrated_volume_m3/1e6:.2f} MCM (Err: {sc.metadata.volume_error_percent:.4f}%)"
        plt.plot(df["time_hr"], df["cumulative_volume_m3"] / 1e6, label=lbl, color=colors.get(s_id, "black"), linewidth=2.0)

    plt.axhline(y=vw / 1e6, color="grey", linestyle=":", label=f"Target Volume: {vw/1e6:.1f} MCM (780.5 MCM Live Storage)")
    plt.title("Cumulative Breached Water Volume Over Time (M4)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Time from Breach Initiation (hours)", fontsize=12)
    plt.ylabel("Cumulative Volume (Million Cubic Metres / MCM)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right", frameon=True, fontsize=10)
    plt.tight_layout()

    vol_plot_path = maps_dir / "m4_cumulative_volume.png"
    plt.savefig(vol_plot_path)
    plt.close()
    print(f"Saved cumulative volume plot to: {vol_plot_path.relative_to(PROJECT_ROOT)}")
    print("=" * 95)


if __name__ == "__main__":
    generate_breach_hydrographs()
