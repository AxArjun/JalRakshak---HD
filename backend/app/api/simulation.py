"""
JalRakshak-HD: Simulation Timeline, Hydrograph & Station Endpoints (Tasks 10, 11, 12)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.app.schemas.dashboard import (
    SimulationTimeline, SimulationFrameMetadata, HydrographData, HydrographPoint, SimulationStation
)

router = APIRouter(prefix="/simulation", tags=["Simulation"])
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
FRAMES_DIR = ROOT_DIR / "outputs" / "dashboard" / "simulation_frames"
HYDROGRAPH_CSV = ROOT_DIR / "data" / "dflowfm" / "hydrographs" / "BHV_BASE.csv"
STATIONS_CSV = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE" / "observation_hydrographs.csv"


@router.get("/timeline", response_model=SimulationTimeline)
def get_simulation_timeline() -> SimulationTimeline:
    meta_path = FRAMES_DIR / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Simulation frames metadata not found. Run frame preprocessing first.")
    
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return SimulationTimeline(
        scenario_id=data["scenario_id"],
        total_frames=data["total_frames"],
        interval_seconds=data["interval_seconds"],
        total_duration_hours=data["total_duration_hours"],
        bounds_wgs84=data["bounds_wgs84"]["leaflet_bounds"],
        depth_legend_bins=data["depth_legend_bins_m"],
        frames=[SimulationFrameMetadata(**frm) for frm in data["frames"]]
    )


@router.get("/meta")
def get_simulation_meta():
    return {
        "model": "D-Flow FM 1.2.181 (Deltares)",
        "scenario": "BHV_BASE",
        "classification": "HYPOTHETICAL_ENGINEERING_STRESS_TEST",
        "domain_area_km2": 818.37,
        "max_inundated_area_km2": 101.29,
        "solver_max_depth_m": 22.02,
        "p95_depth_m": 12.72,
        "solver_max_velocity_mps": 11.79,
        "p95_velocity_mps": 4.27,
        "rendered_raster_max_depth_m": 21.92,
        "rendered_raster_max_velocity_mps": 11.72,
        "peak_depth_m": 22.02,
        "peak_velocity_mps": 11.79,
        "total_frames": 181,
        "simulation_duration_s": 108000.0,
        "duration_hours": 30.0,
        "timestep_hours": 0.166,
        "frame_rate_s": 600,
        "bounds_wgs84": [[11.359179, 77.111197], [11.57997, 77.423552]],
        "breach_start_hour": 0.0
    }


@router.get("/frame/{frame_index}", response_model=SimulationFrameMetadata)
def get_simulation_frame(frame_index: int) -> SimulationFrameMetadata:
    meta_path = FRAMES_DIR / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Simulation frames metadata not found.")
    
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if frame_index < 0 or frame_index >= len(data["frames"]):
        raise HTTPException(status_code=404, detail=f"Frame index {frame_index} out of range (0 to {len(data['frames'])-1}).")

    return SimulationFrameMetadata(**data["frames"][frame_index])


@router.get("/frames/{filename}")
def get_frame_image(filename: str):
    file_path = FRAMES_DIR / filename
    if not file_path.exists() or not filename.endswith(".png"):
        raise HTTPException(status_code=404, detail="Frame image not found.")
    return FileResponse(file_path, media_type="image/png")


@router.get("/hydrograph", response_model=HydrographData)
def get_hydrograph() -> HydrographData:
    if not HYDROGRAPH_CSV.exists():
        raise HTTPException(status_code=404, detail="Breach hydrograph CSV not found.")
    
    df = pd.read_csv(HYDROGRAPH_CSV)
    
    # Required columns: time_s, discharge_m3s (or time_hr)
    time_s = df["time_s"].values if "time_s" in df.columns else df["time_hr"].values * 3600.0
    time_hr = df["time_hr"].values if "time_hr" in df.columns else df["time_s"].values / 3600.0
    q = df["discharge_m3s"].values

    # Compute cumulative volume
    dt = np.diff(time_s, prepend=0)
    cum_vol = np.cumsum(q * dt)

    points = []
    for ts, th, q_val, v_val in zip(time_s, time_hr, q, cum_vol):
        points.append(HydrographPoint(
            time_s=round(float(ts), 2),
            time_hr=round(float(th), 3),
            discharge_m3s=round(float(q_val), 2),
            cumulative_volume_m3=round(float(v_val), 2)
        ))

    return HydrographData(
        scenario_id="BHV_BASE",
        peak_discharge_m3s=round(float(np.max(q)), 2),
        total_volume_m3=round(float(cum_vol[-1]), 2),
        data_points_count=len(points),
        hydrograph=points
    )


@router.get("/stations", response_model=List[SimulationStation])
def get_observation_stations() -> List[SimulationStation]:
    # Key downstream observation points across Bhavanisagar flood corridor
    stations = [
        {
            "station_id": "OBS_01_TOE",
            "name": "Dam Toe / Outlet Structure",
            "chainage_km": 0.1,
            "coordinates_utm": [730500.0, 1271300.0],
            "coordinates_wgs84": [11.4705, 77.1140],
            "arrival_time_hr": 0.05,
            "peak_depth_m": 21.98,
            "peak_velocity_mps": 10.76
        },
        {
            "station_id": "OBS_02_SATHYAMANGALAM",
            "name": "Sathyamangalam Urban Reach",
            "chainage_km": 15.2,
            "coordinates_utm": [743800.0, 1272900.0],
            "coordinates_wgs84": [11.5030, 77.2360],
            "arrival_time_hr": 1.15,
            "peak_depth_m": 9.42,
            "peak_velocity_mps": 4.85
        },
        {
            "station_id": "OBS_03_KODIVERI",
            "name": "Kodiveri Anicut & Regulator",
            "chainage_km": 24.8,
            "coordinates_utm": [751500.0, 1269800.0],
            "coordinates_wgs84": [11.4810, 77.3060],
            "arrival_time_hr": 2.45,
            "peak_depth_m": 6.85,
            "peak_velocity_mps": 3.20
        },
        {
            "station_id": "OBS_04_GOBI_BORDER",
            "name": "Gobichettipalayam Rural Confluence",
            "chainage_km": 34.0,
            "coordinates_utm": [759200.0, 1267400.0],
            "coordinates_wgs84": [11.4600, 77.3770],
            "arrival_time_hr": 4.10,
            "peak_depth_m": 4.52,
            "peak_velocity_mps": 2.10
        }
    ]
    return [SimulationStation(**s) for s in stations]
