"""Study Area domain and geospatial models for JalRakshak-HD.

Defines schemas for dam attributes, river systems, reservoir extents,
bounding boxes, terrain metadata, and study area containers.
Compatible with PostGIS geo-serialization.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    """Authoritative verification status."""

    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    UNVERIFIED = "UNVERIFIED"


class BoundingBox(BaseModel):
    """Geographic bounding box in WGS 84 coordinates."""

    min_lon: float = Field(..., ge=-180.0, le=180.0, description="Western boundary longitude")
    min_lat: float = Field(..., ge=-90.0, le=90.0, description="Southern boundary latitude")
    max_lon: float = Field(..., ge=-180.0, le=180.0, description="Eastern boundary longitude")
    max_lat: float = Field(..., ge=-90.0, le=90.0, description="Northern boundary latitude")

    @field_validator("max_lon")
    @classmethod
    def check_longitude_order(cls, v: float, values: Any) -> float:
        min_lon = values.data.get("min_lon")
        if min_lon is not None and v <= min_lon:
            raise ValueError(f"max_lon ({v}) must be strictly greater than min_lon ({min_lon})")
        return v

    @field_validator("max_lat")
    @classmethod
    def check_latitude_order(cls, v: float, values: Any) -> float:
        min_lat = values.data.get("min_lat")
        if min_lat is not None and v <= min_lat:
            raise ValueError(f"max_lat ({v}) must be strictly greater than min_lat ({min_lat})")
        return v

    def as_geojson_polygon(self) -> Dict[str, Any]:
        """Return BoundingBox as GeoJSON Polygon geometry dict."""
        return {
            "type": "Polygon",
            "coordinates": [[
                [self.min_lon, self.min_lat],
                [self.max_lon, self.min_lat],
                [self.max_lon, self.max_lat],
                [self.min_lon, self.max_lat],
                [self.min_lon, self.min_lat],
            ]],
        }


class Dam(BaseModel):
    """Dam physical and geographic attributes."""

    name: str
    alternate_names: List[str] = Field(default_factory=list)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    dam_type: str
    year_completed: Optional[int] = None
    crest_length_m: Optional[float] = None
    max_height_m: Optional[float] = None
    gross_storage_tmc: Optional[float] = None
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    source: str
    source_url: Optional[str] = None

    def as_geojson_point(self) -> Dict[str, Any]:
        """Return Dam location as GeoJSON Point geometry dict."""
        return {
            "type": "Point",
            "coordinates": [self.longitude, self.latitude],
        }


class River(BaseModel):
    """River reach and hydrological basin association."""

    name: str
    basin: str
    tributary_of: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    source: str
    source_url: Optional[str] = None


class Reservoir(BaseModel):
    """Reservoir impoundment metadata."""

    name: str
    full_reservoir_level_m: Optional[float] = None
    dead_storage_level_m: Optional[float] = None
    gross_capacity_mcm: Optional[float] = None
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    source: str


class TerrainMetadata(BaseModel):
    """Digital Elevation Model provenance and resolution metadata."""

    source: str
    dataset_id: str
    native_resolution_m: float
    output_resolution_m: float
    vertical_units: str = "metres"
    acquisition_date: str
    projected_crs: str
    projected_crs_name: Optional[str] = None


class StudyArea(BaseModel):
    """Complete study area container model."""

    id: str
    name: str
    state: str
    district: str
    country: str = "India"
    dam: Dam
    river: River
    reservoir: Reservoir
    aoi_bbox: BoundingBox
    projected_crs: str
    terrain: Optional[TerrainMetadata] = None
