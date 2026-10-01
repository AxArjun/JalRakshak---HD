// ============================================================
// JalRakshak-HD M10 — API Service Layer
// All data from validated M0–M9 outputs via FastAPI backend
// ============================================================

import type {
  ProjectMeta, SimulationMeta,
  HADRSummary, ResponseZone,
  SPHSummary, EOSummary, PointAnalysis
} from '../types/dashboard';

const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`API ${path} → ${r.status}`);
  return r.json();
}

// ─── Project / Health / Multi-Site ─────────────────────────
export async function fetchProjectMeta(): Promise<ProjectMeta> {
  return get<ProjectMeta>('/project/meta');
}

export async function fetchSites(): Promise<{ active_site: string; total_sites: number; sites: any[] }> {
  return get<{ active_site: string; total_sites: number; sites: any[] }>('/sites');
}

export async function fetchSiteDetails(siteId: string): Promise<any> {
  return get<any>(`/sites/${siteId}`);
}

export async function fetchSiteCapability(siteId: string): Promise<any> {
  return get<any>(`/sites/${siteId}/capability-matrix`);
}

export async function fetchHealth(): Promise<{ status: string }> {
  return get('/health');
}

// ─── Simulation ────────────────────────────────────────────
export async function fetchSimulationMeta(): Promise<SimulationMeta> {
  return get<SimulationMeta>('/simulation/meta');
}

export function getFrameUrl(frameIndex: number): string {
  return `/api/simulation/frame/${frameIndex}`;
}

export function getStaticFrameUrl(frameIndex: number): string {
  const padded = String(frameIndex).padStart(3, '0');
  return `/api/tiles/simulation_frames/frame_${padded}.png`;
}

// ─── HADR / Exposure ───────────────────────────────────────
export async function fetchHADRSummary(siteId?: string): Promise<HADRSummary> {
  if (siteId && siteId !== 'bhavanisagar') {
    throw new Error('NOT_RUN');
  }
  return get<HADRSummary>('/hadr/summary');
}

export async function fetchResponseZones(siteId?: string): Promise<ResponseZone[]> {
  if (siteId && siteId !== 'bhavanisagar') {
    return [];
  }
  const data = await get<any>('/hadr/zones');
  return Array.isArray(data) ? data : (data?.zones ?? []);
}

// ─── SPH Near-Field ─────────────────────────────────────────
export async function fetchSPHSummary(): Promise<SPHSummary> {
  return get<SPHSummary>('/sph/summary');
}

// ─── Earth Observation ─────────────────────────────────────
export async function fetchEOSummary(): Promise<EOSummary> {
  return get<EOSummary>('/remote-sensing/summary');
}

// ─── GIS Tiles ─────────────────────────────────────────────
export function getOverlayUrl(name: string): string {
  return `/api/tiles/overlays/${name}.png`;
}

export function getGeoJsonUrl(name: string): string {
  return `/api/tiles/geojson/${name}.geojson`;
}

// ─── Point Query ────────────────────────────────────────────
export async function queryPoint(lat: number, lng: number): Promise<PointAnalysis> {
  return get<PointAnalysis>(`/gis/query-point?lat=${lat}&lng=${lng}`);
}

// ─── Reports & Timestep Impact ──────────────────────────────
export async function fetchImpactReport(frameIndex: number): Promise<any> {
  return get<any>(`/reports/impact/${frameIndex}`);
}

export async function fetchFinalReport(): Promise<any> {
  return get<any>('/reports/final');
}

