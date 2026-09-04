"""
compute_between_run_iqr_mad.py — between-run IQR and MAD for 12-24h pilot metrics.

This is the 12-24h pilot-local variant of the between-run variability analysis.
For each patient and metric, it computes:

  between-run IQR = q75(runs) - q25(runs)
  between-run MAD = median |x_run - median(runs)|

The script is intentionally scoped to the fixed five 12-24h reachability metrics.
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
RESULTS_DIR = ARTICLE_DIR / "results"

DEFAULT_INPUT_DIR = RESULTS_DIR / "mnps_summary_20260608_part1_noregional_subjectanchor_primary12h_true1224"
DEFAULT_OUTPUT_DIR = RESULTS_DIR / "between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min2"

DEFAULT_METRICS: tuple[str, ...] = (
    "tube_d_eff_median",
    "persistence_kappa_median",
    "persistence_log_eig_var_median",
    "tube_a_operator_norm_median",
    "tube_capture_gate_median",
)

GOOD_CPC = 1
POOR_CPC = 5
PRIMARY_TIME_BIN = "12_24h"
MIN_RUNS = 2


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    g = good[np.isfinite(good)]
    p = poor[np.isfinite(poor)]
    if g.size < 2 or p.size < 2:
        return float("nan")
    pooled_var = ((g.size - 1) * np.var(g, ddof=1) + (p.size - 1) * np.var(p, ddof=1)) / (g.size + p.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((np.mean(g) - np.mean(p)) / np.sqrt(pooled_var))


def compute_between_run_stats(
    run_metrics: pd.DataFrame,
    *,
    metrics: tuple[str, ...],
    time_bin: str,
    min_runs: int,
) -> pd.DataFrame:
    subset = run_metrics[
        (run_metrics["time_bin"] == time_bin) & (run_metrics["metric"].isin(metrics))
    ].copy()
    subset["value"] = pd.to_numeric(subset["value"], errors="coerce")

    rows: list[dict[str, Any]] = []
    for subject, subj_frame in subset.groupby("subject"):
        row: dict[str, Any] = {"subject": subject}
        for metric in metrics:
            vals = subj_frame.loc[subj_frame["metric"] == metric, "value"].dropna().to_numpy(dtype=float)
            n = int(np.isfinite(vals).sum())
            row[f"n_runs_{metric}"] = n
            if n >= min_runs:
                finite = vals[np.isfinite(vals)]
                q25, q75 = float(np.percentile(finite, 25)), float(np.percentile(finite, 75))
                med = float(np.median(finite))
                row[f"{metric}_iqr"] = q75 - q25
                row[f"{metric}_mad"] = float(np.median(np.abs(finite - med)))
            else:
                row[f"{metric}_iqr"] = float("nan")
                row[f"{metric}_mad"] = float("nan")
        rows.append(row)

    return pd.DataFrame(rows).sort_values("subject").reset_index(drop=True)


def load_cpc_labels(input_dir: Path, *, good_cpc: int, poor_cpc: int) -> pd.DataFrame:
    path = input_dir / "subject_outcome_index.csv"
    frame = pd.read_csv(path, low_memory=False)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(good_cpc), float(poor_cpc)])].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(good_cpc), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, f"CPC{good_cpc}", f"CPC{poor_cpc}")
    return frame[["subject", "cpc", "cpc_numeric", "label", "label_name"]].drop_duplicates("subject")


def build_contrast_table(
    patient_stats: pd.DataFrame,
    stat_cols: list[str],
    *,
    good_cpc: int,
    poor_cpc: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for col in stat_cols:
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
        return pd.DataFrame(columns=["metric_stat"])
    return pd.DataFrame(rows).sort_values("abs_d", ascending=False).reset_index(drop=True)


def build_markdown(
    contrast: pd.DataFrame,
    *,
    n_total: int,
    n_good: int,
    n_poor: int,
    good_cpc: int,
    poor_cpc: int,
    time_bin: str,
    min_runs: int,
    metrics: tuple[str, ...],
) -> str:
    lines = [
        "# Between-run IQR and MAD — 12-24h pilot",
        "",
        f"- cohort: `{n_total}` subjects (`{n_good}` CPC{good_cpc}, `{n_poor}` CPC{poor_cpc})",
        f"- time bin: `{time_bin}`",
        f"- minimum runs for IQR/MAD: `{min_runs}`",
        f"- metrics: {', '.join(f'`{m}`' for m in metrics)}",
        "",
        "## Contrasts",
        "",
    ]

    if contrast.empty or "metric_stat" not in contrast.columns:
        lines.append("No contrast rows available under the current minimum-run threshold.")
        lines.append("")
        lines.append("This commonly occurs when most patients contribute only one run in the selected time bin.")
        return "\n".join(lines)

    iqr_rows = contrast[contrast["metric_stat"].str.endswith("_iqr")]
    mad_rows = contrast[contrast["metric_stat"].str.endswith("_mad")]

    lines.append("### IQR")
    if iqr_rows.empty:
        lines.append("- No IQR rows available.")
    else:
        for _, row in iqr_rows.iterrows():
            lines.append(
                f"- `{row['metric_stat']}`: "
                f"CPC{good_cpc} `{row[f'cpc{good_cpc}_median']:.4g}` vs "
                f"CPC{poor_cpc} `{row[f'cpc{poor_cpc}_median']:.4g}`, "
                f"d=`{row['cohens_d']:+.3f}`, p=`{row['mw_p']:.3g}`, n=`{int(row[f'n_cpc{good_cpc}'])}/{int(row[f'n_cpc{poor_cpc}'])}`"
            )

    lines.append("")
    lines.append("### MAD")
    if mad_rows.empty:
        lines.append("- No MAD rows available.")
    else:
        for _, row in mad_rows.iterrows():
            lines.append(
                f"- `{row['metric_stat']}`: "
                f"CPC{good_cpc} `{row[f'cpc{good_cpc}_median']:.4g}` vs "
                f"CPC{poor_cpc} `{row[f'cpc{poor_cpc}_median']:.4g}`, "
                f"d=`{row['cohens_d']:+.3f}`, p=`{row['mw_p']:.3g}`, n=`{int(row[f'n_cpc{good_cpc}'])}/{int(row[f'n_cpc{poor_cpc}'])}`"
            )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1].strip())
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--min-runs", type=int, default=MIN_RUNS)
    parser.add_argument(
        "--metric",
        dest="metrics",
        action="append",
        default=None,
        help="Metric to include. Repeat to specify multiple. Defaults to the 12-24h five-metric set.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics: tuple[str, ...] = tuple(args.metrics) if args.metrics else DEFAULT_METRICS
    ensure_dir(args.output_dir)

    print(f"Loading run-level signal metrics from {args.input_dir}...")
    run_metrics = pd.read_csv(args.input_dir / "run_level_signal_metrics.csv", low_memory=False)
    print(f"  {len(run_metrics):,} rows loaded")

    print("Loading CPC labels...")
    cpc_labels = load_cpc_labels(args.input_dir, good_cpc=args.good_cpc, poor_cpc=args.poor_cpc)
    print(f"  {len(cpc_labels)} subjects with CPC {args.good_cpc} or {args.poor_cpc}")

    print(f"Computing between-run IQR and MAD (time_bin={args.time_bin}, min_runs={args.min_runs})...")
    patient_stats = compute_between_run_stats(
        run_metrics,
        metrics=metrics,
        time_bin=args.time_bin,
        min_runs=args.min_runs,
    )
    print(f"  {len(patient_stats)} subjects with any qualifying runs")

    patient_stats = patient_stats.merge(cpc_labels, on="subject", how="inner")
    n_total = len(patient_stats)
    n_good = int((patient_stats["label"] == 1).sum())
    n_poor = int((patient_stats["label"] == 0).sum())
    print(f"  After CPC join: {n_total} subjects ({n_good} CPC{args.good_cpc}, {n_poor} CPC{args.poor_cpc})")

    patient_stats.to_csv(args.output_dir / "patient_between_run_stats.csv", index=False)

    stat_cols = [f"{m}_iqr" for m in metrics] + [f"{m}_mad" for m in metrics]
    contrast = build_contrast_table(
        patient_stats,
        stat_cols,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )
    contrast.to_csv(args.output_dir / "contrast_iqr_mad.csv", index=False)

    summary_md = build_markdown(
        contrast,
        n_total=n_total,
        n_good=n_good,
        n_poor=n_poor,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        time_bin=args.time_bin,
        min_runs=args.min_runs,
        metrics=metrics,
    )
    (args.output_dir / "iqr_mad_summary.md").write_text(summary_md, encoding="utf-8")

    manifest = {
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "metrics": list(metrics),
        "time_bin": args.time_bin,
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
        for _, row in contrast.head(8).iterrows():
            print(
                f"  {row['metric_stat']:<55} d={row['cohens_d']:+.3f}  "
                f"p={row['mw_p']:.3g}  AUROC={row['auroc']:.3f}"
            )


if __name__ == "__main__":
    main()
