"""
Breach event definition and scenario models for JalRakshak-HD.
SIH PS 26161 - Milestone M3 (Repaired).

Defines schemas for hypothetical breach scenarios, empirical parameter estimates,
uncertainty envelopes, and spatial breach coordinates.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FailureMechanism(str, Enum):
    """Supported dam failure mechanisms."""

    PRESCRIBED_BREACH = "PRESCRIBED_BREACH"
    OVERTOPPING = "OVERTOPPING"
    PIPING = "PIPING"
    CONTROLLED_RELEASE = "CONTROLLED_RELEASE"
    NATURAL_BLOCKAGE_FAILURE = "NATURAL_BLOCKAGE_FAILURE"


class ScenarioType(str, Enum):
    """Classification of simulation scenario."""

    HYPOTHETICAL_ENGINEERING_STRESS_TEST = "HYPOTHETICAL_ENGINEERING_STRESS_TEST"
    HISTORICAL_RECONSTRUCTION = "HISTORICAL_RECONSTRUCTION"
    DESIGN_FLOOD_ROUTING = "DESIGN_FLOOD_ROUTING"


class ModelResultStatus(str, Enum):
    """Execution status of empirical model."""

    VALID = "VALID"
    VALID_WITH_EXTRAPOLATION = "VALID_WITH_EXTRAPOLATION"
    INSUFFICIENT_VERIFIED_INPUT = "INSUFFICIENT_VERIFIED_INPUT"
    INSUFFICIENT_CROSS_SECTION_GEOMETRY = "INSUFFICIENT_CROSS_SECTION_GEOMETRY"


class BreachLocation(BaseModel):
    """Spatial coordinate and structural placement of dam breach."""

    x_projected_epsg32643: float = Field(..., description="Easting in EPSG:32643 (UTM Zone 43N metres)")
    y_projected_epsg32643: float = Field(..., description="Northing in EPSG:32643 (UTM Zone 43N metres)")
    latitude_wgs84: float = Field(..., description="Latitude WGS84")
    longitude_wgs84: float = Field(..., description="Longitude WGS84")
    structural_component: str = Field(..., description="Target structural component (e.g. Left Earthen Flank)")
    selection_method: str = Field(..., description="Geometric derivation from composite structure axis")
    distance_from_metadata_dam_m: float
    verification_level: str


class BreachGeometry(BaseModel):
    """Physical dimensions of trapezoidal breach opening."""

    average_breach_width_m: Optional[float] = Field(None, description="Average breach width B_avg in metres, null if insufficient geometry")
    top_breach_width_m: Optional[float] = Field(None, description="Top breach width in metres")
    bottom_breach_width_m: Optional[float] = Field(None, description="Bottom breach width in metres")
    breach_height_m: float = Field(..., description="Breach height h_b in metres")
    side_slope_z: float = Field(..., description="Breach side slope z (1V:zH)")
    invert_elevation_m: Optional[float] = Field(None, description="Breach bottom invert elevation in m MSL")
    width_status: str = Field("COMPUTED", description="COMPUTED, INSUFFICIENT_CROSS_SECTION_GEOMETRY, etc.")


class InitialReservoirState(BaseModel):
    """Pre-failure reservoir hydraulic condition."""

    initial_water_level_m_msl: float = Field(..., description="Starting water elevation in m MSL (e.g. FRL 280.42 m)")
    initial_water_level_source: str = "AUTHORITATIVE_VERIFIED"
    total_stored_volume_m3: float = Field(..., description="Total reservoir volume at initial level in m3")
    active_water_volume_m3: float = Field(..., description="Volume considered for empirical breach scaling in m3")
    volume_classification: str = "MODEL_ASSUMPTION_FIRST_ESTIMATE"
    volume_source: str


class BreachParameterEstimate(BaseModel):
    """Single empirical model result."""

    model_name: str
    authors: str
    publication_year: int
    breach_width_m: Optional[float] = None
    width_status: ModelResultStatus
    formation_time_s: Optional[float] = None
    formation_time_hr: Optional[float] = None
    eroded_volume_m3: Optional[float] = None
    side_slope_z: Optional[float] = None
    peak_discharge_m3s: Optional[float] = None
    required_inputs: Dict[str, Any]
    formula_traceability: str
    calibration_range_status: str
    extrapolation_warning: Optional[str] = None
    validity_assessment: str


class BreachScenario(BaseModel):
    """Defensible hypothetical breach scenario."""

    scenario_id: str = Field(..., description="e.g. BHV_BASE, BHV_SENSITIVITY_VTG")
    scenario_name: str
    scenario_type: ScenarioType = ScenarioType.HYPOTHETICAL_ENGINEERING_STRESS_TEST
    historical_status: str = "NON_HISTORICAL_HYPOTHETICAL_TEST"
    breached_component: str
    component_material: str
    initial_reservoir: InitialReservoirState
    failure_mechanism: FailureMechanism
    selected_breach_model: str
    breach_geometry: BreachGeometry
    formation_time_s: float
    observed_inputs: List[str]
    model_derived_inputs: List[str]
    model_assumptions: List[str]
    unverified_inputs: List[str]
    uncertainties: str
    validity: str


class BreachUncertaintyEnvelope(BaseModel):
    """Engineering sensitivity envelope across valid empirical models."""

    parameter: str
    lower_estimate: float
    reference_estimate: float
    upper_estimate: Optional[float] = None
    unit: str
    derivation_method: str = "MODEL_SPREAD_SCENARIOS"


class BreachScenarioSet(BaseModel):
    """Complete container for M3 breach event definition."""

    study_site: str = "Bhavanisagar Dam"
    location: BreachLocation
    scenarios: List[BreachScenario]
    uncertainty_envelopes: List[BreachUncertaintyEnvelope]
    model_evaluations: List[BreachParameterEstimate]
