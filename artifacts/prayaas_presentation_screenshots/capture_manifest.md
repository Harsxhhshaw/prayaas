# PRAYAAS — SIH26191 Presentation Screenshot Capture Manifest

**Capture Date/Time:** 2026-09-30 03:15:00 IST  
**Environment:** Local / Demo Evaluation Environment  
**Repository Path:** `c:\Users\Roshni\Pictures\Screenshots\PRAYAAS`  
**Git Remote:** `https://github.com/Harsxhhshaw/prayaas.git`  
**Git Branch:** `main`  
**Git Commit:** `1d0b9209ae26c2d6c6625951afb3332f78ea6855`  
**Commit Message:** `chore(freeze): final demo and github publish freeze`  
**Viewport:** 1920 × 1080 (Desktop), 100% Zoom  
**Services Running:**
- Backend: FastAPI on `http://127.0.0.1:8000` (Python 3.12, Uvicorn)
- Frontend: Vite + React on `http://127.0.0.1:5173` (Node.js v22)

---

## 1. Verified Screenshot Inventory

| # | Filename | View Description | Target Entity / Context | Key Visible Metrics & Statuses |
|---|---|---|---|---|
| 1 | `01_command_centre.png` | Main GIS Command Centre | Chamoli District Study Catchment | Full workstation interface, active layer management drawer (Hazard, Exposure, Red Zones, Relocation Strategy), topographic map controls, study bounds |
| 2 | `02_raini_assessment.png` | Habitation Risk Assessment Modal | Raini Settlement (`HAB-002`) | Risk Level: **PERMANENT RED** (Composite Risk: **87.0/100**), Primary Driver: Landslide (Slope >42°, toe-cutting instability), Population: **1,256**, 5-Year Trajectory: **+29**, Confidence: **82%** |
| 3 | `02b_raini_risk_overview.png` | Comprehensive Habitation Risk Inspector | Raini Settlement (`HAB-002`) | Full-screen detail showing Multi-Hazard Breakdown (Landslide 87, Flash Flood 65, Seismic 72), Household Count: 314, Readiness Cap: $\le 55.0$ |
| 4 | `03_candidate_discovery_map.png` | Candidate Discovery & Feasibility Layer | Chamoli Feasible Mask ($\le 25^\circ$) | Discovery Run Badge: `Found 2 contiguous candidate parcels (>=2.0 ha)`, Top Suitability: **84.5/100**, Relocation Need: **71.9/100**, Reception Readiness: **55.0/100** (Moderate Readiness Review) |
| 5 | `04_candidate_detail.png` | Candidate Site Inspection Modal | Chamoli Town Extension (`RS-002`) | Suitability: **78/100**, Carrying Capacity: **6,200 persons**, Area: **62 ha**, Elevation: **1,050 m**, Hazard Buffer: **12.3 km**, Utilities: Road/Water/Grid Connected, Status: **VERIFIED** |
| 6 | `05_candidate_sites_inventory.png` | Candidate Relocation Sites Table | District Candidate Inventory (`/candidate-sites`) | Full tabular inventory of benchmark reception sites (`RS-001` through `RS-006`), suitability scores (68–84/100), capacities (2,400–6,200), slope, distance, verification states |
| 7 | `07_relocation_priority_matrix.png` | Relocation Priority Matrix | 13 Red Zone Habitations (`/relocation-priority`) | Prioritization tiers (Immediate, Short-term, Medium-term), risk scores (76–87/100), displaced populations, designated relocation sites, phased timelines |
| 8 | `08_scenario_lab_workspace.png` | Multi-Hazard Scenario Lab | Parametric Stress Simulator (`/scenario-lab`) | Deterministic scenario matrix: Baseline, Water Stress, Population Surge, Road Outage, Candidate Outage, Infrastructure Upgrade |
| 9 | `09_digital_twin_3d_workspace.png` | 3D Digital Twin Simulation | Physics & Sensor Workspace (`/digital-twin`) | 8-dimension infrastructure and environmental capacity limits evaluation under stressed scenarios |
| 10 | `10_evidence_layers_pipeline.png` | Data Pipeline & Evidence Feeds | Scientific Ingestion Hub (`/data-sources`) | Primary telemetry feeds, derived analytical evidence layers (DEM, Slope, Aspect, Road Distance, Fault Line Proximity, Stream Drainage Buffer) |

---

## 2. Current Implementation Status (Tasks 6 to 10)

### Task 6: Feasible Land Mask & Topology-Driven Candidate Discovery
- **Status:** **COMPLETE & FROZEN**
- **Algorithm:** Multi-criteria raster mask filtering out slope $>25^\circ$, river buffers ($<100\text{ m}$), reserve forest boundaries, and active landslide zones.
- **Topology Segmentation:** Region-growing algorithm driven by suitability cores and watershed ridge topology rather than arbitrary area truncation.
- **Frozen Run:** `CDR-8E12008ADCC0` produced 2 contiguous modeled candidate parcels with top suitability $84.5/100$.

### Task 6.5: Honest Governance & Readiness Evaluation
- **Status:** **COMPLETE & FROZEN**
- **Readiness Matrix:**
  - Relocation Need: **71.9 / 100**
  - Reception Readiness: **55.0 / 100** (capped at 55.0)
  - Readiness Classification: `MODERATE_READINESS_REVIEW` (neutral classification; unsupported `READY_FOR_EXECUTION` was purged)
  - Active Blockers: `FIELD_VERIFICATION_PENDING_ON_RECEPTION_SITES`, `CARRYING_CAPACITY_INSUFFICIENT_EVIDENCE`.

### Task 7: 8-Dimension Carrying Capacity & Data Honesty
- **Status:** **COMPLETE & FROZEN (Backend Engine)**
- **Dimensions Audited:** Housing, Water, Sanitation, Healthcare, Education, Transport, Utilities, Environment.
- **Evidence Provenance:** Every metric strictly classified under evidence tiers (`OBSERVED`, `PUBLIC_VERIFIED`, `MODELED`, `PLANNING_ASSUMPTION`, `DEMO`, `UNKNOWN`).
- **Data Honesty:** Unsupported claims (such as fabricated PHC Pipalkoti 30 beds or exact feeder headroom) removed; real government-standard planning assumptions applied.

### Task 8: Multi-Site Relocation Optimization (MILP)
- **Status:** **COMPLETE & FROZEN (Backend Engine)**
- **Solver:** Mixed-Integer Linear Programming (MILP) optimizing:
  - Plan A: Proximity / Minimum Displacement Distance
  - Plan B: Maximum Environmental & Geotechnical Suitability
  - Plan C: Balanced Multi-Objective (Suitability + Proximity + Infrastructure Headroom)
- **Candidate Pool:** Strictly constrained to final discovery run `CDR-8E12008ADCC0`. Benchmark `DEMO` sites are excluded by default in production mode.

### Task 9: Digital Twin & Scenario Lab Robustness
- **Status:** **COMPLETE & FROZEN (Engine & Lab UI)**
- **Scenario Stress Testing:** 6 standardized stress scenarios (Baseline, Water Stress −20%, Population Surge +25%, Road Outage, Candidate Outage, Infrastructure Delay).
- **Semantics:** Critical UNKNOWN services prevent a scenario from receiving a `PASS` rating. Utilization $>100\%$ on any critical dimension results in `FAIL`.

### Task 10: Field Evidence, Satellite Monitoring & Governance Dossier
- **Status:** **COMPLETE & FROZEN**
- **Field Evidence Workflow:** Mobile inspection intake with cryptographic hash validation, GPS EXIF verification, and role-based officer sign-off.
- **Satellite & Change Monitoring:** Optical/NDVI change detection and surface observation schema.
- **Decision Dossier:** Automated export of end-to-end relocation evidence pack.

---

## 3. Test & Verification Results

During the current freeze audit, tests and builds were run directly:
- **Backend Test Suite:** `133 passed, 0 failed, 0 skipped` (Command: `python -m pytest backend/tests/ -q`)
  - Task 1–5: 95 tests passed
  - Task 6–7: 21 tests passed
  - Task 8–9: 13 tests passed
  - Task 10: 4 tests passed
- **Frontend Type Check:** `PASS` (`tsc --noEmit`)
- **Frontend Production Build:** `PASS` (`vite build`, zero errors)
- **Git Working Tree:** `100% clean` matching commit `1d0b920` on `main`.

---

## 4. Discrepancy & Evolution Analysis

1. **Raini Population (Census vs Core Displacement Subset):**
   - In `02_raini_assessment.png` and backend optimization runs, Raini settlement (`HAB-002`) population is recorded as **1,256 persons** (314 households) representing the total census population of the revenue village.
   - In `07_relocation_priority_matrix.png`, the tabular view shows a displaced population of **380 persons** (95 households), which represents the immediate catastrophic hazard zone (Ward 1–3) designated for urgent Phase 1 relocation.
2. **Benchmark Pre-seeded Sites vs Modeled Discovered Parcels:**
   - The frontend `/candidate-sites` table displays the pre-seeded benchmark sites (`RS-001` to `RS-006`) used during early platform prototyping.
   - The backend candidate discovery engine (`CDR-8E12008ADCC0`) generates dynamic, polygon-segmented modeled parcels (`PARCEL-F350766B5739` and `PARCEL-84F7EDFCF6A8`) with steep slope cutoffs ($\le 25^\circ$).
   - Both are preserved consistently: benchmark sites are explicitly tagged as `DEMO`/`BENCHMARK` in the database, while newly discovered sites are tagged as `MODELED`.

---

## 5. Unavailable Frontend Views & Technical Rationale

Per the strict instructions not to construct mockups or alter application code, the following requested views could not be captured as standalone frontend screens because their data is currently surfaced via the backend REST API:

1. **`05_capacity_evidence.png` (8-Dimension Carrying Capacity Breakdown):**
   - *Backend Status:* Implemented at `/api/candidate-sites/{id}/carrying-capacity`.
   - *Frontend Status:* The frontend displays candidate metadata (suitability, capacity, slope, area, utilities) in the modal and inventory table, but does not have a dedicated 8-column carrying capacity matrix view.
2. **`06_capacity_stress.png` (Water −20% Stress Result):**
   - *Backend Status:* Implemented at `/api/candidate-sites/{id}/carrying-capacity/stress-test`.
   - *Frontend Status:* Interactive stress sliders exist in `/scenario-lab` (`08_scenario_lab_workspace.png`), but the specific carrying-capacity stress outcome table is an API endpoint.
3. **`07_allocation_result.png` (Raini Plan A/B/C MILP Allocation Breakdown):**
   - *Backend Status:* Implemented at `/api/habitations/HAB-002/relocation-optimization`.
   - *Frontend Status:* The platform displays the master settlement priority table at `/relocation-priority` (`07_relocation_priority_matrix.png`), while single-habitation MILP candidate allocation results are served via JSON responses.
4. **`08_robustness_results.png` (Digital Twin 6-Scenario Pass/Fail Summary):**
   - *Backend Status:* Implemented at `/api/relocation-plans/{id}/robustness-evaluation`.
   - *Frontend Status:* The scenario lab workspace (`08_scenario_lab_workspace.png`) and 3D terrain simulation (`09_digital_twin_3d_workspace.png`) render the interactive controls and terrain physics, whereas the batch pass/fail robustness matrix is exposed as an analytical API.
