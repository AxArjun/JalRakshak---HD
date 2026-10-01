// EOPanel – Earth Observation / Sentinel-1 SAR results
import { useApi } from '../hooks/useApi';
import { fetchEOSummary } from '../services/api';

const DERIV_COLOR: Record<string, string> = {
  DATA_DERIVED_OTSU:       '#dcfce7',
  DATA_DERIVED_HISTOGRAM:  '#d1fae5',
  PUBLISHED_LITERATURE:    '#dbeafe',
  MODEL_ASSUMPTION:        '#fef9c3',
  UNSUPPORTED:             '#fee2e2',
};
const DERIV_TEXT: Record<string, string> = {
  DATA_DERIVED_OTSU:       '#166534',
  DATA_DERIVED_HISTOGRAM:  '#166534',
  PUBLISHED_LITERATURE:    '#1e40af',
  MODEL_ASSUMPTION:        '#713f12',
  UNSUPPORTED:             '#991b1b',
};

export default function EOPanel() {
  const { data, loading, error } = useApi(fetchEOSummary);

  if (loading) return <div className="loading-state">Loading EO / remote-sensing data…</div>;
  if (error || !data) return (
    <div style={{ padding: 14 }}>
      <div className="scientific-warn">
        EO data not available via API. Check /api/remote-sensing/summary.
      </div>
    </div>
  );

  const thresholds = data.thresholds ?? {};

  return (
    <div style={{ padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>

      {/* Historical event */}
      <div>
        <div style={{ fontSize: 10.5, fontWeight: 600, color: '#475569', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Historical Flood Benchmark (Sentinel-1A SAR)
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
          <div className="stat-card" style={{ borderLeft: '3px solid #8b5cf6' }}>
            <div className="stat-label">Event Window</div>
            <div className="stat-value" style={{ fontSize: 12 }}>{data.historical_event ?? 'Aug 2019'}</div>
            <div className="stat-sub">{data.historical_date ?? '2019-08-10'} (Rel. Orbit 165)</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '3px solid #6d28d9' }}>
            <div className="stat-label">New Flood Area</div>
            <div className="stat-value">{(data.historical_flood_vector_km2 ?? data.historical_flood_area_km2 ?? 1.115).toFixed(3)} km²</div>
            <div className="stat-sub">Raster: {(data.historical_flood_area_km2 ?? 1.1925).toFixed(3)} km²</div>
          </div>
        </div>
        <div style={{ marginTop: 6, fontSize: 10, color: '#64748b' }}>
          <strong>M5 Intersection:</strong> 0.305 km² (27.35% of observed · 0.30% of M5 domain)
        </div>
        <div style={{ marginTop: 2, fontSize: 9, color: '#94a3b8', wordBreak: 'break-all' }}>
          Scene: {data.historical_scene_id ?? 'COPERNICUS/S1_GRD/S1A_IW_GRDH_1SDV_20190810T003943_20190810T004008_028500_033878_041D'}
        </div>
      </div>

      {/* Latest scene */}
      {data.latest_scene && (
        <div>
          <div style={{ fontSize: 10.5, fontWeight: 600, color: '#475569', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Latest Near-Real-Time Scene (Audited)
          </div>
          <div className="satellite-status-bar">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, fontSize: 11.5, color: '#0f172a' }}>
                {data.latest_scene.platform} (Orbit: {data.latest_scene.absolute_orbit ?? 4581})
              </span>
              <span className="badge badge-candidate">
                {data.latest_scene.flood_status?.replace(/_/g, ' ')}
              </span>
            </div>
            <div style={{ fontSize: 10, color: '#64748b' }}>
              {data.latest_scene.date} · {data.latest_scene.orbit_pass} · Rel. orbit {data.latest_scene.relative_orbit}
            </div>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>
              Mode: {data.latest_scene.mode} · Resolution: {data.latest_scene.resolution_m}m · Status: UNVERIFIED
            </div>
            <div style={{ fontSize: 9, color: '#cbd5e1', wordBreak: 'break-all', marginTop: 2 }}>
              ID: {data.latest_scene.scene_id}
            </div>
          </div>
        </div>
      )}

      {/* Monitoring status */}
      <div className="scientific-note">
        <strong>Monitoring status:</strong>{' '}
        {data.monitoring_status ?? 'HISTORICAL_BENCHMARK_ONLY'}
      </div>

      {/* Threshold audit table */}
      {Object.keys(thresholds).length > 0 && (
        <div>
          <div style={{ fontSize: 10.5, fontWeight: 600, color: '#475569', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Detection Threshold Audit
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10.5 }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={{ padding: '4px 8px', textAlign: 'left', color: '#64748b', fontSize: 9, fontWeight: 600, textTransform: 'uppercase' }}>Parameter</th>
                <th style={{ padding: '4px 4px', textAlign: 'right', color: '#64748b', fontSize: 9, fontWeight: 600, textTransform: 'uppercase' }}>Value</th>
                <th style={{ padding: '4px 8px', textAlign: 'left', color: '#64748b', fontSize: 9, fontWeight: 600, textTransform: 'uppercase' }}>Derivation</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(thresholds).map(([param, t]) => (
                <tr key={param} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '4px 8px', fontFamily: 'monospace', fontSize: 10, color: '#334155' }}>
                    {param}
                  </td>
                  <td style={{ padding: '4px 4px', textAlign: 'right', fontWeight: 600, color: '#0f172a' }}>
                    {typeof t.value === 'number' ? t.value.toFixed(1) : String(t.value)}
                  </td>
                  <td style={{ padding: '4px 8px' }}>
                    <span
                      style={{
                        padding: '1px 6px',
                        borderRadius: 8,
                        fontSize: 9,
                        fontWeight: 600,
                        background: DERIV_COLOR[t.class] ?? '#f1f5f9',
                        color: DERIV_TEXT[t.class] ?? '#334155',
                      }}
                    >
                      {t.class?.replace(/_/g, ' ')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Scientific disclaimer */}
      <div className="scientific-warn">
        Sentinel-1 thresholds are validated per M9 audit.
        Historical event: REAL observed flood (Aug 2019).
        M5 simulation scenario: HYPOTHETICAL — not linked to any observed breach.
      </div>
    </div>
  );
}
