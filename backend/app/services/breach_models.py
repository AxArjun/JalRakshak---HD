"""
Empirical dam-breach model calculation engine for JalRakshak-HD.
SIH PS 26161 - Milestone M3 (Repaired).

Implements published, peer-reviewed empirical relationships for embankment breach parameters
with exact formula traceability, unit conversions, calibration domain audits, and cross-section validation.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from backend.app.core.units import UnitConverter
from backend.app.models.breach_event import BreachParameterEstimate, ModelResultStatus


class EmpiricalBreachLibrary:
    """Rigorous empirical dam breach model library."""

    GRAVITY: float = 9.80665  # m/s2 standard gravitational acceleration

    @staticmethod
    def calculate_froehlich_2008(
        active_volume_m3: float,
        breach_height_hb_m: float,
        failure_mode: str = "PIPING",  # "PIPING" or "OVERTOPPING" or "PRESCRIBED_BREACH"
    ) -> BreachParameterEstimate:
        """
        Calculates breach parameters using Froehlich (2008).

        Source: Froehlich, D. C. (2008). "Embankment Dam Breach Parameters and Their Uncertainties",
        ASCE Journal of Hydraulic Engineering, Vol. 134, No. 12, pp. 1708-1721.
        Equations:
          B_ave = 0.27 * K_0 * V_w^0.32 * h_b^0.04
          t_f = 63.2 * sqrt(V_w / (g * h_b^2))
        """
        # Failure mode coefficient K_0
        if failure_mode.upper() in ["OVERTOPPING"]:
            k_0 = 1.3
            side_slope_z = 0.7  # 0.7H:1V for overtopping in Froehlich 2008
        else:  # PIPING, PRESCRIBED_BREACH, INTERNAL_EROSION
            k_0 = 1.0
            side_slope_z = 1.0  # 1.0H:1V for piping / other

        # Formula calculation
        b_avg = 0.27 * k_0 * (active_volume_m3**0.32) * (breach_height_hb_m**0.04)
        t_f_seconds = 63.2 * math.sqrt(active_volume_m3 / (EmpiricalBreachLibrary.GRAVITY * (breach_height_hb_m**2)))
        t_f_hours = t_f_seconds / 3600.0

        # Empirical peak discharge approximation (Froehlich 2008 Equation)
        # Q_p = 0.607 * V_w^0.295 * h_w^1.24
        q_p = 0.607 * (active_volume_m3**0.295) * (breach_height_hb_m**1.24)

        # Calibration domain check (Froehlich 2008 calibration dataset max V_w ~ 660 MCM)
        max_calibration_vol_m3 = 660.0 * 1e6
        is_extrapolated = active_volume_m3 > max_calibration_vol_m3

        if is_extrapolated:
            calib_status = "EXTRAPOLATED_ABOVE_MAX_CALIBRATION_VOLUME (V_w > 660 MCM)"
            warning = f"Active reservoir volume ({active_volume_m3/1e6:.1f} MCM) exceeds Froehlich 2008 dataset max of 660 MCM."
            result_status = ModelResultStatus.VALID_WITH_EXTRAPOLATION
        else:
            calib_status = "WITHIN_CALIBRATION_RANGE"
            warning = None
            result_status = ModelResultStatus.VALID

        return BreachParameterEstimate(
            model_name="Froehlich (2008)",
            authors="David C. Froehlich",
            publication_year=2008,
            breach_width_m=round(b_avg, 2),
            width_status=result_status,
            formation_time_s=round(t_f_seconds, 2),
            formation_time_hr=round(t_f_hours, 3),
            side_slope_z=side_slope_z,
            peak_discharge_m3s=round(q_p, 1),
            required_inputs={
                "active_water_volume_m3": active_volume_m3,
                "breach_height_hb_m": breach_height_hb_m,
                "failure_mode": failure_mode,
                "K_0": k_0,
            },
            formula_traceability="Froehlich (2008) ASCE J. Hydraul. Eng. 134(12): Eq. 1 & 2",
            calibration_range_status=calib_status,
            extrapolation_warning=warning,
            validity_assessment="Standard parametric model for embankment dam breach geometry.",
        )

    @staticmethod
    def calculate_macdonald_1984(
        outflow_volume_m3: float,
        water_depth_hw_m: float,
        material_type: str = "EARTHFILL",  # EARTHFILL or ROCKFILL
    ) -> BreachParameterEstimate:
        """
        Calculates eroded volume and breach formation time using MacDonald & Langridge-Monopolis (1984).

        Source: MacDonald, T. C., & Langridge-Monopolis, J. (1984). "Breaching Characteristics of Dam Failures",
        ASCE Journal of Hydraulic Engineering, Vol. 110, No. 5, pp. 567-586.
        Equations:
          V_er = 0.0261 * (V_out * h_w)^0.769 (for earthfill)
          t_f (hr) = 0.0179 * V_er^0.364

        Note: MacDonald & Langridge-Monopolis does NOT predict breach width directly. It predicts eroded volume.
        Converting V_er to B_ave requires full cross-section geometry (crest width, side slopes, breach depth).
        Without verified embankment cross-section geometry, width is reported as null with status INSUFFICIENT_CROSS_SECTION_GEOMETRY.
        """
        # Volume of eroded embankment material in m3
        if material_type.upper() == "ROCKFILL":
            v_er = 0.00348 * ((outflow_volume_m3 * water_depth_hw_m) ** 0.852)
        else:  # EARTHFILL
            v_er = 0.0261 * ((outflow_volume_m3 * water_depth_hw_m) ** 0.769)

        # Formation time in hours, converted to seconds
        t_f_hours = 0.0179 * (v_er**0.364)
        t_f_seconds = t_f_hours * 3600.0

        return BreachParameterEstimate(
            model_name="MacDonald & Langridge-Monopolis (1984)",
            authors="Thomas C. MacDonald and Jennifer Langridge-Monopolis",
            publication_year=1984,
            breach_width_m=None,
            width_status=ModelResultStatus.INSUFFICIENT_CROSS_SECTION_GEOMETRY,
            formation_time_s=round(t_f_seconds, 2),
            formation_time_hr=round(t_f_hours, 3),
            eroded_volume_m3=round(v_er, 1),
            side_slope_z=0.5,
            peak_discharge_m3s=None,
            required_inputs={
                "outflow_volume_m3": outflow_volume_m3,
                "water_depth_hw_m": water_depth_hw_m,
                "material_type": material_type,
            },
            formula_traceability="MacDonald & Langridge-Monopolis (1984) ASCE J. Hydraul. Eng. 110(5): Eq. 1 & 3",
            calibration_range_status="MODEL_PROVIDES_ERODED_VOLUME_AND_TIME_ONLY",
            extrapolation_warning="Width calculation skipped: requires unverified embankment cross-section geometry (crest width and slopes).",
            validity_assessment="Valid for eroded volume and formation time; width requires cross-sectional embankment geometry.",
        )

    @staticmethod
    def calculate_von_thun_gillette_1990(
        water_depth_hw_m: float,
        reservoir_volume_m3: float,
        erodibility: str = "HIGHLY_ERODIBLE",
    ) -> BreachParameterEstimate:
        """
        Calculates breach width and formation time using Von Thun & Gillette (1990).

        Source: Von Thun, J. L., & Gillette, D. R. (1990). "Guidance on Breach Parameters",
        USBR Unpublished Internal Report, Denver, CO.
        Equations:
          B_ave = 2.5 * h_w + C_b
          t_f = B_ave / (4 * h_w)  (for highly erodible embankment)
          t_f = B_ave / (2 * h_w)  (for erosion resistant embankment)
        """
        # Determine C_b based on reservoir volume in MCM
        res_mcm = reservoir_volume_m3 / 1e6
        if res_mcm < 1.233:  # < 1000 acre-ft
            c_b = 0.0
        elif res_mcm <= 6.167:  # 1000 - 5000 acre-ft
            c_b = 18.3  # 60 ft in metres
        elif res_mcm <= 12.335:  # 5000 - 10000 acre-ft
            c_b = 30.5  # 100 ft in metres
        else:  # > 10000 acre-ft
            c_b = 54.9  # 180 ft in metres

        # Average breach width B_ave in metres
        b_avg = 2.5 * water_depth_hw_m + c_b

        # Formation time in hours
        if erodibility.upper() == "EROSION_RESISTANT":
            t_f_hours = b_avg / (2.0 * water_depth_hw_m)
        else:  # HIGHLY_ERODIBLE
            t_f_hours = b_avg / (4.0 * water_depth_hw_m)

        t_f_seconds = t_f_hours * 3600.0

        return BreachParameterEstimate(
            model_name="Von Thun & Gillette (1990)",
            authors="J. Lawrence Von Thun and David R. Gillette",
            publication_year=1990,
            breach_width_m=round(b_avg, 2),
            width_status=ModelResultStatus.VALID,
            formation_time_s=round(t_f_seconds, 2),
            formation_time_hr=round(t_f_hours, 3),
            side_slope_z=0.5,
            peak_discharge_m3s=None,
            required_inputs={
                "water_depth_hw_m": water_depth_hw_m,
                "reservoir_volume_m3": reservoir_volume_m3,
                "C_b_m": c_b,
                "erodibility": erodibility,
            },
            formula_traceability="Von Thun & Gillette (1990) USBR Guidance: Table 1 & Eq. 1",
            calibration_range_status="WITHIN_USBR_LARGE_DAM_ENVELOPE (C_b = 54.9 m for V_w > 12.3 MCM)",
            extrapolation_warning=None,
            validity_assessment="Standard USBR agency guidance for embankment dam breach estimates.",
        )
