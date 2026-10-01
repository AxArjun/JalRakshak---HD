// SimulationPanel – Hydrodynamic Timeline Scrubber & Real-Time Impact Report
import { useState, useEffect, useRef, useCallback } from 'react';
import { useApi } from '../hooks/useApi';
import { fetchSimulationMeta, getStaticFrameUrl } from '../services/api';
import ImpactReportTab from './ImpactReportTab';

interface Props {
  onFrame: (url: string, bounds: [[number, number], [number, number]]) => void;
  resetKey?: number;
  onEnsureFloodVisible?: () => void;
}

const SIM_BOUNDS: [[number, number], [number, number]] = [
  [11.359179, 77.111197],
  [11.57997,  77.423552]
];

export default function SimulationPanel({ onFrame, resetKey, onEnsureFloodVisible }: Props) {

  const { data: meta, loading } = useApi(fetchSimulationMeta);

  const [activeTab, setActiveTab] = useState<'timeline' | 'impact'>('timeline');
  const [frameIdx, setFrameIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 0.5x, 1x, 2x, 4x
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const totalFrames = meta?.total_frames ?? 181;

  const goToFrame = useCallback((idx: number) => {
    const clamped = Math.max(0, Math.min(idx, totalFrames - 1));
    setFrameIdx(clamped);
    onFrame(getStaticFrameUrl(clamped), SIM_BOUNDS);
  }, [totalFrames, onFrame]);

  // Handle explicit Reset / Demo trigger
  useEffect(() => {
    if (!resetKey) return;
    setFrameIdx(0);
    setPlaying(false);
    setSpeed(1);
    setActiveTab('timeline');
    onFrame(getStaticFrameUrl(0), SIM_BOUNDS);
  }, [resetKey, onFrame]);


  // Auto-play interval handling with speed multipliers
  useEffect(() => {
    if (playing) {
      const baseMs = 250;
      const ms = Math.round(baseMs / speed);
      intervalRef.current = setInterval(() => {
        setFrameIdx(prev => {
          const next = prev + 1;
          if (next >= totalFrames) {
            setPlaying(false);
            return totalFrames - 1;
          }
          onFrame(getStaticFrameUrl(next), SIM_BOUNDS);
          return next;
        });
      }, ms);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, speed, totalFrames, onFrame]);

  // Exact Elapsed Time formatted as T + HH:MM
  const totalSimSeconds = frameIdx * 600; // 600s per timestep
  const hours = Math.floor(totalSimSeconds / 3600);
  const minutes = Math.floor((totalSimSeconds % 3600) / 60);
  const formattedTime = `T + ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;

  if (loading) return <div className="loading-state">Loading simulation metadata…</div>;

  return (
    <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 8, userSelect: 'none' }}>

      {/* Panel Top Tabs: TIMELINE vs IMPACT REPORT */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 4,
          background: '#f1f5f9',
          padding: 3,
          borderRadius: 6,
          border: '1px solid #e2e8f0',
        }}
      >
        <button
          onClick={() => setActiveTab('timeline')}
          style={{
            padding: '6px 0',
            fontSize: 11,
            fontWeight: 700,
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            background: activeTab === 'timeline' ? '#ffffff' : 'transparent',
            color: activeTab === 'timeline' ? '#2563eb' : '#64748b',
            boxShadow: activeTab === 'timeline' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
          }}
        >
          ⏱ TIMELINE
        </button>
        <button
          onClick={() => setActiveTab('impact')}
          style={{
            padding: '6px 0',
            fontSize: 11,
            fontWeight: 700,
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            background: activeTab === 'impact' ? '#ffffff' : 'transparent',
            color: activeTab === 'impact' ? '#2563eb' : '#64748b',
            boxShadow: activeTab === 'impact' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
          }}
        >
          📊 IMPACT REPORT
        </button>
      </div>

      {activeTab === 'timeline' ? (
        <>
          {/* Scenario & Solver Provenance Badge */}
          <div className="scientific-warn" style={{ padding: '6px 8px', fontSize: 10 }}>
            <strong>HYPOTHETICAL BREACH SCREENING (BHV_BASE)</strong><br />
            <span style={{ color: '#475569' }}>
              D-Flow FM 2D · 181 frames (600s interval) · 108,000 s (30 hr).
            </span>
          </div>

          {/* Current Elapsed Time Display Card */}
          <div
            style={{
              background: 'linear-gradient(135deg, #0d1b2e 0%, #1e293b 100%)',
              borderRadius: 6,
              padding: '8px 12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              border: '1px solid #334155',
              boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
            }}
          >
            <div>
              <div style={{ fontSize: 8.5, color: '#94a3b8', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>
                Simulation Elapsed Time
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#38bdf8', fontVariantNumeric: 'tabular-nums' }}>
                {formattedTime}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 8.5, color: '#94a3b8', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>
                Solver Timestep
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc' }}>
                {frameIdx + 1} / {totalFrames}
              </div>
            </div>
          </div>

          {/* Timeline Scrubber */}
          <div>
            <input
              type="range"
              min={0}
              max={totalFrames - 1}
              step={1}
              value={frameIdx}
              onChange={e => goToFrame(parseInt(e.target.value, 10))}
              className="timeline-slider"
              style={{ width: '100%', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 8.5, color: '#94a3b8', marginTop: 2 }}>
              <span>T+00:00 (Breach)</span>
              <span>T+15:00</span>
              <span>T+30:00 (End)</span>
            </div>
          </div>

          {/* Playback Controls & Speed Selectors */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <button className="map-btn" onClick={() => goToFrame(0)} title="Rewind to T+00:00">⏮</button>
            <button className="map-btn" onClick={() => goToFrame(frameIdx - 6)} title="Back 1 Hour (6 frames)">◀◀</button>
            <button className="map-btn" onClick={() => goToFrame(frameIdx - 1)} title="Step Previous Frame">◀</button>
            <button
              className={`map-btn ${playing ? 'playing' : ''}`}
              onClick={() => {
                setPlaying(p => {
                  const nextState = !p;
                  if (nextState) {
                    onEnsureFloodVisible?.();
                  }
                  return nextState;
                });
              }}
              style={{
                width: 34,
                height: 34,
                fontSize: 15,
                background: playing ? '#ea580c' : '#2563eb',
                color: 'white',
                borderColor: playing ? '#c2410c' : '#1d4ed8',
              }}
              title={playing ? 'Pause' : 'Play'}
            >
              {playing ? '⏸' : '▶'}
            </button>
            <button className="map-btn" onClick={() => goToFrame(frameIdx + 1)} title="Step Next Frame">▶</button>
            <button className="map-btn" onClick={() => goToFrame(frameIdx + 6)} title="Forward 1 Hour (6 frames)">▶▶</button>
            <button className="map-btn" onClick={() => goToFrame(totalFrames - 1)} title="Jump to T+30:00">⏭</button>

            <div style={{ flex: 1 }} />

            {/* Speed Selector Buttons: 0.5x, 1x, 2x, 4x */}
            <div style={{ display: 'flex', gap: 2 }}>
              {[0.5, 1, 2, 4].map(s => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  style={{
                    padding: '2px 5px',
                    fontSize: 9,
                    fontWeight: 700,
                    border: '1px solid',
                    borderRadius: 3,
                    cursor: 'pointer',
                    background: speed === s ? '#2563eb' : '#f8fafc',
                    color: speed === s ? 'white' : '#475569',
                    borderColor: speed === s ? '#2563eb' : '#cbd5e1',
                  }}
                >
                  {s}×
                </button>
              ))}
            </div>
          </div>

          {/* Key Authoritative Scientific Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5 }}>
            <div className="stat-card">
              <div className="stat-label">Model Domain</div>
              <div className="stat-value" style={{ color: '#475569', fontSize: 13 }}>
                {meta?.domain_area_km2?.toFixed(2) ?? '818.37'} km²
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Max Inundated Area</div>
              <div className="stat-value" style={{ color: '#2563eb', fontSize: 13 }}>
                {meta?.max_inundated_area_km2?.toFixed(2) ?? '101.29'} km²
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 5 }}>
            <div className="stat-card">
              <div className="stat-label">Peak Depth</div>
              <div className="stat-value" style={{ color: '#1d4ed8', fontSize: 13 }}>
                {(meta?.solver_max_depth_m ?? meta?.peak_depth_m ?? 22.02).toFixed(2)} m
              </div>
              <div className="stat-sub">P95: {meta?.p95_depth_m ?? '12.72'}m</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Peak Velocity</div>
              <div className="stat-value" style={{ color: '#0891b2', fontSize: 13 }}>
                {(meta?.solver_max_velocity_mps ?? meta?.peak_velocity_mps ?? 11.79).toFixed(2)} m/s
              </div>
              <div className="stat-sub">P95: {meta?.p95_velocity_mps ?? '4.27'}m/s</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Peak Q</div>
              <div className="stat-value" style={{ color: '#dc2626', fontSize: 13 }}>
                18,742 m³/s
              </div>
              <div className="stat-sub">Froehlich</div>
            </div>
          </div>
        </>
      ) : (
        <ImpactReportTab frameIdx={frameIdx} />
      )}

    </div>
  );
}
