"""Automatic spatial Coordinate Reference System (CRS) derivation and validation.

Eliminates hardcoded EPSG:32643 and dynamically computes the appropriate
WGS 84 / UTM Zone or designated projected coordinate system.
"""

from __future__ import annotations

import math
from typing import Dict, Any, Optional
from backend.app.schemas.site import CRSConfig


def derive_project_crs(
    latitude: float,
    longitude: float,
    override_crs: Optional[str] = None
) -> CRSConfig:
    """Derive appropriate projected Coordinate Reference System (CRS).

    Parameters
    ----------
    latitude : float
        WGS 84 latitude in decimal degrees (-90 to 90).
    longitude : float
        WGS 84 longitude in decimal degrees (-180 to 180).
    override_crs : Optional[str]
        Explicit user override (e.g. 'EPSG:32644').

    Returns
    -------
    CRSConfig
        Validated CRS configuration with derivation metadata.
    """
    if override_crs:
        # Determine if it's UTM
        utm_zone = None
        hemisphere = "N"
        if override_crs.startswith("EPSG:326"):
            utm_zone = int(override_crs.replace("EPSG:326", ""))
            hemisphere = "N"
        elif override_crs.startswith("EPSG:327"):
            utm_zone = int(override_crs.replace("EPSG:327", ""))
            hemisphere = "S"

        return CRSConfig(
            source_crs="EPSG:4326",
            project_crs=override_crs,
            utm_zone=utm_zone,
            hemisphere=hemisphere,
            derivation_reason="USER_EXPLICIT_OVERRIDE",
            override_applied=True,
        )

    # Validate coordinate bounds
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"Latitude {latitude} is outside valid range [-90, 90].")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Longitude {longitude} is outside valid range [-180, 180].")

    # Standard UTM Zone calculation: floor((lon + 180) / 6) + 1
    utm_zone = int(math.floor((longitude + 180.0) / 6.0)) + 1

    if utm_zone < 1:
        utm_zone = 1
    elif utm_zone > 60:
        utm_zone = 60

    hemisphere = "N" if latitude >= 0.0 else "S"
    epsg_code = 32600 + utm_zone if hemisphere == "N" else 32700 + utm_zone
    project_crs = f"EPSG:{epsg_code}"

    return CRSConfig(
        source_crs="EPSG:4326",
        project_crs=project_crs,
        utm_zone=utm_zone,
        hemisphere=hemisphere,
        derivation_reason=f"AUTOMATIC_UTM_ZONE_DERIVATION_ZONE_{utm_zone}{hemisphere}",
        override_applied=False,
    )
