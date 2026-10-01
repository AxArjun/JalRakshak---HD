"""Unit and integration tests for Multi-Site Registry service.

Tests site listing, loading, CRS derivation, and directory resolution.
"""

import pytest
from pathlib import Path
from backend.app.services.site_registry import list_sites, load_site, get_active_site
from backend.app.core.crs import derive_project_crs
from backend.app.core.site_paths import get_site_paths


def test_list_sites():
    sites = list_sites()
    assert len(sites) >= 2
    site_ids = [s["site_id"] for s in sites]
    assert "bhavanisagar" in site_ids
    assert "hirakud" in site_ids


def test_get_active_site():
    active = get_active_site()
    assert active == "bhavanisagar"


def test_load_bhavanisagar_site():
    site_cfg = load_site("bhavanisagar")
    assert site_cfg.site_id == "bhavanisagar"
    assert site_cfg.identity.dam_name == "Bhavanisagar Dam"
    assert site_cfg.identity.state == "Tamil Nadu"
    assert site_cfg.identity.river_name == "Bhavani River"
    assert site_cfg.study_area.crs.project_crs == "EPSG:32643"
    assert site_cfg.geometry.dam_height_m == 40.0
    assert site_cfg.reservoir.gross_storage_capacity_mcm == 928.8
    assert "bhavanisagar_base" in site_cfg.breach_scenarios


def test_load_hirakud_site():
    site_cfg = load_site("hirakud")
    assert site_cfg.site_id == "hirakud"
    assert site_cfg.identity.dam_name == "Hirakud Dam"
    assert site_cfg.identity.state == "Odisha"
    assert site_cfg.identity.river_name == "Mahanadi River"
    assert site_cfg.study_area.crs.project_crs == "EPSG:32644"  # Different UTM zone
    assert site_cfg.geometry.dam_height_m == 60.96
    assert site_cfg.reservoir.gross_storage_capacity_mcm == 8136.0


def test_automatic_crs_derivation():
    # Bhavanisagar: 11.47N, 77.11E -> Zone 43N (EPSG:32643)
    crs_bhv = derive_project_crs(11.47083, 77.11389)
    assert crs_bhv.project_crs == "EPSG:32643"
    assert crs_bhv.utm_zone == 43

    # Hirakud: 21.57N, 83.87E -> Zone 44N (EPSG:32644)
    crs_hrk = derive_project_crs(21.5700, 83.8694)
    assert crs_hrk.project_crs == "EPSG:32644"
    assert crs_hrk.utm_zone == 44


def test_site_paths_resolution():
    paths_bhv = get_site_paths("bhavanisagar")
    assert paths_bhv.site_id == "bhavanisagar"
    assert paths_bhv.terrain.is_dir() or paths_bhv.site_root.is_dir()

    paths_hrk = get_site_paths("hirakud")
    assert paths_hrk.site_id == "hirakud"
    assert "hirakud" in str(paths_hrk.terrain)
