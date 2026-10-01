"""
JalRakshak-HD: Hydrograph Validation Engine (Milestone M4)
=========================================================
Strictly validates all generated breach outflow hydrograph time series and metadata
against rigorous scientific, physical conservation, and dimensional criteria.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
import pandas as pd
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
HYDROGRAPH_DIR = ROOT_DIR / "data" / "dflowfm" / "hydrographs"
VALIDATION_DIR = ROOT_DIR / "outputs" / "validation"
CONFIG_PATH = ROOT_DIR / "configs" / "hydrograph.yaml"


def validate_hydrographs() -> bool:
    print("=" * 80)
    print(" JALRAKSHAK-HD: HYDROGRAPH VALIDATION & SANITY AUDIT (MILESTONE M4)")
    print("=" * 80)

    if not CONFIG_PATH.exists():
        print(f"[FAIL] Missing config file: {CONFIG_PATH}")
        return False

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    tolerance_pct = config.get("hydrograph", {}).get("volume_tolerance_percent", 0.5)
    timestep_s = config.get("hydrograph", {}).get("timestep_seconds", 60.0)

    comparison_path = VALIDATION_DIR / "hydrograph_comparison.json"
    if not comparison_path.exists():
        print(f"[FAIL] Missing comparison manifest: {comparison_path}")
        return False

    with open(comparison_path, "r", encoding="utf-8") as f:
        comparison_data = json.load(f)

    scenarios = comparison_data.get("scenarios", [])
    if not scenarios:
        print("[FAIL] No scenarios found in comparison manifest.")
        return False

    all_passed = True

    print(f"{'Scenario':<28} | {'Qmin>=0':<7} | {'Peak Q':<7} | {'Peak t':<7} | {'Mono':<6} | {'FinalQ=0':<8} | {'Vol Err%':<8} | {'Status'}")
    print("-" * 96)

    for item in scenarios:
        meta = item.get("metadata", {})
        scenario_id = meta.get("scenario_id")
        csv_file = HYDROGRAPH_DIR / f"{scenario_id}.csv"
        tim_file = HYDROGRAPH_DIR / f"{scenario_id}_boundary.tim"

        if not csv_file.exists():
            print(f"[{scenario_id}] Missing CSV: {csv_file}")
            all_passed = False
            continue

        if not tim_file.exists():
            print(f"[{scenario_id}] Missing TIM boundary: {tim_file}")
            all_passed = False
            continue

        # Load CSV
        df = pd.read_csv(csv_file)
        required_cols = ["time_s", "time_hr", "discharge_m3s", "cumulative_volume_m3", "normalized_discharge"]
        for col in required_cols:
            if col not in df.columns:
                print(f"[{scenario_id}] Missing column: {col}")
                all_passed = False

        # 1. No NaN or Inf
        if df.isna().any().any() or np_has_inf(df):
            print(f"[{scenario_id}] Contains NaN or Inf values!")
            all_passed = False

        # 2. Qmin >= 0
        q_min = df["discharge_m3s"].min()
        qmin_ok = q_min >= 0.0

        # 3. Peak discharge match
        q_max = df["discharge_m3s"].max()
        expected_qpeak = meta["peak_discharge_m3s"]
        qmax_ok = math.isclose(q_max, expected_qpeak, rel_tol=1e-3, abs_tol=1e-2)

        # 4. Peak time match within timestep
        peak_idx = df["discharge_m3s"].idxmax()
        peak_time_s = df.loc[peak_idx, "time_s"]
        expected_rise_s = meta["rise_time_s"]
        peakt_ok = abs(peak_time_s - expected_rise_s) <= (timestep_s + 1e-3)

        # 5. Exactly one peak & Monotonicity
        rise_series = df.loc[:peak_idx, "discharge_m3s"]
        recession_series = df.loc[peak_idx:, "discharge_m3s"]
        mono_rise = rise_series.is_monotonic_increasing
        mono_rec = recession_series.is_monotonic_decreasing
        mono_ok = mono_rise and mono_rec

        # 6. Final Q = 0
        final_q = df["discharge_m3s"].iloc[-1]
        final_q_ok = math.isclose(final_q, 0.0, abs_tol=1e-6)

        # 7. Time strictly increasing
        time_increasing = df["time_s"].is_monotonic_increasing and (df["time_s"].diff().iloc[1:] > 0).all()

        # 8. Cumulative volume non-decreasing
        cum_vol_increasing = df["cumulative_volume_m3"].is_monotonic_increasing

        # 9. Integrated volume conservation
        vol_err_pct = meta.get("volume_error_percent", 0.0)
        vol_ok = abs(vol_err_pct) <= tolerance_pct

        # 10. Classification check
        classification = meta.get("classification", "")
        class_ok = "SCREENING_HYDROGRAPH" in classification

        scenario_status = all([
            qmin_ok, qmax_ok, peakt_ok, mono_ok, final_q_ok,
            time_increasing, cum_vol_increasing, vol_ok, class_ok
        ])

        if not scenario_status:
            all_passed = False

        status_str = "PASS" if scenario_status else "FAIL"
        print(
            f"{scenario_id:<28} | "
            f"{'OK' if qmin_ok else 'FAIL':<7} | "
            f"{'OK' if qmax_ok else 'FAIL':<7} | "
            f"{'OK' if peakt_ok else 'FAIL':<7} | "
            f"{'OK' if mono_ok else 'FAIL':<6} | "
            f"{'OK' if final_q_ok else 'FAIL':<8} | "
            f"{vol_err_pct:>7.4f}% | "
            f"{status_str}"
        )

    print("=" * 80)
    if all_passed:
        print("[SUCCESS] All M4 breach outflow hydrographs passed 100% of scientific validation criteria.")
    else:
        print("[ERROR] One or more hydrograph scenarios failed validation.")
    print("=" * 80)

    return all_passed


def np_has_inf(df: pd.DataFrame) -> bool:
    for col in df.select_dtypes(include=["number"]).columns:
        if ((df[col] == float("inf")) | (df[col] == float("-inf"))).any():
            return True
    return False


if __name__ == "__main__":
    success = validate_hydrographs()
    sys.exit(0 if success else 1)
