// Header bar – project identity, location subtitle, DEMO mode, Reset Map, panel toggles & mode switcher
import type { DashboardMode, SiteItem } from '../types/dashboard';

interface Props {
  mode: DashboardMode;
  onMode: (m: DashboardMode) => void;
  apiOk: boolean;
  currentSite: string;
  onSelectSite: (siteId: string) => void;
  sites: SiteItem[];
  leftPanelOpen: boolean;
  onToggleLeftPanel: () => void;
  rightPanelOpen: boolean;
  onToggleRightPanel: () => void;
  onResetMap: () => void;
  onDemoMode: () => void;
}

const MODES: { id: DashboardMode; label: string; icon: string }[] = [
  { id: 'simulation', label: 'Simulation', icon: '▶' },
  { id: 'hadr',       label: 'HADR Exposure', icon: '⚠' },
  { id: 'sph',        label: 'Near-Field SPH', icon: '〜' },
  { id: 'eo',         label: 'Earth Observation', icon: '🛰' },
];

export default function Header({
  mode, onMode, apiOk, currentSite, onSelectSite, sites,
  leftPanelOpen, onToggleLeftPanel, rightPanelOpen, onToggleRightPanel,
  onResetMap, onDemoMode
}: Props) {
  const isBhavani = currentSite === 'bhavanisagar';
  const locationSubtitle = isBhavani
    ? 'Bhavanisagar Dam · Lower Bhavani River'
    : 'Hirakud Dam · Mahanadi River Basin';

  return (
    <header className="header-bar">
      {/* 1. Brand & Location */}
      <div className="header-brand-section">
        <div className="header-logo-icon">
          💧
        </div>
        <div className="header-brand-text">
          <div className="header-title-row">
            <span className="header-brand-title">JalRakshak-HD</span>
            <span className="header-badge-gis">GIS CENTRE</span>
          </div>
          <div className="header-subtitle">
            {locationSubtitle}
          </div>
        </div>
      </div>

      {/* 2. Site Selector Dropdown */}
      <div className="header-site-container">
        <select
          value={currentSite}
          onChange={(e) => onSelectSite(e.target.value)}
          className="header-site-select"
          title="Select Active Dam Site"
        >
          {sites.map((s) => (
            <option key={s.site_id} value={s.site_id}>
              {s.site_id === 'bhavanisagar' ? 'Bhavanisagar (Validated M1–M10)' : 'Hirakud (Portability Proof)'}
            </option>
          ))}
        </select>
      </div>

      {/* 3. Quick Action Presets: DEMO MODE & RESET */}
      <div className="header-quick-actions">
        <button
          onClick={onDemoMode}
          title="Deterministic SIH Demo Preset (Shortcut: D)"
          className="btn-demo-mode"
        >
          ★ DEMO MODE
        </button>

        <button
          onClick={onResetMap}
          title="Reset Dashboard & Map (Shortcut: R)"
          className="btn-reset-map"
        >
          ↺ Reset
        </button>
      </div>

      {/* 4. Panel Visibility Toggles */}
      <div className="header-panel-toggles">
        <button
          onClick={onToggleLeftPanel}
          title={leftPanelOpen ? 'Collapse Layer Panel' : 'Expand Layer Panel'}
          className={`btn-panel-toggle ${leftPanelOpen ? 'active' : ''}`}
        >
          ◨ Layers
        </button>

        <button
          onClick={onToggleRightPanel}
          title={rightPanelOpen ? 'Collapse Analysis Panel' : 'Expand Analysis Panel'}
          className={`btn-panel-toggle ${rightPanelOpen ? 'active' : ''}`}
        >
          ◧ Controls
        </button>
      </div>

      {/* 5. Optional Middle Disclaimer Badge (visible only on large ultra-wide screens >= 1600px) */}
      <div className="header-disclaimer-pill">
        ⚠ HYPOTHETICAL STRESS-TEST — NOT AN OPERATIONAL WARNING
      </div>

      {/* 6. Four Primary Mode Tabs (ALWAYS fully visible, never clipped) */}
      <nav className="header-mode-nav" aria-label="Dashboard Primary Modes">
        {MODES.map(m => {
          const isActive = mode === m.id;
          return (
            <button
              key={m.id}
              className={`mode-nav-btn ${isActive ? 'active' : ''}`}
              onClick={() => onMode(m.id)}
              title={`Switch to ${m.label} Mode`}
              id={`nav-mode-${m.id}`}
            >
              <span className="mode-nav-icon">{m.icon}</span>
              <span className="mode-nav-label">{m.label}</span>
            </button>
          );
        })}
      </nav>

      {/* 7. Live API Health Indicator */}
      <div className="header-health-badge">
        <div className={`health-dot ${apiOk ? 'online' : 'offline'}`} />
        <span className="health-text">{apiOk ? 'LIVE' : 'DOWN'}</span>
      </div>
    </header>
  );
}

