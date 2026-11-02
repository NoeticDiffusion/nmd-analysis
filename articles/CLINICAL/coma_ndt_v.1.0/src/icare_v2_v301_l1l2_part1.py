"""COMA-L1L2-001: observed G90 rate vs qualified one-step operator gain (sl_010).

Not Family B alpha, not spectral abscissa as a CPC score. Missingness of
one-step identification is reported before contrasts. Part2 stays sealed.
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
    as_scalar,
    discover_h5_files,
    median_finite,
    parallel_map,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    time_reference_from_handle,
    write_csv,
    write_json,
)
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_l1_panel import _annotate, _s

EPS = 1e-12
OP_GROUP = "/dynamical_families/one_step/v1/operator_max_gain_rate_level2"
GAIN_RATE = "/dynamical_families/amplification/v1/neighbor_gain_rate_q90_level1"


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "one_step_identified": False,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            qual = None
            if f"{OP_GROUP}/qualification_status" in handle:
                qual = _s(as_scalar(handle[f"{OP_GROUP}/qualification_status"][()]))
            elif f"{OP_GROUP}/summary/qualification_status" in handle:
                qual = _s(as_scalar(handle[f"{OP_GROUP}/summary/qualification_status"][()]))
            row["operator_qualification"] = qual
            g_op = None
            if f"{OP_GROUP}/series/operator_max_gain_rate" in handle:
                g_op = np.asarray(handle[f"{OP_GROUP}/series/operator_max_gain_rate"][:], dtype=float)
            row["g_op_max_median"] = median_finite(g_op)
            row["one_step_identified"] = bool(np.isfinite(row["g_op_max_median"]))
            g_obs_subj = None
            if f"{GAIN_RATE}/series/neighbor_gain_rate_q90" in handle:
                g_obs_subj = np.asarray(handle[f"{GAIN_RATE}/series/neighbor_gain_rate_q90"][:], dtype=float)
            row["g_obs_subject_median"] = median_finite(g_obs_subj)
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _patient(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    if work.empty:
        return work
    agg = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "n_runs": ("source_h5", "nunique"),
        "n_identified": ("one_step_identified", "sum"),
        "g_op_max_median": ("g_op_max_median", "median"),
        "g_obs_subject_median": ("g_obs_subject_median", "median"),
        "g_obs_cohort_median": ("g_obs_cohort_median", "median"),
        "delta_g_subject_median": ("delta_g_subject_median", "median"),
        "delta_g_cohort_median": ("delta_g_cohort_median", "median"),
    }
    present = {k: v for k, v in agg.items() if v[0] in work.columns or k in {"cpc", "contrast_group", "n_runs", "n_identified"}}
    return work.groupby("subject_id", as_index=False).agg(**present)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: L1L2 extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="l1l2")
    runs = _annotate(pd.DataFrame(rows), cfg)
    ddc = cfg.output_dir / "ddc_run_level.csv"
    if ddc.exists():
        extra = pd.read_csv(ddc, usecols=lambda c: c in {"source_h5", "g90_cohort_reknn_median", "nominal_dt_sec"})
        runs = runs.merge(extra, on="source_h5", how="left")
        g90 = pd.to_numeric(runs.get("g90_cohort_reknn_median"), errors="coerce")
        dt = pd.to_numeric(runs.get("nominal_dt_sec"), errors="coerce").replace(0, np.nan)
        dt = dt.fillna(4.0)
        runs["g_obs_cohort_median"] = np.where(g90 > EPS, np.log(g90) / dt, np.nan)
    else:
        runs["g_obs_cohort_median"] = np.nan
    runs["delta_g_subject_median"] = pd.to_numeric(runs.get("g_obs_subject_median"), errors="coerce") - pd.to_numeric(
        runs.get("g_op_max_median"), errors="coerce"
    )
    runs["delta_g_cohort_median"] = pd.to_numeric(runs.get("g_obs_cohort_median"), errors="coerce") - pd.to_numeric(
        runs.get("g_op_max_median"), errors="coerce"
    )
    patients = _patient(runs, cfg)
    rec = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    missing_rows = []
    for grain, frame, metric in (
        ("recording", rec, "g_op_max_median"),
        ("subject", patients, "g_op_max_median"),
        ("recording", rec, "g_obs_cohort_median"),
        ("subject", patients, "g_obs_cohort_median"),
        ("recording", rec, "one_step_identified"),
        ("subject", patients, "g_op_max_median"),
    ):
        good = frame[frame["contrast_group"] == cfg.good_label]
        poor = frame[frame["contrast_group"] == cfg.poor_label]
        if metric == "one_step_identified":
            g_yes = int(good[metric].fillna(False).astype(bool).sum()) if metric in good else 0
            p_yes = int(poor[metric].fillna(False).astype(bool).sum()) if metric in poor else 0
        else:
            g_yes = int(pd.to_numeric(good.get(metric), errors="coerce").notna().sum())
            p_yes = int(pd.to_numeric(poor.get(metric), errors="coerce").notna().sum())
        table = np.array([[g_yes, max(len(good) - g_yes, 0)], [p_yes, max(len(poor) - p_yes, 0)]], dtype=int)
        fisher_p = float(stats.fisher_exact(table)[1]) if table.sum() else float("nan")
        missing_rows.append(
            {
                "grain": grain,
                "metric": metric,
                "n_cpc1_finite": g_yes,
                "n_cpc1": int(len(good)),
                "n_cpc5_finite": p_yes,
                "n_cpc5": int(len(poor)),
                "fisher_p": fisher_p,
            }
        )
    missing = pd.DataFrame(missing_rows)
    specs = (
        ("l1l2_obs_cohort", "g_obs_cohort_median", "g_obs_90", "exploratory"),
        ("l1l2_op", "g_op_max_median", "g_op_max", "exploratory; qualified Phi, not Family B alpha"),
        ("l1l2_gap_cohort", "delta_g_cohort_median", "delta_g", "exploratory model-gap, not diffusion"),
        ("l1l2_obs_subject", "g_obs_subject_median", "g_obs_subject", "same-chart companion"),
        ("l1l2_gap_subject", "delta_g_subject_median", "delta_g_subject", "same-chart model-gap"),
    )
    contrast_rows = []
    for family, metric, hyp, pred in specs:
        if metric in patients.columns:
            contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    lines = [
        "# COMA-L1L2-001 part1 (sl_010)",
        "",
        "Observed amplification rate vs qualified discrete operator max-gain rate.",
        "Not Family B alpha. Not a CPC score mixing G90 with spectral radius.",
        "Part2 is not opened.",
        "",
        "## Missingness",
        "",
        "| Grain | Metric | CPC1 | CPC5 | Fisher p |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for _, row in missing.iterrows():
        lines.append(
            f"| {row['grain']} | `{row['metric']}` | {int(row['n_cpc1_finite'])}/{int(row['n_cpc1'])} | "
            f"{int(row['n_cpc5_finite'])}/{int(row['n_cpc5'])} | {row['fisher_p']:.3g} |"
        )
    lines += [
        "",
        "## Contrasts (0-12h subject median)",
        "",
        "| Family | Metric | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if contrasts.empty:
        lines.append("| - | - | - | - | - | - | - | - |")
    else:
        for _, row in contrasts.iterrows():
            lines.append(
                f"| {row['family']} | `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{row['cpc1_median']:.4g} | {row['cpc5_median']:.4g} | "
                f"{row['cohens_d_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} |"
            )
    lines += [
        "",
        "`g_op` is the producer lag-1 operator on the subject-anchored chart.",
        "`g_obs_cohort` uses SL-004A cohort-frame G90. Same-chart companion uses stored subject G90 rate.",
        "Delta g is a model-gap, not diffusion.",
        "",
    ]
    out = cfg.output_dir
    write_csv(out / "l1l2_run_level.csv", runs)
    write_csv(out / "l1l2_patient_primary.csv", patients)
    write_csv(out / "l1l2_missingness_by_cpc.csv", missing)
    write_csv(out / "l1l2_contrasts.csv", contrasts)
    (out / "l1l2_part1.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(out / "l1l2_part1_manifest.json", {"experiment": "COMA-L1L2-001", "part2_opened": False, "not": ["family_b_alpha", "spectral_abscissa_as_score"]})
    print(f"wrote {out / 'l1l2_part1.md'}", flush=True)
    print(missing.to_string(index=False), flush=True)
    if not contrasts.empty:
        print(contrasts[["family", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
