import json
import csv
from pathlib import Path

def build_affected_places():
    root = Path("C:/JalRakshak-HD")
    out_dir = root / "outputs" / "dashboard" / "impact"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load settlements geojson
    with open(root / "outputs" / "dashboard" / "geojson" / "settlements.geojson", "r", encoding="utf-8") as f:
        settlements_gj = json.load(f)
        
    # Authoritative D-Flow FM, HADR Zones, and Reach Extent (Total Length = 51.73 km)
    # Zone 1: Bhavanisagar (Ch. 0.00-7.50 km, Arr: 0.00h, Depth: 21.99m, Vel: 10.76m/s, Haz: H6)
    # Zone 2: Sathyamangalam (Ch. 7.50-17.50 km, Arr: 1.83h / 2.00h, Depth: 17.56m, Vel: 6.40m/s, Haz: H6)
    # Zone 3: Kodiveri (Ch. 17.50-26.50 km, Arr: 4.17h, Depth: 18.80m, Vel: 6.07m/s, Haz: H6)
    # Zone 4: Gobichettipalayam (Ch. 26.50-35.50 km, Arr: 6.00h, Depth: 16.06m, Vel: 5.68m/s, Haz: H6)
    # Zone 5: Kalingarayanpalayam (Ch. 35.50-44.50 km, Arr: 7.83h / 8.00h, Depth: 12.69m, Vel: 5.61m/s, Haz: H6)
    # Zone 6: Bhavani (Ch. 44.50-51.73 km, Arr: 8.33h / 9.50h, Depth: 11.59m / 15.60m, Vel: 3.11m / 8.04m/s, Haz: H6)
    
    zone_profiles = {
        "Bhavanisagar": {
            "zone": "ZONE_01 (Bhavanisagar Dam Toe Reach, Ch. 0.00-7.50 km)",
            "affected": True,
            "arrival_hr": 0.0,
            "max_depth_m": 21.99,
            "max_vel_mps": 10.76,
            "hazard_class": "H6",
            "priority": "IMMEDIATE_<30_MIN",
            "buildings_zone": 5050,
            "roads_zone_km": 19.8,
            "bridges_zone": 1,
            "facilities_zone": 1,
            "notes": "Settlement reference point affected; whole municipal area not quantified. Located downstream of earthen embankment breach (Ch. 0.00-7.50 km)."
        },
        "Sathyamangalam": {
            "zone": "ZONE_02 (Sathyamangalam Urban & Peri-Urban Corridor, Ch. 7.50-17.50 km)",
            "affected": True,
            "arrival_hr": 2.0,
            "max_depth_m": 17.56,
            "max_vel_mps": 6.40,
            "hazard_class": "H6",
            "priority": "PRIORITY_1_2_HR",
            "buildings_zone": 6140,
            "roads_zone_km": 59.24,
            "bridges_zone": 4,
            "facilities_zone": 0,
            "notes": "Settlement reference point affected; whole municipal area not quantified. Major urban reach along Lower Bhavani River (Ch. 7.50-17.50 km)."
        },
        "Kodiveri": {
            "zone": "ZONE_03 (Ariyappampalayam-Kodiveri Agricultural Reach, Ch. 17.50-26.50 km)",
            "affected": True,
            "arrival_hr": 4.17,
            "max_depth_m": 18.80,
            "max_vel_mps": 6.07,
            "hazard_class": "H6",
            "priority": "ADVANCE_NOTICE_>2_HR",
            "buildings_zone": 8681,
            "roads_zone_km": 83.02,
            "bridges_zone": 9,
            "facilities_zone": 15,
            "notes": "Settlement reference point affected; whole municipal area not quantified. Agricultural and anicut reach (Ch. 17.50-26.50 km)."
        },
        "Gobichettipalayam": {
            "zone": "ZONE_04 (Gobichettipalayam Approach Reach, Ch. 26.50-35.50 km)",
            "affected": True,
            "arrival_hr": 6.0,
            "max_depth_m": 16.06,
            "max_vel_mps": 5.68,
            "hazard_class": "H6",
            "priority": "ADVANCE_NOTICE_>2_HR",
            "buildings_zone": 4742,
            "roads_zone_km": 59.02,
            "bridges_zone": 3,
            "facilities_zone": 6,
            "notes": "Settlement reference point affected; whole municipal area not quantified. Approach reach along Lower Bhavani River (Ch. 26.50-35.50 km)."
        },
        "Kalingarayanpalayam": {
            "zone": "ZONE_05 (Gobichettipalayam-Kavindapadi Northern Floodplain, Ch. 35.50-44.50 km)",
            "affected": True,
            "arrival_hr": 8.0,
            "max_depth_m": 12.69,
            "max_vel_mps": 5.61,
            "hazard_class": "H6",
            "priority": "ADVANCE_NOTICE_>2_HR",
            "buildings_zone": 376,
            "roads_zone_km": 5.62,
            "bridges_zone": 1,
            "facilities_zone": 3,
            "notes": "Settlement reference point affected; whole municipal area not quantified. Canal intake and northern floodplain reach (Ch. 35.50-44.50 km)."
        },
        "Bhavani": {
            "zone": "ZONE_06 (Lower Bhavani Canal Confluence Reach, Ch. 44.50-51.73 km)",
            "affected": True,
            "arrival_hr": 8.33,
            "max_depth_m": 11.59,
            "max_vel_mps": 3.11,
            "hazard_class": "H6",
            "priority": "ADVANCE_NOTICE_>2_HR",
            "buildings_zone": 663,
            "roads_zone_km": 17.12,
            "bridges_zone": 2,
            "facilities_zone": 15,
            "notes": "Settlement reference point affected; whole municipal area not quantified. Kaveri confluence reach terminating at Ch. 51.73 km."
        },
        "Komarapalayam": {
            "zone": "Outside Modeled Reach (>51.73 km)",
            "affected": False,
            "arrival_hr": None,
            "max_depth_m": None,
            "max_vel_mps": None,
            "hazard_class": None,
            "priority": "OUTSIDE_MODELED_INUNDATION",
            "buildings_zone": None,
            "roads_zone_km": None,
            "bridges_zone": None,
            "facilities_zone": None,
            "notes": "Settlement lies on eastern bank of Kaveri River beyond the 51.73 km Lower Bhavani modeled reach boundary."
        },
        "Nambiyur": {
            "zone": "Outside Inundation Corridor",
            "affected": False,
            "arrival_hr": None,
            "max_depth_m": None,
            "max_vel_mps": None,
            "hazard_class": None,
            "priority": "OUTSIDE_MODELED_INUNDATION",
            "buildings_zone": None,
            "roads_zone_km": None,
            "bridges_zone": None,
            "facilities_zone": None,
            "notes": "Located on southern elevated ridge outside D-Flow wet extent."
        },
        "Sirumugai": {
            "zone": "Upstream Reservoir Catchment",
            "affected": False,
            "arrival_hr": None,
            "max_depth_m": None,
            "max_vel_mps": None,
            "hazard_class": None,
            "priority": "OUTSIDE_MODELED_INUNDATION",
            "buildings_zone": None,
            "roads_zone_km": None,
            "bridges_zone": None,
            "facilities_zone": None,
            "notes": "Located upstream along Bhavani River reservoir inflow arm."
        },
        "Mettupalayam": {
            "zone": "Upstream Reservoir Catchment",
            "affected": False,
            "arrival_hr": None,
            "max_depth_m": None,
            "max_vel_mps": None,
            "hazard_class": None,
            "priority": "OUTSIDE_MODELED_INUNDATION",
            "buildings_zone": None,
            "roads_zone_km": None,
            "bridges_zone": None,
            "facilities_zone": None,
            "notes": "Located upstream in Nilgiris foothill catchment above reservoir headwaters."
        }
    }
    
    places_list = []
    
    for feat in settlements_gj["features"]:
        props = feat["properties"]
        geom = feat["geometry"]
        name = props["name"]
        lat = props["latitude"]
        lon = props["longitude"]
        
        prof = zone_profiles.get(name, {
            "zone": "Unclassified",
            "affected": False,
            "arrival_hr": None,
            "max_depth_m": None,
            "max_vel_mps": None,
            "hazard_class": None,
            "priority": "OUTSIDE_MODELED_INUNDATION",
            "buildings_zone": None,
            "roads_zone_km": None,
            "bridges_zone": None,
            "facilities_zone": None,
            "notes": "No model coverage."
        })
        
        place_record = {
            "place_name": name,
            "source": "OpenStreetMap Real Geographic Settlements",
            "geometry_type": "Point",
            "classification": "POINT_BASED_SETTLEMENT_SCREENING",
            "lat": lat,
            "lon": lon,
            "response_zone": prof["zone"],
            "affected": prof["affected"],
            "earliest_arrival_hr": prof["arrival_hr"],
            "max_depth_m": prof["max_depth_m"],
            "max_velocity_mps": prof["max_vel_mps"],
            "hazard_class": prof["hazard_class"],
            "arrival_priority": prof["priority"],
            "population_estimate": None,
            "population_method": "POINT_SCREENING_POPULATION_UNALLOCATED",
            "buildings_exposed": prof["buildings_zone"],
            "roads_exposed_km": prof["roads_zone_km"],
            "bridges_exposed": prof["bridges_zone"],
            "facilities_exposed": prof["facilities_zone"],
            "notes": prof["notes"]
        }
        places_list.append(place_record)
        
    # Sort: affected first, earliest arrival ascending, then hazard
    def sort_key(p):
        if not p["affected"] or p["earliest_arrival_hr"] is None:
            return (999, 999)
        return (0, p["earliest_arrival_hr"])
        
    places_list.sort(key=sort_key)
    
    # Write JSON
    json_path = out_dir / "affected_places.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "project": "JalRakshak-HD",
            "scenario": "BHV_BASE",
            "site": "Bhavanisagar Dam",
            "total_settlements_screened": len(places_list),
            "affected_settlements_count": len([p for p in places_list if p["affected"]]),
            "unaffected_settlements_count": len([p for p in places_list if not p["affected"]]),
            "places": places_list
        }, f, indent=2)
        
    # Write CSV
    csv_path = out_dir / "affected_places.csv"
    fieldnames = [
        "place_name", "source", "geometry_type", "lat", "lon", "response_zone",
        "affected", "earliest_arrival_hr", "max_depth_m", "max_velocity_mps",
        "hazard_class", "arrival_priority", "population_estimate", "population_method",
        "buildings_exposed", "roads_exposed_km", "bridges_exposed", "facilities_exposed", "notes"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for p in places_list:
            writer.writerow(p)
            
    print(f"[OK] Generated {json_path} and {csv_path}")

if __name__ == "__main__":
    build_affected_places()

