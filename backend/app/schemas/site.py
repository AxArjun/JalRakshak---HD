"""Pydantic schemas and enums for generalized multi-site dam break modeling.

Supports any-dam/any-river onboarding with strict provenance and validation gates.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class VerificationClassification(str, Enum):
    """Standardized provenance and verification classifications for site data."""
    AUTHORITATIVE_VERIFIED = "AUTHORITATIVE_VERIFIED"
    SECONDARY_VERIFIED = "SECONDARY_VERIFIED"
    MODEL_DERIVED = "MODEL_DERIVED"
    MODEL_ASSUMPTION = "MODEL_ASSUMPTION"
    UNVERIFIED = "UNVERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ImpoundmentType(str, Enum):
    """Classification of the water impoundment / barrier structure."""
    ENGINEERED_DAM = "ENGINEERED_DAM"
    LANDSLIDE_DAM = "LANDSLIDE_DAM"
    GLACIAL_BLOCKAGE = "GLACIAL_BLOCKAGE"
    TEMPORARY_DEBRIS_BLOCKAGE = "TEMPORARY_DEBRIS_BLOCKAGE"
    OTHER = "OTHER"


class GateStatus(str, Enum):
    """Workflow readiness gate status."""
    READY = "READY"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DataSourceRecord(BaseModel):
    """Provenance tracking record for any site property or dataset."""
    parameter: str
    value: Optional[Any] = None
    unit: Optional[str] = None
    dataset_name: Optional[str] = None
    provider: Optional[str] = None
    retrieval_date: Optional[str] = None
    verification: VerificationClassification = VerificationClassification.UNVERIFIED
    citation: Optional[str] = None
    limitations: Optional[str] = None


class CRSConfig(BaseModel):
    """Spatial coordinate reference system configuration."""
    source_crs: str = "EPSG:4326"
    project_crs: str
    utm_zone: Optional[int] = None
    hemisphere: str = "N"
    derivation_reason: str = "AUTOMATIC_UTM_ZONE_DERIVATION"
    override_applied: bool = False


class DamIdentity(BaseModel):
    """Dam metadata and administrative identification."""
    dam_name: str
    river_name: str
    basin_name: str
    country: str = "India"
    state: str
    district: str
    latitude: float
    longitude: float
    impoundment_type: ImpoundmentType = ImpoundmentType.ENGINEERED_DAM
    national_id: Optional[str] = None
    year_completed: Optional[int] = None
    dam_type: Optional[str] = None  # e.g., Earth-fill / Composite / Concrete gravity


class DamGeometry(BaseModel):
    """Authoritative structural and engineering dimensions of the dam."""
    crest_elevation_m: Optional[float] = None
    dam_height_m: Optional[float] = None  # Height above lowest foundation or riverbed
    height_above_riverbed_m: Optional[float] = None
    crest_length_m: Optional[float] = None
    crest_width_m: Optional[float] = None
    upstream_slope_ratio: Optional[float] = None  # e.g., 3.0 for 1V:3H
    downstream_slope_ratio: Optional[float] = None  # e.g., 2.0 for 1V:2H
    spillway_type: Optional[str] = None
    spillway_crest_elevation_m: Optional[float] = None
    spillway_capacity_m3s: Optional[float] = None
    number_of_gates: Optional[int] = None
    verification: VerificationClassification = VerificationClassification.UNVERIFIED


class ReservoirMetadata(BaseModel):
    """Reservoir hydrological levels, surface areas, and storage capacities."""
    full_reservoir_level_m: Optional[float] = None  # FRL
    maximum_water_level_m: Optional[float] = None  # MWL
    dead_storage_level_m: Optional[float] = None  # DSL
    gross_storage_capacity_mcm: Optional[float] = None
    live_storage_capacity_mcm: Optional[float] = None
    dead_storage_capacity_mcm: Optional[float] = None
    reservoir_area_frl_km2: Optional[float] = None
    catchment_area_km2: Optional[float] = None
    verification: VerificationClassification = VerificationClassification.UNVERIFIED


class RiverMetadata(BaseModel):
    """Downstream river corridor characteristics."""
    reach_name: str
    downstream_length_km: float
    average_bed_slope: Optional[float] = None
    main_confluence: Optional[str] = None
    primary_gauges: List[str] = Field(default_factory=list)


class StudyAreaConfig(BaseModel):
    """Domain boundaries and spatial extents."""
    aoi_bbox_wgs84: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    dam_coordinates_wgs84: List[float]  # [lon, lat]
    downstream_reach_length_km: float
    domain_area_km2: Optional[float] = None
    crs: CRSConfig


class BreachScenarioConfig(BaseModel):
    """Configuration for parametric dam breach hydrograph modeling."""
    scenario_id: str
    scenario_name: str
    breach_method: str = "Froehlich_2008"
    breach_formation_mode: str = "OVERTOPPING"  # or PIPING
    failure_elevation_m: Optional[float] = None
    breach_bottom_elevation_m: Optional[float] = None
    breach_height_m: Optional[float] = None
    reservoir_volume_at_breach_mcm: Optional[float] = None
    average_breach_width_m: Optional[float] = None
    side_slope_z: float = 1.0  # 1V:zH
    breach_formation_time_s: Optional[float] = None
    peak_discharge_m3s: Optional[float] = None
    hydrograph_time_step_s: float = 60.0
    hydrograph_duration_s: float = 108000.0  # 30 hours
    verification: VerificationClassification = VerificationClassification.MODEL_DERIVED


class HydraulicModelConfig(BaseModel):
    """D-Flow FM 2D hydraulic flood routing configuration."""
    solver_name: str = "D-Flow FM"
    grid_type: str = "flexible_mesh_unstructured"
    target_cell_size_m: float = 50.0
    manning_roughness_global: float = 0.035
    upstream_boundary_type: str = "discharge_hydrograph"
    downstream_boundary_type: str = "waterlevel_or_weir"
    timestep_min_s: float = 0.1
    timestep_max_s: float = 10.0
    simulation_duration_s: float = 108000.0
    output_interval_s: float = 600.0


class SPHModelConfig(BaseModel):
    """DualSPHysics near-field 3D/2D SPH configuration."""
    solver_name: str = "DualSPHysics"
    dimension: str = "2D_UNIT_WIDTH"
    dp_particle_spacing_m: float = 1.0
    simulation_duration_s: float = 600.0
    upstream_reservoir_extent_m: float = 100.0
    downstream_chute_extent_m: float = 1500.0
    time_step_out_s: float = 1.0


class EarthObservationConfig(BaseModel):
    """Earth observation / satellite benchmark configuration."""
    satellite_platform: str = "Sentinel-1"
    orbit_pass_preference: Optional[str] = "DESCENDING"
    relative_orbit_preference: Optional[int] = None
    aoi_bounds: Optional[List[float]] = None
    detection_threshold_delta_db: float = -3.0


class ValidationStatus(BaseModel):
    """Status summary across all workflow stages."""
    gate_a_location: GateStatus = GateStatus.READY
    gate_b_terrain: GateStatus = GateStatus.BLOCKED
    gate_c_hydrology: GateStatus = GateStatus.BLOCKED
    gate_d_engineering: GateStatus = GateStatus.BLOCKED
    gate_e_breach: GateStatus = GateStatus.BLOCKED
    gate_f_hydraulic: GateStatus = GateStatus.BLOCKED
    gate_g_consequence: GateStatus = GateStatus.BLOCKED
    gate_h_earth_observation: GateStatus = GateStatus.BLOCKED
    overall_readiness: str = "INITIALIZED"
    blocking_reasons: List[str] = Field(default_factory=list)


class SiteConfig(BaseModel):
    """Root configuration object for any dam / river site in JalRakshak-HD."""
    site_id: str
    display_name: str
    description: str
    identity: DamIdentity
    geometry: DamGeometry
    reservoir: ReservoirMetadata
    river: RiverMetadata
    study_area: StudyAreaConfig
    breach_scenarios: Dict[str, BreachScenarioConfig] = Field(default_factory=dict)
    hydraulic_model: HydraulicModelConfig = Field(default_factory=HydraulicModelConfig)
    sph_model: SPHModelConfig = Field(default_factory=SPHModelConfig)
    earth_observation: EarthObservationConfig = Field(default_factory=EarthObservationConfig)
    provenance: List[DataSourceRecord] = Field(default_factory=list)
    validation: ValidationStatus = Field(default_factory=ValidationStatus)


class RunManifest(BaseModel):
    """Execution run manifest recording provenance and configuration hashes."""
    run_id: str
    site_id: str
    scenario_id: str
    created_at: str
    pipeline_version: str = "1.0.0"
    configuration_hash: str
    input_hashes: Dict[str, str] = Field(default_factory=dict)
    solver: str
    solver_version: Optional[str] = None
    classification: str
    status: str
    outputs: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
