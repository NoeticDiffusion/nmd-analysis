"""Extract Family A diffusion-geometry metrics (H1-H4) from stored a_hat series."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from icare_v2_common import (
    add_common_args,
    as_scalar,
    diffusion_geometry_from_tensor,
    median_finite,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    write_csv,
    write_json,
    parallel_map,
)


def _extract_one(path: str, eps: float) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "diffusion_computation_status": "unavailable",
        "n_windows": 0,
        "n_valid_windows": 0,
        "d_eff_a_median": float("nan"),
        "d_eff_a_stored_median": float("nan"),
        "h_tilde_a_median": float("nan"),
        "e_perp_median": float("nan"),
        "e_perp_from_stored_abd_median": float("nan"),
        "d_total_median": float("nan"),
        "d_total_stored_median": float("nan"),
        "a_bd_median": float("nan"),
        "d_eff_a_vs_stored_abs_median": float("nan"),
        "read_ok": False,
        "read_error": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            if "/dynamical_families/diffusion/v1" not in handle:
                row["read_ok"] = True
                return row
            group = handle["/dynamical_families/diffusion/v1"]
            row["diffusion_computation_status"] = str(
                as_scalar(group["computation_status"][()]) if "computation_status" in group else "not_recorded"
            )
            series = group["series"] if "series" in group else None
            if series is None or "a_hat" not in series:
                row["read_ok"] = True
                return row
            a_hat = np.asarray(series["a_hat"][:], dtype=float)
            valid = np.asarray(series["valid"][:], dtype=int).reshape(-1) if "valid" in series else np.ones(a_hat.shape[0], dtype=int)
            stored_d_eff = np.asarray(series["d_diff"][:], dtype=float) if "d_diff" in series else None
            stored_d_total = np.asarray(series["D_total"][:], dtype=float) if "D_total" in series else None
            stored_abd = (
                np.asarray(series["drift_diffusion_alignment"][:], dtype=float)
                if "drift_diffusion_alignment" in series
                else None
            )
            drift = None
            if "/mnps_3d_dot" in handle:
                drift = np.asarray(handle["/mnps_3d_dot"][:], dtype=float)
            n = a_hat.shape[0]
            d_eff = np.full(n, np.nan)
            h_tilde = np.full(n, np.nan)
            e_perp = np.full(n, np.nan)
            d_total = np.full(n, np.nan)
            a_bd = np.full(n, np.nan)
            e_perp_stored = np.full(n, np.nan)
            for i in range(n):
                if valid[i] != 1 or not np.isfinite(a_hat[i]).all():
                    continue
                local_drift = drift[i] if drift is not None and i < len(drift) else None
                metrics = diffusion_geometry_from_tensor(a_hat[i], local_drift, eps=eps)
                d_eff[i] = metrics["d_eff_a"]
                h_tilde[i] = metrics["h_tilde_a"]
                e_perp[i] = metrics["e_perp"]
                d_total[i] = metrics["d_total"]
                a_bd[i] = metrics["a_bd"]
                if stored_abd is not None and np.isfinite(stored_abd[i]):
                    e_perp_stored[i] = 1.0 - float(stored_abd[i])
            row["n_windows"] = int(n)
            row["n_valid_windows"] = int(np.isfinite(d_eff).sum())
            row["d_eff_a_median"] = median_finite(d_eff)
            row["h_tilde_a_median"] = median_finite(h_tilde)
            row["e_perp_median"] = median_finite(e_perp)
            row["d_total_median"] = median_finite(d_total)
            row["a_bd_median"] = median_finite(a_bd)
            row["e_perp_from_stored_abd_median"] = median_finite(e_perp_stored)
            if stored_d_eff is not None:
                row["d_eff_a_stored_median"] = median_finite(np.where(valid == 1, stored_d_eff, np.nan))
                row["d_eff_a_vs_stored_abs_median"] = median_finite(np.abs(d_eff - stored_d_eff))
            if stored_d_total is not None:
                row["d_total_stored_median"] = median_finite(np.where(valid == 1, stored_d_total, np.nan))
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _extract_one_star(item: tuple[str, float]) -> dict[str, Any]:
    return _extract_one(item[0], item[1])


def _patient_timebin(run_frame: pd.DataFrame) -> pd.DataFrame:
    if run_frame.empty:
        return pd.DataFrame()
    metrics = [
        "d_eff_a_median",
        "h_tilde_a_median",
        "e_perp_median",
        "d_total_median",
        "a_bd_median",
        "e_perp_from_stored_abd_median",
        "d_eff_a_stored_median",
        "d_total_stored_median",
    ]
    agg = {
        "cpc": ("cpc", "first"),
        "outcome": ("outcome", "first"),
        "hospital": ("hospital", "first"),
        "ttm": ("ttm", "first"),
        "n_runs": ("source_h5", "nunique"),
        "n_valid_windows": ("n_valid_windows", "sum"),
    }
    for metric in metrics:
        agg[metric] = (metric, "median")
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
    print(f"Diffusion extraction: {len(paths)} runs", flush=True)
    rows = parallel_map(
        _extract_one_star,
        [(path, cfg.diffusion_eps) for path in paths],
        workers=cfg.workers,
        desc="diffusion",
    )
    run_frame = pd.DataFrame(rows)
    if not run_frame.empty:
        keep = ["source_h5", "time_bin_primary", "time_bin_hourly", "in_primary_window"]
        run_frame = run_frame.merge(runs[keep], on="source_h5", how="left")
        run_frame["bundle_id"] = cfg.bundle_id
        run_frame["confirmatory_status"] = cfg.confirmatory_status
    patient = _patient_timebin(run_frame)
    write_csv(out_dir / "diffusion_geometry_run_level.csv", run_frame)
    write_csv(out_dir / "diffusion_geometry_patient_timebin.csv", patient)
    write_json(
        out_dir / "diffusion_geometry_manifest.json",
        {
            "n_runs": int(len(run_frame)),
            "n_read_ok": int(run_frame["read_ok"].sum()) if not run_frame.empty else 0,
            "n_valid_windows_total": int(run_frame["n_valid_windows"].sum()) if not run_frame.empty else 0,
            "d_eff_crosscheck_abs_median": float(run_frame["d_eff_a_vs_stored_abs_median"].median())
            if not run_frame.empty
            else None,
            "e_perp_source": "computed from a_hat and mnps_3d_dot; stored A_bD used only as a cross-check via 1-A_bD",
        },
    )
    print(f"Wrote diffusion tables to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
