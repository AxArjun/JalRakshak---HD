import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_impact_report_success():
    response = client.get("/api/reports/impact/0")
    assert response.status_code == 200
    data = response.json()
    assert data["frame_index"] == 0
    assert "current_impact" in data
    assert "building_vulnerability_screening" in data
    assert "evacuation_screening" in data
    assert "next_60_minutes_window" in data
    assert "response_sectors" in data

def test_get_impact_report_invalid_frame():
    response = client.get("/api/reports/impact/999")
    assert response.status_code == 400

def test_get_final_report_success():
    response = client.get("/api/reports/final")
    assert response.status_code == 200
    data = response.json()
    assert data["hydraulics"]["maximum_inundated_area_km2"] == 101.29
    assert data["exposure"]["worldpop_exposed"] == 42428.1
    assert data["exposure"]["buildings_exposed"] == 25652

def test_get_html_reports():
    resp1 = client.get("/api/reports/impact/10/html")
    assert resp1.status_code == 200
    assert "<!DOCTYPE html>" in resp1.text
    
    resp2 = client.get("/api/reports/final/html")
    assert resp2.status_code == 200
    assert "<!DOCTYPE html>" in resp2.text
