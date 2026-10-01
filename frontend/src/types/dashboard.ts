// ============================================================
// JalRakshak-HD M10 Dashboard — TypeScript Types
// ============================================================

export type DashboardMode = 'simulation' | 'hadr' | 'sph' | 'eo';

export interface SiteItem {
  site_id: string;
  display_name: string;
  enabled: boolean;
  state?: string;
  river?: string;
  status?: string;
}

export interface SiteCapabilityResponse {
  site_id: string;
  display_name: string;
  has_production_simulation: boolean;
  capability_matrix: Record<string, string>;
}

export interface ProjectMeta {
  project: string;
  milestone: string;
  scenario: string;
  classification: string;
  scenario_note: string;
  dam: string;
  river: string;
  study_area_km: number;
  coordinate_system: string;
  backend_status: string;
}

// ─── Simulation ────────────────────────────────────────────
export interface SimulationMeta {
  model: string;
  scenario: string;
  classification: string;
  domain_area_km2?: number;
  max_inundated_area_km2?: number;
  solver_max_depth_m?: number;
  p95_depth_m?: number;
  solver_max_velocity_mps?: number;
  p95_velocity_mps?: number;
  total_frames: number;
  duration_hours: number;
  timestep_hours: number;
  frame_rate_s: number;
  bounds_wgs84: [[number, number], [number, number]];
  peak_depth_m: number;
  peak_velocity_mps: number;
  breach_start_hour: number;
}

export interface SimulationFrame {
  frame_index: number;
  frame_url: string;
  time_hours: number;
  label: string;
}

// ─── HADR Exposure ─────────────────────────────────────────
export interface HazardClass {
  code: string;
  description: string;
  area_km2: number;
  area_pct: number;
  worldpop: number;
  ghsl: number;
  buildings: number;
}

export interface HADRSummary {
  site_id?: string;
  total_inundated_area_km2: number;
  severe_h3h6_area_km2: number;
  severe_hazard_h3_h6_area_km2?: number;
  severe_h3h6_pct: number;
  extreme_h5h6_area_km2?: number;
  extreme_hazard_h5_h6_area_km2?: number;
  max_depth_m?: number;
  max_velocity_mps?: number;
  worldpop_total: number;
  worldpop_exposed?: number;
  worldpop_2020?: number;
  ghsl_total: number;
  ghsl_exposed?: number;
  ghsl_2025?: number;
  buildings_total: number;
  buildings_exposed?: number;
  h5_h6_buildings_total?: number;
  h5_h6_buildings_exposed?: number;
  h5_h6_buildings?: number;
  roads_km: number;
  roads_exposed_km?: number;
  h3_h6_roads_km?: number;
  bridges_total?: number;
  bridges_exposed_count?: number;
  bridges?: number;
  critical_facilities_total?: number;
  critical_facilities_count?: number;
  critical_facilities?: number;
  h3_h6_area_km2?: number;
  cropland_km2?: number;
  builtup_km2?: number;
  hazard_classes?: HazardClass[];
  hazard_areas_km2?: Record<string, number>;
}

export interface ResponseZone {
  zone_id: string;
  zone_name: string;
  name?: string;
  locality?: string;
  priority: string;
  priority_rank?: number;
  rank?: number;
  worldpop: number;
  worldpop_exposure?: number;
  ghsl: number;
  ghsl_exposure?: number;
  buildings: number;
  buildings_count?: number;
  h5_h6_buildings?: number;
  h5_h6_buildings_count?: number;
  roads_km: number;
  roads_exposed_km?: number;
  area_km2: number;
  critical_facilities?: number;
  critical_facilities_count?: number;
  dominant_hazard: string;
  max_hazard?: string;
  earliest_arrival?: string;
  earliest_arrival_hr?: number;
  earliest_arrival_min?: number;
}

// ─── SPH Near-Field ─────────────────────────────────────────
export interface SPHGauge {
  gauge_id: string;
  name: string;
  distance_m: number;
  peak_depth_m: number;
  peak_velocity_mps: number;
  arrival_time_s: number;
  max_discharge_m3s: number;
}

export interface SPHSummary {
  model_classification?: string;
  coupling_status?: string;
  forcing_method?: string;
  model: string;
  scenario: string;
  gauges: SPHGauge[];
  breach_width_m: number;
  breach_depth_m: number;
  peak_outflow_m3s: number;
  initial_fluid_particles?: number;
  boundary_particles?: number;
  total_particles?: number;
  max_depth_m?: number;
  p95_depth_m?: number;
  max_velocity_mps?: number;
  p95_velocity_mps?: number;
  front_position_at_600s_m?: number;
  depth_trend?: string;
  velocity_trend?: string;
  recommended_future_handoff_candidate?: string;
  direct_coupling_ready?: boolean;
  overall_coupling_readiness?: string;
}

// ─── Earth Observation ─────────────────────────────────────
export interface EOScene {
  scene_id: string;
  platform: string;
  date: string;
  orbit_pass: string;
  absolute_orbit?: number;
  relative_orbit: number;
  mode: string;
  resolution_m: number;
  flood_status: string;
}

export interface EOSummary {
  historical_event: string;
  historical_date: string;
  historical_flood_area_km2: number;
  historical_flood_vector_km2?: number;
  historical_platform?: string;
  historical_scene_id?: string;
  historical_method: string;
  delta_vv_threshold_db: number;
  thresholds: Record<string, { value: number; derivation: string; class: string }>;
  latest_scene: EOScene | null;
  monitoring_status: string;
}

// ─── Point Analysis ─────────────────────────────────────────
export interface PointAnalysis {
  location?: { lat: number; lon: number };
  lat?: number;
  lng?: number;
  in_study_area?: boolean;
  max_depth_m?: number | null;
  max_velocity_mps?: number | null;
  arrival_time_hr?: number | null;
  hazard_class?: string | null;
  hazard_description?: string | null;
  response_zone?: string | null;
  response_zone_rank?: number | null;
  historical_flood_detected?: boolean;
  latest_candidate_water_change?: boolean;
  status_message?: string;
  depth_m?: number | null;
  velocity_mps?: number | null;
  arrival_hr?: number | null;
}

// ─── Layer config ──────────────────────────────────────────
export interface RasterLayer {
  id: string;
  label: string;
  url: string;
  bounds: [[number, number], [number, number]];
  unit: string;
  opacity: number;
  visible: boolean;
}

export interface VectorLayer {
  id: string;
  label: string;
  url: string;
  visible: boolean;
  color: string;
  weight?: number;
  fillOpacity?: number;
}

export interface LayerState {
  rasters: Record<string, boolean>;
  vectors: Record<string, boolean>;
}

// ─── Simulation Timestep Impact & Reports ──────────────────
export interface TimestepImpactMetrics {
  inundated_area_km2: number;
  worldpop_exposed: number;
  ghsl_exposed: number;
  buildings_exposed: number;
  roads_exposed_km: number;
  bridges_exposed: number;
  total_bridges: number;
  critical_facilities_exposed: number;
  total_critical_facilities: number;
  highest_hazard_reached: string;
}

export interface BuildingVulnerabilityScreening {
  h1_h2_low_medium: number;
  h3_h4_high: number;
  h5_high_structural_vulnerability: number;
  h6_vulnerable_to_structural_failure: number;
  total_exposed_buildings: number;
  classification_standard: string;
  damage_claim_disclaimer: string;
}

export interface ArrivalWindowStats {
  inundated_area_km2: number;
  worldpop_exposed: number;
  ghsl_exposed: number;
  buildings_exposed: number;
  roads_exposed_km: number;
  bridges_count: number;
  critical_facilities_count: number;
}

export interface EvacuationScreeningData {
  disclaimer: string;
  arrival_windows: {
    already_reached: ArrivalWindowStats;
    next_30_minutes: ArrivalWindowStats;
    thirty_to_sixty_minutes: ArrivalWindowStats;
    one_to_two_hours: ArrivalWindowStats;
    greater_than_two_hours?: ArrivalWindowStats;
  };
}

export interface Next60MinutesWindowData {
  additional_inundated_area_km2: number;
  additional_worldpop: number;
  additional_ghsl: number;
  additional_buildings: number;
  additional_roads_km: number;
  bridges_entering_flood: string[];
  facilities_entering_flood: string[];
}

export interface ResponseSectorStatusData {
  zone_id: string;
  sector_name: string;
  locality_name: string;
  status: string;
  earliest_arrival_hr: number;
  remaining_lead_time_hr: number;
  remaining_lead_time_s: number;
  max_hazard_class: string;
  current_worldpop_exposed: number;
  current_ghsl_exposed: number;
  current_buildings_exposed: number;
  total_zone_worldpop: number;
  total_zone_buildings: number;
  priority_rank: number;
}

export interface AffectedPlaceItem {
  place_name: string;
  source: string;
  geometry_type: string;
  classification: string;
  lat: number;
  lon: number;
  response_zone: string;
  affected: boolean;
  earliest_arrival_hr: number | null;
  max_depth_m: number | null;
  max_velocity_mps: number | null;
  hazard_class: string | null;
  arrival_priority: string;
  population_estimate: number | null;
  population_method: string;
  buildings_exposed: number | null;
  roads_exposed_km: number | null;
  bridges_exposed: number | null;
  facilities_exposed: number | null;
  notes: string | null;
}

export interface EvacuationPriorityGrouping {
  immediate_under_30_min: AffectedPlaceItem[];
  high_30_to_60_min: AffectedPlaceItem[];
  priority_1_to_2_hr: AffectedPlaceItem[];
  advance_notice_over_2_hr: AffectedPlaceItem[];
  already_reached: AffectedPlaceItem[];
  outside_modeled_inundation: AffectedPlaceItem[];
  disclaimer: string;
}

export interface TimestepImpactReport {
  title: string;
  site: string;
  scenario: string;
  classification: string;
  frame_index: number;
  time_s: number;
  time_hr: number;
  formatted_time: string;
  generation_timestamp: string;
  current_impact: TimestepImpactMetrics;
  building_vulnerability_screening: BuildingVulnerabilityScreening;
  evacuation_screening: EvacuationScreeningData;
  next_60_minutes_window: Next60MinutesWindowData;
  response_sectors: ResponseSectorStatusData[];
  affected_places?: AffectedPlaceItem[];
  evacuation_priority_screening?: EvacuationPriorityGrouping;
  data_sources: string[];
  limitations: string[];
  disclaimer: string;
  provenance: Record<string, any>;
}

export interface FinalSimulationReportData {
  title: string;
  site: string;
  scenario: string;
  classification: string;
  simulation_duration_hours: number;
  frame_count: number;
  generation_timestamp: string;
  hydraulics: Record<string, any>;
  exposure: Record<string, any>;
  affected_places?: AffectedPlaceItem[];
  evacuation_priority_screening?: EvacuationPriorityGrouping;
  response_sectors: any[];
  earth_observation_context: Record<string, any>;
  nearfield_sph_summary: Record<string, any>;
  limitations: string[];
  provenance: Record<string, any>;
  disclaimer: string;
}

