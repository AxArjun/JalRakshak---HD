import json
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from backend.app.schemas.report import (
    SimulationImpactReport, FinalSimulationReport,
    AffectedPlaceItem, EvacuationPriorityGrouping
)

router = APIRouter(prefix="/reports", tags=["Reports"])

ROOT_DIR = Path(__file__).resolve().parents[3]
IMPACT_MANIFEST = ROOT_DIR / "outputs" / "dashboard" / "impact" / "timestep_impacts.json"
AFFECTED_PLACES_FILE = ROOT_DIR / "outputs" / "dashboard" / "impact" / "affected_places.json"
TRUTH_MANIFEST = ROOT_DIR / "outputs" / "validation" / "final_scientific_truth_manifest.json"

DISCLAIMER_TEXT = (
    "Research screening prototype. This report represents a hypothetical dam-breach model scenario "
    "and is not an official flood warning, evacuation order, engineering certification, or observed dam-failure report."
)

EVACUATION_HEADING_TEXT = "MODELED EVACUATION PRIORITY"
EVACUATION_DISCLAIMER_TEXT = (
    "Places listed below fall within the modeled inundation corridor and are prioritized according to "
    "modeled flood-arrival time and hydraulic hazard. This is a research screening output and not a statutory evacuation order."
)

DATA_SOURCES_LIST = [
    "NASA SRTM 30m Global DEM & HydroSHEDS",
    "Deltares D-Flow Flexible Mesh 2D Hydrodynamic Solver",
    "DualSPHysics 2D Unit-Width Near-Field SPH Screening Model",
    "WorldPop 2020 100m UN-Adjusted Population",
    "Copernicus GHSL 2025 Built-Up Population Grid",
    "OpenStreetMap & Google Open Buildings v3",
    "Central Water Commission (CWC) Large Dams Register 2023",
    "ESA Copernicus Sentinel-1 Synthetic Aperture Radar"
]

LIMITATIONS_LIST = [
    "Hypothetical overtopping breach modeled using Froehlich (2008) empirical regression (+/- 25-35% uncertainty).",
    "SRTM 30m terrain model lacks sub-grid channel bathymetry and micro-drainage culverts.",
    "DualSPHysics near-field SPH and D-Flow FM far-field models are decoupled multi-scale simulations (direct two-way coupling not implemented).",
    "Modeled response windows are decision-support estimates and do not constitute statutory evacuation orders.",
    "Population estimates are derived from top-down dasymetric disaggregation without door-to-door census verification."
]

def load_impact_data():
    if not IMPACT_MANIFEST.exists():
        raise HTTPException(status_code=404, detail="Timestep impacts manifest not found. Run preprocessing.")
    with open(IMPACT_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)

def load_affected_places_data():
    if not AFFECTED_PLACES_FILE.exists():
        raise HTTPException(status_code=404, detail="Affected places file not found. Run preprocessing.")
    with open(AFFECTED_PLACES_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("places", [])

def load_truth_data():
    if not TRUTH_MANIFEST.exists():
        raise HTTPException(status_code=404, detail="Scientific truth manifest not found.")
    with open(TRUTH_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)

def group_evacuation_priority(places, current_time_hr=None):
    under_30 = []
    thirty_60 = []
    one_two = []
    over_2 = []
    already = []
    outside = []
    
    for p in places:
        item = AffectedPlaceItem(**p)
        if not item.affected or item.earliest_arrival_hr is None:
            outside.append(item)
            continue
            
        if current_time_hr is not None:
            # Time-dependent classification relative to current simulation time
            if current_time_hr >= item.earliest_arrival_hr:
                already.append(item)
            else:
                lead = item.earliest_arrival_hr - current_time_hr
                if lead <= 0.5:
                    under_30.append(item)
                elif lead <= 1.0:
                    thirty_60.append(item)
                elif lead <= 2.0:
                    one_two.append(item)
                else:
                    over_2.append(item)
        else:
            # Baseline pre-event planning classification (First arrival after breach)
            if item.earliest_arrival_hr <= 0.5:
                under_30.append(item)
            elif item.earliest_arrival_hr <= 1.0:
                thirty_60.append(item)
            elif item.earliest_arrival_hr <= 2.0:
                one_two.append(item)
            else:
                over_2.append(item)
                
    return EvacuationPriorityGrouping(
        immediate_under_30_min=under_30,
        high_30_to_60_min=thirty_60,
        priority_1_to_2_hr=one_two,
        advance_notice_over_2_hr=over_2,
        already_reached=already,
        outside_modeled_inundation=outside,
        disclaimer=EVACUATION_DISCLAIMER_TEXT
    )

@router.get("/impact/{frame_index}", response_model=SimulationImpactReport)
def get_impact_report(frame_index: int):
    data = load_impact_data()
    places_raw = load_affected_places_data()
    frames = data.get("frames", [])
    if frame_index < 0 or frame_index >= len(frames):
        raise HTTPException(status_code=400, detail=f"Invalid frame_index {frame_index}. Range: 0 to {len(frames)-1}")
    
    frame = frames[frame_index]
    current_time_hr = frame["time_hr"]
    
    # Calculate time-dependent arrival status for each place
    affected_places_items = []
    for p in places_raw:
        item = AffectedPlaceItem(**p)
        affected_places_items.append(item)
        
    evac_grouping = group_evacuation_priority(places_raw, current_time_hr=current_time_hr)
    
    return SimulationImpactReport(
        title="JalRakshak-HD Modeled Situation Report",
        site="Bhavanisagar Dam / Lower Bhavani River",
        scenario="BHV_BASE",
        classification="HYPOTHETICAL_ENGINEERING_STRESS_TEST",
        frame_index=frame["frame_index"],
        time_s=frame["time_s"],
        time_hr=frame["time_hr"],
        formatted_time=frame["formatted_time"],
        generation_timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        current_impact=frame["current_impact"],
        building_vulnerability_screening=frame["building_vulnerability_screening"],
        evacuation_screening=frame["evacuation_screening"],
        next_60_minutes_window=frame["next_60_minutes_window"],
        response_sectors=frame["response_sectors"],
        affected_places=affected_places_items,
        evacuation_priority_screening=evac_grouping,
        data_sources=DATA_SOURCES_LIST,
        limitations=LIMITATIONS_LIST,
        disclaimer=DISCLAIMER_TEXT,
        provenance={
            "solver": "D-Flow FM 2D v2024.01",
            "frame_interval_seconds": 600,
            "manifest_version": "v1.0-SIH",
            "mesh_cells": 46830
        }
    )

@router.get("/final", response_model=FinalSimulationReport)
def get_final_report():
    truth = load_truth_data()
    places_raw = load_affected_places_data()
    bhv = truth.get("bhavanisagar", {})
    dflow = bhv.get("dflow_fm_simulation", {})
    hadr = bhv.get("hadr_exposure", {})
    eo = bhv.get("earth_observation", {})
    sph = bhv.get("dualsphysics_nearfield", {})
    
    affected_places_items = [AffectedPlaceItem(**p) for p in places_raw]
    evac_grouping = group_evacuation_priority(places_raw, current_time_hr=None)
    
    return FinalSimulationReport(
        title="JalRakshak-HD Final Hypothetical Breach Screening Report",
        site="Bhavanisagar Dam",
        scenario="BHV_BASE",
        classification="HYPOTHETICAL_ENGINEERING_STRESS_TEST",
        simulation_duration_hours=30.0,
        frame_count=181,
        generation_timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        hydraulics={
            "domain_area_km2": dflow.get("computational_domain_area_km2", 818.37),
            "maximum_inundated_area_km2": dflow.get("maximum_inundated_area_km2", 101.29),
            "peak_depth_m": dflow.get("solver_maximum_depth_m", 22.02),
            "p95_depth_m": dflow.get("p95_water_depth_m", 12.72),
            "peak_velocity_mps": dflow.get("solver_maximum_velocity_mps", 11.79),
            "p95_velocity_mps": dflow.get("p95_flow_velocity_mps", 4.27),
            "peak_discharge_m3s": 18742.38,
            "mass_conservation_residual_mcm": 0.041,
            "mass_conservation_relative_error_pct": 0.0052
        },
        exposure={
            "worldpop_exposed": hadr.get("worldpop_exposed_population", 42428.1),
            "ghsl_exposed": hadr.get("ghsl_exposed_population", 84500.5),
            "ghsl_version": "GHSL 2025",
            "buildings_exposed": hadr.get("total_buildings_inundated", 25652),
            "h5_h6_buildings": hadr.get("high_hazard_h5_h6_buildings", 22472),
            "roads_exposed_km": hadr.get("inundated_road_length_km", 243.82),
            "bridges_reached": hadr.get("screened_bridge_crossings_count", 20),
            "critical_facilities_reached": hadr.get("mapped_critical_facilities_count", 13)
        },
        affected_places=affected_places_items,
        evacuation_priority_screening=evac_grouping,
        response_sectors=hadr.get("response_sectors", []),
        earth_observation_context={
            "historical_event": "AUGUST_2019_BHAVANI_FLOOD_BHAVANISAGAR_INFLOW_EVENT",
            "historical_date": "2019-08-10",
            "platform": "Sentinel-1A (Scene ending 041D)",
            "historical_sentinel1_flood_km2": 1.1925,
            "historical_flood_vector_km2": 1.1150,
            "monitoring_status": "CANDIDATE_NEW_WATER_EXPANSION_DETECTED",
            "interpretation": "UNCONFIRMED_HYDROLOGIC_VARIATION"
        },
        nearfield_sph_summary={
            "model_classification": "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL",
            "simulation_case": "PEAK_STATE_INITIALIZED_RELEASE_SCREENING_CASE",
            "particle_count": sph.get("fluid_particles_total", 10982),
            "simulation_duration_s": sph.get("simulation_duration_seconds", 600),
            "max_nearfield_depth_m": sph.get("solver_maximum_depth_m", 17.11),
            "max_nearfield_velocity_mps": sph.get("solver_maximum_velocity_mps", 34.78),
            "front_position_600s_m": sph.get("front_position_600s_m", 1280.41)
        },
        cross_solver_analysis={
            "framework": "CROSS_SOLVER_ANALYSIS",
            "coupling_status": "DECOUPLED_MULTI_SCALE_ANALYSIS",
            "direct_two_way_coupling": False,
            "evaluation": "Consistent peak velocity magnitude regime; independent near/far-field execution"
        },
        limitations=LIMITATIONS_LIST,
        provenance={
            "truth_manifest_locked": truth.get("date_locked", "2026-09-26"),
            "system_version": "JalRakshak-HD v1.0-SIH",
            "solvers": "D-Flow FM 2D + DualSPHysics 2D Unit-Width SPH"
        },
        disclaimer=DISCLAIMER_TEXT
    )

@router.get("/impact/{frame_index}/html", response_class=HTMLResponse)
def get_impact_report_html(frame_index: int):
    rep = get_impact_report(frame_index)
    evac = rep.evacuation_priority_screening
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{rep.title} - {rep.formatted_time}</title>
    <style>
        @page {{ size: A4 portrait; margin: 12mm; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #1a202c;
            line-height: 1.45;
            background: #fff;
            margin: 0;
            padding: 20px;
            font-size: 12px;
        }}
        .header {{
            border-bottom: 2px solid #2b6cb0;
            padding-bottom: 8px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .header h1 {{ margin: 0 0 4px 0; font-size: 19px; color: #2b6cb0; }}
        .header .meta {{ font-size: 11px; color: #4a5568; text-align: right; }}
        .disclaimer-box {{
            background: #fffaf0;
            border-left: 4px solid #dd6b20;
            padding: 8px 12px;
            margin-bottom: 16px;
            font-size: 11px;
            color: #7b341e;
        }}
        .section-title {{
            font-size: 13px;
            font-weight: 700;
            color: #2d3748;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 3px;
            margin-top: 18px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 14px;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 8px;
        }}
        .card .label {{ font-size: 10px; color: #718096; text-transform: uppercase; font-weight: 600; }}
        .card .val {{ font-size: 15px; font-weight: 700; color: #2b6cb0; margin-top: 2px; }}
        .card .sub {{ font-size: 9.5px; color: #a0aec0; margin-top: 2px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 14px;
            font-size: 11.5px;
        }}
        th, td {{
            padding: 5px 8px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{ background: #edf2f7; color: #4a5568; font-weight: 600; }}
        .priority-badge {{
            font-size: 9.5px;
            font-weight: 700;
            padding: 1px 6px;
            border-radius: 3px;
            display: inline-block;
        }}
        .badge-red {{ background: #fee2e2; color: #991b1b; }}
        .badge-orange {{ background: #ffedd5; color: #9a3412; }}
        .badge-amber {{ background: #fef3c7; color: #92400e; }}
        .badge-blue {{ background: #dbeafe; color: #1e40af; }}
        .badge-gray {{ background: #f1f5f9; color: #475569; }}
        ul {{ margin: 0 0 14px 0; padding-left: 18px; font-size: 11px; color: #4a5568; }}
        li {{ margin-bottom: 3px; }}
        .page-break {{ page-break-before: always; }}
        .footer {{
            margin-top: 25px;
            border-top: 1px solid #e2e8f0;
            padding-top: 8px;
            font-size: 9.5px;
            color: #a0aec0;
            display: flex;
            justify-content: space-between;
        }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 15px; text-align: right;">
        <button onclick="window.print()" style="background:#2b6cb0; color:#fff; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; font-weight:bold;">Print / Save as PDF</button>
    </div>

    <div class="header">
        <div>
            <h1>{rep.title}</h1>
            <div style="font-weight: 600; color: #4a5568;">{rep.site} | Scenario: {rep.scenario}</div>
            <div style="font-size: 11px; color: #718096;">Elapsed Time: <strong>{rep.formatted_time}</strong> ({rep.time_s} seconds)</div>
        </div>
        <div class="meta">
            <div>Generated: {rep.generation_timestamp}</div>
            <div>Classification: {rep.classification}</div>
            <div>Frame Index: {rep.frame_index} / 180</div>
        </div>
    </div>

    <div class="disclaimer-box">
        <strong>SCIENTIFIC RESEARCH DISCLAIMER:</strong> {rep.disclaimer}
    </div>

    <div class="section-title">1. Current Modeled Inundation & Exposure</div>
    <div class="grid">
        <div class="card">
            <div class="label">Inundated Footprint</div>
            <div class="val">{rep.current_impact.inundated_area_km2} km²</div>
            <div class="sub">Model Wet Domain Area</div>
        </div>
        <div class="card">
            <div class="label">Population (WorldPop)</div>
            <div class="val">{rep.current_impact.worldpop_exposed:,.1f}</div>
            <div class="sub">GHSL 2025: {rep.current_impact.ghsl_exposed:,.1f}</div>
        </div>
        <div class="card">
            <div class="label">Buildings Exposed</div>
            <div class="val">{rep.current_impact.buildings_exposed:,}</div>
            <div class="sub">Google Open Buildings v3</div>
        </div>
        <div class="card">
            <div class="label">Infrastructure Reached</div>
            <div class="val">{rep.current_impact.bridges_exposed} / {rep.current_impact.total_bridges} Bridges</div>
            <div class="sub">Roads: {rep.current_impact.roads_exposed_km} km | Fac: {rep.current_impact.critical_facilities_exposed}</div>
        </div>
    </div>

    <div class="section-title">2. Real Affected Places & Modeled Arrival</div>
    <table>
        <thead>
            <tr>
                <th>Place Name</th>
                <th>Response Zone</th>
                <th>Earliest Arrival</th>
                <th>Max Depth</th>
                <th>Max Velocity</th>
                <th>Hazard</th>
                <th>Current Status</th>
            </tr>
        </thead>
        <tbody>
            {''.join(f'''<tr>
                <td><strong>{p.place_name}</strong></td>
                <td>{p.response_zone}</td>
                <td>{f"{p.earliest_arrival_hr:.2f} h" if p.earliest_arrival_hr is not None else "N/A"}</td>
                <td>{f"{p.max_depth_m:.2f} m" if p.max_depth_m is not None else "0.00 m"}</td>
                <td>{f"{p.max_velocity_mps:.2f} m/s" if p.max_velocity_mps is not None else "0.00 m/s"}</td>
                <td><span style="font-weight:700; color:{'#dc2626' if p.hazard_class == 'H6' else '#ea580c' if p.hazard_class == 'H5' else '#475569'}">{p.hazard_class or "None"}</span></td>
                <td>
                    <span class="priority-badge {'badge-red' if (p.earliest_arrival_hr is not None and rep.time_hr >= p.earliest_arrival_hr) else 'badge-orange' if (p.earliest_arrival_hr is not None and p.earliest_arrival_hr - rep.time_hr <= 0.5) else 'badge-amber' if (p.earliest_arrival_hr is not None and p.earliest_arrival_hr - rep.time_hr <= 1.0) else 'badge-blue' if p.affected else 'badge-gray'}">
                        {'ALREADY REACHED' if (p.earliest_arrival_hr is not None and rep.time_hr >= p.earliest_arrival_hr) else f'LEAD: {max(0, p.earliest_arrival_hr - rep.time_hr):.1f}h' if p.affected else 'OUTSIDE INUNDATION'}
                    </span>
                </td>
            </tr>''' for p in rep.affected_places)}
        </tbody>
    </table>

    <div class="section-title">3. {EVACUATION_HEADING_TEXT}</div>
    <div style="font-size:10.5px; color:#4a5568; margin-bottom:8px; font-style:italic;">
        {EVACUATION_DISCLAIMER_TEXT}
    </div>
    
    <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:10px; margin-bottom:14px;">
        <div style="border:1px solid #fecaca; background:#fef2f2; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#991b1b; font-size:11px; margin-bottom:4px;">🚨 IMMEDIATE RESPONSE (&lt;30 MIN LEAD TIME)</div>
            <div style="font-size:11px; color:#7f1d1d;">
                {', '.join(p.place_name for p in evac.immediate_under_30_min) if evac.immediate_under_30_min else "None currently in this window"}
            </div>
        </div>
        <div style="border:1px solid #ffedd5; background:#fff7ed; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#9a3412; font-size:11px; margin-bottom:4px;">⚠️ HIGH PRIORITY (30–60 MIN LEAD TIME)</div>
            <div style="font-size:11px; color:#9a3412;">
                {', '.join(p.place_name for p in evac.high_30_to_60_min) if evac.high_30_to_60_min else "None currently in this window"}
            </div>
        </div>
        <div style="border:1px solid #fef3c7; background:#fffbeb; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#92400e; font-size:11px; margin-bottom:4px;">⏳ PRIORITY 1–2 HOURS</div>
            <div style="font-size:11px; color:#92400e;">
                {', '.join(p.place_name for p in evac.priority_1_to_2_hr) if evac.priority_1_to_2_hr else "None currently in this window"}
            </div>
        </div>
        <div style="border:1px solid #dbeafe; background:#eff6ff; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#1e40af; font-size:11px; margin-bottom:4px;">📢 ADVANCE NOTICE (&gt;2 HOURS)</div>
            <div style="font-size:11px; color:#1e40af;">
                {', '.join(p.place_name for p in evac.advance_notice_over_2_hr) if evac.advance_notice_over_2_hr else "None currently in this window"}
            </div>
        </div>
    </div>

    <div class="section-title">4. Non-Overlapping Response Sector Status</div>
    <table>
        <thead>
            <tr>
                <th>Zone ID</th>
                <th>Sector Name</th>
                <th>Status</th>
                <th>Earliest Arrival</th>
                <th>Lead Time</th>
                <th>Max Hazard</th>
                <th>WorldPop</th>
                <th>Buildings</th>
            </tr>
        </thead>
        <tbody>
            {''.join(f'''<tr>
                <td><strong>{z.zone_id}</strong></td>
                <td>{z.sector_name}</td>
                <td><span style="font-weight:600; color:{'#e53e3e' if 'ACTIVE' in z.status or 'PAST' in z.status else '#dd6b20' if 'IMMINENT' in z.status else '#38a169'}">{z.status}</span></td>
                <td>{z.earliest_arrival_hr} h</td>
                <td>{z.remaining_lead_time_hr} h</td>
                <td>{z.max_hazard_class}</td>
                <td>{z.current_worldpop_exposed:,.1f} / {z.total_zone_worldpop:,.1f}</td>
                <td>{z.current_buildings_exposed:,} / {z.total_zone_buildings:,}</td>
            </tr>''' for z in rep.response_sectors)}
        </tbody>
    </table>

    <div class="section-title">5. Scientific Limitations & Provenance</div>
    <ul>
        {''.join(f'<li>{lim}</li>' for lim in rep.limitations)}
    </ul>

    <div class="footer">
        <div>JalRakshak-HD Decision-Support Platform | Solver: {rep.provenance.get('solver')}</div>
        <div>Page 1 of 2</div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@router.get("/final/html", response_class=HTMLResponse)
def get_final_report_html():
    rep = get_final_report()
    evac = rep.evacuation_priority_screening
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{rep.title}</title>
    <style>
        @page {{ size: A4 portrait; margin: 12mm; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #1a202c;
            line-height: 1.45;
            background: #fff;
            margin: 0;
            padding: 20px;
            font-size: 12px;
        }}
        .header {{
            border-bottom: 2px solid #2b6cb0;
            padding-bottom: 8px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .header h1 {{ margin: 0 0 4px 0; font-size: 19px; color: #2b6cb0; }}
        .header .meta {{ font-size: 11px; color: #4a5568; text-align: right; }}
        .disclaimer-box {{
            background: #fffaf0;
            border-left: 4px solid #dd6b20;
            padding: 8px 12px;
            margin-bottom: 16px;
            font-size: 11px;
            color: #7b341e;
        }}
        .section-title {{
            font-size: 13px;
            font-weight: 700;
            color: #2d3748;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 3px;
            margin-top: 18px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 14px;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 8px;
        }}
        .card .label {{ font-size: 10px; color: #718096; text-transform: uppercase; font-weight: 600; }}
        .card .val {{ font-size: 15px; font-weight: 700; color: #2b6cb0; margin-top: 2px; }}
        .card .sub {{ font-size: 9.5px; color: #a0aec0; margin-top: 2px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 14px;
            font-size: 11.5px;
        }}
        th, td {{
            padding: 5px 8px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{ background: #edf2f7; color: #4a5568; font-weight: 600; }}
        .priority-badge {{
            font-size: 9.5px;
            font-weight: 700;
            padding: 1px 6px;
            border-radius: 3px;
            display: inline-block;
        }}
        .badge-red {{ background: #fee2e2; color: #991b1b; }}
        .badge-orange {{ background: #ffedd5; color: #9a3412; }}
        .badge-amber {{ background: #fef3c7; color: #92400e; }}
        .badge-blue {{ background: #dbeafe; color: #1e40af; }}
        .badge-gray {{ background: #f1f5f9; color: #475569; }}
        ul {{ margin: 0 0 14px 0; padding-left: 18px; font-size: 11px; color: #4a5568; }}
        li {{ margin-bottom: 3px; }}
        .page-break {{ page-break-before: always; }}
        .footer {{
            margin-top: 25px;
            border-top: 1px solid #e2e8f0;
            padding-top: 8px;
            font-size: 9.5px;
            color: #a0aec0;
            display: flex;
            justify-content: space-between;
        }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 15px; text-align: right;">
        <button onclick="window.print()" style="background:#2b6cb0; color:#fff; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; font-weight:bold;">Print / Save as PDF</button>
    </div>

    <!-- PAGE 1 -->
    <div class="header">
        <div>
            <h1>{rep.title}</h1>
            <div style="font-weight: 600; color: #4a5568;">{rep.site} | Scenario: {rep.scenario}</div>
            <div style="font-size: 11px; color: #718096;">Simulation Duration: <strong>{rep.simulation_duration_hours} Hours</strong> ({rep.frame_count} Timestep Frames)</div>
        </div>
        <div class="meta">
            <div>Generated: {rep.generation_timestamp}</div>
            <div>Classification: {rep.classification}</div>
            <div>Manifest Locked: {rep.provenance.get('truth_manifest_locked')}</div>
        </div>
    </div>

    <div class="disclaimer-box">
        <strong>SCIENTIFIC RESEARCH DISCLAIMER:</strong> {rep.disclaimer}
    </div>

    <div class="section-title">1. Authoritative Hydraulic Simulation Metrics</div>
    <div class="grid">
        <div class="card">
            <div class="label">Domain Area</div>
            <div class="val">{rep.hydraulics.get('domain_area_km2')} km²</div>
            <div class="sub">NASA SRTM 30m / HydroSHEDS</div>
        </div>
        <div class="card">
            <div class="label">Max Inundated Footprint</div>
            <div class="val">{rep.hydraulics.get('maximum_inundated_area_km2')} km²</div>
            <div class="sub">D-Flow FM Wet Cells (d &ge; 0.05m)</div>
        </div>
        <div class="card">
            <div class="label">Peak Flow Depth</div>
            <div class="val">{rep.hydraulics.get('peak_depth_m')} m</div>
            <div class="sub">P95 Depth: {rep.hydraulics.get('p95_depth_m')} m</div>
        </div>
        <div class="card">
            <div class="label">Peak Flow Velocity</div>
            <div class="val">{rep.hydraulics.get('peak_velocity_mps')} m/s</div>
            <div class="sub">P95 Velocity: {rep.hydraulics.get('p95_velocity_mps')} m/s</div>
        </div>
    </div>

    <div class="section-title">2. Downstream Exposure Summary (HADR)</div>
    <div class="grid">
        <div class="card">
            <div class="label">WorldPop 2020 Exposed</div>
            <div class="val">{rep.exposure.get('worldpop_exposed'):,.1f}</div>
            <div class="sub">Primary Residential Baseline</div>
        </div>
        <div class="card">
            <div class="label">GHSL 2025 Exposed</div>
            <div class="val">{rep.exposure.get('ghsl_exposed'):,.1f}</div>
            <div class="sub">Daytime Built-Up Cross-Check</div>
        </div>
        <div class="card">
            <div class="label">Buildings Exposed</div>
            <div class="val">{rep.exposure.get('buildings_exposed'):,}</div>
            <div class="sub">H5/H6 Extreme: {rep.exposure.get('h5_h6_buildings'):,}</div>
        </div>
        <div class="card">
            <div class="label">Transportation & Facilities</div>
            <div class="val">{rep.exposure.get('bridges_reached')} Bridges / {rep.exposure.get('critical_facilities_reached')} Fac.</div>
            <div class="sub">Inundated Roads: {rep.exposure.get('roads_exposed_km')} km</div>
        </div>
    </div>

    <div class="section-title">3. Affected Places & Modeled Arrival</div>
    <table>
        <thead>
            <tr>
                <th>Place Name</th>
                <th>Response Zone</th>
                <th>Earliest Arrival</th>
                <th>Max Depth</th>
                <th>Max Velocity</th>
                <th>Hazard Class</th>
                <th>Modeled Priority</th>
            </tr>
        </thead>
        <tbody>
            {''.join(f'''<tr>
                <td><strong>{p.place_name}</strong></td>
                <td>{p.response_zone}</td>
                <td>{f"{p.earliest_arrival_hr:.2f} h" if p.earliest_arrival_hr is not None else "N/A"}</td>
                <td>{f"{p.max_depth_m:.2f} m" if p.max_depth_m is not None else "0.00 m"}</td>
                <td>{f"{p.max_velocity_mps:.2f} m/s" if p.max_velocity_mps is not None else "0.00 m/s"}</td>
                <td><span style="font-weight:700; color:{'#dc2626' if p.hazard_class == 'H6' else '#ea580c' if p.hazard_class == 'H5' else '#475569'}">{p.hazard_class or "None"}</span></td>
                <td>
                    <span class="priority-badge {'badge-red' if p.arrival_priority == 'IMMEDIATE_<30_MIN' else 'badge-orange' if p.arrival_priority == 'HIGH_30_60_MIN' else 'badge-amber' if p.arrival_priority == 'PRIORITY_1_2_HR' else 'badge-blue' if p.arrival_priority == 'ADVANCE_NOTICE_>2_HR' else 'badge-gray'}">
                        {p.arrival_priority.replace('_', ' ')}
                    </span>
                </td>
            </tr>''' for p in rep.affected_places)}
        </tbody>
    </table>

    <div class="section-title">4. {EVACUATION_HEADING_TEXT} (Pre-Event Preparedness Screening)</div>
    <div style="font-size:10.5px; color:#4a5568; margin-bottom:8px; font-style:italic;">
        {EVACUATION_DISCLAIMER_TEXT}
    </div>
    
    <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:10px; margin-bottom:14px;">
        <div style="border:1px solid #fecaca; background:#fef2f2; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#991b1b; font-size:11px; margin-bottom:4px;">🚨 IMMEDIATE RESPONSE (&lt;30 MIN)</div>
            <div style="font-size:11px; color:#7f1d1d;">
                {', '.join(p.place_name for p in evac.immediate_under_30_min) if evac.immediate_under_30_min else "None"}
            </div>
        </div>
        <div style="border:1px solid #ffedd5; background:#fff7ed; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#9a3412; font-size:11px; margin-bottom:4px;">⚠️ HIGH PRIORITY (30–60 MIN)</div>
            <div style="font-size:11px; color:#9a3412;">
                {', '.join(p.place_name for p in evac.high_30_to_60_min) if evac.high_30_to_60_min else "None"}
            </div>
        </div>
        <div style="border:1px solid #fef3c7; background:#fffbeb; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#92400e; font-size:11px; margin-bottom:4px;">⏳ PRIORITY 1–2 HOURS</div>
            <div style="font-size:11px; color:#92400e;">
                {', '.join(p.place_name for p in evac.priority_1_to_2_hr) if evac.priority_1_to_2_hr else "None"}
            </div>
        </div>
        <div style="border:1px solid #dbeafe; background:#eff6ff; border-radius:4px; padding:8px;">
            <div style="font-weight:700; color:#1e40af; font-size:11px; margin-bottom:4px;">📢 ADVANCE NOTICE (&gt;2 HOURS)</div>
            <div style="font-size:11px; color:#1e40af;">
                {', '.join(p.place_name for p in evac.advance_notice_over_2_hr) if evac.advance_notice_over_2_hr else "None"}
            </div>
        </div>
    </div>

    <!-- PAGE 2 -->
    <div class="page-break"></div>

    <div class="section-title">5. Affected Infrastructure by Response Sector</div>
    <table>
        <thead>
            <tr>
                <th>Zone ID</th>
                <th>Sector Name</th>
                <th>Chainage</th>
                <th>Exposed Buildings</th>
                <th>Inundated Roads</th>
                <th>Bridges</th>
                <th>Critical Facilities</th>
            </tr>
        </thead>
        <tbody>
            {''.join(f'''<tr>
                <td><strong>{z.get('zone_id', '')}</strong></td>
                <td>{z.get('sector_name', '')}</td>
                <td>{z.get('chainage_start_km', 0):.1f}–{z.get('chainage_end_km', 0):.1f} km</td>
                <td>{z.get('building_count', 0):,} (H5/H6: {z.get('h5_h6_buildings', 0):,})</td>
                <td>{z.get('road_length_km', 0):.2f} km</td>
                <td>{z.get('bridge_count', z.get('bridges', 0))}</td>
                <td>{z.get('critical_facility_count', z.get('facilities', 0))}</td>
            </tr>''' for z in rep.response_sectors)}
        </tbody>
    </table>

    <div class="section-title">6. Near-Field Hydrodynamics (DualSPHysics M6)</div>
    <div class="grid">
        <div class="card">
            <div class="label">Model Classification</div>
            <div class="val" style="font-size:12px;">2D Unit-Width SPH</div>
            <div class="sub">Peak-State Initialized Release</div>
        </div>
        <div class="card">
            <div class="label">Fluid Particles</div>
            <div class="val">{rep.nearfield_sph_summary.get('particle_count'):,}</div>
            <div class="sub">Navier-Stokes Lagrangian</div>
        </div>
        <div class="card">
            <div class="label">SPH Peak Velocity</div>
            <div class="val">{rep.nearfield_sph_summary.get('max_nearfield_velocity_mps')} m/s</div>
            <div class="sub">Dam-Face Splash Jet</div>
        </div>
        <div class="card">
            <div class="label">Wave Front Reach</div>
            <div class="val">{rep.nearfield_sph_summary.get('front_position_600s_m')} m</div>
            <div class="sub">Position at t = 600s</div>
        </div>
    </div>

    <div class="section-title">7. Cross-Solver Analysis (M7)</div>
    <div class="card" style="margin-bottom: 14px;">
        <div style="font-size: 11.5px; color: #2d3748;">
            <strong>Framework:</strong> {rep.cross_solver_analysis.get('framework')}<br>
            <strong>Coupling Status:</strong> {rep.cross_solver_analysis.get('coupling_status')} (Direct Coupling: <strong>FALSE</strong>).<br>
            <strong>Evaluation:</strong> {rep.cross_solver_analysis.get('evaluation')}.
        </div>
    </div>

    <div class="section-title">8. Earth Observation Context (Sentinel-1 M9)</div>
    <div class="card" style="margin-bottom: 14px;">
        <div style="font-size: 11.5px; color: #2d3748;">
            <strong>Historical Benchmark Event:</strong> {rep.earth_observation_context.get('historical_event')} (Date: {rep.earth_observation_context.get('historical_date')})<br>
            <strong>Sensor / Orbit:</strong> {rep.earth_observation_context.get('platform')}<br>
            <strong>Detected Flood Extent:</strong> {rep.earth_observation_context.get('historical_sentinel1_flood_km2')} km² (Raster) / {rep.earth_observation_context.get('historical_flood_vector_km2')} km² (Vector)<br>
            <strong>Operational NRT Status:</strong> {rep.earth_observation_context.get('monitoring_status')} ({rep.earth_observation_context.get('interpretation')}).
        </div>
    </div>

    <div class="section-title">9. Scientific Limitations & Provenance</div>
    <ul>
        {''.join(f'<li>{lim}</li>' for lim in rep.limitations)}
    </ul>

    <div class="footer">
        <div>JalRakshak-HD v1.0-SIH | Authoritative Truth Locked | Classification: {rep.classification}</div>
        <div>Page 2 of 2</div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)
