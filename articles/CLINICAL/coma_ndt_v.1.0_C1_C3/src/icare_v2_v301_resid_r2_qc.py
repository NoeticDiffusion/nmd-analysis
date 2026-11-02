"""COMA-RESID-001 OOS R^2_mu QC (sl_027). Not a new Holm family. Part2 sealed.

Reports whether the blocked-crossfit x-only kNN mean captures any increment
variance. If R2>0 the residual CPC result is cleaner; if R2~0 or negative,
RESID-001 remains valid as residual-under-this-mean-model.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import (
    add_common_args,
    discover_h5_files,
    parallel_map,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    time_reference_from_handle,
    write_csv,
    write_json,
)
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_l1_estimators import _segment_id
from icare_v2_v301_l1_panel import _annotate
from icare_v2_v301_resid_metrics import estimate_crossfit_r2_mu
from icare_v2_v301_resid_synthetic_gate import _simulate_constant, _simulate_varying_mean


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "r2_status": None,
        "r2_failure": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            if "/coords_3d_cohort_anchored/values" not in handle or "/time" not in handle:
                row["r2_status"] = "missing_chart"
                row["read_ok"] = True
                return row
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            raw = handle["/row_source/raw_file"][:] if "/row_source/raw_file" in handle else None
            result = estimate_crossfit_r2_mu(xc, time, segment_id=_segment_id(raw, xc.shape[0]))
            row["r2_status"] = result.get("status")
            row["r2_failure"] = result.get("failure_reason")
            row["r2_mu"] = result.get("r2_mu", float("nan"))
            row["r2_n_held"] = result.get("n_held")
            row["nominal_dt_sec"] = result.get("nominal_dt_sec")
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _missing_row(frame: pd.DataFrame, metric: str, *, grain: str, window: str, cfg) -> dict[str, Any]:
    work = frame[frame["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    good = work[work["contrast_group"] == cfg.good_label]
    poor = work[work["contrast_group"] == cfg.poor_label]
    g_yes = int(pd.to_numeric(good.get(metric), errors="coerce").notna().sum()) if metric in good else 0
    p_yes = int(pd.to_numeric(poor.get(metric), errors="coerce").notna().sum()) if metric in poor else 0
    g_n = int(len(good))
    p_n = int(len(poor))
    table = np.array([[g_yes, max(g_n - g_yes, 0)], [p_yes, max(p_n - p_yes, 0)]], dtype=int)
    fisher_p = float("nan")
    try:
        if table.sum() > 0:
            fisher_p = float(stats.fisher_exact(table)[1])
    except ValueError:
        pass
    return {
        "grain": grain,
        "window": window,
        "metric": metric,
        "n_cpc1_finite": g_yes,
        "n_cpc1": g_n,
        "rate_cpc1": g_yes / g_n if g_n else float("nan"),
        "n_cpc5_finite": p_yes,
        "n_cpc5": p_n,
        "rate_cpc5": p_yes / p_n if p_n else float("nan"),
        "fisher_p": fisher_p,
    }


def _patient(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    if work.empty:
        return work
    return work.groupby("subject_id", as_index=False).agg(
        cpc=("cpc", "first"),
        contrast_group=("contrast_group", "first"),
        hospital=("hospital", "first"),
        n_runs=("source_h5", "nunique"),
        r2_mu=("r2_mu", "median"),
    )


def _synthetic_r2() -> dict[str, Any]:
    x, t = _simulate_constant(900, np.array([1.0, 0.0, 0.0]), seed=11)
    const = estimate_crossfit_r2_mu(x, t)
    x_v, t_v, seg_v = _simulate_varying_mean(800, seed=19)
    vary = estimate_crossfit_r2_mu(x_v, t_v, segment_id=seg_v)
    r2_c = float(const.get("r2_mu", float("nan")))
    r2_v = float(vary.get("r2_mu", float("nan")))
    return {
        "constant_drift_r2": r2_c,
        "varying_mean_r2": r2_v,
        "constant_near_zero": bool(np.isfinite(r2_c) and abs(r2_c) < 0.15),
        "varying_positive": bool(np.isfinite(r2_v) and r2_v > 0.05),
        "pass": bool(np.isfinite(r2_c) and abs(r2_c) < 0.15 and np.isfinite(r2_v) and r2_v > 0.05),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    synth = _synthetic_r2()
    print(f"R2 synthetic pass={synth['pass']} constant={synth['constant_drift_r2']:.4g} varying={synth['varying_mean_r2']:.4g}", flush=True)
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: RESID R2 QC extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="resid_r2")
    runs = _annotate(pd.DataFrame(rows), cfg)
    patients = _patient(runs, cfg)
    rec_primary = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    missing = pd.DataFrame(
        [
            _missing_row(rec_primary, "r2_mu", grain="recording", window="0_12h", cfg=cfg),
            _missing_row(patients, "r2_mu", grain="subject", window="0_12h", cfg=cfg),
        ]
    )
    contrast = _contrast_row(patients, "r2_mu", cfg=cfg, family="resid_r2_qc", hypothesis="r2_mu", prediction="descriptive QC")
    contrasts = pd.DataFrame([contrast])
    finite = pd.to_numeric(patients.get("r2_mu"), errors="coerce")
    n_pos = int((finite > 0).sum())
    n_fin = int(finite.notna().sum())
    out = cfg.output_dir
    write_csv(out / "resid_r2_run_level.csv", runs)
    write_csv(out / "resid_r2_patient_primary.csv", patients)
    write_csv(out / "resid_r2_missingness_by_cpc.csv", missing)
    write_csv(out / "resid_r2_contrasts.csv", contrasts)
    write_json(out / "resid_r2_synthetic.json", synth)
    lines = [
        "# COMA-RESID-001 R2_mu QC (sl_027)",
        "",
        "Not a new Holm family. Not innovation. Part2 sealed. SL-004A unchanged.",
        "",
        f"Synthetic: pass={synth['pass']}; constant-drift R2={synth['constant_drift_r2']:.4g};",
        f"varying-mean R2={synth['varying_mean_r2']:.4g}.",
        "",
        f"Subject 0-12h finite R2: {n_fin}; fraction >0: {n_pos}/{n_fin if n_fin else 0}.",
        f"Subject median R2 CPC1={contrast.get('cpc1_median', float('nan')):.4g},",
        f"CPC5={contrast.get('cpc5_median', float('nan')):.4g}, d={contrast.get('cohens_d_cpc1_minus_cpc5', float('nan')):.3g},",
        f"MW p={contrast.get('mannwhitney_p', float('nan')):.3g}.",
        "",
        "If median R2>0 the kNN mean captures some displacement, so RESID-001 is residual",
        "spread after a mean that does some work. If R2~0 the claim stays narrower:",
        "residual under this particular mean model.",
        "",
    ]
    (out / "resid_r2_qc.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'resid_r2_qc.md'}", flush=True)
    print(missing.to_string(index=False), flush=True)
    print(contrasts[["family", "metric", "n_cpc1", "n_cpc5", "cpc1_median", "cpc5_median", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
