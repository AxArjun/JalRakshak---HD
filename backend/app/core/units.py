"""
Scientific Unit Safety and Conversion Module for JalRakshak-HD.
SIH PS 26161 - Milestone M3.

Guards against unit conflation between imperial and SI units for dam engineering,
hydrology, and empirical breach modelling.
"""
from __future__ import annotations

from typing import Union

# Length Conversions
FEET_TO_METRES = 0.3048
METRES_TO_FEET = 1.0 / FEET_TO_METRES

# Volume Conversions
# 1 TMC (Thousand Million Cubic Feet) = 1,000,000,000 cu ft = 28,316,846.592 m3 = 28.316846592 MCM
TMC_TO_M3 = 28_316_846.592
TMC_TO_MCM = 28.316846592
MCM_TO_M3 = 1_000_000.0
M3_TO_MCM = 1.0 / MCM_TO_M3
M3_TO_TMC = 1.0 / TMC_TO_M3
ACRE_FEET_TO_M3 = 1233.48183754752

# Time Conversions
HOURS_TO_SECONDS = 3600.0
MINUTES_TO_SECONDS = 60.0
SECONDS_TO_HOURS = 1.0 / 3600.0
SECONDS_TO_MINUTES = 1.0 / 60.0

# Discharge Conversions
CFS_TO_CMS = 0.028316846592
CMS_TO_CFS = 1.0 / CFS_TO_CMS


def feet_to_metres(feet: float) -> float:
    """Convert feet to standard SI metres."""
    if feet is None:
        raise ValueError("Cannot convert None value.")
    return float(feet * FEET_TO_METRES)


def metres_to_feet(metres: float) -> float:
    """Convert metres to feet."""
    if metres is None:
        raise ValueError("Cannot convert None value.")
    return float(metres * METRES_TO_FEET)


def tmc_to_m3(tmc: float) -> float:
    """Convert TMC (Thousand Million Cubic Feet) to cubic metres (m3)."""
    if tmc is None:
        raise ValueError("Cannot convert None value.")
    return float(tmc * TMC_TO_M3)


def mcm_to_m3(mcm: float) -> float:
    """Convert MCM (Million Cubic Metres) to cubic metres (m3)."""
    if mcm is None:
        raise ValueError("Cannot convert None value.")
    return float(mcm * MCM_TO_M3)


def hours_to_seconds(hours: float) -> float:
    """Convert hours to SI seconds."""
    if hours is None:
        raise ValueError("Cannot convert None value.")
    return float(hours * HOURS_TO_SECONDS)


def seconds_to_hours(seconds: float) -> float:
    """Convert seconds to hours."""
    if seconds is None:
        raise ValueError("Cannot convert None value.")
    return float(seconds * SECONDS_TO_HOURS)


def validate_unit(value: float, expected_unit: str, declared_unit: str, param_name: str) -> float:
    """Validate that declared unit matches expected unit before calculation."""
    if declared_unit.lower().strip() != expected_unit.lower().strip():
        raise ValueError(
            f"Unit mismatch for {param_name}: expected '{expected_unit}', got '{declared_unit}'."
        )
    return float(value)


class UnitConverter:
    """Convenience namespace for unit conversions."""

    feet_to_metres = staticmethod(feet_to_metres)
    metres_to_feet = staticmethod(metres_to_feet)
    tmc_to_m3 = staticmethod(tmc_to_m3)
    mcm_to_m3 = staticmethod(mcm_to_m3)
    hours_to_seconds = staticmethod(hours_to_seconds)
    seconds_to_hours = staticmethod(seconds_to_hours)
    validate_unit = staticmethod(validate_unit)

