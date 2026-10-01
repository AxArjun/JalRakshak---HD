"""
JalRakshak-HD: Health Check Endpoint (Task 3)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter
from backend.app.schemas.dashboard import HealthResponse

router = APIRouter(tags=["Health"])
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    milestones = {
        "M0_CORE_SETUP": "COMPLETE",
        "M1_TERRAIN_DEM": "COMPLETE",
        "M2_HYDROLOGY_NETWORK": "COMPLETE",
        "M3_DAM_ENGINEERING": "COMPLETE",
        "M4_BREACH_HYDROGRAPH": "COMPLETE",
        "M5_2D_DFLOWFM_SIMULATION": "COMPLETE",
        "M6_3D_SPH_NEARFIELD": "COMPLETE",
        "M7_CROSS_SOLVER_AUDIT": "COMPLETE",
        "M8_HADR_EXPOSURE": "COMPLETE",
        "M9_EARTH_OBSERVATION": "COMPLETE",
        "M10_GIS_DASHBOARD": "READY"
    }

    return HealthResponse(
        status="ready",
        project="JalRakshak-HD",
        backend_version="1.0.0",
        data_readiness="ALL_MILESTONES_COMPLETE",
        milestones_status=milestones,
        timestamp=now_str
    )
