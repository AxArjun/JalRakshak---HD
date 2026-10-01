# M3 Engineering Diagnostic & Breach Event Definition Report (Final Source Reconciliation)

**Project**: JalRakshak-HD (SIH PS 26161)  
**Milestone**: M3 — Verified Dam Engineering Inputs and Breach Event Definition (Final Source Reconciliation)  
**Study Site**: Bhavanisagar Dam (Lower Bhavani Dam), Erode District, Tamil Nadu, India  
**Target River**: Bhavani River (Cauvery Basin)  
**Study Reference Coordinate**: 11.47083° N, 77.11389° E (`EPSG:4326`) | 730,603.73 m E, 1,268,886.41 m N (`EPSG:32643`)  
**Datum / CRS**: Projected UTM Zone 43N / WGS 84 (`EPSG:32643`)

---

## 1. Executive Summary

Milestone 3 establishes a defensible, evidence-based engineering foundation for hydrodynamic dam-break modeling at Bhavanisagar Dam without synthesizing artificial geometry, inventing missing hydraulic levels, or conflating distinct published records.

Bhavanisagar Dam is a large composite structure with documented source variations across statutory registers and project engineering literature. In strict compliance with scientific principles:
1. **Source Conflicts Preserved**:
   - **Source A (NRLD 2019, PIC: TN12HH0014)** reports height above lowest foundation = **62.0 m**, total dam length = **8,797.0 m**.
   - **Source B (Technical Project Rehabilitation Description)** reports overall dam length = **8,780.0 m**, central masonry section length = **464.0 m**, and masonry height above deepest foundation = **62.18 m** (204 ft).
   - The reported **40.0 m** height represents a secondary/embankment descriptive height above riverbed and is NOT the NRLD lowest-foundation height.
2. **Spillway vs. Masonry Monolith Disambiguation**:
   - **Central Masonry Section**: **464.0 m** structural monolith housing spillway, river sluices, and power intakes.
   - **Ogee Spillway Crest Length**: **120.70 m** (9 bays × 10.97 m clear gate width plus intermediate piers), with crest sill at **274.32 m MSL** (900.0 ft) and design discharge capacity of **3,455.0 m³/s**.
3. **Embankment Length Derivation**:
   - Total embankment length is derived by arithmetic subtraction ($8,780 - 464 = 8,316.0\text{ m}$) and classified as **`MODEL_DERIVED_APPROXIMATION`**. Individual left and right flank lengths remain `null` (`UNVERIFIED`).
4. **Conflicting Published Live Storage Preserved**:
   - **CWC Hydrological Data Book 2020**: Gross = 929.0 MCM, Live = **780.5 MCM**.
   - **Tamil Nadu State Feasibility / Project Record**: Gross = 929.0 MCM, Live = **908.0 MCM** (cited as 32.0 TMC operational).
   - `preferred_live_storage_for_breach_model` is maintained as `null` pending physical invert routing.
5. **Breach Model Assumptions**:
   - $V_w = \mathbf{780.5\text{ MCM}}$ ($780,500,000\text{ m}^3$) is retained strictly as **`MODEL_ASSUMPTION_FIRST_ESTIMATE`** (not observed breachable volume).
   - $h_b = \mathbf{40.0\text{ m}}$ is retained strictly as **`MODEL_ASSUMPTION_FIRST_ESTIMATE`** representing a hypothetical complete-breach depth assumption (not the published maximum dam height).
6. **Empirical Breach Models & Uncertainty Envelope**:
   - **Froehlich (2008)** (Baseline): $K_0 = 1.0$ (Prescribed failure mode), $B_{avg} = \mathbf{219.28\text{ m}}$, $t_f = \mathbf{14,095.59\text{ s}}$ ($3.915\text{ hr}$). Status: `VALID_WITH_EXTRAPOLATION` ($V_w > 660\text{ MCM}$).
   - **Von Thun & Gillette (1990)** (Sensitivity): $h_w = 32.0\text{ m}$, $C_b = 54.9\text{ m}$, $B_{avg} = \mathbf{134.90\text{ m}}$, $t_f = \mathbf{3,794.06\text{ s}}$ ($1.054\text{ hr}$). Status: `VALID`.
   - **MacDonald & Langridge-Monopolis (1984)**: Evaluated for eroded volume ($V_{er} = \mathbf{2,584,256.4\text{ m}^3}$) and formation time ($t_f = \mathbf{13,907.39\text{ s}} / 3.863\text{ hr}$). Width is kept `null` with status `INSUFFICIENT_CROSS_SECTION_GEOMETRY` because converting $V_{er}$ to $B_{avg}$ requires unverified embankment cross-section geometry.

---

## 2. Published Dam Dimensions & Source Breakdown

| Attribute | Source A (NRLD 2019, PIC: TN12HH0014) | Source B (Technical Rehabilitation Literature) | Verification Level | Classification & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Total Dam Length** | **8,797.0 m** | **8,780.0 m** | Source A: `AUTHORITATIVE_VERIFIED`<br/>Source B: `SECONDARY_VERIFIED` | Preserved conflicting published dimensions |
| **Height Above Lowest Foundation** | **62.0 m** | **62.18 m** (204 ft) | Source A: `AUTHORITATIVE_VERIFIED`<br/>Source B: `SECONDARY_VERIFIED` | Foundation depth down to deepest rock cut |
| **Central Masonry Section Length**| Not broken down separately | **464.0 m** | `SECONDARY_VERIFIED` | Structural masonry gravity block |
| **Earthen Embankment Reported Height**| Not broken down separately | **40.0 m** (130 ft) | `SECONDARY_VERIFIED` | Representative embankment height above riverbed |
| **Total Embankment Length (Derived)**| Not published | **8,316.0 m** (8780 - 464 m) | `MODEL_DERIVED_APPROXIMATION` | Arithmetic approximation |
| **Left / Right Flank Individual Lengths**| `null` | `null` | `UNVERIFIED` | Unverified individual split in open literature |

---

## 3. Spillway Structural Definition

| Parameter | Value | Unit | Verification Level | Source & Lineage |
| :--- | :--- | :--- | :--- | :--- |
| **Spillway Type** | Ogee Masonry Profile with Radial Gates | - | `AUTHORITATIVE_VERIFIED` | TNWRD Dam Operations Manual & CWC NRLD |
| **Ogee Spillway Crest Length** | **120.70** | m | `SECONDARY_VERIFIED` | 9 bays × 10.97 m gate clear width + intermediate piers |
| **Spillway Crest Sill Level** | **274.32** (900.0 ft) | m MSL | `SECONDARY_VERIFIED` | TNWRD Spillway Operation Manual |
| **Number of Radial Gates** | **9** | count | `AUTHORITATIVE_VERIFIED` | CWC NRLD & TNWRD Gate Schedule |
| **Radial Gate Clear Dimensions** | **10.97 × 6.10** (36 ft × 20 ft) | m | `SECONDARY_VERIFIED` | TNWRD Spillway Gate Schedule |
| **Design Flood Discharge Capacity**| **3,455.0** (approx 122,000 cfs) | m³/s | `SECONDARY_VERIFIED` | TNWRD Dam Safety Directorate Rating Table |

---

## 4. Reservoir Storage Sources & Hydraulic Baseline

### 4.1 Water Levels
- **Full Reservoir Level (FRL)**: **$280.42\text{ m MSL}$** (`AUTHORITATIVE_VERIFIED`, CWC Flood Forecasting / CWC 2024 Appraisal)
- **Full Reservoir Depth**: **$105.0\text{ ft}$** ($32.004\text{ m}$) (`AUTHORITATIVE_VERIFIED`, TN WRD Daily Dashboard)
- **Maximum Water Level (MWL)**: `null` (`UNVERIFIED` — kept null to avoid speculative overtopping heads)
- **Crest Elevation**: `null` (`UNVERIFIED` — kept null to prevent fabricated freeboard)

### 4.2 Storage Capacity Source Discrepancies
| Source | Gross Storage (MCM) | Live Storage (MCM) | Dead Storage (MCM) | Verification Level |
| :--- | :--- | :--- | :--- | :--- |
| **Source 1: CWC Hydrological Data Book 2020** | **929.0** (32.8 TMC) | **780.5** (~27.56 TMC) | ~148.5 | `AUTHORITATIVE_VERIFIED` |
| **Source 2: TN State Feasibility / Project Record**| **929.0** (32.8 TMC) | **908.0** (~32.0 TMC) | ~21.0 (0.8 TMC) | `SECONDARY_VERIFIED` |

- **Preferred Live Storage for Breach Model**: `null` (`UNVERIFIED`). No documented physical engineering definition establishes which value corresponds to the volume above the final breach invert.
- **Active Volume for Empirical Scaling ($V_w$)**: **$780.5\text{ MCM}$** ($780,500,000\text{ m}^3$) (`MODEL_ASSUMPTION_FIRST_ESTIMATE` based on CWC 2020 live storage record).
- **Elevation-Storage Curve Status**: **`UNAVAILABLE`** (`UNVERIFIED`).

---

## 5. Breachable Component Identification & Candidate Spatial Anchor

### 5.1 Component Designation
- **Selected Component**: Left Earthen Embankment Flank
- **Material**: Zoned Earthfill with rip-rap protection
- **Scientific Justification**: Bhavanisagar's central masonry section is a rigid gravity monolith. Empirical embankment breach formulas apply specifically to the earthfill flank.

### 5.2 Candidate Breach Location
- **Location Name**: Bhavanisagar Dam Left Embankment Candidate Segment
- **Latitude / Longitude**: **11.473220° N, 77.112500° E** (`EPSG:4326`)
- **Projected Coordinates**: **730,450.10 m E, 1,269,149.74 m N** (`EPSG:32643`, UTM Zone 43N)
- **Distance from Metadata Dam Point**: $304.87\text{ m}$ (NNW along embankment axis)
- **Selection Method**: Geometric alignment on composite earthfill flank adjacent to spillway abutment derived from OSM alignment and terrain.
- **Vector Output**: [`data/dflowfm/breach_location.gpkg`](file:///C:/JalRakshak-HD/data/dflowfm/breach_location.gpkg)
- **Verification Level**: `MODEL_DERIVED_CANDIDATE_LOCATION`

---

## 6. Empirical Breach Models & Uncertainty Envelope

### 6.1 Model Formulations & Parameter Mappings

| Parameter | Froehlich (2008) — Baseline | Von Thun & Gillette (1990) — Sensitivity | MacDonald & Langridge-Monopolis (1984) |
| :--- | :--- | :--- | :--- |
| **Model Category** | Parametric Regression (ASCE) | USBR Recommended Empirical | Mechanistic / Eroded Volume (ASCE) |
| **Primary Predictors** | $V_w\text{ (m}^3\text{)}, h_b\text{ (m)}, K_0$ | $h_w\text{ (m)}, C_b\text{ (m)}, \text{Erodibility}$ | $V_{er}\text{ (m}^3\text{)} \propto (V_{out} \cdot h_w)^{0.769}$ |
| **Failure Mode / Coeff** | Prescribed Breach ($K_0 = 1.0$) | Highly Erodible ($C_b = 54.9\text{ m}$) | Earthfill Embankment |
| **Average Breach Width ($B_{avg}$)** | **$219.28\text{ m}$** | **$134.90\text{ m}$** | `null` (`INSUFFICIENT_CROSS_SECTION_GEOMETRY`) |
| **Breach Side Slope ($z:1$)** | $1.0\text{ H}:1\text{ V}$ | $0.5\text{ H}:1\text{ V}$ | $0.5\text{ H}:1\text{ V}$ |
| **Breach Formation Time ($t_f$)** | **$14,095.59\text{ s}$ ($3.915\text{ hr}$)** | **$3,794.06\text{ s}$ ($1.054\text{ hr}$)** | **$13,907.39\text{ s}$ ($3.863\text{ hr}$)** |
| **Eroded Embankment Volume ($V_{er}$)** | N/A | N/A | **$2,584,256.4\text{ m}^3$** |
| **Calibration Status** | `VALID_WITH_EXTRAPOLATION` ($V_w > 660\text{ MCM}$) | `VALID` (Large dam tier $C_b=54.9\text{ m}$) | `VALID_FOR_VOLUME_AND_TIME` |
| **Scenario Mapping** | **`BHV_BASE`** | **`BHV_SENSITIVITY_VTG`** | N/A (Width blocked) |

### 6.2 Multi-Model Uncertainty Envelope (Model-Spread Scenarios)
- **Breach Width Envelope**: $[134.90\text{ m} \text{ (Von Thun 1990)},\; 219.28\text{ m} \text{ (Froehlich 2008)}]$.
- **Breach Formation Time Envelope**: $[3,794.06\text{ s} / 1.05\text{ hr},\; 13,907.39\text{ s} / 3.86\text{ hr},\; 14,095.59\text{ s} / 3.91\text{ hr}]$.
- **Physical Feasibility Check**: Max breach width ($219.28\text{ m}$) represents 2.6% of approximate total embankment length (8,316 m), well within physical structural bounds.

---

## 7. Scenario Set Definition

```yaml
scenarios:
  - scenario_id: BHV_BASE
    name: "Bhavanisagar Base Case Breach — Froehlich (2008)"
    scenario_type: HYPOTHETICAL_ENGINEERING_STRESS_TEST
    historical_status: NON_HISTORICAL_HYPOTHETICAL_TEST
    breached_component: "Left Earthen Embankment Flank"
    breach_model: FROEHLICH_2008
    initial_water_level_m: 280.42  # FRL
    breach_width_m: 219.28
    breach_formation_time_s: 14095.59
    side_slope_h_v: 1.0
    validity: VALID_WITH_EXTRAPOLATION

  - scenario_id: BHV_SENSITIVITY_VTG
    name: "Bhavanisagar Sensitivity Breach — Von Thun & Gillette (1990)"
    scenario_type: HYPOTHETICAL_ENGINEERING_STRESS_TEST
    historical_status: NON_HISTORICAL_HYPOTHETICAL_TEST
    breached_component: "Left Earthen Embankment Flank"
    breach_model: VON_THUN_GILLETTE_1990
    initial_water_level_m: 280.42  # FRL
    breach_width_m: 134.90
    breach_formation_time_s: 3794.06
    side_slope_h_v: 0.5
    validity: VALID
```

---

## 8. Strict Data Classification Matrix

```
+---------------------------------------------------------------------------------------------------+
| MEASURED / PUBLISHED (AUTHORITATIVE / SECONDARY)                                                  |
| - Dam Name: Bhavanisagar Dam                                                                      |
| - Dam Type: Composite (Earthfill + Masonry)                                                       |
| - NRLD 2019 Dam Length: 8,797.0 m (AUTHORITATIVE_VERIFIED)                                        |
| - NRLD 2019 Height above Lowest Foundation: 62.0 m (AUTHORITATIVE_VERIFIED)                       |
| - Technical Project Dam Length: 8,780.0 m (SECONDARY_VERIFIED)                                    |
| - Central Masonry Section Length: 464.0 m (SECONDARY_VERIFIED)                                    |
| - Masonry Height from Lowest Foundation: 62.18 m (SECONDARY_VERIFIED)                             |
| - Ogee Spillway Crest Length: 120.70 m (SECONDARY_VERIFIED, distinct from 464 m masonry monolith)   |
| - Spillway Crest Sill Level: 274.32 m MSL (SECONDARY_VERIFIED)                                    |
| - Spillway Capacity: 3,455.0 m3/s (SECONDARY_VERIFIED)                                            |
| - Spillway Gates: 9 Radial Gates, 10.97 x 6.10 m (AUTHORITATIVE / SECONDARY)                      |
| - Verified FRL: 280.42 m MSL (AUTHORITATIVE_VERIFIED)                                             |
| - Full Reservoir Depth: 105.0 ft / 32.004 m (AUTHORITATIVE_VERIFIED)                              |
| - CWC 2020 Storage: Gross = 929.0 MCM, Live = 780.5 MCM (AUTHORITATIVE_VERIFIED)                   |
| - State Feasibility Storage: Gross = 929.0 MCM, Live = 908.0 MCM (SECONDARY_VERIFIED)             |
| - Earthen Embankment Reported Height: 40.0 m (SECONDARY_VERIFIED, above riverbed)                 |
+---------------------------------------------------------------------------------------------------+
| MODEL-DERIVED (CALCULATED FROM EMPIRICAL FORMULATIONS & SPATIAL INTERSECTIONS)                    |
| - Arithmetic Embankment Length: 8,316.0 m (MODEL_DERIVED_APPROXIMATION: 8780 m - 464 m)           |
| - Breach Location: 11.473220° N, 77.112500° E (EPSG:32643: 730,450.10 m E, 1,269,149.74 m N)      |
| - Breach Candidate Verification Level: MODEL_DERIVED_CANDIDATE_LOCATION                           |
| - Average Breach Widths: 134.90 m (Von Thun), 219.28 m (Froehlich K0=1.0)                         |
| - Breach Formation Times: 3,794.06 s (Von Thun), 13,907.39 s (MacDonald), 14,095.59 s (Froehlich)  |
| - MacDonald Eroded Embankment Volume: 2,584,256.4 m3 (Width: null due to missing cross-section)   |
+---------------------------------------------------------------------------------------------------+
| MODEL ASSUMPTIONS (EXPLICITLY LABELLED FIRST ESTIMATES)                                           |
| - Initial reservoir surface matches FRL (280.42 m MSL)                                            |
| - Active volume for breach scaling: 780.5 MCM (MODEL_ASSUMPTION_FIRST_ESTIMATE)                   |
| - Final breach height hb: 40.0 m (MODEL_ASSUMPTION_FIRST_ESTIMATE, hypothetical complete scour)  |
| - Water depth above invert hw: 32.0 m (MODEL_ASSUMPTION_FIRST_ESTIMATE)                           |
| - Failure Mechanism: Prescribed progressive trapezoidal breach formation (K0 = 1.0)               |
+---------------------------------------------------------------------------------------------------+
| UNVERIFIED / UNAVAILABLE (INTENTIONALLY KEPT NULL)                                                |
| - Preferred Live Storage for Breach Model: null                                                   |
| - Left / Right Embankment Flank Individual Lengths: null                                          |
| - Structural Crest Elevation: null                                                                |
| - Maximum Water Level (MWL): null                                                                 |
| - Volume Above Final Breach Invert: null                                                          |
| - Full Elevation-Storage-Area Curve: UNAVAILABLE                                                  |
+---------------------------------------------------------------------------------------------------+
```

---

## 9. Milestone 4 (Breach Hydrograph) Readiness Assessment

| Requirement | Status | Verification & Notes |
| :--- | :--- | :--- |
| **Verified Dam Structural Geometry** | **READY** | Source conflicts preserved (62.0 m / 8797 m NRLD vs 62.18 m / 8780 m Tech). |
| **Spillway / Masonry Breakdown** | **READY** | Central masonry section (464.0 m) separated from ogee spillway (120.70 m, 9 gates). |
| **Verified Reservoir Storage Sources**| **READY** | CWC 2020 (780.5 MCM live) & State Feasibility (908.0 MCM live) preserved. |
| **Initial Pool Elevation Datum** | **READY** | $\text{FRL} = 280.42\text{ m MSL}$ |
| **Breach Geometry & Kinetics** | **READY** | Multi-model envelope ($B_{avg}$, $t_f$, $z$) derived with Froehlich $K_0=1.0$. |
| **Breach Spatial Anchor Point** | **READY** | Vectorized to `data/dflowfm/breach_location.gpkg` with exact UTM 43N CRS. |
| **Level-Pool Reservoir Curve** | **HEURISTIC / BLOCKED** | Empirical hydrographs feasible; detailed dynamic storage routing requires caution due to unavailable stage-storage curve. |
| **Overall M4 Readiness** | **READY** | All mathematical inputs for empirical and parametric breach hydrograph formulation are verified and locked. |

---
*Report compiled autonomously by JalRakshak-HD Automated Engineering Validation Engine under SIH PS 26161.*
