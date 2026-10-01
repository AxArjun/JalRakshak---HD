"""
JalRakshak-HD: Pydantic Data Models for HADR Consequence & Exposure Analysis (Milestone M8)
========================================================================================
Defines strongly-typed schemas for:
- Hazard classification breakdowns (CWC H1–H6)
- Population exposure overlays (WorldPop 2020 primary & GHSL 2025 cross-check)
- Building footprint exposure (Google Open Buildings v3)
- Land cover consequences (ESA WorldCover 2021)
- Transportation and critical infrastructure exposure (OSM)
- Deterministic HADR response priority zones (OPERATIONAL_SCREENING_PRIORITY_ORDER)
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HazardClassBreakdown(BaseModel):
    hazard_code: int
    name: str
    description: str
    vulnerability: str
    face_count: int
    area_km2: float
    area_percentage_inundated: float


class HazardSeveritySummary(BaseModel):
    standard: str = "CWC_AIDR_GUIDELINE_7_3_SMITH_2014"
    classification_method: str = "TIME_SYNCHRONOUS_STEPWISE_EVALUATION"
    total_domain_faces: int
    total_inundated_faces: int
    total_inundated_area_km2: float
    severe_hazard_h3_h6_area_km2: float
    severe_hazard_h3_h6_pct: float
    extreme_hazard_h5_h6_area_km2: float
    hazard_breakdown: Dict[str, HazardClassBreakdown]
    max_observed_dv_product_m2ps: float
    max_observed_depth_m: float
    max_observed_velocity_mps: float


class PopulationArrivalContext(BaseModel):
    time_window_hr: str
    arrival_window_min: int
    population_exposed_worldpop: float
    population_exposed_ghsl: float
    cumulative_worldpop: float
    cumulative_pct: float


class PopulationExposureSummary(BaseModel):
    primary_dataset: str = "WorldPop 2020 UN-Adjusted 100m (sum-conserved reprojected)"
    crosscheck_dataset: str = "GHSL GHS-POP R2023A 100m (sum-conserved reprojected)"
    worldpop_total_inundated: float
    worldpop_severe_h3_h6: float
    worldpop_extreme_h5_h6: float
    worldpop_by_hazard_class: Dict[str, float]
    ghsl_total_inundated: float
    ghsl_severe_h3_h6: float
    ghsl_extreme_h5_h6: float
    ghsl_by_hazard_class: Dict[str, float]
    population_crosscheck_dataset_spread: float
    population_crosscheck_ratio_ghsl_to_worldpop: float
    population_arrival_context: List[PopulationArrivalContext]
    potential_loss_of_life_model: str = "NOT_IMPLEMENTED"
    potential_loss_of_life_status: str = "SCREENING_EXPOSURE_ONLY_NO_CASUALTY_ESTIMATION"


class BuildingExposureSummary(BaseModel):
    dataset: str = "Google Open Buildings v3 (confidence >= 0.75)"
    total_buildings_inundated: int
    total_footprint_area_m2: float
    severe_h3_h6_buildings: int
    h5_h6_structural_damage_exposure: int
    buildings_by_hazard_class: Dict[str, int]
    building_damage_state: str = "EXPOSURE_ONLY_NO_FRAGILITY_CURVES"
    damage_classification_note: str = "Buildings in H5/H6 classified as H5_H6_STRUCTURAL_DAMAGE_EXPOSURE, NOT assumed destroyed"


class LandCoverExposureSummary(BaseModel):
    dataset: str = "ESA WorldCover 2021 v200 (10m categorical, nearest-neighbor reprojected)"
    cropland_class_40_inundated_km2: float
    cropland_severe_h3_h6_km2: float
    cropland_by_hazard_class_km2: Dict[str, float]
    builtup_class_50_inundated_km2: float
    builtup_severe_h3_h6_km2: float
    builtup_by_hazard_class_km2: Dict[str, float]
    other_classes_inundated_km2: float
    cropland_loss_model: str = "NOT_IMPLEMENTED"
    monetary_damage_status: str = "NOT_IMPLEMENTED_IN_M8"


class RoadExposureSummary(BaseModel):
    dataset: str = "OpenStreetMap (OSM) Overpass API"
    total_roads_inundated_km: float
    severe_h3_h6_roads_km: float
    roads_by_hazard_class_km: Dict[str, float]
    roads_by_highway_type_km: Dict[str, float]
    road_status_classification: str = "HYDRAULICALLY_EXPOSED_ROAD_SEGMENT"
    road_status_note: str = "Exposed road segments are NOT assumed closed/washed out"


class BridgeExposureSummary(BaseModel):
    dataset: str = "OpenStreetMap (OSM) Bridge Attributes & River Intersections"
    total_bridges_in_study_area: int
    bridges_hydraulically_exposed: int
    bridges_severe_h3_h6: int
    bridge_screening_classification: str = "BRIDGE_HYDRAULIC_EXPOSURE_SCREENING"
    bridge_screening_note: str = "Bridges NOT assumed collapsed; detailed structural/scour rating requires bridge deck elevation surveys"


class CriticalFacilityExposureSummary(BaseModel):
    dataset: str = "OpenStreetMap (OSM) Healthcare, Education, Emergency & Government"
    total_facilities_inundated: int
    severe_h3_h6_facilities: int
    facilities_by_category: Dict[str, int]
    facilities_by_hazard_class: Dict[str, int]
    facilities_details: List[Dict[str, str]]


class HADRResponseZone(BaseModel):
    zone_id: str
    locality_name: str
    locality_relation: str # "inside", "intersects", "nearest_distance_m"
    distance_to_locality_m: float
    max_hazard_class: str
    zone_area_km2: float
    population_worldpop: float
    population_ghsl: float
    building_count: int
    h5_h6_buildings: int
    road_length_km: float
    earliest_arrival_hr: float
    h3_arrival_hr: float
    h5_arrival_hr: float
    priority_rank: int
    priority_sort_rule: str = "OPERATIONAL_SCREENING_PRIORITY_ORDER"


class HADRConsequenceReport(BaseModel):
    milestone: str = "M8"
    analysis_type: str = "SCREENING_HADR_CONSEQUENCE_ANALYSIS"
    hydraulic_source_model: str = "2D_DFLOWFM_SCREENING_INUNDATION_MODEL"
    study_area: str = "Bhavanisagar Dam Downstream Reach (51.73 km), Tamil Nadu, India"
    coordinate_system: str = "EPSG:32643 (WGS 84 / UTM Zone 43N)"
    hazard_severity: HazardSeveritySummary
    population_exposure: PopulationExposureSummary
    building_exposure: BuildingExposureSummary
    landcover_exposure: LandCoverExposureSummary
    road_exposure: RoadExposureSummary
    bridge_exposure: BridgeExposureSummary
    critical_facility_exposure: CriticalFacilityExposureSummary
    response_zones: List[HADRResponseZone]
    priority_delineation_methodology: str = "OPERATIONAL_SCREENING_PRIORITY_ORDER (sorted by max hazard H6>H5>H4>H3, then earlier arrival, then larger population; no arbitrary weights)"
    scientific_limitations: List[str]
