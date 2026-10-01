// LayerPanel – Grouped & Exclusive GIS Layer Control Panel (SIH UX Enhancement)
import { useState } from 'react';
import type { DashboardMode } from '../types/dashboard';

interface Props {
  mode: DashboardMode;
  rasterVisible: Record<string, boolean>;
  vectorVisible: Record<string, boolean>;
  onRasterToggle: (id: string) => void;
  onVectorToggle: (id: string) => void;
  rasterOpacity: Record<string, number>;
  onOpacity: (id: string, v: number) => void;
  onSelectGroupPreset?: (preset: string) => void;
  simAnimationVisible?: boolean;
  onSimAnimationToggle?: () => void;
  floodOpacity?: number;
  onFloodOpacityChange?: (v: number) => void;
}

export default function LayerPanel({
  rasterVisible, vectorVisible, onRasterToggle, onVectorToggle,
  rasterOpacity, onOpacity,
  simAnimationVisible = true, onSimAnimationToggle,
  floodOpacity = 0.65, onFloodOpacityChange
}: Props) {
  // Collapsible section states
  const [hydraulicsOpen, setHydraulicsOpen] = useState(true);
  const [realGisOpen, setRealGisOpen] = useState(true);
  const [riskOpen, setRiskOpen] = useState(true);
  const [eoOpen, setEoOpen] = useState(false);

  return (
    <div
      style={{
        width: 250,
        flexShrink: 0,
        background: '#ffffff',
        borderRight: '1px solid #e2e8f0',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        overflowX: 'hidden',
        height: '100%',
        userSelect: 'none',
      }}
    >
      <div className="panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>🗺 Map Layers</span>
        <span style={{ fontSize: 10, color: '#94a3b8', fontWeight: 500 }}>SIH GIS Stacking</span>
      </div>

      {/* ─── GROUP 1: HYDRAULICS ─── */}
      <div
        className="collapsible-header"
        onClick={() => setHydraulicsOpen(o => !o)}
        style={{ background: '#f8fafc', fontWeight: 700, color: '#0369a1', borderTop: '1px solid #e2e8f0' }}
      >
        <span>🌊 1. HYDRAULICS</span>
        <span style={{ fontSize: 10 }}>{hydraulicsOpen ? '▲' : '▼'}</span>
      </div>
      {hydraulicsOpen && (
        <div style={{ padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
          {/* 🌊 D-Flow Flood Animation */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="sim-flood-animation"
              checked={simAnimationVisible}
              onChange={onSimAnimationToggle}
            />
            <span style={{ width: 9, height: 9, background: '#008CEB', borderRadius: 2, display: 'inline-block' }} />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontWeight: simAnimationVisible ? 600 : 400, fontSize: 11.5 }}>
                🌊 D-Flow Flood Animation
              </span>
              <span style={{ fontSize: 9, color: '#64748b' }}>Depth by timestep</span>
            </div>
            <span style={{ fontSize: 9, color: '#0284c7', background: '#e0f2fe', padding: '1px 4px', borderRadius: 3, fontWeight: 600 }}>
              FILLED
            </span>
          </div>
          {simAnimationVisible && onFloodOpacityChange && (
            <div style={{ padding: '0 12px 6px 32px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: '#64748b', minWidth: 24 }}>
                {Math.round(floodOpacity * 100)}%
              </span>
              <input
                type="range"
                min={0.1} max={1} step={0.05}
                value={floodOpacity}
                onChange={e => onFloodOpacityChange(parseFloat(e.target.value))}
                className="timeline-slider"
              />
            </div>
          )}

          {/* Maximum Inundation Extent (Static Outline) */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-inundation_extent"
              checked={vectorVisible['inundation_extent'] ?? false}
              onChange={() => onVectorToggle('inundation_extent')}
            />
            <span style={{ width: 9, height: 9, border: '1.5px solid #3b82f6', borderRadius: 2, display: 'inline-block' }} />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontWeight: vectorVisible['inundation_extent'] ? 600 : 400, fontSize: 11.5 }}>
                Maximum Inundation Extent
              </span>
              <span style={{ fontSize: 9, color: '#64748b' }}>Static envelope boundary</span>
            </div>
            <span style={{ fontSize: 9, color: '#64748b', background: '#f1f5f9', padding: '1px 4px', borderRadius: 3 }}>
              STATIC
            </span>
          </div>

          {/* Maximum Depth Raster */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="raster-max_depth"
              checked={rasterVisible['max_depth'] ?? false}
              onChange={() => onRasterToggle('max_depth')}
            />
            <span style={{ flex: 1, fontWeight: rasterVisible['max_depth'] ? 600 : 400 }}>
              🌊 Maximum Depth Envelope
            </span>
            <span style={{ fontSize: 9, color: '#64748b' }}>22.02m</span>
          </div>
          {rasterVisible['max_depth'] && (
            <div style={{ padding: '0 12px 6px 32px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: '#64748b', minWidth: 24 }}>
                {Math.round((rasterOpacity['max_depth'] ?? 0.75) * 100)}%
              </span>
              <input
                type="range"
                min={0.1} max={1} step={0.05}
                value={rasterOpacity['max_depth'] ?? 0.75}
                onChange={e => onOpacity('max_depth', parseFloat(e.target.value))}
                className="timeline-slider"
              />
            </div>
          )}

          {/* Maximum Velocity Raster */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="raster-max_velocity"
              checked={rasterVisible['max_velocity'] ?? false}
              onChange={() => onRasterToggle('max_velocity')}
            />
            <span style={{ flex: 1, fontWeight: rasterVisible['max_velocity'] ? 600 : 400 }}>
              💨 Maximum Velocity
            </span>
            <span style={{ fontSize: 9, color: '#64748b' }}>11.79m/s</span>
          </div>
          {rasterVisible['max_velocity'] && (
            <div style={{ padding: '0 12px 6px 32px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: '#64748b', minWidth: 24 }}>
                {Math.round((rasterOpacity['max_velocity'] ?? 0.75) * 100)}%
              </span>
              <input
                type="range"
                min={0.1} max={1} step={0.05}
                value={rasterOpacity['max_velocity'] ?? 0.75}
                onChange={e => onOpacity('max_velocity', parseFloat(e.target.value))}
                className="timeline-slider"
              />
            </div>
          )}

          {/* Arrival Time Raster */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="raster-arrival_time"
              checked={rasterVisible['arrival_time'] ?? false}
              onChange={() => onRasterToggle('arrival_time')}
            />
            <span style={{ flex: 1, fontWeight: rasterVisible['arrival_time'] ? 600 : 400 }}>
              ⏱ Flood Arrival Time
            </span>
            <span style={{ fontSize: 9, color: '#64748b' }}>0–30h</span>
          </div>
        </div>
      )}

      {/* ─── GROUP 2: REAL GIS VECTORS ─── */}
      <div
        className="collapsible-header"
        onClick={() => setRealGisOpen(o => !o)}
        style={{ background: '#f8fafc', fontWeight: 700, color: '#047857', borderTop: '1px solid #e2e8f0' }}
      >
        <span>📍 2. REAL GIS VECTORS</span>
        <span style={{ fontSize: 10 }}>{realGisOpen ? '▲' : '▼'}</span>
      </div>
      {realGisOpen && (
        <div style={{ padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
          {/* Dam */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-dam_point"
              checked={vectorVisible['dam_point'] ?? false}
              onChange={() => onVectorToggle('dam_point')}
            />
            <span style={{ width: 9, height: 9, background: '#f59e0b', borderRadius: '50%', border: '1px solid #b45309', display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['dam_point'] ? 600 : 400 }}>
              ▲ Dam Structure
            </span>
            <span style={{ fontSize: 9, color: '#16a34a', fontWeight: 600 }}>REAL</span>
          </div>

          {/* Reservoir */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-reservoir_surface"
              checked={vectorVisible['reservoir_surface'] ?? false}
              onChange={() => onVectorToggle('reservoir_surface')}
            />
            <span style={{ width: 9, height: 9, background: '#60a5fa', border: '1px solid #1d4ed8', borderRadius: 2, display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['reservoir_surface'] ? 600 : 400 }}>
              💧 Reservoir Surface
            </span>
            <span style={{ fontSize: 9, color: '#16a34a', fontWeight: 600 }}>REAL</span>
          </div>

          {/* Bhavani River */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-bhavani_river"
              checked={vectorVisible['bhavani_river'] ?? false}
              onChange={() => onVectorToggle('bhavani_river')}
            />
            <span style={{ width: 12, height: 3, background: '#0ea5e9', display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['bhavani_river'] ? 600 : 400 }}>
              〰 Bhavani River
            </span>
            <span style={{ fontSize: 9, color: '#16a34a', fontWeight: 600 }}>REAL</span>
          </div>

          {/* Bridges */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-bridges"
              checked={vectorVisible['bridges'] ?? false}
              onChange={() => onVectorToggle('bridges')}
            />
            <span style={{ width: 9, height: 9, background: '#f59e0b', border: '1px solid #78350f', transform: 'rotate(45deg)', display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['bridges'] ? 600 : 400 }}>
              ☲ Bridges / Crossings
            </span>
            <span style={{ fontSize: 9, color: '#b45309', fontWeight: 700 }}>20</span>
          </div>

          {/* Highlighted Settlements */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-settlements"
              checked={vectorVisible['settlements'] ?? false}
              onChange={() => onVectorToggle('settlements')}
            />
            <span style={{ width: 8, height: 8, background: '#94a3b8', borderRadius: '50%', display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['settlements'] ? 600 : 400 }}>
              🏘 Highlighted Settlements
            </span>
            <span style={{ fontSize: 9, color: '#64748b' }}>10</span>
          </div>

          {/* Critical Facilities */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-critical_facilities"
              checked={vectorVisible['critical_facilities'] ?? false}
              onChange={() => onVectorToggle('critical_facilities')}
            />
            <span style={{ width: 8, height: 8, background: '#ef4444', borderRadius: '50%', display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['critical_facilities'] ? 600 : 400 }}>
              🏥 Critical Facilities
            </span>
            <span style={{ fontSize: 9, color: '#64748b' }}>13</span>
          </div>

          {/* Road Exposure */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-road_exposure"
              checked={vectorVisible['road_exposure'] ?? false}
              onChange={() => onVectorToggle('road_exposure')}
            />
            <span style={{ width: 10, height: 2, background: '#64748b', display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['road_exposure'] ? 600 : 400 }}>
              🛣 Road Exposure
            </span>
            <span style={{ fontSize: 9, color: '#64748b' }}>243.8km</span>
          </div>
        </div>
      )}

      {/* ─── GROUP 3: RISK & HADR ─── */}
      <div
        className="collapsible-header"
        onClick={() => setRiskOpen(o => !o)}
        style={{ background: '#f8fafc', fontWeight: 700, color: '#b45309', borderTop: '1px solid #e2e8f0' }}
      >
        <span>⚠ 3. RISK & HADR</span>
        <span style={{ fontSize: 10 }}>{riskOpen ? '▲' : '▼'}</span>
      </div>
      {riskOpen && (
        <div style={{ padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
          {/* CWC Hazard Raster */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="raster-hazard_class"
              checked={rasterVisible['hazard_class'] ?? false}
              onChange={() => onRasterToggle('hazard_class')}
            />
            <span style={{ flex: 1, fontWeight: rasterVisible['hazard_class'] ? 600 : 400 }}>
              🎨 CWC H1–H6 Hazard Raster
            </span>
            <span style={{ fontSize: 9, color: '#ea580c', fontWeight: 600 }}>CWC</span>
          </div>

          {/* Response Zones Vector */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-response_zones"
              checked={vectorVisible['response_zones'] ?? false}
              onChange={() => onVectorToggle('response_zones')}
            />
            <span style={{ width: 9, height: 9, background: '#f59e0b', borderRadius: 2, display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['response_zones'] ? 600 : 400 }}>
              🛡 Response Sectors (Z1–Z6)
            </span>
            <span style={{ fontSize: 9, color: '#f59e0b', fontWeight: 700 }}>6</span>
          </div>
        </div>
      )}

      {/* ─── GROUP 4: EARTH OBSERVATION ─── */}
      <div
        className="collapsible-header"
        onClick={() => setEoOpen(o => !o)}
        style={{ background: '#f8fafc', fontWeight: 700, color: '#6b21a8', borderTop: '1px solid #e2e8f0' }}
      >
        <span>🛰 4. EARTH OBSERVATION</span>
        <span style={{ fontSize: 10 }}>{eoOpen ? '▲' : '▼'}</span>
      </div>
      {eoOpen && (
        <div style={{ padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
          {/* Historical Sentinel-1 */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-historical_flood"
              checked={vectorVisible['historical_flood'] ?? false}
              onChange={() => onVectorToggle('historical_flood')}
            />
            <span style={{ width: 9, height: 9, background: '#8b5cf6', borderRadius: 2, display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['historical_flood'] ? 600 : 400 }}>
              Historical Flood (Aug 2019)
            </span>
            <span style={{ fontSize: 9, color: '#8b5cf6', fontWeight: 600 }}>S1-SAR</span>
          </div>

          {/* Latest Candidate Water */}
          <div className="layer-row">
            <input
              type="checkbox"
              id="vec-latest_water_change"
              checked={vectorVisible['latest_water_change'] ?? false}
              onChange={() => onVectorToggle('latest_water_change')}
            />
            <span style={{ width: 9, height: 9, background: '#06b6d4', borderRadius: 2, display: 'inline-block' }} />
            <span style={{ flex: 1, fontWeight: vectorVisible['latest_water_change'] ? 600 : 400 }}>
              Latest Candidate Water
            </span>
            <span style={{ fontSize: 9, color: '#06b6d4', fontWeight: 600 }}>S1-SAR</span>
          </div>
        </div>
      )}

      {/* ─── Compact Legend Key ─── */}
      <div style={{ marginTop: 'auto', borderTop: '1px solid #e2e8f0', background: '#fafafa' }}>
        <div style={{ padding: '6px 12px 2px', fontSize: 10, fontWeight: 700, color: '#475569' }}>
          CWC Hazard Severity Levels
        </div>
        <div style={{ padding: '4px 12px 8px', display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {[
            { cls: 'H1', label: 'Generally safe (d<0.3m)', c: '#fefce8' },
            { cls: 'H2', label: 'Unsafe for small vehicles', c: '#fef9c3' },
            { cls: 'H3', label: 'Unsafe for vehicles & elderly', c: '#ffedd5' },
            { cls: 'H4', label: 'Unsafe for people & vehicles', c: '#fee2e2' },
            { cls: 'H5', label: 'Structural damage risk', c: '#fecaca' },
            { cls: 'H6', label: 'Structural failure / Collapse', c: '#e9d5ff' },
          ].map(h => (
            <div key={h.cls} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 9.5 }}>
              <div style={{ width: 10, height: 10, background: h.c, border: '1px solid #cbd5e1', borderRadius: 1, flexShrink: 0 }} />
              <span style={{ fontWeight: 700, color: '#334155', minWidth: 18 }}>{h.cls}</span>
              <span style={{ color: '#64748b', fontSize: 9 }}>{h.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
