"""Site directory and artifact path resolver for multi-site JalRakshak-HD platform.

Provides dynamic, site-namespaced directory resolution while supporting
legacy Bhavanisagar paths for zero-regression compatibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel


class SitePaths(BaseModel):
    """Container for site-specific data, simulation, and output directories."""
    site_id: str
    site_root: Path
    config_root: Path
    raw_data: Path
    terrain: Path
    hydrology: Path
    dflowfm_data: Path
    sph_data: Path
    hadr_data: Path
    gee_data: Path
    outputs: Path
    reports: Path
    validation: Path
    dashboard_assets: Path

    def ensure_directories(self) -> None:
        """Create all site-specific folders if they do not exist."""
        for name, val in self:
            if isinstance(val, Path):
                val.mkdir(parents=True, exist_ok=True)


def get_site_paths(site_id: str, project_root: Optional[Path] = None) -> SitePaths:
    """Resolve paths for a given site identifier.

    Parameters
    ----------
    site_id : str
        Unique site slug (e.g. 'bhavanisagar', 'hirakud').
    project_root : Optional[Path]
        Root directory of the JalRakshak-HD project.

    Returns
    -------
    SitePaths
        Initialized and resolved directory paths.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent.parent

    site_id_normalized = site_id.strip().lower()

    # Legacy Bhavanisagar fallback adapter to maintain M0-M10 outputs
    if site_id_normalized == "bhavanisagar":
        return SitePaths(
            site_id="bhavanisagar",
            site_root=project_root / "sites" / "bhavanisagar",
            config_root=project_root / "sites" / "bhavanisagar",
            raw_data=project_root / "data" / "raw",
            terrain=project_root / "data" / "terrain",
            hydrology=project_root / "data" / "hydrology",
            dflowfm_data=project_root / "data" / "dflowfm",
            sph_data=project_root / "data" / "sph",
            hadr_data=project_root / "data" / "hadr",
            gee_data=project_root / "data" / "gee",
            outputs=project_root / "outputs",
            reports=project_root / "outputs" / "reports",
            validation=project_root / "outputs" / "validation",
            dashboard_assets=project_root / "outputs" / "dashboard",
        )

    # Generalized structure for new sites
    site_data_dir = project_root / "data" / site_id_normalized
    site_output_dir = project_root / "outputs" / site_id_normalized

    return SitePaths(
        site_id=site_id_normalized,
        site_root=project_root / "sites" / site_id_normalized,
        config_root=project_root / "sites" / site_id_normalized,
        raw_data=site_data_dir / "raw",
        terrain=site_data_dir / "terrain",
        hydrology=site_data_dir / "hydrology",
        dflowfm_data=site_data_dir / "dflowfm",
        sph_data=site_data_dir / "sph",
        hadr_data=site_data_dir / "hadr",
        gee_data=site_data_dir / "gee",
        outputs=site_output_dir,
        reports=site_output_dir / "reports",
        validation=site_output_dir / "validation",
        dashboard_assets=site_output_dir / "dashboard",
    )
