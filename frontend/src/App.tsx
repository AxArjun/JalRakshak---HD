// JalRakshak-HD SIH Dashboard — Root Application (Multi-Site Platform & GIS UX Enhancement)
import { useState, useCallback, useEffect } from 'react';
import type { DashboardMode, SiteItem } from './types/dashboard';
import { fetchHealth, fetchSites } from './services/api';

import Header from './components/Header';
import LayerPanel from './components/LayerPanel';
import MapView from './components/MapView';
import SimulationPanel from './components/SimulationPanel';
import HADRPanel from './components/HADRPanel';
import SPHPanel from './components/SPHPanel';
import EOPanel from './components/EOPanel';
import SiteCapabilityPanel from './components/SiteCapabilityPanel';

// ─── Default layer visibility ──────────────────────────────
const DEFAULT_RASTER_VIS: Record<string, boolean> = {
  hillshade: false,
  max_depth: false,
  max_velocity: false,
  arrival_time: false,
  hazard_class: false,
  historical_flood: false,
};

const DEFAULT_RASTER_OPQ: Record<string, number> = {
  hillshade: 0.55,
  max_depth: 0.75,
  max_velocity: 0.75,
  arrival_time: 0.75,
  hazard_class: 0.75,
  historical_flood: 0.65,
};

const DEFAULT_VEC_VIS: Record<string, boolean> = {
  inundation_extent: false,
  hazard_severity: false,
  response_zones: false,
  road_exposure: false,
  bhavani_river: true,
  reservoir_surface: true,
  dam_point: true,
  bridges: true,
  settlements: false,
  critical_facilities: false,
  historical_flood: false,
  latest_water_change: false,
  sph_gauges: false,
  sph_reach: false,
};

const RIGHT_PANEL_LABEL: Record<DashboardMode, string> = {
  simulation: '▶ Simulation Timeline',
  hadr:       '⚠ HADR Exposure Analysis',
  sph:        '〜 Near-Field SPH',
  eo:         '🛰 Earth Observation',
};

// ─── Right panel — mode-aware defaults ────────────────────
function modeLayerDefaults(mode: DashboardMode): {
  raster?: Partial<Record<string, boolean>>;
  vector?: Partial<Record<string, boolean>>;
} {
  switch (mode) {
    case 'simulation':
      return {
        raster: { hillshade: false, max_depth: false, max_velocity: false, arrival_time: false },
        vector: { bhavani_river: true, reservoir_surface: true, dam_point: true, bridges: true, inundation_extent: false }
      };
    case 'hadr':
      return {
        raster: { hazard_class: true, hillshade: false },
        vector: { hazard_severity: false, response_zones: true, road_exposure: false, bridges: true, inundation_extent: false }
      };
    case 'sph':
      return {
        raster: { max_depth: true, max_velocity: true },
        vector: { sph_gauges: true, sph_reach: true, dam_point: true, inundation_extent: false }
      };
    case 'eo':
      return {
        raster: { hillshade: false, historical_flood: true },
        vector: { historical_flood: true, latest_water_change: true, bhavani_river: true, inundation_extent: false }
      };
  }
}


export default function App() {
  const [mode, setMode] = useState<DashboardMode>(() => {
    const params = new URLSearchParams(window.location.search);
    const m = params.get('mode') as DashboardMode;
    if (m && ['simulation', 'hadr', 'sph', 'eo'].includes(m)) {
      return m;
    }
    return 'simulation';
  });
  const [apiOk, setApiOk] = useState(false);
  const [sites, setSites] = useState<SiteItem[]>([
    { site_id: 'bhavanisagar', display_name: 'Bhavanisagar Dam & Lower Bhavani Basin', enabled: true },
    { site_id: 'hirakud', display_name: 'Hirakud Dam & Mahanadi River Basin', enabled: true }
  ]);
  const [currentSite, setCurrentSite] = useState<string>(() => {
    const params = new URLSearchParams(window.location.search);
    const s = params.get('site');
    return s === 'hirakud' ? 'hirakud' : 'bhavanisagar';
  });

  const [rasterVisible, setRasterVisible] = useState<Record<string, boolean>>(() => {
    const params = new URLSearchParams(window.location.search);
    const m = (params.get('mode') as DashboardMode) || 'simulation';
    const defs = modeLayerDefaults(m);
    const initial: Record<string, boolean> = { ...DEFAULT_RASTER_VIS };
    if (defs.raster) {
      Object.assign(initial, defs.raster);
    }
    return initial;
  });
  const [rasterOpacity, setRasterOpacity] = useState<Record<string, number>>(DEFAULT_RASTER_OPQ);
  const [vectorVisible, setVectorVisible] = useState<Record<string, boolean>>(() => {
    const params = new URLSearchParams(window.location.search);
    const m = (params.get('mode') as DashboardMode) || 'simulation';
    const defs = modeLayerDefaults(m);
    const initial: Record<string, boolean> = { ...DEFAULT_VEC_VIS };
    if (defs.vector) {
      Object.assign(initial, defs.vector);
    }
    return initial;
  });
  const [simAnimationVisible, setSimAnimationVisible] = useState<boolean>(() => {
    const params = new URLSearchParams(window.location.search);
    const m = params.get('mode');
    return m ? m === 'simulation' : true;
  });
  const [floodOpacity, setFloodOpacity] = useState<number>(0.65);

  // Collapsible panels
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);

  // Simulation frame state
  const [simFrameUrl, setSimFrameUrl] = useState<string | null>(
    '/api/tiles/simulation_frames/frame_000.png'
  );
  const [simBounds] = useState<[[number, number], [number, number]]>([
    [11.359179, 77.111197],
    [11.57997, 77.423552],
  ]);

  // HADR selected zone
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  // ─── API health & sites fetch ─────────────────────────────
  useEffect(() => {
    fetchHealth()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));

    fetchSites()
      .then((data) => {
        if (data && data.sites) setSites(data.sites);
        if (data && data.active_site) setCurrentSite(data.active_site);
      })
      .catch(() => {});

    const t = setInterval(() => {
      fetchHealth().then(() => setApiOk(true)).catch(() => setApiOk(false));
    }, 30_000);
    return () => clearInterval(t);
  }, []);

  // ─── Mode switch → apply recommended layers ───────────────
  const handleMode = useCallback((m: DashboardMode) => {
    setMode(m);
    const defs = modeLayerDefaults(m);

    if (defs.raster) {
      setRasterVisible(prev => ({
        ...Object.fromEntries(Object.keys(prev).map(k => [k, false])),
        ...(defs.raster as Record<string, boolean>),
      }));
    }
    if (defs.vector) {
      setVectorVisible(prev => ({
        ...Object.fromEntries(Object.keys(prev).map(k => [k, false])),
        bhavani_river: true,
        dam_point: true,
        ...(defs.vector as Record<string, boolean>),
      }));
    }

    if (m !== 'simulation') {
      setSimFrameUrl(null);
    } else {
      setSimAnimationVisible(true);
      setSimFrameUrl('/api/tiles/simulation_frames/frame_000.png');
    }
  }, []);

  const onRasterToggle = useCallback((id: string) => {
    setRasterVisible(prev => {
      const nextState = !prev[id];
      const updated = { ...prev, [id]: nextState };
      // Mutual raster exclusivity: if enabling max_depth/velocity/arrival, deactivate other heavy rasters
      if (nextState && (id === 'max_depth' || id === 'max_velocity' || id === 'arrival_time' || id === 'hazard_class')) {
        ['max_depth', 'max_velocity', 'arrival_time', 'hazard_class'].forEach(k => {
          if (k !== id) updated[k] = false;
        });
      }
      return updated;
    });
  }, []);

  const onVectorToggle = useCallback((id: string) => {
    setVectorVisible(prev => ({ ...prev, [id]: !prev[id] }));
  }, []);

  const onOpacity = useCallback((id: string, v: number) => {
    setRasterOpacity(prev => ({ ...prev, [id]: v }));
  }, []);

  const onSimFrame = useCallback((url: string, _bounds: [[number, number], [number, number]]) => {
    setSimFrameUrl(url);
  }, []);

  const [resetKey, setResetKey] = useState<number>(0);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toastMsg) return;
    const t = setTimeout(() => setToastMsg(null), 2400);
    return () => clearTimeout(t);
  }, [toastMsg]);

  // ─── Reset Map & State to Default (Respects Current Site) ──
  const handleResetMap = useCallback(() => {
    if (currentSite === 'bhavanisagar') {
      setMode('simulation');
      setRasterVisible(DEFAULT_RASTER_VIS);
      setVectorVisible(DEFAULT_VEC_VIS);
      setSimAnimationVisible(true);
      setSimFrameUrl('/api/tiles/simulation_frames/frame_000.png');
      setSelectedZone(null);
      setFloodOpacity(0.65);
      setLeftPanelOpen(true);
      setRightPanelOpen(true);
      setResetKey(k => k + 1);
      setToastMsg('↺ Dashboard reset (Bhavanisagar)');
    } else {
      // Hirakud Site Reset — Keep site as Hirakud, do NOT load Bhavanisagar frames
      setMode('simulation');
      setRasterVisible(DEFAULT_RASTER_VIS);
      setVectorVisible(DEFAULT_VEC_VIS);
      setSimAnimationVisible(false);
      setSimFrameUrl(null);
      setSelectedZone(null);
      setLeftPanelOpen(true);
      setRightPanelOpen(true);
      setResetKey(k => k + 1);
      setToastMsg('↺ Dashboard reset (Hirakud)');
    }
  }, [currentSite]);

  // ─── Instant Deterministic SIH DEMO MODE Preset ───────────
  const handleDemoMode = useCallback(() => {
    setCurrentSite('bhavanisagar');
    setMode('simulation');
    setRasterVisible({
      hillshade: false,
      max_depth: false,
      max_velocity: false,
      arrival_time: false,
      hazard_class: false,
      historical_flood: false,
    });
    setVectorVisible({
      inundation_extent: false,
      hazard_severity: false,
      response_zones: false,
      road_exposure: false,
      bhavani_river: true,
      reservoir_surface: true,
      dam_point: true,
      bridges: true,
      settlements: false,
      critical_facilities: false,
      historical_flood: false,
      latest_water_change: false,
      sph_gauges: false,
      sph_reach: false,
    });
    setSimAnimationVisible(true);
    setSimFrameUrl('/api/tiles/simulation_frames/frame_000.png');
    setSelectedZone(null);
    setFloodOpacity(0.65);
    setLeftPanelOpen(true);
    setRightPanelOpen(true);
    setResetKey(k => k + 1);
    setToastMsg('★ Demo view restored');
  }, []);

  // Ensure flood layer is enabled when Play is pressed
  const handleEnsureFloodVisible = useCallback(() => {
    if (!simAnimationVisible) {
      setSimAnimationVisible(true);
      setToastMsg('🌊 D-Flow flood animation enabled');
    }
  }, [simAnimationVisible]);


  // Keyboard Shortcuts: 'D' for Demo Mode, 'R' for Reset
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if (e.key === 'd' || e.key === 'D') {
        handleDemoMode();
      } else if (e.key === 'r' || e.key === 'R') {
        handleResetMap();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [handleDemoMode, handleResetMap]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        background: '#f8fafc',
      }}
    >
      {/* Top Header */}
      <Header
        mode={mode}
        onMode={handleMode}
        apiOk={apiOk}
        currentSite={currentSite}
        onSelectSite={setCurrentSite}
        sites={sites}
        leftPanelOpen={leftPanelOpen}
        onToggleLeftPanel={() => setLeftPanelOpen(o => !o)}
        rightPanelOpen={rightPanelOpen}
        onToggleRightPanel={() => setRightPanelOpen(o => !o)}
        onResetMap={handleResetMap}
        onDemoMode={handleDemoMode}
      />

      {/* Scientific Disclaimer Banner */}
      <div className="disclaimer-bar">
        Research screening prototype. The breach scenario is hypothetical; hydraulic results are model outputs and not an official warning.
      </div>

      {/* Floating Action Feedback Toast */}
      {toastMsg && (
        <div
          style={{
            position: 'fixed',
            top: 58,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 9999,
            background: 'rgba(15, 23, 42, 0.94)',
            backdropFilter: 'blur(8px)',
            color: '#38bdf8',
            border: '1px solid #38bdf8',
            borderRadius: 6,
            padding: '5px 14px',
            fontSize: 11.5,
            fontWeight: 700,
            boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          {toastMsg}
        </div>
      )}

      {/* Main Responsive GIS Layout */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', position: 'relative' }}>

        {/* Left Layer Control Panel (Collapsible) */}
        {leftPanelOpen && (
          <LayerPanel
            mode={mode}
            rasterVisible={rasterVisible}
            vectorVisible={vectorVisible}
            onRasterToggle={onRasterToggle}
            onVectorToggle={onVectorToggle}
            rasterOpacity={rasterOpacity}
            onOpacity={onOpacity}
            simAnimationVisible={simAnimationVisible}
            onSimAnimationToggle={() => setSimAnimationVisible(v => !v)}
            floodOpacity={floodOpacity}
            onFloodOpacityChange={setFloodOpacity}
          />
        )}

        {/* Center GIS Map View (Expands to 100% when sidebars collapse) */}
        <MapView
          mode={mode}
          currentSite={currentSite}
          rasterVisible={rasterVisible}
          rasterOpacity={rasterOpacity}
          vectorVisible={vectorVisible}
          simFrameUrl={mode === 'simulation' ? simFrameUrl : null}
          simBounds={simBounds}
          selectedZone={selectedZone}
          simAnimationVisible={simAnimationVisible}
          floodOpacity={floodOpacity}
          onFloodOpacityChange={setFloodOpacity}
          resetKey={resetKey}
        />

        {/* Right Data & Control Panel (Collapsible) */}
        {rightPanelOpen && (
          <div
            style={{
              width: 340,
              minWidth: 320,
              maxWidth: 360,
              flexShrink: 0,
              display: 'flex',
              flexDirection: 'column',
              background: '#ffffff',
              borderLeft: '1px solid #e2e8f0',
              overflowY: 'auto',
              height: '100%',
              zIndex: 10,
            }}
          >
            {currentSite !== 'bhavanisagar' ? (
              <>
                <div className="panel-header">
                  📋 Site Portability Diagnostics
                </div>
                <SiteCapabilityPanel siteId={currentSite} />
              </>
            ) : (
              <>
                <div className="panel-header">
                  {RIGHT_PANEL_LABEL[mode]}
                </div>

                {mode === 'simulation' && (
                  <SimulationPanel
                    onFrame={onSimFrame}
                    resetKey={resetKey}
                    onEnsureFloodVisible={handleEnsureFloodVisible}
                  />
                )}
                {mode === 'hadr' && (
                  <HADRPanel
                    siteId={currentSite}
                    selectedZone={selectedZone}
                    onSelectZone={setSelectedZone}
                  />
                )}
                {mode === 'sph' && <SPHPanel />}
                {mode === 'eo'  && <EOPanel />}
              </>
            )}
          </div>
        )}
      </div>


      {/* Bottom Status & Provenance Bar */}
      <div
        style={{
          height: 22,
          flexShrink: 0,
          background: '#0d1b2e',
          display: 'flex',
          alignItems: 'center',
          padding: '0 14px',
          gap: 16,
          fontSize: 9.5,
          color: '#64748b',
          borderTop: '1px solid #1e293b',
        }}
      >
        <span style={{ color: '#94a3b8', fontWeight: 600 }}>JalRakshak-HD GIS Command Centre</span>
        <span>·</span>
        <span>CRS: EPSG:4326 / EPSG:32643 UTM 43N</span>
        <span>·</span>
        <span>181 D-Flow FM 2D Frames (108,000s / 30h)</span>
        <span>·</span>
        <span>20 Screened Bridge Crossings</span>
        <span>·</span>
        <span>CWC/AIDR Guideline 7.3</span>
        <div style={{ flex: 1 }} />
        <span style={{ color: apiOk ? '#86efac' : '#fca5a5' }}>
          {apiOk ? '● API ONLINE' : '● API DISCONNECTED'}
        </span>
      </div>
    </div>
  );
}
