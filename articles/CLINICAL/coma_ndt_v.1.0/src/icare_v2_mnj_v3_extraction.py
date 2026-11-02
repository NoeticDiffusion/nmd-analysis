"""Extract MNJ-v3 Family B metrics from stored Jacobian derived-metrics series."""
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
    h5_scalar,
    mean_finite,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    write_csv,
    write_json,
    parallel_map,
)


def _extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "jacobian_metrics_3d_status": "unavailable",
        "ftr_3d_status": "unavailable",
        "n_windows": 0,
        "n_valid_windows": 0,
        "alpha_mean": float("nan"),
        "omega_mean": float("nan"),
        "reactivity_gap_mean": float("nan"),
        "reactivity_gap_given_alpha_neg_mean": float("nan"),
        "f_reactive": float("nan"),
        "f_contract": float("nan"),
        "f_unstable": float("nan"),
        "stable_reactive_fraction_stored": float("nan"),
        "f_reactive_vs_stored_abs": float("nan"),
        "g_peak_over_horizons": float("nan"),
        "read_ok": False,
        "read_error": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            path_3d = "/jacobian/derived_metrics/v1"
            if path_3d in handle:
                group = handle[path_3d]
                row["jacobian_metrics_3d_status"] = str(as_scalar(group["computation_status"][()]) if "computation_status" in group else "not_recorded")
                row["stable_reactive_fraction_stored"] = h5_scalar(handle, f"{path_3d}/summary/stable_reactive_fraction")
                series = group["series"] if "series" in group else None
                if series is not None and "spectral_abscissa" in series:
                    alpha = np.asarray(series["spectral_abscissa"][:], dtype=float)
                    omega = np.asarray(series["numerical_abscissa"][:], dtype=float)
                    gap = np.asarray(series["reactivity_gap"][:], dtype=float) if "reactivity_gap" in series else omega - alpha
                    valid = np.isfinite(alpha) & np.isfinite(omega)
                    n_valid = int(valid.sum())
                    row["n_windows"] = int(alpha.size)
                    row["n_valid_windows"] = n_valid
                    if n_valid:
                        a = alpha[valid]
                        w = omega[valid]
                        g = gap[valid]
                        row["alpha_mean"] = mean_finite(a)
                        row["omega_mean"] = mean_finite(w)
                        row["reactivity_gap_mean"] = mean_finite(g)
                        row["f_reactive"] = float(np.mean((a < 0) & (w > 0)))
                        row["f_contract"] = float(np.mean(w < 0))
                        row["f_unstable"] = float(np.mean(a > 0))
                        cond = a < 0
                        row["reactivity_gap_given_alpha_neg_mean"] = mean_finite(g[cond]) if cond.any() else float("nan")
                        stored = row["stable_reactive_fraction_stored"]
                        if stored is not None and np.isfinite(float(stored)):
                            row["f_reactive_vs_stored_abs"] = abs(row["f_reactive"] - float(stored))
            ftr_path = "/finite_time_response/v1/primary"
            if ftr_path in handle:
                row["ftr_3d_status"] = str(
                    as_scalar(handle[f"{ftr_path}/computation_status"][()])
                    if f"{ftr_path}/computation_status" in handle
                    else "not_recorded"
                )
                row["g_peak_over_horizons"] = h5_scalar(handle, f"{ftr_path}/summary/g_peak_over_horizons")
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _patient_timebin(run_frame: pd.DataFrame) -> pd.DataFrame:
    if run_frame.empty:
        return pd.DataFrame()
    return run_frame.groupby(["subject_id", "time_bin_primary"], as_index=False).agg(
        cpc=("cpc", "first"),
        outcome=("outcome", "first"),
        hospital=("hospital", "first"),
        ttm=("ttm", "first"),
        n_runs=("source_h5", "nunique"),
        n_valid_windows=("n_valid_windows", "sum"),
        alpha_mean=("alpha_mean", "median"),
        omega_mean=("omega_mean", "median"),
        reactivity_gap_mean=("reactivity_gap_mean", "median"),
        reactivity_gap_given_alpha_neg_mean=("reactivity_gap_given_alpha_neg_mean", "median"),
        f_reactive=("f_reactive", "median"),
        f_contract=("f_contract", "median"),
        f_unstable=("f_unstable", "median"),
        stable_reactive_fraction_stored=("stable_reactive_fraction_stored", "median"),
        g_peak_over_horizons=("g_peak_over_horizons", "median"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    runs = pd.read_csv(in_dir / "run_inventory_timebinned.csv")
    paths = runs["source_h5"].astype(str).tolist()
    print(f"MNJ-v3 extraction: {len(paths)} runs", flush=True)
    rows = parallel_map(_extract_one, paths, workers=cfg.workers, desc="mnj")
    run_frame = pd.DataFrame(rows)
    if not run_frame.empty:
        keep = ["source_h5", "time_bin_primary", "time_bin_hourly", "in_primary_window"]
        run_frame = run_frame.merge(runs[keep], on="source_h5", how="left")
        run_frame["bundle_id"] = cfg.bundle_id
        run_frame["confirmatory_status"] = cfg.confirmatory_status
    patient = _patient_timebin(run_frame)
    write_csv(out_dir / "mnj_v3_run_level.csv", run_frame)
    write_csv(out_dir / "mnj_v3_patient_timebin.csv", patient)
    write_json(
        out_dir / "mnj_v3_manifest.json",
        {
            "n_runs": int(len(run_frame)),
            "n_read_ok": int(run_frame["read_ok"].sum()) if not run_frame.empty else 0,
            "jacobian_metrics_3d_status_counts": run_frame["jacobian_metrics_3d_status"].value_counts(dropna=False).to_dict()
            if not run_frame.empty
            else {},
            "n_runs_with_any_valid_window": int((run_frame["n_valid_windows"] > 0).sum()) if not run_frame.empty else 0,
            "n_patient_timebins": int(len(patient)),
            "n_patient_timebins_alpha_finite": int(patient["alpha_mean"].notna().sum()) if not patient.empty else 0,
            "f_reactive_vs_stored_abs_median": float(run_frame["f_reactive_vs_stored_abs"].median())
            if not run_frame.empty
            else None,
            "ftr_status_counts": run_frame["ftr_3d_status"].value_counts(dropna=False).to_dict() if not run_frame.empty else {},
            "note": (
                "FTR g_peak is extracted for QC only and is not tested in this pass. "
                "jacobian_metrics_3d_status reflects the ingest fit-fidelity gate "
                "(insufficient_support = local linear fit did not beat baseline); "
                "if n_patient_timebins_alpha_finite is small, Family B is not testable "
                "on this bundle regardless of the contrast p-value."
            ),
        },
    )
    print(f"Wrote MNJ-v3 tables to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
