# JalRakshak-HD: SIH Jury Comprehensive Q&A Bank

**Project Classification:** Research Screening & GIS Decision-Support Prototype  
**Primary Demonstration Site:** Bhavanisagar Dam / Lower Bhavani River Basin, Tamil Nadu  
**Generalization Proof Site:** Hirakud Dam / Mahanadi Basin, Odisha  
**Core Solvers:** D-Flow Flexible Mesh (Delft3D FM 2D Hydrodynamics) + DualSPHysics (3D Smoothed Particle Hydrodynamics)

---

## Section 1: Physics & Hydrodynamics Solvers

### Q1: Why use D-Flow Flexible Mesh (Delft3D FM) instead of standard 1D/2D HEC-RAS?
**Answer:**
1. **Unstructured Mesh Flexibility:** D-Flow FM operates on flexible, unstructured staggered grids (quadrilateral and triangular cells), allowing dynamic refinement along complex river thalwegs, embankment boundaries, and floodplains without the interpolation artifacts typical of uniform Cartesian grids.
2. **Robust Wetting-Drying & Shock-Capturing:** It implements finite-volume formulations of the 2D Shallow Water Equations (SWE) with robust Riemann solvers capable of handling abrupt dam-break wave discontinuities and high Froude number transitions ($Fr > 1.0$) across complex terrain.
3. **Open Standards & Proven Coastal/Riverine Hydrodynamics:** Developed by Deltares, D-Flow FM is globally validated for large-scale inundation, estuarine dynamics, and hydraulic structure failures.

### Q2: Why DualSPHysics? Why not run the entire 30-hour flood domain in 3D SPH?
**Answer:**
1. **Governing Physics Domain:** Mesh-free Smoothed Particle Hydrodynamics (SPH) solves the full Navier-Stokes equations with free-surface Lagrangian particle tracking. This is essential for capturing 3D overturning jets, dam structure impact pressures, and near-field turbulence in the first few hundred meters ($0$ to $1.3\text{ km}$) and initial minutes ($0$ to $600\text{ s}$).
2. **Computational Tractability:** SPH requires resolving millions of fluid particles with microscopic timesteps ($dt \sim 10^{-4}\text{ s}$) dictated by the CFL condition and speed of sound. Simulating an $818.37\text{ km}^2$, 30-hour domain ($108,000\text{ s}$) in 3D SPH would require billions of particles and months of HPC compute.
3. **Multi-Scale Separation:** JalRakshak-HD applies DualSPHysics specifically to the near-field dam structure ($10,982$ particles, $600\text{ s}$) for structural splash/impact assessment, and D-Flow FM for the far-field 2D riverine propagation ($818.37\text{ km}^2$, $108,000\text{ s}$).

### Q3: Are DualSPHysics and D-Flow FM directly dynamically coupled?
**Answer:**
**No.** We maintain strict scientific honesty: **DualSPHysics and D-Flow FM are decoupled multi-scale models.**
- They are driven by identical breach geometry ($B_{\text{avg}} = 219.28\text{ m}$, $H_{\text{dam}} = 40.0\text{ m}$) and hydraulic parameters.
- Near-field hydrodynamics ($0$–$600\text{ s}$) are analyzed independently in 3D SPH, while the reach-scale inundation ($0$–$30\text{ hr}$) is computed in 2D D-Flow FM.
- Direct boundary-flux two-way coupling is an active research area and is not implemented in this prototype.

---

## Section 2: Dam Engineering & Breach Modeling

### Q4: Why Bhavanisagar Dam?
**Answer:**
1. **Compound Dam Geometry:** Bhavanisagar is one of the world's longest earthen dams ($\approx 8.8\text{ km}$ composite earthen embankment with a central masonry spillway). Earthen composite dams present the highest risk of piping and overtopping breach.
2. **Downstream Exposure:** The Lower Bhavani basin houses dense agricultural settlements, major transportation corridors (SH-15, NH-948), 20 mapped bridge crossings, and municipal centers (Sathyamangalam, Gobichettipalayam).
3. **Data Availability:** Authentic geometry, reservoir storage curves, and historical flood records (CWC, NRLD, TNSDMA) provide verifiable boundary constraints.

### Q5: How was the breach geometry and hydrograph calculated?
**Answer:**
- **Breach Formulation:** Calculated using Froehlich (2008) empirical breach equations for earthen dams:
  $$B_{\text{avg}} = 0.27 \cdot K_0 \cdot V_w^{0.32} \cdot h_b^{0.04}$$
  $$t_f = 63.2 \cdot \sqrt{\frac{V_w}{g \cdot h_b^2}}$$
- **Parameters:**
  - Reservoir Volume at FRL ($V_w$): $780.50\text{ MCM}$ ($780.50 \times 10^6\text{ m}^3$)
  - Breach Height ($h_b$): $32.0\text{ m}$ (effective earthen section over foundation)
  - Failure Mode Factor ($K_0$): $1.3$ (overtopping mode)
- **Computed Breach Dimensions:**
  - Average Breach Width ($B_{\text{avg}}$): $219.28\text{ m}$
  - Formation Time ($t_f$): $14,095.59\text{ s}$ ($\approx 3.915\text{ hr}$)
  - Peak Breach Discharge ($Q_{\text{peak}}$): $18,742.38\text{ m}^3/\text{s}$

### Q6: What if the Froehlich empirical breach equation has high uncertainty?
**Answer:**
Froehlich (2008) is an empirical regression based on 74 historical dam failures with an inherent uncertainty of $\pm 25$–$35\%$. JalRakshak-HD treats breach hydrographs as **screening scenarios** rather than deterministic prophecies. Our multi-site architecture allows parameter overrides (Von Thun & Gillette, MacDonald & Langridge-Monopolis, or parametric CWC hydrographs) via simple YAML/JSON site configurations.

---

## Section 3: Data Provenance & Real GIS

### Q7: Is this real data or synthetic/demo data?
**Answer:**
**Every layer in JalRakshak-HD is derived from authentic, verified geospatial and hydrologic datasets:**
- **Dam Engineering:** Central Water Commission (CWC) National Register of Large Dams (NRLD 2023) and Tamil Nadu Water Resources Department (WRD).
- **Terrain:** NASA SRTM 1 Arc-Second ($30\text{ m}$) Global DEM conditioned with HydroSHEDS river burn-in.
- **Surface Water & Drainage:** JRC Global Surface Water (GSW) + HydroSHEDS flow accumulation.
- **Population:** WorldPop 2020 ($100\text{ m}$ UN-adjusted) and Copernicus GHSL ($100\text{ m}$ built-up population density).
- **Settlements, Roads, Bridges & Facilities:** OpenStreetMap (OSM) verified via Overpass API and Google Open Buildings v3.
- **Earth Observation:** European Space Agency (ESA) Copernicus Sentinel-1 Synthetic Aperture Radar (SAR) Ground Range Detected (GRD) imagery.

### Q8: Why are bridge crossings and facilities termed "mapped/screened" instead of "surveyed"?
**Answer:**
Scientific precision. The bridge crossings ($20$ locations) and critical facilities ($13$ locations) were extracted from OpenStreetMap and high-resolution satellite imagery through automated spatial intersecting, not through physical on-site structural bathymetric surveys.

---

## Section 4: HADR Consequence Screening & Population Discrepancy

### Q9: Why do WorldPop and GHSL population exposure numbers differ ($42,428$ vs $84,501$)?
**Answer:**
- **WorldPop ($42,428$ exposed):** Top-down dasymetric disaggregation of census data weighted by land cover, nighttime lights, and slope. It estimates ambient residential population.
- **GHSL ($84,501$ exposed):** Derived from European Commission Global Human Settlement Layer built-up surface area ($100\text{ m}$). It emphasizes urban infrastructure footprint and daytime economic activity density.
- **Why we present both without averaging:** Averaging two fundamentally distinct statistical models destroys error bounds and creates false precision. Presenting the range ($42.4\text{k}$–$84.5\text{k}$) allows disaster commanders to plan resources for lower-bound residential night scenarios and upper-bound daytime activity peaks.

### Q10: Why are H5/H6 hazard zones not labeled as "destroyed"?
**Answer:**
JalRakshak-HD adheres to international flood hazard standards (USACE / Australian ARR / CWC):
- Hazard zones ($H_1$ to $H_6$) classify hydrodynamic hazard rating ($v \cdot d + \text{debris factor}$ or depth-velocity thresholds).
- $H_5$ and $H_6$ indicate **extreme structural hazard to human life and high potential for structural failure**, not guaranteed total collapse of all engineered reinforced concrete structures.

---

## Section 5: Earth Observation & Satellite Monitoring

### Q11: What does Sentinel-1 SAR detect? Can it predict a dam break?
**Answer:**
1. **What it detects:** Sentinel-1 Synthetic Aperture Radar (SAR) emits C-band microwaves ($5.405\text{ GHz}$) that undergo specular reflection on smooth water surfaces, appearing dark in backscatter ($<-16\text{ dB}$). It detects actual inundation through clouds, rain, and nighttime.
2. **Predictive Capability:** **SAR cannot predict a dam break before it happens.** It serves as:
   - Near-Real-Time (NRT) post-event inundation validation.
   - Historical baseline benchmarking (e.g., Nov 2021 Lower Bhavani flood event).
   - Validation against simulated flood footprints.

---

## Section 6: Portability & Multi-Site Architecture

### Q12: How does JalRakshak-HD generalize to "Any-Dam / Any-River"?
**Answer:**
JalRakshak-HD decouples code from site data using a **Configuration-Driven Site Architecture**:
- Each dam site is defined by a standardized `site_config.yaml` specifying geographic bounds, CRS (UTM projection), dam engineering parameters, terrain DEM, river geometry, and response sectors.
- All geospatial extractors, mesh generators, hydrograph engines, and HADR processors read configurations dynamically.
- Demonstrated on **Hirakud Dam (Odisha)**: Automated ingestion of NRLD data, SRTM DEM, OSM layers, and breach screening hydrograph without modifying backend source code.

### Q13: Did you run production D-Flow FM for Hirakud?
**Answer:**
**No.** We explicitly label Hirakud as `PORTABILITY_VALIDATED / INPUT_READY_NOT_EXECUTED`. All boundary vectors, terrain models, breach hydrographs, and exposure rasters are validated and ready for solver execution, but no unverified hydrodynamic simulation was run or fabricated.

---

## Section 7: Operational & SIH Jury Constraints

### Q14: How does the system function without an active internet connection?
**Answer:**
- All scientific simulation layers (D-Flow animation frames, SPH trajectories, HADR polygons, exposure grids, bridge points, DEM hillshades) are cached locally in optimized formats (`.png`, `.geojson`, `.json`).
- If internet connectivity is lost, the Leaflet GIS dashboard automatically falls back to the **local NASA SRTM 30m hillshade raster** with full scientific playback, query tools, and vector layers intact.

### Q15: What are the main limitations of this prototype?
**Answer:**
1. **Hypothetical Breach Scenario:** Assumes overtopping failure at FRL; real events depend on structural geotechnical factors.
2. **DEM Resolution:** $30\text{ m}$ SRTM lacks fine sub-grid river bathymetry and drainage culverts.
3. **Manning Roughness:** Spatially uniform calibrated roughness ($n = 0.035$) rather than dynamic land-cover distributed Manning coefficients.
4. **Satellite Latency:** Sentinel-1 has a 6–12 day orbital revisit cycle; it is not a 1-minute real-time camera.
5. **Decoupled Solvers:** SPH and D-Flow are multi-scale decoupled, not dynamically boundary-flux coupled.
