"""Solver coupling data models for JalRakshak-HD (Milestone M7).

Defines rigorous data structures and transfer contracts for future hybrid
coupling between near-field (DualSPHysics) and long-reach (D-Flow FM)
hydrodynamic solvers. Follows SIH PS 26161 specifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CouplingRole(str, Enum):
    """Scientific role of solver in hybrid architecture."""

    NEAR_FIELD_DIAGNOSTICS = "near-field high-gradient diagnostics"
    LONG_REACH_ROUTING = "long-reach floodplain inundation routing"


class CouplingStatus(str, Enum):
    """Operational coupling readiness state."""

    DESIGN_ONLY = "DESIGN_ONLY"
    NOT_READY = "NOT_READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    ACTIVE = "ACTIVE"


class TransferMethod(str, Enum):
    """Method applied for lateral flow conversion."""

    UNIT_WIDTH_RAW = "UNIT_WIDTH_RAW"
    INTEGRATED_BATHYMETRY = "INTEGRATED_BATHYMETRY"
    UNRESOLVED = "UNRESOLVED"


class CouplingStation(BaseModel):
    """Geospatial definition of a hybrid handoff station."""

    station_id: str = Field(..., description="Unique alphanumeric station identifier (e.g. G_500m)")
    chainage_m: float = Field(..., ge=0.0, description="Downstream distance from breach origin along river centerline in meters")
    easting: float = Field(..., description="Projected Easting coordinate in EPSG:32643 (UTM Zone 43N)")
    northing: float = Field(..., description="Projected Northing coordinate in EPSG:32643 (UTM Zone 43N)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS 84 geographic longitude in decimal degrees")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS 84 geographic latitude in decimal degrees")
    bed_elevation_m: float = Field(..., description="Local DEM bed elevation at station in meters above MSL")
    mesh_face_id: Optional[int] = Field(None, description="Corresponding D-Flow FM 2D computational mesh face index")
    channel_width_m: Optional[float] = Field(None, gt=0.0, description="Physical valley cross-section width at this chainage in meters")


class DischargeTransfer(BaseModel):
    """Discharge transfer packet between near-field and long-reach domains."""

    station_id: str = Field(..., description="Target coupling station identifier")
    timestamp_s: float = Field(..., ge=0.0, description="Simulation timestamp in seconds")
    unit_discharge_m2ps: float = Field(..., ge=0.0, description="DualSPHysics 2D unit-width discharge (q = u * h) in m2/s")
    effective_flow_width_m: Optional[float] = Field(None, gt=0.0, description="Defensible physical or hydraulic flow width in meters")
    total_discharge_m3ps: Optional[float] = Field(None, ge=0.0, description="Calculated total discharge in m3/s if flow width is resolved")
    transfer_method: TransferMethod = Field(..., description="Discharge scaling method applied")
    direct_coupling_ready: bool = Field(..., description="Flag indicating whether discharge can be directly ingested by D-Flow FM")
    blocker_reason: Optional[str] = Field(None, description="Scientific blocker explanation if direct coupling is not ready")


class DepthTransfer(BaseModel):
    """Water depth and free-surface boundary packet."""

    station_id: str = Field(..., description="Target coupling station identifier")
    timestamp_s: float = Field(..., ge=0.0, description="Simulation timestamp in seconds")
    water_depth_m: float = Field(..., ge=0.0, description="Flow depth normal to bed or vertical in meters")
    water_level_m_msl: float = Field(..., description="Absolute water surface elevation in meters above MSL")
    bed_elevation_m: float = Field(..., description="Local bed elevation in meters above MSL")
    froude_number: Optional[float] = Field(None, ge=0.0, description="Dimensionless Froude number Fr = U / sqrt(g*h)")
    is_hydrostatic_valid: bool = Field(..., description="Whether vertical acceleration is sufficiently small for hydrostatic SWE validity")


class VelocityTransfer(BaseModel):
    """Flow velocity vector transfer packet."""

    station_id: str = Field(..., description="Target coupling station identifier")
    timestamp_s: float = Field(..., ge=0.0, description="Simulation timestamp in seconds")
    velocity_magnitude_mps: float = Field(..., ge=0.0, description="Scalar flow velocity magnitude in m/s")
    u_longitudinal_mps: float = Field(..., description="Longitudinal flow velocity component along reach centerline in m/s")
    v_lateral_mps: Optional[float] = Field(None, description="Transverse velocity component in m/s")
    w_vertical_mps: Optional[float] = Field(None, description="Vertical velocity component in m/s")
    flow_direction_deg: float = Field(..., ge=0.0, le=360.0, description="Azimuthal direction of flow in degrees from True North")


class TimeSeriesTransfer(BaseModel):
    """Multi-step time series transfer buffer for dynamic boundary coupling."""

    station_id: str = Field(..., description="Target coupling station identifier")
    start_time_s: float = Field(..., ge=0.0, description="Start timestamp of transfer window in seconds")
    end_time_s: float = Field(..., ge=0.0, description="End timestamp of transfer window in seconds")
    time_step_s: float = Field(..., gt=0.0, description="Uniform sampling time step in seconds")
    timestamps_s: List[float] = Field(..., description="Monotonically increasing timestamp array in seconds")
    depth_series_m: List[float] = Field(..., description="Water depth values in meters")
    velocity_series_mps: List[float] = Field(..., description="Velocity magnitude values in m/s")
    discharge_series_m3ps: Optional[List[float]] = Field(None, description="Volumetric discharge values in m3/s")
    record_count: int = Field(..., ge=0, description="Number of samples in buffer")


class CouplingMetadata(BaseModel):
    """Provenance and architectural metadata for cross-solver hybrid linkage."""

    source_solver: str = Field(..., description="Near-field source solver name (e.g. DualSPHysics v5.4)")
    target_solver: str = Field(..., description="Long-reach target solver name (e.g. D-Flow FM)")
    source_role: CouplingRole = Field(..., description="Scientific role of near-field solver")
    target_role: CouplingRole = Field(..., description="Scientific role of long-reach solver")
    coupling_status: CouplingStatus = Field(..., description="Architectural status of coupling interface")
    handoff_chainage_m: float = Field(..., ge=0.0, description="Designated handoff station chainage in meters")
    crs: str = Field(..., description="Coordinate Reference System identifier (EPSG:32643)")
    direct_coupling_activated: bool = Field(..., description="Flag indicating if live numerical feedback is executing")
    direct_discharge_coupling_ready: bool = Field(..., description="Flag indicating scientific validity of direct flow transfer")
    scaling_blocker: Optional[str] = Field(None, description="Scientific justification if direct discharge coupling is not ready")
    temporal_alignment_note: str = Field(..., description="Explicit documentation of non-synchronous time references")
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Metadata timestamp in UTC")
