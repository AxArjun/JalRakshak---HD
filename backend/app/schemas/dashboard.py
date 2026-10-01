"""
JalRakshak-HD: Milestone M10 Task 21 — Dashboard Response Schemas
=================================================================
Pydantic schemas for typed API responses across all dashboard endpoints.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ready"
    project: str = "JalRakshak-HD"
    backend_version: str = "1.0.0"
    data_readiness: str = "ALL_MILESTONES_COMPLETE"
    milestones_status: Dict[str, str]
    timestamp: str


class ProjectSummary(BaseModel):
    project_name: str
    problem_statement: str
    study_area: str
    dam: str
    river: str
    frl_m_msl: float
    scenario_id: str
    scenario_classification: str
    simulation_duration_hours: float
    dflow_solver_version: str
    sph_solver_version: str
    crs: str
    bounds_wgs84: List[List[float]]
    scientific_disclaimer: str


class ScenarioSummary(BaseModel):
    scenario_id: str
    hypothetical: bool = True
    initial_water_level_m_msl: float
    hydrograph_classification: str
    peak_discharge_m3s: float
    flood_volume_mcm: float
    breach_width_m: float
    breach_formation_time_hr: float
    model_assumptions: List[str]
    scientific_warnings: List[str]
    simulation_classification: str


class SimulationFrameMetadata(BaseModel):
    frame_index: int
    solver_time_s: float
    solver_time_hr: float
    timestamp_label: str
    max_depth_at_frame: float
    wet_area_km2: float
    image_filename: str
    image_url: str
    bounds_wgs84: List[List[float]]


class SimulationTimeline(BaseModel):
    scenario_id: str
    total_frames: int
    interval_seconds: int
    total_duration_hours: float
    bounds_wgs84: List[List[float]]
    depth_legend_bins: List[Dict[str, Any]]
    frames: List[SimulationFrameMetadata]


class HydrographPoint(BaseModel):
    time_s: float
    time_hr: float
    discharge_m3s: float
    cumulative_volume_m3: float


class HydrographData(BaseModel):
    scenario_id: str
    peak_discharge_m3s: float
    total_volume_m3: float
    data_points_count: int
    hydrograph: List[HydrographPoint]


class SimulationStation(BaseModel):
    station_id: str
    name: str
    chainage_km: float
    coordinates_utm: List[float]
    coordinates_wgs84: List[float]
    arrival_time_hr: float
    peak_depth_m: float
    peak_velocity_mps: float


class PointAnalysis(BaseModel):
    location: Dict[str, float]
    in_study_area: bool
    max_depth_m: Optional[float]
    max_velocity_mps: Optional[float]
    arrival_time_hr: Optional[float]
    hazard_class: Optional[str]
    hazard_description: Optional[str]
    response_zone: Optional[str]
    response_zone_rank: Optional[int]
    historical_flood_detected: bool
    latest_candidate_water_change: bool
    status_message: str


class HADRSummary(BaseModel):
    model_config = {"extra": "allow"}
    milestone: Optional[str] = "M8"
    site_id: Optional[str] = "bhavanisagar"
    total_inundated_area_km2: float = 101.29
    severe_hazard_h3_h6_area_km2: Optional[float] = 97.99
    severe_h3h6_area_km2: Optional[float] = 97.99
    severe_h3h6_pct: Optional[float] = 96.74
    extreme_hazard_h5_h6_area_km2: Optional[float] = 87.29
    extreme_h5h6_area_km2: Optional[float] = 87.29
    worldpop_exposed: float = 42428.1
    worldpop_total: Optional[float] = 42428.1
    ghsl_exposed: float = 84500.5
    ghsl_total: Optional[float] = 84500.5
    h3_h6_population_worldpop: Optional[float] = 40744.3
    buildings_exposed: int = 25652
    buildings_total: Optional[int] = 25652
    h5_h6_buildings_exposed: int = 22472
    h5_h6_buildings_total: Optional[int] = 22472
    cropland_exposed_km2: Optional[float] = 39.66
    cropland_km2: Optional[float] = 39.66
    built_up_exposed_km2: Optional[float] = 7.86
    builtup_km2: Optional[float] = 7.86
    roads_exposed_km: float = 243.82
    roads_km: Optional[float] = 243.82
    h3_h6_roads_km: Optional[float] = 226.35
    bridges_exposed_count: int = 20
    bridges: Optional[int] = 20
    bridges_total: Optional[int] = 20
    critical_facilities_count: int = 13
    critical_facilities: Optional[int] = 13
    critical_facilities_total: Optional[int] = 13
    h3_h6_area_km2: Optional[float] = 97.99
    population_datasets_note: Optional[str] = ""
    hazard_classes: Optional[List[Dict[str, Any]]] = None
    hazard_areas_km2: Optional[Dict[str, float]] = None


class HADRZoneDetail(BaseModel):
    model_config = {"extra": "allow"}
    rank: int
    zone_id: str
    name: Optional[str] = ""
    zone_name: Optional[str] = ""
    priority: Optional[str] = ""
    priority_rank: Optional[int] = None
    max_hazard: str = "H6"
    dominant_hazard: Optional[str] = "H6"
    earliest_arrival_min: float = 0.0
    earliest_arrival: Optional[str] = ""
    earliest_arrival_hr: Optional[float] = 0.0
    worldpop: Optional[float] = None
    worldpop_exposure: float = 0.0
    ghsl: Optional[float] = None
    ghsl_exposure: float = 0.0
    buildings: Optional[int] = None
    buildings_count: int = 0
    h5_h6_buildings: Optional[int] = None
    h5_h6_buildings_count: int = 0
    roads_km: Optional[float] = None
    roads_exposed_km: float = 0.0
    area_km2: Optional[float] = 0.0
    critical_facilities: Optional[int] = None
    critical_facilities_count: int = 0
    operational_screening_note: Optional[str] = ""


class SPHGaugeResult(BaseModel):
    gauge_name: str
    chainage_m: float
    easting: float
    northing: float
    longitude: float
    latitude: float
    arrival_time_s: Union[float, str]
    arrival_time_min: Union[float, str]
    max_water_depth_m: float
    max_velocity_mps: float
    time_of_max_velocity_s: Union[float, str]


class SPHSummary(BaseModel):
    model_classification: str
    coupling_status: str
    domain_length_m: float
    particle_spacing_dp_m: float
    total_particles: int
    simulation_duration_s: float
    max_depth_m: float
    p95_depth_m: float
    max_velocity_mps: float
    p95_velocity_mps: float
    max_front_chainage_m: float
    limitations: List[str]


class CrossSolverComparison(BaseModel):
    comparison_classification: str
    forcing_equivalent: bool
    depth_trend: str
    velocity_trend: str
    future_handoff_candidate_m: float
    direct_coupling_ready: bool
    profile_data: List[Dict[str, Any]]
    scientific_interpretation: str


class HistoricalSatelliteSummary(BaseModel):
    event_name: str
    official_flood_period: Dict[str, str]
    sentinel1_scene_id: str
    orbit_pass: str
    relative_orbit: int
    recurrent_water_baseline_km2: float
    observed_new_flood_raster_km2: float
    observed_new_flood_vector_km2: float
    m5_intersection_km2: float
    m5_overlap_fraction_pct: float
    spatial_context_classification: str
    model_validation: bool = False
    scientific_disclaimer: str


class LatestSatelliteMonitoring(BaseModel):
    scene_id: str
    platform: str
    acquisition_datetime: str
    observation_age_hours: float
    days_since_acquisition: float
    candidate_new_water_area_km2: float
    latest_status: str
    cause: str
    observation_quality: str
    flood_interpretation_confidence: str
    quality_details: Dict[str, Any]


class ProvenanceItem(BaseModel):
    category: str
    source_dataset: str
    provider_agency: str
    year_or_date: str
    classification: str
    key_limitations: str
