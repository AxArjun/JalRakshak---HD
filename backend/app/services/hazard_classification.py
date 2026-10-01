"""
JalRakshak-HD: Flood Hazard Severity & Vulnerability Classification Service
============================================================================
Implements the Central Water Commission (CWC) / AIDR Guideline 7-3 combined
depth-velocity flood hazard vulnerability classification (H1 to H6).

Source Documentation & Lineage:
- Provider: Central Water Commission (CWC) Dam Safety Organization / Australian Institute for Disaster Resilience (AIDR)
- Document: Guidelines for Mapping Dam Inundation and Hazard Classification / Australian Disaster Resilience Guideline 7-3: Flood Hazard
- Document Number: AIDR Guideline 7-3 (ISBN 978-0-9953963-3-3)
- Table/Figure: Table 1 & Figure 1: Combined Flood Hazard Vulnerability Thresholds
- Research Citation: Smith, G.P., Davey, E.K., and Cox, R.J. (2014). "Flood Hazard", WRL Technical Report 2014/07, UNSW Water Research Laboratory.
- Reference URL: https://knowledge.aidr.org.au/resources/guideline-7-3-flood-hazard/
- Retrieval Date: 2026-09-25

Hazard Classes:
- H1: Generally safe for people, vehicles, and buildings (D*V <= 0.3, D <= 0.3, V <= 2.0).
- H2: Unsafe for small vehicles (D*V <= 0.6, D <= 0.5, V <= 2.0).
- H3: Unsafe for vehicles, children, and the elderly (D*V <= 0.6, D <= 1.2, V <= 2.0).
- H4: Unsafe for vehicles and people (D*V <= 1.0, D <= 2.0, V <= 2.0).
- H5: Unsafe for vehicles and people; all buildings vulnerable to structural damage (D*V <= 4.0, D <= 4.0, V <= 4.0).
- H6: Unsafe for vehicles and people; all building types considered vulnerable to failure (D*V > 4.0 or D > 4.0 or V > 4.0).
"""

from __future__ import annotations

from enum import IntEnum
from typing import Dict, Tuple, Union

import numpy as np


class HazardClass(IntEnum):
    """CWC / AIDR Combined Flood Hazard Vulnerability Class (H1 to H6)."""

    DRY = 0
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6


HAZARD_METADATA: Dict[HazardClass, Dict[str, str]] = {
    HazardClass.DRY: {
        "name": "DRY",
        "description": "Dry ground or below wetting threshold (depth < 0.05 m)",
        "vulnerability": "No flood hazard",
    },
    HazardClass.H1: {
        "name": "H1",
        "description": "Generally safe for vehicles, people, and buildings",
        "vulnerability": "Low hazard; wading safe for all, standard vehicles can drive with caution",
    },
    HazardClass.H2: {
        "name": "H2",
        "description": "Unsafe for small vehicles",
        "vulnerability": "Moderate hazard; small passenger vehicles become unstable or buoyant",
    },
    HazardClass.H3: {
        "name": "H3",
        "description": "Unsafe for vehicles, children, and the elderly",
        "vulnerability": "Significant hazard; all vehicles unsafe, children and elderly unstable",
    },
    HazardClass.H4: {
        "name": "H4",
        "description": "Unsafe for vehicles and people",
        "vulnerability": "Severe hazard; adults lose footing, vehicles swept away",
    },
    HazardClass.H5: {
        "name": "H5",
        "description": "Unsafe for vehicles and people; all buildings vulnerable to structural damage",
        "vulnerability": "Extreme hazard; structural damage to residential/commercial buildings",
    },
    HazardClass.H6: {
        "name": "H6",
        "description": "Unsafe for vehicles and people; all building types considered vulnerable to failure",
        "vulnerability": "Catastrophic hazard; full structural failure/collapse of all building types",
    },
}


def classify_hazard(depth_m: float, velocity_mps: float, wet_threshold_m: float = 0.05) -> HazardClass:
    """Classifies a single (depth, velocity) pair into CWC H1-H6 hazard vulnerability class.
    
    Evaluates both product threshold (D * V) and individual limiting depths/velocities.
    
    Args:
        depth_m: Water depth in meters (must be non-negative).
        velocity_mps: Flow velocity magnitude in m/s (must be non-negative).
        wet_threshold_m: Minimum depth threshold to consider a cell wetted (default 0.05 m).
        
    Returns:
        HazardClass enum (DRY, H1, H2, H3, H4, H5, or H6).
    """
    if depth_m < wet_threshold_m or np.isnan(depth_m) or np.isnan(velocity_mps):
        return HazardClass.DRY

    d = max(0.0, float(depth_m))
    v = max(0.0, float(velocity_mps))
    dv = d * v

    # H6: Catastrophic structural failure zone
    # D*V > 4.0 or D > 4.0 m or V > 4.0 m/s
    if dv > 4.0 or d > 4.0 or v > 4.0:
        return HazardClass.H6

    # H5: Structural damage vulnerability zone
    # D*V > 1.0 or D > 2.0 m or V > 2.0 m/s (up to H6 boundary)
    if dv > 1.0 or d > 2.0 or v > 2.0:
        return HazardClass.H5

    # H4: Unsafe for people and vehicles
    # D*V > 0.6 or D > 1.2 m (with D <= 2.0, V <= 2.0, D*V <= 1.0)
    if dv > 0.6 or d > 1.2:
        return HazardClass.H4

    # H3: Unsafe for vehicles, children, and elderly
    # D > 0.5 m (with D*V <= 0.6, D <= 1.2, V <= 2.0)
    if d > 0.5:
        return HazardClass.H3

    # H2: Unsafe for small vehicles
    # D*V > 0.3 or D > 0.3 m (with D*V <= 0.6, D <= 0.5, V <= 2.0)
    if dv > 0.3 or d > 0.3:
        return HazardClass.H2

    # H1: Generally safe
    # D*V <= 0.3, D <= 0.3, V <= 2.0
    return HazardClass.H1


def classify_hazard_vectorized(depth_arr: np.ndarray, vel_arr: np.ndarray, wet_threshold_m: float = 0.05) -> np.ndarray:
    """Vectorized classification of 1D/2D arrays of depth and velocity into H0..H6 integer classes.
    
    Optimized for high-performance chunked array processing without full-memory duplication.
    """
    d = np.asarray(depth_arr, dtype=np.float32)
    v = np.asarray(vel_arr, dtype=np.float32)
    dv = d * v

    # Initialize with DRY (0)
    h_class = np.zeros(d.shape, dtype=np.uint8)

    wetted = (d >= wet_threshold_m) & (~np.isnan(d)) & (~np.isnan(v))

    # Base wetted is at least H1
    h_class[wetted] = int(HazardClass.H1)

    # H2: (dv > 0.3) | (d > 0.3)
    mask_h2 = wetted & ((dv > 0.3) | (d > 0.3))
    h_class[mask_h2] = int(HazardClass.H2)

    # H3: d > 0.5
    mask_h3 = wetted & (d > 0.5)
    h_class[mask_h3] = int(HazardClass.H3)

    # H4: (dv > 0.6) | (d > 1.2)
    mask_h4 = wetted & ((dv > 0.6) | (d > 1.2))
    h_class[mask_h4] = int(HazardClass.H4)

    # H5: (dv > 1.0) | (d > 2.0) | (v > 2.0)
    mask_h5 = wetted & ((dv > 1.0) | (d > 2.0) | (v > 2.0))
    h_class[mask_h5] = int(HazardClass.H5)

    # H6: (dv > 4.0) | (d > 4.0) | (v > 4.0)
    mask_h6 = wetted & ((dv > 4.0) | (d > 4.0) | (v > 4.0))
    h_class[mask_h6] = int(HazardClass.H6)

    return h_class
