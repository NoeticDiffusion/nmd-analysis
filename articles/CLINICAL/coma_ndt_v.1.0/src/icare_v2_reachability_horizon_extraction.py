"""Recompute reachability cones at h=1/2/4 from subject-anchored 3D coordinates."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from icare_v2_common import (
    add_common_args,
    ensure_nmd_analysis_on_path,
    median_finite,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    write_csv,
    write_json,
    parallel_map,
)

ensure_nmd_analysis_on_path()
from nmd_analysis.h5_contract import resolve_coords_3d  # noqa: E402
from nmd_analysis.reachability_core import compute_reachability_cones_from_mnps  # noqa: E402


def _extract_one(item: tuple[str, str, dict[str, Any]]) -> dict[str, Any]:
    path, contract, reach_cfg = item
    parsed = parse_run_stem(Path(path).stem)
    horizons = [int(h) for h in reach_cfg.get("horizons", [1, 2, 4])]
    max_h = max(horizons)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "reachability_ok": False,
        "reachability_error": None,
        "n_windows": 0,
        "n_valid_windows": 0,
        "tube_d_eff_median": float("nan"),
    }
    for horizon in horizons:
        row[f"cone_d_eff_h{horizon}_median"] = float("nan")
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            resolved = resolve_coords_3d(handle, coordinate_contract=contract)
            if resolved is None:
                row["reachability_error"] = "coords_3d_unresolved"
                return row
            x = np.asarray(resolved.values, dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float) if "/time" in handle else np.arange(len(x), dtype=float)
            if len(time) != len(x):
                time = np.arange(len(x), dtype=float)
        if len(x) < 8 or x.shape[1] != 3:
            row["reachability_error"] = f"insufficient_points_or_dim:{x.shape}"
            return row
        result = compute_reachability_cones_from_mnps(
            x,
            time,
            k=int(reach_cfg.get("k", 25)),
            super_window_size=int(reach_cfg.get("super_window_size", 3)),
            method=str(reach_cfg.get("method", "ridge")),
            alpha_grid=[float(reach_cfg.get("ridge_alpha", 1e-3))],
            horizon=max_h,
            jitter=float(reach_cfg.get("jitter", 1e-6)),
            eps=float(reach_cfg.get("eps", 1e-12)),
            persistence_mode="stability",
        )
        metrics = result["metrics_by_h"]["d_eff"]
        tube = result["tube_metrics"]["tube_d_eff"]
        row["n_windows"] = int(metrics.shape[0])
        row["n_valid_windows"] = int(np.isfinite(tube).sum())
        row["tube_d_eff_median"] = median_finite(tube)
        for horizon in horizons:
            if metrics.shape[1] >= horizon:
                row[f"cone_d_eff_h{horizon}_median"] = median_finite(metrics[:, horizon - 1])
        row["reachability_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["reachability_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _patient_timebin(run_frame: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    if run_frame.empty:
        return pd.DataFrame()
    agg = {
        "cpc": ("cpc", "first"),
        "outcome": ("outcome", "first"),
        "hospital": ("hospital", "first"),
        "ttm": ("ttm", "first"),
        "n_runs": ("source_h5", "nunique"),
        "n_valid_windows": ("n_valid_windows", "sum"),
        "n_ok_runs": ("reachability_ok", "sum"),
        "tube_d_eff_median": ("tube_d_eff_median", "median"),
    }
    for horizon in horizons:
        key = f"cone_d_eff_h{horizon}_median"
        agg[key] = (key, "median")
    return run_frame.groupby(["subject_id", "time_bin_primary"], as_index=False).agg(**agg)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    runs = pd.read_csv(in_dir / "run_inventory_timebinned.csv")
    paths = runs["source_h5"].astype(str).tolist()
    horizons = [int(h) for h in cfg.reachability.get("horizons", [1, 2, 4])]
    print(f"Reachability extraction: {len(paths)} runs, horizons={horizons}", flush=True)
    rows = parallel_map(
        _extract_one,
        [(path, cfg.coordinate_contract, dict(cfg.reachability)) for path in paths],
        workers=cfg.workers,
        desc="reachability",
    )
    run_frame = pd.DataFrame(rows)
    if not run_frame.empty:
        keep = ["source_h5", "time_bin_primary", "time_bin_hourly", "in_primary_window"]
        run_frame = run_frame.merge(runs[keep], on="source_h5", how="left")
        run_frame["bundle_id"] = cfg.bundle_id
        run_frame["confirmatory_status"] = cfg.confirmatory_status
    patient = _patient_timebin(run_frame, horizons)
    write_csv(out_dir / "reachability_horizon_run_level.csv", run_frame)
    write_csv(out_dir / "reachability_horizon_patient_timebin.csv", patient)
    write_json(
        out_dir / "reachability_horizon_manifest.json",
        {
            "n_runs": int(len(run_frame)),
            "n_ok": int(run_frame["reachability_ok"].sum()) if not run_frame.empty else 0,
            "horizons": horizons,
            "coordinate_contract": cfg.coordinate_contract,
            "note": "Recomputed from coords_3d_subject_anchored; stored /stochastic_reachability/v1 is not used.",
        },
    )
    print(f"Wrote reachability tables to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
