# Milestone M11: Any-Dam / Any-River Generalization & Multi-Site Portability

**Project:** JalRakshak-HD  
**Milestone:** M11 — Architecture Generalization, Config-Driven Onboarding, Second-Site Portability Proof & Validation-Gate Design  
**Date:** September 2026  
**Status:** COMPLETED & VALIDATED  

---

## Executive Summary

Milestone M11 transitions **JalRakshak-HD** from a Bhavanisagar-specific prototype into a **CONFIG-DRIVEN MULTI-SITE DAM-BREAK MODELING PLATFORM**. The core hydrodynamic, numerical, and consequence pipelines now operate against generalized site configurations and schemas without any hardcoded coordinates, local EPSG codes, or site-specific identifiers in production logic.

To rigorously demonstrate architecture portability without synthetic data, a second real Indian dam—**Hirakud Dam** on the Mahanadi River in Sambalpur District, Odisha—was fully onboarded and validated through Gates A through E.

---

## Architecture Generalization Overview

```
                      JalRakshak-HD Multi-Site Engine
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
     Site Registry                                     Workflow Gate Engine
  (configs/sites.yaml)                              (Gates A–H Readiness)
           │                                                   │
   ┌───────┴───────┐                                           │
   ▼               ▼                                           ▼
Bhavanisagar    Hirakud                              Gate A: Location (CRS)
   (TN)          (OD)                                Gate B: Terrain (SRTM 30m)
   UTM 43N      UTM 44N                              Gate C: Hydrology (River)
   EPSG:32643   EPSG:32644                           Gate D: Engineering (NRLD)
                                                     Gate E: Screening Breach
                                                     Gate F: Solver Inputs (MDU/BC)
                                                     Gate G: HADR Consequence
                                                     Gate H: Earth Observation
```

---

## What Is Fully Generalized

1. **Site Package Architecture (`sites/<site_id>/`):**
   - Standardized YAML schemas: `site.yaml`, `dam.yaml`, `hydrology.yaml`, `breach.yaml`, `model.yaml`, `monitoring.yaml`, `source_manifest.json`.
2. **Automatic Spatial Coordinate Reference System (CRS):**
   - Dynamically calculates the appropriate UTM zone and EPSG code (`EPSG:32601`–`EPSG:32660` / `EPSG:32701`–`EPSG:32760`) from decimal coordinates.
   - Tested: Bhavanisagar $\rightarrow$ `EPSG:32643` (UTM 43N); Hirakud $\rightarrow$ `EPSG:32644` (UTM 44N).
3. **Workflow Readiness Gates (A through H):**
   - Evaluates data completeness and blocks execution of downstream solvers until prerequisites are satisfied.
   - Zero false positive passes; unexecuted solver stages are strictly classified as `NOT_RUN` or `BLOCKED`.
4. **Empirical Breach Parameter & Hydrograph Services:**
   - Universal implementation of Froehlich (2008, 1995) and MacDonald et al. parameterized against Pydantic models.
   - Preserves exact Bhavanisagar regression: $B_{avg} = 219.28\text{ m}$, $t_f = 14095.59\text{ s}$, $Q_{peak} = 18742.38\text{ m}^3\text{/s}$, Volume = $780.5\text{ MCM}$.
5. **D-Flow FM & SPH Input Preparation:**
   - Automated generation of master `.mdu` configuration, boundary `.bc` time-series, and SPH geometry configurations.
6. **Multi-Site Dashboard & API:**
   - Real-time site switching dropdown in dashboard header.
   - Displays honest preflight capability matrix and metadata for secondary sites without substituting baseline results.

---

## Second Real Site Portability Proof: Hirakud Dam (Odisha)

| Parameter | Authoritative Value | Source / Classification |
| :--- | :--- | :--- |
| **Dam Name** | Hirakud Dam | CWC NRLD 2023 (PIC: `OD08MH0001`) |
| **River / Basin** | Mahanadi River / Mahanadi Basin | Odisha DoWR / CWC Basin Records |
| **State / District** | Odisha / Sambalpur District | Government of Odisha |
| **Dam Coordinates** | Lat: `21.5700° N`, Lon: `83.8694° E` | CWC & Survey of India |
| **Project CRS** | `EPSG:32644` (WGS 84 / UTM Zone 44N) | Automatically derived |
| **Dam Height** | `60.96 m` (200 ft above lowest foundation) | Authoritative Verified (NRLD) |
| **Crest Length** | `4,800 m` (Main Dam) / `25,800 m` (Composite) | Authoritative Verified (DoWR) |
| **Crest Elevation** | `195.68 m MSL` (642.0 ft MSL) | Authoritative Verified (DoWR) |
| **Full Reservoir Level (FRL)** | `192.024 m MSL` (630.0 ft MSL) | Authoritative Verified (CWC Bulletins) |
| **Gross Storage Capacity** | `8,136.0 MCM` (8.136 km³) | Authoritative Verified (NRLD) |
| **Active Live Storage** | `5,818.0 MCM` (5.818 km³) | Authoritative Verified (DoWR) |
| **Spillway Capacity** | `42,475.0 m³/s` (1,500,000 cfs) | Authoritative Verified (Rating Curves) |
| **Spillway Gates** | 98 gates (64 undersluices + 34 crest radial) | Authoritative Verified (DoWR) |
| **Terrain DEM** | NASA SRTM GL1 30 m GeoTIFF ($1100 \times 800$) | Authoritative Verified (NASA/USGS) |
| **Screening Breach ($B_{avg}$)** | `541.34 m` | Model Derived (Froehlich 2008) |
| **Screening Peak ($Q_{peak}$)** | `56,420.8 m³/s` | Model Derived (Froehlich 1995) |

---

## Natural Blockage Extensibility

To address the broader problem statement context involving natural blockages (landslide dams, glacial lake outburst blockages, and temporary debris dams), an explicit architectural hook `ImpoundmentType` was implemented:

```python
class ImpoundmentType(str, Enum):
    ENGINEERED_DAM = "ENGINEERED_DAM"                              # [IMPLEMENTED]
    LANDSLIDE_DAM = "LANDSLIDE_DAM"                                # [ARCHITECTURE_SUPPORTED_BUT_PHYSICS_NOT_IMPLEMENTED]
    GLACIAL_BLOCKAGE = "GLACIAL_BLOCKAGE"                          # [ARCHITECTURE_SUPPORTED_BUT_PHYSICS_NOT_IMPLEMENTED]
    TEMPORARY_DEBRIS_BLOCKAGE = "TEMPORARY_DEBRIS_BLOCKAGE"        # [ARCHITECTURE_SUPPORTED_BUT_PHYSICS_NOT_IMPLEMENTED]
    OTHER = "OTHER"
```

*Scientific Note:* Engineered dam breach equations (e.g. Froehlich 2008) are calibrated on compacted fill and masonry structures; they are NOT physically valid for uncompacted landslide scree or moraine dams without distinct geotechnical erosion parameters. The system explicitly warns users when non-engineered impoundment types are configured.

---

## Scientific Limitations of Generalized Onboarding

While the software architecture is fully generalized, high-fidelity dam break and hydrodynamic modeling remains fundamentally dependent on site-specific physical calibration:

1. **Bathymetry vs. Satellite Topography:** Spaceborne DEMs (NASA SRTM 30 m) represent dry-season water surfaces and canopy tops, lacking sub-water riverbed bathymetry.
2. **Geotechnical Erodibility Parameters:** Breach formation rates ($t_f$) and side slopes ($z$) depend heavily on soil core compaction and riprap sizing.
3. **Manning Roughness Spatial Heterogeneity:** Surface roughness varies with local floodplain vegetation, crops, and urban building densities.
4. **Hydrometric Stage-Discharge Calibration:** Accurate downstream flood wave arrival requires calibration against real stream gauges during historic flood pulses.
