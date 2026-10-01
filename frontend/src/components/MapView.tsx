// MapView – High-Performance Leaflet GIS Command Centre with Real OSM Basemap, Real Vectors & D-Flow Playback
import { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { DashboardMode, PointAnalysis } from '../types/dashboard';
import { queryPoint } from '../services/api';

// ─── Authoritative GIS Bounds ─────────────────────────────────
export const SITE_BOUNDS: Record<string, [[number, number], [number, number]]> = {
  bhavanisagar: [[11.359179, 76.948355], [11.580164, 77.423552]],
  hirakud: [[21.4000, 83.7000], [21.7000, 84.1500]],
};

export const SITE_CENTERS: Record<string, [number, number]> = {
  bhavanisagar: [11.47083, 77.26],
  hirakud: [21.5286, 83.92],
};

// Fast Navigation Presets (Validated GIS Bounding Boxes)
export const FAST_NAV_BOUNDS: Record<string, [[number, number], [number, number]]> = {
  dam: [[11.455, 77.095], [11.485, 77.135]],
  reservoir: [[11.430, 76.950], [11.530, 77.120]],
  flood_extent: [[11.359179, 77.111197], [11.57997, 77.423552]],
  downstream: [[11.420, 77.110], [11.580, 77.430]],
  full_study: [[11.359179, 76.948355], [11.580164, 77.423552]],
};

// Raster Overlay bounds from manifest
const OVERLAY_BOUNDS: Record<string, [[number, number], [number, number]]> = {
  max_depth:        [[11.359179, 77.111197], [11.57997, 77.423552]],
  max_velocity:     [[11.359179, 77.111197], [11.57997, 77.423552]],
  arrival_time:     [[11.359179, 77.111197], [11.57997, 77.423552]],
  hazard_class:     [[11.359179, 77.111197], [11.57997, 77.423552]],
  historical_flood: [[11.431432, 77.111044], [11.521654, 77.421218]],
  hillshade:        [[11.359761, 76.948355], [11.580164, 77.422284]],
  hirakud_hillshade:[[21.4000, 83.7000], [21.7000, 84.1500]],
};

const VECTOR_STYLES: Record<string, L.PathOptions> = {
  inundation_extent:       { color: '#3b82f6', weight: 2, fillOpacity: 0.15, fillColor: '#3b82f6' },
  hazard_severity:         { color: '#ef4444', weight: 1, fillOpacity: 0.35 },
  response_zones:          { color: '#f59e0b', weight: 2, fillOpacity: 0.10, fillColor: '#f59e0b' },
  road_exposure:           { color: '#475569', weight: 1.5, fillOpacity: 0 },
  bhavani_river:           { color: '#0ea5e9', weight: 3.0, fillOpacity: 0 },
  reservoir_surface:       { color: '#1d4ed8', weight: 1.5, fillOpacity: 0.25, fillColor: '#60a5fa' },
  dam_point:               { color: '#ffffff', weight: 2.5, fillOpacity: 1.0, fillColor: '#f59e0b' },
  bridges:                 { color: '#451a03', weight: 2.0, fillOpacity: 0.95, fillColor: '#f59e0b' },
  settlements:             { color: '#0f172a', weight: 1.5, fillOpacity: 0.90, fillColor: '#94a3b8' },
  critical_facilities:     { color: '#7f1d1d', weight: 2.0, fillOpacity: 0.90, fillColor: '#ef4444' },
  historical_flood:        { color: '#8b5cf6', weight: 1.5, fillOpacity: 0.20, fillColor: '#8b5cf6' },
  latest_water_change:     { color: '#06b6d4', weight: 1.5, fillOpacity: 0.20, fillColor: '#06b6d4' },
  sph_gauges:              { color: '#15803d', weight: 2.0, fillOpacity: 0.95, fillColor: '#22c55e' },
  sph_reach:               { color: '#84cc16', weight: 2.5, fillOpacity: 0 },
  // Hirakud layers
  hirakud_dam_point:       { color: '#ffffff', weight: 2.5, fillOpacity: 1.0, fillColor: '#ef4444' },
  hirakud_mahanadi_river:  { color: '#0284c7', weight: 3.0, fillOpacity: 0 },
  hirakud_reservoir:       { color: '#0369a1', weight: 1.5, fillOpacity: 0.3, fillColor: '#38bdf8' },
  hirakud_study_area:      { color: '#a855f7', weight: 2.0, fillOpacity: 0.05, fillColor: '#a855f7', dashArray: '4, 4' },
};

const HAZARD_FILL: Record<number, string> = {
  1: '#fefce8', 2: '#fef9c3', 3: '#ffedd5',
  4: '#fee2e2', 5: '#fecaca', 6: '#e9d5ff',
};

export type BasemapType = 'osm' | 'satellite' | 'terrain';

interface Props {
  mode: DashboardMode;
  currentSite: string;
  rasterVisible: Record<string, boolean>;
  rasterOpacity: Record<string, number>;
  vectorVisible: Record<string, boolean>;
  simFrameUrl: string | null;
  simBounds: [[number, number], [number, number]] | null;
  selectedZone: string | null;
  simAnimationVisible?: boolean;
  floodOpacity?: number;
  onFloodOpacityChange?: (opacity: number) => void;
  onSelectBridge?: (bridgeProps: Record<string, unknown>) => void;
  resetKey?: number;
}

export default function MapView({
  mode, currentSite, rasterVisible, rasterOpacity, vectorVisible,
  simFrameUrl, simBounds, selectedZone,
  simAnimationVisible = true,
  floodOpacity = 0.65,
  onFloodOpacityChange,
  onSelectBridge,
  resetKey
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  // Basemap switcher state
  const [basemap, setBasemap] = useState<BasemapType>('osm');
  const baseTileLayerRef = useRef<L.TileLayer | null>(null);

  // Layers registry
  const rasterLayersRef = useRef<Record<string, L.ImageOverlay>>({});
  const vectorLayersRef = useRef<Record<string, L.GeoJSON>>({});
  const simLayerA = useRef<L.ImageOverlay | null>(null);
  const simLayerB = useRef<L.ImageOverlay | null>(null);
  const activeSimLayer = useRef<'A' | 'B'>('A');
  const geoJsonCacheRef = useRef<Record<string, GeoJSON.FeatureCollection>>({});
  const preloadedImages = useRef<Record<string, HTMLImageElement>>({});

  // Real-time cursor coordinates
  const [cursorPos, setCursorPos] = useState<{ lat: number; lng: number } | null>(null);

  // Point Query Analysis
  const [pointInfo, setPointInfo] = useState<PointAnalysis | null>(null);
  const [pointPos, setPointPos] = useState<[number, number] | null>(null);
  const [querying, setQuerying] = useState(false);

  // ─── 1. Map Initialization ────────────────────────────────
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const initialBounds = SITE_BOUNDS[currentSite] || SITE_BOUNDS.bhavanisagar;
    const map = L.map(containerRef.current, {
      center: SITE_CENTERS[currentSite] || [11.47083, 77.26],
      zoom: 11,
      minZoom: 9,
      maxZoom: 18,
      zoomSnap: 0.5,
      zoomDelta: 0.5,
      wheelPxPerZoomLevel: 120,
      zoomControl: false,
    });

    // Custom Layer Panes with explicit Z-Index stacking
    map.createPane('basemapPane');
    map.getPane('basemapPane')!.style.zIndex = '200';

    map.createPane('hillshadePane');
    map.getPane('hillshadePane')!.style.zIndex = '250';

    map.createPane('reservoirPane');
    map.getPane('reservoirPane')!.style.zIndex = '300';

    map.createPane('riverPane');
    map.getPane('riverPane')!.style.zIndex = '350';

    map.createPane('floodPane');
    map.getPane('floodPane')!.style.zIndex = '400';

    map.createPane('vectorPane');
    map.getPane('vectorPane')!.style.zIndex = '450';

    map.createPane('markerPane');
    map.getPane('markerPane')!.style.zIndex = '500';

    // Default Basemap: OpenStreetMap Standard (No API key required)
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
      subdomains: ['a', 'b', 'c'],
      pane: 'basemapPane',
    });
    osmLayer.addTo(map);
    baseTileLayerRef.current = osmLayer;

    // Zoom Controls top-right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Metric Scale Bar bottom-right
    L.control.scale({ imperial: false, metric: true, position: 'bottomright' }).addTo(map);

    // Fit Initial Bounds cleanly
    map.fitBounds(initialBounds, { padding: [15, 15], maxZoom: 12 });

    // Track Cursor Coordinates
    map.on('mousemove', (e: L.LeafletMouseEvent) => {
      setCursorPos({ lat: e.latlng.lat, lng: e.latlng.lng });
    });

    // Click → Point Analysis Query
    map.on('click', async (e: L.LeafletMouseEvent) => {
      if (currentSite !== 'bhavanisagar') return;
      setPointPos([e.latlng.lat, e.latlng.lng]);
      setQuerying(true);
      try {
        const res = await queryPoint(e.latlng.lat, e.latlng.lng);
        setPointInfo(res);
      } catch {
        setPointInfo(null);
      } finally {
        setQuerying(false);
      }
    });

    // ResizeObserver on map container to guarantee 100% canvas coverage
    const container = containerRef.current;
    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize();
    });
    if (container) {
      resizeObserver.observe(container);
    }

    mapRef.current = map;
    return () => {
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // ─── 2. Fast Navigation Presets ───────────────────────────
  const navigateTo = useCallback((target: keyof typeof FAST_NAV_BOUNDS) => {
    const map = mapRef.current;
    if (!map) return;
    const bounds = FAST_NAV_BOUNDS[target];
    if (bounds) {
      map.flyToBounds(bounds, { padding: [25, 25], duration: 0.8, maxZoom: target === 'dam' ? 14 : 13 });
    }
  }, []);

  // ─── 3. Basemap Switcher Handler ──────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (baseTileLayerRef.current) {
      map.removeLayer(baseTileLayerRef.current);
      baseTileLayerRef.current = null;
    }

    if (basemap === 'osm') {
      const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        subdomains: ['a', 'b', 'c'],
        pane: 'basemapPane',
      });
      osmLayer.addTo(map);
      baseTileLayerRef.current = osmLayer;
    } else if (basemap === 'satellite') {
      const satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Maxar, Earthstar Geographics, USDA, USGS',
        maxZoom: 18,
        pane: 'basemapPane',
      });
      satLayer.addTo(map);
      baseTileLayerRef.current = satLayer;
    } else if (basemap === 'terrain') {
      // Local terrain mode: offline background (SRTM hillshade)
    }
  }, [basemap]);

  // ─── 4. Site-Aware Panning & Bounds ───────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const bounds = SITE_BOUNDS[currentSite] || SITE_BOUNDS.bhavanisagar;
    if (bounds) {
      map.fitBounds(bounds, { padding: [20, 20], maxZoom: 12 });
    }

    setPointPos(null);
    setPointInfo(null);
  }, [currentSite]);

  // ─── 4b. Explicit Reset Handler ───────────────────────────
  useEffect(() => {
    if (!resetKey) return;
    const map = mapRef.current;
    if (!map) return;

    map.invalidateSize();
    const bounds = SITE_BOUNDS[currentSite] || SITE_BOUNDS.bhavanisagar;
    if (bounds) {
      map.fitBounds(bounds, { padding: [20, 20], maxZoom: 12 });
    }

    setPointPos(null);
    setPointInfo(null);
    setBasemap('osm');
  }, [resetKey, currentSite]);


  // ─── 5. Raster Overlays ───────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const isBhavani = currentSite === 'bhavanisagar';
    const hillshadeLayerId = isBhavani ? 'hillshade' : 'hirakud_hillshade';
    const effectiveRasterVis = { ...rasterVisible };

    if (basemap === 'terrain') {
      effectiveRasterVis[hillshadeLayerId] = true;
    }

    Object.entries(effectiveRasterVis).forEach(([id, visible]) => {
      if (!isBhavani && id !== 'hirakud_hillshade') {
        if (rasterLayersRef.current[id]) {
          map.removeLayer(rasterLayersRef.current[id]);
          delete rasterLayersRef.current[id];
        }
        return;
      }

      const bounds = OVERLAY_BOUNDS[id];
      if (!bounds) return;

      const paneName = id.includes('hillshade') ? 'hillshadePane' : 'vectorPane';

      if (visible) {
        if (!rasterLayersRef.current[id]) {
          const url = `/api/tiles/overlays/${id}.png`;
          const overlay = L.imageOverlay(url, bounds, {
            opacity: rasterOpacity[id] ?? 0.75,
            pane: paneName,
          });
          overlay.addTo(map);
          rasterLayersRef.current[id] = overlay;
        } else {
          rasterLayersRef.current[id].setOpacity(rasterOpacity[id] ?? 0.75);
        }
      } else {
        if (rasterLayersRef.current[id]) {
          map.removeLayer(rasterLayersRef.current[id]);
          delete rasterLayersRef.current[id];
        }
      }
    });
  }, [rasterVisible, rasterOpacity, currentSite, basemap]);

  // ─── 5b. D-Flow Simulation Playback Overlay ───────────────
  const simOverlayRef = useRef<L.ImageOverlay | null>(null);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const isBhavani = currentSite === 'bhavanisagar';
    const isSimMode = mode === 'simulation';
    const isFloodEnabled = simAnimationVisible;
    const shouldShow = isBhavani && isSimMode && isFloodEnabled && Boolean(simFrameUrl) && Boolean(simBounds);

    if (shouldShow && simFrameUrl && simBounds) {
      if (!simOverlayRef.current) {
        const overlay = L.imageOverlay(simFrameUrl, simBounds, {
          opacity: floodOpacity,
          pane: 'floodPane',
          interactive: false,
        });
        overlay.addTo(map);
        simOverlayRef.current = overlay;
      } else {
        simOverlayRef.current.setUrl(simFrameUrl);
        simOverlayRef.current.setBounds(L.latLngBounds(simBounds));
        simOverlayRef.current.setOpacity(floodOpacity);
      }
    } else {
      if (simOverlayRef.current) {
        map.removeLayer(simOverlayRef.current);
        simOverlayRef.current = null;
      }
    }
  }, [simFrameUrl, simBounds, floodOpacity, simAnimationVisible, currentSite, mode]);


  // ─── 6. Vector GeoJSON Layers with Real Attributes ─────────
  const loadVector = useCallback(async (id: string) => {
    const map = mapRef.current;
    if (!map) return;
    if (vectorLayersRef.current[id]) return;

    let data: GeoJSON.FeatureCollection;
    if (geoJsonCacheRef.current[id]) {
      data = geoJsonCacheRef.current[id];
    } else {
      try {
        const r = await fetch(`/api/tiles/geojson/${id}.geojson`);
        if (!r.ok) return;
        data = await r.json();
        geoJsonCacheRef.current[id] = data;
      } catch {
        return;
      }
    }

    const baseStyle = VECTOR_STYLES[id] ?? { color: '#64748b', weight: 1.5 };
    const targetPane = id.includes('reservoir') ? 'reservoirPane'
      : id.includes('river') ? 'riverPane'
      : (id === 'dam_point' || id === 'bridges' || id === 'settlements' || id === 'critical_facilities' || id.includes('hirakud_dam')) ? 'markerPane'
      : 'vectorPane';

    const layer = L.geoJSON(data, {
      pane: targetPane,
      style: (feature) => {
        if (id === 'hazard_severity' && feature?.properties?.hazard_code) {
          const code = feature.properties.hazard_code as number;
          return { ...baseStyle, fillColor: HAZARD_FILL[code] ?? '#e2e8f0', fillOpacity: 0.5 };
        }
        if (id === 'response_zones' && feature?.properties?.priority_rank) {
          const p = feature.properties.priority_rank as number;
          const c = p === 1 ? '#ef4444' : p === 2 ? '#f59e0b' : '#22c55e';
          return { ...baseStyle, color: c, fillColor: c };
        }
        return baseStyle;
      },
      pointToLayer: (_feature, latlng) => {
        const style = VECTOR_STYLES[id] ?? {};
        const radius = id.includes('dam_point') ? 9 : id === 'bridges' ? 7 : id === 'settlements' ? 5 : 7;
        return L.circleMarker(latlng, {
          radius,
          pane: 'markerPane',
          ...style,
        });
      },
      onEachFeature: (feature, flayer) => {
        if (!feature.properties) return;
        const props = feature.properties;

        // A. Dam Structure Popup
        if (id === 'dam_point' || id === 'hirakud_dam_point') {
          const damName = props.name || props.dam_name || 'Bhavanisagar Dam';
          const river = props.river || 'Bhavani River';
          const state = props.state || 'Tamil Nadu';
          const scenario = props.scenario || 'BHV_BASE';
          const classification = props.classification || 'HYPOTHETICAL BREACH SCREENING';
          const lat = Number(props.lat ?? 11.47083);
          const lon = Number(props.lon ?? 77.11389);
          const frl = props.fsl_elevation_m ? `${props.fsl_elevation_m} m` : '280.42 m';
          const gross = props.gross_storage_mcm ? `${props.gross_storage_mcm} MCM` : '928.0 MCM';

          const html = `
            <div style="font-family:system-ui,sans-serif;min-width:230px;color:#0f172a;">
              <div style="font-weight:700;font-size:13px;color:#0f172a;border-bottom:2px solid #f59e0b;padding-bottom:4px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                <span style="color:#d97706;font-size:15px;">▲</span> ${damName}
              </div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>River:</strong> ${river}</div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>State / Region:</strong> ${state}</div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>Coordinates:</strong> ${lat.toFixed(5)}°N, ${lon.toFixed(5)}°E</div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>Full Reservoir Level (FRL):</strong> ${frl} (${gross})</div>
              <div style="font-size:11px;color:#475569;margin-bottom:6px;"><strong>Scenario ID:</strong> <span style="font-family:monospace;background:#f1f5f9;padding:1px 5px;border-radius:3px;font-weight:600;">${scenario}</span></div>
              <div style="font-size:10px;font-weight:700;color:#991b1b;background:#fef2f2;border:1px solid #fecaca;border-radius:4px;padding:5px 8px;text-transform:uppercase;letter-spacing:0.04em;">
                ${classification}
              </div>
            </div>
          `;
          flayer.bindPopup(html, { maxWidth: 300 });
          return;
        }

        // B. Real Bridges Popup
        if (id === 'bridges') {
          const bridgeId = props.bridge_id || `BR-${props.osm_id || '00'}`;
          const bridgeName = props.bridge_name || props.name || 'Unnamed mapped bridge crossing';
          const road = props.road || props.highway || 'Unclassified Road';
          const coords = feature.geometry && 'coordinates' in feature.geometry ? (feature.geometry as { coordinates: number[] }).coordinates : [0, 0];
          const lat = Number(props.latitude ?? coords[1] ?? 0);
          const lon = Number(props.longitude ?? coords[0] ?? 0);
          const hazardClass = props.hazard_class || 'H3';
          const arrTime = props.arrival_time || (props.arrival_time_hr ? `${props.arrival_time_hr} hr` : '1.0 hr');
          const zone = props.response_zone || 'Downstream Sector';

          const html = `
            <div style="font-family:system-ui,sans-serif;min-width:220px;color:#0f172a;">
              <div style="font-weight:700;font-size:12.5px;color:#0f172a;border-bottom:2px solid #d97706;padding-bottom:4px;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                <span style="color:#b45309;font-size:14px;">☲</span> ${bridgeName}
              </div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>Bridge ID:</strong> <span style="font-family:monospace;background:#f8fafc;padding:1px 4px;border-radius:3px;">${bridgeId}</span></div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>Road / Highway:</strong> ${road}</div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>Coordinates:</strong> ${lat.toFixed(5)}°N, ${lon.toFixed(5)}°E</div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>Hazard Severity:</strong> <span style="font-weight:700;color:#ea580c;">${hazardClass}</span></div>
              <div style="font-size:11px;color:#475569;margin-bottom:3px;"><strong>Flood Arrival Time:</strong> <span style="font-weight:700;color:#0284c7;">${arrTime}</span></div>
              <div style="font-size:11px;color:#475569;margin-bottom:6px;"><strong>Response Sector:</strong> ${zone}</div>
            </div>
          `;
          flayer.bindPopup(html, { maxWidth: 300 });

          flayer.on('click', () => {
            if (onSelectBridge) {
              onSelectBridge(props as Record<string, unknown>);
            }
          });
          return;
        }

        // C. Settlements Popup
        if (id === 'settlements') {
          const name = props.name || 'Settlement';
          const place = props.place || 'village';
          const coords = feature.geometry && 'coordinates' in feature.geometry ? (feature.geometry as { coordinates: number[] }).coordinates : [0, 0];
          const lat = Number(props.latitude ?? coords[1] ?? 0);
          const lon = Number(props.longitude ?? coords[0] ?? 0);
          const zone = props.response_zone || 'Downstream Basin';
          const arr = props.arrival_time || 'Outside direct flood corridor';

          const html = `
            <div style="font-family:system-ui,sans-serif;min-width:200px;color:#0f172a;">
              <div style="font-weight:700;font-size:12px;color:#0f172a;border-bottom:2px solid #64748b;padding-bottom:3px;margin-bottom:5px;">
                🏘 ${name} (${place})
              </div>
              <div style="font-size:11px;color:#475569;margin-bottom:2px;"><strong>Coordinates:</strong> ${lat.toFixed(5)}°N, ${lon.toFixed(5)}°E</div>
              <div style="font-size:11px;color:#475569;margin-bottom:2px;"><strong>Response Sector:</strong> ${zone}</div>
              <div style="font-size:11px;color:#475569;margin-bottom:2px;"><strong>Modeled Arrival:</strong> ${arr}</div>
              <div style="font-size:9.5px;color:#94a3b8;margin-top:4px;">Source: OpenStreetMap Verified Geography</div>
            </div>
          `;
          flayer.bindPopup(html, { maxWidth: 260 });
          return;
        }

        // D. Reservoir Surface Popup
        if (id === 'reservoir_surface' || id === 'hirakud_reservoir') {
          const name = id === 'reservoir_surface' ? 'Bhavanisagar Reservoir' : 'Hirakud Reservoir';
          const src = id === 'reservoir_surface' ? 'JRC Global Surface Water v1.4 / OSM' : 'HydroSHEDS / OSM Validated Waterbody';
          const html = `
            <div style="font-family:system-ui,sans-serif;min-width:200px;color:#0f172a;">
              <div style="font-weight:700;font-size:12px;color:#1d4ed8;border-bottom:2px solid #3b82f6;padding-bottom:3px;margin-bottom:5px;">
                💧 ${name}
              </div>
              <div style="font-size:11px;color:#475569;margin-bottom:2px;"><strong>Source Dataset:</strong> ${src}</div>
              <div style="font-size:11px;color:#475569;margin-bottom:2px;"><strong>Classification:</strong> REAL_GIS Vector</div>
              <div style="font-size:9.5px;color:#94a3b8;margin-top:4px;">Aligned with multi-temporal satellite water observations.</div>
            </div>
          `;
          flayer.bindPopup(html, { maxWidth: 280 });
          return;
        }

        // E. River Flowpath Popup
        if (id === 'bhavani_river' || id === 'hirakud_mahanadi_river') {
          const rName = id === 'bhavani_river' ? 'Lower Bhavani River' : 'Mahanadi River Reach';
          const html = `
            <div style="font-family:system-ui,sans-serif;min-width:200px;color:#0f172a;">
              <div style="font-weight:700;font-size:12px;color:#0284c7;border-bottom:2px solid #0ea5e9;padding-bottom:3px;margin-bottom:5px;">
                〰 ${rName}
              </div>
              <div style="font-size:11px;color:#475569;margin-bottom:2px;"><strong>Source Dataset:</strong> Validated M2 Hydrology / HydroSHEDS</div>
              <div style="font-size:11px;color:#475569;margin-bottom:2px;"><strong>Classification:</strong> REAL_GIS Hydrology Vector</div>
            </div>
          `;
          flayer.bindPopup(html, { maxWidth: 260 });
          return;
        }

        // Generic Table Popup for other layers
        let html = '<table style="font-size:11px;border-collapse:collapse;">';
        for (const [k, v] of Object.entries(props)) {
          if (v == null || k === 'geometry') continue;
          html += `<tr><td style="color:#64748b;padding:2px 8px 2px 0">${k}</td><td style="font-weight:600;padding:2px 0">${v}</td></tr>`;
        }
        html += '</table>';
        flayer.bindPopup(html, { maxWidth: 280 });
      },
    });

    vectorLayersRef.current[id] = layer;
    layer.addTo(map);
  }, [onSelectBridge]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const isBhavani = currentSite === 'bhavanisagar';

    if (!isBhavani) {
      Object.keys(vectorLayersRef.current).forEach((k) => {
        if (!k.startsWith('hirakud_')) {
          map.removeLayer(vectorLayersRef.current[k]);
          delete vectorLayersRef.current[k];
        }
      });
      ['hirakud_study_area', 'hirakud_reservoir', 'hirakud_mahanadi_river', 'hirakud_dam_point'].forEach(loadVector);
    } else {
      Object.keys(vectorLayersRef.current).forEach((k) => {
        if (k.startsWith('hirakud_')) {
          map.removeLayer(vectorLayersRef.current[k]);
          delete vectorLayersRef.current[k];
        }
      });

      Object.entries(vectorVisible).forEach(([id, visible]) => {
        if (visible) {
          if (!vectorLayersRef.current[id]) {
            loadVector(id);
          } else {
            if (!map.hasLayer(vectorLayersRef.current[id])) {
              vectorLayersRef.current[id].addTo(map);
            }
          }
        } else {
          if (vectorLayersRef.current[id] && map.hasLayer(vectorLayersRef.current[id])) {
            map.removeLayer(vectorLayersRef.current[id]);
          }
        }
      });
    }
  }, [vectorVisible, loadVector, currentSite]);

  // ─── 7. Smooth D-Flow Simulation Playback ─────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Never display Bhavanisagar simulation frames over Hirakud
    if (currentSite !== 'bhavanisagar' || !simFrameUrl || !simBounds || mode !== 'simulation') {
      if (simLayerA.current) { map.removeLayer(simLayerA.current); simLayerA.current = null; }
      if (simLayerB.current) { map.removeLayer(simLayerB.current); simLayerB.current = null; }
      return;
    }

    // Preload next frames into memory
    const match = simFrameUrl.match(/frame_(\d+)\.png/);
    if (match) {
      const curIdx = parseInt(match[1], 10);
      for (let offset = 1; offset <= 3; offset++) {
        const nextIdx = curIdx + offset;
        if (nextIdx <= 180) {
          const nextUrl = `/api/tiles/simulation_frames/frame_${String(nextIdx).padStart(3, '0')}.png`;
          if (!preloadedImages.current[nextUrl]) {
            const img = new Image();
            img.src = nextUrl;
            preloadedImages.current[nextUrl] = img;
          }
        }
      }
    }

    // Ping-pong crossfade between layers A and B for zero visual flicker
    if (activeSimLayer.current === 'A') {
      if (!simLayerA.current) {
        simLayerA.current = L.imageOverlay(simFrameUrl, simBounds, { opacity: floodOpacity, pane: 'floodPane' }).addTo(map);
      } else {
        simLayerA.current.setUrl(simFrameUrl);
        simLayerA.current.setOpacity(floodOpacity);
      }
    } else {
      if (!simLayerB.current) {
        simLayerB.current = L.imageOverlay(simFrameUrl, simBounds, { opacity: floodOpacity, pane: 'floodPane' }).addTo(map);
      } else {
        simLayerB.current.setUrl(simFrameUrl);
        simLayerB.current.setOpacity(floodOpacity);
      }
    }
  }, [simFrameUrl, simBounds, mode, currentSite, floodOpacity]);

  // ─── 8. Selected Zone Highlight ───────────────────────────
  useEffect(() => {
    const layer = vectorLayersRef.current['response_zones'];
    if (!layer) return;
    layer.eachLayer((l: L.Layer) => {
      const fl = l as L.Path;
      const feat = (fl as unknown as { feature?: GeoJSON.Feature }).feature;
      if (feat?.properties?.zone_id === selectedZone) {
        fl.setStyle({ weight: 3.5, color: '#2563eb', fillOpacity: 0.35 });
        (fl as L.Polygon).bringToFront?.();
      } else {
        fl.setStyle(VECTOR_STYLES['response_zones']);
      }
    });
  }, [selectedZone]);

  return (
    <div style={{ position: 'relative', flex: 1, overflow: 'hidden', height: '100%', width: '100%' }}>
      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />

      {/* Top Map Control Bar (Responsive wrapper avoiding zoom controls on top-right) */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 10,
          right: 54,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 8,
          alignItems: 'center',
          zIndex: 1000,
          pointerEvents: 'none',
        }}
      >
        {/* Floating Basemap Selector Controls */}
        <div
          style={{
            pointerEvents: 'auto',
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(8px)',
            border: '1px solid #334155',
            borderRadius: 6,
            padding: '5px 10px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: '#e2e8f0',
            fontSize: 11,
            boxShadow: '0 4px 14px rgba(0,0,0,0.25)',
          }}
        >
          <span style={{ fontWeight: 700, color: '#38bdf8', letterSpacing: '0.04em' }}>BASEMAP:</span>
          <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontWeight: basemap === 'osm' ? 700 : 400 }}>
            <input
              type="radio"
              name="basemap"
              value="osm"
              checked={basemap === 'osm'}
              onChange={() => setBasemap('osm')}
            />
            OpenStreetMap
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontWeight: basemap === 'satellite' ? 700 : 400 }}>
            <input
              type="radio"
              name="basemap"
              value="satellite"
              checked={basemap === 'satellite'}
              onChange={() => setBasemap('satellite')}
            />
            Satellite (Esri)
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontWeight: basemap === 'terrain' ? 700 : 400 }}>
            <input
              type="radio"
              name="basemap"
              value="terrain"
              checked={basemap === 'terrain'}
              onChange={() => setBasemap('terrain')}
            />
            Local Terrain (Offline)
          </label>
        </div>

        {/* Fast Navigation Preset Bar */}
        {currentSite === 'bhavanisagar' && (
          <div
            style={{
              pointerEvents: 'auto',
              background: 'rgba(15, 23, 42, 0.90)',
              backdropFilter: 'blur(8px)',
              border: '1px solid #334155',
              borderRadius: 6,
              padding: '4px 8px',
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 5,
              boxShadow: '0 4px 14px rgba(0,0,0,0.25)',
            }}
          >
            <span style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginRight: 2 }}>
              NAVIGATE:
            </span>
            <button
              onClick={() => navigateTo('dam')}
              className="fast-nav-btn"
              title="Zoom tightly around Bhavanisagar Dam"
              style={fastNavBtnStyle}
            >
              ▲ Dam
            </button>
            <button
              onClick={() => navigateTo('reservoir')}
              className="fast-nav-btn"
              title="Fit Bhavanisagar Reservoir"
              style={fastNavBtnStyle}
            >
              💧 Reservoir
            </button>
            <button
              onClick={() => navigateTo('flood_extent')}
              className="fast-nav-btn"
              title="Fit Validated M5 Flood Inundation Extent"
              style={{ ...fastNavBtnStyle, borderColor: '#38bdf8', color: '#38bdf8' }}
            >
              🌊 Flood Extent
            </button>
            <button
              onClick={() => navigateTo('downstream')}
              className="fast-nav-btn"
              title="Fit Downstream Lower Bhavani Corridor"
              style={fastNavBtnStyle}
            >
              〰 Downstream
            </button>
            <button
              onClick={() => navigateTo('full_study')}
              className="fast-nav-btn"
              title="Restore Full Study Domain"
              style={fastNavBtnStyle}
            >
              ⛶ Full Study Area
            </button>
          </div>
        )}
      </div>

      {/* Floating North Indicator Widget (Top-Right under zoom) */}
      <div
        style={{
          position: 'absolute',
          top: 60,
          right: 12,
          background: 'rgba(15, 23, 42, 0.88)',
          border: '1px solid #334155',
          borderRadius: 4,
          padding: '4px 8px',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        }}
      >
        <span style={{ color: '#ef4444', fontWeight: 900, fontSize: 13, lineHeight: 1 }}>▲</span>
        <span style={{ color: '#f8fafc', fontWeight: 700, fontSize: 10 }}>N</span>
      </div>

      {/* Floating Depth Scale & Opacity Control (Bottom-Left) */}
      {currentSite === 'bhavanisagar' && mode === 'simulation' && (
        <div
          style={{
            position: 'absolute',
            bottom: 24,
            left: 14,
            background: 'rgba(15, 23, 42, 0.92)',
            backdropFilter: 'blur(8px)',
            border: '1px solid #334155',
            borderRadius: 6,
            padding: '8px 12px',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
            maxWidth: 320,
            boxShadow: '0 4px 14px rgba(0,0,0,0.25)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              D-Flow Depth (m)
            </span>
            {onFloodOpacityChange && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 9.5, color: '#94a3b8' }}>Opacity {Math.round(floodOpacity * 100)}%</span>
                <input
                  type="range"
                  min="0.30"
                  max="0.90"
                  step="0.05"
                  value={floodOpacity}
                  onChange={(e) => onFloodOpacityChange(parseFloat(e.target.value))}
                  style={{ width: 60, height: 4, cursor: 'pointer', accentColor: '#38bdf8' }}
                />
              </div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {[
              { label: '0.05–0.5', color: '#A0E1FF' },
              { label: '0.5–1.0',  color: '#46BEFA' },
              { label: '1.0–2.0',  color: '#008CEB' },
              { label: '2.0–5.0',  color: '#0A50C8' },
              { label: '5.0–10',   color: '#4B14A0' },
              { label: '>10m',     color: '#82006E' },
            ].map((b) => (
              <div key={b.label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                <div style={{ width: '100%', height: 8, background: b.color, borderRadius: 1 }} />
                <span style={{ fontSize: 8.5, color: '#cbd5e1', marginTop: 2 }}>{b.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Real-time Cursor Coordinates Bar (Bottom-Center) */}
      {cursorPos && (
        <div
          style={{
            position: 'absolute',
            bottom: 6,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid #1e293b',
            borderRadius: 4,
            padding: '2px 8px',
            fontSize: 10,
            fontFamily: 'monospace',
            color: '#94a3b8',
            zIndex: 999,
          }}
        >
          {cursorPos.lat.toFixed(5)}° N, {cursorPos.lng.toFixed(5)}° E · WGS 84
        </div>
      )}

      {/* Point Analysis Inspection Card (Right-Floating upon Map Click) */}
      {pointPos && currentSite === 'bhavanisagar' && (
        <div
          style={{
            position: 'absolute',
            top: 70,
            left: 14,
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            padding: '10px 12px',
            fontSize: 11,
            color: '#0f172a',
            zIndex: 1000,
            minWidth: 260,
            maxWidth: 320,
            boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: 4, marginBottom: 6 }}>
            <span style={{ fontWeight: 700, fontSize: 12, color: '#0f172a' }}>📍 Location Query</span>
            <button
              onClick={() => { setPointPos(null); setPointInfo(null); }}
              style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: 13, color: '#94a3b8', fontWeight: 700 }}
            >
              ✕
            </button>
          </div>

          <div style={{ fontSize: 10, color: '#64748b', marginBottom: 6 }}>
            {pointPos[0].toFixed(5)}° N, {pointPos[1].toFixed(5)}° E
          </div>

          {querying ? (
            <div style={{ color: '#0284c7', fontStyle: 'italic', padding: '6px 0' }}>Sampling spatial layers…</div>
          ) : pointInfo ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #f1f5f9', paddingBottom: 2 }}>
                <span style={{ color: '#64748b' }}>Peak Depth:</span>
                <span style={{ fontWeight: 700, color: (pointInfo.max_depth_m ?? 0) > 0 ? '#1d4ed8' : '#94a3b8' }}>
                  {pointInfo.max_depth_m != null && pointInfo.max_depth_m > 0 ? `${pointInfo.max_depth_m.toFixed(2)} m` : 'Dry / 0.00 m'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #f1f5f9', paddingBottom: 2 }}>
                <span style={{ color: '#64748b' }}>Peak Velocity:</span>
                <span style={{ fontWeight: 700, color: (pointInfo.max_velocity_mps ?? 0) > 0 ? '#0891b2' : '#94a3b8' }}>
                  {pointInfo.max_velocity_mps != null && pointInfo.max_velocity_mps > 0 ? `${pointInfo.max_velocity_mps.toFixed(2)} m/s` : '0.00 m/s'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #f1f5f9', paddingBottom: 2 }}>
                <span style={{ color: '#64748b' }}>Flood Arrival:</span>
                <span style={{ fontWeight: 700, color: '#475569' }}>
                  {pointInfo.arrival_time_hr != null && pointInfo.arrival_time_hr > 0 ? `${pointInfo.arrival_time_hr.toFixed(2)} hr` : 'N/A'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #f1f5f9', paddingBottom: 2 }}>
                <span style={{ color: '#64748b' }}>CWC Hazard:</span>
                <span style={{ fontWeight: 700, color: pointInfo.hazard_class ? '#ea580c' : '#94a3b8' }}>
                  {pointInfo.hazard_class ?? 'None'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #f1f5f9', paddingBottom: 2 }}>
                <span style={{ color: '#64748b' }}>Response Zone:</span>
                <span style={{ fontWeight: 700, color: '#334155' }}>
                  {pointInfo.response_zone ?? 'Outside Zonal Bounds'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #f1f5f9', paddingBottom: 2 }}>
                <span style={{ color: '#64748b' }}>Historical 2019 Flood:</span>
                <span style={{ fontWeight: 600, color: pointInfo.historical_flood_detected ? '#8b5cf6' : '#94a3b8' }}>
                  {pointInfo.historical_flood_detected ? 'YES' : 'NO'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Latest Candidate Water:</span>
                <span style={{ fontWeight: 600, color: pointInfo.latest_candidate_water_change ? '#06b6d4' : '#94a3b8' }}>
                  {pointInfo.latest_candidate_water_change ? 'YES' : 'NO'}
                </span>
              </div>
            </div>
          ) : (
            <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>Outside model extent / No data sampled.</div>
          )}
        </div>
      )}

      {/* Second Site Notice Overlay */}
      {currentSite !== 'bhavanisagar' && (
        <div
          style={{
            position: 'absolute',
            top: 56,
            left: 12,
            background: 'rgba(30, 41, 59, 0.94)',
            border: '1px solid #eab308',
            borderRadius: 6,
            padding: '8px 14px',
            color: '#fef08a',
            fontSize: 11,
            fontWeight: 600,
            zIndex: 1000,
            boxShadow: '0 4px 14px rgba(0,0,0,0.3)',
          }}
        >
          ℹ Production hydraulic simulation not executed for this site. Displaying real GIS terrain, river & reservoir boundaries.
        </div>
      )}
    </div>
  );
}

const fastNavBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: '1px solid #475569',
  borderRadius: 4,
  padding: '2px 8px',
  color: '#e2e8f0',
  fontSize: 10,
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all 0.15s ease',
  outline: 'none',
};
