"""
Dam engineering domain models for JalRakshak-HD.
SIH PS 26161 - Milestone M3 (Final Source Reconciliation).

Defines strictly typed engineering schemas for composite dam structural attributes,
conflicting published sources, hydraulic storage capacities, spillway characteristics,
and verification lineage.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EngineeringVerificationLevel(str, Enum):
    """Hierarchical scientific verification levels."""

    AUTHORITATIVE_VERIFIED = "AUTHORITATIVE_VERIFIED"
    SECONDARY_VERIFIED = "SECONDARY_VERIFIED"
    REMOTE_SENSING_DERIVED = "REMOTE_SENSING_DERIVED"
    DEM_DERIVED = "DEM_DERIVED"
    MODEL_DERIVED = "MODEL_DERIVED"
    MODEL_DERIVED_APPROXIMATION = "MODEL_DERIVED_APPROXIMATION"
    MODEL_ASSUMPTION = "MODEL_ASSUMPTION"
    MODEL_ASSUMPTION_FIRST_ESTIMATE = "MODEL_ASSUMPTION_FIRST_ESTIMATE"
    MODEL_DERIVED_CANDIDATE_LOCATION = "MODEL_DERIVED_CANDIDATE_LOCATION"
    UNVERIFIED = "UNVERIFIED"


class EngineeringValue(BaseModel):
    """Explicitly verified single engineering parameter."""

    value: Optional[float] = Field(..., description="Numeric value, or null if unverified")
    unit: str = Field(..., description="Engineering unit (e.g. m, m3, TMC, MCM, ft, cfs)")
    verification_level: EngineeringVerificationLevel = Field(..., description="Verification classification")
    source: str = Field(..., description="Authoritative citation, agency register, or published model")
    exact_reference: Optional[str] = Field(None, description="Document, table, or page reference")
    definition: str = Field(..., description="Exact engineering datum or physical meaning")
    notes: Optional[str] = None


class Spillway(BaseModel):
    """Spillway structural and discharge gate metadata."""

    spillway_type: str = Field(..., description="e.g. Ogee Masonry Spillway with Radial Crest Gates")
    number_of_gates: Optional[int] = Field(..., description="Number of spillway crest gates (9)")
    gate_dimensions_m: Optional[str] = Field(None, description="Gate width x height in metres (10.97 x 6.10 m)")
    spillway_crest_length_m: Optional[float] = Field(..., description="Net/Gross length of ogee spillway crest (~120.7 m)")
    spillway_crest_level_m: Optional[float] = Field(None, description="Crest elevation in m MSL (274.32 m)")
    design_flood_discharge_cms: Optional[float] = Field(None, description="Maximum design discharge capacity in m3/s (3455.0 m3/s)")
    verification_level: EngineeringVerificationLevel


class StorageSourceRecord(BaseModel):
    """Individual published reservoir storage capacity record."""

    source_name: str
    gross_storage_mcm: float
    live_storage_mcm: float
    definition: str
    verification_level: EngineeringVerificationLevel


class StorageValue(BaseModel):
    """Multi-unit reservoir volumetric storage record."""

    volume_tmc: Optional[float] = Field(..., description="Volume in Thousand Million Cubic Feet")
    volume_mcm: Optional[float] = Field(..., description="Volume in Million Cubic Metres")
    volume_m3: Optional[float] = Field(..., description="Volume in standard SI cubic metres")
    verification_level: EngineeringVerificationLevel
    source: str
    definition: str


class ReservoirEngineering(BaseModel):
    """Reservoir hydraulic levels and capacity parameters."""

    name: str = "Bhavanisagar Reservoir"
    official_frl_m: EngineeringValue
    official_full_depth_ft: EngineeringValue
    official_mwl_m: EngineeringValue
    official_crest_level_m: EngineeringValue
    storage_sources: List[StorageSourceRecord] = Field(default_factory=list)
    preferred_live_storage_for_breach_model: Optional[float] = Field(None, description="Kept null pending physical invert routing")
    active_volume_for_breach_first_estimate_m3: Optional[EngineeringValue] = None
    volume_above_final_breach_invert: Optional[EngineeringValue] = None
    elevation_storage_curve_status: str = Field("UNAVAILABLE", description="AVAILABLE or UNAVAILABLE")
    catchment_area_official_sqkm: Optional[EngineeringValue] = None


class StructuralComponent(BaseModel):
    """Breakdown of composite dam sub-structures."""

    component_name: str = Field(..., description="e.g. Left Earthen Flank, Central Masonry Section")
    component_type: str = Field(..., description="EARTHEN_EMBANKMENT, MASONRY_SECTION, OUTLET_SLUICE")
    material: str = Field(..., description="Zoned Earthfill, Rubble Masonry, etc.")
    length_m: Optional[float] = Field(None, description="Length of this structural segment in metres")
    max_height_m: Optional[float] = Field(None, description="Max structural height of segment in metres")
    breachable_status: str = Field(..., description="BREACHABLE, NON_BREACHABLE_MASSIVE_MASONRY")
    verification_level: EngineeringVerificationLevel
    justification: str


class DamStructure(BaseModel):
    """Composite dam structural definition."""

    official_name: str = "Bhavanisagar Dam"
    alternate_names: List[str]
    dam_type: str = "Composite Earthen Dam with Central Masonry Spillway"
    year_completed: int
    # Source A (NRLD 2019)
    nrld_height_above_lowest_foundation_m: EngineeringValue
    nrld_dam_length_m: EngineeringValue
    # Source B (Technical Rehabilitation Literature)
    technical_project_dam_length_m: EngineeringValue
    masonry_section_length_m: EngineeringValue
    masonry_section_height_from_lowest_foundation_m: EngineeringValue
    # Derived / Assumed
    arithmetic_embankment_length_approx_m: EngineeringValue
    earthen_embankment_reported_height_m: Optional[EngineeringValue] = None
    final_breach_height_hb_m: Optional[EngineeringValue] = None
    spillway: Spillway
    components: List[StructuralComponent]
    breachable_component_name: str
    verification_level: EngineeringVerificationLevel


class DamEngineeringDataset(BaseModel):
    """Complete root engineering dataset for study site."""

    dam: DamStructure
    reservoir: ReservoirEngineering
