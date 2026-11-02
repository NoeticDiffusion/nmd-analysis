"""Leave-one-subject-out (LOSO) sensitivity analysis for Family A H1-H3.

For each primary metric, drops one patient at a time from the CPC1 vs CPC5
contrast and recomputes Mann-Whitney p and Cohen's d on the remaining
n-1 patients. Reports whether the direction and (nominal, alpha=0.05)
significance are stable under single-patient removal. This is a robustness
check, not a substitute for the pre-specified BH-FDR test in
outcome_contrasts.csv - do not use LOSO p-values as a replacement primary
result.
"""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import (
    add_common_args,
    cliffs_delta,
    cohens_d,
    finite_array,
    resolve_pipeline_config,
    write_csv,
    write_json,
)

METRICS = (
    ("d_eff_a_median", "H1"),
    ("h_tilde_a_median", "H2"),
    ("e_perp_median", "H3"),
)
NOMINAL_ALPHA = 0.05


def _mw_p_d(good: np.ndarray, poor: np.ndarray) -> tuple[float, float]:
    good = finite_array(good)
    poor = finite_array(poor)
    if good.size < 2 or poor.size < 2:
        return float("nan"), float("nan")
    try:
        p = float(stats.mannwhitneyu(good, poor, alternative="two-sided").pvalue)
    except ValueError:
        p = float("nan")
    return p, cohens_d(good, poor)


def _loso_for_metric(frame: pd.DataFrame, metric: str, cfg) -> tuple[pd.DataFrame, dict[str, Any]]:
    work = frame[["subject_id", "contrast_group", metric]].copy()
    work[metric] = pd.to_numeric(work[metric], errors="coerce")
    work = work[np.isfinite(work[metric])]
    good_ids = work.loc[work["contrast_group"] == cfg.good_label, "subject_id"].tolist()
    poor_ids = work.loc[work["contrast_group"] == cfg.poor_label, "subject_id"].tolist()
    full_good = work.loc[work["contrast_group"] == cfg.good_label, metric].to_numpy(dtype=float)
    full_poor = work.loc[work["contrast_group"] == cfg.poor_label, metric].to_numpy(dtype=float)
    baseline_p, baseline_d = _mw_p_d(full_good, full_poor)

    rows: list[dict[str, Any]] = []
    for dropped_id in good_ids + poor_ids:
        dropped_group = cfg.good_label if dropped_id in good_ids else cfg.poor_label
        sub = work[work["subject_id"] != dropped_id]
        g = sub.loc[sub["contrast_group"] == cfg.good_label, metric].to_numpy(dtype=float)
        p_arm = sub.loc[sub["contrast_group"] == cfg.poor_label, metric].to_numpy(dtype=float)
        p_val, d_val = _mw_p_d(g, p_arm)
        rows.append(
            {
                "metric": metric,
                "dropped_subject_id": dropped_id,
                "dropped_from_group": dropped_group,
                "n_cpc1": int(g.size),
                "n_cpc5": int(p_arm.size),
                "mannwhitney_p": p_val,
                "cohens_d": d_val,
                "cliffs_delta": cliffs_delta(g, p_arm),
                "significant_at_0.05": bool(np.isfinite(p_val) and p_val < NOMINAL_ALPHA),
                "same_sign_as_baseline": bool(np.isfinite(d_val) and np.isfinite(baseline_d) and np.sign(d_val) == np.sign(baseline_d)),
            }
        )
    detail = pd.DataFrame(rows)
    p_values = detail["mannwhitney_p"].to_numpy(dtype=float)
    d_values = detail["cohens_d"].to_numpy(dtype=float)
    summary = {
        "metric": metric,
        "baseline_n_cpc1": int(full_good.size),
        "baseline_n_cpc5": int(full_poor.size),
        "baseline_mannwhitney_p": baseline_p,
        "baseline_cohens_d": baseline_d,
        "n_drops": int(len(rows)),
        "loso_p_min": float(np.nanmin(p_values)) if p_values.size else float("nan"),
        "loso_p_max": float(np.nanmax(p_values)) if p_values.size else float("nan"),
        "loso_d_min": float(np.nanmin(d_values)) if d_values.size else float("nan"),
        "loso_d_max": float(np.nanmax(d_values)) if d_values.size else float("nan"),
        "n_drops_flip_to_nonsignificant": int(
            ((p_values >= NOMINAL_ALPHA) & np.isfinite(p_values)).sum()
            if np.isfinite(baseline_p) and baseline_p < NOMINAL_ALPHA
            else -1
        ),
        "all_drops_same_sign": bool(detail["same_sign_as_baseline"].all()) if not detail.empty else False,
        "stable_at_0.05": bool(
            (np.isfinite(baseline_p) and baseline_p < NOMINAL_ALPHA and (p_values < NOMINAL_ALPHA).all())
            or (np.isfinite(baseline_p) and baseline_p >= NOMINAL_ALPHA and (p_values >= NOMINAL_ALPHA).all())
        ) if p_values.size else False,
    }
    return detail, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    table = pd.read_csv(in_dir / "icare_v2_primary_cpc15_table.csv")

    all_detail: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []
    for metric, hyp in METRICS:
        if metric not in table.columns:
            continue
        detail, summary = _loso_for_metric(table, metric, cfg)
        summary["hypothesis"] = hyp
        detail["hypothesis"] = hyp
        all_detail.append(detail)
        summaries.append(summary)

    detail_frame = pd.concat(all_detail, ignore_index=True) if all_detail else pd.DataFrame()
    summary_frame = pd.DataFrame(summaries)
    write_csv(out_dir / "loso_sensitivity_detail.csv", detail_frame)
    write_csv(out_dir / "loso_sensitivity_summary.csv", summary_frame)
    write_json(
        out_dir / "loso_sensitivity_manifest.json",
        {
            "note": (
                "Robustness check only (nominal alpha=0.05 per drop, not BH-corrected). "
                "Does not replace outcome_contrasts.csv as the primary result."
            ),
            "n_metrics": int(len(summaries)),
            "bundle_id": cfg.bundle_id,
            "confirmatory_status": cfg.confirmatory_status,
        },
    )
    print(f"Wrote LOSO sensitivity for {len(summaries)} metrics to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
