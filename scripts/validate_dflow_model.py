"""
JalRakshak-HD: Pre-Run Static D-Flow FM Model Validator (Milestone M5)
=====================================================================
Performs thorough static verification on all configuration files, network structures,
boundary condition files, solver paths, and physical conservation bounds before execution.
"""

from __future__ import annotations

import configparser
import math
from pathlib import Path
import sys
import geopandas as gpd
import netCDF4 as nc
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "data" / "dflowfm" / "model"
MDU_PATH = MODEL_DIR / "Bhavanisagar_DamBreak.mdu"
NET_PATH = MODEL_DIR / "Bhavani_2D_net.nc"
EXT_PATH = MODEL_DIR / "model.ext"
BC_PATH = MODEL_DIR / "BHV_BASE.bc"
UPSTREAM_PLI = MODEL_DIR / "upstream_breach_boundary.pli"
DOWNSTREAM_PLI = MODEL_DIR / "downstream_boundary.pli"
OBS_XYN = MODEL_DIR / "observation_points.xyn"
DIMR_CONFIG = MODEL_DIR / "dimr_config.xml"
ORIGINAL_CSV = ROOT_DIR / "data" / "dflowfm" / "hydrographs" / "BHV_BASE.csv"

DIMR_EXE = Path("C:/Program Files/Deltares/Delft3D FM Suite 2026.02 OpenHMWQ/plugins/DeltaShell.Dimr/kernels/x64/bin/dimr.exe")
DFLOW_EXE = Path("C:/Program Files/Deltares/Delft3D FM Suite 2026.02 OpenHMWQ/plugins/DeltaShell.Dimr/kernels/x64/bin/dflowfm-cli.exe")


def validate_dflow_model() -> bool:
    print("=" * 80)
    print(" JALRAKSHAK-HD: D-FLOW FM PRE-RUN STATIC INTEGRITY VALIDATOR (MILESTONE M5)")
    print("=" * 80)

    checks = []

    # 1. Check file existence
    DOWNSTREAM_BC = MODEL_DIR / "downstream_boundary.bc"

    files_to_check = [
        ("MDU File", MDU_PATH),
        ("2D Mesh NetCDF", NET_PATH),
        ("External Forcing (model.ext)", EXT_PATH),
        ("Upstream Boundary BC (BHV_BASE.bc)", BC_PATH),
        ("Downstream Boundary BC", DOWNSTREAM_BC),
        ("Upstream Boundary PLI", UPSTREAM_PLI),
        ("Downstream Boundary PLI", DOWNSTREAM_PLI),
        ("Observation Points XYN", OBS_XYN),
        ("DIMR Config XML", DIMR_CONFIG),
        ("Original Hydrograph CSV", ORIGINAL_CSV),
        ("DIMR Executable", DIMR_EXE),
        ("DFlowFM Executable", DFLOW_EXE),
    ]

    for label, path in files_to_check:
        exists = path.exists()
        checks.append((f"File Exists: {label}", exists, f"Path: {path}"))
        print(f"[{'PASS' if exists else 'FAIL'}] {label:<36} -> {path}")

    # 2. Check 2D Mesh Structure and Bed Levels
    mesh_ok = True
    mesh_msg = ""
    try:
        ds = nc.Dataset(NET_PATH, "r")
        node_x = ds.variables["mesh2d_node_x"][:]
        node_y = ds.variables["mesh2d_node_y"][:]
        node_z = ds.variables["mesh2d_node_z"][:]
        face_x = ds.variables["mesh2d_face_x"][:]

        if len(node_x) == 0 or len(face_x) == 0:
            mesh_ok = False
            mesh_msg = "Mesh contains zero nodes or faces"
        elif np.isnan(node_z).any() or (node_z < 0).any():
            mesh_ok = False
            mesh_msg = "Mesh contains NaN or negative bed levels"
        else:
            mesh_msg = f"{len(node_x)} nodes, {len(face_x)} faces, z_min={np.min(node_z):.2f}m, z_max={np.max(node_z):.2f}m"
        ds.close()
    except Exception as e:
        mesh_ok = False
        mesh_msg = str(e)

    checks.append(("Mesh Readable & Finite Bed Levels", mesh_ok, mesh_msg))
    print(f"[{'PASS' if mesh_ok else 'FAIL'}] {'Mesh Readable & Finite Bed Levels':<36} -> {mesh_msg}")

    # 3. Check Hydrograph Peak and Conservation in .bc
    bc_ok = True
    bc_msg = ""
    try:
        df_orig = pd.read_csv(ORIGINAL_CSV)
        orig_qmax = df_orig["discharge_m3s"].max()
        orig_vol = np.trapezoid(df_orig["discharge_m3s"], df_orig["time_s"])

        # Parse .bc block by block
        with open(BC_PATH, "r", encoding="utf-8") as f:
            bc_text = f.read()

        forcing_blocks = [b for b in bc_text.split("[Forcing]") if b.strip()]
        if not forcing_blocks:
            bc_ok = False
            bc_msg = "No [Forcing] blocks found in BHV_BASE.bc"
        else:
            for block in forcing_blocks:
                data_lines = []
                is_data = False
                for line in block.splitlines():
                    line_str = line.strip()
                    if not line_str or line_str.startswith("#"):
                        continue
                    if line_str.lower().startswith("unit ="):
                        is_data = True
                        continue
                    if is_data and len(line_str.split()) == 2:
                        try:
                            t_min, q_val = map(float, line_str.split())
                            data_lines.append((t_min * 60.0, q_val))
                        except ValueError:
                            pass

                if not data_lines:
                    continue

                times, qs = zip(*data_lines)
                bc_qmax = max(qs)
                bc_vol = np.trapezoid(qs, times)
                qmax_match = math.isclose(bc_qmax, orig_qmax, rel_tol=1e-3)
                vol_match = math.isclose(bc_vol, orig_vol, rel_tol=1e-3)

                if not qmax_match or not vol_match:
                    bc_ok = False
                    bc_msg = f"Qmax or Volume mismatch: bc_Qmax={bc_qmax:.2f} (orig={orig_qmax:.2f}), bc_Vol={bc_vol/1e6:.2f}MCM (orig={orig_vol/1e6:.2f}MCM)"
                    break
                else:
                    bc_msg = f"Qmax={bc_qmax:.2f} m3/s, Vol={bc_vol/1e6:.2f} MCM (100% matched across {len(forcing_blocks)} forcing blocks)"
    except Exception as e:
        bc_ok = False
        bc_msg = str(e)

    checks.append(("BC Hydrograph Exact Match", bc_ok, bc_msg))
    print(f"[{'PASS' if bc_ok else 'FAIL'}] {'BC Hydrograph Exact Match':<36} -> {bc_msg}")

    # 4. Check MDU Simulation Duration vs Hydrograph End
    mdu_ok = True
    mdu_msg = ""
    try:
        tstop_val = 0.0
        with open(MDU_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().lower().startswith("tstop"):
                    tstop_val = float(line.split("=")[1].strip())
                    break

        hydrograph_end_s = 83287.18
        if tstop_val < hydrograph_end_s:
            mdu_ok = False
            mdu_msg = f"Tstop ({tstop_val} s) is shorter than hydrograph end ({hydrograph_end_s} s)"
        else:
            mdu_msg = f"Tstop = {tstop_val:.0f} s ({tstop_val/3600:.1f} hr) > Hydrograph Duration ({hydrograph_end_s/3600:.1f} hr)"
    except Exception as e:
        mdu_ok = False
        mdu_msg = str(e)

    checks.append(("Simulation Duration Valid", mdu_ok, mdu_msg))
    print(f"[{'PASS' if mdu_ok else 'FAIL'}] {'Simulation Duration Valid':<36} -> {mdu_msg}")

    all_passed = all(c[1] for c in checks)
    print("=" * 80)
    if all_passed:
        print("[SUCCESS] Static pre-run validation passed 100%. Model is ready for solver execution.")
    else:
        print("[ERROR] Static pre-run validation failed. Resolve errors before launching solver.")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = validate_dflow_model()
    sys.exit(0 if success else 1)
