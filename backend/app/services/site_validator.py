"""Site Validation Rule Engine for JalRakshak-HD.

Performs schema, physical sanity, and topological verification on site configurations,
emitting structured ERROR, WARNING, and INFO diagnostics.
"""

from __future__ import annotations

from typing import Dict, List, Any
from pydantic import BaseModel
from backend.app.schemas.site import SiteConfig, ImpoundmentType


class ValidationMessage(BaseModel):
    level: str  # ERROR, WARNING, INFO
    category: str
    message: str
    field_name: str


class ValidationReport(BaseModel):
    site_id: str
    is_valid: bool
    errors: List[ValidationMessage]
    warnings: List[ValidationMessage]
    infos: List[ValidationMessage]


def validate_site_config(site_config: SiteConfig) -> ValidationReport:
    """Validate a SiteConfig object against engineering and physical sanity rules."""
    errors: List[ValidationMessage] = []
    warnings: List[ValidationMessage] = []
    infos: List[ValidationMessage] = []

    # 1. Location & CRS Checks
    lat = site_config.identity.latitude
    lon = site_config.identity.longitude
    if lat is None or not (-90.0 <= lat <= 90.0):
        errors.append(ValidationMessage(
            level="ERROR", category="LOCATION",
            message=f"Dam latitude {lat} is out of valid range [-90, 90].",
            field_name="identity.latitude"
        ))
    if lon is None or not (-180.0 <= lon <= 180.0):
        errors.append(ValidationMessage(
            level="ERROR", category="LOCATION",
            message=f"Dam longitude {lon} is out of valid range [-180, 180].",
            field_name="identity.longitude"
        ))

    bbox = site_config.study_area.aoi_bbox_wgs84
    if len(bbox) == 4:
        min_lon, min_lat, max_lon, max_lat = bbox
        if min_lon >= max_lon or min_lat >= max_lat:
            errors.append(ValidationMessage(
                level="ERROR", category="LOCATION",
                message=f"Invalid bounding box ordering: {bbox}",
                field_name="study_area.aoi_bbox_wgs84"
            ))
        elif not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            errors.append(ValidationMessage(
                level="ERROR", category="LOCATION",
                message=f"Dam coordinate ({lon}, {lat}) is outside study area AOI bbox {bbox}.",
                field_name="study_area.aoi_bbox_wgs84"
            ))
    else:
        errors.append(ValidationMessage(
            level="ERROR", category="LOCATION",
            message="AOI bounding box must contain exactly 4 coordinates [min_lon, min_lat, max_lon, max_lat].",
            field_name="study_area.aoi_bbox_wgs84"
        ))

    # 2. Impoundment Type
    if site_config.identity.impoundment_type != ImpoundmentType.ENGINEERED_DAM:
        warnings.append(ValidationMessage(
            level="WARNING", category="IMPOUNDMENT",
            message=f"Impoundment type is {site_config.identity.impoundment_type.value}. Note: Only ENGINEERED_DAM physics models are currently implemented.",
            field_name="identity.impoundment_type"
        ))

    # 3. Geometry & Elevations
    geom = site_config.geometry
    if geom.dam_height_m is not None and geom.dam_height_m <= 0:
        errors.append(ValidationMessage(
            level="ERROR", category="GEOMETRY",
            message=f"Dam height must be positive, got {geom.dam_height_m}.",
            field_name="geometry.dam_height_m"
        ))

    if geom.crest_length_m is not None and geom.crest_length_m <= 0:
        errors.append(ValidationMessage(
            level="ERROR", category="GEOMETRY",
            message=f"Crest length must be positive, got {geom.crest_length_m}.",
            field_name="geometry.crest_length_m"
        ))

    # 4. Reservoir Storage
    res = site_config.reservoir
    if res.gross_storage_capacity_mcm is not None and res.gross_storage_capacity_mcm <= 0:
        errors.append(ValidationMessage(
            level="ERROR", category="RESERVOIR",
            message=f"Gross storage capacity must be positive, got {res.gross_storage_capacity_mcm}.",
            field_name="reservoir.gross_storage_capacity_mcm"
        ))

    if res.live_storage_capacity_mcm and res.gross_storage_capacity_mcm:
        if res.live_storage_capacity_mcm > res.gross_storage_capacity_mcm:
            errors.append(ValidationMessage(
                level="ERROR", category="RESERVOIR",
                message=f"Live storage ({res.live_storage_capacity_mcm} MCM) cannot exceed gross storage ({res.gross_storage_capacity_mcm} MCM).",
                field_name="reservoir.live_storage_capacity_mcm"
            ))

    if res.full_reservoir_level_m and geom.crest_elevation_m:
        if res.full_reservoir_level_m > geom.crest_elevation_m:
            errors.append(ValidationMessage(
                level="ERROR", category="ELEVATION",
                message=f"FRL ({res.full_reservoir_level_m} m) exceeds dam crest elevation ({geom.crest_elevation_m} m).",
                field_name="reservoir.full_reservoir_level_m"
            ))

    # 5. Breach Scenarios
    if not site_config.breach_scenarios:
        warnings.append(ValidationMessage(
            level="WARNING", category="BREACH",
            message="No breach scenarios defined for this site.",
            field_name="breach_scenarios"
        ))
    else:
        for scn_id, scn in site_config.breach_scenarios.items():
            if scn.average_breach_width_m is not None and scn.average_breach_width_m <= 0:
                errors.append(ValidationMessage(
                    level="ERROR", category="BREACH",
                    message=f"Scenario {scn_id}: Breach width must be positive, got {scn.average_breach_width_m}.",
                    field_name=f"breach_scenarios.{scn_id}.average_breach_width_m"
                ))
            if scn.breach_formation_time_s is not None and scn.breach_formation_time_s <= 0:
                errors.append(ValidationMessage(
                    level="ERROR", category="BREACH",
                    message=f"Scenario {scn_id}: Breach formation time must be positive, got {scn.breach_formation_time_s}.",
                    field_name=f"breach_scenarios.{scn_id}.breach_formation_time_s"
                ))
            if scn.peak_discharge_m3s is not None and scn.peak_discharge_m3s <= 0:
                errors.append(ValidationMessage(
                    level="ERROR", category="BREACH",
                    message=f"Scenario {scn_id}: Peak discharge must be positive, got {scn.peak_discharge_m3s}.",
                    field_name=f"breach_scenarios.{scn_id}.peak_discharge_m3s"
                ))

    # 6. Provenance Info
    if site_config.provenance:
        infos.append(ValidationMessage(
            level="INFO", category="PROVENANCE",
            message=f"{len(site_config.provenance)} authoritative source records tracked.",
            field_name="provenance"
        ))
    else:
        warnings.append(ValidationMessage(
            level="WARNING", category="PROVENANCE",
            message="No source manifest records attached to site package.",
            field_name="provenance"
        ))

    is_valid = len(errors) == 0
    return ValidationReport(
        site_id=site_config.site_id,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        infos=infos,
    )
