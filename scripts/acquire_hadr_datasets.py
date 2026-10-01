"""
Acquire Vector Datasets for M8 HADR Consequence Analysis.

Datasets acquired:
1. Google Open Buildings v3 (confidence >= 0.75) via Earth Engine getDownloadURL tiling.
2. OpenStreetMap (OSM) Road Network & Bridges via Overpass API.
3. OpenStreetMap (OSM) Critical Facilities (healthcare, education, emergency, government) via Overpass API.
4. OpenStreetMap (OSM) Settlements (towns, villages, hamlets) for spatial context and zone naming.

All vector products are projected to EPSG:32643 (UTM Zone 43N).
"""

import os
import sys
import json
import time
import requests
import geopandas as gpd
import pandas as pd
import shapely.geometry as sgeom
from shapely.ops import unary_union
import ee

RAW_DIR = "data/raw/hadr"
PROC_DIR = "data/hadr"
INUNDATION_PATH = "outputs/simulations/dflowfm/BHV_BASE/inundation_extent.gpkg"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)


def get_inundation_bounds_wgs84():
    """Load inundation extent and get WGS84 bounding box and polygon."""
    gdf = gpd.read_file(INUNDATION_PATH)
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    # 500m buffer in UTM before converting to WGS84 for safety margin
    gdf_buffered = gdf.buffer(500)
    gdf_buffered_wgs84 = gdf_buffered.to_crs(epsg=4326)
    bounds = gdf_buffered_wgs84.total_bounds # minx, miny, maxx, maxy (lon_min, lat_min, lon_max, lat_max)
    return bounds, gdf_wgs84, gdf_buffered_wgs84


def download_open_buildings_ee(bounds, buffer_gdf):
    """Download Google Open Buildings v3 from Earth Engine using spatial grid tiling."""
    print("=== Acquiring Google Open Buildings v3 ===")
    ee.Initialize(project='jalrakshak-hd')
    
    min_lon, min_lat, max_lon, max_lat = bounds
    # Split into a 4 (lon) x 2 (lat) grid = 8 tiles to stay well within getDownloadURL limits
    n_x, n_y = 4, 2
    dx = (max_lon - min_lon) / n_x
    dy = (max_lat - min_lat) / n_y
    
    all_features = []
    
    for i in range(n_x):
        for j in range(n_y):
            tile_min_lon = min_lon + i * dx
            tile_max_lon = min_lon + (i + 1) * dx
            tile_min_lat = min_lat + j * dy
            tile_max_lat = min_lat + (j + 1) * dy
            
            tile_geom = ee.Geometry.Rectangle([tile_min_lon, tile_min_lat, tile_max_lon, tile_max_lat])
            dataset = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons") \
                .filterBounds(tile_geom) \
                .filter(ee.Filter.gte('confidence', 0.75))
            
            count = dataset.size().getInfo()
            print(f"Tile [{i},{j}] ({tile_min_lon:.4f}, {tile_min_lat:.4f} to {tile_max_lon:.4f}, {tile_max_lat:.4f}): {count} buildings")
            
            if count == 0:
                continue
                
            if count > 10000:
                print(f"  Subdividing tile [{i},{j}]...")
                sub_dx = dx / 2
                sub_dy = dy / 2
                for si in range(2):
                    for sj in range(2):
                        s_min_lon = tile_min_lon + si * sub_dx
                        s_max_lon = tile_min_lon + (si + 1) * sub_dx
                        s_min_lat = tile_min_lat + sj * sub_dy
                        s_max_lat = tile_min_lat + (sj + 1) * sub_dy
                        s_geom = ee.Geometry.Rectangle([s_min_lon, s_min_lat, s_max_lon, s_max_lat])
                        s_ds = dataset.filterBounds(s_geom)
                        s_count = s_ds.size().getInfo()
                        if s_count == 0:
                            continue
                        url = s_ds.getDownloadURL(filetype='geojson')
                        resp = requests.get(url, timeout=120)
                        data = resp.json()
                        features = data.get('features', [])
                        print(f"    Sub-tile [{si},{sj}]: downloaded {len(features)} features")
                        all_features.extend(features)
            else:
                url = dataset.getDownloadURL(filetype='geojson')
                resp = requests.get(url, timeout=120)
                data = resp.json()
                features = data.get('features', [])
                print(f"  Tile [{i},{j}]: downloaded {len(features)} features")
                all_features.extend(features)
                
    print(f"Total raw Open Buildings downloaded: {len(all_features)}")
    
    # Save raw geojson
    raw_geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }
    raw_path = os.path.join(RAW_DIR, "open_buildings_raw.geojson")
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(raw_geojson, f)
        
    print(f"Saved raw buildings to {raw_path}")
    
    if len(all_features) > 0:
        gdf_bld = gpd.GeoDataFrame.from_features(raw_geojson, crs="EPSG:4326")
        gdf_bld = gdf_bld.drop_duplicates(subset=['geometry'])
        
        buffer_geom = unary_union(buffer_gdf.geometry)
        gdf_bld = gdf_bld[gdf_bld.intersects(buffer_geom)].copy()
        
        gdf_bld_proj = gdf_bld.to_crs(epsg=32643)
        gdf_bld_proj['footprint_area_m2'] = gdf_bld_proj.geometry.area
        
        out_gpkg = os.path.join(PROC_DIR, "buildings.gpkg")
        gdf_bld_proj.to_file(out_gpkg, driver="GPKG")
        print(f"Saved {len(gdf_bld_proj)} clipped & projected buildings to {out_gpkg}")
    else:
        print("WARNING: No buildings downloaded!")


def query_overpass(query, max_retries=3):
    """Query Overpass API with retry."""
    url = "https://overpass-api.de/api/interpreter"
    headers = {'User-Agent': 'JalRakshak-HD-HADR-Analysis/1.0'}
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, data={'data': query}, headers=headers, timeout=120)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                print(f"Overpass rate-limited (429). Waiting 10s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(10)
            else:
                print(f"Overpass status {resp.status_code}: {resp.text[:200]}")
                time.sleep(5)
        except Exception as e:
            print(f"Overpass error: {e}. Retrying...")
            time.sleep(5)
    raise RuntimeError("Failed to query Overpass API after retries.")


def acquire_osm_infrastructure(bounds, buffer_gdf):
    """Query OSM for roads, bridges, critical facilities, and settlements."""
    print("=== Acquiring OpenStreetMap Infrastructure ===")
    min_lon, min_lat, max_lon, max_lat = bounds
    bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    
    # 1. Roads & Bridges
    road_query = f"""
    [out:json][timeout:120];
    (
      way["highway"]({bbox_str});
    );
    out body;
    >;
    out skel qt;
    """
    print("Querying OSM roads and bridges...")
    road_data = query_overpass(road_query)
    
    raw_road_path = os.path.join(RAW_DIR, "roads_osm_raw.json")
    with open(raw_road_path, 'w', encoding='utf-8') as f:
        json.dump(road_data, f)
        
    nodes = {}
    for el in road_data.get('elements', []):
        if el['type'] == 'node':
            nodes[el['id']] = (el['lon'], el['lat'])
            
    road_records = []
    for el in road_data.get('elements', []):
        if el['type'] == 'way' and 'highway' in el.get('tags', {}):
            tags = el.get('tags', {})
            way_nodes = el.get('nodes', [])
            coords = [nodes[nid] for nid in way_nodes if nid in nodes]
            if len(coords) >= 2:
                line = sgeom.LineString(coords)
                road_records.append({
                    'osm_id': el['id'],
                    'highway': tags.get('highway', 'unclassified'),
                    'name': tags.get('name', 'Unnamed Road'),
                    'bridge': tags.get('bridge', 'no'),
                    'surface': tags.get('surface', 'unknown'),
                    'lanes': tags.get('lanes', 'unknown'),
                    'maxspeed': tags.get('maxspeed', 'unknown'),
                    'geometry': line
                })
                
    if road_records:
        gdf_roads = gpd.GeoDataFrame(road_records, crs="EPSG:4326")
        gdf_roads_proj = gdf_roads.to_crs(epsg=32643)
        gdf_roads_proj['length_m'] = gdf_roads_proj.geometry.length
        
        out_road_gpkg = os.path.join(PROC_DIR, "roads.gpkg")
        gdf_roads_proj.to_file(out_road_gpkg, driver="GPKG")
        print(f"Saved {len(gdf_roads_proj)} road segments ({gdf_roads_proj['length_m'].sum()/1000:.2f} km) to {out_road_gpkg}")
        
        bridges = gdf_roads_proj[gdf_roads_proj['bridge'].isin(['yes', 'true', 'viaduct']) | gdf_roads_proj['name'].str.contains('Bridge|Palam', case=False, na=False)]
        print(f"Identified {len(bridges)} potential bridge segments in bounding box.")
    
    # 2. Critical Facilities
    fac_query = f"""
    [out:json][timeout:120];
    (
      node["amenity"~"hospital|clinic|doctors|pharmacy|school|college|kindergarten|police|fire_station|townhall|courthouse|place_of_worship"]({bbox_str});
      way["amenity"~"hospital|clinic|doctors|pharmacy|school|college|kindergarten|police|fire_station|townhall|courthouse|place_of_worship"]({bbox_str});
      node["emergency"~"ambulance_station|fire_hydrant|defibrillator|emergency_ward_entrance"]({bbox_str});
      way["emergency"~"ambulance_station"]({bbox_str});
    );
    out center;
    """
    print("Querying OSM critical facilities...")
    fac_data = query_overpass(fac_query)
    
    raw_fac_path = os.path.join(RAW_DIR, "critical_facilities_osm_raw.json")
    with open(raw_fac_path, 'w', encoding='utf-8') as f:
        json.dump(fac_data, f)
        
    fac_records = []
    for el in fac_data.get('elements', []):
        tags = el.get('tags', {})
        if el['type'] == 'node':
            pt = sgeom.Point(el['lon'], el['lat'])
        elif 'center' in el:
            pt = sgeom.Point(el['center']['lon'], el['center']['lat'])
        else:
            continue
            
        fac_type = tags.get('amenity', tags.get('emergency', 'other'))
        category = 'other'
        if fac_type in ['hospital', 'clinic', 'doctors', 'pharmacy']:
            category = 'healthcare'
        elif fac_type in ['school', 'college', 'kindergarten']:
            category = 'education'
        elif fac_type in ['police', 'fire_station', 'ambulance_station']:
            category = 'emergency_service'
        elif fac_type in ['townhall', 'courthouse']:
            category = 'government'
        elif fac_type == 'place_of_worship':
            category = 'community_assembly'
            
        fac_records.append({
            'osm_id': el['id'],
            'osm_type': el['type'],
            'name': tags.get('name', f"Unnamed {fac_type}"),
            'facility_type': fac_type,
            'category': category,
            'operator': tags.get('operator', 'unknown'),
            'geometry': pt
        })
        
    if fac_records:
        gdf_fac = gpd.GeoDataFrame(fac_records, crs="EPSG:4326")
        gdf_fac_proj = gdf_fac.to_crs(epsg=32643)
        out_fac_gpkg = os.path.join(PROC_DIR, "critical_facilities.gpkg")
        gdf_fac_proj.to_file(out_fac_gpkg, driver="GPKG")
        print(f"Saved {len(gdf_fac_proj)} critical facilities to {out_fac_gpkg}")
        
    # 3. Settlements
    place_query = f"""
    [out:json][timeout:120];
    (
      node["place"~"city|town|village|hamlet|suburb|neighbourhood"]({bbox_str});
    );
    out body;
    """
    print("Querying OSM settlements...")
    place_data = query_overpass(place_query)
    
    place_records = []
    for el in place_data.get('elements', []):
        tags = el.get('tags', {})
        pt = sgeom.Point(el['lon'], el['lat'])
        place_records.append({
            'osm_id': el['id'],
            'name': tags.get('name', tags.get('name:en', 'Unnamed')),
            'place_type': tags.get('place', 'village'),
            'population': tags.get('population', 'unknown'),
            'geometry': pt
        })
        
    if place_records:
        gdf_places = gpd.GeoDataFrame(place_records, crs="EPSG:4326")
        gdf_places_proj = gdf_places.to_crs(epsg=32643)
        out_place_gpkg = os.path.join(PROC_DIR, "settlements.gpkg")
        gdf_places_proj.to_file(out_place_gpkg, driver="GPKG")
        print(f"Saved {len(gdf_places_proj)} settlements to {out_place_gpkg}")


def main():
    print("=== Starting M8 Vector Data Acquisition ===")
    bounds, gdf_wgs84, buffer_gdf = get_inundation_bounds_wgs84()
    print(f"Inundation bounds (WGS84): min_lon={bounds[0]:.4f}, min_lat={bounds[1]:.4f}, max_lon={bounds[2]:.4f}, max_lat={bounds[3]:.4f}")
    
    download_open_buildings_ee(bounds, buffer_gdf)
    acquire_osm_infrastructure(bounds, buffer_gdf)
    print("=== Vector Data Acquisition Completed Successfully ===")


if __name__ == "__main__":
    main()
