# JalRakshak-HD

**Hydrodynamic Dam-Break & HADR Intelligence Platform**  
*Smart India Hackathon 2026 — Problem Statement: SIH26161*  
*“Dam Break Inundation Modelling Using Hydrodynamic Modelling of any River”*

---

## 🌊 1. Problem Statement

Dam failures and catastrophic reservoir releases represent high-consequence hydraulic hazards capable of causing severe loss of life, devastating downstream communities, and wiping out critical civil infrastructure within hours. Traditional dam-break emergency action plans (EAPs) frequently suffer from:
- **Static & Coarse Inundation Maps:** Outdated 1D hydraulic profiles that fail to capture 2D terrain inundation dynamics, transverse velocities, and complex flood fronts.
- **Disconnected HADR Intelligence:** Hydrodynamic models rarely integrate with real-time exposure databases (buildings, population densities, road network cutoffs, hospitals, bridges).
- **Near-Field Structural Blindspots:** Shallow-water approximations fail to resolve 3D turbulence, violent splash-up, and localized impact pressures on dam faces and immediately adjacent structures.
- **Lack of Multi-Site Adaptability:** Hardcoded single-dam workflows that cannot be generalized to other river basins across India without extensive manual refactoring.

**JalRakshak-HD** addresses Problem Statement **SIH26161** by providing a configuration-driven, fail-honest hydrodynamic screening and humanitarian decision-support platform designed to model breach hydrodynamics, calculate dynamic inundation propagation, quantify infrastructure exposure, and support civil defense agencies with actionable evacuation intelligence.

---

## 💡 2. Solution Workflow

```
[Dam Geometry & Hydraulic Scenario]
                 │
                 ▼
[Empirical Breach Parameterization (Froehlich / MacDonald-Langridge-Monopolis)]
                 │
                 ▼
[Breach Outflow Hydrograph Synthesis Q(t)]
                 │
                 ├──────────────────────────────────────┐
                 ▼                                      ▼
[3D SPH Near-Field Modeling (DualSPHysics)]   [2D Flexible Mesh Hydrodynamics (D-Flow FM)]
(Near-dam splash, wall pressure, jet front)   (Downstream water depth, velocity, arrival time)
                 │                                      │
                 └───────────────────┬──────────────────┘
                                     │
                                     ▼
                      [Flood Hazard Classification (H1–H6)]
                                     │
                                     ▼
                 [HADR Consequence & Exposure Screening]
                 (Population, Buildings, Road Corridors, Critical Assets)
                                     │
                                     ▼
                [GIS Command Centre & Decision Support Dashboard]
```

---

## ⚡ 3. Core Prototype Capabilities

The current working prototype demonstrates:

- **Parametric Dam-Break Modeling:** Automated calculation of breach formation time ($t_f$), average breach width ($B_{\text{avg}}$), and peak discharge ($Q_{\text{peak}}$) using peer-reviewed empirical regressions (Froehlich 2008, MacDonald & Langridge-Monopolis 1984, CWC guidelines).
- **Outflow Hydrograph Synthesis:** Verified mass-conserving hydrograph $Q(t)$ generation with exact reservoir storage balance verification ($780.50\text{ MCM}$ at Bhavanisagar FRL).
- **2D Hydrodynamic Flood Routing:** Flexible mesh simulation tracking flood propagation over $30\text{ hours}$ ($108,000\text{ s}$) with $181$ continuous timesteps ($600\text{ s}$ resolution), outputting spatial depth, velocity vectors, and flood front arrival times.
- **3D Particle Near-Field Modeling:** DualSPHysics Lagrangian modeling ($10,982$ fluid particles) resolving near-field hydrodynamics, splashing fronts, and force distribution on the spillway face ($0$–$600\text{ s}$).
- **Humanitarian Assistance & Disaster Relief (HADR) Exposure Analysis:**
  - Multi-tier population exposure quantification using high-resolution gridded datasets (**WorldPop 2020:** $42,428$ exposed; **Copernicus GHSL 2023:** $84,501$ exposed).
  - High-resolution infrastructure screening ($25,652$ buildings via Google Open Buildings / OSM, $243.82\text{ km}$ affected road segments, $20$ bridges, $13$ critical facilities).
  - Delineation of 9 prioritized HADR operational response sectors from near-dam high-hazard zones to downstream settlements.
- **Satellite Earth Observation Benchmarking:** ESA Copernicus Sentinel-1 C-band SAR backscatter flood extraction pipeline for all-weather satellite verification of observed historical inundation.
- **Multi-Site Architecture:** Declarative, schema-validated site onboarding (`site_config.yaml`) demonstrated on two distinct basins:
  - **Bhavanisagar Dam (Tamil Nadu):** Primary fully modeled and validated scenario ($818.37\text{ km}^2$ study area).
  - **Hirakud Dam (Odisha):** Generalization test site demonstrating automated basin delineation, geometry ingestion, and parameterization ($2,367.43\text{ km}^2$ study area).
- **Zero-Dependency Offline Operation:** Built-in raster overlays, GeoJSON caches, and NASA SRTM 30m hillshades allowing full operational GIS dashboard functionality during disconnected field operations.

---

## 🏗️ 4. System Architecture

### Architectural Components

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           JALRAKSHAK-HD PLATFORM                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  [DATA LAYER]                                                             │
│  ├── Elevation & Terrain: NASA SRTM 30m / HydroSHEDS                     │
│  ├── Engineering: CWC National Register of Large Dams (NRLD 2023)        │
│  ├── Exposure: Google Open Buildings, OpenStreetMap, WorldPop, GHSL      │
│  └── Earth Observation: ESA Copernicus Sentinel-1 SAR (GEE / Local)      │
│                                                                           │
│  [COMPUTATIONAL & SCREENING ENGINE]                                       │
│  ├── Breach & Hydrograph: Froehlich & MacDonald-Monopolis Synthesizer     │
│  ├── 2D Hydraulic Solver: Deltares D-Flow Flexible Mesh (DFlowFM)        │
│  ├── 3D Particle Solver: DualSPHysics Lagrangian SPH                      │
│  └── Hazard Classifier: Australian Disaster Resilience Handbook 7 (H1–H6)│
│                                                                           │
│  [BACKEND REST API (FastAPI)]                                             │
│  ├── Multi-Site Registry & Path Resolver (`/api/sites`)                   │
│  ├── Simulation Time-Series & Frame Streaming (`/api/simulation`)         │
│  ├── GIS Vector & Raster Layers (`/api/tiles`, `/api/gis`)                │
│  ├── HADR Impact Assessment (`/api/hadr`)                                 │
│  └── Data Lineage & Provenance Auditor (`/api/provenance`)                │
│                                                                           │
│  [GIS COMMAND CENTRE FRONTEND (React 18 + Vite + Leaflet)]                │
│  ├── Real-Time Simulation Playback & Scrubbing Controller                 │
│  ├── Multi-Layer GIS Map with Dynamic Hazard Severity Coloring            │
│  ├── Interactive Point-Click Hydraulic & Risk Inspector                   │
│  ├── Multi-Site Basin Switcher (Bhavanisagar / Hirakud)                   │
│  └── Humanitarian Logistics & Evacuation Priority Tab                     │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### Prototype Demonstrated vs. Full Deployment Architecture

| Aspect | Prototype Demonstrated (SIH 2026) | Full Production Deployment Target |
| :--- | :--- | :--- |
| **Solver Coupling** | Decoupled execution parameterized from unified site geometry | Automated bidirectional boundary coupling pipeline |
| **Execution Mode** | Pre-computed, verified 181-frame high-resolution time series | Real-time HPC cluster job queuing & on-demand solver runs |
| **Database** | Lightweight local file manifests + Optional PostGIS schema | Distributed PostgreSQL / PostGIS with live SCADA telemetry |
| **Satellite Ingestion** | Pre-processed Sentinel-1 SAR scenes + GEE scripts | Automated live Copernicus Hub webhook ingestion pipeline |
| **Multi-Site Scope** | Bhavanisagar (Fully simulated) + Hirakud (Configured & Parametric) | National inventory scaling across CWC major dam registry |

---

## 📡 5. Data Sources & Provenance

All data utilized in JalRakshak-HD originates from authentic, peer-reviewed, and official government or space agency repositories:

- **Dam Engineering & Reservoir Specs:** Central Water Commission (CWC) National Register of Large Dams (NRLD 2023) & Tamil Nadu Water Resources Department (TN WRD).
- **Elevation & Terrain:** NASA Shuttle Radar Topography Mission (SRTM) 30m Global DEM & USGS HydroSHEDS hydro-conditioned drainage network.
- **Land Cover & Roughness:** ESA WorldCover 10m global land cover dataset (Manning's $n$ calibrated per land use class).
- **Infrastructure & Assets:** OpenStreetMap (OSM) Overpass API (roads, bridges, waterways, medical centres, emergency services) & Google Open Buildings v3.
- **Population Exposure:** WorldPop 2020 UN-Adjusted 100m Spatial Demographics & European Commission Copernicus Global Human Settlement Layer (GHSL 2023).
- **Satellite Radar:** ESA Copernicus Sentinel-1 C-band Synthetic Aperture Radar (SAR) Ground Range Detected (GRD) backscatter imagery.

---

## 🛠️ 6. Technology Stack

### Frontend
- **Framework:** React 19 / Vite / TypeScript
- **Mapping & GIS:** Leaflet / React-Leaflet
- **Styling & UI:** TailwindCSS v4 / Lucide React Icons
- **Data Visualization:** Recharts

### Backend & API
- **Framework:** FastAPI / Uvicorn (Asynchronous REST API)
- **Data Validation & Settings:** Pydantic v2 / PyYAML / Python-Dotenv
- **Geospatial & Vector Processing:** GeoPandas / Shapely / PyProj / Rasterio
- **Scientific Computing & IO:** NumPy / SciPy / Pandas / NetCDF4 / Xarray / h5py
- **Spatial Database (Optional):** PostgreSQL / PostGIS (`psycopg`)

### Hydrodynamic Solvers Represented
- **2D Mesh Hydrodynamics:** Deltares Delft3D Flexible Mesh (D-Flow FM 2026.02)
- **3D Particle Hydrodynamics:** DualSPHysics v5.4 (Smoothed Particle Hydrodynamics)

---

## 🛡️ 7. Fail-Honest Scientific Verification Architecture

JalRakshak-HD implements a strict **Fail-Honest** design philosophy. Output claims are cryptographically and programmatically audited into four explicit verification tiers:

- 🟢 **VERIFIED:** Computationally executed, mass-conserved, and validated against authoritative criteria (e.g. Bhavanisagar $780.50\text{ MCM}$ reservoir volume conservation, 181-frame hydrodynamic propagation).
- 🟡 **ASSUMPTION:** Documented empirical or parametric engineering estimates (e.g. Froehlich 2008 breach geometry with $\pm 25\text{–}35\%$ uncertainty bounds).
- 🟠 **PARTIAL:** Baseline terrain, hydrologic routing, and parametric estimates derived, pending full solver meshing (e.g. Hirakud generalization site).
- 🔴 **BLOCKED / NOT-RUN:** Solvers or modules that have not been executed for a specific site are explicitly flagged as `NOT_RUN` in the UI and API rather than displaying fabricated or interpolated data.

---

## 📁 8. Project Structure

```
JalRakshak-HD/
├── VERSION                               # Release identifier (v1.0-SIH)
├── README.md                             # Comprehensive technical documentation
├── requirements.txt                      # Python dependencies
├── .env.example                          # Safe environment variable template
├── .gitignore                            # Comprehensive ignore rules
├── START_DEMO.bat                        # Windows 1-click startup batch script
├── start_jalrakshak.ps1                  # PowerShell launcher & port checker
│
├── backend/                              # FastAPI REST backend service
│   ├── app/
│   │   ├── main.py                       # FastAPI entrypoint & router mounts
│   │   ├── api/                          # Endpoints (simulation, hadr, gis, sites, reports)
│   │   ├── core/                         # Configuration & dynamic site path resolvers
│   │   ├── models/                       # Domain data models & schemas
│   │   ├── schemas/                      # Pydantic request/response schemas
│   │   └── services/                     # Breach physics, hazard logic & loaders
│   └── tests/                            # Pytest test suite (57/57 tests passing)
│
├── frontend/                             # React 19 + TypeScript + Vite GIS Dashboard
│   ├── src/
│   │   ├── components/                   # MapView, PlaybackControls, HADRPanel, SPHPanel, etc.
│   │   ├── hooks/                        # Custom animation and state hooks
│   │   ├── services/                     # API client interface layer
│   │   └── types/                        # TypeScript type definitions
│   ├── package.json                      # Node dependencies & build scripts
│   └── vite.config.ts                    # Vite bundler & API proxy configuration
│
├── sites/                                # Multi-site configuration directory
│   ├── bhavanisagar/                     # Primary demo site (Tamil Nadu)
│   │   ├── site.yaml                     # Site parameters & bounding box
│   │   ├── dam.yaml                      # Engineering dimensions & storage specs
│   │   ├── breach.yaml                   # Empirical breach calculations
│   │   ├── hydrology.yaml                # Catchment & inflow configuration
│   │   ├── model.yaml                    # Solver resolution & timestep settings
│   │   ├── monitoring.yaml               # Gauges & satellite observation specs
│   │   └── source_manifest.json          # Data provenance record
│   └── hirakud/                          # Generalization test site (Odisha)
│       └── [site, dam, breach, hydrology, model, monitoring configs]
│
├── configs/                              # Global project configuration
│   ├── paths.yaml                        # Base directory mappings & solver paths
│   └── project.yaml                      # Project metadata & default CRS
│
├── data/                                 # Spatial datasets & model inputs
│   ├── terrain/                          # Projected DEMs, slope & hillshades
│   ├── hydrology/                        # Hydroconditioned DEM & stream network
│   ├── hadr/                             # Buildings, roads & facility GPKGs
│   ├── gee/                              # Satellite SAR backscatter GeoTIFFs
│   ├── dflowfm/                          # D-Flow FM model setups & mesh files
│   └── hirakud/                          # Hirakud generalization inputs
│
├── docs/                                 # Engineering documentation & jury guides
│   ├── SIH_DEMO_SCRIPT.md                # 5-minute timed presentation script
│   ├── SIH_JURY_QA.md                    # 25+ jury scientific defense Q&A
│   ├── final_architecture.md             # System architecture documentation
│   ├── final_data_lineage.md             # Data lineage & provenance specification
│   ├── final_project_structure.md        # Comprehensive file tree description
│   └── data_provenance.md                # Detailed dataset origins & citations
│
├── demo_package/                         # Lightweight standalone demonstration bundle
│
├── outputs/                              # Validated outputs & dashboard assets
│   ├── dashboard/                        # Web-optimized simulation frames (181 PNGs), overlays, GeoJSONs
│   ├── reports/                          # Compliance tables & impact reports
│   └── validation/                       # Scientific truth manifests & audit matrices
│
├── scripts/                              # Automated data acquisition, modeling & validation scripts
│   ├── preflight_demo.py                 # System preflight validator
│   ├── validate_final_scientific_values.py # 33-point scientific consistency check
│   ├── audit_final_claims.py             # Scientific claim auditor
│   ├── validate_real_map.py              # Map projection & vector alignment tester
│   ├── validate_dashboard.py             # API endpoint integration test
│   ├── validate_m11_generalization.py    # Multi-site configuration integrity checker
│   └── validate_m12_final.py             # Master M12 release validation gate
│
└── solver_tests/                         # Benchmark & standalone test cases
    └── dflowfm_f34/                      # Deltares official F34 benchmark model
```

---

## 🚀 9. Installation & Setup

### Prerequisites
- **Python:** 3.10 to 3.12 (Python 3.12.3 verified)
- **Node.js:** v18 or later (v20+ recommended) & npm
- **Git:** Git 2.30+
- **OS:** Windows 10/11 (PowerShell / Command Prompt) or Linux

### 1. Clone the Repository
```bash
git clone https://github.com/vishalgokul504/JalRakshak---HD.git
cd JalRakshak---HD
```

### 2. Backend Setup
```bash
# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Linux/macOS: source .venv/bin/activate

# Install required Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration (Optional)
```bash
# Copy the environment template
copy .env.example .env
```
*(Default settings work out-of-the-box for local file-based offline demo mode without requiring external database or Google Earth Engine credentials).*

---

## ▶️ 10. Running the Application

### Option A: One-Click Startup (Recommended on Windows)
Simply double-click:
```cmd
START_DEMO.bat
```
*(Or in PowerShell: `.\start_jalrakshak.ps1`)*

This script automatically verifies port availability, starts the FastAPI backend on `http://127.0.0.1:8000`, starts the Vite frontend on `http://localhost:5173`, and opens the browser.

### Option B: Manual Startup

**Terminal 1 — Backend:**
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 🧪 11. Verification & Automated Testing

Run the automated scientific validation and test suites:

```powershell
# 1. Run all backend unit & integration tests (57 tests)
python -m pytest backend/tests -v

# 2. Run scientific consistency and data integrity checks
python scripts/validate_final_scientific_values.py
python scripts/validate_dashboard.py
python scripts/validate_m11_generalization.py
python scripts/validate_m12_final.py

# 3. Test frontend production build
cd frontend
npm run build
cd ..
```

---

## 🔬 12. Scientific Baseline Summary (Bhavanisagar Dam)

| Parameter | Value | Unit | Source / Validation Method |
| :--- | :--- | :--- | :--- |
| **Reservoir Storage at FRL ($V_w$)** | $780.50$ | $\text{MCM}$ | CWC NRLD 2023 / TN WRD Official |
| **Dam Height ($H_{\text{dam}}$)** | $40.0$ | $\text{m}$ | CWC NRLD 2023 |
| **Full Reservoir Level (FRL)** | $280.20$ | $\text{m MSL}$ | TN WRD Datum |
| **Average Breach Width ($B_{\text{avg}}$)** | $219.28$ | $\text{m}$ | Froehlich (2008) Empirical Regression |
| **Breach Formation Time ($t_f$)** | $14,095.59$ ($3.92\text{ hr}$) | $\text{s}$ | Froehlich (2008) Empirical Regression |
| **Peak Breach Discharge ($Q_{\text{peak}}$)** | $18,742.38$ | $\text{m}^3/\text{s}$ | Parametric Hydrograph Peak |
| **Hydrograph Conservation** | $780.50$ | $\text{MCM}$ | Mass Balance Verified ($0.00\%$ discrepancy) |
| **Study Area Domain** | $818.37$ | $\text{km}^2$ | NASA SRTM 30m / HydroSHEDS Delineation |
| **Max Inundated Extent** | $101.29$ | $\text{km}^2$ | D-Flow FM 2D Wet Cells ($d > 0.05\text{m}$) |
| **Maximum Water Depth** | $22.02$ | $\text{m}$ | D-Flow FM 2D Numerical Simulation |
| **Maximum Flow Velocity** | $11.79$ | $\text{m/s}$ | D-Flow FM 2D Numerical Simulation |
| **DualSPHysics 3D Particles** | $10,982$ | $\text{particles}$ | SPH Lagrangian Splash Simulation |
| **WorldPop Exposed Population** | $42,428$ | $\text{persons}$ | WorldPop 2020 UN-Adjusted Overlay |
| **GHSL Exposed Population** | $84,501$ | $\text{persons}$ | Copernicus GHSL 2023 Overlay |
| **Exposed Buildings** | $25,652$ | $\text{structures}$ | Google Open Buildings v3 & OSM |
| **Affected Road Corridors** | $243.82$ | $\text{km}$ | OpenStreetMap Highway Network |
| **Affected Bridges / Facilities** | $20 / 13$ | $\text{count}$ | OSM Overpass API Geocoded Entities |

---

## ⚠️ 13. Limitations & Research Scope

1. **Screening Prototype:** JalRakshak-HD is a research prototype developed for hydrodynamic consequence screening, risk zoning, and humanitarian planning. It is not an official statutory early warning broadcast system.
2. **Empirical Breach Uncertainty:** Breach formation parameters are derived from empirical regressions (Froehlich 2008), with inherent physical uncertainties ($\pm 25\text{–}35\%$).
3. **Decoupled 3D/2D Hydrodynamics:** DualSPHysics (3D particle solver for near-dam splash) and D-Flow FM (2D shallow water mesh for downstream routing) share unified initial geometry but operate as decoupled simulation domains in the prototype.
4. **Terrain Resolution:** Bathymetric channel geometry below the water surface is approximated based on NASA SRTM 30m terrain and HydroSHEDS drainage conditioning; localized riverbed scouring and micro-embankments may not be fully resolved.
5. **Satellite Latency:** Sentinel-1 SAR observations depend on orbital revisit periods ($6\text{–}12\text{ days}$) and serve as post-event or historical flood benchmarks rather than continuous real-time telemetry.

---

*Developed for the Smart India Hackathon 2026 — JalRakshak-HD Team.*
