"""Tests for site configuration validation rule engine and workflow gates."""

import pytest
from backend.app.services.site_registry import load_site
from backend.app.services.site_validator import validate_site_config
from backend.app.services.workflow_gates import evaluate_workflow_gates
from backend.app.schemas.site import GateStatus


def test_bhavanisagar_validation():
    site_cfg = load_site("bhavanisagar")
    report = validate_site_config(site_cfg)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_hirakud_validation():
    site_cfg = load_site("hirakud")
    report = validate_site_config(site_cfg)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_bhavanisagar_workflow_gates():
    site_cfg = load_site("bhavanisagar")
    status = evaluate_workflow_gates(site_cfg)
    assert status.gate_a_location == GateStatus.READY
    assert status.gate_b_terrain == GateStatus.READY
    assert status.gate_c_hydrology == GateStatus.READY
    assert status.gate_d_engineering == GateStatus.READY
    assert status.gate_e_breach == GateStatus.READY
    assert status.gate_f_hydraulic == GateStatus.READY
    assert status.gate_g_consequence == GateStatus.READY
    assert status.gate_h_earth_observation == GateStatus.READY


def test_hirakud_workflow_gates():
    site_cfg = load_site("hirakud")
    status = evaluate_workflow_gates(site_cfg)
    assert status.gate_a_location == GateStatus.READY
    assert status.gate_b_terrain == GateStatus.READY
    assert status.gate_c_hydrology == GateStatus.READY
    assert status.gate_d_engineering == GateStatus.READY
    assert status.gate_e_breach == GateStatus.READY
    # Production solvers not executed for second site in M11
    assert status.gate_g_consequence == GateStatus.BLOCKED
