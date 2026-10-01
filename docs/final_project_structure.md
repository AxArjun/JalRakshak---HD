# JalRakshak-HD: Project Directory Structure

```
JalRakshak-HD/
├── VERSION                               # Project version identifier (v1.0-SIH)
├── README.md                             # Comprehensive technical documentation & quickstart
├── START_DEMO.bat                        # One-click Windows launch script
├── start_jalrakshak.ps1                  # PowerShell safe startup orchestrator
│
├── backend/                              # FastAPI async backend service
│   ├── app/
│   │   ├── main.py                       # FastAPI entrypoint, CORS, and router registry
│   │   ├── api/                          # REST API endpoints (sites, sim, hadr, eo, etc.)
│   │   └── services/                     # Business logic and scientific data loaders
│   └── tests/                            # Comprehensive pytest test suite (53/53 tests passing)
│
├── frontend/                             # React 18 + Vite GIS Command Centre
│   ├── src/
│   │   ├── components/                   # MapView, PlaybackControls, HADRPanel, SPHViewer, etc.
│   │   ├── hooks/                        # Custom React state and animation hooks
│   │   ├── services/                     # API client interfaces
│   │   └── types/                        # TypeScript scientific interfaces
│   ├── package.json
│   └── vite.config.ts
│
├── sites/                                # Site definitions and spatial boundary configurations
│   ├── bhavanisagar/                     # Primary demo site (Tamil Nadu)
│   │   └── site_config.yaml
│   └── hirakud/                          # Generalization proof site (Odisha)
│       └── site_config.yaml
│
├── data/                                 # Authentic input datasets (SRTM, OSM, NRLD, Satellite)
│   ├── raw/
│   └── processed/
│
├── docs/                                 # Engineering and jury documentation
│   ├── SIH_DEMO_SCRIPT.md                # 5-7 minute timed demonstration script
│   ├── SIH_JURY_QA.md                    # 25+ question scientific defense guide
│   ├── final_architecture.md             # System architecture & data flow
│   ├── final_data_lineage.md             # End-to-end data provenance specification
│   └── final_project_structure.md        # This directory breakdown
│
├── outputs/                              # Validated simulation runs and verification artifacts
│   ├── dashboard/                        # Web-optimized GeoJSON, hillshades, and 181 PNG frames
│   ├── reports/                          # Benchmark tables, compliance, and final technical report
│   └── validation/                       # Authoritative truth manifests and audit logs
│       ├── final_scientific_truth_manifest.json
│       ├── m12_release_manifest.json
│       ├── m12_validation_matrix.csv
│       ├── m12_source_traceability.csv
│       ├── m12_claim_audit.json
│       ├── m12_gis_alignment.json
│       ├── m12_offline_demo_validation.json
│       └── M12_FINAL_FREEZE.json
│
├── demo_package/                         # Lightweight portable deployment bundle (zero HPC dependencies)
│
└── scripts/                              # Automated validation, audit, and diagnostic utilities
    ├── preflight_demo.py                 # Fresh-machine preflight verification
    ├── validate_final_scientific_values.py # 33-point scientific regression validator
    ├── audit_final_claims.py             # Scientific claim compliance checker
    ├── validate_real_map.py              # Map projection and GIS layer alignment tester
    ├── validate_dashboard.py             # API endpoint integration test suite
    ├── validate_m11_generalization.py    # Multi-site configuration integrity checker
    ├── audit_no_fake_results.py          # Fabricated / placeholder data scanner
    └── validate_m12_final.py             # Master M12 release validation gate
```
