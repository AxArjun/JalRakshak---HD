"""
Acquire OSM Settlements / Places for Locality Association.
"""

import os
import json
import requests
import geopandas as gpd
import shapely.geometry as sgeom

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

q = """[out:json][timeout:30];
(
  node["place"~"city|town|village|hamlet|suburb|neighbourhood"](11.35,77.05,11.65,77.75);
);
out body;"""

for ep in ENDPOINTS:
    try:
        print(f"Trying {ep}...")
        r = requests.post(ep, data={"data": q}, headers=HEADERS, timeout=25)
        if r.status_code == 200:
            data = r.json()
            elems = data.get("elements", [])
            print(f"Fetched {len(elems)} settlements from {ep}")
            records = []
            for el in elems:
                tags = el.get("tags", {})
                records.append({
                    "osm_id": el["id"],
                    "name": tags.get("name", tags.get("name:en", "Unnamed")),
                    "place_type": tags.get("place", "village"),
                    "geometry": sgeom.Point(el["lon"], el["lat"])
                })
            gdf = gpd.GeoDataFrame(records, crs="EPSG:4326").to_crs(epsg=32643)
            out_path = "data/hadr/settlements.gpkg"
            gdf.to_file(out_path, driver="GPKG")
            print(f"Saved {len(gdf)} settlements to {out_path}")
            break
    except Exception as e:
        print(f"{ep} error: {e}")
