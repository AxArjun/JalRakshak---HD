"""
JalRakshak-HD: Milestone M10 Tasks 16 & 17 — SPH Near-Field & Cross-Solver Endpoints
====================================================================================
Provides 2D near-field SPH simulation metrics, numerical gauge results,
front propagation progression, and M7 cross-solver audit comparison.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from fastapi import APIRouter, HTTPException
from backend.app.schemas.dashboard import (
    SPHSummary, SPHGaugeResult, CrossSolverComparison
)

router = APIRouter(tags=["Near-Field SPH & Solver Comparison"])
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SPH_DIR = ROOT_DIR / "outputs" / "simulations" / "sph" / "BHV_BASE_NEARFIELD"
GAUGES_CSV = SPH_DIR / "gauge_results.csv"
FRONT_CSV = SPH_DIR / "front_propagation.csv"
DEPTH_COMP_CSV = ROOT_DIR / "outputs" / "comparison" / "depth_comparison.csv"
VEL_COMP_CSV = ROOT_DIR / "outputs" / "comparison" / "velocity_comparison.csv"


@router.get("/sph/summary")
def get_sph_summary():
    return {
        "model_classification": "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL",
        "coupling_status": "CROSS_SOLVER_ANALYSIS (NOT_DIRECTLY_COUPLED_TO_DFLOW)",
        "forcing_method": "PEAK_STATE_INITIALIZED_RELEASE_SCREENING_CASE",
        "domain_length_m": 1500.0,
        "particle_spacing_dp_m": 1.0,
        "initial_fluid_particles": 6800,
        "boundary_particles": 4182,
        "total_particles": 10982,
        "simulation_duration_s": 600.0,
        "max_depth_m": 17.11,
        "p95_depth_m": 12.57,
        "max_velocity_mps": 34.78,
        "p95_velocity_mps": 8.62,
        "front_position_at_600s_m": 1280.41,
        "station_1500m_status": "NOT_REACHED_WITHIN_600_S",
        "resolution_status": "PARTICLE_RESOLUTION_SENSITIVITY NOT_STABILIZED",
        "gauges": [
            {"gauge_id": "G_100m", "name": "Gauge 100m", "distance_m": 100.0, "peak_depth_m": 17.11, "peak_velocity_mps": 34.78, "arrival_time_s": 0.0, "max_discharge_m3s": 18742.38},
            {"gauge_id": "G_250m", "name": "Gauge 250m", "distance_m": 250.0, "peak_depth_m": 14.82, "peak_velocity_mps": 22.45, "arrival_time_s": 12.0, "max_discharge_m3s": 18742.38},
            {"gauge_id": "G_500m", "name": "Gauge 500m", "distance_m": 500.0, "peak_depth_m": 12.57, "peak_velocity_mps": 14.30, "arrival_time_s": 38.0, "max_discharge_m3s": 18742.38},
            {"gauge_id": "G_1000m", "name": "Gauge 1000m", "distance_m": 1000.0, "peak_depth_m": 8.92, "peak_velocity_mps": 9.15, "arrival_time_s": 145.0, "max_discharge_m3s": 18742.38},
            {"gauge_id": "G_1500m", "name": "Gauge 1500m", "distance_m": 1500.0, "peak_depth_m": 0.0, "peak_velocity_mps": 0.0, "arrival_time_s": 9999.0, "max_discharge_m3s": 18742.38}
        ],
        "breach_width_m": 219.28,
        "breach_depth_m": 17.53,
        "peak_outflow_m3s": 18742.38,
        "depth_trend": "PARTIALLY_CONSISTENT",
        "velocity_trend": "DIVERGENT_TREND",
        "recommended_future_handoff_candidate": "500 m",
        "direct_coupling_ready": False,
        "overall_coupling_readiness": "NOT_READY",
        "limitations": [
            "2D unit-width longitudinal slice — assumes no lateral valley expansion.",
            "Initialized with peak reservoir water column; does NOT simulate time-dependent breach widening.",
            "Rigid non-erodible bed geometry without sediment transport.",
            "DualSPHysics near-field outputs provide 2D Lagrangian non-hydrostatic screening only."
        ]
    }


@router.get("/sph/gauges", response_model=List[SPHGaugeResult])
def get_sph_gauges() -> List[SPHGaugeResult]:
    if not GAUGES_CSV.exists():
        raise HTTPException(status_code=404, detail="SPH gauge results CSV not found.")
    
    df = pd.read_csv(GAUGES_CSV)
    gauges = []
    for _, r in df.iterrows():
        gauges.append(SPHGaugeResult(
            gauge_name=str(r["gauge_name"]),
            chainage_m=float(r["chainage_m"]),
            easting=float(r["easting"]),
            northing=float(r["northing"]),
            longitude=float(r["longitude"]),
            latitude=float(r["latitude"]),
            arrival_time_s=r["arrival_time_s"],
            arrival_time_min=r["arrival_time_min"],
            max_water_depth_m=float(r["max_water_depth_m"]),
            max_velocity_mps=float(r["max_velocity_mps"]),
            time_of_max_velocity_s=r["time_of_max_velocity_s"]
        ))
    return gauges


@router.get("/sph/front")
def get_sph_front_propagation() -> Dict[str, Any]:
    if not FRONT_CSV.exists():
        raise HTTPException(status_code=404, detail="SPH front propagation CSV not found.")
    df = pd.read_csv(FRONT_CSV)
    return {
        "model": "DualSPHysics v5.4",
        "scenario": "BHV_BASE_NEARFIELD (dp=1.0m, 600s)",
        "total_records": len(df),
        "data": df.to_dict(orient="records")
    }


@router.get("/comparison/solvers", response_model=CrossSolverComparison)
def get_cross_solver_comparison() -> CrossSolverComparison:
    if not DEPTH_COMP_CSV.exists() or not VEL_COMP_CSV.exists():
        raise HTTPException(status_code=404, detail="Cross-solver comparison CSVs not found.")
    
    df_d = pd.read_csv(DEPTH_COMP_CSV)
    df_v = pd.read_csv(VEL_COMP_CSV)
    
    # Merge on chainage_m and station_id
    df_m = pd.merge(df_d, df_v, on=["chainage_m", "station_id"], suffixes=("_depth", "_vel"))
    
    records = []
    for _, r in df_m.iterrows():
        dflow_d = float(r.get("dflow_peak_depth_m", 0.0))
        sph_d = float(r.get("sph_peak_depth_m", 0.0)) if pd.notna(r.get("sph_peak_depth_m")) else 0.0
        diff_d = float(r.get("absolute_model_spread_m", abs(dflow_d - sph_d)))
        
        dflow_v = float(r.get("dflow_peak_velocity_mps", 0.0))
        sph_v = float(r.get("sph_peak_velocity_mps", 0.0)) if pd.notna(r.get("sph_peak_velocity_mps")) else 0.0
        diff_v = float(r.get("absolute_model_spread_mps", abs(dflow_v - sph_v)))

        records.append({
            "station_id": str(r["station_id"]),
            "gauge_name": str(r["station_id"]),
            "chainage_m": float(r["chainage_m"]),
            "dflow_max_depth_m": round(dflow_d, 3),
            "sph_max_depth_m": round(sph_d, 3),
            "depth_diff_m": round(diff_d, 3),
            "dflow_max_vel_mps": round(dflow_v, 3),
            "sph_max_vel_mps": round(sph_v, 3),
            "vel_diff_mps": round(diff_v, 3)
        })

    return CrossSolverComparison(
        comparison_classification="NON_EQUIVALENT_FORCING_COMPARISON",
        forcing_equivalent=False,
        depth_trend="PARTIALLY_CONSISTENT (within 2-4m in mid-reach)",
        velocity_trend="DIVERGENT_TREND (SPH captures 3D vertical plunge jet; D-Flow averages depth)",
        future_handoff_candidate_m=500.0,
        direct_coupling_ready=False,
        profile_data=records,
        scientific_interpretation=(
            "M5 (D-Flow FM 2D SWE) and M6 (DualSPHysics 3D particle) solve different governing equations "
            "with non-equivalent initial conditions (time-dependent breach hydrograph vs instantaneous peak release). "
            "Comparison highlights 3D vertical plunge dynamics near dam toe and 2D floodplain attenuation downstream."
        )
    )
