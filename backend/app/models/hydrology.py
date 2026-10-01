"""Hydrology and river network domain models for JalRakshak-HD.

Defines schemas for river alignment metadata, remote-sensing-derived
reservoir extents, D8 drainage parameters, pour points, catchment
delineation records, and longitudinal profile summaries.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HydrologyVerificationLevel(str, Enum):
    """Scientific verification strength levels."""

    AUTHORITATIVE_VERIFIED = "AUTHORITATIVE_VERIFIED"
    SECONDARY_VERIFIED = "SECONDARY_VERIFIED"
    REMOTE_SENSING_DERIVED = "REMOTE_SENSING_DERIVED"
    DEM_DERIVED = "DEM_DERIVED"
    UNVERIFIED = "UNVERIFIED"


class RiverMetadata(BaseModel):
    """River reach and centerline metadata."""

    name: str = "Bhavani River"
    basin: str = "Cauvery Basin"
    sub_basin: Optional[str] = "Lower Cauvery"
    network_total_length_km: float = Field(..., description="Total length of all river features in AOI in km")
    mainstem_length_km: float = Field(..., description="Length of connected downstream Bhavani mainstem in km")
    start_distance_from_dam_m: float = Field(..., description="Distance from dam reference point to mainstem origin in meters")
    sinuosity: float = Field(..., description="Channel sinuosity ratio (thalweg length / valley length)")
    geometry_source: str
    verification_level: HydrologyVerificationLevel = HydrologyVerificationLevel.SECONDARY_VERIFIED
    downstream_flow_direction: str = "West-to-East / South-East"
    observed_surface_water_width_m: Optional[float] = None


class ReservoirGeometry(BaseModel):
    """Satellite-observed reservoir surface geometry attributes."""

    name: str = "Bhavanisagar Reservoir"
    occurrence50_area_km2: float = Field(..., description="Multi-decadal surface water occurrence (>=50%) area in km2")
    persistent_core_area_km2: Optional[float] = Field(None, description="Persistent water core (seasonality >= 10 mo) area in km2")
    perimeter_km: float = Field(..., description="Reservoir boundary perimeter in km")
    source_dataset: str = "JRC/GSW1_4/GlobalSurfaceWater"
    observation_period: str = "1984–2021 Multi-Decadal Historical Record"
    geometry_type: str = "REMOTE_SENSING_DERIVED_WATER_FREQUENCY_EXTENT"
    verification_level: HydrologyVerificationLevel = HydrologyVerificationLevel.REMOTE_SENSING_DERIVED
    uncertainty_notes: Optional[str] = None


class DrainageMetadata(BaseModel):
    """DEM hydrologic conditioning and flow routing parameters."""

    conditioning_method: str = "Priority-Flood Depression Filling"
    cells_modified_count: int
    cells_modified_percentage: float
    max_elevation_adjustment_m: float
    mean_elevation_adjustment_m: float
    flow_direction_method: str = "D8 Gradient-Enforced DAG Routing"
    accumulation_units: str = "upstream_contributing_cells"
    cell_area_m2: float = 900.0
    selected_stream_threshold_cells: int = 1000
    threshold_selection_basis: str


class PourPoint(BaseModel):
    """Dam pour point hydrologic snapping record."""

    original_dam_latitude: float
    original_dam_longitude: float
    snapped_x_projected: float
    snapped_y_projected: float
    snapped_latitude: float
    snapped_longitude: float
    snap_distance_m: float
    flow_accumulation_cells: int
    flow_accumulation_km2: float
    stream_threshold_cells: int
    valid_against_threshold: bool
    reason_for_snap: str
    status: str = "PASS"


class HydrobasinsContext(BaseModel):
    """HydroBASINS Level 12 upstream basin context."""

    dataset: str = "WWF/HydroSHEDS/v1/Basins/hybas_12"
    hybas_id: int = 4121595750
    main_bas: int = 4120028760
    next_down: int = 4121595720
    sub_area_sqkm: float = 161.8
    up_area_sqkm: float = 4257.7
    pfaf_id: int = 453804030300
    order: int = 2
    verification_level: HydrologyVerificationLevel = HydrologyVerificationLevel.SECONDARY_VERIFIED


class CatchmentMetadata(BaseModel):
    """Catchment and upstream basin context record."""

    local_catchment_area_km2: float
    catchment_polygon_touches_dem_boundary: bool
    upstream_flow_path_touches_dem_boundary: bool
    inflow_enters_from_outside_dem: bool
    catchment_truncated: bool
    local_catchment_validity: str = "INVALID_FOR_TOTAL_UPSTREAM_AREA"
    upstream_basin: HydrobasinsContext
    interpretation: str
    limitations: str


class RiverProfileSummary(BaseModel):
    """Downstream longitudinal profile diagnostic summary."""

    total_profile_length_m: float
    total_profile_length_km: float
    start_distance_from_dam_m: float
    start_elevation_m: float
    end_elevation_m: float
    net_elevation_fall_m: float
    average_slope_m_per_km: float
    average_longitudinal_slope: float
    sampling_interval_m: float
    number_of_uphill_steps: int
    max_uphill_step_m: float
    starts_above_frl: bool


class HydrologyStudy(BaseModel):
    """Comprehensive container model for M2 hydrologic foundation."""

    study_area_id: str
    river: RiverMetadata
    reservoir: ReservoirGeometry
    drainage: DrainageMetadata
    pour_point: PourPoint
    catchment: CatchmentMetadata
    profile: RiverProfileSummary
