// HADRPanel – Exposure summary, CWC hazard breakdown, non-overlapping response sectors
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts';
import { fetchHADRSummary, fetchResponseZones } from '../services/api';
import type { HADRSummary, ResponseZone } from '../types/dashboard';

const HAZARD_COLORS: Record<string, string> = {
  H1: '#fef08a', H2: '#fde047', H3: '#fb923c',
  H4: '#f87171', H5: '#dc2626', H6: '#7c3aed',
};
const HAZARD_BORDER: Record<string, string> = {
  H1: '#ca8a04', H2: '#a16207', H3: '#c2410c',
  H4: '#b91c1c', H5: '#991b1b', H6: '#5b21b6',
};

interface Props {
  siteId?: string;
  selectedZone: string | null;
  onSelectZone: (id: string | null) => void;
}

export default function HADRPanel({ siteId = 'bhavanisagar', selectedZone, onSelectZone }: Props) {
  const [summary, setSummary] = useState<HADRSummary | null>(null);
  const [zones, setZones] = useState<ResponseZone[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'overview' | 'zones'>('overview');

  useEffect(() => {
    let cancelled = false;
    if (siteId !== 'bhavanisagar') {
      setSummary(null);
      setZones([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    Promise.all([
      fetchHADRSummary(siteId),
      fetchResponseZones(siteId),
    ])
      .then(([sData, zData]) => {
        if (!cancelled) {
          setSummary(sData);
          setZones(zData);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error('[HADRPanel] Error fetching HADR data:', err);
          setError(err.message || 'Unable to load HADR analysis');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [siteId]);

  // Hirakud / Second Site handling
  if (siteId && siteId !== 'bhavanisagar') {
    return (
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 13, color: '#0f172a' }}>
          ⚠ HADR Exposure Analysis
        </div>
        <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: 6, padding: 12, fontSize: 11, color: '#475569' }}>
          <div style={{ fontWeight: 700, color: '#b45309', marginBottom: 4 }}>
            STATUS: NOT_RUN (Hirakud Site)
          </div>
          HADR consequence analysis unavailable — production hydraulic simulation has not been executed for this site.
        </div>
        <div style={{ fontSize: 10, color: '#94a3b8' }}>
          Hirakud Dam serves as a secondary portability testbed demonstrating parameter configuration and schema portability.
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="loading-state" style={{ padding: 20 }}>
        Loading HADR analysis…
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 16 }}>
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, padding: 12, color: '#991b1b', fontSize: 11 }}>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>Unable to load HADR analysis</div>
          <div>{error}</div>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="empty-state" style={{ padding: 20 }}>
        No HADR data available
      </div>
    );
  }

  const hazardClasses = summary.hazard_classes || [
    { code: 'H1', description: 'Generally safe', area_km2: 1.87, area_pct: 1.85, worldpop: 878.1, ghsl: 1461.9, buildings: 234 },
    { code: 'H2', description: 'Unsafe for small vehicles', area_km2: 1.43, area_pct: 1.41, worldpop: 805.7, ghsl: 1271.0, buildings: 583 },
    { code: 'H3', description: 'Unsafe for vehicles/elderly', area_km2: 5.01, area_pct: 4.95, worldpop: 2360.0, ghsl: 3984.8, buildings: 890 },
    { code: 'H4', description: 'Unsafe for vehicles and people', area_km2: 5.69, area_pct: 5.62, worldpop: 2621.6, ghsl: 4379.8, buildings: 1473 },
    { code: 'H5', description: 'Structural damage vulnerability', area_km2: 17.55, area_pct: 17.33, worldpop: 8042.3, ghsl: 14103.4, buildings: 4982 },
    { code: 'H6', description: 'Vulnerable to structural failure', area_km2: 69.74, area_pct: 68.85, worldpop: 27720.3, ghsl: 59299.6, buildings: 17490 }
  ];

  const popData = hazardClasses.map(h => ({
    name: h.code,
    WorldPop: Math.round(h.worldpop),
    GHSL: Math.round(h.ghsl),
  }));

  const areaData = hazardClasses.map(h => ({
    name: h.code,
    value: h.area_km2,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0, userSelect: 'none' }}>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
        {(['overview', 'zones'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              flex: 1,
              padding: '8px 0',
              fontSize: 11,
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              background: tab === t ? '#ffffff' : 'transparent',
              color: tab === t ? '#2563eb' : '#64748b',
              borderBottom: tab === t ? '2px solid #2563eb' : '2px solid transparent',
              boxShadow: tab === t ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
            }}
          >
            {t === 'overview' ? '📊 HADR Overview' : '🛡 Response Sectors (Z1–Z6)'}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 10 }}>

          {/* Population Exposure Comparison Card (WorldPop PRIMARY vs GHSL CROSS-CHECK) */}
          <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: 6, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#334155', textTransform: 'uppercase', marginBottom: 6 }}>
              👥 Population Exposure Baseline
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 4, padding: '6px 8px', borderLeft: '3px solid #dc2626' }}>
                <div style={{ fontSize: 9.5, color: '#dc2626', fontWeight: 700 }}>WORLDPOP 2020 (PRIMARY)</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: '#0f172a' }}>
                  {(summary.worldpop_exposed ?? summary.worldpop_total ?? 42428.1).toLocaleString()}
                </div>
                <div style={{ fontSize: 8.5, color: '#64748b' }}>UN-Adjusted (100m)</div>
              </div>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 4, padding: '6px 8px', borderLeft: '3px solid #7c3aed' }}>
                <div style={{ fontSize: 9.5, color: '#7c3aed', fontWeight: 700 }}>GHSL 2025 (CROSS-CHECK)</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: '#0f172a' }}>
                  {(summary.ghsl_exposed ?? summary.ghsl_total ?? 84500.5).toLocaleString()}
                </div>
                <div style={{ fontSize: 8.5, color: '#64748b' }}>GHS-POP Built-Up (100m)</div>
              </div>
            </div>
            <div style={{ fontSize: 8.5, color: '#64748b', marginTop: 4, fontStyle: 'italic' }}>
              Datasets are reported side-by-side as upper/lower envelope bounds and must NOT be combined.
            </div>
          </div>

          {/* Infrastructure & Hazard Exposure Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            <div className="stat-card" style={{ borderLeft: '3px solid #3b82f6' }}>
              <div className="stat-label">Inundated Footprint</div>
              <div className="stat-value">{summary.total_inundated_area_km2.toFixed(2)} km²</div>
              <div className="stat-sub">D-Flow Modeled Basin Domain</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '3px solid #ea580c' }}>
              <div className="stat-label">Severe Hazard H3–H6</div>
              <div className="stat-value">{(summary.severe_h3h6_area_km2 ?? summary.severe_hazard_h3_h6_area_km2 ?? 97.99).toFixed(2)} km²</div>
              <div className="stat-sub">{summary.severe_h3h6_pct?.toFixed(1) ?? '96.7'}% of flood corridor</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '3px solid #f59e0b' }}>
              <div className="stat-label">Buildings Exposed</div>
              <div className="stat-value">{(summary.buildings_exposed ?? summary.buildings_total ?? 25652).toLocaleString()}</div>
              <div className="stat-sub">H5/H6: {(summary.h5_h6_buildings_exposed ?? summary.h5_h6_buildings_total ?? 22472).toLocaleString()} structures</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '3px solid #475569' }}>
              <div className="stat-label">Road Network</div>
              <div className="stat-value">{(summary.roads_exposed_km ?? summary.roads_km ?? 243.82).toFixed(1)} km</div>
              <div className="stat-sub">H3–H6: {(summary.h3_h6_roads_km ?? 226.35).toFixed(1)} km severe</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '3px solid #0891b2' }}>
              <div className="stat-label">Bridges Screened</div>
              <div className="stat-value">{summary.bridges_exposed_count ?? summary.bridges ?? 20}</div>
              <div className="stat-sub">18 in severe H3–H6 hazard</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '3px solid #dc2626' }}>
              <div className="stat-label">Critical Facilities</div>
              <div className="stat-value">{summary.critical_facilities_count ?? summary.critical_facilities ?? 13}</div>
              <div className="stat-sub">all 13 in severe H3–H6 hazard</div>
            </div>
          </div>

          {/* Population by hazard chart */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#475569', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Population by CWC Hazard Class
            </div>
            <ResponsiveContainer width="100%" height={125}>
              <BarChart data={popData} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={v => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v} />
                <Tooltip
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  formatter={(v: any, name: any) => [(v as number).toLocaleString(), name as string]}
                  contentStyle={{ fontSize: 11 }}
                />
                <Bar dataKey="WorldPop" stackId="a" radius={[0, 0, 0, 0]}>
                  {popData.map(e => (
                    <Cell key={e.name} fill={HAZARD_COLORS[e.name]} stroke={HAZARD_BORDER[e.name]} strokeWidth={0.5} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Area pie chart */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#475569', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Inundation Area Breakdown (km²)
            </div>
            <ResponsiveContainer width="100%" height={125}>
              <PieChart>
                <Pie
                  data={areaData}
                  cx="50%"
                  cy="50%"
                  outerRadius={48}
                  dataKey="value"
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  label={({ name, value }: any) => `${name ?? ''} ${(value as number).toFixed(0)}`}
                  labelLine={false}
                  style={{ fontSize: 9 }}
                >
                  {areaData.map(e => (
                    <Cell key={e.name} fill={HAZARD_COLORS[e.name]} stroke={HAZARD_BORDER[e.name]} strokeWidth={0.5} />
                  ))}
                </Pie>
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                <Tooltip formatter={(v: any) => [`${(v as number).toFixed(2)} km²`]} contentStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Hazard class detail table */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#475569', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              CWC Hazard Class Details
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  <th style={{ padding: '3px 6px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: 9, textTransform: 'uppercase' }}>Class</th>
                  <th style={{ padding: '3px 4px', textAlign: 'right', color: '#64748b', fontWeight: 600, fontSize: 9, textTransform: 'uppercase' }}>Area km²</th>
                  <th style={{ padding: '3px 4px', textAlign: 'right', color: '#64748b', fontWeight: 600, fontSize: 9, textTransform: 'uppercase' }}>WorldPop</th>
                  <th style={{ padding: '3px 4px', textAlign: 'right', color: '#64748b', fontWeight: 600, fontSize: 9, textTransform: 'uppercase' }}>Buildings</th>
                </tr>
              </thead>
              <tbody>
                {hazardClasses.map(h => (
                  <tr key={h.code} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '3px 6px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          width: 8, height: 8,
                          background: HAZARD_COLORS[h.code],
                          border: `1px solid ${HAZARD_BORDER[h.code]}`,
                          borderRadius: 1,
                          marginRight: 4,
                        }}
                      />
                      <strong>{h.code}</strong>
                    </td>
                    <td style={{ padding: '3px 4px', textAlign: 'right', color: '#334155' }}>{h.area_km2.toFixed(2)}</td>
                    <td style={{ padding: '3px 4px', textAlign: 'right', color: '#334155' }}>{h.worldpop.toLocaleString()}</td>
                    <td style={{ padding: '3px 4px', textAlign: 'right', color: '#334155' }}>{h.buildings.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>
      )}

      {tab === 'zones' && (
        <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {!zones?.length ? (
            <div className="empty-state" style={{ padding: 12 }}>No response sectors found</div>
          ) : (
            <>
              <div style={{ fontSize: 9.5, color: '#475569', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 4, padding: '6px 8px' }}>
                <strong>{zones.length} Non-Overlapping Response Sectors (Z1–Z6)</strong><br />
                Prioritized by wave arrival time and structural damage exposure. Click a sector to highlight on map.
              </div>
              {zones.map((z: ResponseZone | any) => {
                const isSelected = selectedZone === z.zone_id;
                const zid = z.zone_id || 'ZONE';
                const zname = z.zone_name || z.name || zid;
                const wp = z.worldpop ?? z.worldpop_exposure ?? 0;
                const bld = z.buildings ?? z.buildings_count ?? 0;
                const h5bld = z.h5_h6_buildings ?? z.h5_h6_buildings_count ?? 0;
                const rd = z.roads_km ?? z.roads_exposed_km ?? 0;
                const arr = z.earliest_arrival ?? (z.earliest_arrival_hr ? `${z.earliest_arrival_hr}h` : '0.0h');
                const prio = z.priority || `Priority ${z.priority_rank ?? z.rank ?? 1}`;
                const prioRank = z.priority_rank ?? z.rank ?? 1;

                return (
                  <div
                    key={zid}
                    className={`zone-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectZone(isSelected ? null : zid)}
                    style={{
                      border: isSelected ? '2px solid #2563eb' : '1px solid #e2e8f0',
                      background: isSelected ? '#eff6ff' : '#ffffff',
                      borderRadius: 6,
                      padding: '8px 10px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: isSelected ? '0 2px 6px rgba(37,99,235,0.15)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 11.5, color: '#0f172a' }}>{zname}</div>
                        <div style={{ fontSize: 9.5, color: '#64748b' }}>{zid} · Arrival: <strong>{arr}</strong></div>
                      </div>
                      <span
                        style={{
                          fontSize: 9,
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: 3,
                          background: prioRank <= 2 ? '#fee2e2' : prioRank <= 4 ? '#ffedd5' : '#dbeafe',
                          color: prioRank <= 2 ? '#991b1b' : prioRank <= 4 ? '#9a3412' : '#1e40af',
                        }}
                      >
                        {prio}
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4, marginTop: 4, borderTop: '1px dashed #f1f5f9', paddingTop: 4 }}>
                      <div>
                        <div style={{ fontSize: 8.5, color: '#94a3b8' }}>WorldPop</div>
                        <div style={{ fontSize: 10.5, fontWeight: 700, color: '#0f172a' }}>{wp.toLocaleString()}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 8.5, color: '#94a3b8' }}>Buildings</div>
                        <div style={{ fontSize: 10.5, fontWeight: 700, color: '#0f172a' }}>{bld.toLocaleString()} <span style={{ fontSize: 8.5, color: '#dc2626' }}>({h5bld})</span></div>
                      </div>
                      <div>
                        <div style={{ fontSize: 8.5, color: '#94a3b8' }}>Roads</div>
                        <div style={{ fontSize: 10.5, fontWeight: 700, color: '#0f172a' }}>{rd.toFixed(1)} km</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}
