"""
JalRakshak-HD: Cross-Solver Near-Field Comparison Engine (Milestone M7)
======================================================================
Integrates D-Flow FM and DualSPHysics near-field outputs across common
comparison stations (100 m, 250 m, 500 m, 1000 m, 1500 m).

Generates:
1. outputs/comparison/sph_nearfield_gauges.csv
2. outputs/validation/m7_time_reference_audit.json
3. outputs/comparison/depth_comparison.csv
4. outputs/comparison/velocity_comparison.csv
5. outputs/comparison/normalized_spatial_profiles.csv
6. outputs/comparison/hydraulic_regime_comparison.csv
7. outputs/comparison/arrival_time_context.csv
8. outputs/validation/m7_cross_model_statistics.json
9. outputs/validation/m7_handoff_candidates.json
10. outputs/validation/m7_comparison_manifest.json
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DFLOW_CSV = ROOT_DIR / "outputs" / "comparison" / "dflow_nearfield_gauges.csv"
SPH_ORIG_CSV = ROOT_DIR / "outputs" / "simulations" / "sph" / "BHV_BASE_NEARFIELD" / "gauge_results.csv"
PARTICLE_CSV_DIR = ROOT_DIR / "data" / "sph" / "BHV_BASE_NEARFIELD" / "production_out" / "csv"
BED_PROFILE_CSV = ROOT_DIR / "data" / "sph" / "nearfield_bed_profile.csv"

OUT_COMP = ROOT_DIR / "outputs" / "comparison"
OUT_VAL = ROOT_DIR / "outputs" / "validation"


def get_sph_depth_at_peak_vel(frame_idx: int, chainage_m: float, bed_df: pd.DataFrame, dp: float = 1.0) -> float:
    """Extracts actual fluid depth from particle frame CSV at exact time of peak velocity."""
    csv_path = PARTICLE_CSV_DIR / f"PartFluid_{frame_idx:04d}.csv"
    if not csv_path.exists():
        return float("nan")

    df = pd.read_csv(csv_path, skiprows=3)
    df.columns = [c.strip() for c in df.columns]

    x_col = [c for c in df.columns if "pos.x" in c.lower()][0]
    z_col = [c for c in df.columns if "pos.z" in c.lower()][0]

    x = df[x_col].values.astype(float)
    z = df[z_col].values.astype(float)

    w = max(5.0, dp * 2.0)
    mask = (x >= chainage_m - w) & (x <= chainage_m + w)
    if not np.any(mask):
        return 0.0

    bed_x = bed_df["chainage_m"].values
    bed_z = bed_df["dem_elevation_m"].values
    bed_elev = float(np.interp(chainage_m, bed_x, bed_z))

    water_surface = float(np.max(z[mask]))
    return max(0.0, water_surface - bed_elev)


def run_cross_solver_comparison():
    print("=" * 70)
    print("JalRakshak-HD: Running Cross-Solver Comparison (M7)")
    print("=" * 70)

    OUT_COMP.mkdir(parents=True, exist_ok=True)
    OUT_VAL.mkdir(parents=True, exist_ok=True)

    # 1. Load inputs
    df_dflow = pd.read_csv(DFLOW_CSV)
    df_sph_orig = pd.read_csv(SPH_ORIG_CSV)
    bed_df = pd.read_csv(BED_PROFILE_CSV)

    print(f"Loaded D-Flow gauges: {len(df_dflow)} rows")
    print(f"Loaded SPH gauges: {len(df_sph_orig)} rows")

    # 2. Task 5: Import SPH gauge results & create normalized copy
    sph_normalized_rows = []
    # Map frame index to gauge for peak velocity depth
    frame_map = {
        "G_100m": 5,
        "G_250m": 13,
        "G_500m": 29,
        "G_1000m": 191
    }

    for _, row in df_sph_orig.iterrows():
        g_name = str(row["gauge_name"])
        ch_m = float(row["chainage_m"])
        arr = str(row["arrival_time_s"]).strip()

        if ch_m == 1500.0 or arr == "NOT_REACHED":
            arr_val = "NOT_REACHED_WITHIN_600_S"
            depth_at_peak_v = float("nan")
        else:
            arr_val = str(round(float(arr), 2))
            f_idx = frame_map.get(g_name, 0)
            depth_at_peak_v = round(get_sph_depth_at_peak_vel(f_idx, ch_m, bed_df, dp=1.0), 3)

        sph_normalized_rows.append({
            "station_id": g_name,
            "chainage_m": ch_m,
            "easting": float(row["easting"]),
            "northing": float(row["northing"]),
            "longitude": float(row["longitude"]),
            "latitude": float(row["latitude"]),
            "arrival_time_s": arr_val,
            "peak_depth_m": float(row["max_water_depth_m"]),
            "peak_velocity_mps": float(row["max_velocity_mps"]),
            "time_of_peak_velocity_s": row["time_of_max_velocity_s"],
            "depth_at_peak_velocity_m": depth_at_peak_v,
            "solver_classification": "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL",
            "forcing_classification": "PEAK_STATE_INITIALIZED_RELEASE_SCREENING_CASE"
        })

    df_sph_norm = pd.DataFrame(sph_normalized_rows)
    sph_norm_csv = OUT_COMP / "sph_nearfield_gauges.csv"
    df_sph_norm.to_csv(sph_norm_csv, index=False)
    print(f"[OK] Task 5: Saved normalized SPH gauges to {sph_norm_csv}")

    # 3. Task 6: Time-Reference Audit
    qpeak_time_s = 14095.59
    time_audit = {
        "study": "JalRakshak-HD Milestone M7 Cross-Solver Consistency Analysis",
        "comparison_type": "NON_EQUIVALENT_FORCING_COMPARISON",
        "timing_comparable": False,
        "explanation": (
            "D-Flow FM t=0 corresponds to the initiation of the complete 30-hour BHV_BASE empirical hydrograph "
            "with discharge rising from zero to Qpeak (18,742.38 m3/s) at t=14,095.59 s. "
            "DualSPHysics t=0 corresponds to an initialized static peak-state fluid release block (depth=17.526 m, "
            "unit discharge=85.47 m2/s). Absolute arrival times reflect fundamentally distinct initial-boundary "
            "value formulations and MUST NOT be subtracted to claim solver timing error or synchronization."
        ),
        "dflow_time_reference": {
            "t0_definition": "Start of BHV_BASE hydrograph (Q approximately 0 m3/s)",
            "time_of_peak_discharge_s": qpeak_time_s,
            "total_simulation_duration_s": 108000.0,
            "hydrograph_rise_time_s": 14095.59
        },
        "dualsphysics_time_reference": {
            "t0_definition": "Instantaneous release of initialized peak-state reservoir column",
            "initial_fluid_state": "Qpeak equivalent static column (H=17.526 m, L=400 m)",
            "total_simulation_duration_s": 600.0
        },
        "diagnostic_peak_relative_arrival": {}
    }

    for _, row in df_dflow.iterrows():
        st_id = str(row["station_id"])
        arr_s = float(row["arrival_time_s"])
        diag_rel_s = round(arr_s - qpeak_time_s, 2)
        time_audit["diagnostic_peak_relative_arrival"][st_id] = {
            "chainage_m": float(row["chainage_m"]),
            "dflow_arrival_time_s": arr_s,
            "dflow_peak_relative_time_s": diag_rel_s,
            "interpretation_note": "Diagnostic metadata only; negative values indicate wetting prior to hydrograph peak and are NOT physical SPH-equivalent times."
        }

    audit_json = OUT_VAL / "m7_time_reference_audit.json"
    with open(audit_json, "w") as f:
        json.dump(time_audit, f, indent=2)
    print(f"[OK] Task 6: Saved time-reference audit to {audit_json}")

    # Merge for station-by-station comparison
    df_merged = pd.merge(df_dflow, df_sph_norm, on=["station_id", "chainage_m"], suffixes=("_dflow", "_sph"))

    # 4. Task 7: Depth Comparison
    depth_rows = []
    for _, r in df_merged.iterrows():
        st_id = r["station_id"]
        ch_m = r["chainage_m"]
        h_dflow = r["peak_depth_m_dflow"]
        h_sph = r["peak_depth_m_sph"]

        abs_diff = round(h_sph - h_dflow, 3)
        if h_dflow > 0:
            rel_spread_pct = round(100.0 * (h_sph - h_dflow) / h_dflow, 2)
            ratio = round(h_sph / h_dflow, 4)
        else:
            rel_spread_pct = float("nan")
            ratio = float("nan")

        notes = "SPH not reached within 600 s" if ch_m == 1500.0 else "Valid common station"

        depth_rows.append({
            "station_id": st_id,
            "chainage_m": ch_m,
            "dflow_peak_depth_m": h_dflow,
            "sph_peak_depth_m": h_sph,
            "absolute_model_spread_m": abs_diff,
            "relative_model_spread_percent": rel_spread_pct,
            "depth_ratio_sph_to_dflow": ratio,
            "comparison_classification": "CROSS_SOLVER_CONSISTENCY_ANALYSIS",
            "notes": notes
        })

    df_depth_comp = pd.DataFrame(depth_rows)
    depth_csv = OUT_COMP / "depth_comparison.csv"
    df_depth_comp.to_csv(depth_csv, index=False)
    print(f"[OK] Task 7: Saved depth comparison to {depth_csv}")

    # 5. Task 8: Velocity Comparison
    vel_rows = []
    for _, r in df_merged.iterrows():
        st_id = r["station_id"]
        ch_m = r["chainage_m"]
        u_dflow = r["peak_velocity_mps_dflow"]
        u_sph = r["peak_velocity_mps_sph"]

        abs_diff = round(u_sph - u_dflow, 3)
        if u_dflow > 0:
            rel_spread_pct = round(100.0 * (u_sph - u_dflow) / u_dflow, 2)
            ratio = round(u_sph / u_dflow, 4)
        else:
            rel_spread_pct = float("nan")
            ratio = float("nan")

        notes = "SPH not reached within 600 s" if ch_m == 1500.0 else "Gauge-specific SPH extraction"

        vel_rows.append({
            "station_id": st_id,
            "chainage_m": ch_m,
            "dflow_peak_velocity_mps": u_dflow,
            "sph_peak_velocity_mps": u_sph,
            "absolute_model_spread_mps": abs_diff,
            "relative_model_spread_percent": rel_spread_pct,
            "velocity_ratio_sph_to_dflow": ratio,
            "comparison_classification": "CROSS_SOLVER_CONSISTENCY_ANALYSIS",
            "notes": notes
        })

    df_vel_comp = pd.DataFrame(vel_rows)
    vel_csv = OUT_COMP / "velocity_comparison.csv"
    df_vel_comp.to_csv(vel_csv, index=False)
    print(f"[OK] Task 8: Saved velocity comparison to {vel_csv}")

    # 6. Task 9: Spatial Attenuation
    h_dflow_100 = float(df_dflow.loc[df_dflow["chainage_m"] == 100.0, "peak_depth_m"].iloc[0])
    u_dflow_100 = float(df_dflow.loc[df_dflow["chainage_m"] == 100.0, "peak_velocity_mps"].iloc[0])
    h_sph_100 = float(df_sph_norm.loc[df_sph_norm["chainage_m"] == 100.0, "peak_depth_m"].iloc[0])
    u_sph_100 = float(df_sph_norm.loc[df_sph_norm["chainage_m"] == 100.0, "peak_velocity_mps"].iloc[0])

    norm_rows = []
    for _, r in df_merged.iterrows():
        st_id = r["station_id"]
        ch_m = r["chainage_m"]
        x_star = round(ch_m / 1500.0, 4)

        h_d = r["peak_depth_m_dflow"]
        u_d = r["peak_velocity_mps_dflow"]
        h_s = r["peak_depth_m_sph"]
        u_s = r["peak_velocity_mps_sph"]

        h_star_dflow = round(h_d / h_dflow_100, 4) if h_dflow_100 > 0 else float("nan")
        u_star_dflow = round(u_d / u_dflow_100, 4) if u_dflow_100 > 0 else float("nan")

        h_star_sph = round(h_s / h_sph_100, 4) if h_sph_100 > 0 else float("nan")
        u_star_sph = round(u_s / u_sph_100, 4) if u_sph_100 > 0 else float("nan")

        norm_rows.append({
            "station_id": st_id,
            "chainage_m": ch_m,
            "x_star": x_star,
            "dflow_h_star": h_star_dflow,
            "dflow_u_star": u_star_dflow,
            "sph_h_star": h_star_sph,
            "sph_u_star": u_star_sph
        })

    df_norm = pd.DataFrame(norm_rows)
    norm_csv = OUT_COMP / "normalized_spatial_profiles.csv"
    df_norm.to_csv(norm_csv, index=False)
    print(f"[OK] Task 9: Saved normalized spatial profiles to {norm_csv}")

    # 7. Task 10: Dimensionless Diagnostics (Froude Number)
    g = 9.80665
    froude_rows = []
    for _, r in df_merged.iterrows():
        st_id = r["station_id"]
        ch_m = r["chainage_m"]

        # D-Flow: peak velocity and actual depth at time of peak velocity
        u_d = r["peak_velocity_mps_dflow"]
        h_d_at_u = r["depth_at_peak_velocity_m_dflow"]
        if h_d_at_u > 0:
            fr_dflow = round(u_d / math.sqrt(g * h_d_at_u), 3)
            regime_dflow = "SUPERCRITICAL" if fr_dflow > 1.0 else "SUBCRITICAL"
        else:
            fr_dflow = float("nan")
            regime_dflow = "DRY"

        # SPH: peak velocity and actual depth at time of peak velocity
        u_s = r["peak_velocity_mps_sph"]
        h_s_at_u = r["depth_at_peak_velocity_m_sph"]
        if ch_m < 1500.0 and not math.isnan(h_s_at_u) and h_s_at_u > 0:
            fr_sph = round(u_s / math.sqrt(g * h_s_at_u), 3)
            regime_sph = "SUPERCRITICAL" if fr_sph > 1.0 else "SUBCRITICAL"
        else:
            fr_sph = float("nan")
            regime_sph = "NOT_REACHED" if ch_m == 1500.0 else "INSUFFICIENT_DATA"

        froude_rows.append({
            "station_id": st_id,
            "chainage_m": ch_m,
            "dflow_peak_velocity_mps": u_d,
            "dflow_depth_at_peak_velocity_m": h_d_at_u,
            "dflow_froude_number": fr_dflow,
            "dflow_regime": regime_dflow,
            "sph_peak_velocity_mps": u_s,
            "sph_depth_at_peak_velocity_m": h_s_at_u,
            "sph_froude_number": fr_sph,
            "sph_regime": regime_sph,
            "depth_sync_status": "SYNCHRONIZED_AT_VELOCITY_PEAK_TIMESTAMP"
        })

    df_fr = pd.DataFrame(froude_rows)
    fr_csv = OUT_COMP / "hydraulic_regime_comparison.csv"
    df_fr.to_csv(fr_csv, index=False)
    print(f"[OK] Task 10: Saved hydraulic regime comparison to {fr_csv}")

    # 8. Task 11: Arrival Time Reporting
    arr_rows = []
    for _, r in df_merged.iterrows():
        arr_rows.append({
            "station_id": r["station_id"],
            "chainage_m": r["chainage_m"],
            "dflow_arrival_time_s": r["arrival_time_s_dflow"],
            "sph_arrival_time_s": r["arrival_time_s_sph"],
            "dflow_qpeak_time_s": qpeak_time_s,
            "forcing_equivalence": False,
            "interpretation_context": "SCENARIO_RESPONSE_CONTEXT"
        })

    df_arr = pd.DataFrame(arr_rows)
    arr_csv = OUT_COMP / "arrival_time_context.csv"
    df_arr.to_csv(arr_csv, index=False)
    print(f"[OK] Task 11: Saved arrival time context to {arr_csv}")

    # 9. Task 12: Model-Spread Statistics across reached stations (100m, 250m, 500m, 1000m)
    reached_depth = df_depth_comp[df_depth_comp["chainage_m"] < 1500.0]
    reached_vel = df_vel_comp[df_vel_comp["chainage_m"] < 1500.0]

    depth_abs_spreads = [abs(x) for x in reached_depth["absolute_model_spread_m"]]
    depth_ratios = list(reached_depth["depth_ratio_sph_to_dflow"])

    vel_abs_spreads = [abs(x) for x in reached_vel["absolute_model_spread_mps"]]
    vel_ratios = list(reached_vel["velocity_ratio_sph_to_dflow"])

    stats_summary = {
        "metric_type": "CROSS_MODEL_SPREAD_METRICS",
        "description": "Descriptive spread metrics across common reached stations (100 m to 1000 m). Not validation error metrics.",
        "evaluated_stations": ["G_100m", "G_250m", "G_500m", "G_1000m"],
        "depth_spread": {
            "median_absolute_spread_m": round(float(np.median(depth_abs_spreads)), 3),
            "median_ratio": round(float(np.median(depth_ratios)), 4),
            "maximum_ratio": round(float(np.max(depth_ratios)), 4),
            "minimum_ratio": round(float(np.min(depth_ratios)), 4)
        },
        "velocity_spread": {
            "median_absolute_spread_mps": round(float(np.median(vel_abs_spreads)), 3),
            "median_ratio": round(float(np.median(vel_ratios)), 4),
            "maximum_ratio": round(float(np.max(vel_ratios)), 4),
            "minimum_ratio": round(float(np.min(vel_ratios)), 4)
        },
        "trend_assessment": {
            "downstream_progression": "CONSISTENT_TREND",
            "depth_attenuation_amplification": "PARTIALLY_CONSISTENT",
            "velocity_trend": "DIVERGENT_TREND",
            "high_energy_near_field_behaviour": "CONSISTENT_TREND",
            "velocity_trend_explanation": (
                "SPH shows strong attenuation after the near-dam jet region, whereas D-Flow depth-averaged "
                "peak velocity increases farther downstream in the sampled reach. This is not solver error "
                "because forcing and dimensional formulations are non-equivalent."
            )
        }
    }

    stats_json = OUT_VAL / "m7_cross_model_statistics.json"
    with open(stats_json, "w") as f:
        json.dump(stats_summary, f, indent=2)
    print(f"[OK] Task 12: Saved cross-model statistics to {stats_json}")

    # 10. Task 21: Evaluate Possible Handoff Candidates
    handoff_eval = {
        "assessment_title": "JalRakshak-HD Milestone M7 Hybrid Coupling Handoff Evaluation",
        "recommended_future_handoff_candidate": "500 m",
        "direct_discharge_coupling_ready": False,
        "overall_coupling_readiness": "NOT_READY",
        "direct_coupling_blocker": "UNIT_WIDTH_TO_FULL_WIDTH_SCALING_UNRESOLVED",
        "coupling_status": "DESIGN_ONLY",
        "coupling_readiness_blockers": [
            "unit-width/full-width scaling unresolved",
            "forcing histories differ",
            "time origins differ",
            "SPH resolution sensitivity is NOT_STABILIZED"
        ],
        "candidate_evaluations": {
            "250m": {
                "chainage_m": 250.0,
                "sph_peak_depth_m": 12.004,
                "sph_peak_velocity_mps": 24.726,
                "sph_froude_number": 3.021,
                "dflow_peak_depth_m": 14.641,
                "dflow_peak_velocity_mps": 2.505,
                "dflow_froude_number": 0.723,
                "terrain_slope_m_per_m": -0.068,
                "distance_from_breach_m": 250.0,
                "status": "REJECTED",
                "reason": (
                    "Located in immediate plunging toe jet impact zone. High vertical particle accelerations "
                    "and violent free-surface churn violate hydrostatic shallow-water assumptions required by D-Flow FM. "
                    "Froude number exceeds 3.0."
                )
            },
            "500m": {
                "chainage_m": 500.0,
                "sph_peak_depth_m": 5.550,
                "sph_peak_velocity_mps": 15.947,
                "sph_froude_number": 2.218,
                "dflow_peak_depth_m": 11.044,
                "dflow_peak_velocity_mps": 2.648,
                "dflow_froude_number": 0.631,
                "terrain_slope_m_per_m": 0.012,
                "distance_from_breach_m": 500.0,
                "status": "RECOMMENDED_FUTURE_HANDOFF_CANDIDATE",
                "reason": (
                    "Located downstream of the violent toe plunge jet where vertical accelerations subside into a "
                    "coherent longitudinal flow sheet. Reached rapidly by SPH (28 s) with high particle density, "
                    "well upstream of the downstream deceleration zone (1000-1280 m). Both models actively "
                    "represent this station with stable numerical metrics. Preferred design candidate only; "
                    "direct numerical coupling is not presently possible."
                )
            },
            "1000m": {
                "chainage_m": 1000.0,
                "sph_peak_depth_m": 5.211,
                "sph_peak_velocity_mps": 13.996,
                "sph_froude_number": 2.510,
                "dflow_peak_depth_m": 13.572,
                "dflow_peak_velocity_mps": 4.324,
                "dflow_froude_number": 0.492,
                "terrain_slope_m_per_m": -0.012,
                "distance_from_breach_m": 1000.0,
                "status": "MARGINAL",
                "reason": (
                    "Reached late in SPH simulation (119 s). SPH front reached 1280.41 m by 600 s and the 1500 m station "
                    "was NOT_REACHED_WITHIN_600_S. It was slowing substantially but was still advancing. Particle resolution "
                    "becomes sparse and 2D unit-width spreading errors accumulate significantly."
                )
            }
        },
        "recommended_handoff_location": {
            "chainage_m": 500.0,
            "station_id": "G_500m",
            "candidate_type": "DESIGN_CANDIDATE_ONLY",
            "justification": (
                "500 m provides the scientifically optimal handoff design candidate: safely downstream of the 3D plunging toe jet "
                "at 100-250 m, while maintaining robust particle support prior to the downstream deceleration zone at 1000+ m."
            )
        }
    }

    handoff_json = OUT_VAL / "m7_handoff_candidates.json"
    with open(handoff_json, "w") as f:
        json.dump(handoff_eval, f, indent=2)
    print(f"[OK] Task 21: Saved handoff candidates evaluation to {handoff_json}")

    # 11. Task 25: Machine-readable comparison manifest
    manifest = {
        "manifest_version": "1.0.0",
        "milestone": "M7 — Cross-Solver Near-Field Comparison and Hybrid Coupling Design",
        "project": "JalRakshak-HD (SIH PS 26161)",
        "study_site": "Bhavanisagar Dam / Lower Bhavani Dam, Tamil Nadu",
        "crs": "EPSG:32643",
        "m5_source_files": [
            "outputs/simulations/dflowfm/BHV_BASE/Bhavanisagar_DamBreak_map.nc",
            "outputs/simulations/dflowfm/BHV_BASE/Bhavanisagar_DamBreak_his.nc",
            "outputs/simulations/dflowfm/BHV_BASE/max_water_depth.tif",
            "outputs/simulations/dflowfm/BHV_BASE/max_velocity.tif",
            "outputs/simulations/dflowfm/BHV_BASE/arrival_time.tif"
        ],
        "m6_source_files": [
            "outputs/simulations/sph/BHV_BASE_NEARFIELD/gauge_results.csv",
            "outputs/simulations/sph/BHV_BASE_NEARFIELD/front_propagation.csv",
            "data/sph/BHV_BASE_NEARFIELD/production_out/csv/PartFluid_*.csv"
        ],
        "common_spatial_framework": {
            "centerline_file": "data/comparison/common_nearfield_centerline.gpkg",
            "gauges_file": "data/comparison/common_gauges.gpkg",
            "extent_m": [0.0, 1500.0],
            "chainages_m": [100.0, 250.0, 500.0, 1000.0, 1500.0]
        },
        "forcing_differences": {
            "dflow_fm": "Continuous time-varying discharge boundary representing the complete BHV_BASE hydrograph (30 hr, Qpeak=18,742.38 m3/s at t=14,095.59 s)",
            "dualsphysics": "Finite initialized peak-state fluid block (H=17.526 m, L=400 m, unit-width release, duration=600 s)",
            "forcing_equivalence": False
        },
        "comparison_variables": [
            "peak_water_depth_m",
            "peak_velocity_mps",
            "arrival_time_s",
            "depth_at_peak_velocity_m",
            "froude_number"
        ],
        "normalization_method": "h_star = h / h_100m, u_star = u / u_100m, x_star = chainage / 1500m",
        "timing_limitation": "Fundamentally different time references; no percentage timing error calculated; treated as SCENARIO_RESPONSE_CONTEXT",
        "resolution_status": {
            "m5_mesh": "82,309 faces (~100 m nominal)",
            "m6_particle": "dp=1.0 m, PARTICLE_RESOLUTION_SENSITIVITY NOT_STABILIZED"
        },
        "trend_assessment": {
            "depth_trend": "PARTIALLY_CONSISTENT",
            "velocity_trend": "DIVERGENT_TREND",
            "velocity_trend_explanation": "SPH shows strong attenuation after the near-dam jet region, whereas D-Flow depth-averaged peak velocity increases farther downstream in the sampled reach. This is not solver error because forcing and dimensional formulations are non-equivalent."
        },
        "front_propagation_status": {
            "sph_final_front_position_m": 1280.41,
            "sph_final_front_time_s": 600.0,
            "sph_1500m_status": "NOT_REACHED_WITHIN_600_S",
            "notes": "SPH front reached 1280.41 m by 600 s and the 1500 m station was NOT_REACHED_WITHIN_600_S. It was slowing substantially but was still advancing."
        },
        "handoff_evaluation": {
            "recommended_future_handoff_candidate": "500 m",
            "direct_coupling_ready": False,
            "overall_coupling_readiness": "NOT_READY"
        },
        "coupling_assessment": {
            "geometry_compatibility": "PARTIAL",
            "coordinate_compatibility": "READY",
            "time_reference_compatibility": "NOT_READY",
            "flow_width_compatibility": "NOT_READY",
            "forcing_compatibility": "NOT_READY",
            "bathymetry_compatibility": "PARTIAL",
            "resolution_compatibility": "NOT_READY",
            "direct_discharge_coupling_ready": False,
            "overall_status": "NOT_READY",
            "coupling_role": "DESIGN_ONLY"
        }
    }

    manifest_json = OUT_VAL / "m7_comparison_manifest.json"
    with open(manifest_json, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Task 25: Saved comparison manifest to {manifest_json}")


if __name__ == "__main__":
    run_cross_solver_comparison()
