"""
Volume-Constrained Triangular Screening Hydrograph Generator.
SIH PS 26161 - Milestone M4.

Implements mathematically volume-constrained triangular hydrograph synthesis for
empirical breach outflow forcing without fabricating dynamic reservoir routing.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from backend.app.models.hydrograph import (
    HydrographClassification,
    HydrographMetadata,
    HydrographPoint,
    HydrographScenario,
    HydrographShape,
    HydrographValidation,
)


class HydrographGenerator:
    """Service to synthesize volume-constrained screening hydrographs."""

    @staticmethod
    def generate_triangular_hydrograph(
        scenario_id: str,
        scenario_name: str,
        peak_discharge_m3s: float,
        rise_time_s: float,
        target_volume_m3: float,
        breach_geometry_model: str,
        peak_discharge_model: str,
        volume_source: str,
        rise_time_source: str,
        limitations: str,
        timestep_seconds: float = 60.0,
        volume_tolerance_percent: float = 0.5,
    ) -> Tuple[HydrographScenario, pd.DataFrame]:
        """
        Synthesizes a volume-constrained triangular screening hydrograph.

        Total Duration: T = 2 * V_w / Q_peak
        Recession Time: t_recession = T - t_rise
        """
        if peak_discharge_m3s <= 0:
            raise ValueError(f"Peak discharge must be > 0 (got {peak_discharge_m3s}).")
        if target_volume_m3 <= 0:
            raise ValueError(f"Target volume must be > 0 (got {target_volume_m3}).")
        if rise_time_s <= 0:
            raise ValueError(f"Rise time must be > 0 (got {rise_time_s}).")

        # Total duration constrained strictly by total water volume V_w
        total_duration_s = (2.0 * target_volume_m3) / peak_discharge_m3s
        recession_time_s = total_duration_s - rise_time_s

        if recession_time_s <= 0:
            raise ValueError(
                f"Physical impossibility: Rise time ({rise_time_s:.2f} s) exceeds total duration ({total_duration_s:.2f} s)."
            )

        # Build discrete uniform time array with 60s step, ensuring exact peak and end times are included
        times = list(np.arange(0.0, total_duration_s, timestep_seconds))
        if abs(times[-1] - total_duration_s) > 1e-3:
            times.append(total_duration_s)

        # Ensure exact rise_time_s is present in the grid for perfect peak capture
        if not any(math.isclose(t, rise_time_s, abs_tol=1e-3) for t in times):
            times.append(rise_time_s)
        times = sorted(list(set([round(t, 4) for t in times])))

        # Compute piecewise linear discharge Q(t)
        discharges = []
        for t in times:
            if t <= rise_time_s:
                q = peak_discharge_m3s * (t / rise_time_s)
            elif t <= total_duration_s:
                q = peak_discharge_m3s * (1.0 - (t - rise_time_s) / recession_time_s)
            else:
                q = 0.0
            discharges.append(max(0.0, round(q, 4)))

        # Trapezoidal numerical integration of cumulative volume
        cumulative_vols = [0.0]
        for i in range(len(times) - 1):
            dt = times[i + 1] - times[i]
            dv = 0.5 * (discharges[i] + discharges[i + 1]) * dt
            cumulative_vols.append(cumulative_vols[-1] + dv)

        integrated_volume_m3 = cumulative_vols[-1]
        vol_error_percent = abs(integrated_volume_m3 - target_volume_m3) / target_volume_m3 * 100.0

        # Build DataFrame
        df = pd.DataFrame(
            {
                "time_s": times,
                "time_hr": [round(t / 3600.0, 4) for t in times],
                "discharge_m3s": discharges,
                "cumulative_volume_m3": [round(v, 2) for v in cumulative_vols],
                "normalized_discharge": [round(q / peak_discharge_m3s, 4) for q in discharges],
            }
        )

        # Perform rigorous validation checks
        is_non_negative = bool(all(df["discharge_m3s"] >= 0.0))
        peak_idx = int(df["discharge_m3s"].idxmax())
        has_single_peak = (df["discharge_m3s"].iloc[peak_idx] == df["discharge_m3s"].max())
        is_monotonic_rise = bool(df["discharge_m3s"].iloc[:peak_idx].is_monotonic_increasing)
        is_monotonic_recession = bool(df["discharge_m3s"].iloc[peak_idx:].is_monotonic_decreasing)
        is_final_zero = math.isclose(df["discharge_m3s"].iloc[-1], 0.0, abs_tol=1e-3)
        is_vol_conserved = vol_error_percent <= volume_tolerance_percent

        peak_match_err = abs(df["discharge_m3s"].max() - peak_discharge_m3s) / peak_discharge_m3s * 100.0
        rise_time_match_err = abs(df["time_s"].iloc[peak_idx] - rise_time_s)

        validation_status = "PASS" if (
            is_non_negative
            and has_single_peak
            and is_monotonic_rise
            and is_monotonic_recession
            and is_final_zero
            and is_vol_conserved
        ) else "FAIL"

        validation = HydrographValidation(
            scenario_id=scenario_id,
            is_non_negative=is_non_negative,
            has_single_peak=has_single_peak,
            is_monotonic_rise=is_monotonic_rise,
            is_monotonic_recession=is_monotonic_recession,
            is_final_discharge_zero=is_final_zero,
            is_volume_conserved=is_vol_conserved,
            volume_error_percent=round(vol_error_percent, 4),
            peak_matching_error_percent=round(peak_match_err, 4),
            rise_time_matching_error_s=round(rise_time_match_err, 2),
            overall_status=validation_status,
        )

        mean_discharge = integrated_volume_m3 / total_duration_s
        peak_to_mean = peak_discharge_m3s / mean_discharge if mean_discharge > 0 else 0.0

        metadata = HydrographMetadata(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            classification=HydrographClassification.SCREENING_HYDROGRAPH,
            hydrograph_shape=HydrographShape.VOLUME_CONSTRAINED_TRIANGULAR,
            breach_geometry_model=breach_geometry_model,
            peak_discharge_model=peak_discharge_model,
            volume_source=volume_source,
            rise_time_source=rise_time_source,
            target_volume_m3=round(target_volume_m3, 2),
            integrated_volume_m3=round(integrated_volume_m3, 2),
            volume_error_percent=round(vol_error_percent, 4),
            peak_discharge_m3s=round(peak_discharge_m3s, 2),
            rise_time_s=round(rise_time_s, 2),
            rise_time_hr=round(rise_time_s / 3600.0, 4),
            recession_time_s=round(recession_time_s, 2),
            recession_time_hr=round(recession_time_s / 3600.0, 4),
            total_duration_s=round(total_duration_s, 2),
            total_duration_hr=round(total_duration_s / 3600.0, 4),
            mean_discharge_m3s=round(mean_discharge, 2),
            peak_to_mean_ratio=round(peak_to_mean, 4),
            limitations=limitations,
        )

        scenario = HydrographScenario(
            metadata=metadata,
            validation=validation,
            points_count=len(df),
            csv_file_path=f"data/dflowfm/hydrographs/{scenario_id}.csv",
            boundary_tim_file_path=f"data/dflowfm/hydrographs/{scenario_id}_boundary.tim",
        )

        return scenario, df

    @staticmethod
    def export_boundary_tim_file(df: pd.DataFrame, output_path: Path) -> None:
        """
        Exports a D-Flow FM boundary time series (.tim) file.
        Format: Two space-separated columns:
          time_in_minutes discharge_m3s
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for _, row in df.iterrows():
                time_min = row["time_s"] / 60.0
                q = row["discharge_m3s"]
                f.write(f"{time_min:10.2f} {q:12.4f}\n")
