"""
JalRakshak-HD: Milestone M9 Task 17 & 20 — Run GEE Flood Monitor CLI
====================================================================
CLI script to run near-real-time (NRT) Sentinel-1 flood monitoring pipeline
in latest mode or historical event mode.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.gee_flood_monitor import GEEFloodMonitor


def main():
    parser = argparse.ArgumentParser(description="JalRakshak-HD: Earth Engine Flood Monitor")
    parser.add_argument("--mode", choices=["latest", "historical"], default="latest",
                        help="Execution mode: 'latest' (newest available S1) or 'historical' (Aug 2019)")
    args = parser.parse_args()

    print("=" * 70)
    print(f" JALRAKSHAK-HD: Earth Engine NRT Flood Monitor (Mode: {args.mode.upper()})")
    print("=" * 70)

    monitor = GEEFloodMonitor()

    if args.mode == "latest":
        result = monitor.run_nrt_detection()
        print("\n--- Latest Sentinel-1 Acquisition Monitoring Result ---")
        print(f"  Latest Scene ID:                 {result.latest_scene_id}")
        print(f"  Acquisition DateTime:            {result.latest_acquisition_datetime}")
        print(f"  Observation Age:                 {result.observation_age_hours:.1f} hours ({result.days_since_acquisition:.1f} days)")
        print(f"  Orbit Pass / Relative:           {result.orbit_pass.value} (Orbit {result.relative_orbit})")
        print(f"  Reference Scenes Used:           {len(result.reference_scenes_used)} scenes")
        print(f"  Candidate New Water Area:        {result.candidate_new_water_detected_km2:.3f} km2")
        print(f"  Monitoring Status:               {result.latest_status}")
        print(f"  Causal Attribution:              {result.cause}")
        print(f"  Observation Quality:             {result.observation_quality.value}")
        print(f"  Flood Interpretation Confidence: {result.flood_interpretation_confidence.value}")
        print(f"  Output GeoTIFF:                  {result.output_tif}")
        print(f"  Output GeoPackage:               {result.output_gpkg}")
        print(f"\n[OK] Latest monitoring execution complete. Metadata saved to outputs/gee/latest/")


if __name__ == "__main__":
    main()
