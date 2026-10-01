"""
Empirical peak-discharge regression models for dam breach outflows.
SIH PS 26161 - Milestone M4.

Implements exact published SI empirical equations from peer-reviewed literature
and agency guidance (Froehlich 1995, MacDonald & Langridge-Monopolis 1984 / Wahl 1998).
"""
from __future__ import annotations

import math
from typing import Any, Dict

from backend.app.core.units import UnitConverter
from backend.app.models.hydrograph import PeakDischargeEstimate


class PeakDischargeModelLibrary:
    """Rigorous empirical peak outflow regression service."""

    @staticmethod
    def calculate_froehlich_1995_peak(
        water_volume_vw_m3: float,
        water_depth_hw_m: float,
    ) -> PeakDischargeEstimate:
        """
        Calculates peak breach discharge using Froehlich (1995).

        Source: Froehlich, D. C. (1995). "Peak Outflow from Breached Embankment Dam",
        Journal of Water Resources Planning and Management, ASCE, Vol. 121, No. 1, pp. 90-97.
        Equation:
          Q_p = 0.607 * V_w^0.295 * h_w^1.24

        Inputs:
          water_volume_vw_m3: Volume of water above breach invert at failure (m3)
          water_depth_hw_m: Depth of water above breach invert at failure (m)
        Output:
          Peak discharge Q_p (m3/s)
        """
        if water_volume_vw_m3 <= 0:
            raise ValueError(f"Water volume V_w must be strictly positive (got {water_volume_vw_m3}).")
        if water_depth_hw_m <= 0:
            raise ValueError(f"Water depth h_w must be strictly positive (got {water_depth_hw_m}).")

        q_p = 0.607 * (water_volume_vw_m3**0.295) * (water_depth_hw_m**1.24)

        return PeakDischargeEstimate(
            model_name="Froehlich (1995)",
            authors="David C. Froehlich",
            publication_year=1995,
            peak_discharge_m3s=round(q_p, 2),
            required_inputs={
                "V_w_m3": water_volume_vw_m3,
                "h_w_m": water_depth_hw_m,
                "input_units": "SI (m3, m)",
                "output_units": "SI (m3/s)",
            },
            formula_traceability="Froehlich (1995) ASCE J. Water Resour. Plann. Manage. 121(1): Eq. 2",
            calibration_notes="Calibrated against 22 historical dam failure cases with volume up to 660 MCM and height up to 85 m.",
            validity_assessment="Standard parametric peak outflow regression for embankment dam failures.",
        )

    @staticmethod
    def calculate_froehlich_1995_formation_time(
        water_volume_vw_m3: float,
        breach_height_hb_m: float,
    ) -> float:
        """
        Calculates breach formation time using Froehlich (1995).

        Source: Froehlich, D. C. (1995). "Peak Outflow from Breached Embankment Dam",
        ASCE J. Water Resour. Plann. Manage. 121(1), pp. 90-97.
        Equation:
          t_f (hr) = 0.00254 * V_w^0.53 * h_b^-0.9
        Returns:
          Formation time in seconds (SI)
        """
        if water_volume_vw_m3 <= 0:
            raise ValueError(f"Water volume V_w must be strictly positive (got {water_volume_vw_m3}).")
        if breach_height_hb_m <= 0:
            raise ValueError(f"Breach height h_b must be strictly positive (got {breach_height_hb_m}).")

        tf_hours = 0.00254 * (water_volume_vw_m3**0.53) * (breach_height_hb_m**-0.9)
        tf_seconds = tf_hours * 3600.0
        return round(tf_seconds, 2)

    @staticmethod
    def calculate_macdonald_langridge_monopolis_peak_wahl(
        water_volume_vw_m3: float,
        water_depth_hw_m: float,
    ) -> PeakDischargeEstimate:
        """
        Calculates peak breach outflow using MacDonald & Langridge-Monopolis (1984) / Wahl (1998, 2004).

        Source: MacDonald, T. C., & Langridge-Monopolis, J. (1984). ASCE J. Hydraul. Eng. 110(5);
        Wahl, T. L. (1998). "Prediction of Embankment Dam Breach Parameters", USBR DSO-98-004, Table 5.
        SI Equation:
          Q_p = 1.154 * (V_w * h_w)^0.412

        Inputs:
          water_volume_vw_m3: Stored volume above breach invert (m3)
          water_depth_hw_m: Height of water above breach invert (m)
        Output:
          Peak discharge Q_p (m3/s)
        """
        if water_volume_vw_m3 <= 0:
            raise ValueError(f"Water volume V_w must be strictly positive (got {water_volume_vw_m3}).")
        if water_depth_hw_m <= 0:
            raise ValueError(f"Water depth h_w must be strictly positive (got {water_depth_hw_m}).")

        formation_factor = water_volume_vw_m3 * water_depth_hw_m
        q_p = 1.154 * (formation_factor**0.412)

        return PeakDischargeEstimate(
            model_name="MacDonald & Langridge-Monopolis (1984) / Wahl (1998)",
            authors="Thomas C. MacDonald and Jennifer Langridge-Monopolis (SI form by Tony L. Wahl)",
            publication_year=1998,
            peak_discharge_m3s=round(q_p, 2),
            required_inputs={
                "V_w_m3": water_volume_vw_m3,
                "h_w_m": water_depth_hw_m,
                "breach_formation_factor_m4": formation_factor,
                "input_units": "SI (m3, m)",
                "output_units": "SI (m3/s)",
            },
            formula_traceability="USBR DSO-98-004 Table 5 / Wahl (2004) Eq. 6",
            calibration_notes="Evaluated across 42 historical dam failures (23 earthfill, 19 rockfill).",
            validity_assessment="Standard upper-envelope peak outflow regression based on breach formation factor.",
        )
