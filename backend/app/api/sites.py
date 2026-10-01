"""Multi-Site Management API Endpoints for JalRakshak-HD.

Exposes site registry, configuration retrieval, validation diagnostics,
and capability matrices across registered dam study areas.
"""

from __future__ import annotations

from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Path

from backend.app.services.site_registry import list_sites, load_site, get_active_site
from backend.app.services.site_validator import validate_site_config
from backend.app.services.workflow_gates import evaluate_workflow_gates

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("", summary="List all registered study sites")
def get_all_sites() -> Dict[str, Any]:
    """Retrieve list of all registered study sites with their status."""
    sites = list_sites()
    active = get_active_site()
    return {
        "active_site": active,
        "total_sites": len(sites),
        "sites": sites,
    }


@router.get("/{site_id}", summary="Get configuration for a specific site")
def get_site_details(site_id: str = Path(..., description="Site identifier (e.g. bhavanisagar, hirakud)")) -> Dict[str, Any]:
    """Retrieve full validated configuration for a specific study site."""
    try:
        site_cfg = load_site(site_id)
        return site_cfg.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found in registry.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load site '{site_id}': {str(e)}")


@router.get("/{site_id}/status", summary="Get workflow gates status for a site")
def get_site_status(site_id: str = Path(..., description="Site identifier")) -> Dict[str, Any]:
    """Evaluate and return workflow readiness gates A through H for a site."""
    try:
        site_cfg = load_site(site_id)
        val_report = validate_site_config(site_cfg)
        gate_status = evaluate_workflow_gates(site_cfg)
        return {
            "site_id": site_id,
            "display_name": site_cfg.display_name,
            "is_schema_valid": val_report.is_valid,
            "validation_errors": [e.model_dump() for e in val_report.errors],
            "validation_warnings": [w.model_dump() for w in val_report.warnings],
            "workflow_gates": gate_status.model_dump(),
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{site_id}/capability-matrix", summary="Get capability matrix across milestones")
def get_site_capability_matrix(site_id: str = Path(..., description="Site identifier")) -> Dict[str, Any]:
    """Return milestone capability matrix for dashboard display."""
    try:
        site_cfg = load_site(site_id)
        gate_status = evaluate_workflow_gates(site_cfg)

        is_bhavani = (site_id.lower() == "bhavanisagar")

        matrix = {
            "Terrain": "READY" if gate_status.gate_b_terrain.value == "READY" else gate_status.gate_b_terrain.value,
            "Hydrology": "READY" if gate_status.gate_c_hydrology.value == "READY" else gate_status.gate_c_hydrology.value,
            "Engineering": "READY" if gate_status.gate_d_engineering.value == "READY" else gate_status.gate_d_engineering.value,
            "Breach": "READY" if gate_status.gate_e_breach.value == "READY" else gate_status.gate_e_breach.value,
            "Hydrograph": "READY" if gate_status.gate_e_breach.value == "READY" else "BLOCKED",
            "D-Flow Production": "READY" if is_bhavani else "NOT_RUN",
            "SPH Production": "READY" if is_bhavani else "NOT_RUN",
            "HADR Consequence": "READY" if is_bhavani else "NOT_RUN",
            "Earth Observation": "READY" if is_bhavani else "PARTIAL",
        }

        return {
            "site_id": site_id,
            "display_name": site_cfg.display_name,
            "has_production_simulation": is_bhavani,
            "capability_matrix": matrix,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
