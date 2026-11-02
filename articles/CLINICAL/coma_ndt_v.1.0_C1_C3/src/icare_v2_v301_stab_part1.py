"""COMA-L1-STAB-001: between-run MAD/IQR of dense L1 quantities (sl_010).

Separate hypothesis family from the SL-004A confirmatory pair. Part2 stays
sealed. Between-run MAD is primary; IQR is sensitivity. Within-run IQR is
exploratory and filled when series IQRs are present.
"""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import add_common_args, resolve_pipeline_config, write_csv, write_json
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_l1_prepart2_gates import _holm

MIN_RUNS = 2
PRIMARY = (
    ("g90_cohort_reknn_median_mad", "G90_MAD", "CPC1 < CPC5"),
    ("r_ba_median_mad", "R_ba_MAD", "CPC1 < CPC5"),
)
SECONDARY = (
    ("f_perp_median_mad", "F_perp_MAD", "CPC1 < CPC5"),
    ("d_eff_cohort_reknn_median_mad", "d_eff_MAD", "CPC1 < CPC5"),
)
SENSITIVITY = (
    ("g90_cohort_reknn_median_iqr", "G90_IQR", "CPC1 < CPC5"),
    ("r_ba_median_iqr", "R_ba_IQR", "CPC1 < CPC5"),
    ("f_perp_median_iqr", "F_perp_IQR", "CPC1 < CPC5"),
    ("d_eff_cohort_reknn_median_iqr", "d_eff_IQR", "CPC1 < CPC5"),
)
EXPLORATORY = (
    ("g90_within_iqr_median", "G90_within_IQR", "unspecified"),
    ("r_ba_within_iqr_median", "R_ba_within_IQR", "unspecified"),
)
BASE = (
    "g90_cohort_reknn_median",
    "r_ba_median",
    "f_perp_median",
    "d_eff_cohort_reknn_median",
)


def _mad(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < MIN_RUNS:
        return float("nan")
    return float(np.median(np.abs(finite - np.median(finite))))


def _iqr(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < MIN_RUNS:
        return float("nan")
    q75, q25 = np.percentile(finite, [75.0, 25.0])
    return float(q75 - q25)


def _patient_stab(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    rows = []
    for subject, block in work.groupby("subject_id"):
        row: dict[str, Any] = {
            "subject_id": subject,
            "cpc": block["cpc"].iloc[0],
            "contrast_group": block["contrast_group"].iloc[0],
            "hospital": block["hospital"].iloc[0] if "hospital" in block else None,
            "n_runs": int(block["source_h5"].nunique()),
        }
        for metric in BASE:
            if metric not in block.columns:
                continue
            values = pd.to_numeric(block[metric], errors="coerce").to_numpy(dtype=float)
            row[f"{metric}_n"] = int(np.isfinite(values).sum())
            row[f"{metric}_mad"] = _mad(values)
            row[f"{metric}_iqr"] = _iqr(values)
        for metric in ("g90_within_iqr", "r_ba_within_iqr", "a_dom_median"):
            if metric in block.columns:
                row[f"{metric}_median"] = float(np.nanmedian(pd.to_numeric(block[metric], errors="coerce")))
        rows.append(row)
    return pd.DataFrame(rows)


def _render(*, cfg, n_run_audit: pd.DataFrame, missing: pd.DataFrame, contrasts: pd.DataFrame) -> str:
    lines = [
        "# COMA-L1-STAB-001 part1 (sl_010)",
        "",
        "Between-run MAD of recording medians is primary. IQR is sensitivity.",
        "Within-run IQR is exploratory. Separate family from SL-004A Holm.",
        "Part2 is not opened. Not Family B / spectral abscissa.",
        "",
        "## Run-count audit (CPC-blind eligibility for MAD)",
        "",
        "| Group | n subjects | median n runs | n with >=2 finite G90 | n with >=2 finite R_b/a |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for _, row in n_run_audit.iterrows():
        lines.append(
            f"| {row['contrast_group']} | {int(row['n_subjects'])} | {row['median_n_runs']:.3g} | "
            f"{int(row['n_g90_ge2'])} | {int(row['n_rba_ge2'])} |"
        )
    lines += [
        "",
        "## Missingness of MAD endpoints",
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
        "## Contrasts (subject-level, 0-12h)",
        "",
        "| Family | Hypothesis | Metric | Prediction | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p | Holm p |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in contrasts.iterrows():
        holm = row.get("holm_p", float("nan"))
        holm_s = "-" if not np.isfinite(holm) else f"{holm:.3g}"
        lines.append(
            f"| {row['family']} | {row['hypothesis']} | `{row['metric']}` | {row['prediction']} | "
            f"{int(row['n_cpc1'])} | {int(row['n_cpc5'])} | {row['cpc1_median']:.4g} | "
            f"{row['cpc5_median']:.4g} | {row['cohens_d_cpc1_minus_cpc5']:.3g} | "
            f"{row['mannwhitney_p']:.3g} | {holm_s} |"
        )
    lines += ["", "Hypothesis is greater CPC5 instability, not a median shift.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    runs = pd.read_csv(cfg.output_dir / "ddc_run_level.csv")
    extra = cfg.output_dir / "ddc_adom_run_level.csv"
    if extra.exists():
        add = pd.read_csv(extra)
        keep = [c for c in add.columns if c in {"source_h5", "g90_within_iqr", "r_ba_within_iqr", "a_dom_median"}]
        if "source_h5" in keep and len(keep) > 1:
            runs = runs.merge(add[keep], on="source_h5", how="left")
    patients = _patient_stab(runs, cfg)
    audit_rows = []
    for group, block in patients.groupby("contrast_group"):
        audit_rows.append(
            {
                "contrast_group": group,
                "n_subjects": int(len(block)),
                "median_n_runs": float(pd.to_numeric(block["n_runs"], errors="coerce").median()),
                "n_g90_ge2": int((pd.to_numeric(block.get("g90_cohort_reknn_median_n"), errors="coerce") >= MIN_RUNS).sum())
                if "g90_cohort_reknn_median_n" in block
                else 0,
                "n_rba_ge2": int((pd.to_numeric(block.get("r_ba_median_n"), errors="coerce") >= MIN_RUNS).sum())
                if "r_ba_median_n" in block
                else 0,
            }
        )
    audit = pd.DataFrame(audit_rows)
    missing_rows = []
    for metric, _, _ in PRIMARY + SECONDARY:
        good = patients[patients["contrast_group"] == cfg.good_label]
        poor = patients[patients["contrast_group"] == cfg.poor_label]
        g_yes = int(pd.to_numeric(good.get(metric), errors="coerce").notna().sum()) if metric in good else 0
        p_yes = int(pd.to_numeric(poor.get(metric), errors="coerce").notna().sum()) if metric in poor else 0
        table = np.array([[g_yes, max(len(good) - g_yes, 0)], [p_yes, max(len(poor) - p_yes, 0)]], dtype=int)
        fisher_p = float(stats.fisher_exact(table)[1]) if table.sum() else float("nan")
        missing_rows.append(
            {
                "metric": metric,
                "n_cpc1_finite": g_yes,
                "n_cpc1": int(len(good)),
                "n_cpc5_finite": p_yes,
                "n_cpc5": int(len(poor)),
                "fisher_p": fisher_p,
            }
        )
    missing = pd.DataFrame(missing_rows)
    contrast_rows = []
    for family, specs in (
        ("stab_primary", PRIMARY),
        ("stab_secondary", SECONDARY),
        ("stab_sensitivity_iqr", SENSITIVITY),
        ("stab_exploratory_within", EXPLORATORY),
    ):
        for metric, hyp, pred in specs:
            if metric in patients.columns:
                contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    if not contrasts.empty:
        idx = contrasts.index[contrasts["family"] == "stab_primary"].tolist()
        holm = _holm([float(contrasts.loc[i, "mannwhitney_p"]) for i in idx])
        for i, value in zip(idx, holm):
            contrasts.loc[i, "holm_p"] = value
    out = cfg.output_dir
    write_csv(out / "stab_patient_primary.csv", patients)
    write_csv(out / "stab_run_count_audit.csv", audit)
    write_csv(out / "stab_missingness_by_cpc.csv", missing)
    write_csv(out / "stab_contrasts.csv", contrasts)
    md = _render(cfg=cfg, n_run_audit=audit, missing=missing, contrasts=contrasts)
    (out / "stab_part1.md").write_text(md, encoding="utf-8")
    write_json(out / "stab_part1_manifest.json", {"experiment": "COMA-L1-STAB-001", "min_runs": MIN_RUNS, "part2_opened": False})
    print(f"wrote {out / 'stab_part1.md'}", flush=True)
    print(audit.to_string(index=False), flush=True)
    if not contrasts.empty:
        print(contrasts[["family", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
