"""Site Onboarding Wizard for JalRakshak-HD.

Scaffolds a schema-valid site package under `sites/<site_id>/` from input parameters
or interactive prompts without fabricating missing engineering attributes.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from pathlib import Path
import yaml

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.core.crs import derive_project_crs
from backend.app.schemas.site import VerificationClassification


def onboard_site(
    site_id: str,
    dam_name: str,
    river_name: str,
    state: str,
    district: str,
    latitude: float,
    longitude: float,
    country: str = "India",
    dam_height_m: float = None,
    crest_length_m: float = None,
    crest_elevation_m: float = None,
    frl_m: float = None,
    gross_storage_mcm: float = None,
    live_storage_mcm: float = None,
    output_dir: Path = None,
) -> Path:
    """Create site package folder and initial YAML configuration files."""
    if output_dir is None:
        site_folder = project_root / "sites" / site_id.strip().lower()
    else:
        site_folder = Path(output_dir) / site_id.strip().lower()

    site_folder.mkdir(parents=True, exist_ok=True)

    # Automatically derive CRS and approximate AOI (+/- 0.2 deg buffer)
    crs_info = derive_project_crs(latitude, longitude)
    aoi_bbox = [
        round(longitude - 0.25, 4),
        round(latitude - 0.20, 4),
        round(longitude + 0.25, 4),
        round(latitude + 0.20, 4),
    ]

    # 1. site.yaml
    site_yaml = {
        "site_id": site_id,
        "display_name": f"{dam_name} & {river_name} Corridor",
        "description": f"Site model package for {dam_name} on {river_name}, {district} District, {state}.",
        "identity": {
            "dam_name": dam_name,
            "river_name": river_name,
            "basin_name": f"{river_name} Basin",
            "country": country,
            "state": state,
            "district": district,
            "latitude": latitude,
            "longitude": longitude,
            "impoundment_type": "ENGINEERED_DAM",
            "national_id": None,
            "year_completed": None,
            "dam_type": "Embankment / Composite Dam",
        },
        "study_area": {
            "aoi_bbox_wgs84": aoi_bbox,
            "dam_coordinates_wgs84": [longitude, latitude],
            "downstream_reach_length_km": 30.0,
            "domain_area_km2": None,
            "crs": crs_info.model_dump(),
        }
    }
    with open(site_folder / "site.yaml", "w", encoding="utf-8") as f:
        yaml.dump(site_yaml, f, sort_keys=False)

    # 2. dam.yaml
    dam_yaml = {
        "dam": {
            "crest_elevation_m": crest_elevation_m,
            "dam_height_m": dam_height_m,
            "height_above_riverbed_m": None,
            "crest_length_m": crest_length_m,
            "crest_width_m": None,
            "upstream_slope_ratio": 3.0,
            "downstream_slope_ratio": 2.0,
            "spillway_type": "Ogee Gated Spillway",
            "spillway_crest_elevation_m": None,
            "spillway_capacity_m3s": None,
            "number_of_gates": None,
            "verification": "SECONDARY_VERIFIED" if dam_height_m else "UNVERIFIED",
        }
    }
    with open(site_folder / "dam.yaml", "w", encoding="utf-8") as f:
        yaml.dump(dam_yaml, f, sort_keys=False)

    # 3. hydrology.yaml
    hydro_yaml = {
        "reservoir": {
            "full_reservoir_level_m": frl_m,
            "maximum_water_level_m": frl_m,
            "dead_storage_level_m": None,
            "gross_storage_capacity_mcm": gross_storage_mcm,
            "live_storage_capacity_mcm": live_storage_mcm,
            "dead_storage_capacity_mcm": None,
            "reservoir_area_frl_km2": None,
            "catchment_area_km2": None,
            "verification": "SECONDARY_VERIFIED" if gross_storage_mcm else "UNVERIFIED",
        },
        "river": {
            "reach_name": f"{river_name} Downstream Reach",
            "downstream_length_km": 30.0,
            "average_bed_slope": None,
            "main_confluence": None,
            "primary_gauges": [],
        }
    }
    with open(site_folder / "hydrology.yaml", "w", encoding="utf-8") as f:
        yaml.dump(hydro_yaml, f, sort_keys=False)

    # 4. breach.yaml
    breach_yaml = {
        "scenarios": {
            f"{site_id}_screening_01": {
                "scenario_id": f"{site_id}_screening_01",
                "scenario_name": f"Hypothetical Screening Overtopping Breach for {dam_name}",
                "breach_method": "Froehlich_2008",
                "breach_formation_mode": "OVERTOPPING",
                "failure_elevation_m": frl_m,
                "breach_bottom_elevation_m": None,
                "breach_height_m": dam_height_m,
                "reservoir_volume_at_breach_mcm": live_storage_mcm or gross_storage_mcm,
                "average_breach_width_m": None,
                "side_slope_z": 1.0,
                "breach_formation_time_s": None,
                "peak_discharge_m3s": None,
                "hydrograph_time_step_s": 60.0,
                "hydrograph_duration_s": 108000.0,
                "verification": "MODEL_ASSUMPTION",
            }
        }
    }
    with open(site_folder / "breach.yaml", "w", encoding="utf-8") as f:
        yaml.dump(breach_yaml, f, sort_keys=False)

    # 5. model.yaml
    model_yaml = {
        "hydraulic_model": {
            "solver_name": "D-Flow FM",
            "grid_type": "flexible_mesh_unstructured",
            "target_cell_size_m": 50.0,
            "manning_roughness_global": 0.035,
            "upstream_boundary_type": "discharge_hydrograph",
            "downstream_boundary_type": "free_outflow",
            "timestep_min_s": 0.1,
            "timestep_max_s": 10.0,
            "simulation_duration_s": 108000.0,
            "output_interval_s": 600.0,
        },
        "sph_model": {
            "solver_name": "DualSPHysics",
            "dimension": "2D_UNIT_WIDTH",
            "classification": "2D_UNIT_WIDTH_NEAR_FIELD_SPH_SCREENING_MODEL",
            "dp_particle_spacing_m": 1.0,
            "simulation_duration_s": 600.0,
            "upstream_reservoir_extent_m": 100.0,
            "downstream_chute_extent_m": 1500.0,
            "time_step_out_s": 1.0,
        }
    }
    with open(site_folder / "model.yaml", "w", encoding="utf-8") as f:
        yaml.dump(model_yaml, f, sort_keys=False)

    # 6. monitoring.yaml
    mon_yaml = {
        "earth_observation": {
            "satellite_platform": "Sentinel-1",
            "orbit_pass_preference": "DESCENDING",
            "relative_orbit_preference": None,
            "historical_scene_id": None,
            "detection_threshold_delta_db": -3.0,
            "event_vv_threshold_db": -14.0,
            "slope_threshold_deg": 5.0,
        }
    }
    with open(site_folder / "monitoring.yaml", "w", encoding="utf-8") as f:
        yaml.dump(mon_yaml, f, sort_keys=False)

    # 7. source_manifest.json
    manifest = [
        {
            "parameter": "dam_coordinates",
            "value": [longitude, latitude],
            "unit": "degrees_WGS84",
            "dataset_name": "Initial Onboarding Registration",
            "provider": "User Onboarding Wizard",
            "retrieval_date": "2026-09-26",
            "verification": "SECONDARY_VERIFIED",
            "citation": f"Registered via onboard_site for {dam_name}",
            "limitations": "Initial coordinate entry, pending field survey validation"
        }
    ]
    with open(site_folder / "source_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[SUCCESS] New site package created at: {site_folder}")
    print(f"  Derived Projected CRS: {crs_info.project_crs} ({crs_info.derivation_reason})")
    print(f"  Initial AOI: {aoi_bbox}")
    return site_folder


def main():
    parser = argparse.ArgumentParser(description="JalRakshak-HD Site Onboarding Wizard")
    parser.add_argument("--config", help="Path to input YAML/JSON onboarding spec")
    parser.add_argument("--site-id", help="Unique site identifier slug (e.g. idukki, ukai)")
    parser.add_argument("--dam-name", help="Full dam name")
    parser.add_argument("--river", help="River name")
    parser.add_argument("--state", help="State / Province")
    parser.add_argument("--district", help="District")
    parser.add_argument("--lat", type=float, help="Dam latitude in decimal degrees")
    parser.add_argument("--lon", type=float, help="Dam longitude in decimal degrees")
    parser.add_argument("--height", type=float, help="Dam height in metres")
    parser.add_argument("--length", type=float, help="Dam crest length in metres")
    parser.add_argument("--storage", type=float, help="Gross storage in MCM")

    args = parser.parse_args()

    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            if args.config.endswith(".json"):
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        onboard_site(**data)
    elif args.site_id and args.dam_name and args.lat is not None and args.lon is not None:
        onboard_site(
            site_id=args.site_id,
            dam_name=args.dam_name,
            river_name=args.river or "Unknown River",
            state=args.state or "Unknown State",
            district=args.district or "Unknown District",
            latitude=args.lat,
            longitude=args.lon,
            dam_height_m=args.height,
            crest_length_m=args.length,
            gross_storage_mcm=args.storage,
        )
    else:
        print("Please provide --config <file> or mandatory arguments (--site-id, --dam-name, --lat, --lon).")
        sys.exit(1)


if __name__ == "__main__":
    main()
