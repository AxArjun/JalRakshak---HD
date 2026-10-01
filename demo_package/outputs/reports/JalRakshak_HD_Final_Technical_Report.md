# JalRakshak-HD: Comprehensive Final Technical Report

**Project Title:** JalRakshak-HD: Configuration-Driven Multi-Site Dam-Break Screening & Decision-Support Platform  
**Classification:** Research Screening & Decision-Support Prototype  
**Primary Demonstration Site:** Bhavanisagar Dam / Lower Bhavani River Basin, Tamil Nadu  
**Portability Proof Site:** Hirakud Dam / Mahanadi River Basin, Odisha  
**Release Version:** JalRakshak-HD v1.0-SIH  

---

## 1. Executive Summary
JalRakshak-HD is an end-to-end computational framework and GIS decision-support platform designed to simulate dam failure hydrodynamics, assess downstream humanitarian and infrastructural exposure, and provide near-real-time satellite validation. The system couples 3D Smoothed Particle Hydrodynamics (DualSPHysics) for near-field structure impacts with 2D Flexible Mesh hydrodynamics (D-Flow FM) for reach-scale flood propagation. The platform operates on a configuration-driven architecture, enabling rapid onboarding of distinct dam sites.

---

## 2. Problem Statement & Objectives
Dam failures and sudden outburst floods present catastrophic risks to downstream populations, critical lifelines, and economic infrastructure. Traditional screening models either oversimplify physics (1D steady-state approximations) or lack spatial consequence context. JalRakshak-HD addresses this challenge by providing:
1. Rigorous hydrodynamic wave propagation across complex terrain.
2. Near-field 3D particle impact screening.
3. Multi-source population and infrastructure exposure assessment.
4. Sentinel-1 SAR satellite benchmarking.
5. High-resilience web GIS command centre with zero-dependency offline fallback.

---

## 3. System Architecture & Methodology
The platform comprises six integrated tiers:
- **Geospatial & Hydrologic Ingestion:** NASA SRTM 30m DEM, HydroSHEDS streamlines, JRC Global Surface Water, CWC NRLD dam registry, OpenStreetMap, and ESA Copernicus Sentinel-1.
- **Site Configuration Engine:** Parameterized YAML schemas for geospatial boundaries, projections, and dam engineering properties.
- **Breach & Hydrograph Engines:** Froehlich (2008) empirical dam-break equations and parametric hydrograph generation.
- **Multi-Scale Hydrodynamic Solvers:** D-Flow FM 2D (Eulerian shallow water) and DualSPHysics 3D (Lagrangian SPH).
- **Consequence Screening (HADR):** Sectoral exposure overlays with WorldPop, GHSL, Open Buildings, and OSM road/bridge infrastructure.
- **GIS Command Centre:** FastAPI async backend paired with a React 18 + Leaflet mapping frontend.

---

## 4. Primary Study Area: Bhavanisagar Dam
- **Location:** Erode District, Tamil Nadu, India ($11.4705^\circ\text{ N}, 77.1465^\circ\text{ E}$).
- **Dam Characteristics:** Composite earthen embankment with central masonry spillway; total crest length $\approx 8.8\text{ km}$; maximum structural height $40.0\text{ m}$; Full Reservoir Level (FRL) $280.20\text{ m}$.
- **Active Storage ($V_w$):** $780.50\text{ MCM}$ ($780.50 \times 10^6\text{ m}^3$).
- **Downstream River:** Lower Bhavani River extending through Sathyamangalam, Gobichettipalayam, and Bhavani to the Kaveri confluence ($818.37\text{ km}^2$ study domain).

---

## 5. Breach Parameterization & Hydrograph
- **Breach Formulation:** Froehlich (2008) overtopping failure mode ($K_0 = 1.3$, $h_b = 32.0\text{ m}$ effective breach depth).
- **Average Breach Width ($B_{\text{avg}}$):** $219.28\text{ m}$
- **Breach Formation Time ($t_f$):** $14,095.59\text{ s}$ ($\approx 3.915\text{ hr}$)
- **Peak Outflow Discharge ($Q_{\text{peak}}$):** $18,742.38\text{ m}^3/\text{s}$
- **Hydrograph Volume:** $780.50\text{ MCM}$ (Conservation of mass confirmed).

---

## 6. Far-Field 2D Hydrodynamics (D-Flow FM)
- **Model Domain:** $818.37\text{ km}^2$
- **Simulation Duration:** $108,000\text{ s}$ ($30\text{ hours}$), discretized into $181$ output frames at $600\text{ s}$ intervals.
- **Maximum Inundated Footprint:** $101.29\text{ km}^2$
- **Peak Flow Depth:** $22.02\text{ m}$ (P95 Depth: $12.72\text{ m}$)
- **Peak Flow Velocity:** $11.79\text{ m/s}$ (P95 Velocity: $4.27\text{ m/s}$)
- **Mass Balance Audit:** Inflow $780.50\text{ MCM}$, Outflow $618.85\text{ MCM}$, Final Domain Storage $161.69\text{ MCM}$, Residual $0.041\text{ MCM}$ ($0.0052\%$ relative residual error, `MASS_CONSERVATION_PASS`).

---

## 7. Near-Field 3D Hydrodynamics (DualSPHysics)
- **Fluid Particle Count:** $10,982$ particles
- **Physical Duration:** $600\text{ s}$ ($10\text{ minutes}$)
- **Maximum Near-Field Depth:** $17.11\text{ m}$
- **Maximum Near-Field Velocity:** $34.78\text{ m/s}$
- **Leading Wave Front Position:** $1,280.41\text{ m}$ downstream at $t = 600\text{ s}$.

---

## 8. Humanitarian Assistance & Disaster Relief (HADR) Screening
- **Exposed Population (WorldPop 2020):** $42,428$ persons (residential baseline)
- **Exposed Population (GHSL 2023):** $84,501$ persons (daytime / built-up activity baseline)
- **Building Exposure:** $25,652$ mapped structures ($22,472$ in extreme $H_5/H_6$ hazard zones)
- **Transportation Impact:** $243.82\text{ km}$ inundated roads; $20$ mapped bridge crossings screened
- **Critical Facilities:** $13$ mapped emergency/medical facilities within inundation zone
- **Response Zoning:** Segmented into 9 non-overlapping municipal sectors.

---

## 9. Earth Observation & Satellite Benchmarking
- **Sensor:** ESA Copernicus Sentinel-1 Synthetic Aperture Radar (SAR) C-band GRD.
- **Historical Benchmark Event:** November 2021 Lower Bhavani flood event.
- **Detected Inundation Extent:** $1.19\text{ km}^2$ newly inundated area extracted via backscatter thresholding ($\sigma_0 < -16\text{ dB}$).
- **Operational Mode:** Automated ingestion pipeline configured for NRT post-flood mapping.

---

## 10. Multi-Site Portability: Hirakud Dam Proof
- **Location:** Sambalpur District, Odisha ($21.5700^\circ\text{ N}, 83.8700^\circ\text{ E}$).
- **Storage Profile:** NRLD Live Storage $5,818\text{ MCM}$; Gross Storage $8,136\text{ MCM}$.
- **Screening Breach Discharge:** $Q_{\text{peak}} = 65,163.63\text{ m}^3/\text{s}$
- **Domain Extent:** $2,367.43\text{ km}^2$ along the Mahanadi River corridor.
- **Portability Status:** Complete GIS boundary extraction, DEM conditioning, and config validation completed. Solver execution marked honestly as `INPUT_READY_NOT_EXECUTED`.

---

## 11. Known Scientific Limitations
1. **Empirical Breach Formulation:** Uses Froehlich (2008) empirical regression with typical $\pm 25$–$35\%$ uncertainty bounds.
2. **DEM Resolution:** SRTM 30m terrain lacks micro-topography, drainage ditches, and sub-surface bridge culverts.
3. **Roughness Representation:** Spatially uniform calibrated Manning coefficient ($n = 0.035$).
4. **Solver Decoupling:** SPH near-field and D-Flow far-field are independently parameterized rather than dynamically flux-coupled.
5. **Satellite Latency:** Sentinel-1 revisit intervals ($6$–$12\text{ days}$) preclude real-time second-by-second tracking.

---

## 12. Conclusion & Operational Path
JalRakshak-HD provides a scientifically rigorous, transparently documented screening tool for emergency planners, disaster management authorities, and dam safety engineers. Future operational deployment pathways include bathymetric LiDAR integration, real-time telemetry ingestion, and GPU-accelerated 2D shallow water solvers.
