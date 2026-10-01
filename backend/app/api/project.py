"""
JalRakshak-HD: Project & Scenario Summary Endpoints (Task 4 & 5)
"""

from __future__ import annotations

import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.app.schemas.dashboard import ProjectSummary, ScenarioSummary

router = APIRouter(tags=["Project & Scenarios"])
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = ROOT_DIR / "configs" / "study_area.yaml"


@router.get("/project")
@router.get("/project/meta")
def get_project_summary():
    return {
        "project": "JalRakshak-HD",
        "milestone": "M10",
        "scenario": "BHV_BASE",
        "classification": "HYPOTHETICAL_ENGINEERING_STRESS_TEST",
        "scenario_note": "Bhavanisagar Dam hypothetical breach screening scenario. NOT an operational forecast.",
        "dam": "Bhavanisagar Dam (Lower Bhavani)",
        "river": "Bhavani River (Cauvery Basin)",
        "domain_area_km2": 818.37,
        "max_inundated_area_km2": 101.29,
        "study_area_km": 101.29,
        "coordinate_system": "EPSG:32643 (UTM 43N) / WGS84",
        "terrain_source": "NASA SRTM 30 m DEM",
        "backend_status": "operational"
    }


@router.get("/scenario/BHV_BASE", response_model=ScenarioSummary)
def get_scenario_summary() -> ScenarioSummary:
    return ScenarioSummary(
        scenario_id="BHV_BASE",
        hypothetical=True,
        initial_water_level_m_msl=280.42,
        hydrograph_classification="EMPIRICAL_PARAMETRIC_FROEHLEH_VON_THUN_SYNTHESIS",
        peak_discharge_m3s=18742.38,
        flood_volume_mcm=408.0,
        breach_width_m=136.5,
        breach_formation_time_hr=1.42,
        model_assumptions=[
            "Full Reservoir Level (280.42 m MSL) initial condition",
            "Trapezoidal composite overtopping / piping breach initiation",
            "Froehlich (2008) geometry & Von Thun & Gillette (1990) formation timing",
            "Rigid non-erodible downstream bathymetry (SRTM 30m DEM)"
        ],
        scientific_warnings=[
            "Hypothetical stress test — Bhavanisagar Dam has never failed and is currently intact.",
            "Hydrograph represents an extreme upper-bound screening envelope."
        ],
        simulation_classification="2D_DFLOWFM_SCREENING_INUNDATION_MODEL"
    )
