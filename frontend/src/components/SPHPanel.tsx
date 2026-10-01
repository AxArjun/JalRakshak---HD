// SPHPanel – DualSPHysics near-field gauge results & M7 cross-solver analysis
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';
import { useApi } from '../hooks/useApi';
import { fetchSPHSummary } from '../services/api';

export default function SPHPanel() {
  const { data, loading, error } = useApi(fetchSPHSummary);

  if (loading) return <div className="loading-state">Loading SPH near-field data…</div>;
  if (error || !data) return (
    <div style={{ padding: 14 }}>
      <div className="scientific-warn">
        SPH near-field data not available via API.<br />
        Check backend /api/sph/summary endpoint.
      </div>
    </div>
  );

  const radarData = data.gauges?.map(g => ({
    subject: g.name.replace('Gauge ', 'G'),
    depth: g.peak_depth_m,
    velocity: g.peak_velocity_mps,
  })) ?? [];

  return (
    <div style={{ padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>

      <div className="scientific-note">
        <strong>2D Unit-Width Near-Field SPH Screening Model</strong><br />
        DualSPHysics v5.4 · Peak-state release · {data.total_particles ?? 10982} total particles (6,800 fluid + 4,182 boundary) · dp=1.0m · 600s
      </div>

      {/* Physics & Particle metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        <div className="stat-card" style={{ borderLeft: '3px solid #2563eb' }}>
          <div className="stat-label">Peak Depth (SPH)</div>
          <div className="stat-value">{data.max_depth_m?.toFixed(2) ?? '17.11'} m</div>
          <div className="stat-sub">P95: {data.p95_depth_m?.toFixed(2) ?? '12.57'}m</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #0891b2' }}>
          <div className="stat-label">Peak Velocity (SPH)</div>
          <div className="stat-value">{data.max_velocity_mps?.toFixed(2) ?? '34.78'} m/s</div>
          <div className="stat-sub">P95 bulk: {data.p95_velocity_mps?.toFixed(2) ?? '8.62'}m/s</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #16a34a' }}>
          <div className="stat-label">Front at 600s</div>
          <div className="stat-value">{data.front_position_at_600s_m?.toFixed(1) ?? '1280.4'} m</div>
          <div className="stat-sub">1500m: NOT_REACHED_WITHIN_600_S</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid #b91c1c' }}>
          <div className="stat-label">Peak Outflow (M4)</div>
          <div className="stat-value">{data.peak_outflow_m3s?.toLocaleString() ?? '18,742'}</div>
          <div className="stat-sub">m³/s (Froehlich width: 219.3m)</div>
        </div>
      </div>

      {/* Cross-Solver Audit Card */}
      <div className="stat-card" style={{ borderLeft: '3px solid #7c3aed', background: '#f8fafc' }}>
        <div className="stat-label" style={{ color: '#6d28d9', fontWeight: 700 }}>
          M7 Cross-Solver Audit & Coupling Status
        </div>
        <div style={{ fontSize: 11, color: '#334155', marginTop: 4 }}>
          <strong>Depth Trend:</strong> {data.depth_trend ?? 'PARTIALLY_CONSISTENT'}<br />
          <strong>Velocity Trend:</strong> {data.velocity_trend ?? 'DIVERGENT_TREND'}<br />
          <strong>Recommended Handoff:</strong> {data.recommended_future_handoff_candidate ?? '500 m'}<br />
          <strong>Direct Coupling Ready:</strong> {String(data.direct_coupling_ready ?? false)} (Status: {data.overall_coupling_readiness ?? 'NOT_READY'})
        </div>
      </div>

      {/* Gauge table */}
      <div>
        <div style={{ fontSize: 10.5, fontWeight: 600, color: '#475569', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Virtual Gauge Results
        </div>
        <table className="gauge-table">
          <thead>
            <tr>
              <th>Gauge</th>
              <th>Dist (m)</th>
              <th>Peak d (m)</th>
              <th>Peak u (m/s)</th>
              <th>Arr (s)</th>
            </tr>
          </thead>
          <tbody>
            {data.gauges?.map(g => (
              <tr key={g.gauge_id}>
                <td>{g.name}</td>
                <td>{g.distance_m.toFixed(0)}</td>
                <td style={{ color: '#1d4ed8' }}>{g.peak_depth_m.toFixed(2)}</td>
                <td style={{ color: '#0891b2' }}>{g.peak_velocity_mps.toFixed(2)}</td>
                <td>{g.arrival_time_s >= 9000 ? 'N/R' : g.arrival_time_s.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Radar chart */}
      {radarData.length > 2 && (
        <div>
          <div style={{ fontSize: 10.5, fontWeight: 600, color: '#475569', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Peak Depth Profile
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
              <Radar dataKey="depth" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.3} name="Depth (m)" />
              <Tooltip contentStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
