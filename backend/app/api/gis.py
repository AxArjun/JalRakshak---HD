"""
JalRakshak-HD: Milestone M10 Tasks 6, 7, 13 — GIS Vectors, Raster Overlays & Point Analysis
=============================================================================================
Provides GeoJSON vector layers, bounding-box filtered building/road queries,
static raster overlay serving, and real multi-raster point sampling analysis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import Point, box
from pyproj import Transformer
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from backend.app.schemas.dashboard import PointAnalysis

router = APIRouter(tags=["GIS & Spatial Data"])
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
GEOJSON_DIR = ROOT_DIR / "outputs" / "dashboard" / "geojson"
OVERLAYS_DIR = ROOT_DIR / "outputs" / "dashboard" / "overlays"
HADR_DIR = ROOT_DIR / "outputs" / "hadr"
SIM_DIR = ROOT_DIR / "outputs" / "simulations" / "dflowfm" / "BHV_BASE"
GEE_DIR = ROOT_DIR / "data" / "gee"
LATEST_GEE_DIR = ROOT_DIR / "outputs" / "gee" / "latest"

# Lazy-loaded in-memory caches for fast point and vector queries
_CACHED_GEOJSON = {}
_CACHED_ZONES_GDF = None
_CACHED_BUILDINGS_GDF = None
_CACHED_ROADS_GDF = None

transformer_wgs_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)


def load_geojson(filename: str) -> Dict[str, Any]:
    if filename in _CACHED_GEOJSON:
        return _CACHED_GEOJSON[filename]
    p = GEOJSON_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"GeoJSON layer {filename} not found.")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    _CACHED_GEOJSON[filename] = data
    return data


# ============================================================================
# Vector GeoJSON Endpoints (Task 6)
# ============================================================================

@router.get("/gis/dam")
def get_dam_layer():
    return load_geojson("dam_point.geojson")


@router.get("/gis/river")
def get_river_layer():
    return load_geojson("bhavani_river.geojson")


@router.get("/gis/reservoir")
def get_reservoir_layer():
    return load_geojson("reservoir_surface.geojson")


@router.get("/gis/inundation")
def get_inundation_extent():
    return load_geojson("inundation_extent.geojson")


@router.get("/gis/hazard")
def get_hazard_severity():
    return load_geojson("hazard_severity.geojson")


@router.get("/gis/hadr-zones")
def get_hadr_zones():
    return load_geojson("response_zones.geojson")


@router.get("/gis/critical-facilities")
def get_critical_facilities():
    return load_geojson("critical_facilities.geojson")


@router.get("/gis/historical-flood")
def get_historical_flood():
    return load_geojson("historical_flood.geojson")


@router.get("/gis/latest-water-change")
def get_latest_water_change():
    return load_geojson("latest_water_change.geojson")


@router.get("/gis/sph-reach")
def get_sph_reach():
    return load_geojson("sph_reach.geojson")


@router.get("/gis/sph-gauges")
def get_sph_gauges():
    return load_geojson("sph_gauges.geojson")


@router.get("/gis/bridges")
def get_bridges_layer():
    return load_geojson("bridges.geojson")


@router.get("/gis/settlements")
def get_settlements_layer():
    return load_geojson("settlements.geojson")


@router.get("/gis/roads")
def get_roads(
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None
):
    global _CACHED_ROADS_GDF
    if _CACHED_ROADS_GDF is None:
        p = HADR_DIR / "road_exposure.gpkg"
        if p.exists():
            _CACHED_ROADS_GDF = gpd.read_file(p).to_crs("EPSG:4326")
        else:
            return load_geojson("road_exposure.geojson")

    if min_lon is not None and min_lat is not None and max_lon is not None and max_lat is not None:
        bbox_geom = box(min_lon, min_lat, max_lon, max_lat)
        filtered = _CACHED_ROADS_GDF[_CACHED_ROADS_GDF.intersects(bbox_geom)]
        return json.loads(filtered.to_json())
    
    return json.loads(_CACHED_ROADS_GDF.to_json())


@router.get("/gis/buildings")
def get_buildings(
    min_lon: Optional[float] = Query(None, description="Bounding box minimum longitude"),
    min_lat: Optional[float] = Query(None, description="Bounding box minimum latitude"),
    max_lon: Optional[float] = Query(None, description="Bounding box maximum longitude"),
    max_lat: Optional[float] = Query(None, description="Bounding box maximum latitude"),
    limit: int = Query(1000, description="Max buildings to return in viewport")
):
    """
    Returns buildings intersected with viewport bounding box.
    Limits payload size to avoid overwhelming browser memory.
    """
    global _CACHED_BUILDINGS_GDF
    if _CACHED_BUILDINGS_GDF is None:
        p = HADR_DIR / "building_exposure.gpkg"
        if not p.exists():
            raise HTTPException(status_code=404, detail="Building exposure layer not found.")
        _CACHED_BUILDINGS_GDF = gpd.read_file(p).to_crs("EPSG:4326")

    if min_lon is not None and min_lat is not None and max_lon is not None and max_lat is not None:
        bbox_geom = box(min_lon, min_lat, max_lon, max_lat)
        sub = _CACHED_BUILDINGS_GDF[_CACHED_BUILDINGS_GDF.intersects(bbox_geom)]
        if len(sub) > limit:
            sub = sub.iloc[:limit]
        return json.loads(sub.to_json())
    
    # Default sample if no bbox provided (first 500 buildings)
    sample = _CACHED_BUILDINGS_GDF.iloc[:500]
    return json.loads(sample.to_json())


# ============================================================================
# Static Raster Overlay Service (Task 7)
# ============================================================================

@router.get("/tiles/overlays/manifest")
def get_overlays_manifest():
    p = OVERLAYS_DIR / "manifest.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Overlays manifest not found.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/tiles/overlays/{layer_name}")
def get_overlay_png(layer_name: str):
    if not layer_name.endswith(".png"):
        layer_name = f"{layer_name}.png"
    p = OVERLAYS_DIR / layer_name
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Overlay image {layer_name} not found.")
    return FileResponse(p, media_type="image/png")


# ============================================================================
# Map Click Analysis API (Task 13)
# ============================================================================

def sample_raster_at_utm(tif_path: Path, x_utm: float, y_utm: float) -> Optional[float]:
    if not tif_path.exists():
        return None
    try:
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
            if not (bounds.left <= x_utm <= bounds.right and bounds.bottom <= y_utm <= bounds.top):
                return None
            val = list(src.sample([(x_utm, y_utm)]))[0][0]
            if val == src.nodata or np.isnan(val) or val < -9000:
                return None
            return float(val)
    except Exception:
        return None


@router.get("/analyze-point", response_model=PointAnalysis)
@router.get("/gis/analyze-point", response_model=PointAnalysis)
@router.get("/gis/query-point")
def analyze_point(
    lat: float = Query(..., description="Latitude in WGS 84 (e.g. 11.4705)"),
    lon: Optional[float] = Query(None, description="Longitude in WGS 84 (e.g. 77.1140)"),
    lng: Optional[float] = Query(None, description="Longitude in WGS 84 (e.g. 77.1140)")
):
    """
    Samples real raster and vector datasets at the requested geographic point.
    Returns maximum depth, velocity, arrival time, CWC hazard class, HADR response sector,
    and historical/latest satellite water presence.
    """
    if lon is None and lng is None:
        raise HTTPException(status_code=422, detail="Must provide either 'lon' or 'lng'")
    lon = lon if lon is not None else lng
    global _CACHED_ZONES_GDF
    
    # 1. Transform WGS84 (lon, lat) to UTM EPSG:32643
    x_utm, y_utm = transformer_wgs_to_utm.transform(lon, lat)

    # 2. Sample M5 hydraulic rasters
    depth_val = sample_raster_at_utm(SIM_DIR / "max_water_depth.tif", x_utm, y_utm)
    vel_val = sample_raster_at_utm(SIM_DIR / "max_velocity.tif", x_utm, y_utm)
    arr_val = sample_raster_at_utm(SIM_DIR / "arrival_time.tif", x_utm, y_utm)
    
    # Convert arrival time to hours
    arr_hr = None
    if arr_val is not None and arr_val > 0:
        arr_hr = round(arr_val / 3600.0, 2) if arr_val > 60 else round(arr_val, 2)

    # 3. Sample Hazard Class raster
    hz_code = sample_raster_at_utm(HADR_DIR / "hazard_class.tif", x_utm, y_utm)
    hz_class = None
    hz_desc = None
    if hz_code is not None and int(hz_code) in [1, 2, 3, 4, 5, 6]:
        hz_int = int(hz_code)
        hz_class = f"H{hz_int}"
        desc_map = {
            1: "H1 — Low hazard (depth < 0.3m); generally safe for people and light vehicles",
            2: "H2 — Moderate hazard (depth 0.3–0.5m); wading dangerous for children and elderly",
            3: "H3 — Significant hazard (depth 0.5–1.2m); wading hazardous for adults; vehicles unstable",
            4: "H4 — High hazard (depth 1.2–2.0m); structural damage to non-engineered buildings",
            5: "H5 — Severe hazard (depth > 2.0m or v > 2m/s); extensive structural failures",
            6: "H6 — Extreme hazard (depth > 5.0m or v > 4m/s); all building types considered vulnerable"
        }
        hz_desc = desc_map.get(hz_int, "")

    # 4. Query Response Zone membership
    if _CACHED_ZONES_GDF is None:
        zp = HADR_DIR / "response_zones_exclusive.gpkg"
        if zp.exists():
            _CACHED_ZONES_GDF = gpd.read_file(zp)
            if _CACHED_ZONES_GDF.crs != "EPSG:32643":
                _CACHED_ZONES_GDF = _CACHED_ZONES_GDF.to_crs("EPSG:32643")

    zone_id = None
    zone_rank = None
    pt_geom = Point(x_utm, y_utm)
    if _CACHED_ZONES_GDF is not None:
        match = _CACHED_ZONES_GDF[_CACHED_ZONES_GDF.contains(pt_geom)]
        if len(match) > 0:
            row = match.iloc[0]
            zone_id = str(row.get("zone_id", row.get("name", "ZONE")))
            zone_rank = int(row.get("priority_rank", row.get("rank", 1)))

    # 5. Check Historical Flood (Aug 2019) raster
    hist_val = sample_raster_at_utm(GEE_DIR / "observed_new_flood.tif", x_utm, y_utm)
    hist_detected = bool(hist_val is not None and hist_val > 0)

    # 6. Check Latest Water Change Anomaly vector
    latest_val = sample_raster_at_utm(LATEST_GEE_DIR / "latest_water_change.tif", x_utm, y_utm)
    latest_detected = bool(latest_val is not None and latest_val > 0)

    # Determine status
    in_bounds = depth_val is not None or hz_code is not None or zone_id is not None
    if depth_val is not None and depth_val >= 0.05:
        status_msg = f"Inundated in hypothetical M5 dam breach simulation (Peak depth: {depth_val:.2f} m)"
    elif in_bounds:
        status_msg = "Location within study area (Dry / Uninundated)"
    else:
        status_msg = "Location outside hydraulic simulation domain"

    return PointAnalysis(
        location={"latitude": lat, "longitude": lon, "x_utm": round(x_utm, 1), "y_utm": round(y_utm, 1)},
        in_study_area=in_bounds,
        max_depth_m=round(depth_val, 2) if depth_val is not None else None,
        max_velocity_mps=round(vel_val, 2) if vel_val is not None else None,
        arrival_time_hr=arr_hr,
        hazard_class=hz_class,
        hazard_description=hz_desc,
        response_zone=zone_id,
        response_zone_rank=zone_rank,
        historical_flood_detected=hist_detected,
        latest_candidate_water_change=latest_detected,
        status_message=status_msg
    )
