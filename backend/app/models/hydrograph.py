"""
Breach outflow hydrograph domain models for JalRakshak-HD.
SIH PS 26161 - Milestone M4.

Defines schemas for peak discharge estimates, time-series hydrograph points,
volume-constrained triangular screening hydrographs, and validation metrics.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HydrographClassification(str, Enum):
    """Classification of generated hydrograph."""

    SCREENING_HYDROGRAPH = "SCREENING_HYDROGRAPH"
    OBSERVED_HYDROGRAPH = "OBSERVED_HYDROGRAPH"
    LEVEL_POOL_ROUTED_HYDROGRAPH = "LEVEL_POOL_ROUTED_HYDROGRAPH"


class HydrographShape(str, Enum):
    """Geometric shape of the screening hydrograph."""

    VOLUME_CONSTRAINED_TRIANGULAR = "VOLUME_CONSTRAINED_TRIANGULAR"
    TRAPEZOIDAL = "TRAPEZOIDAL"
    PARABOLIC = "PARABOLIC"


class PeakDischargeEstimate(BaseModel):
    """Empirical peak outflow regression result."""

    model_name: str
    authors: str
    publication_year: int
    peak_discharge_m3s: float
    required_inputs: Dict[str, Any]
    formula_traceability: str
    calibration_notes: str
    validity_assessment: str


class HydrographPoint(BaseModel):
    """Single discrete time-step point on the breach hydrograph."""

    time_s: float = Field(..., description="Time from breach initiation in seconds")
    time_hr: float = Field(..., description="Time from breach initiation in hours")
    discharge_m3s: float = Field(..., description="Breach outflow discharge in m3/s")
    cumulative_volume_m3: float = Field(..., description="Trapezoidally integrated volume up to this timestep in m3")
    normalized_discharge: float = Field(..., description="Discharge divided by Q_peak (0.0 to 1.0)")


class HydrographMetadata(BaseModel):
    """Engineering and hydrologic summary of a generated hydrograph."""

    scenario_id: str
    scenario_name: str
    classification: HydrographClassification = HydrographClassification.SCREENING_HYDROGRAPH
    hydrograph_shape: HydrographShape = HydrographShape.VOLUME_CONSTRAINED_TRIANGULAR
    breach_geometry_model: str
    peak_discharge_model: str
    volume_source: str
    rise_time_source: str
    target_volume_m3: float
    integrated_volume_m3: float
    volume_error_percent: float
    peak_discharge_m3s: float
    rise_time_s: float
    rise_time_hr: float
    recession_time_s: float
    recession_time_hr: float
    total_duration_s: float
    total_duration_hr: float
    mean_discharge_m3s: float
    peak_to_mean_ratio: float
    limitations: str


class HydrographValidation(BaseModel):
    """Quality assurance check results for a generated hydrograph."""

    scenario_id: str
    is_non_negative: bool
    has_single_peak: bool
    is_monotonic_rise: bool
    is_monotonic_recession: bool
    is_final_discharge_zero: bool
    is_volume_conserved: bool
    volume_error_percent: float
    peak_matching_error_percent: float
    rise_time_matching_error_s: float
    overall_status: str


class HydrographScenario(BaseModel):
    """Complete hydrograph package for a single scenario."""

    metadata: HydrographMetadata
    validation: HydrographValidation
    points_count: int
    csv_file_path: str
    boundary_tim_file_path: str


class HydrographScenarioSet(BaseModel):
    """Complete suite of M4 hydrograph scenarios."""

    study_site: str = "Bhavanisagar Dam"
    dam_frl_m_msl: float = 280.42
    timestep_seconds: float = 60.0
    scenarios: List[HydrographScenario]
    peak_model_evaluations: List[PeakDischargeEstimate]
