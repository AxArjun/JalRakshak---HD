# JalRakshak-HD: Cross-Solver Physics & Hydrodynamic Formulation Comparison (Milestone M7)

**Project:** JalRakshak-HD (SIH PS 26161)  
**Study Site:** Bhavanisagar Dam / Lower Bhavani Dam, Bhavani River, Tamil Nadu  
**Milestone:** M7 — Cross-Solver Near-Field Comparison and Hybrid Coupling Design  
**Comparison Classification:** `CROSS_SOLVER_CONSISTENCY_ANALYSIS`  
**Forcing Classification:** `NON_EQUIVALENT_FORCING_COMPARISON`  

---

## 1. Executive Summary

Milestone M7 establishes a rigorous cross-solver consistency analysis between two distinct numerical hydrodynamic models deployed for Bhavanisagar Dam break simulation:
1. **D-Flow FM (Milestone M5):** A 2D depth-averaged finite-volume shallow-water equation (SWE) solver operating across an 818.37 km² domain over 51.73 km of river reach.
2. **DualSPHysics (Milestone M6):** A Lagrangian Smoothed Particle Hydrodynamics (SPH) solver operating across the immediate 0–1500 m near-field reach.

**Fundamental Scientific Principle:**  
DualSPHysics does **NOT** validate D-Flow FM, and D-Flow FM does **NOT** validate DualSPHysics. Differences between the two models represent **model spread** arising from fundamentally non-equivalent forcing histories, dimensionality, boundary conditions, and governing physics—**not solver error**. Neither model serves as observed ground truth.

---

## 2. Solver Formulations & Governing Equations

| Dimension / Feature | D-Flow FM (M5) | DualSPHysics v5.4 (M6) |
| :--- | :--- | :--- |
| **Solver Type** | Eulerian 2D Unstructured Finite-Volume | Lagrangian Particle-Based Navier-Stokes (SPH) |
| **Governing Equations** | 2D Shallow Water Equations (SWE) / Depth-Averaged Reynolds-Averaged Navier-Stokes | Navier-Stokes equations with weakly compressible SPH formulation (Tait EOS) |
| **Spatial Discretization** | 82,309 polygonal/quadrilateral faces (~100 m nominal cell width) | 10,982 discrete particles (dp = 1.0 m spacing, 6,800 fluid + 4,182 boundary) |
| **Vertical Dimension** | Depth-averaged ($z$-independent velocity profile, hydrostatic pressure assumption) | Fully resolved vertical coordinate ($x$-$z$ plane), non-hydrostatic, full dynamic pressure |
| **Lateral Dimension** | Fully active 2D lateral floodplain spreading across valley floor | Unit-width ($1.0$ m thickness, zero lateral spreading, periodic/slip sidewalls) |
| **Free Surface Representation** | Single-valued elevation field $\eta(x,y,t)$ defined per cell | Lagrangian particle free-surface; breaks, plunges, splashes, and air entrainment resolved |
| **Bed Resistance Formulation** | Manning roughness coefficient ($n = 0.035$ s/m$^{1/3}$) applied uniformly | Artificial viscosity ($\alpha = 0.05$) + boundary repulsive/DBC particle interaction |
| **Terrain Representation** | SRTM 30 m DEM averaged onto 100 m cell faces | High-resolution 1D longitudinal terrain profile extracted from SRTM at 10 m intervals |

---

## 3. Forcing Incompatibilities & Initial Conditions

### 3.1 D-Flow FM Forcing Framework
- **Forcing Type:** Continuous time-varying inflow hydrograph (`BHV_BASE` screening scenario).
- **Time Evolution:** Inflow discharge starts at $Q(0) \approx 0$ m³/s, gradually rises over $t_{\text{rise}} = 14,095.59$ s (3.92 hours) to $Q_{\text{peak}} = 18,742.38$ m³/s, and recedes over a total duration of 83,287.18 s (23.14 hours).
- **Domain Initial State:** Initially dry bed (`DRY_START_SCREENING`), with cells progressively wetted as discharge ramps up.
- **Physical Consequence:** Flood inundation at early timestamps ($t < 4,000$ s) represents small introductory discharges ($Q < 2,000$ m³/s) filling the low-lying river channel and depressions. Maximum depth occurs near the hydrograph peak ($t \approx 15,000$ s).

### 3.2 DualSPHysics Forcing Framework
- **Forcing Type:** Instantaneous release of a static fluid block initialized at the peak-outflow hydraulic state (`PEAK_STATE_INITIALIZED_RELEASE_SCREENING_CASE`).
- **Initial Reservoir State:** Upstream fluid column of height $H_{\text{rel}} = 17.526$ m (FRL 280.42 m MSL, reservoir length 400 m, unit width 1.0 m), representing a stored unit volume of $7,010.4$ m³/m.
- **Release Dynamics:** At $t = 0$ s, the confining dam boundary is instantaneously removed, releasing the fluid block under gravity ($g = 9.80665$ m/s²).
- **Physical Consequence:** The fluid undergoes an immediate violent dam-break collapse, forming a plunging toe jet that impacts the channel floor within 5–12 seconds at velocities exceeding 23–25 m/s. The finite fluid block attenuates rapidly as it spreads over the 1500 m reach.

---

## 4. Hydraulic Regime & Physical Differences

### 4.1 Froude Number & Energy State
Synchronized Froude number diagnostics ($Fr = U / \sqrt{g \cdot h}$) evaluated at the timestamp of peak velocity demonstrate diametrically opposed hydrodynamic regimes:

- **DualSPHysics (Supercritical Jetting):**
  - $G_{\text{100m}}$: $Fr = 3.173$ ($U = 23.16$ m/s, $h = 5.43$ m)
  - $G_{\text{250m}}$: $Fr = 3.021$ ($U = 24.73$ m/s, $h = 6.83$ m)
  - $G_{\text{500m}}$: $Fr = 2.219$ ($U = 15.95$ m/s, $h = 5.27$ m)
  - $G_{\text{1000m}}$: $Fr = 2.511$ ($U = 14.00$ m/s, $h = 3.17$ m)
  - *Mechanism:* Non-hydrostatic vertical acceleration down the steep breach face converts potential energy directly into a thin, unconfined, hyper-turbulent supercritical shooting jet.

- **D-Flow FM (Subcritical Floodplain Routing):**
  - $G_{\text{100m}}$: $Fr = 0.510$ ($U = 2.47$ m/s, $h = 2.38$ m)
  - $G_{\text{250m}}$: $Fr = 0.723$ ($U = 2.51$ m/s, $h = 1.22$ m)
  - $G_{\text{500m}}$: $Fr = 0.631$ ($U = 2.65$ m/s, $h = 1.79$ m)
  - $G_{\text{1000m}}$: $Fr = 0.492$ ($U = 4.32$ m/s, $h = 7.89$ m)
  - $G_{\text{1500m}}$: $Fr = 0.510$ ($U = 4.45$ m/s, $h = 7.78$ m)
  - *Mechanism:* Hydrostatic SWE depth-averages velocity across 100 m wide cells; lateral spreading over the flat valley floor dissipates kinetic energy into broad inundation storage, maintaining subcritical flow throughout.

### 4.2 Depth Profiles & Spatial Attenuation
- At $G_{\text{100m}}$, both models exhibit similar initial flow depths ($h_{\text{SPH}} = 8.06$ m vs. $h_{\text{DFlow}} = 6.22$ m, ratio 1.30).
- At $G_{\text{250m}}$ (toe plunge basin), both models record localized depth amplification ($h_{\text{SPH}} = 12.00$ m, $h_{\text{DFlow}} = 14.64$ m, ratio 0.82) due to the sharp topographical drop below the dam foundation.
- Downstream of 500 m, the models diverge structurally:
  - DualSPHysics depth attenuates to $5.55$ m (500 m) and $5.21$ m (1000 m) because the finite fluid mass is spread across the longitudinal corridor without upstream replenishment.
  - D-Flow FM depth rises to $11.04$ m (500 m) and $13.57$ m (1000 m) because the continuous multi-hour hydrograph steadily fills the entire Bhavani valley floor.

### 4.3 Velocity Attenuation vs. Downstream Acceleration (`DIVERGENT_TREND`)
The two models exhibit fundamentally divergent velocity trends along the downstream chainage:
- **DualSPHysics:** Displays strong velocity attenuation after the plunging jet zone ($24.73\text{ m/s at 250 m} \rightarrow 15.95\text{ m/s at 500 m} \rightarrow 14.00\text{ m/s at 1000 m}$). The finite fluid volume decelerates as bed friction dissipates kinetic energy. By $t = 600$ s, the SPH front reached $1,280.41$ m and station $G_{\text{1500m}}$ was `NOT_REACHED_WITHIN_600_S` (it was slowing substantially but was still advancing).
- **D-Flow FM:** Depth-averaged peak velocity steadily increases downstream ($2.47\text{ m/s at 100 m} \rightarrow 2.51\text{ m/s} \rightarrow 2.65\text{ m/s} \rightarrow 4.32\text{ m/s at 1000 m} \rightarrow 4.45\text{ m/s at 1500 m}$) as the large-volume discharge is conveyed through the incised river channel.

Consequently:
$$\text{velocity\_trend} = \mathbf{DIVERGENT\_TREND}$$
*Scientific Justification:* This directional divergence reflects the non-equivalent forcing (finite block vs. continuous hydrograph) and dimensional formulations (2D unit-width vs. depth-averaged SWE), and must **not** be interpreted as numerical solver error.

---

## 5. Methodological Strengths & Limitations

Neither solver is universally superior; each solves a different hydrodynamic domain:

1. **DualSPHysics (M6):**
   - *Superior for:* Hydrodynamic impact pressures on toe structures, plunging jet trajectories, free-surface aeration, non-hydrostatic vertical acceleration, high-energy near-field velocities relevant to potential erosion/scour assessment, and near-field turbulence dissipation within 0–500 m.
   - *Inadequate for:* Catchment-scale flood routing, multi-hour inundation extents, lateral valley floodplain storage, or long-term hydrograph attenuation. Does **not** simulate sediment transport or morphological scour.

2. **D-Flow FM (M5):**
   - *Superior for:* Large-scale 2D inundation mapping, regional flood travel times, village/infrastructure evacuation timing, downstream arrival schedules, and mass-conservative multi-day hydrograph routing across 50+ km.
   - *Inadequate for:* Resolving localized vertical jet plunge dynamics, wave impact forces on the dam toe, or sub-grid non-hydrostatic jets narrower than the 100 m mesh scale.

---

## 6. Conclusion

The cross-solver comparison confirms that the two models produce distinct hydrodynamic behaviors necessitated by their governing equations. Depth trends show partial consistency near the toe depression, whereas downstream velocity trends are divergent (`DIVERGENT_TREND`). Combining them in a **loosely coupled hybrid hierarchy** (`configs/hybrid_solver.yaml`) leverages SPH for near-field high-gradient diagnostics (design handoff candidate at 500 m) and D-Flow FM for regional floodplain mapping, while keeping numerical coupling at `DESIGN_ONLY` (`overall_coupling_readiness = NOT_READY`).
