"""Integration tests for multi-site FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_sites_list():
    response = client.get("/api/sites")
    assert response.status_code == 200
    data = response.json()
    assert data["total_sites"] >= 2
    site_ids = [s["site_id"] for s in data["sites"]]
    assert "bhavanisagar" in site_ids
    assert "hirakud" in site_ids


def test_get_bhavanisagar_details():
    response = client.get("/api/sites/bhavanisagar")
    assert response.status_code == 200
    data = response.json()
    assert data["site_id"] == "bhavanisagar"
    assert data["identity"]["dam_name"] == "Bhavanisagar Dam"
    assert data["study_area"]["crs"]["project_crs"] == "EPSG:32643"


def test_get_hirakud_details():
    response = client.get("/api/sites/hirakud")
    assert response.status_code == 200
    data = response.json()
    assert data["site_id"] == "hirakud"
    assert data["identity"]["dam_name"] == "Hirakud Dam"
    assert data["study_area"]["crs"]["project_crs"] == "EPSG:32644"


def test_get_hirakud_capability_matrix():
    response = client.get("/api/sites/hirakud/capability-matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["has_production_simulation"] is False
    matrix = data["capability_matrix"]
    assert matrix["Terrain"] == "READY"
    assert matrix["Hydrology"] == "READY"
    assert matrix["D-Flow Production"] == "NOT_RUN"


def test_get_nonexistent_site():
    response = client.get("/api/sites/nonexistent_dam_xyz")
    assert response.status_code == 404
