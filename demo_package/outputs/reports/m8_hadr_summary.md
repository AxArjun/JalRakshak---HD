# JalRakshak-HD: Milestone M8 — HADR Consequence & Exposure Analysis (Final Repair)
**Classification:** `SCREENING_HADR_CONSEQUENCE_ANALYSIS`
**Hydraulic Source:** `2D_DFLOWFM_SCREENING_INUNDATION_MODEL` (M5 D-Flow FM 2D Simulation, 82,309 faces, 181 timesteps)
**Hazard Standard:** CWC CDSO_GUD_DS_09_v1.0 (Guidelines for Classifying the Hazard Potential of Dams) / AIDR Guideline 7-3 (Smith, Davey, Cox, 2014)
**Study Area:** Bhavanisagar Dam Downstream Reach (51.73 km), Tamil Nadu, India
**CRS:** EPSG:32643 (WGS 84 / UTM Zone 43N)

---

## 1. Hazard Severity — CWC / AIDR 7-3 Combined Depth-Velocity Classification

Hazard evaluated synchronously at each of 181 timesteps across 82,309 D-Flow FM computational faces (`TIME_SYNCHRONOUS_STEPWISE_EVALUATION`).

| Class | CWC CDSO_GUD_DS_09_v1.0 Vulnerability Descriptor | Thresholds | Faces | Area (km²) | % of Inundated |
|:---:|:---|:---|:---:|:---:|:---:|
| H1 | Generally safe for vehicles, people, and buildings | D·V ≤ 0.3, D ≤ 0.3, V ≤ 2.0 | 187 | 1.87 | 1.85% |
| H2 | Unsafe for small vehicles | D·V ≤ 0.6, D ≤ 0.5, V ≤ 2.0 | 143 | 1.43 | 1.41% |
| H3 | Unsafe for vehicles, children, and the elderly | D·V ≤ 0.6, D ≤ 1.2, V ≤ 2.0 | 501 | 5.01 | 4.95% |
| H4 | Unsafe for vehicles and people | D·V ≤ 1.0, D ≤ 2.0, V ≤ 2.0 | 569 | 5.69 | 5.62% |
| H5 | Buildings vulnerable to structural damage; some less robust buildings may be subject to failure | D·V ≤ 4.0, D ≤ 4.0, V ≤ 4.0 | 1755 | 17.55 | 17.33% |
| H6 | All building types considered vulnerable to failure | D·V > 4.0 or D > 4.0 or V > 4.0 | 6974 | 69.74 | 68.85% |
| **Total** | — | — | **10129** | **101.29** | **100.00%** |

---

## 2. Population Exposure

> **Dataset Interpretation (MANDATORY):**
> WorldPop 2020 is the **PRIMARY** population dataset for priority ordering.
> GHSL 2025 is an independent **CROSS_CHECK** (DATASET_SPREAD ~2x) only.
> Both are modelled gridded estimates. The spread reflects different disaggregation
> methodologies, NOT two measurements of the same true population.
> **Do NOT average, combine, or weight-average the two datasets.**

| Dataset | Role | Total Inundated | Severe H3–H6 | Extreme H5–H6 |
|:---|:---:|:---:|:---:|:---:|
| WorldPop 2020 UN-Adjusted | **PRIMARY** | **42,428.1** | 40,744.3 | 35,762.7 |
| GHSL GHS-POP R2023A 2025 | CROSS_CHECK | 84,500.5 | 81,767.6 | 73,403.0 |
| Dataset Spread (Ratio) | GHSL/WP = 1.99x | ΔSpread = 42,072 persons | — | — |

---

## 3. Response Zone Geometry — Overlap Audit & Correction

**Original zones** (convex-hull corridor buffers in `response_zones.gpkg`) were found to overlap significantly:
- Sum of individual zone areas: **210.18 km²**
- Union (unique) area: **101.29 km²**
- Total overlap: **108.89 km²** (51.8%)

**Correction applied:** Non-overlapping exclusive sectors (`response_zones_exclusive.gpkg`) were created by projecting each D-Flow FM face and each 25m population pixel onto the river mainstem chainage and assigning it to exactly one sector. Double-counting = 0.

| Metric | Whole Inundation | Exclusive Zone Sum | Delta | Interpretation |
|:---|:---:|:---:|:---:|:---|
| D-Flow FM faces | 10129 | 10129 | +0 | Exact (face-level bijection) |
| Area (km²) | 101.290 | 101.290 | -0.000 | Exact (face area sum) |
| WorldPop (persons) | 42,428.1 | 42,428.1 | +0.0 | Conserved (exact pixel allocation) |
| GHSL (persons) | 84,500.5 | 84,500.6 | +0.1 | Conserved (exact pixel allocation) |
| Buildings | 25652 | 25652 | +0 | Chainage boundary assignment |
| Roads (km) | 243.82 | 243.82 | -0.00 | Chainage boundary assignment |

---

## 4. Operational HADR Response Priority Zones — Non-Overlapping Exclusive Sectors

**Ranking:** `OPERATIONAL_SCREENING_PRIORITY_ORDER` — strictly deterministic, NO weighted scores:
1. Maximum hazard class (H6 > H5 > H4 > H3)
2. Earliest wave arrival time (ascending)
3. WorldPop 2020 exposed population (descending, PRIMARY dataset only)

| Rank | Zone | Sector / Locality | Max Hazard | CWC Vulnerability | Earliest Arrival | WorldPop (PRIMARY) | GHSL (CROSS_CHECK) | Buildings | H5/H6 Bldgs | Roads (km) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | `ZONE_01` | Bhavanisagar | **H6** | All building types considered vulnerable to failure | 0.00 hr | 4,601.4 | 9,405.7 | 5,050 | 4,797 | 19.80 |
| **2** | `ZONE_02` | Sathyamangalam | **H6** | All building types considered vulnerable to failure | 2.00 hr | 8,856.2 | 11,387.7 | 6,140 | 5,466 | 59.23 |
| **3** | `ZONE_03` | Kodiveri | **H6** | All building types considered vulnerable to failure | 4.17 hr | 11,220.5 | 47,728.8 | 8,681 | 7,442 | 83.02 |
| **4** | `ZONE_04` | Gobichettipalayam | **H6** | All building types considered vulnerable to failure | 6.00 hr | 7,094.0 | 14,381.5 | 4,742 | 3,896 | 59.02 |
| **5** | `ZONE_05` | Kalingarayanpalayam | **H6** | All building types considered vulnerable to failure | 8.00 hr | 5,691.3 | 753.2 | 376 | 248 | 5.62 |
| **6** | `ZONE_06` | Bhavani | **H6** | All building types considered vulnerable to failure | 9.50 hr | 4,964.7 | 843.7 | 663 | 623 | 17.12 |


---

## 5. Scientific Limitations

1. **Screening hydraulic model:** 30m SRTM terrain; does not resolve micro-topographic defences.
2. **Population estimates:** Modelled gridded disaggregations — interpret as sensitivity range, not field surveys.
3. **Building vulnerability:** H5/H6 buildings identified per CWC CDSO_GUD_DS_09_v1.0 as "vulnerable to structural damage / failure". **Buildings are NOT assumed destroyed, collapsed, or failed** without structural engineering assessment.
4. **Bridge and road status:** `HYDRAULICALLY_EXPOSED_ROAD_SEGMENT` / `BRIDGE_HYDRAULIC_EXPOSURE_SCREENING`. NOT assumed closed or failed.
5. **Life loss / monetary loss:** `NOT_IMPLEMENTED`.
