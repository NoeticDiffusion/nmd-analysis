"""
compute_tac_between_run_mad.py — between-run IQR and MAD for TAC 6/8/10 metrics.

Reads the run_level_metrics.csv produced by run_tac_sigma_jacobian_dynamics.py
(wide format, one row per run) and computes two within-patient variability measures:

  between-run IQR  = q75(runs) − q25(runs)
  between-run MAD  = median |x_run − median(runs)|

Requires ≥ --min-runs finite values per patient per metric.

Usage
-----
  python compute_tac_between_run_mad.py \\
      --input-dir  J:/repos/NoeticDiffusion/articles/CLINICAL/comatose_experimental/results/tac_sigma_jacobian_20260803_invalidityfix_gated \\
      --output-dir J:/repos/NoeticDiffusion/articles/CLINICAL/comatose_experimental/results/tac_between_run_mad_20260803_invalidityfix_gated
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.metrics import roc_auc_score

ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ARTICLE_DIR / "results" / "tac_sigma_jacobian_20260803_invalidityfix_gated"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "tac_between_run_mad_20260803_invalidityfix_gated"

TAC_METRICS: tuple[str, ...] = (
    "tac6_3d_sigma_velocity_median",
    "tac6_9d_sigma_velocity_median",
    "tac8_3d_cone_twist_median",
    "tac8_9d_cone_twist_median",
    "tac10_9d_cross_band_flux_median",
    "tac10_9d_within_band_flux_median",
    "tac10_9d_cross_band_ratio_median",
)

GOOD_CPC = 1
POOR_CPC = 5
MIN_RUNS = 3


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    g = good[np.isfinite(good)]
    p = poor[np.isfinite(poor)]
    if g.size < 2 or p.size < 2:
        return float("nan")
    pooled_var = (
        (g.size - 1) * np.var(g, ddof=1) + (p.size - 1) * np.var(p, ddof=1)
    ) / (g.size + p.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((np.mean(g) - np.mean(p)) / np.sqrt(pooled_var))


def compute_between_run_stats(
    run_df: pd.DataFrame,
    *,
    metrics: tuple[str, ...],
    min_runs: int,
) -> pd.DataFrame:
    """
    Group by subject and compute between-run IQR + MAD for each metric.
    run_df is wide-format: one row per run, metric values as columns.
    """
    rows: list[dict[str, Any]] = []
    for subject, grp in run_df.groupby("subject"):
        row: dict[str, Any] = {
            "subject": subject,
            "cpc": grp["cpc"].iloc[0],
            "cpc_numeric": grp["cpc_numeric"].iloc[0],
            "label": grp["label"].iloc[0],
            "label_name": grp["label_name"].iloc[0],
        }
        for metric in metrics:
            if metric not in grp.columns:
                row[f"n_runs_{metric}"] = 0
                row[f"{metric}_iqr"] = float("nan")
                row[f"{metric}_mad"] = float("nan")
                continue
            vals = pd.to_numeric(grp[metric], errors="coerce").dropna().to_numpy(dtype=float)
            finite = vals[np.isfinite(vals)]
            n = len(finite)
            row[f"n_runs_{metric}"] = n
            if n >= min_runs:
                q25, q75 = float(np.percentile(finite, 25)), float(np.percentile(finite, 75))
                med = float(np.median(finite))
                row[f"{metric}_iqr"] = q75 - q25
                row[f"{metric}_mad"] = float(np.median(np.abs(finite - med)))
            else:
                row[f"{metric}_iqr"] = float("nan")
                row[f"{metric}_mad"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows).sort_values("subject").reset_index(drop=True)


def build_contrast_table(
    patient_stats: pd.DataFrame,
    stat_cols: list[str],
    *,
    good_cpc: int,
    poor_cpc: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for col in stat_cols:
        if col not in patient_stats.columns:
            continue
        good = pd.to_numeric(
            patient_stats.loc[patient_stats["label"] == 1, col], errors="coerce"
        ).dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(
            patient_stats.loc[patient_stats["label"] == 0, col], errors="coerce"
        ).dropna().to_numpy(dtype=float)
        if good.size < 4 or poor.size < 4:
            continue
        mw_p = float(mannwhitneyu(good, poor, alternative="two-sided").pvalue)
        d_val = cohens_d(good, poor)
        labels = np.concatenate([np.ones(good.size), np.zeros(poor.size)])
        scores = np.concatenate([good, poor])
        try:
            auroc = float(roc_auc_score(labels, scores)) if np.isfinite(scores).all() else float("nan")
        except Exception:
            auroc = float("nan")
        rows.append(
            {
                "metric_stat": col,
                f"cpc{good_cpc}_median": float(np.nanmedian(good)),
                f"cpc{poor_cpc}_median": float(np.nanmedian(poor)),
                "cohens_d": d_val,
                "abs_d": abs(d_val) if np.isfinite(d_val) else float("nan"),
                "mw_p": mw_p,
                "auroc": auroc,
                f"n_cpc{good_cpc}": int(good.size),
                f"n_cpc{poor_cpc}": int(poor.size),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("abs_d", ascending=False).reset_index(drop=True)


def build_markdown(
    contrast: pd.DataFrame,
    median_contrast: pd.DataFrame,
    *,
    n_total: int,
    n_good: int,
    n_poor: int,
    good_cpc: int,
    poor_cpc: int,
    min_runs: int,
) -> str:
    lines = [
        "# TAC 6/8/10 — Between-run IQR and MAD",
        "",
        f"- cohort: `{n_total}` subjects (`{n_good}` CPC{good_cpc}, `{n_poor}` CPC{poor_cpc})",
        f"- minimum runs for IQR/MAD: `{min_runs}`",
        "",
        "## Reference: median contrasts (from patient_level_metrics.csv)",
        "",
    ]
    if not median_contrast.empty:
        for _, row in median_contrast.iterrows():
            lines.append(
                f"- `{row['metric_stat']}`: "
                f"CPC{good_cpc} `{row[f'cpc{good_cpc}_median']:.4g}` vs "
                f"CPC{poor_cpc} `{row[f'cpc{poor_cpc}_median']:.4g}`, "
                f"d = `{row['cohens_d']:+.3f}`, p = `{row['mw_p']:.3g}`, "
                f"n = `{row[f'n_cpc{good_cpc}']}/{row[f'n_cpc{poor_cpc}']}`"
            )

    lines += ["", "## Between-run IQR contrasts", ""]
    iqr_rows = contrast[contrast["metric_stat"].str.endswith("_iqr")] if not contrast.empty else pd.DataFrame()
    if iqr_rows.empty:
        lines.append("No IQR contrast rows available.")
    else:
        for _, row in iqr_rows.iterrows():
            lines.append(
                f"- `{row['metric_stat']}`: "
                f"CPC{good_cpc} med `{row[f'cpc{good_cpc}_median']:.4g}` vs "
                f"CPC{poor_cpc} med `{row[f'cpc{poor_cpc}_median']:.4g}`, "
                f"d = `{row['cohens_d']:+.3f}`, p = `{row['mw_p']:.3g}`, "
                f"AUROC = `{row['auroc']:.3f}`, "
                f"n = `{row[f'n_cpc{good_cpc}']}/{row[f'n_cpc{poor_cpc}']}`"
            )

    lines += ["", "## Between-run MAD contrasts", ""]
    mad_rows = contrast[contrast["metric_stat"].str.endswith("_mad")] if not contrast.empty else pd.DataFrame()
    if mad_rows.empty:
        lines.append("No MAD contrast rows available.")
    else:
        for _, row in mad_rows.iterrows():
            lines.append(
                f"- `{row['metric_stat']}`: "
                f"CPC{good_cpc} med `{row[f'cpc{good_cpc}_median']:.4g}` vs "
                f"CPC{poor_cpc} med `{row[f'cpc{poor_cpc}_median']:.4g}`, "
                f"d = `{row['cohens_d']:+.3f}`, p = `{row['mw_p']:.3g}`, "
                f"AUROC = `{row['auroc']:.3f}`, "
                f"n = `{row[f'n_cpc{good_cpc}']}/{row[f'n_cpc{poor_cpc}']}`"
            )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1].strip())
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--min-runs", type=int, default=MIN_RUNS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    print(f"Loading run-level TAC metrics from {args.input_dir}...")
    run_df = pd.read_csv(args.input_dir / "run_level_metrics.csv", low_memory=False)
    run_df = run_df[run_df["cpc_numeric"].isin([float(args.good_cpc), float(args.poor_cpc)])]
    print(f"  {len(run_df):,} runs from {run_df['subject'].nunique()} subjects")

    print(f"Computing between-run IQR and MAD (min_runs={args.min_runs})...")
    patient_stats = compute_between_run_stats(
        run_df, metrics=TAC_METRICS, min_runs=args.min_runs
    )
    n_total = len(patient_stats)
    n_good = int((patient_stats["label"] == 1).sum())
    n_poor = int((patient_stats["label"] == 0).sum())
    print(f"  {n_total} subjects ({n_good} CPC{args.good_cpc}, {n_poor} CPC{args.poor_cpc})")
    patient_stats.to_csv(args.output_dir / "patient_between_run_stats.csv", index=False)

    iqr_cols = [f"{m}_iqr" for m in TAC_METRICS]
    mad_cols = [f"{m}_mad" for m in TAC_METRICS]
    contrast = build_contrast_table(
        patient_stats, iqr_cols + mad_cols,
        good_cpc=args.good_cpc, poor_cpc=args.poor_cpc,
    )
    contrast.to_csv(args.output_dir / "contrast_iqr_mad.csv", index=False)

    # Reference: median contrasts from patient_level_metrics
    patient_medians = pd.read_csv(args.input_dir / "patient_level_metrics.csv", low_memory=False)
    patient_medians = patient_medians[
        patient_medians["cpc_numeric"].isin([float(args.good_cpc), float(args.poor_cpc)])
    ]
    median_contrast = build_contrast_table(
        patient_medians, list(TAC_METRICS),
        good_cpc=args.good_cpc, poor_cpc=args.poor_cpc,
    )

    summary_md = build_markdown(
        contrast, median_contrast,
        n_total=n_total, n_good=n_good, n_poor=n_poor,
        good_cpc=args.good_cpc, poor_cpc=args.poor_cpc, min_runs=args.min_runs,
    )
    (args.output_dir / "tac_mad_summary.md").write_text(summary_md, encoding="utf-8")

    manifest = {
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "metrics": list(TAC_METRICS),
        "good_cpc": args.good_cpc,
        "poor_cpc": args.poor_cpc,
        "min_runs": args.min_runs,
        "n_subjects_total": n_total,
        "n_good": n_good,
        "n_poor": n_poor,
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nWrote results to {args.output_dir}")
    if not contrast.empty:
        print("\nTop contrasts (IQR + MAD, sorted by |d|):")
        for _, row in contrast.head(10).iterrows():
            print(
                f"  {row['metric_stat']:<55} d={row['cohens_d']:+.3f}  "
                f"p={row['mw_p']:.3g}  AUROC={row['auroc']:.3f}  "
                f"n={row[f'n_cpc{args.good_cpc}']}/{row[f'n_cpc{args.poor_cpc}']}"
            )


if __name__ == "__main__":
    main()
