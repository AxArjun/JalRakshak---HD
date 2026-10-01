# Milestone M4: Breach Outflow Hydrograph Generation Summary

**Project:** JalRakshak-HD (SIH PS 26161)  
**Study Site:** Bhavanisagar Dam (Lower Bhavani Project), Bhavani River, Tamil Nadu, India  
**Selected Coordinates:** 11.47083° N, 77.11389° E  
**Milestone:** M4 — Breach Outflow Hydrograph Generation  
**Status:** COMPLETE / VALIDATED  

---

## 1. Scientific Limitations & Methodological Declarations

> [!IMPORTANT]
> ### Mandatory Scientific Declarations (M4 Engineering Protocol)
> 1. **No Measured Breach Hydrograph Exists:** Bhavanisagar Dam is an operational, intact infrastructure asset. No historical failure or measured breach outflow has occurred.
> 2. **Hypothetical Scenario:** All scenarios modeled herein represent hypothetical catastrophic breach events simulated strictly for disaster preparedness, emergency action planning (EAP), and hydrodynamic risk assessment under SIH PS 26161.
> 3. **Stage-Storage Curve Unavailable:** Authoritative surveyed reservoir bathymetry and elevation-storage-discharge tables are not publicly published.
> 4. **Empirically Synthesized Screening Hydrographs:** The hydrographs are synthesized using empirical peak-discharge regressions and volume-constrained geometric formulations (`VOLUME_CONSTRAINED_TRIANGULAR_SCREENING_HYDROGRAPH`).
> 5. **Modelling Assumptions for $V_w$ and $h_w$:** The water volume released ($V_w = 780.5\text{ MCM}$) and water depth above breach invert ($h_w = 32.0\text{ m}$) are locked M3 modeling assumptions (`MODEL_ASSUMPTION_FIRST_ESTIMATE`) based on CWC live storage and operational full depth records.
> 6. **Mathematical Volume Constraint:** The hydrograph duration and recession limb are mathematically constrained by conservation of mass such that:
>    $$\int_0^{T} Q(t)\,dt = \frac{1}{2} Q_{\text{peak}} T = V_w \implies T = \frac{2 V_w}{Q_{\text{peak}}}$$
>    Recession time is derived, not artificially invented.
> 7. **Dynamic Level-Pool Reservoir Routing Not Claimed:** Full dynamic level-pool or 2D dynamic reservoir drawdown routing is not claimed due to lack of bathymetry.
> 8. **Downstream Routing in M5:** Milestone M5 will ingest these validated boundary forcing hydrographs (`.tim` / `.csv`) to drive 2D hydrodynamic flood propagation across the high-resolution terrain using D-Flow FM.

---

## 2. Locked Reservoir and Breach Inputs (M3 Provenance)

| Parameter | Value | Unit | Classification | Source & Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Full Reservoir Level (FRL)** | `280.42` | m MSL | `AUTHORITATIVE_VERIFIED` | CWC National Register of Large Dams / WRD Dam Safety Records |
| **Reference Breach Water Volume ($V_w$)** | `780.50` | MCM ($780.5 \times 10^6\text{ m}^3$) | `MODEL_ASSUMPTION_FIRST_ESTIMATE` | CWC Hydrological Data Book 2020 Live Storage |
| **Reference Water Depth ($h_w$)** | `32.00` | m | `MODEL_ASSUMPTION_FIRST_ESTIMATE` | TNDWR Operational Full Depth (105.0 ft) |
| **Reference Breach Structure Height ($h_b$)** | `40.00` | m | `MODEL_ASSUMPTION_FIRST_ESTIMATE` | JalRakshak-HD M3 Earthen Flank Breach Definition |
| **M3 Froehlich (2008) Formation Time ($t_f$)** | `14,095.59` (3.915 hr) | s | `PUBLISHED_EMPIRICAL_RELATIONSHIP` | Froehlich (2008) ASCE JHE 134(12) |
| **M3 MacDonald (1984) Formation Time ($t_f$)** | `13,907.39` (3.863 hr) | s | `PUBLISHED_EMPIRICAL_RELATIONSHIP` | MacDonald & Langridge-Monopolis (1984) ASCE JHE 110(5) |

---

## 3. Implemented Peak-Discharge Regressions

### 3.1 Model A: Froehlich (1995)
Exact published SI regression (ASCE Water Resources Engineering Conf., pp. 887–891; USBR DSO-98-004 Eq. 2):
$$Q_p = 0.607 \cdot V_w^{0.295} \cdot h_w^{1.24}$$

Evaluating with $V_w = 780,500,000\text{ m}^3$ and $h_w = 32.0\text{ m}$:
- $V_w^{0.295} = (780,500,000)^{0.295} = 422.3787$
- $h_w^{1.24} = (32.0)^{1.24} = 73.0874$
- $Q_p = 0.607 \times 422.3787 \times 73.0874 = \mathbf{18,742.38\text{ m}^3/\text{s}}$

Froehlich (1995) Breach Formation Time Diagnostic Equation:
$$t_f\,[\text{hr}] = 0.00254 \cdot V_w^{0.53} \cdot h_b^{-0.9} \implies t_f = 4.7417\text{ hr} = 17,070.25\text{ s}$$

### 3.2 Model B: MacDonald & Langridge-Monopolis (1984) / Wahl (1998)
Exact SI regression based on Breach Formation Factor ($V_w \cdot h_w$) (Wahl 1998 Table 5; Wahl 2004 Eq. 6):
$$Q_p = 1.154 \cdot (V_w \cdot h_w)^{0.412}$$

Evaluating with $V_w \cdot h_w = 2.4976 \times 10^{10}\text{ m}^4$:
- $(2.4976 \times 10^{10})^{0.412} = 19,221.15$
- $Q_p = 1.154 \times 19,221.15 = \mathbf{22,181.21\text{ m}^3/\text{s}}$

---

## 4. Screening Hydrograph Synthesis Results

All hydrographs are synthesized at a uniform $\Delta t = 60\text{ s}$ resolution using mass conservation:

| Metric | `BHV_BASE` (Hybrid Base) | `BHV_FROEHLICH95_DIAGNOSTIC` | `BHV_PEAK_SENSITIVITY_MLM` |
| :--- | :--- | :--- | :--- |
| **Geometry Model** | Froehlich (2008) | Froehlich (1995) | MacDonald et al. (1984) |
| **Peak Discharge Model** | Froehlich (1995) | Froehlich (1995) | MacDonald / Wahl (1998) |
| **Peak Discharge ($Q_p$)** | **$18,742.38\text{ m}^3/\text{s}$** | **$18,742.38\text{ m}^3/\text{s}$** | **$22,181.21\text{ m}^3/\text{s}$** |
| **Rise Time ($t_{\text{rise}}$)** | $14,095.59\text{ s}$ ($3.915\text{ hr}$) | $17,070.25\text{ s}$ ($4.742\text{ hr}$) | $13,907.39\text{ s}$ ($3.863\text{ hr}$) |
| **Recession Time ($t_{\text{rec}}$)** | $69,191.59\text{ s}$ ($19.220\text{ hr}$) | $66,216.93\text{ s}$ ($18.394\text{ hr}$) | $56,467.49\text{ s}$ ($15.685\text{ hr}$) |
| **Total Duration ($T_{\text{total}}$)** | $83,287.18\text{ s}$ ($23.135\text{ hr}$) | $83,287.18\text{ s}$ ($23.135\text{ hr}$) | $70,374.88\text{ s}$ ($19.549\text{ hr}$) |
| **Mean Discharge** | $9,371.19\text{ m}^3/\text{s}$ | $9,371.19\text{ m}^3/\text{s}$ | $11,090.60\text{ m}^3/\text{s}$ |
| **$Q_{\text{peak}} / \bar{Q}$ Ratio** | $2.00$ | $2.00$ | $2.00$ |
| **Target Volume** | $780.50\text{ MCM}$ | $780.50\text{ MCM}$ | $780.50\text{ MCM}$ |
| **Integrated Volume** | $780.50\text{ MCM}$ | $780.50\text{ MCM}$ | $780.50\text{ MCM}$ |
| **Volume Error** | **$0.0000\%$** | **$0.0000\%$** | **$0.0000\%$** |
| **Status** | **PASS** | **PASS** | **PASS** |

---

## 5. Hydrodynamic Boundary File Export (D-Flow FM Preparation)

For each scenario, high-resolution boundary files are generated:
- CSV time series: `data/dflowfm/hydrographs/<SCENARIO_ID>.csv`
- D-Flow FM boundary forcing `.tim` files: `data/dflowfm/hydrographs/<SCENARIO_ID>_boundary.tim`

Format for `.tim`:
Two-column ASCII with time in minutes and discharge in $\text{m}^3/\text{s}$, ready for D-Flow FM external open boundary injection in Milestone M5.

---

## 6. Diagnostic Visualizations

Diagnostic plots have been generated and archived:
1. `outputs/maps/m4_breach_hydrograph.png` — Multi-scenario breach outflow discharge vs. time comparison.
2. `outputs/maps/m4_cumulative_volume.png` — Mass conservation and cumulative release volume progression.
