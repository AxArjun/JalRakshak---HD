"""Tests for volume-constrained triangular hydrograph generation."""

import pytest
import math
from backend.app.schemas.site import BreachScenarioConfig
from backend.app.services.hydrograph import generate_site_hydrograph
from backend.app.services.site_registry import load_site


def test_bhavanisagar_hydrograph_regression():
    site_cfg = load_site("bhavanisagar")
    scenario = site_cfg.breach_scenarios["bhavanisagar_base"]
    summary, df = generate_site_hydrograph(scenario)

    assert math.isclose(summary.peak_discharge_m3s, 18742.38, abs_tol=1.0)
    assert math.isclose(summary.rise_time_s, 14095.59, abs_tol=1.0)
    assert math.isclose(summary.integrated_volume_mcm, 780.5, abs_tol=0.1)
    assert summary.volume_error_percent < 0.1
    assert len(df) > 1000


def test_hirakud_hydrograph_synthesis():
    site_cfg = load_site("hirakud")
    scenario = site_cfg.breach_scenarios["hirakud_screening_01"]
    summary, df = generate_site_hydrograph(scenario)

    assert summary.peak_discharge_m3s > 50000.0
    assert math.isclose(summary.integrated_volume_mcm, 5818.0, abs_tol=1.0)
    assert summary.volume_error_percent < 0.1
