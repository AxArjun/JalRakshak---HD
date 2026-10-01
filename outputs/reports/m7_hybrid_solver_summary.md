# JalRakshak-HD: Cross-Solver Near-Field Comparison and Hybrid Coupling Design Report (Milestone M7)

**Project:** JalRakshak-HD (SIH PS 26161)  
**Study Site:** Bhavanisagar Dam / Lower Bhavani Dam, Bhavani River, Tamil Nadu  
**Milestone:** M7 — Cross-Solver Near-Field Comparison and Hybrid Coupling Design  
**Comparison Classification:** `CROSS_SOLVER_CONSISTENCY_ANALYSIS`  
**Forcing Classification:** `NON_EQUIVALENT_FORCING_COMPARISON`  
**Coupling Status:** `DESIGN_ONLY` (`direct_coupling_activated = false`)  

---

> [!IMPORTANT]
> **CRITICAL SCIENTIFIC PRINCIPLE:**  
> Cross-solver comparison is **NOT** model validation because neither solver serves as observed ground truth. DualSPHysics does **NOT** validate D-Flow FM, and D-Flow FM does **NOT** validate DualSPHysics. Differences between the models represent **cross-model spread** arising from fundamentally non-equivalent forcing histories, dimensionality, and governing physics—**not solver error**.

---

## 1. Purpose

The objective of Milestone M7 is to establish a rigorous, objective, and reproducible cross-solver consistency analysis between the two hydrodynamic engines developed in JalRakshak-HD:
1. **D-Flow FM (Milestone M5):** 2D depth-averaged finite-volume shallow-water equation (SWE) solver operating across an 818.37 km² catchment over 51.73 km reach.
2. **DualSPHysics v5.4 (Milestone M6):** 2D Lagrangian Smoothed Particle Hydrodynamics (SPH) solver operating across the 0–1500 m near-field reach.

M7 provides:
- A shared geospatial comparison corridor and common gauge network.
- Objective comparison of water depths, velocities, spatial attenuation, and hydraulic regimes.
- Quantitative audit of temporal and forcing incompatibilities.
- Hybrid architecture design defining the scientific roles of each solver.
- Rigorous coupling readiness assessment without unscientific shortcuts (e.g., multiplying unit discharge by arbitrary valley width).

---

## 2. Common Spatial Framework

To ensure that both numerical models are sampled at mathematically identical physical locations:
- **Common Centerline:** Preserved directly from `data/sph/nearfield_centerline.gpkg` to `data/comparison/common_nearfield_centerline.gpkg`.
- **Projected CRS:** EPSG:32643 (WGS 84 / UTM Zone 43N).
- **Breach Origin:** $11.47083^\circ\text{ N}, 77.11389^\circ\text{ E}$ $\rightarrow$ $(730,450.10\text{ m E}, 1,269,149.74\text{ m N})$.
- **Common Gauge Network (`data/comparison/common_gauges.gpkg`):** Five benchmark stations defined at exact downstream chainages:

| Station ID | Chainage [m] | Easting [m] | Northing [m] | Longitude [°E] | Latitude [°N] | Bed Elev [m MSL] | D-Flow Mesh Face | Sampling Dist [m] | Inside Cell? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **G_100m** | 100.0 | 730545.28 | 1269119.06 | 77.113370 | 11.472936 | 255.18 | 7968 | 31.30 | True |
| **G_250m** | 250.0 | 730688.05 | 1269073.04 | 77.114675 | 11.472511 | 246.82 | 7969 | 44.48 | True |
| **G_500m** | 500.0 | 730759.76 | 1269272.56 | 77.115346 | 11.474309 | 250.39 | 8351 | 24.58 | True |
| **G_1000m** | 1000.0 | 730603.09 | 1269729.06 | 77.113941 | 11.478445 | 245.83 | 8872 | 51.37 | True |
| **G_1500m** | 1500.0 | 730628.27 | 1270210.45 | 77.114204 | 11.482794 | 245.43 | 9547 | 45.13 | True |

*Note: All five gauge locations lie strictly within their queried ~100 m x 100 m D-Flow mesh face polygons.*

---

## 3. D-Flow FM Formulation (Milestone M5)

- **Governing Equations:** 2D Shallow Water Equations (SWE) based on depth-averaged Navier-Stokes.
- **Mesh:** 82,309 computational faces (~100 m nominal cell dimension).
- **Terrain:** SRTM 30 m DEM averaged onto cell faces.
- **Bed Friction:** Uniform Manning coefficient ($n = 0.035\text{ s/m}^{1/3}$).
- **Flow Physics:** Fully accommodates 2D lateral floodplain spreading across the Bhavani valley; assumes hydrostatic pressure distribution (vertical acceleration $\approx 0$).

---

## 4. DualSPHysics Formulation (Milestone M6)

- **Governing Equations:** Weakly Compressible Navier-Stokes equations discretized via Smoothed Particle Hydrodynamics (SPH) with Tait Equation of State.
- **Discretization:** 10,982 particles ($dp = 1.0$ m nominal resolution; 6,800 fluid + 4,182 boundary particles).
- **Domain Geometry:** 2D longitudinal unit-width profile ($1.0$ m width) along the river centerline.
- **Flow Physics:** Resolves full non-hydrostatic vertical acceleration, plunging toe jet dynamics, dynamic free-surface breakup, and violent turbulence. Does **not** include lateral floodplain expansion.
- **Resolution Status:** `PARTICLE_RESOLUTION_SENSITIVITY NOT_STABILIZED` (retains resolution dependency across $dp = 1.0$ m to $4.0$ m).

---

## 5. Forcing Differences & Non-Equivalence

The two models operate under fundamentally distinct initial-boundary conditions:
- **D-Flow FM:** Continuous inflow discharge boundary condition representing the complete 30-hour `BHV_BASE` screening hydrograph ($Q_{\text{peak}} = 18,742.38$ m³/s at $t = 14,095.59$ s, rise time 3.92 hours, volume $595.66$ MCM).
- **DualSPHysics:** Instantaneous release of an initialized static fluid block representing peak-state outflow ($H = 17.526$ m, $L = 400$ m, unit volume $7,010.4$ m³/m, duration 600 s).

Because of this difference, **direct one-to-one hydrograph equivalence does NOT exist**.

---

## 6. Depth Comparison

Peak water depth comparison across the common gauge network:

| Station ID | Chainage [m] | D-Flow Peak Depth [m] | SPH Peak Depth [m] | Absolute Model Spread [m] | Relative Model Spread [%] | Depth Ratio (SPH / D-Flow) | Comparison Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **G_100m** | 100.0 | 6.215 | 8.059 | +1.844 | +29.67% | 1.2967 | Valid common station |
| **G_250m** | 250.0 | 14.641 | 12.004 | -2.637 | -18.01% | 0.8199 | Valid common station |
| **G_500m** | 500.0 | 11.044 | 5.550 | -5.494 | -49.75% | 0.5025 | Valid common station |
| **G_1000m** | 1000.0 | 13.572 | 5.211 | -8.361 | -61.60% | 0.3840 | Valid common station |
| **G_1500m** | 1500.0 | 14.126 | 0.000 | -14.126 | -100.00% | 0.0000 | SPH not reached within 600 s |

**Hydrodynamic Interpretation:**  
- At 100 m, SPH exhibits higher depth ($8.06$ m vs $6.22$ m) due to the steep breach plunge.  
- At 250 m, both models record localized depth peaks ($12.00$ m vs $14.64$ m) in the toe foundation depression.  
- Downstream of 500 m, D-Flow depths rise ($11.0$–$14.1$ m) as the multi-hour hydrograph inundates the valley floor, whereas SPH depths attenuate ($5.55$–$5.21$ m) as the finite fluid mass spreads longitudinally.

---

## 7. Velocity Comparison

Peak flow velocity comparison (excluding unrepresentative global particle extremes):

| Station ID | Chainage [m] | D-Flow Peak Vel [m/s] | SPH Peak Vel [m/s] | Absolute Model Spread [m/s] | Relative Model Spread [%] | Velocity Ratio (SPH / D-Flow) | Comparison Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **G_100m** | 100.0 | 2.466 | 23.159 | +20.693 | +839.13% | 9.3913 | Gauge-specific SPH extraction |
| **G_250m** | 250.0 | 2.505 | 24.726 | +22.221 | +887.07% | 9.8707 | Gauge-specific SPH extraction |
| **G_500m** | 500.0 | 2.648 | 15.947 | +13.299 | +502.23% | 6.0223 | Gauge-specific SPH extraction |
| **G_1000m** | 1000.0 | 4.324 | 13.996 | +9.672 | +223.68% | 3.2368 | Gauge-specific SPH extraction |
| **G_1500m** | 1500.0 | 4.451 | 0.000 | -4.451 | -100.00% | 0.0000 | SPH not reached within 600 s |

**Hydrodynamic Interpretation:**  
SPH captures violent non-hydrostatic jet plunging down the breach face ($23$–$25$ m/s), whereas D-Flow FM averages flow across 100 m wide mesh cells ($2.5$–$4.5$ m/s). As flow travels downstream to 1000 m, SPH decelerates due to bed resistance ($24.7 \rightarrow 14.0$ m/s), while D-Flow accelerates slightly as water enters the confined downstream channel.

---

## 8. Arrival-Time Context

| Station ID | Chainage [m] | D-Flow Arrival (from $t_0$) [s] | SPH Arrival (from Release) [s] | D-Flow $Q_{\text{peak}}$ Time [s] | Forcing Equivalence | Interpretation Context |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **G_100m** | 100.0 | 4,200 | 5.00 | 14,095.59 | **FALSE** | `SCENARIO_RESPONSE_CONTEXT` |
| **G_250m** | 250.0 | 1,800 | 12.00 | 14,095.59 | **FALSE** | `SCENARIO_RESPONSE_CONTEXT` |
| **G_500m** | 500.0 | 1,800 | 28.00 | 14,095.59 | **FALSE** | `SCENARIO_RESPONSE_CONTEXT` |
| **G_1000m** | 1000.0 | 600 | 119.00 | 14,095.59 | **FALSE** | `SCENARIO_RESPONSE_CONTEXT` |
| **G_1500m** | 1500.0 | 1,200 | NOT_REACHED_WITHIN_600_S | 14,095.59 | **FALSE** | `SCENARIO_RESPONSE_CONTEXT` |

**Diagnostic Time Audit:**  
- In D-Flow FM, $t = 0$ is the start of the hydrograph where $Q \approx 0$. Wetting times ($600$–$4200$ s) correspond to early rising-limb discharges.
- In SPH, $t = 0$ is the instant of peak fluid release. Arrivals ($5$–$119$ s) reflect wave front celerity under peak energy head.
- **Timing equivalence is FALSE for every station.** Percentage timing error is **not computed**.

---

## 9. Normalized Spatial Profiles

To evaluate spatial decay and amplification patterns independent of absolute magnitudes, metrics are normalized by the 100 m station values ($h^* = h / h_{100\text{m}}$, $u^* = u / u_{100\text{m}}$):

| Station ID | Chainage [m] | $x^*$ (Ch / 1500) | D-Flow $h^*$ | SPH $h^*$ | D-Flow $u^*$ | SPH $u^*$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **G_100m** | 100.0 | 0.0667 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **G_250m** | 250.0 | 0.1667 | 2.3558 | 1.4895 | 1.0158 | 1.0677 |
| **G_500m** | 500.0 | 0.3333 | 1.7770 | 0.6887 | 1.0738 | 0.6886 |
| **G_1000m** | 1000.0 | 0.6667 | 2.1837 | 0.6466 | 1.7534 | 0.6043 |
| **G_1500m** | 1500.0 | 1.0000 | 2.2729 | 0.0000 | 1.8049 | 0.0000 |

**Trend Observation:**  
- Both models capture peak depth pooling at 250 m ($h^* > 1.0$).
- Beyond 250 m, SPH exhibits continuous attenuation ($h^*: 1.49 \rightarrow 0.69 \rightarrow 0.65$; $u^*: 1.07 \rightarrow 0.69 \rightarrow 0.60$).
- D-Flow maintains elevated depths ($h^* \approx 1.8$–$2.3$) due to sustained multi-hour volume accumulation.

---

## 10. Hydraulic Regime & Dimensionless Diagnostics

Using synchronized depths extracted at the exact timestamp of peak velocity:

| Station ID | Chainage [m] | D-Flow $U_{\text{peak}}$ [m/s] | D-Flow $h$ at $U_{\text{peak}}$ [m] | D-Flow Froude ($Fr$) | D-Flow Regime | SPH $U_{\text{peak}}$ [m/s] | SPH $h$ at $U_{\text{peak}}$ [m] | SPH Froude ($Fr$) | SPH Regime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **G_100m** | 100.0 | 2.466 | 2.380 | 0.510 | SUBCRITICAL | 23.159 | 5.433 | 3.173 | SUPERCRITICAL |
| **G_250m** | 250.0 | 2.505 | 1.223 | 0.723 | SUBCRITICAL | 24.726 | 6.830 | 3.021 | SUPERCRITICAL |
| **G_500m** | 500.0 | 2.648 | 1.793 | 0.631 | SUBCRITICAL | 15.947 | 5.268 | 2.219 | SUPERCRITICAL |
| **G_1000m** | 1000.0 | 4.324 | 7.885 | 0.492 | SUBCRITICAL | 13.996 | 3.169 | 2.511 | SUPERCRITICAL |
| **G_1500m** | 1500.0 | 4.451 | 7.777 | 0.510 | SUBCRITICAL | 0.000 | N/A | N/A | NOT_REACHED |

DualSPHysics operates strictly in the **supercritical regime** ($Fr \approx 2.2$–$3.2$), reflecting shooting unconfined plunge flow. D-Flow FM operates in the **subcritical regime** ($Fr \approx 0.49$–$0.72$), reflecting tranquil floodplain storage and depth-averaged shear.

---

## 11. Cross-Model Spread Statistics

Descriptive metrics across the four common reached stations (100 m to 1000 m):
- **Depth Spread:**
  - Median absolute spread: **4.066 m**
  - Median ratio (SPH / D-Flow): **0.6612**
  - Ratio range: **0.3840** (at 1000 m) to **1.2967** (at 100 m)
- **Velocity Spread:**
  - Median absolute spread: **16.996 m/s**
  - Median ratio (SPH / D-Flow): **7.7068**
  - Ratio range: **3.2368** (at 1000 m) to **9.8707** (at 250 m)
- **Trend Classifications:**
  - Downstream Progression: `CONSISTENT_TREND`
  - Depth Attenuation / Amplification: `PARTIALLY_CONSISTENT`
  - Velocity Trend: `DIVERGENT_TREND`
    - *Explanation:* SPH shows strong attenuation after the near-dam jet region ($24.73 \rightarrow 15.95 \rightarrow 14.00$ m/s), whereas D-Flow depth-averaged peak velocity increases farther downstream in the sampled reach ($2.47 \rightarrow 2.51 \rightarrow 2.65 \rightarrow 4.32 \rightarrow 4.45$ m/s). This is not solver error because forcing and dimensional formulations are non-equivalent.
  - High-Energy Near-Field Behaviour: `CONSISTENT_TREND`

---

## 12. Near-Field Role (DualSPHysics)

The scientific purpose of DualSPHysics in JalRakshak-HD is:
- High-gradient near-field hydrodynamic diagnostics (0–500 m).
- Calculation of dynamic wave plunge trajectories down the dam face.
- Assessment of maximum hydrodynamic impact loads and high-energy near-field velocities relevant to potential erosion/scour assessment on immediate toe structures and energy dissipators (without claiming actual sediment transport or morphological scour simulation).
- Resolution of free-surface aeration and splash behavior inaccessible to shallow-water models.

---

## 13. Long-Reach Role (D-Flow FM)

The scientific purpose of D-Flow FM in JalRakshak-HD is:
- Long-reach catchment inundation routing (0–51.73 km reach, 818.37 km² domain).
- Prediction of regional flood arrival times for downstream settlements (Sathyamangalam, Gobichettipalayam, Erode).
- Peak inundation extent, depth hazard mapping, and critical infrastructure exposure analysis.
- Mass-conservative 30-hour flood volume attenuation across real river morphology.

---

## 14. Handoff Candidates Evaluation

| Candidate Chainage | SPH Peak Depth | SPH Peak Vel | SPH $Fr$ | D-Flow Peak Depth | D-Flow Peak Vel | D-Flow $Fr$ | Evaluation Status | Scientific Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **250 m** | 12.00 m | 24.73 m/s | 3.02 | 14.64 m | 2.51 m/s | 0.72 | **REJECTED** | Plunging toe jet impact zone; violent non-hydrostatic vertical accelerations violate SWE assumptions. |
| **500 m** | 5.55 m | 15.95 m/s | 2.22 | 11.04 m | 2.65 m/s | 0.63 | **RECOMMENDED_FUTURE_HANDOFF_CANDIDATE** | Located downstream of the toe plunge jet; flow has transitioned into a coherent longitudinal sheet; well upstream of downstream front deceleration; both models actively represent this chainage. Preferred design candidate only; direct numerical coupling is not presently possible. |
| **1000 m** | 5.21 m | 14.00 m/s | 2.51 | 13.57 m | 4.32 m/s | 0.49 | **MARGINAL** | Reached late in SPH (119 s); SPH front reached 1280.41 m by 600 s and the 1500 m station was NOT_REACHED_WITHIN_600_S (it was slowing substantially but was still advancing); sparse particle support. |

---

## 15. Coupling Limitations & Scaling Blocker

### 15.1 The Unit-Width Scaling Blocker
DualSPHysics M6 is a **2D unit-width longitudinal model** (1.0 m thickness). At 500 m, SPH produces a unit discharge $q = u \cdot h \approx 15.95 \cdot 5.27 = 84.06$ m²/s.  
To transfer this discharge into D-Flow FM, an effective valley flow width $B_{\text{eff}}$ is required:
$$Q = q \cdot B_{\text{eff}}$$
However, SRTM terrain indicates the Bhavani valley width at 500 m is non-uniform and varies continuously with water elevation. **Multiplying unit discharge by an arbitrary width would introduce unphysical mass injection or deficit.**  
Therefore:
$$\text{direct\_discharge\_coupling\_ready} = \text{false}$$
$$\text{Reason: } \text{UNIT\_WIDTH\_TO\_FULL\_WIDTH\_SCALING\_UNRESOLVED}$$

### 15.2 Coupling Readiness Assessment

| Dimension | Readiness State | Technical Evaluation |
| :--- | :--- | :--- |
| **Geometry Compatibility** | `PARTIAL` | 1D longitudinal centerline vs. 2D planform unstructured mesh |
| **Coordinate Compatibility** | `READY` | Both solvers aligned to EPSG:32643 UTM Zone 43N |
| **Time-Reference Compatibility** | `NOT_READY` | Hydrograph start ($t_0 \approx 0$) vs. peak-state release ($t_0 = \text{peak}$) |
| **Flow-Width Compatibility** | `NOT_READY` | Unit-width (1.0 m) vs. full valley width; scaling unresolved |
| **Forcing Compatibility** | `NOT_READY` | Complete continuous hydrograph vs. finite initialized block |
| **Bathymetry Compatibility** | `PARTIAL` | Both derived from SRTM 30 m, but discretized differently |
| **Resolution Compatibility** | `NOT_READY` | 1.0 m SPH particle spacing vs. 100 m D-Flow mesh cells |
| **Overall Coupling Status** | **`NOT_READY`** | **Direct numerical coupling is DESIGN_ONLY** |

**Coupling Readiness Blockers:**
1. Unit-width to full-width scaling unresolved.
2. Forcing histories differ (continuous 30-hour hydrograph vs. finite peak block).
3. Time origins differ ($t_0$ at hydrograph start vs. $t_0$ at release).
4. DualSPHysics particle resolution sensitivity is `NOT_STABILIZED`.

---

## 16. Future Coupling Requirements

To achieve physically sound, bidirectional or unidirectional numerical coupling in future research:
1. **3D SPH Near-Field Model:** Expand SPH from 2D unit-width to full 3D with surveyed bathymetry across 0–500 m to naturally resolve lateral spreading and physical discharge.
2. **Continuous Dynamic Boundary Inflow in SPH:** Replace static fluid block initialization with a time-varying inlet boundary matching the full breach hydrograph.
3. **Synchronized Time Framework:** Align temporal origins such that SPH boundary forcing matches the real-time hydrograph progression.
4. **Non-Reflective Flux-Interpolating Boundary:** Implement a buffer zone at 500 m capable of interpolating SPH particle mass and momentum fluxes onto the 2D SWE mesh without artificial wave reflection.

---

## 17. Conclusion

Milestone M7 successfully establishes the common spatial corridor, extracts authentic NetCDF and SPH hydrodynamic metrics across five common stations, documents temporal non-equivalence, evaluates handoff candidates, and delivers a complete, modular coupling architecture (`configs/hybrid_solver.yaml` and `backend/app/models/solver_coupling.py`).

By maintaining strict scientific honesty—classifying the comparison as `CROSS_SOLVER_CONSISTENCY_ANALYSIS`, documenting model spread rather than claiming validation, and holding coupling at `DESIGN_ONLY` due to unresolved unit-width scaling—Milestone M7 provides a solid foundation for Milestone M8 (HADR Logistics and Evacuation Planning).
