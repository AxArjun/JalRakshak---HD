"""Configuration loader and schema validator for JalRakshak-HD.

Loads paths, external solver locations, and project metadata from YAML configuration
files and environment variables, validating file system paths and external tool availability.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure PROJ uses Python environment database
try:
    import pyproj
    os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
    os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()
except Exception:
    pass

import yaml
from pydantic import BaseModel, Field, field_validator


class ProjectPathsConfig(BaseModel):
    """File system paths used throughout JalRakshak-HD."""

    project_root: Path
    raw_data: Path
    processed_data: Path
    terrain: Path
    hydrology: Path
    gee: Path
    dflowfm_data: Path
    sph_data: Path
    hadr_data: Path
    observations: Path
    outputs: Path
    logs: Path

    @field_validator("*", mode="before")
    @classmethod
    def resolve_path(cls, v: Any) -> Path:
        """Resolve string or Path object to normalized absolute Path."""
        if v is None:
            raise ValueError("Path value cannot be None")
        return Path(v).expanduser().resolve()

    def ensure_directories(self) -> None:
        """Ensure all defined directory paths exist on disk."""
        for field_name, path_val in self:
            if isinstance(path_val, Path):
                path_val.mkdir(parents=True, exist_ok=True)


class ExternalToolsConfig(BaseModel):
    """Executable paths for external scientific hydrodynamic and particle solvers."""

    dflowfm_exe: Path
    dimr_exe: Path
    dualsphysics_cpu_exe: Path
    gencase_exe: Path

    @field_validator("*", mode="before")
    @classmethod
    def resolve_exe_path(cls, v: Any) -> Path:
        """Resolve executable path."""
        if v is None:
            raise ValueError("Executable path value cannot be None")
        return Path(v).expanduser().resolve()

    def validate_tools(self, raise_on_error: bool = False) -> Dict[str, bool]:
        """Check if all configured executables exist on disk.

        Parameters
        ----------
        raise_on_error : bool
            If True, raise FileNotFoundError on the first missing executable.

        Returns
        -------
        Dict[str, bool]
            Dictionary mapping tool field name to existence status.
        """
        statuses = {}
        for field_name, exe_path in self:
            exists = isinstance(exe_path, Path) and exe_path.is_file()
            statuses[field_name] = exists
            if not exists and raise_on_error:
                raise FileNotFoundError(
                    f"Required external executable '{field_name}' not found at: {exe_path}"
                )
        return statuses


class ProjectMetadataConfig(BaseModel):
    """General project metadata and high-level simulation configuration."""

    project_name: str = "JalRakshak-HD"
    problem_statement: str = "PS 26161"
    simulation_mode: str = "research_prototype"
    default_crs: Optional[str] = None
    study_area: Optional[str] = None
    dam: Optional[str] = None
    river: Optional[str] = None


class Settings(BaseModel):
    """Composite settings container for JalRakshak-HD."""

    paths: ProjectPathsConfig
    external_tools: ExternalToolsConfig
    project: ProjectMetadataConfig
    postgres_host: str = Field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = Field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    postgres_db: str = Field(default_factory=lambda: os.getenv("POSTGRES_DB", "jalrakshak_db"))
    postgres_user: str = Field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    postgres_password: Optional[str] = Field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    earth_engine_project: str = Field(
        default_factory=lambda: os.getenv("EARTH_ENGINE_PROJECT", "jalrakshak-hd")
    )


def load_yaml(file_path: Path | str) -> Dict[str, Any]:
    """Safely load and parse a YAML file."""
    path = Path(file_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file {path} did not parse into a dictionary.")
    return data


def load_settings(
    paths_yaml: Optional[Path | str] = None,
    project_yaml: Optional[Path | str] = None,
) -> Settings:
    """Load and validate all project configurations from YAML files."""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    paths_file = Path(paths_yaml) if paths_yaml else base_dir / "configs" / "paths.yaml"
    proj_file = Path(project_yaml) if project_yaml else base_dir / "configs" / "project.yaml"

    paths_data = load_yaml(paths_file)
    project_data = load_yaml(proj_file)

    if "paths" not in paths_data or "external_tools" not in paths_data:
        raise KeyError(
            f"paths.yaml at {paths_file} must contain 'paths' and 'external_tools' root keys."
        )

    paths_config = ProjectPathsConfig(**paths_data["paths"])
    external_tools_config = ExternalToolsConfig(**paths_data["external_tools"])
    project_config = ProjectMetadataConfig(**project_data)

    return Settings(
        paths=paths_config,
        external_tools=external_tools_config,
        project=project_config,
    )


# Global singleton cache
_settings: Optional[Settings] = None


def get_settings(force_reload: bool = False) -> Settings:
    """Retrieve global cached settings instance."""
    global _settings
    if _settings is None or force_reload:
        _settings = load_settings()
    return _settings
