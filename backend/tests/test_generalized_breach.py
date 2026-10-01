"""Regression and generalization tests for empirical dam breach parameter calculations."""

import pytest
import math
from backend.app.services.hydrograph import compute_breach_parameters
from backend.app.services.site_registry import load_site


def test_bhavanisagar_m3_breach_regression():
    """Verify that generalized breach calculation preserves exact M3/M4 Bhavanisagar values."""
    # Inputs from BHV_BASE in configs/breach_scenarios.yaml:
    # active volume = 780.5 MCM, structural breach height = 40.0 m, hydraulic depth hw = 32.0 m, K_0 = 1.0
    res = compute_breach_parameters(
        reservoir_volume_mcm=780.5,
        breach_height_m=40.0,
        water_depth_hw_m=32.0,
        failure_mode="PRESCRIBED_BREACH",
    )

    assert math.isclose(res["average_breach_width_m"], 219.28, abs_tol=0.05)
    assert math.isclose(res["formation_time_s"], 14095.59, abs_tol=0.5)
    assert math.isclose(res["peak_discharge_m3s"], 18742.38, abs_tol=0.5)
    assert res["side_slope_z"] == 1.0


def test_hirakud_breach_calculation():
    """Verify second-site breach parameter derivation."""
    res = compute_breach_parameters(
        reservoir_volume_mcm=5818.0,
        breach_height_m=48.0,
        failure_mode="OVERTOPPING",
    )

    assert res["average_breach_width_m"] > 400.0  # ~541.34 m
    assert res["formation_time_s"] > 20000.0      # ~32025 s
    assert res["peak_discharge_m3s"] > 40000.0    # ~56420 m3/s
