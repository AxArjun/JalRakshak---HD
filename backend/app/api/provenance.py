"""
JalRakshak-HD: Milestone M10 Task 20 — Provenance & Scientific Lineage Endpoint
================================================================================
Provides structured source provenance, citations, and explicit scientific limitations.
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter
from backend.app.schemas.dashboard import ProvenanceItem

router = APIRouter(prefix="/provenance", tags=["Data Provenance & Scientific Lineage"])


@router.get("", response_model=List[ProvenanceItem])
def get_provenance() -> List[ProvenanceItem]:
    items = [
        {
            "category": "Dam Engineering & Levels",
            "source_dataset": "Central Water Commission (CWC) NRLD & TNWRD Project Record",
            "provider_agency": "Central Water Commission (CWC) & Tamil Nadu Water Resources Department",
            "year_or_date": "1955 / 2024 CWC Appraisal",
            "classification": "AUTHORITATIVE_VERIFIED",
            "key_limitations": "FRL verified at 280.42 m MSL; Full Depth (105 ft) is sill-relative column height; MWL/Crest marked UNVERIFIED pending design drawings."
        },
        {
            "category": "Topography & DEM",
            "source_dataset": "NASA Shuttle Radar Topography Mission Global 1 Arc-Second (SRTM V3)",
            "provider_agency": "NASA JPL / USGS EROS",
            "year_or_date": "2000 (Reprocessed 2014)",
            "classification": "DEM_DERIVED",
            "key_limitations": "30m resolution radar DSM; captures vegetation canopy tops; does not resolve sub-grid culverts or narrow masonry embankments."
        },
        {
            "category": "Hydrology & River Network",
            "source_dataset": "OpenStreetMap Mainstem & HydroSHEDS / HydroBASINS Level 12",
            "provider_agency": "OpenStreetMap Contributors & WWF / HydroSHEDS (Lehner & Grill 2013)",
            "year_or_date": "2024 OSM Overpass & 2013 HydroSHEDS",
            "classification": "SECONDARY_VERIFIED",
            "key_limitations": "Mainstem aligns with channel thalweg within 43.2m median error; upstream basin boundaries truncated outside DEM."
        },
        {
            "category": "Breach Hydrograph",
            "source_dataset": "Froehlich (2008) Geometry & Von Thun & Gillette (1990) Timing Synthesis",
            "provider_agency": "Empirical dam breach literature / JalRakshak-HD Synthesis Engine",
            "year_or_date": "2008 / 1990",
            "classification": "EMPIRICAL_PARAMETRIC_FROEHLEH_VON_THUN_SYNTHESIS",
            "key_limitations": "Empirical envelope overtopping/piping hydrograph (Qpeak = 18,742 m3/s); hypothetical extreme stress-test."
        },
        {
            "category": "2D Hydrodynamic Simulation",
            "source_dataset": "Deltares D-Flow Flexible Mesh (D-Flow FM 1.2.181)",
            "provider_agency": "Deltares Open-Source Hydraulic Suite",
            "year_or_date": "2024 Engine Build",
            "classification": "2D_DFLOWFM_SCREENING_INUNDATION_MODEL",
            "key_limitations": "2D Shallow Water Equations; hydrostatic pressure assumption; Manning n = 0.035 s/m^(1/3) uniform roughness."
        },
        {
            "category": "3D Near-Field Dynamics",
            "source_dataset": "DualSPHysics v5.4 (Smoothed Particle Hydrodynamics)",
            "provider_agency": "DualSPHysics Open-Source Particle Engine",
            "year_or_date": "2024 Engine Build",
            "classification": "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL",
            "key_limitations": "2D longitudinal unit-width slice (dp=1.0m, 15,164 particles); standalone peak release; NOT coupled directly to D-Flow."
        },
        {
            "category": "Population Exposure",
            "source_dataset": "WorldPop 2020 (100m UN-Adjusted) & GHSL 2025 (100m Built-Up Population)",
            "provider_agency": "WorldPop Project & European Commission Joint Research Centre (JRC)",
            "year_or_date": "2020 / 2025 Projection",
            "classification": "HADR_POPULATION_EXPOSURE_DUAL_CROSSCHECK",
            "key_limitations": "Reported side-by-side (WorldPop: 42,428; GHSL: 84,501); raster pixel fractions strictly conserved."
        },
        {
            "category": "Building Infrastructure",
            "source_dataset": "Google Open Buildings v3 (High-Confidence Footprints)",
            "provider_agency": "Google Research & OpenStreetMap",
            "year_or_date": "2023",
            "classification": "HADR_BUILDING_EXPOSURE",
            "key_limitations": "25,652 inundated building footprints; structural vulnerability screening based on CWC hazard depth/velocity."
        },
        {
            "category": "Historical Satellite Flood",
            "source_dataset": "Copernicus Sentinel-1 SAR GRD & JRC Global Surface Water v1.4",
            "provider_agency": "ESA Copernicus & European Commission Joint Research Centre",
            "year_or_date": "August 2019 / 1984–2021 Baseline",
            "classification": "HISTORICAL_FLOOD_REMOTE_SENSING_BENCHMARK",
            "key_limitations": "Meteorological flood release benchmark (1.19 km2); provides spatial context only; does NOT validate dam-break simulation."
        },
        {
            "category": "Near-Real-Time Monitoring",
            "source_dataset": "Google Earth Engine Sentinel-1 SAR Pipeline (`COPERNICUS/S1_GRD`)",
            "provider_agency": "Google Earth Engine API & ESA",
            "year_or_date": "2026 Live NRT",
            "classification": "NRT_FLOOD_MONITORING_PIPELINE",
            "key_limitations": "Satellite revisit latency 6–12 days; candidate water change labeled UNVERIFIED / UNCONFIRMED pending ground gauge data."
        }
    ]
    return [ProvenanceItem(**item) for item in items]
