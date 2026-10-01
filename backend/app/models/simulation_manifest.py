"""Simulation manifest model for JalRakshak-HD.

Provides a structured, auditable schema for hydrodynamic and particle
simulation runs, tracking provenance, solver versions, inputs, and outputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SimulationStatus(str, Enum):
    """Execution status of a hydrodynamic simulation."""

    PENDING = "PENDING"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class SolverType(str, Enum):
    """Supported scientific solvers."""

    DFLOWFM = "DFLOWFM"
    DUALSPHYSICS_CPU = "DUALSPHYSICS_CPU"
    DUALSPHYSICS_GPU = "DUALSPHYSICS_GPU"
    HYBRID_COUPLING = "HYBRID_COUPLING"


class InputDatasetRecord(BaseModel):
    """Data provenance record for an input dataset used in simulation."""

    dataset_name: str
    dataset_type: str  # e.g., "DEM", "HYDROGRAPH", "BOUNDARY_CONDITION", "LAND_COVER"
    source_path: Path
    checksum_sha256: Optional[str] = None
    provider: Optional[str] = None
    crs: Optional[str] = None
    spatial_resolution_m: Optional[float] = None
    temporal_resolution: Optional[str] = None
    acquisition_date: Optional[str] = None


class SimulationManifest(BaseModel):
    """Comprehensive, reproducible manifest for a single simulation run."""

    simulation_id: str = Field(..., description="Unique simulation identifier (e.g. SIM-2026-001)")
    study_area: Optional[str] = Field(default=None, description="Study region / basin name")
    dam_name: Optional[str] = Field(default=None, description="Target dam or structure name")
    river_name: Optional[str] = Field(default=None, description="Reach or river system name")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of manifest creation",
    )
    input_datasets: List[InputDatasetRecord] = Field(
        default_factory=list, description="List of validated input datasets"
    )
    solver: SolverType = Field(..., description="Engine solver used for run")
    solver_version: Optional[str] = Field(default=None, description="Solver version string")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Solver parameters, mesh config, and time-step controls"
    )
    output_directory: Path = Field(..., description="Target directory for simulation output artifacts")
    status: SimulationStatus = Field(default=SimulationStatus.PENDING, description="Current execution state")
    completed_at: Optional[datetime] = Field(default=None, description="Timestamp upon completion")
    error_message: Optional[str] = Field(default=None, description="Error log summary if failed")

    class Config:
        use_enum_values = True
