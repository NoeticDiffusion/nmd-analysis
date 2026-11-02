"""COMA-L1L2-STAB-001: MAD of observed gain, operator gain, and model-gap (sl_012).

Same-chart decomposition uses subject-anchored g_obs and stored Phi.
Cohort g_obs MAD is mixed-frame diagnostic only. Part2 stays sealed.
Not Family B alpha.
"""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import add_common_args, resolve_pipeline_config, write_csv, write_json
from icare_v2_outcome_contrast_analysis import _contrast_row

MIN_RUNS = 2
SPECS = (
    ("g_obs_subject_median", "g_obs_subject_mad", "g_obs_90", "CPC1 < CPC5; same-chart observed"),
    ("g_op_max_median", "g_op_max_mad", "g_op_max", "unspecified; operator may be null or hide instability"),
    ("delta_g_subject_median", "delta_g_subject_mad", "delta_g_same_chart", "CPC1 < CPC5 if gap carries instability"),
    ("g_obs_cohort_median", "g_obs_cohort_mad", "g_obs_cohort", "mixed-frame diagnostic"),
    ("delta_g_cohort_median", "delta_g_cohort_mad", "delta_g_mixed", "mixed-frame diagnostic"),
)


def _mad(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < MIN_RUNS:
        return float("nan")
    return float(np.median(np.abs(finite - np.median(finite))))


def _patient(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    rows = []
    for subject, block in work.groupby("subject_id"):
        row: dict[str, Any] = {
            "subject_id": subject,
            "cpc": block["cpc"].iloc[0],
            "contrast_group": block["contrast_group"].iloc[0],
            "hospital": block["hospital"].iloc[0] if "hospital" in block.columns else None,
            "n_runs": int(block["source_h5"].nunique()),
        }
        for src, dest, _, _ in SPECS:
            if src not in block.columns:
                continue
            values = pd.to_numeric(block[src], errors="coerce").to_numpy(dtype=float)
            row[f"{src}_n"] = int(np.isfinite(values).sum())
            row[dest] = _mad(values)
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    runs = pd.read_csv(cfg.output_dir / "l1l2_run_level.csv")
    patients = _patient(runs, cfg)
    missing_rows = []
    contrast_rows = []
    for src, dest, hyp, pred in SPECS:
        good = patients[patients["contrast_group"] == cfg.good_label]
        poor = patients[patients["contrast_group"] == cfg.poor_label]
        g_yes = int(pd.to_numeric(good.get(dest), errors="coerce").notna().sum()) if dest in good else 0
        p_yes = int(pd.to_numeric(poor.get(dest), errors="coerce").notna().sum()) if dest in poor else 0
        table = np.array([[g_yes, max(len(good) - g_yes, 0)], [p_yes, max(len(poor) - p_yes, 0)]], dtype=int)
        fisher_p = float(stats.fisher_exact(table)[1]) if table.sum() else float("nan")
        missing_rows.append(
            {
                "metric": dest,
                "n_cpc1_finite": g_yes,
                "n_cpc1": int(len(good)),
                "n_cpc5_finite": p_yes,
                "n_cpc5": int(len(poor)),
                "fisher_p": fisher_p,
            }
        )
        if dest in patients.columns:
            contrast_rows.append(
                _contrast_row(patients, dest, cfg=cfg, family="l1l2_stab", hypothesis=hyp, prediction=pred)
            )
    missing = pd.DataFrame(missing_rows)
    contrasts = pd.DataFrame(contrast_rows)
    lines = [
        "# COMA-L1L2-STAB-001 part1 (sl_012)",
        "",
        "Between-run MAD of observed G90 rate, qualified operator max-gain, and same-chart model-gap.",
        "Part2 is not opened. Not Family B alpha.",
        "",
        "## Missingness",
        "",
        "| Metric | CPC1 | CPC5 | Fisher p |",
        "| --- | --- | --- | ---: |",
    ]
    for _, row in missing.iterrows():
        lines.append(
            f"| `{row['metric']}` | {int(row['n_cpc1_finite'])}/{int(row['n_cpc1'])} | "
            f"{int(row['n_cpc5_finite'])}/{int(row['n_cpc5'])} | {row['fisher_p']:.3g} |"
        )
    lines += [
        "",
        "## Contrasts",
        "",
        "| Hypothesis | Metric | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if contrasts.empty:
        lines.append("| - | - | - | - | - | - | - | - |")
    else:
        for _, row in contrasts.iterrows():
            lines.append(
                f"| {row['hypothesis']} | `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{row['cpc1_median']:.4g} | {row['cpc5_median']:.4g} | "
                f"{row['cohens_d_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} |"
            )
    lines += [
        "",
        "If MAD(g_obs) and MAD(delta_g) separate while MAD(g_op) does not, instability sits in the model-gap.",
        "",
    ]
    out = cfg.output_dir
    write_csv(out / "l1l2_stab_patient.csv", patients)
    write_csv(out / "l1l2_stab_missingness_by_cpc.csv", missing)
    write_csv(out / "l1l2_stab_contrasts.csv", contrasts)
    (out / "l1l2_stab_part1.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(out / "l1l2_stab_part1_manifest.json", {"experiment": "COMA-L1L2-STAB-001", "part2_opened": False})
    print(f"wrote {out / 'l1l2_stab_part1.md'}", flush=True)
    print(missing.to_string(index=False), flush=True)
    if not contrasts.empty:
        print(contrasts[["hypothesis", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
