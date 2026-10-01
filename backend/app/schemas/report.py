from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ImpactMetrics(BaseModel):
    inundated_area_km2: float
    worldpop_exposed: float
    ghsl_exposed: float
    buildings_exposed: int
    roads_exposed_km: float
    bridges_exposed: int
    total_bridges: int = 20
    critical_facilities_exposed: int
    total_critical_facilities: int = 13
    highest_hazard_reached: str

class BuildingVulnerability(BaseModel):
    h1_h2_low_medium: int
    h3_h4_high: int
    h5_high_structural_vulnerability: int
    h6_vulnerable_to_structural_failure: int
    total_exposed_buildings: int
    classification_standard: str = "USACE / Australian ARR / CWC Hazard Categorization"
    damage_claim_disclaimer: str

class ArrivalWindowStats(BaseModel):
    inundated_area_km2: float
    worldpop_exposed: float
    ghsl_exposed: float
    buildings_exposed: int
    roads_exposed_km: float
    bridges_count: int
    critical_facilities_count: int

class EvacuationScreening(BaseModel):
    disclaimer: str
    arrival_windows: Dict[str, ArrivalWindowStats]

class Next60MinutesWindow(BaseModel):
    additional_inundated_area_km2: float
    additional_worldpop: float
    additional_ghsl: float
    additional_buildings: int
    additional_roads_km: float
    bridges_entering_flood: List[str]
    facilities_entering_flood: List[str]

class ResponseSectorStatus(BaseModel):
    zone_id: str
    sector_name: str
    locality_name: str
    status: str
    earliest_arrival_hr: float
    remaining_lead_time_hr: float
    remaining_lead_time_s: int
    max_hazard_class: str
    current_worldpop_exposed: float
    current_ghsl_exposed: float
    current_buildings_exposed: int
    total_zone_worldpop: float
    total_zone_buildings: int
    priority_rank: int

class AffectedPlaceItem(BaseModel):
    place_name: str
    source: str = "OpenStreetMap Real Geographic Settlements"
    geometry_type: str = "Point"
    classification: str = "POINT_BASED_SETTLEMENT_SCREENING"
    lat: float
    lon: float
    response_zone: str
    affected: bool
    earliest_arrival_hr: Optional[float] = None
    max_depth_m: Optional[float] = None
    max_velocity_mps: Optional[float] = None
    hazard_class: Optional[str] = None
    arrival_priority: str
    population_estimate: Optional[float] = None
    population_method: str = "POINT_SCREENING_POPULATION_UNALLOCATED"
    buildings_exposed: Optional[int] = None
    roads_exposed_km: Optional[float] = None
    bridges_exposed: Optional[int] = None
    facilities_exposed: Optional[int] = None
    notes: Optional[str] = None

class EvacuationPriorityGrouping(BaseModel):
    immediate_under_30_min: List[AffectedPlaceItem]
    high_30_to_60_min: List[AffectedPlaceItem]
    priority_1_to_2_hr: List[AffectedPlaceItem]
    advance_notice_over_2_hr: List[AffectedPlaceItem]
    already_reached: List[AffectedPlaceItem]
    outside_modeled_inundation: List[AffectedPlaceItem]
    disclaimer: str = (
        "Places listed fall within the modeled inundation corridor and are prioritized according to "
        "modeled flood-arrival time and hydraulic hazard. This is a research screening output and not a statutory evacuation order."
    )

class SimulationImpactReport(BaseModel):
    title: str = "JalRakshak-HD Modeled Situation Report"
    site: str
    scenario: str
    classification: str
    frame_index: int
    time_s: int
    time_hr: float
    formatted_time: str
    generation_timestamp: str
    current_impact: ImpactMetrics
    building_vulnerability_screening: BuildingVulnerability
    evacuation_screening: EvacuationScreening
    next_60_minutes_window: Next60MinutesWindow
    response_sectors: List[ResponseSectorStatus]
    affected_places: List[AffectedPlaceItem]
    evacuation_priority_screening: EvacuationPriorityGrouping
    data_sources: List[str]
    limitations: List[str]
    disclaimer: str
    provenance: Dict[str, Any]

class FinalSimulationReport(BaseModel):
    title: str = "JalRakshak-HD Final Hypothetical Breach Screening Report"
    site: str = "Bhavanisagar Dam"
    scenario: str = "BHV_BASE"
    classification: str = "HYPOTHETICAL_ENGINEERING_STRESS_TEST"
    simulation_duration_hours: float = 30.0
    frame_count: int = 181
    generation_timestamp: str
    hydraulics: Dict[str, Any]
    exposure: Dict[str, Any]
    affected_places: List[AffectedPlaceItem]
    evacuation_priority_screening: EvacuationPriorityGrouping
    response_sectors: List[Dict[str, Any]]
    earth_observation_context: Dict[str, Any]
    nearfield_sph_summary: Dict[str, Any]
    cross_solver_analysis: Dict[str, Any]
    limitations: List[str]
    provenance: Dict[str, Any]
    disclaimer: str
