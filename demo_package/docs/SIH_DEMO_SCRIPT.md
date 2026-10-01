# JalRakshak-HD: SIH Jury Demonstration Script (5–7 Minutes)

## Demonstration Opening (0:00 – 0:30)
> **Presenter:** "Respected Jury Members, welcome to JalRakshak-HD. JalRakshak-HD is a configuration-driven, multi-site dam-break screening and GIS decision-support platform designed to bridge the gap between heavy hydrodynamic numerical simulation and frontline emergency response.
>
> What you are viewing right now is the real geographic environment of Bhavanisagar Dam in Tamil Nadu — displaying real OpenStreetMap roads, settlements, reservoir boundaries, river centerline, bridge crossings, and NASA SRTM terrain — with the actual output of our 2D D-Flow FM hydrodynamic numerical simulation overlaid directly on top."

---

## 1. Real Geographic Context & Basemap Stacking (0:30 – 1:15)
* **Action:** Click `[ ⛶ Full Study Area ]` and pan smoothly along the Lower Bhavani corridor.
* **Talking Points:**
  * "Notice that this is not a blank scientific canvas or an artificial bounding box. The basemap is OpenStreetMap standard, displaying actual town names like Sathyamangalam, Alathucombai, and Punjaipuliampatti."
  * "The reservoir polygon is derived from JRC Global Surface Water at Full Reservoir Level ($280.42\text{ m MSL}$), and the dam point is anchored at the exact verified crest coordinate ($11.47083^\circ\text{N}, 77.11389^\circ\text{E}$)."
  * "All 20 mapped bridge crossings have exact coordinates, highway identifiers, and modeled flood arrival times."

---

## 2. 181-Frame D-Flow FM Solver Playback (1:15 – 2:30)
* **Action:** Hit `[ ▶ Play ]` on the timeline scrubber or drag the slider from `T+00:00` to `T+30:00`.
* **Talking Points:**
  * "This simulation is powered by the production D-Flow FM 2D Flexible Mesh solver across an $818.37\text{ km}^2$ domain with $46,830$ mesh cells."
  * "There is zero synthetic interpolation or CSS trickery. Every frame represents a real $600\text{-second}$ solver timestep from the $108,000\text{-second}$ ($30\text{-hour}$) numerical run."
  * "The dry cells are $100\%$ transparent, so you can observe the flood wave advancing downstream through real agricultural corridors, highway networks, and settlement boundaries."
  * "Our mass balance achieves $0.0052\%$ relative residual error, validating numerical conservation."

---

## 3. Interactive Point Query & Bridge Risk Inspection (2:30 – 3:15)
* **Action:** Click on a bridge marker (e.g., Bridge BR-966247490) and click anywhere inside the flood plain.
* **Talking Points:**
  * "When we click any point on the map, our backend samples multi-raster layers in real time, returning exact peak water depth ($22.02\text{ m}$ toe max), flow velocity ($11.79\text{ m/s}$ max), arrival time, and Central Water Commission hazard class."
  * "Clicking outside the model domain returns `Outside model extent` — never fake zero values."
  * "Inspecting the bridge crossing displays the road name, hazard class ($H_5$ extreme risk), arrival time ($1.25\text{ hr}$), and assigned response sector."

---

## 4. HADR Consequence & Vulnerability Screening (3:15 – 4:00)
* **Action:** Switch to `[ ⚠ HADR Exposure ]` mode tab.
* **Talking Points:**
  * "JalRakshak-HD translates raw hydraulics into actionable humanitarian insights using dual population baselines: WorldPop ($42,428$ exposed) and GHSL ($84,500$ exposed)."
  * "We do not average these conflicting datasets because they measure different metrics — WorldPop measures residential density while GHSL measures built structure capacity. We present both transparently."
  * "$25,652$ buildings are mapped, with $22,472$ located in extreme $H_5/H_6$ structural damage zones. The corridor is partitioned into 6 disjoint response sectors ($Z_1$ to $Z_6$) prioritized by flood arrival speed."

---

## 5. DualSPHysics Near-Field & Cross-Solver Analysis (4:00 – 4:40)
* **Action:** Switch to `[ 〜 Near-Field SPH ]` mode tab.
* **Talking Points:**
  * "In the immediate dam toe zone ($0\text{--}1,500\text{ m}$), where 3D turbulence and vertical acceleration violate shallow-water assumptions, we ran DualSPHysics meshless particle hydrodynamics with $10,982$ particles."
  * "We honestly report our cross-solver comparative findings: water depth trends are partially consistent, but velocity diverges due to SPH resolution and lack of lateral spreading in 2D."
  * "We explicitly state that direct coupling is not yet implemented — representing scientific honesty rather than black-box claims."

---

## 6. Earth Observation Benchmark & NRT Monitoring (4:40 – 5:20)
* **Action:** Switch to `[ 🛰 Earth Observation ]` mode tab.
* **Talking Points:**
  * "We validated our GIS domain against historical Sentinel-1 SAR C-Band radar imagery from the August 2019 monsoon flood ($1.115\text{ km}^2$ observed new water)."
  * "Our automated Sentinel-1 pipeline ingests new satellite passes every 6–12 days to monitor baseline reservoir extent and monsoonal anomalies."

---

## 7. Second-Site Generalization & Portability (5:20 – 6:00)
* **Action:** Select `[ Hirakud Dam ▼ ]` in the top header site dropdown.
* **Talking Points:**
  * "To prove any-dam / any-river architecture, we onboarded Hirakud Dam on the Mahanadi River in Odisha entirely through declarative YAML configs (`dam.yaml`, `breach.yaml`)."
  * "The system automatically reprojected the domain to UTM Zone 44N, delineated the terrain model, reservoir boundary, and river reach."
  * "Crucially, the system refuses to show fake simulation results — displaying a prominent notice that production simulation has not been executed."

---

## 8. Offline Demonstration & Conclusion (6:00 – 6:30)
* **Action:** Click `[ Terrain (Offline) ]` in the basemap selector.
* **Talking Points:**
  * "If internet connectivity fails at the evaluation booth, JalRakshak-HD operates $100\%$ offline using local NASA SRTM 30m hillshade rasters and local vector caches."
  * "In conclusion, JalRakshak-HD provides a reproducible, multi-site, scientifically grounded dam safety screening platform ready for disaster management evaluation. Thank you!"
