"""Generic Earth Observation and Satellite Monitoring Configuration Builder.

Prepares per-site orbit geometry preferences, Sentinel-1 SAR acquisition parameters,
and Otsu/threshold detection baselines without assuming fixed hardcoded orbits.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.app.schemas.site import SiteConfig


class EOSiteConfiguration(BaseModel):
    site_id: str
    satellite_platform: str
    pass_preference: str
    target_relative_orbit: Optional[int]
    aoi_bbox: list[float]
    delta_vv_threshold_db: float
    event_vv_threshold_db: float
    slope_mask_deg: float


def build_eo_config(site_config: SiteConfig) -> EOSiteConfiguration:
    """Build dynamic EO configuration for a given site."""
    eo = site_config.earth_observation
    return EOSiteConfiguration(
        site_id=site_config.site_id,
        satellite_platform=eo.satellite_platform,
        pass_preference=eo.orbit_pass_preference or "DESCENDING",
        target_relative_orbit=eo.relative_orbit_preference,
        aoi_bbox=site_config.study_area.aoi_bbox_wgs84,
        delta_vv_threshold_db=eo.detection_threshold_delta_db,
        event_vv_threshold_db=-14.0,
        slope_mask_deg=5.0,
    )
