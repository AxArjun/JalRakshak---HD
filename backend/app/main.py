"""
JalRakshak-HD: FastAPI Backend Application (Milestone M10 Task 2)
=================================================================
Unified API backend serving hydraulic simulation frames, GIS vector layers,
point sampling analysis, HADR consequence summaries, SPH near-field diagnostics,
and Earth Observation satellite benchmarks.
"""

from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.health import router as health_router
from backend.app.api.project import router as project_router
from backend.app.api.simulation import router as simulation_router
from backend.app.api.gis import router as gis_router
from backend.app.api.hadr import router as hadr_router
from backend.app.api.sph import router as sph_router
from backend.app.api.remote_sensing import router as remote_sensing_router
from backend.app.api.provenance import router as provenance_router
from backend.app.api.sites import router as sites_router
from backend.app.api.reports import router as reports_router

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FRAMES_DIR = ROOT_DIR / "outputs" / "dashboard" / "simulation_frames"
OVERLAYS_DIR = ROOT_DIR / "outputs" / "dashboard" / "overlays"
GEOJSON_DIR = ROOT_DIR / "outputs" / "dashboard" / "geojson"

app = FastAPI(
    title="JalRakshak-HD: Dam Safety & GIS Command Centre API",
    description="Operational API for Bhavanisagar Dam Hypothetical Breach Inundation, HADR Exposure & Satellite Monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API route modules under /api
app.include_router(health_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(gis_router, prefix="/api")
app.include_router(hadr_router, prefix="/api")
app.include_router(sph_router, prefix="/api")
app.include_router(remote_sensing_router, prefix="/api")
app.include_router(provenance_router, prefix="/api")
app.include_router(sites_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

# Mount static asset directories if they exist
if FRAMES_DIR.exists():
    app.mount("/api/simulation/frames", StaticFiles(directory=str(FRAMES_DIR)), name="simulation_frames")
    app.mount("/api/tiles/simulation_frames", StaticFiles(directory=str(FRAMES_DIR)), name="tiles_simulation_frames")
if OVERLAYS_DIR.exists():
    app.mount("/api/tiles/overlays", StaticFiles(directory=str(OVERLAYS_DIR)), name="raster_overlays")
if GEOJSON_DIR.exists():
    app.mount("/api/tiles/geojson", StaticFiles(directory=str(GEOJSON_DIR)), name="tiles_geojson")


@app.get("/")
def root_info():
    return {
        "project": "JalRakshak-HD",
        "service": "Dam Safety & GIS Simulation Dashboard Backend",
        "api_docs": "/docs",
        "status": "ready"
    }


@app.get("/health")
def root_health():
    return {
        "status": "ready",
        "project": "JalRakshak-HD",
        "backend_version": "1.0.0"
    }
