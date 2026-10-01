// SiteCapabilityPanel — displays multi-site capability matrix and preflight diagnostics
import { useEffect, useState } from 'react';
import { fetchSiteCapability, fetchSiteDetails } from '../services/api';

interface Props {
  siteId: string;
}

export default function SiteCapabilityPanel({ siteId }: Props) {
  const [capData, setCapData] = useState<any>(null);
  const [siteDetails, setSiteDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchSiteCapability(siteId).catch(() => null),
      fetchSiteDetails(siteId).catch(() => null),
    ]).then(([cap, details]) => {
      setCapData(cap);
      setSiteDetails(details);
      setLoading(false);
    });
  }, [siteId]);

  if (loading) {
    return (
      <div style={{ padding: 20, color: '#94a3b8' }}>
        Loading site capability and preflight diagnostics...
      </div>
    );
  }

  const isBhavani = siteId.toLowerCase() === 'bhavanisagar';
  const identity = siteDetails?.identity || {};
  const geom = siteDetails?.geometry || {};
  const res = siteDetails?.reservoir || {};
  const crs = siteDetails?.study_area?.crs || {};
  const matrix = capData?.capability_matrix || {};

  return (
    <div style={{ padding: 16, overflowY: 'auto', height: '100%', color: '#e2e8f0' }}>
      {/* Header */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18 }}>🏞</span>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: '#f8fafc' }}>
              {siteDetails?.display_name || siteId}
            </h2>
            <div style={{ fontSize: 11, color: '#94a3b8' }}>
              {identity.river_name} · {identity.district}, {identity.state} · Lat: {identity.latitude}° N, Lon: {identity.longitude}° E
            </div>
          </div>
        </div>
      </div>

      {/* Production vs Portability Notice */}
      {!isBhavani ? (
        <div
          style={{
            padding: '12px 14px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            borderRadius: 6,
            marginBottom: 16,
          }}
        >
          <div style={{ color: '#f87171', fontWeight: 700, fontSize: 12, marginBottom: 4 }}>
            ⚠ SIMULATION UNAVAILABLE — HYDRAULIC PRODUCTION RUN NOT YET EXECUTED
          </div>
          <div style={{ fontSize: 11, color: '#cbd5e1', lineHeight: 1.4 }}>
            This secondary site serves as an <strong>Any-Dam / Any-River architecture generalization & portability proof</strong>.
            Gates A through E (Location, Terrain, Hydrology, Engineering, Screening Breach & Hydrograph) are validated.
            Full production 2D hydrodynamic flood routing (D-Flow FM), 3D/2D SPH, and HADR exposure models have not been executed.
          </div>
        </div>
      ) : (
        <div
          style={{
            padding: '10px 12px',
            background: 'rgba(34, 197, 94, 0.12)',
            border: '1px solid rgba(34, 197, 94, 0.35)',
            borderRadius: 6,
            marginBottom: 16,
          }}
        >
          <div style={{ color: '#4ade80', fontWeight: 700, fontSize: 12 }}>
            ✓ FULL PRODUCTION VALIDATED (M1–M10 BASELINE SITE)
          </div>
        </div>
      )}

      {/* Capability Matrix */}
      <div style={{ marginBottom: 18 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
          Milestone Workflow Capability Matrix
        </div>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
            <thead>
              <tr style={{ background: '#1e293b', color: '#94a3b8', textAlign: 'left' }}>
                <th style={{ padding: '6px 10px' }}>Workflow Stage</th>
                <th style={{ padding: '6px 10px' }}>Readiness</th>
                <th style={{ padding: '6px 10px' }}>Classification</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(matrix).map(([stage, status]: [string, any]) => {
                const isReady = status === 'READY';
                const isPartial = status === 'PARTIAL';
                const color = isReady ? '#4ade80' : isPartial ? '#facc15' : '#94a3b8';
                const bg = isReady ? 'rgba(34,197,94,0.1)' : isPartial ? 'rgba(250,204,21,0.1)' : 'rgba(148,163,184,0.08)';

                return (
                  <tr key={stage} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '6px 10px', color: '#f1f5f9', fontWeight: 500 }}>{stage}</td>
                    <td style={{ padding: '6px 10px' }}>
                      <span style={{ padding: '2px 6px', borderRadius: 3, fontSize: 10, fontWeight: 600, color, background: bg }}>
                        {status}
                      </span>
                    </td>
                    <td style={{ padding: '6px 10px', color: '#94a3b8', fontSize: 10 }}>
                      {isReady ? 'Fully Verified' : isPartial ? 'Partial Observation' : 'Awaiting Solver Run'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Engineering Attributes */}
      <div>
        <div style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
          Verified Engineering Metadata
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>Dam Height</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#38bdf8' }}>{geom.dam_height_m ? `${geom.dam_height_m} m` : '—'}</div>
          </div>
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>Crest Length</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#38bdf8' }}>{geom.crest_length_m ? `${geom.crest_length_m} m` : '—'}</div>
          </div>
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>Gross Storage</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#38bdf8' }}>{res.gross_storage_capacity_mcm ? `${res.gross_storage_capacity_mcm} MCM` : '—'}</div>
          </div>
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>FRL Elevation</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#38bdf8' }}>{res.full_reservoir_level_m ? `${res.full_reservoir_level_m} m MSL` : '—'}</div>
          </div>
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>Projected CRS</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#a78bfa' }}>{crs.project_crs || '—'}</div>
          </div>
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>Spillway Capacity</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#38bdf8' }}>{geom.spillway_capacity_m3s ? `${geom.spillway_capacity_m3s} m³/s` : '—'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
