"""
JalRakshak-HD: Remote Sensing & Earth Observation Data Models
=============================================================
Pydantic schemas for Sentinel-1 SAR, Sentinel-2 optical cross-check,
JRC surface water baseline, CHIRPS rainfall context, and near-real-time
satellite flood monitoring.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OrbitPass(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"
    UNKNOWN = "UNKNOWN"


class PolarizationMode(str, Enum):
    VV_VH = "VV+VH"
    HH_HV = "HH+HV"
    VV = "VV"
    VH = "VH"
    HH = "HH"


class ObservationRole(str, Enum):
    PRE_EVENT = "PRE_EVENT"
    EVENT_PEAK = "EVENT_PEAK"
    POST_EVENT = "POST_EVENT"
    NRT_LATEST = "NRT_LATEST"
    NRT_REFERENCE = "NRT_REFERENCE"


class OpticalCrossCheckStatus(str, Enum):
    VALIDATED = "VALIDATED"
    CLOUD_LIMITED = "CLOUD_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    INCONCLUSIVE = "INCONCLUSIVE"


class ObservationQualityFlag(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class FloodInterpretationConfidence(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"
    INCONCLUSIVE = "INCONCLUSIVE"


class SatelliteScene(BaseModel):
    scene_id: str = Field(..., description="Unique Earth Engine / provider scene identifier")
    satellite: str = Field(..., description="Satellite platform (e.g. Sentinel-1B, Sentinel-1D, Sentinel-2A)")
    instrument: str = Field(..., description="Sensor payload name (e.g. C-SAR, MSI)")
    acquisition_datetime: str = Field(..., description="UTC ISO-8601 acquisition timestamp")
    coverage_percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of analysis AOI covered")
    cloud_fraction: Optional[float] = Field(None, ge=0.0, le=100.0, description="Cloud cover percentage (optical)")


class SARAcquisition(BaseModel):
    scene_id: str
    acquisition_datetime: str
    orbit_pass: OrbitPass
    relative_orbit: int
    platform: str
    instrument_mode: str = "IW"
    polarizations: str = "VV+VH"
    resolution_m: float = 10.0
    role: ObservationRole
    coverage_percent: float


class FloodExtentMetrics(BaseModel):
    observed_total_water_area_km2: float = Field(..., ge=0.0)
    historical_recurrent_water_baseline_km2: float = Field(..., ge=0.0, description="JRC GSW Occurrence >= 50% baseline")
    observed_new_flood_area_km2: float = Field(..., ge=0.0)
    steep_slope_masked_area_km2: float = Field(..., ge=0.0)
    detection_method_primary: str = "BACKSCATTER_CHANGE_DETECTION"
    detection_method_secondary: str = "ABSOLUTE_LOW_BACKSCATTER_SCREENING"
    vv_threshold_db: float
    change_threshold_db: float


class OpticalCrossCheck(BaseModel):
    status: OpticalCrossCheckStatus
    sensor: str = "Sentinel-2 MSI (Harmonized L2A)"
    scene_count: int
    scenes_examined: List[str]
    mean_cloud_cover_percent: float
    mndwi_water_detected: bool = False
    evidence_summary: str


class RainfallContext(BaseModel):
    dataset: str = "UCSB-CHG/CHIRPS/DAILY"
    spatial_resolution_deg: float = 0.05
    event_accumulation_mm: float
    three_day_accumulation_mm: float
    seven_day_accumulation_mm: float
    peak_daily_rainfall_mm: float
    peak_date: str
    classification: str = "REMOTE_SENSING_RAINFALL_CONTEXT"
    interpretation_note: str = "Contextual meteorological forcing only; not dam inflow or calibrated discharge."


class MonitoringQuality(BaseModel):
    observation_quality: ObservationQualityFlag = Field(..., description="Data completeness and SAR geometry quality")
    flood_interpretation_confidence: FloodInterpretationConfidence = Field(
        default=FloodInterpretationConfidence.UNCONFIRMED,
        description="Physical causal attribution confidence (requires independent ground/telemetry confirmation)"
    )
    orbit_consistency: bool
    reference_scene_count: int
    aoi_coverage_percent: float
    terrain_shadow_masked: bool
    baseline_water_masked: bool
    optical_corroborated: bool
    quality_rationale: List[str]


class FloodObservation(BaseModel):
    observation_id: str
    benchmark_classification: str = "HISTORICAL_FLOOD_REMOTE_SENSING_BENCHMARK"
    event_name: str = "AUGUST_2019_BHAVANI_FLOOD_BHAVANISAGAR_INFLOW_EVENT"
    officially_documented_flood_period: str = "2019-08-08 to 2019-08-16"
    sentinel1_analysis_window: str = "2019-07-15 to 2019-08-31"
    sentinel1_event_acquisition_date: str = "2019-08-10 00:39:43 UTC"
    s1_pre_scenes: List[str]
    s1_event_scenes: List[str]
    relative_orbit: int
    orbit_pass: OrbitPass
    metrics: FloodExtentMetrics
    optical_crosscheck: OpticalCrossCheck
    rainfall_context: RainfallContext
    quality: MonitoringQuality


class NRTMonitoringResult(BaseModel):
    execution_timestamp: str
    mode: str = "LATEST_MONITORING_MODE"
    latest_scene_id: str
    latest_acquisition_datetime: str
    observation_age_hours: float
    days_since_acquisition: float
    reference_scenes_used: List[str]
    relative_orbit: int
    orbit_pass: OrbitPass
    candidate_new_water_detected_km2: float
    latest_status: str
    cause: str = "UNVERIFIED"
    observation_quality: ObservationQualityFlag
    flood_interpretation_confidence: FloodInterpretationConfidence = FloodInterpretationConfidence.UNCONFIRMED
    quality_details: MonitoringQuality
    output_tif: str
    output_gpkg: str
