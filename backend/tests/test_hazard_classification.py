"""
Unit tests for CWC / AIDR H1-H6 combined flood hazard classification service.
"""

import numpy as np
import pytest

from backend.app.services.hazard_classification import (
    HazardClass,
    classify_hazard,
    classify_hazard_vectorized,
)


def test_dry_classification():
    """Verify that cells below wetting threshold are classified as DRY (0)."""
    assert classify_hazard(0.0, 0.0) == HazardClass.DRY
    assert classify_hazard(0.04, 2.0) == HazardClass.DRY
    assert classify_hazard(np.nan, 1.0) == HazardClass.DRY
    assert classify_hazard(1.0, np.nan) == HazardClass.DRY


def test_h1_classification():
    """H1: Generally safe for people, vehicles, buildings (D*V <= 0.3, D <= 0.3, V <= 2.0)."""
    assert classify_hazard(0.1, 0.5) == HazardClass.H1  # DV = 0.05
    assert classify_hazard(0.25, 1.0) == HazardClass.H1  # DV = 0.25
    assert classify_hazard(0.3, 1.0) == HazardClass.H1  # DV = 0.3


def test_h2_classification():
    """H2: Unsafe for small vehicles (D*V <= 0.6, D <= 0.5, V <= 2.0; D > 0.3 or D*V > 0.3)."""
    assert classify_hazard(0.2, 2.0) == HazardClass.H2  # D <= 0.3, DV = 0.4 > 0.3
    assert classify_hazard(0.4, 0.5) == HazardClass.H2  # D = 0.4 > 0.3, DV = 0.2 <= 0.6
    assert classify_hazard(0.5, 1.0) == HazardClass.H2  # D = 0.5, DV = 0.5 <= 0.6


def test_h3_classification():
    """H3: Unsafe for vehicles, children, and elderly (D*V <= 0.6, D <= 1.2, V <= 2.0; D > 0.5)."""
    assert classify_hazard(0.6, 0.5) == HazardClass.H3  # D = 0.6 > 0.5, DV = 0.3 <= 0.6
    assert classify_hazard(0.8, 0.6) == HazardClass.H3  # D = 0.8 > 0.5, DV = 0.48 <= 0.6
    assert classify_hazard(1.1, 0.5) == HazardClass.H3  # D = 1.1 > 0.5, DV = 0.55 <= 0.6


def test_h4_classification():
    """H4: Unsafe for vehicles and people (D*V <= 1.0, D <= 2.0, V <= 2.0; D > 1.2 or D*V > 0.6)."""
    assert classify_hazard(0.8, 1.0) == HazardClass.H4  # D = 0.8 <= 1.2, DV = 0.8 > 0.6
    assert classify_hazard(1.5, 0.5) == HazardClass.H4  # D = 1.5 > 1.2, DV = 0.75 <= 1.0
    assert classify_hazard(1.8, 0.5) == HazardClass.H4  # D = 1.8 > 1.2, DV = 0.9 <= 1.0


def test_h5_classification():
    """H5: Unsafe for people/vehicles; structural damage vulnerability (D*V <= 4.0, D <= 4.0, V <= 4.0; D > 2.0 or V > 2.0 or D*V > 1.0)."""
    assert classify_hazard(1.5, 1.5) == HazardClass.H5  # DV = 2.25 > 1.0
    assert classify_hazard(2.5, 0.8) == HazardClass.H5  # D = 2.5 > 2.0, DV = 2.0
    assert classify_hazard(0.8, 2.5) == HazardClass.H5  # V = 2.5 > 2.0, DV = 2.0
    assert classify_hazard(3.5, 1.0) == HazardClass.H5  # D = 3.5 > 2.0, DV = 3.5 <= 4.0


def test_h6_classification():
    """H6: Catastrophic structural failure (D*V > 4.0 or D > 4.0 or V > 4.0)."""
    assert classify_hazard(5.0, 0.5) == HazardClass.H6  # D = 5.0 > 4.0
    assert classify_hazard(1.0, 5.0) == HazardClass.H6  # V = 5.0 > 4.0
    assert classify_hazard(2.5, 2.0) == HazardClass.H6  # DV = 5.0 > 4.0
    assert classify_hazard(10.0, 3.0) == HazardClass.H6  # D = 10.0 > 4.0, DV = 30.0


def test_vectorized_classification():
    """Verify that vectorized array classification strictly matches scalar classification."""
    depths = np.array([0.02, 0.1, 0.4, 0.8, 1.5, 2.5, 5.0, 1.0], dtype=np.float32)
    velocities = np.array([0.0, 0.5, 0.5, 0.6, 0.5, 0.8, 0.5, 5.0], dtype=np.float32)

    vec_result = classify_hazard_vectorized(depths, velocities)
    expected = [
        int(HazardClass.DRY),
        int(HazardClass.H1),
        int(HazardClass.H2),
        int(HazardClass.H3),
        int(HazardClass.H4),
        int(HazardClass.H5),
        int(HazardClass.H6),
        int(HazardClass.H6),
    ]

    assert list(vec_result) == expected
