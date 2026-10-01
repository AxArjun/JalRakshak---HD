"""Generic Dam Breach Hydrograph Service for JalRakshak-HD.

Synthesizes mathematically volume-constrained breach hydrographs for any configured site
using established empirical parametric breach models (Froehlich 2008/1995, MacDonald et al.).
"""

from __future__ import annotations

import math
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel

from backend.app.schemas.site import (
    SiteConfig,
    DamGeometry,
    ReservoirMetadata,
    BreachScenarioConfig,
)


class HydrographResult(BaseModel):
    scenario_id: str
    peak_discharge_m3s: float
    rise_time_s: float
    total_duration_s: float
    target_volume_mcm: float
    integrated_volume_mcm: float
    volume_error_percent: float
    time_series_points: int
    classification: str = "VOLUME_CONSTRAINED_TRIANGULAR_SCREENING_HYDROGRAPH"


def compute_breach_parameters(
    reservoir_volume_mcm: float,
    breach_height_m: float,
    water_depth_hw_m: Optional[float] = None,
    failure_mode: str = "OVERTOPPING",
    breach_method: str = "Froehlich_2008",
) -> Dict[str, float]:
    """Compute empirical breach width, formation time, and peak discharge.

    Parameters
    ----------
    reservoir_volume_mcm : float
        Active reservoir storage volume at breach in MCM (million cubic metres).
    breach_height_m : float
        Height of the breach structure in metres (h_b).
    water_depth_hw_m : Optional[float]
        Hydraulic water depth above breach invert in metres (h_w). If None, defaults to breach_height_m.
    failure_mode : str
        Failure mode ('OVERTOPPING' or 'PIPING' or 'PRESCRIBED_BREACH').
    breach_method : str
        Method name ('Froehlich_2008').

    Returns
    -------
    Dict[str, float]
        Dictionary with average_breach_width_m, formation_time_s, peak_discharge_m3s.
    """
    volume_m3 = reservoir_volume_mcm * 1e6
    g = 9.80665
    hw = water_depth_hw_m if water_depth_hw_m is not None else breach_height_m

    if failure_mode.upper() == "OVERTOPPING":
        k_0 = 1.3
        z = 0.7
    else:
        k_0 = 1.0
        z = 1.0

    # Froehlich (2008) equations:
    # B_avg = 0.27 * K_0 * V_w^0.32 * h_b^0.04
    b_avg = 0.27 * k_0 * (volume_m3 ** 0.32) * (breach_height_m ** 0.04)

    # t_f = 63.2 * sqrt(V_w / (g * h_b^2))
    t_f = 63.2 * math.sqrt(volume_m3 / (g * (breach_height_m ** 2)))

    # Froehlich (1995) Peak Discharge:
    # Q_p = 0.607 * V_w^0.295 * h_w^1.24
    q_p = 0.607 * (volume_m3 ** 0.295) * (hw ** 1.24)

    return {
        "average_breach_width_m": round(b_avg, 2),
        "formation_time_s": round(t_f, 2),
        "peak_discharge_m3s": round(q_p, 2),
        "side_slope_z": z,
    }


def generate_site_hydrograph(
    scenario: BreachScenarioConfig,
    timestep_s: float = 60.0
) -> Tuple[HydrographResult, pd.DataFrame]:
    """Generate a volume-constrained triangular hydrograph for a scenario config.

    Parameters
    ----------
    scenario : BreachScenarioConfig
        Validated breach scenario specification.
    timestep_s : float
        Uniform discrete time step in seconds.

    Returns
    -------
    Tuple[HydrographResult, pd.DataFrame]
        Summary metadata and full time-series DataFrame (time_s, discharge_m3s, cumulative_volume_m3).
    """
    if not scenario.reservoir_volume_at_breach_mcm or scenario.reservoir_volume_at_breach_mcm <= 0:
        raise ValueError(f"Scenario {scenario.scenario_id}: Invalid volume {scenario.reservoir_volume_at_breach_mcm}")

    volume_m3 = scenario.reservoir_volume_at_breach_mcm * 1e6
    q_peak = scenario.peak_discharge_m3s
    rise_time_s = scenario.breach_formation_time_s

    # Derive peak and formation time if not explicitly provided
    if q_peak is None or rise_time_s is None:
        params = compute_breach_parameters(
            reservoir_volume_mcm=scenario.reservoir_volume_at_breach_mcm,
            breach_height_m=scenario.breach_height_m or 32.0,
            failure_mode=scenario.breach_formation_mode,
        )
        q_peak = q_peak or params["peak_discharge_m3s"]
        rise_time_s = rise_time_s or params["formation_time_s"]

    # Total duration for exact volume conservation: T = 2 * V_w / Q_peak
    total_duration_s = (2.0 * volume_m3) / q_peak
    recession_time_s = total_duration_s - rise_time_s

    if recession_time_s <= 0:
        raise ValueError(
            f"Physical impossibility: Rise time {rise_time_s}s exceeds total duration {total_duration_s}s."
        )

    times = list(np.arange(0.0, total_duration_s, timestep_s))
    if abs(times[-1] - total_duration_s) > 1e-3:
        times.append(total_duration_s)
    if not any(math.isclose(t, rise_time_s, abs_tol=1e-3) for t in times):
        times.append(rise_time_s)
    times = sorted(list(set([round(t, 4) for t in times])))

    discharges = []
    for t in times:
        if t <= rise_time_s:
            q = q_peak * (t / rise_time_s)
        elif t <= total_duration_s:
            q = q_peak * (1.0 - (t - rise_time_s) / recession_time_s)
        else:
            q = 0.0
        discharges.append(max(0.0, round(q, 4)))

    cumulative_vols = [0.0]
    for i in range(len(times) - 1):
        dt = times[i + 1] - times[i]
        dv = 0.5 * (discharges[i] + discharges[i + 1]) * dt
        cumulative_vols.append(cumulative_vols[-1] + dv)

    integrated_volume_m3 = cumulative_vols[-1]
    integrated_volume_mcm = integrated_volume_m3 / 1e6
    vol_err = abs(integrated_volume_m3 - volume_m3) / volume_m3 * 100.0

    df = pd.DataFrame({
        "time_seconds": times,
        "time_hours": [round(t / 3600.0, 4) for t in times],
        "discharge_m3s": discharges,
        "cumulative_volume_m3": cumulative_vols,
    })

    summary = HydrographResult(
        scenario_id=scenario.scenario_id,
        peak_discharge_m3s=round(q_peak, 2),
        rise_time_s=round(rise_time_s, 2),
        total_duration_s=round(total_duration_s, 2),
        target_volume_mcm=round(scenario.reservoir_volume_at_breach_mcm, 2),
        integrated_volume_mcm=round(integrated_volume_mcm, 2),
        volume_error_percent=round(vol_err, 4),
        time_series_points=len(times),
    )

    return summary, df
