"""H3 (E_perp) robustness check with an independently smoothed drift estimator.

`e_perp_median` in the primary analysis uses the stored `/mnps_3d_dot` field
as the drift proxy: a raw, unsmoothed one-step finite difference of the
subject-anchored 3D coordinates, computed at the same 4 s cadence as the
diffusion-tensor windows themselves. It has never been independently
qualified (see handover/ingest_jacobian_fidelity_handover.md and
S1_Supplementary_methods.typ Sec. 1.3), so an E_perp result built on it is
reported as a candidate metric, not a confirmed one.

This script recomputes E_perp using a second, independent drift estimator:
a local polynomial (Savitzky-Golay) smoothed derivative of the same
subject-anchored 3D coordinate series, over a wider local neighborhood
(default 11 points = ~40 s at the 4 s cadence) than the single-step
mnps_3d_dot proxy. If H3 is a real effect and not an artifact of a noisy
one-step drift estimate, the smoothed-drift E_perp should point the same
direction and remain BH-significant. If it does not, that is evidence H3 is
sensitive to the choice of drift estimator, not yet a robust finding.

This does NOT touch mnps_3d_dot, a_hat, or any ingest-side artifact. It is a
purely article-local, read-only robustness re-derivation from already
exported coordinates + diffusion tensors.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import savgol_filter

from icare_v2_common import (
    add_common_args,
    as_scalar,
    bootstrap_two_sample_ci,
    cliffs_delta,
    cohens_d,
    diffusion_geometry_from_tensor,
    finite_array,
    median_finite,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    write_csv,
    write_json,
    parallel_map,
)
from icare_v2_loso_sensitivity import _loso_for_metric

SAVGOL_WINDOW = 11
SAVGOL_POLYORDER = 2


def _smoothed_drift(coords: np.ndarray, dt: float, window_cfg: int = SAVGOL_WINDOW) -> np.ndarray | None:
    n = coords.shape[0]
    window = min(window_cfg, n if n % 2 == 1 else n - 1)
    if window < SAVGOL_POLYORDER + 2 or window < 5:
        return None
    try:
        drift = savgol_filter(
            coords, window_length=window, polyorder=SAVGOL_POLYORDER, deriv=1, delta=dt, axis=0, mode="interp"
        )
    except Exception:  # noqa: BLE001
        return None
    return drift


def _extract_one(path: str, eps: float, window_cfg: int = SAVGOL_WINDOW) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "n_windows": 0,
        "n_valid_windows_qualified": 0,
        "e_perp_qualified_median": float("nan"),
        "a_bd_qualified_median": float("nan"),
        "savgol_window_used": 0,
        "read_ok": False,
        "read_error": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            if "/dynamical_families/diffusion/v1" not in handle or "/coords_3d_subject_anchored" not in handle or "/time" not in handle:
                row["read_ok"] = True
                return row
            group = handle["/dynamical_families/diffusion/v1"]
            series = group["series"] if "series" in group else None
            if series is None or "a_hat" not in series:
                row["read_ok"] = True
                return row
            a_hat = np.asarray(series["a_hat"][:], dtype=float)
            valid = np.asarray(series["valid"][:], dtype=int).reshape(-1) if "valid" in series else np.ones(a_hat.shape[0], dtype=int)
            coords = np.asarray(handle["/coords_3d_subject_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            n = a_hat.shape[0]
            row["n_windows"] = int(n)
            if coords.shape[0] != n or time.shape[0] != n or n < 5:
                row["read_ok"] = True
                return row
            dt_diffs = np.diff(time)
            dt = float(np.median(dt_diffs[np.isfinite(dt_diffs) & (dt_diffs > 0)])) if dt_diffs.size else float("nan")
            if not np.isfinite(dt) or dt <= 0:
                row["read_ok"] = True
                return row
            drift = _smoothed_drift(coords, dt, window_cfg)
            if drift is None:
                row["read_ok"] = True
                return row
            row["savgol_window_used"] = min(window_cfg, n if n % 2 == 1 else n - 1)
            e_perp = np.full(n, np.nan)
            a_bd = np.full(n, np.nan)
            for i in range(n):
                if valid[i] != 1 or not np.isfinite(a_hat[i]).all() or not np.isfinite(drift[i]).all():
                    continue
                metrics = diffusion_geometry_from_tensor(a_hat[i], drift[i], eps=eps)
                e_perp[i] = metrics["e_perp"]
                a_bd[i] = metrics["a_bd"]
            row["n_valid_windows_qualified"] = int(np.isfinite(e_perp).sum())
            row["e_perp_qualified_median"] = median_finite(e_perp)
            row["a_bd_qualified_median"] = median_finite(a_bd)
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _extract_one_star(item: tuple[str, float, int]) -> dict[str, Any]:
    return _extract_one(item[0], item[1], item[2])


def _patient_timebin(run_frame: pd.DataFrame) -> pd.DataFrame:
    if run_frame.empty:
        return pd.DataFrame()
    return run_frame.groupby(["subject_id", "time_bin_primary"], as_index=False).agg(
        n_runs_qualified=("source_h5", "nunique"),
        n_valid_windows_qualified=("n_valid_windows_qualified", "sum"),
        e_perp_qualified_median=("e_perp_qualified_median", "median"),
        a_bd_qualified_median=("a_bd_qualified_median", "median"),
    )


def _contrast_row(good: np.ndarray, poor: np.ndarray, *, cfg, window_cfg: int = SAVGOL_WINDOW) -> dict[str, Any]:
    good = finite_array(good)
    poor = finite_array(poor)
    mw_u = mw_p = float("nan")
    if good.size and poor.size:
        try:
            mw = stats.mannwhitneyu(good, poor, alternative="two-sided")
            mw_u, mw_p = float(mw.statistic), float(mw.pvalue)
        except ValueError:
            pass
    d_lo, d_hi, _ = bootstrap_two_sample_ci(good, poor, cohens_d) if good.size >= 2 and poor.size >= 2 else (float("nan"), float("nan"), 0)
    delta_lo, delta_hi, _ = bootstrap_two_sample_ci(good, poor, cliffs_delta) if good.size and poor.size else (float("nan"), float("nan"), 0)
    return {
        "metric": "e_perp_qualified_median",
        "hypothesis": "H3_qualified_drift_robustness_check",
        "drift_estimator": f"savgol_window{window_cfg}_poly{SAVGOL_POLYORDER}_deriv1",
        "n_cpc1": int(good.size),
        "n_cpc5": int(poor.size),
        "cpc1_mean": float(np.mean(good)) if good.size else float("nan"),
        "cpc1_median": float(np.median(good)) if good.size else float("nan"),
        "cpc5_mean": float(np.mean(poor)) if poor.size else float("nan"),
        "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
        "cohens_d_cpc1_minus_cpc5": cohens_d(good, poor),
        "cohens_d_ci_lo": d_lo,
        "cohens_d_ci_hi": d_hi,
        "cliffs_delta_cpc1_minus_cpc5": cliffs_delta(good, poor),
        "cliffs_delta_ci_lo": delta_lo,
        "cliffs_delta_ci_hi": delta_hi,
        "mannwhitney_u": mw_u,
        "mannwhitney_p": mw_p,
        "family_testable": bool(good.size >= cfg.min_testable_group_n and poor.size >= cfg.min_testable_group_n),
        "min_testable_group_n": cfg.min_testable_group_n,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument(
        "--savgol-window",
        type=int,
        default=SAVGOL_WINDOW,
        help="Savitzky-Golay window length (samples) for the smoothed-drift sensitivity sweep.",
    )
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    window_cfg = int(args.savgol_window)
    runs = pd.read_csv(in_dir / "run_inventory_timebinned.csv")
    paths = runs["source_h5"].astype(str).tolist()
    print(f"Qualified-drift extraction: {len(paths)} runs (savgol_window={window_cfg})", flush=True)
    rows = parallel_map(
        _extract_one_star,
        [(path, cfg.diffusion_eps, window_cfg) for path in paths],
        workers=cfg.workers,
        desc="qualified_drift",
    )
    run_frame = pd.DataFrame(rows)
    if not run_frame.empty:
        keep = ["source_h5", "time_bin_primary", "in_primary_window"]
        run_frame = run_frame.merge(runs[keep], on="source_h5", how="left")
    patient = _patient_timebin(run_frame)
    write_csv(out_dir / "qualified_drift_geometry_run_level.csv", run_frame)
    write_csv(out_dir / "qualified_drift_geometry_patient_timebin.csv", patient)

    # Merge onto the already-built primary CPC1/5 table for the contrast.
    primary_path = in_dir / "icare_v2_primary_cpc15_table.csv"
    contrast_row = {}
    if primary_path.exists() and not patient.empty:
        primary = pd.read_csv(primary_path)
        merged = primary.merge(patient, on=["subject_id", "time_bin_primary"], how="left")
        good = merged.loc[merged["contrast_group"] == cfg.good_label, "e_perp_qualified_median"].to_numpy(dtype=float)
        poor = merged.loc[merged["contrast_group"] == cfg.poor_label, "e_perp_qualified_median"].to_numpy(dtype=float)
        contrast_row = _contrast_row(good, poor, cfg=cfg, window_cfg=window_cfg)
        write_csv(out_dir / "qualified_drift_primary_merged.csv", merged)
        loso_detail, loso_summary = _loso_for_metric(merged, "e_perp_qualified_median", cfg)
        loso_detail["hypothesis"] = "H3_qualified_drift_robustness_check"
        loso_summary["hypothesis"] = "H3_qualified_drift_robustness_check"
        write_csv(out_dir / "qualified_drift_loso_detail.csv", loso_detail)
        write_json(out_dir / "qualified_drift_loso_summary.json", loso_summary)
    contrast_frame = pd.DataFrame([contrast_row]) if contrast_row else pd.DataFrame()
    write_csv(out_dir / "qualified_drift_contrast.csv", contrast_frame)
    write_json(
        out_dir / "qualified_drift_manifest.json",
        {
            "note": (
                "H3/E_perp robustness check using a Savitzky-Golay smoothed drift "
                "estimator instead of the raw one-step mnps_3d_dot proxy. Exploratory "
                "robustness check, not a primary or pre-registered result; not folded "
                "into the H1-H3 BH-FDR family."
            ),
            "savgol_window": SAVGOL_WINDOW,
            "savgol_polyorder": SAVGOL_POLYORDER,
            "n_runs": int(len(run_frame)),
            "n_runs_with_qualified_estimate": int(run_frame["e_perp_qualified_median"].notna().sum()) if not run_frame.empty else 0,
            "bundle_id": cfg.bundle_id,
            "confirmatory_status": cfg.confirmatory_status,
        },
    )
    print(f"Wrote qualified-drift E_perp robustness check to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
