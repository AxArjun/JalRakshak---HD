"""
Unit and numerical tests for empirical peak discharge models.
SIH PS 26161 - JalRakshak-HD Milestone M4.
"""
from __future__ import annotations

import math
import unittest

from backend.app.services.peak_discharge_models import PeakDischargeModelLibrary


class TestPeakDischargeModels(unittest.TestCase):
    """Test suite verifying empirical peak discharge regressions and input checking."""

    def test_froehlich_1995_peak_numerical_accuracy(self):
        """Verify Froehlich 1995 peak outflow calculation against analytical formula."""
        vw = 780.5 * 1e6  # 780.5 MCM in m3
        hw = 32.0  # m

        res = PeakDischargeModelLibrary.calculate_froehlich_1995_peak(
            water_volume_vw_m3=vw,
            water_depth_hw_m=hw,
        )

        expected_qp = 0.607 * (vw**0.295) * (hw**1.24)
        self.assertTrue(math.isclose(res.peak_discharge_m3s, expected_qp, rel_tol=1e-3))
        # Verify peak is in the expected ~18,700 m3/s magnitude
        self.assertTrue(18000.0 < res.peak_discharge_m3s < 19500.0)
        self.assertEqual(res.required_inputs["input_units"], "SI (m3, m)")
        self.assertEqual(res.required_inputs["output_units"], "SI (m3/s)")

    def test_froehlich_1995_formation_time(self):
        """Verify Froehlich 1995 formation time calculation."""
        vw = 780.5 * 1e6
        hb = 40.0

        tf_s = PeakDischargeModelLibrary.calculate_froehlich_1995_formation_time(
            water_volume_vw_m3=vw,
            breach_height_hb_m=hb,
        )

        expected_tf_hr = 0.00254 * (vw**0.53) * (hb**-0.9)
        expected_tf_s = expected_tf_hr * 3600.0
        self.assertTrue(math.isclose(tf_s, expected_tf_s, rel_tol=1e-3))
        self.assertTrue(tf_s > 0)

    def test_macdonald_wahl_peak_numerical_accuracy(self):
        """Verify MacDonald / Wahl 1998 SI peak outflow calculation."""
        vw = 780.5 * 1e6
        hw = 32.0

        res = PeakDischargeModelLibrary.calculate_macdonald_langridge_monopolis_peak_wahl(
            water_volume_vw_m3=vw,
            water_depth_hw_m=hw,
        )

        expected_qp = 1.154 * ((vw * hw) ** 0.412)
        self.assertTrue(math.isclose(res.peak_discharge_m3s, expected_qp, rel_tol=1e-3))
        self.assertTrue(21000.0 < res.peak_discharge_m3s < 23500.0)

    def test_zero_and_negative_input_rejection(self):
        """Ensure invalid non-positive inputs raise ValueError."""
        with self.assertRaises(ValueError):
            PeakDischargeModelLibrary.calculate_froehlich_1995_peak(water_volume_vw_m3=-100, water_depth_hw_m=30)

        with self.assertRaises(ValueError):
            PeakDischargeModelLibrary.calculate_froehlich_1995_peak(water_volume_vw_m3=1000, water_depth_hw_m=0)

        with self.assertRaises(ValueError):
            PeakDischargeModelLibrary.calculate_froehlich_1995_formation_time(water_volume_vw_m3=0, breach_height_hb_m=40)

        with self.assertRaises(ValueError):
            PeakDischargeModelLibrary.calculate_macdonald_langridge_monopolis_peak_wahl(water_volume_vw_m3=1000, water_depth_hw_m=-5)


if __name__ == "__main__":
    unittest.main()
