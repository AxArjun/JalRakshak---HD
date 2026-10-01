"""Generic HADR Consequence and Exposure Analysis Configuration Builder.

Prepares standardized hazard classification, response zone mapping,
and asset exposure schemas for any site domain.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.schemas.site import SiteConfig
from backend.app.core.site_paths import get_site_paths


class HADRConfiguration(BaseModel):
    site_id: str
    hazard_matrix_standard: str = "CWC_GUIDELINES_FOR_DAM_SAFETY_1987"
    response_zones_count: int = 6
    population_sources: List[str] = ["WorldPop_2020", "GHSL_2025"]
    building_sources: List[str] = ["OSM_Buildings", "Microsoft_Building_Footprints"]
    infrastructure_sources: List[str] = ["OSM_Highways", "OpenRailwayMap", "Overpass_Bridges"]
    critical_facility_types: List[str] = [
        "hospital", "school", "emergency_service", "police", "fire_station", "power_substation"
    ]


def build_hadr_config(site_config: SiteConfig) -> HADRConfiguration:
    """Build standardized HADR configuration object for a site."""
    return HADRConfiguration(
        site_id=site_config.site_id,
    )
