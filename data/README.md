# JalRakshak-HD Data Directory Structure

This directory houses all raw, conditioned, geospatial, hydrodynamic, and particle simulation data.

## Directory Responsibilities

| Directory | Purpose & Contents |
| :--- | :--- |
| `data/raw/` | Unmodified incoming data from external providers (raw DEM tiles, satellite imagery, raw boundary files). Never edit in place. |
| `data/processed/` | Standardized, re-projected, clipped, and cleaned vector/raster layers ready for ingestion by processing pipelines. |
| `data/terrain/` | Hydrologically conditioned Digital Elevation Models (DEMs), bathymetry rasters, Manning roughness maps, and slope grids. |
| `data/hydrology/` | Inflow/outflow hydrographs, discharge time-series, stage-discharge rating curves, and reservoir water level curves. |
| `data/gee/` | Google Earth Engine exports, cloud masks, satellite surface water extents (Sentinel-1 SAR / Sentinel-2 / Landsat). |
| `data/dflowfm/` | D-Flow Flexible Mesh input files (unstructured mesh grids `.nc`, boundary definitions `.ext`, parameters `.mdu`). |
| `data/sph/` | DualSPHysics input definitions, XML case files (`Case_Def.xml`), STL geometry models for dam/spillways, particle configs. |
| `data/hadr/` | Humanitarian Assistance and Disaster Relief layers (critical infrastructure, evacuation routes, shelter polygons, population density). |
| `data/observations/` | Ground-truth measurements, gauge sensor logs, high-water marks, satellite-derived flood inundation validation footprints. |

## Scientific Integrity Policy
All data placed here must adhere to the data provenance standards defined in [`docs/data_provenance.md`](file:///C:/JalRakshak-HD/docs/data_provenance.md). Fabricated scientific inputs are strictly forbidden.
