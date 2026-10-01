# JalRakshak-HD (v1.0-SIH)

**Configuration-Driven Multi-Site Dam-Break Screening & GIS Decision-Support Platform**  
*Developed for Smart India Hackathon (SIH PS 26161)*

---

## 🌊 Overview

**JalRakshak-HD** is an open-source, configuration-driven computational screening platform designed for high-resolution dam-break inundation modeling, structural splash assessment, humanitarian consequence screening, and satellite-based flood validation.

- **Primary Validation Site:** Bhavanisagar Dam / Lower Bhavani River Basin, Tamil Nadu ($818.37\text{ km}^2$)
- **Generalization Site:** Hirakud Dam / Mahanadi River Basin, Odisha ($2,367.43\text{ km}^2$)
- **Core Solvers:** Deltares D-Flow Flexible Mesh 2D + DualSPHysics 3D Particle Hydrodynamics

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ and npm
- Windows PowerShell / Command Prompt

### One-Click Launch
To launch both the FastAPI backend and React GIS frontend simultaneously:

```cmd
START_DEMO.bat
```
*(Or in PowerShell: `.\start_jalrakshak.ps1`)*

- **Backend API:** `http://localhost:8000` (Docs: `http://localhost:8000/docs`)
- **Web GIS Command Centre:** `http://localhost:5173`

---

## 🗺️ Key Features

1. **2D Flexible Mesh Hydrodynamics (D-Flow FM):**
   - 30-hour ($108,000\text{ s}$) hydrodynamic simulation with $181$ continuous frames ($600\text{ s}$ resolution).
   - Peak depth ($22.02\text{ m}$) and peak velocity ($11.79\text{ m/s}$) tracking with verified mass conservation ($0.0052\%$ residual).
2. **3D Smoothed Particle Hydrodynamics (DualSPHysics):**
   - Lagrangian 3D simulation ($10,982$ particles) resolving dam-face splash, overturning jets, and near-field impact pressures ($0$–$600\text{ s}$).
3. **HADR Consequence Screening:**
   - Multi-source population exposure overlay (WorldPop: $42,428$; GHSL: $84,501$).
   - Infrastructure impact screening ($25,652$ buildings, $243.82\text{ km}$ roads, $20$ mapped bridges, $13$ critical facilities) across 9 response sectors.
4. **Earth Observation & Sentinel-1 Benchmarking:**
   - ESA Copernicus Sentinel-1 C-band SAR backscatter flood extent extraction for all-weather flood validation.
5. **Multi-Site Portability Framework:**
   - Declarative `site_config.yaml` architecture enabling seamless onboarding of new dams (demonstrated on Hirakud Dam).
6. **Zero-Dependency Offline Resilience:**
   - Automatic graceful fallback to local NASA SRTM 30m hillshade rasters and local GeoJSON layers when internet connectivity is lost.

---

## 📊 Scientific Truth Summary (Bhavanisagar Dam)

| Metric | Authoritative Value | Unit | Source / Method |
| :--- | :--- | :--- | :--- |
| **Reservoir Storage at FRL ($V_w$)** | $780.50$ | $\text{MCM}$ | CWC NRLD 2023 / TN WRD |
| **Dam Structural Height ($H_{\text{dam}}$)** | $40.0$ | $\text{m}$ | CWC NRLD 2023 |
| **Full Reservoir Level (FRL)** | $280.20$ | $\text{m}$ | TN WRD Official Datum |
| **Average Breach Width ($B_{\text{avg}}$)** | $219.28$ | $\text{m}$ | Froehlich (2008) Empirical Regression |
| **Breach Formation Time ($t_f$)** | $14,095.59$ | $\text{s}$ | Froehlich (2008) Empirical Regression |
| **Peak Breach Discharge ($Q_{\text{peak}}$)** | $18,742.38$ | $\text{m}^3/\text{s}$ | Parametric Hydrograph Peak |
| **Hydrograph Volume** | $780.50$ | $\text{MCM}$ | Mass Balance Verified |
| **D-Flow Model Domain Area** | $818.37$ | $\text{km}^2$ | NASA SRTM 30m / HydroSHEDS |
| **Maximum Inundated Area** | $101.29$ | $\text{km}^2$ | D-Flow FM 2D Wet Cells ($d > 0.05\text{m}$) |
| **Maximum Water Depth** | $22.02$ | $\text{m}$ | D-Flow FM 2D Simulation |
| **P95 Water Depth** | $12.72$ | $\text{m}$ | D-Flow FM 2D Simulation |
| **Maximum Flow Velocity** | $11.79$ | $\text{m/s}$ | D-Flow FM 2D Simulation |
| **P95 Flow Velocity** | $4.27$ | $\text{m/s}$ | D-Flow FM 2D Simulation |
| **Simulation Duration / Frames** | $108,000 / 181$ | $\text{s} / \text{frames}$ | $600\text{ s}$ Frame Interval |
| **DualSPHysics Particles / Duration** | $10,982 / 600$ | $\text{particles} / \text{s}$ | SPH 3D Near-Field Solver |
| **WorldPop Exposed Population** | $42,428$ | $\text{persons}$ | WorldPop 2020 UN-Adjusted |
| **GHSL Exposed Population** | $84,501$ | $\text{persons}$ | Copernicus GHSL 2023 |
| **Exposed Buildings / Roads** | $25,652 / 243.82$ | $\text{count} / \text{km}$ | OpenStreetMap / Google Open Buildings |
| **Mapped Bridges / Facilities** | $20 / 13$ | $\text{count}$ | OpenStreetMap Overpass API |

---

## ⚙️ Running Automated Validation Suite

To verify system integrity, numerical consistency, and scientific honesty:

```powershell
python scripts/preflight_demo.py
python scripts/validate_final_scientific_values.py
python scripts/audit_final_claims.py
python scripts/validate_real_map.py
python scripts/validate_dashboard.py
python scripts/validate_m11_generalization.py
python scripts/validate_m12_final.py
python -m pytest backend/tests -v
```

---

## ⚠️ Known Scientific Limitations & Research Disclaimer

1. **Screening Prototype:** JalRakshak-HD is a research and screening prototype designed for rapid consequence analysis. It is **not** a government-certified statutory emergency warning system.
2. **Hypothetical Breach Scenario:** Inundation maps represent a simulated overtopping failure at FRL based on empirical regression equations (Froehlich 2008, $\pm 25$–$35\%$ uncertainty).
3. **Decoupled Solvers:** DualSPHysics (3D) and D-Flow FM (2D) are parameterized from the same geometry but are not dynamically boundary-flux coupled.
4. **DEM & Bathymetry:** NASA SRTM 30m terrain lacks submerged river bathymetry and micro-drainage features.
5. **Satellite Latency:** Sentinel-1 provides periodic orbital revisit observations ($6$–$12\text{ days}$) for post-event benchmarking, not real-time video surveillance.
