"""
JalRakshak-HD: Milestone M10 Tasks 49 & 50 — Dashboard API Test Suite
======================================================================
Comprehensive pytest test suite validating all FastAPI dashboard endpoints,
data schemas, point sampling on inundated vs dry locations, and error handling.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["project"] == "JalRakshak-HD"
    assert "M10_GIS_DASHBOARD" in data["milestones_status"]


def test_project_summary_endpoint():
    res = client.get("/api/project")
    assert res.status_code == 200
    data = res.json()
    assert data["project"] == "JalRakshak-HD"
    assert data["domain_area_km2"] == 818.37
    assert data["max_inundated_area_km2"] == 101.29
    assert data["classification"] == "HYPOTHETICAL_ENGINEERING_STRESS_TEST"


def test_scenario_summary_endpoint():
    res = client.get("/api/scenario/BHV_BASE")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "BHV_BASE"
    assert data["hypothetical"] is True
    assert data["peak_discharge_m3s"] == 18742.38
    assert data["flood_volume_mcm"] == 408.0


def test_simulation_timeline_endpoint():
    res = client.get("/api/simulation/timeline")
    assert res.status_code == 200
    data = res.json()
    assert data["total_frames"] == 181
    assert data["total_duration_hours"] == 30.0
    assert len(data["frames"]) == 181
    assert data["frames"][0]["solver_time_s"] == 0.0
    assert data["frames"][-1]["solver_time_s"] == 108000.0


def test_simulation_meta_endpoint():
    res = client.get("/api/simulation/meta")
    assert res.status_code == 200
    data = res.json()
    assert data["domain_area_km2"] == 818.37
    assert data["max_inundated_area_km2"] == 101.29
    assert data["solver_max_depth_m"] == 22.02
    assert data["p95_depth_m"] == 12.72
    assert data["solver_max_velocity_mps"] == 11.79
    assert data["p95_velocity_mps"] == 4.27
    assert data["total_frames"] == 181
    assert data["duration_hours"] == 30.0


def test_simulation_single_frame():
    res = client.get("/api/simulation/frame/60")
    assert res.status_code == 200
    data = res.json()
    assert data["frame_index"] == 60
    assert data["solver_time_s"] == 36000.0
    assert data["solver_time_hr"] == 10.0
    assert data["max_depth_at_frame"] > 15.0


def test_hydrograph_endpoint():
    res = client.get("/api/simulation/hydrograph")
    assert res.status_code == 200
    data = res.json()
    assert data["peak_discharge_m3s"] >= 18000.0
    assert len(data["hydrograph"]) > 50


def test_observation_stations_endpoint():
    res = client.get("/api/simulation/stations")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4
    assert any(s["station_id"] == "OBS_01_TOE" for s in data)


def test_gis_vector_endpoints():
    endpoints = [
        "/api/gis/dam",
        "/api/gis/river",
        "/api/gis/reservoir",
        "/api/gis/inundation",
        "/api/gis/hazard",
        "/api/gis/hadr-zones",
        "/api/gis/critical-facilities",
        "/api/gis/historical-flood",
        "/api/gis/latest-water-change",
        "/api/gis/sph-reach",
        "/api/gis/sph-gauges"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Failed on endpoint: {ep}"
        data = res.json()
        assert data.get("type") == "FeatureCollection"
        assert len(data.get("features", [])) > 0, f"Empty features in {ep}"


def test_gis_buildings_bbox_filtering():
    # Test bbox around Sathyamangalam
    res = client.get("/api/gis/buildings?min_lon=77.20&min_lat=11.48&max_lon=77.26&max_lat=11.53&limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) <= 50


def test_gis_overlays_manifest():
    res = client.get("/api/tiles/overlays/manifest")
    assert res.status_code == 200
    data = res.json()
    assert "max_depth" in data["layers"]
    assert "hazard_class" in data["layers"]


def test_point_analysis_inundated_location():
    # Point near dam outlet / downstream reach
    res = client.get("/api/analyze-point?lat=11.4705&lon=77.1140")
    assert res.status_code == 200
    data = res.json()
    assert data["in_study_area"] is True
    assert data["max_depth_m"] is not None
    assert data["max_depth_m"] > 0.5
    assert data["hazard_class"] in ["H1", "H2", "H3", "H4", "H5", "H6"]
    assert "Inundated" in data["status_message"]


def test_point_analysis_dry_outside_location():
    # Remote dry point far outside bounding box
    res = client.get("/api/analyze-point?lat=12.5000&lon=78.5000")
    assert res.status_code == 200
    data = res.json()
    assert data["in_study_area"] is False
    assert data["max_depth_m"] is None
    assert data["hazard_class"] is None
    assert "outside" in data["status_message"].lower()


def test_hadr_summary_endpoint():
    res = client.get("/api/hadr/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_inundated_area_km2"] == 101.29
    assert data["severe_hazard_h3_h6_area_km2"] == 97.99
    assert data["extreme_hazard_h5_h6_area_km2"] == 87.29
    assert data["worldpop_exposed"] == 42428.1
    assert data["ghsl_exposed"] == 84500.5
    assert data["buildings_exposed"] == 25652
    assert data["h5_h6_buildings_exposed"] == 22472
    assert data["bridges_exposed_count"] == 20
    assert data["critical_facilities_count"] == 13


def test_hadr_zones_endpoint():
    res = client.get("/api/hadr/zones")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 6
    zone_ids = [z["zone_id"] for z in data]
    assert "ZONE_01" in zone_ids
    assert "ZONE_06" in zone_ids


def test_sph_summary_endpoint():
    res = client.get("/api/sph/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["model_classification"] == "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL"
    assert data["domain_length_m"] == 1500.0
    assert data["total_particles"] == 10982
    assert data["max_depth_m"] == 17.11
    assert data["p95_depth_m"] == 12.57
    assert data["max_velocity_mps"] == 34.78
    assert data["p95_velocity_mps"] == 8.62
    assert data["front_position_at_600s_m"] == 1280.41


def test_sph_gauges_endpoint():
    res = client.get("/api/sph/gauges")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    gauge_names = [g["gauge_name"] for g in data]
    assert "G_100m" in gauge_names
    assert "G_1500m" in gauge_names


def test_sph_front_endpoint():
    res = client.get("/api/sph/front")
    assert res.status_code == 200
    data = res.json()
    assert len(data["data"]) > 0


def test_comparison_solvers_endpoint():
    res = client.get("/api/comparison/solvers")
    assert res.status_code == 200
    data = res.json()
    assert data["forcing_equivalent"] is False
    assert "DIVERGENT" in data["velocity_trend"]
    assert data["direct_coupling_ready"] is False
    assert len(data["profile_data"]) >= 5


def test_remote_sensing_historical():
    res = client.get("/api/remote-sensing/historical")
    assert res.status_code == 200
    data = res.json()
    assert data["event_name"] == "AUGUST_2019_BHAVANI_FLOOD_BHAVANISAGAR_INFLOW_EVENT"
    assert data["model_validation"] is False
    assert "S1A" in data["sentinel1_scene_id"]
    assert data["observed_new_flood_raster_km2"] == 1.1925
    assert data["observed_new_flood_vector_km2"] == 1.1150


def test_remote_sensing_latest():
    res = client.get("/api/remote-sensing/latest")
    assert res.status_code == 200
    data = res.json()
    assert data["platform"] == "Sentinel-1D"
    assert data["cause"] == "UNVERIFIED"
    assert data["observation_quality"] == "HIGH"
    assert data["flood_interpretation_confidence"] == "UNCONFIRMED"


def test_provenance_endpoint():
    res = client.get("/api/provenance")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 8
    categories = [p["category"] for p in data]
    assert any("Dam Engineering" in c for c in categories)
    assert any("2D Hydrodynamic" in c for c in categories)
