# JalRakshak-HD: Final Scientific Benchmark Table

| Capability / Dimension | JalRakshak-HD Implementation | Technical Evidence & Metrics | Scientific Limitation |
| :--- | :--- | :--- | :--- |
| **Terrain Modeling** | NASA SRTM 30m Global DEM with HydroSHEDS river burn-in | Conditioned $818.37\text{ km}^2$ domain; zero elevation sinks; sub-pixel CRS alignment | Lacks submerged channel bathymetry beneath water surface |
| **Far-Field Hydrodynamics** | D-Flow Flexible Mesh 2D (Delft3D FM) | Finite-volume SWE; $181$ frames ($108,000\text{ s}$); Max depth $22.02\text{ m}$; Max vel $11.79\text{ m/s}$; Mass residual $0.0052\%$ | Calibrated uniform roughness ($n=0.035$); ignores culvert bypasses |
| **Near-Field Hydrodynamics** | DualSPHysics 3D Smoothed Particle Hydrodynamics | $10,982$ Lagrangian particles; $600\text{ s}$; Max velocity $34.78\text{ m/s}$; Front reach $1,280.41\text{ m}$ | Particle resolution constrained; decoupled from 2D mesh |
| **Breach Physics** | Empirical Froehlich (2008) Formulations | $B_{\text{avg}} = 219.28\text{ m}$; $t_f = 14,095.59\text{ s}$; $Q_{\text{peak}} = 18,742.38\text{ m}^3/\text{s}$; Volume $780.50\text{ MCM}$ | Empirical statistical uncertainty ($\pm 25$–$35\%$) |
| **Consequence Assessment (HADR)** | Non-overlapping sectoral exposure overlay | WorldPop: $42,428$; GHSL: $84,501$; Buildings: $25,652$; Roads: $243.82\text{ km}$; Bridges: $20$; Facilities: $13$ | Dasymetric statistical disaggregation; not census door-to-door |
| **Earth Observation (EO)** | Copernicus Sentinel-1 SAR backscatter thresholding | Nov 2021 historical flood baseline ($1.19\text{ km}^2$ new inundation detected) | $6$–$12$ day orbital revisit latency; not continuous real-time |
| **Multi-Site Portability** | Configuration-driven architecture | Hirakud Dam onboarded ($2,367.43\text{ km}^2$ domain, $5,818\text{ MCM}$ NRLD storage, $Q_{\text{peak}} = 65,163.63\text{ m}^3/\text{s}$) | Production 2D/3D solvers not executed for Hirakud |
| **Offline Resilience** | Local NASA SRTM hillshade raster & vector caching | Fully operational Leaflet GIS command center without internet access | Online basemap tiles unavailable when disconnected |
