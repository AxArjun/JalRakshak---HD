"""Generic D-Flow FM 2D Hydraulic Model Input Builder.

Prepares standardized simulation directories, boundary conditions (.bc),
external forcing files (.ext), and MDU model definitions from generalized site configurations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from backend.app.schemas.site import SiteConfig, BreachScenarioConfig
from backend.app.core.site_paths import get_site_paths, SitePaths


class DFlowModelBuilder:
    """Builder for site-namespaced D-Flow FM simulation configurations."""

    @staticmethod
    def build_boundary_conditions(
        scenario: BreachScenarioConfig,
        output_bc_file: Path
    ) -> None:
        """Write standard D-Flow FM boundary conditions file (.bc)."""
        output_bc_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_bc_file, "w", encoding="utf-8") as f:
            f.write(f"# D-Flow FM Boundary Condition File: {scenario.scenario_id}\n")
            f.write(f"# Method: {scenario.breach_method} | Failure Mode: {scenario.breach_formation_mode}\n\n")
            f.write("[Boundary]\n")
            f.write("Name                 = UpstreamDamInflow\n")
            f.write("Function             = time-series\n")
            f.write("Time-interpolation   = linear\n")
            f.write("Quantity             = time\n")
            f.write("Unit                 = minutes since 2026-09-26 00:00:00\n")
            f.write("Quantity             = total_discharge\n")
            f.write("Unit                 = m3/s\n\n")
            f.write(f"0.00                 0.00\n")
            if scenario.breach_formation_time_s and scenario.peak_discharge_m3s:
                rise_min = scenario.breach_formation_time_s / 60.0
                f.write(f"{rise_min:.2f}               {scenario.peak_discharge_m3s:.2f}\n")
                dur_min = (2.0 * (scenario.reservoir_volume_at_breach_mcm or 780.5) * 1e6 / scenario.peak_discharge_m3s) / 60.0
                f.write(f"{dur_min:.2f}              0.00\n")

    @staticmethod
    def generate_mdu_config(
        site_config: SiteConfig,
        scenario: BreachScenarioConfig,
        output_dir: Path
    ) -> Path:
        """Generate master D-Flow FM definition file (.mdu)."""
        output_dir.mkdir(parents=True, exist_ok=True)
        mdu_file = output_dir / f"{site_config.site_id}_{scenario.scenario_id}.mdu"
        mdu_content = f"""# Master Definition File for D-Flow FM (JalRakshak-HD Multi-Site Engine)
[model]
Program            = D-Flow FM
Version            = 1.2.0
ModelType          = 2D
SiteId             = {site_config.site_id}
ScenarioId         = {scenario.scenario_id}

[geometry]
NetFile            = {site_config.site_id}_mesh_net.nc
BathymetryFile     = {site_config.site_id}_bathymetry.xyz
BedLevType         = 3

[physics]
Gravity            = 9.80665
WaterDensity       = 1000.0

[numerics]
CFLMax             = 0.7
AdvectionType      = 1
TimeStepMin        = {site_config.hydraulic_model.timestep_min_s}
TimeStepMax        = {site_config.hydraulic_model.timestep_max_s}

[time]
RefDate            = 20260926
TStart             = 0.0
TStop              = {site_config.hydraulic_model.simulation_duration_s}
DtUser             = {site_config.hydraulic_model.output_interval_s}

[output]
OutputDir          = DFM_OUTPUT_{site_config.site_id}
MapInterval        = {site_config.hydraulic_model.output_interval_s}
HisInterval        = 60.0
"""
        with open(mdu_file, "w", encoding="utf-8") as f:
            f.write(mdu_content)

        return mdu_file
