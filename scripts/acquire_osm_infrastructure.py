"""
Acquire OpenStreetMap Infrastructure & Facilities with Multi-Endpoint Fallback.
"""

import os
import json
import time
import requests
import geopandas as gpd
import shapely.geometry as sgeom
from shapely.ops import unary_union

RAW_DIR = "data/raw/hadr"
PROC_DIR = "data/hadr"
INUNDATION_PATH = "outputs/simulations/dflowfm/BHV_BASE/inundation_extent.gpkg"

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def query_overpass_multi(query_str):
    for ep in ENDPOINTS:
        print(f"Trying Overpass endpoint: {ep}...")
        try:
            resp = requests.post(ep, data={"data": query_str}, headers=HEADERS, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get("elements", [])
                print(f"  Success from {ep}: received {len(elements)} elements")
                return data
            else:
                print(f"  Endpoint {ep} returned status {resp.status_code}")
        except Exception as e:
            print(f"  Endpoint {ep} error: {e}")
    raise RuntimeError("All Overpass endpoints failed.")


def acquire_osm():
    gdf_inundation = gpd.read_file(INUNDATION_PATH)
    gdf_wgs84 = gdf_inundation.to_crs(epsg=4326)
    gdf_buffered = gdf_inundation.buffer(1000).to_crs(epsg=4326)
    bounds = gdf_buffered.total_bounds
    min_lon, min_lat, max_lon, max_lat = bounds
    bbox_str = f"{min_lat:.5f},{min_lon:.5f},{max_lat:.5f},{max_lon:.5f}"
    print(f"Querying OSM for bbox: {bbox_str}")

    # 1. Roads
    road_query = f"""[out:json][timeout:60];
(
  way["highway"]({bbox_str});
);
out body;
>;
out skel qt;"""

    print("Fetching roads...")
    road_data = query_overpass_multi(road_query)
    with open(os.path.join(RAW_DIR, "roads_osm_raw.json"), "w", encoding="utf-8") as f:
        json.dump(road_data, f)

    nodes = {}
    for el in road_data.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])

    road_records = []
    for el in road_data.get("elements", []):
        if el["type"] == "way" and "highway" in el.get("tags", {}):
            tags = el.get("tags", {})
            way_nodes = el.get("nodes", [])
            coords = [nodes[nid] for nid in way_nodes if nid in nodes]
            if len(coords) >= 2:
                line = sgeom.LineString(coords)
                road_records.append({
                    "osm_id": el["id"],
                    "highway": tags.get("highway", "unclassified"),
                    "name": tags.get("name", "Unnamed Road"),
                    "bridge": tags.get("bridge", "no"),
                    "surface": tags.get("surface", "unknown"),
                    "lanes": tags.get("lanes", "unknown"),
                    "maxspeed": tags.get("maxspeed", "unknown"),
                    "geometry": line
                })

    if road_records:
        gdf_roads = gpd.GeoDataFrame(road_records, crs="EPSG:4326")
        gdf_roads_proj = gdf_roads.to_crs(epsg=32643)
        gdf_roads_proj["length_m"] = gdf_roads_proj.geometry.length
        out_road_gpkg = os.path.join(PROC_DIR, "roads.gpkg")
        gdf_roads_proj.to_file(out_road_gpkg, driver="GPKG")
        print(f"Saved {len(gdf_roads_proj)} roads ({gdf_roads_proj['length_m'].sum()/1000:.2f} km) to {out_road_gpkg}")

    # 2. Critical Facilities
    fac_query = f"""[out:json][timeout:60];
(
  node["amenity"~"hospital|clinic|doctors|pharmacy|school|college|kindergarten|police|fire_station|townhall|courthouse|place_of_worship"]({bbox_str});
  way["amenity"~"hospital|clinic|doctors|pharmacy|school|college|kindergarten|police|fire_station|townhall|courthouse|place_of_worship"]({bbox_str});
  node["emergency"~"ambulance_station|fire_hydrant|defibrillator|emergency_ward_entrance"]({bbox_str});
  way["emergency"~"ambulance_station"]({bbox_str});
);
out center;"""

    print("Fetching critical facilities...")
    fac_data = query_overpass_multi(fac_query)
    with open(os.path.join(RAW_DIR, "critical_facilities_osm_raw.json"), "w", encoding="utf-8") as f:
        json.dump(fac_data, f)

    fac_records = []
    for el in fac_data.get("elements", []):
        tags = el.get("tags", {})
        if el["type"] == "node":
            pt = sgeom.Point(el["lon"], el["lat"])
        elif "center" in el:
            pt = sgeom.Point(el["center"]["lon"], el["center"]["lat"])
        else:
            continue

        fac_type = tags.get("amenity", tags.get("emergency", "other"))
        category = "other"
        if fac_type in ["hospital", "clinic", "doctors", "pharmacy"]:
            category = "healthcare"
        elif fac_type in ["school", "college", "kindergarten"]:
            category = "education"
        elif fac_type in ["police", "fire_station", "ambulance_station"]:
            category = "emergency_service"
        elif fac_type in ["townhall", "courthouse"]:
            category = "government"
        elif fac_type == "place_of_worship":
            category = "community_assembly"

        fac_records.append({
            "osm_id": el["id"],
            "osm_type": el["type"],
            "name": tags.get("name", f"Unnamed {fac_type}"),
            "facility_type": fac_type,
            "category": category,
            "operator": tags.get("operator", "unknown"),
            "geometry": pt
        })

    if fac_records:
        gdf_fac = gpd.GeoDataFrame(fac_records, crs="EPSG:4326")
        gdf_fac_proj = gdf_fac.to_crs(epsg=32643)
        out_fac_gpkg = os.path.join(PROC_DIR, "critical_facilities.gpkg")
        gdf_fac_proj.to_file(out_fac_gpkg, driver="GPKG")
        print(f"Saved {len(gdf_fac_proj)} critical facilities to {out_fac_gpkg}")

    # 3. Settlements
    place_query = f"""[out:json][timeout:60];
(
  node["place"~"city|town|village|hamlet|suburb|neighbourhood"]({bbox_str});
);
out body;"""

    print("Fetching settlements...")
    place_data = query_overpass_multi(place_query)
    with open(os.path.join(RAW_DIR, "settlements_osm_raw.json"), "w", encoding="utf-8") as f:
        json.dump(place_data, f)

    place_records = []
    for el in place_data.get("elements", []):
        tags = el.get("tags", {})
        pt = sgeom.Point(el["lon"], el["lat"])
        place_records.append({
            "osm_id": el["id"],
            "name": tags.get("name", tags.get("name:en", "Unnamed")),
            "place_type": tags.get("place", "village"),
            "population": tags.get("population", "unknown"),
            "geometry": pt
        })

    if place_records:
        gdf_places = gpd.GeoDataFrame(place_records, crs="EPSG:4326")
        gdf_places_proj = gdf_places.to_crs(epsg=32643)
        out_place_gpkg = os.path.join(PROC_DIR, "settlements.gpkg")
        gdf_places_proj.to_file(out_place_gpkg, driver="GPKG")
        print(f"Saved {len(gdf_places_proj)} settlements to {out_place_gpkg}")


if __name__ == "__main__":
    acquire_osm()
