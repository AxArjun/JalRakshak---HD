import { useState, useEffect } from 'react';
import type { TimestepImpactReport } from '../types/dashboard';
import { fetchImpactReport } from '../services/api';

interface Props {
  frameIdx: number;
}

export default function ImpactReportTab({ frameIdx }: Props) {
  const [report, setReport] = useState<TimestepImpactReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchImpactReport(frameIdx)
      .then((data) => {
        if (!cancelled) {
          setReport(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [frameIdx]);

  const openReportHtml = (url: string) => {
    window.open(url, '_blank');
  };

  if (loading && !report) {
    return <div className="loading-state" style={{ padding: 12 }}>Loading modeled impact data…</div>;
  }

  if (!report) {
    return <div className="scientific-warn" style={{ margin: 10 }}>Modeled impact data unavailable.</div>;
  }

  const imp = report.current_impact;
  const bldg = report.building_vulnerability_screening;
  const evac = report.evacuation_screening.arrival_windows;
  const next60 = report.next_60_minutes_window;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '4px 0' }}>
      
      {/* Current Timestep Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          border: '1px solid #334155',
          borderRadius: 6,
          padding: '8px 12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
        }}
      >
        <div>
          <div style={{ fontSize: 9, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
            Modeled Impact Timeline
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#38bdf8' }}>
            {report.formatted_time}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 4,
              background: imp.highest_hazard_reached === 'H6' ? '#7f1d1d' : '#1e3a8a',
              color: imp.highest_hazard_reached === 'H6' ? '#fca5a5' : '#93c5fd',
              border: '1px solid',
              borderColor: imp.highest_hazard_reached === 'H6' ? '#b91c1c' : '#3b82f6',
            }}
          >
            Max: {imp.highest_hazard_reached}
          </span>
        </div>
      </div>

      {/* Current Modeled Impact Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        <div className="stat-card">
          <div className="stat-label">Inundated Footprint</div>
          <div className="stat-value" style={{ color: '#2563eb', fontSize: 15 }}>
            {imp.inundated_area_km2.toFixed(2)} km²
          </div>
          <div className="stat-sub">Model Wet Domain</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Exposed Population</div>
          <div className="stat-value" style={{ color: '#0f172a', fontSize: 15 }}>
            {imp.worldpop_exposed.toLocaleString()}
          </div>
          <div className="stat-sub">GHSL: {imp.ghsl_exposed.toLocaleString()}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        <div className="stat-card">
          <div className="stat-label">Buildings Exposed</div>
          <div className="stat-value" style={{ color: '#dc2626', fontSize: 15 }}>
            {imp.buildings_exposed.toLocaleString()}
          </div>
          <div className="stat-sub">H5/H6: {(bldg.h5_high_structural_vulnerability + bldg.h6_vulnerable_to_structural_failure).toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Lifelines Reached</div>
          <div className="stat-value" style={{ color: '#d97706', fontSize: 15 }}>
            {imp.bridges_exposed} / {imp.total_bridges} Bridges
          </div>
          <div className="stat-sub">Roads: {imp.roads_exposed_km.toFixed(1)} km | Fac: {imp.critical_facilities_exposed}</div>
        </div>
      </div>

      {/* Building Vulnerability Screening */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '8px 10px' }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#334155', textTransform: 'uppercase', marginBottom: 4 }}>
          Building Vulnerability Screening (H1–H6)
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 10.5 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#64748b' }}>H1 / H2 (Low/Medium):</span>
            <span style={{ fontWeight: 600 }}>{bldg.h1_h2_low_medium.toLocaleString()}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#64748b' }}>H3 / H4 (High Hazard):</span>
            <span style={{ fontWeight: 600 }}>{bldg.h3_h4_high.toLocaleString()}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#ea580c' }}>H5 (High Structural Vulnerability):</span>
            <span style={{ fontWeight: 700, color: '#ea580c' }}>{bldg.h5_high_structural_vulnerability.toLocaleString()}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#dc2626' }}>H6 (Vulnerable to Failure):</span>
            <span style={{ fontWeight: 700, color: '#dc2626' }}>{bldg.h6_vulnerable_to_structural_failure.toLocaleString()}</span>
          </div>
        </div>
        <div style={{ fontSize: 9, color: '#94a3b8', marginTop: 4, fontStyle: 'italic' }}>
          *Classification indicates hydrodynamic potential for structural failure.
        </div>
      </div>

      {/* Arrival-Based Response Lead Time Windows */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '8px 10px' }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#334155', textTransform: 'uppercase', marginBottom: 4 }}>
          Modeled Response / Lead Time Windows
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #e2e8f0', paddingBottom: 2 }}>
            <span style={{ fontWeight: 600, color: '#dc2626' }}>Already Reached (&le; T):</span>
            <span style={{ fontWeight: 700 }}>{evac.already_reached.worldpop_exposed.toLocaleString()} pop · {evac.already_reached.buildings_exposed} bldgs</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #e2e8f0', paddingBottom: 2 }}>
            <span style={{ fontWeight: 600, color: '#ea580c' }}>Next 30 Minutes:</span>
            <span style={{ fontWeight: 600 }}>{evac.next_30_minutes.worldpop_exposed.toLocaleString()} pop · {evac.next_30_minutes.buildings_exposed} bldgs</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #e2e8f0', paddingBottom: 2 }}>
            <span style={{ fontWeight: 600, color: '#d97706' }}>30 to 60 Minutes:</span>
            <span style={{ fontWeight: 600 }}>{evac.thirty_to_sixty_minutes.worldpop_exposed.toLocaleString()} pop · {evac.thirty_to_sixty_minutes.buildings_exposed} bldgs</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 600, color: '#2563eb' }}>1 to 2 Hours:</span>
            <span style={{ fontWeight: 600 }}>{evac.one_to_two_hours.worldpop_exposed.toLocaleString()} pop · {evac.one_to_two_hours.buildings_exposed} bldgs</span>
          </div>
        </div>
        <div style={{ fontSize: 8.5, color: '#94a3b8', marginTop: 4 }}>
          Decision-support guidance derived from arrival times, not an official evacuation order.
        </div>
      </div>

      {/* Next 60 Minutes Forecast Delta */}
      <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: '8px 10px' }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#166534', textTransform: 'uppercase', marginBottom: 3 }}>
          ⏱ Next 60 Minutes Modeled Delta
        </div>
        <div style={{ fontSize: 10.5, color: '#14532d', display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div><strong>+{next60.additional_inundated_area_km2.toFixed(2)} km²</strong> area · <strong>+{next60.additional_worldpop.toLocaleString()}</strong> population</div>
          <div><strong>+{next60.additional_buildings}</strong> buildings · <strong>+{next60.additional_roads_km.toFixed(1)} km</strong> roads</div>
          {next60.bridges_entering_flood.length > 0 && (
            <div style={{ fontSize: 9.5, color: '#b45309' }}>
              Bridges entering flood: {next60.bridges_entering_flood.join(', ')}
            </div>
          )}
        </div>
      </div>

      {/* Real Affected Places & Modeled Priority */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '8px 10px' }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#334155', textTransform: 'uppercase', marginBottom: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>🏘 Affected Places & Priority</span>
          <span style={{ fontSize: 9, color: '#64748b', fontWeight: 600 }}>{report.affected_places ? report.affected_places.filter(p => p.affected).length : 6} In Corridor</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 10.5 }}>
          {(report.affected_places || []).filter(p => p.affected).slice(0, 5).map(p => {
            const isReached = p.earliest_arrival_hr !== null && report.time_hr >= p.earliest_arrival_hr;
            const leadTime = p.earliest_arrival_hr !== null ? Math.max(0, p.earliest_arrival_hr - report.time_hr) : 0;
            return (
              <div key={p.place_name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px dashed #e2e8f0', paddingBottom: 2 }}>
                <div>
                  <div style={{ fontWeight: 700, color: '#0f172a' }}>{p.place_name}</div>
                  <div style={{ fontSize: 9, color: '#64748b' }}>Arr: {p.earliest_arrival_hr?.toFixed(2)}h · {p.hazard_class}</div>
                </div>
                <span
                  style={{
                    fontSize: 9,
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: 3,
                    background: isReached ? '#fee2e2' : leadTime <= 0.5 ? '#ffedd5' : '#dbeafe',
                    color: isReached ? '#991b1b' : leadTime <= 0.5 ? '#9a3412' : '#1e40af',
                  }}
                >
                  {isReached ? 'REACHED' : `LEAD: ${leadTime.toFixed(1)}h`}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Report Generation Action Buttons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
        <button
          onClick={() => openReportHtml(`/api/reports/impact/${frameIdx}/html`)}
          style={{
            background: '#2563eb',
            color: '#ffffff',
            border: 'none',
            borderRadius: 5,
            padding: '8px 12px',
            fontSize: 11,
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            boxShadow: '0 2px 4px rgba(37,99,235,0.2)',
          }}
        >
          📄 View Current Situation Report ({report.formatted_time})
        </button>

        <button
          onClick={() => openReportHtml('/api/reports/final/html')}
          style={{
            background: '#0f172a',
            color: '#38bdf8',
            border: '1px solid #334155',
            borderRadius: 5,
            padding: '7px 12px',
            fontSize: 11,
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
          }}
        >
          📑 View Final Simulation Report (30h)
        </button>
      </div>

    </div>
  );
}
