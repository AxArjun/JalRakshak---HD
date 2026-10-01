"""Site Registry Service for JalRakshak-HD.

Loads, registers, and manages site packages across the multi-site platform
without any hardcoded scientific constants.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from backend.app.schemas.site import (
    SiteConfig,
    DamIdentity,
    DamGeometry,
    ReservoirMetadata,
    RiverMetadata,
    StudyAreaConfig,
    CRSConfig,
    BreachScenarioConfig,
    HydraulicModelConfig,
    SPHModelConfig,
    EarthObservationConfig,
    DataSourceRecord,
    ValidationStatus,
    GateStatus,
)
from backend.app.core.site_paths import get_site_paths, SitePaths
from backend.app.core.crs import derive_project_crs


def get_project_root() -> Path:
    """Find absolute project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent


def list_sites(project_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """List all registered sites and their enabled statuses.

    Returns
    -------
    List[Dict[str, Any]]
        List of registered site summaries.
    """
    if project_root is None:
        project_root = get_project_root()

    sites_config_file = project_root / "configs" / "sites.yaml"
    if not sites_config_file.is_file():
        # Fallback to scanning sites directory
        sites_dir = project_root / "sites"
        results = []
        if sites_dir.is_dir():
            for child in sites_dir.iterdir():
                if child.is_dir() and (child / "site.yaml").is_file():
                    results.append({
                        "site_id": child.name,
                        "display_name": child.name.replace("_", " ").title(),
                        "enabled": True,
                    })
        return results

    with open(sites_config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    sites_dict = data.get("sites", {})
    results = []
    for s_id, s_info in sites_dict.items():
        results.append({
            "site_id": s_id,
            "display_name": s_info.get("display_name", s_id.title()),
            "enabled": s_info.get("enabled", True),
            "state": s_info.get("state"),
            "river": s_info.get("river"),
            "status": s_info.get("status", "REGISTERED"),
        })
    return results


def get_active_site(project_root: Optional[Path] = None) -> str:
    """Get active default site identifier."""
    if project_root is None:
        project_root = get_project_root()

    sites_config_file = project_root / "configs" / "sites.yaml"
    if sites_config_file.is_file():
        with open(sites_config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if "active_site" in data:
                return str(data["active_site"])
    return "bhavanisagar"


def load_site(site_id: str, project_root: Optional[Path] = None) -> SiteConfig:
    """Load fully assembled SiteConfig object for a given site ID.

    Parameters
    ----------
    site_id : str
        Site identifier (e.g., 'bhavanisagar', 'hirakud').
    project_root : Optional[Path]
        Project root directory.

    Returns
    -------
    SiteConfig
        Assembled and validated site configuration.
    """
    if project_root is None:
        project_root = get_project_root()

    site_dir = project_root / "sites" / site_id.strip().lower()
    if not site_dir.is_dir():
        raise FileNotFoundError(f"Site directory not found: {site_dir}")

    # Load constituent yaml files
    site_yaml = site_dir / "site.yaml"
    dam_yaml = site_dir / "dam.yaml"
    hydrology_yaml = site_dir / "hydrology.yaml"
    breach_yaml = site_dir / "breach.yaml"
    model_yaml = site_dir / "model.yaml"
    monitoring_yaml = site_dir / "monitoring.yaml"
    source_manifest_json = site_dir / "source_manifest.json"

    if not site_yaml.is_file():
        raise FileNotFoundError(f"Missing mandatory site.yaml in {site_dir}")

    with open(site_yaml, "r", encoding="utf-8") as f:
        site_data = yaml.safe_load(f) or {}

    dam_data = {}
    if dam_yaml.is_file():
        with open(dam_yaml, "r", encoding="utf-8") as f:
            dam_data = (yaml.safe_load(f) or {}).get("dam", {})

    hydro_data = {}
    if hydrology_yaml.is_file():
        with open(hydrology_yaml, "r", encoding="utf-8") as f:
            hydro_data = yaml.safe_load(f) or {}

    breach_data = {}
    if breach_yaml.is_file():
        with open(breach_yaml, "r", encoding="utf-8") as f:
            breach_data = (yaml.safe_load(f) or {}).get("scenarios", {})

    model_data = {}
    if model_yaml.is_file():
        with open(model_yaml, "r", encoding="utf-8") as f:
            model_data = yaml.safe_load(f) or {}

    monitoring_data = {}
    if monitoring_yaml.is_file():
        with open(monitoring_yaml, "r", encoding="utf-8") as f:
            monitoring_data = (yaml.safe_load(f) or {}).get("earth_observation", {})

    provenance_records = []
    if source_manifest_json.is_file():
        with open(source_manifest_json, "r", encoding="utf-8") as f:
            records = json.load(f)
            for r in records:
                provenance_records.append(DataSourceRecord(**r))

    # Parse and validate components
    identity = DamIdentity(**site_data.get("identity", {}))
    geometry = DamGeometry(**dam_data)
    reservoir = ReservoirMetadata(**hydro_data.get("reservoir", {}))
    river = RiverMetadata(**hydro_data.get("river", {}))

    study_area_raw = site_data.get("study_area", {})
    crs_raw = study_area_raw.get("crs", {})
    if not crs_raw:
        crs_config = derive_project_crs(identity.latitude, identity.longitude)
    else:
        crs_config = CRSConfig(**crs_raw)

    study_area = StudyAreaConfig(
        aoi_bbox_wgs84=study_area_raw.get("aoi_bbox_wgs84", []),
        dam_coordinates_wgs84=study_area_raw.get("dam_coordinates_wgs84", [identity.longitude, identity.latitude]),
        downstream_reach_length_km=study_area_raw.get("downstream_reach_length_km", 30.0),
        domain_area_km2=study_area_raw.get("domain_area_km2"),
        crs=crs_config,
    )

    breach_scenarios = {}
    for scn_id, scn_dict in breach_data.items():
        breach_scenarios[scn_id] = BreachScenarioConfig(**scn_dict)

    hydraulic_model = HydraulicModelConfig(**model_data.get("hydraulic_model", {}))
    sph_model = SPHModelConfig(**model_data.get("sph_model", {}))
    earth_observation = EarthObservationConfig(**monitoring_data)

    return SiteConfig(
        site_id=site_data.get("site_id", site_id),
        display_name=site_data.get("display_name", site_id.title()),
        description=site_data.get("description", ""),
        identity=identity,
        geometry=geometry,
        reservoir=reservoir,
        river=river,
        study_area=study_area,
        breach_scenarios=breach_scenarios,
        hydraulic_model=hydraulic_model,
        sph_model=sph_model,
        earth_observation=earth_observation,
        provenance=provenance_records,
        validation=ValidationStatus(),
    )
