from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold

from incremental_validity_analysis import DEFAULT_RANDOM_STATE, make_classifier, resolve_split_count


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = ARTICLE_DIR / "results"
DEFAULT_INCREMENTAL_DIR = ARTICLE_DIR / "results" / "incremental_validity_20260517_cpc15_primary12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "robustness_checks_20260518_cpc15"
PRIMARY_TIME_BIN = "0_12h"
GOOD_CPC = 1
POOR_CPC = 5
N_SPLITS = 5
N_REPEATS = 20
N_PERMUTATIONS = 2000

GEOMETRY_COLUMNS = [
    "geom_tube_d_eff_median",
    "geom_persistence_kappa_median",
    "geom_persistence_log_eig_var_median",
    "geom_tube_a_operator_norm_median",
    "geom_tube_capture_gate_median",
]
QC_COLUMNS = [
    "qc__n_windows_total",
    "clinical__channel_count_median",
    "clinical__channel_coverage_frac_median",
]


@dataclass(frozen=True)
class Config:
    results_dir: Path
    timeline_dir: Path
    incremental_dir: Path
    output_dir: Path
    primary_time_bin: str
    good_cpc: int
    poor_cpc: int
    n_splits: int
    n_repeats: int
    random_state: int
    n_permutations: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Run robustness and QC checks for the coma manuscript.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument(
        "--timeline-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "timeline_analysis_20260517_cpc15_primary12h",
    )
    parser.add_argument("--incremental-dir", type=Path, default=DEFAULT_INCREMENTAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--n-splits", type=int, default=N_SPLITS)
    parser.add_argument("--n-repeats", type=int, default=N_REPEATS)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    parser.add_argument("--n-permutations", type=int, default=N_PERMUTATIONS)
    args = parser.parse_args()
    return Config(
        results_dir=args.results_dir,
        timeline_dir=args.timeline_dir,
        incremental_dir=args.incremental_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        n_splits=args.n_splits,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
        n_permutations=args.n_permutations,
    )


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (good.size + poor.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def load_cohort(config: Config) -> pd.DataFrame:
    cohort = pd.read_csv(config.incremental_dir / "incremental_validity_cohort.csv")
    timeline = pd.read_csv(config.timeline_dir / "patient_timebin_summaries.csv")
    timeline = timeline[timeline["time_bin"] == config.primary_time_bin].copy()
    timeline["cpc_numeric"] = pd.to_numeric(timeline["cpc"], errors="coerce")
    timeline = timeline[timeline["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    extra = timeline[
        [
            "subject",
            "n_windows_total",
            "artifact_detector_enabled_all",
            "artifact_burden_mean",
            "time_reference_available_all",
            "recording_start_after_anchor_hours",
        ]
    ].copy()
    extra = extra.rename(columns={"n_windows_total": "qc__n_windows_total"})
    extra["qc__n_windows_total"] = pd.to_numeric(extra["qc__n_windows_total"], errors="coerce")
    return cohort.merge(extra, on="subject", how="left")


def subset_metric_contrasts(frame: pd.DataFrame, subset_label: str, subset_mask: pd.Series) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    sub = frame[subset_mask].copy()
    for metric in GEOMETRY_COLUMNS:
        if metric not in sub.columns:
            continue
        good = pd.to_numeric(sub[sub["label"] == 1][metric], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(sub[sub["label"] == 0][metric], errors="coerce").dropna().to_numpy(dtype=float)
        if good.size < 2 or poor.size < 2:
            continue
        u_stat, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
        rows.append(
            {
                "subset": subset_label,
                "metric": metric,
                "n_cpc1": int(good.size),
                "n_cpc5": int(poor.size),
                "cpc1_median": float(np.median(good)),
                "cpc5_median": float(np.median(poor)),
                "cohens_d": cohens_d(good, poor),
                "mannwhitney_u": float(u_stat),
                "mannwhitney_p": float(p_value),
            }
        )
    return pd.DataFrame(rows)


def qc_metric_correlations(frame: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for metric in GEOMETRY_COLUMNS:
        metric_values = pd.to_numeric(frame[metric], errors="coerce")
        for qc_col in QC_COLUMNS:
            if qc_col not in frame.columns:
                continue
            qc_values = pd.to_numeric(frame[qc_col], errors="coerce")
            mask = np.isfinite(metric_values) & np.isfinite(qc_values)
            if int(mask.sum()) < 3:
                rows.append({"metric": metric, "qc_variable": qc_col, "n": int(mask.sum()), "spearman_rho": np.nan, "spearman_p": np.nan})
                continue
            rho, p_value = stats.spearmanr(metric_values[mask], qc_values[mask])
            rows.append(
                {
                    "metric": metric,
                    "qc_variable": qc_col,
                    "n": int(mask.sum()),
                    "spearman_rho": float(rho),
                    "spearman_p": float(p_value),
                }
            )
    return pd.DataFrame(rows)


def compute_binary_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
    }


def evaluate_qc_only_model(frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    qc_columns = [
        column
        for column in QC_COLUMNS
        if column in frame.columns and pd.to_numeric(frame[column], errors="coerce").notna().sum() > 0
    ]
    if not qc_columns:
        return pd.DataFrame()
    model_frame = frame[["subject", "label", *qc_columns]].copy()
    model_frame = model_frame.dropna(subset=qc_columns).reset_index(drop=True)
    y = model_frame["label"].astype(int).to_numpy()
    n_splits = resolve_split_count(y, config.n_splits)
    splitter = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=config.n_repeats, random_state=config.random_state)
    rows: List[Dict[str, Any]] = []
    x = model_frame[qc_columns].copy()
    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x, y)):
        model = make_classifier(config.random_state)
        model.fit(x.iloc[train_idx], y[train_idx])
        y_prob = model.predict_proba(x.iloc[test_idx])[:, 1]
        rows.append(
            {
                "evaluation": "qc_only_repeated_cv",
                "fold": int(fold_idx),
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "n_features": int(len(qc_columns)),
                **compute_binary_metrics(y[test_idx], y_prob),
            }
        )
    return pd.DataFrame(rows)


def summarize_qc_model(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return pd.DataFrame()
    row: Dict[str, Any] = {"evaluation": "qc_only_repeated_cv", "n_folds": int(len(scores)), "n_features": int(scores["n_features"].median())}
    for metric in ("roc_auc", "average_precision", "brier_score"):
        values = scores[metric].to_numpy(dtype=float)
        row[f"{metric}_mean"] = float(np.mean(values))
        row[f"{metric}_sd"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return pd.DataFrame([row])


def run_label_permutation(frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = frame[["subject", "label", *GEOMETRY_COLUMNS]].copy()
    observed_rows: List[Dict[str, Any]] = []
    observed_abs_d: Dict[str, float] = {}
    for metric in GEOMETRY_COLUMNS:
        good = pd.to_numeric(base[base["label"] == 1][metric], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(base[base["label"] == 0][metric], errors="coerce").dropna().to_numpy(dtype=float)
        observed_abs_d[metric] = abs(cohens_d(good, poor))
    observed_max = max(observed_abs_d.values())

    rng = np.random.default_rng(config.random_state)
    perm_rows: List[Dict[str, Any]] = []
    max_rows: List[Dict[str, Any]] = []
    labels = base["label"].to_numpy(dtype=int)
    for perm_idx in range(config.n_permutations):
        shuffled = rng.permutation(labels)
        max_abs_d = 0.0
        for metric in GEOMETRY_COLUMNS:
            values = pd.to_numeric(base[metric], errors="coerce").to_numpy(dtype=float)
            good = values[shuffled == 1]
            poor = values[shuffled == 0]
            good = good[np.isfinite(good)]
            poor = poor[np.isfinite(poor)]
            perm_d = abs(cohens_d(good, poor))
            perm_rows.append({"permutation": perm_idx, "metric": metric, "abs_cohens_d": float(perm_d)})
            if np.isfinite(perm_d):
                max_abs_d = max(max_abs_d, float(perm_d))
        max_rows.append({"permutation": perm_idx, "max_abs_cohens_d": max_abs_d})

    perm_df = pd.DataFrame(perm_rows)
    max_df = pd.DataFrame(max_rows)
    for metric in GEOMETRY_COLUMNS:
        sub = perm_df[perm_df["metric"] == metric]["abs_cohens_d"].to_numpy(dtype=float)
        observed_rows.append(
            {
                "metric": metric,
                "observed_abs_cohens_d": float(observed_abs_d[metric]),
                "null_mean_abs_cohens_d": float(np.mean(sub)),
                "null_p95_abs_cohens_d": float(np.quantile(sub, 0.95)),
                "empirical_p": float((1.0 + np.sum(sub >= observed_abs_d[metric])) / (len(sub) + 1.0)),
            }
        )
    observed_rows.append(
        {
            "metric": "max_abs_cohens_d_across_selected_metrics",
            "observed_abs_cohens_d": float(observed_max),
            "null_mean_abs_cohens_d": float(max_df["max_abs_cohens_d"].mean()),
            "null_p95_abs_cohens_d": float(max_df["max_abs_cohens_d"].quantile(0.95)),
            "empirical_p": float((1.0 + np.sum(max_df["max_abs_cohens_d"].to_numpy(dtype=float) >= observed_max)) / (len(max_df) + 1.0)),
        }
    )
    return pd.DataFrame(observed_rows), max_df


def write_summary(
    frame: pd.DataFrame,
    shockable: pd.DataFrame,
    nonshockable: pd.DataFrame,
    correlations: pd.DataFrame,
    qc_model_summary: pd.DataFrame,
    permutation_summary: pd.DataFrame,
) -> str:
    shockable_known = int(pd.to_numeric(frame["clinical__shockable_rhythm"], errors="coerce").notna().sum())
    shockable_pos = int((pd.to_numeric(frame["clinical__shockable_rhythm"], errors="coerce") == 1.0).sum())
    lines = [
        "# Coma Robustness Checks",
        "",
        f"- n_subjects: `{len(frame)}`",
        f"- selected geometry metrics: `{', '.join(GEOMETRY_COLUMNS)}`",
        f"- shockable status available for: `{shockable_known}` subjects",
        f"- shockable subjects: `{shockable_pos}`",
        "- artifact detector status: unavailable for quantitative use in the locked export (`artifact_detector_enabled_all` is constant false and `artifact_burden_mean` is missing)",
        "- WLST / time-of-death sensitivity: not available from the locked manuscript result bundle",
        "- time-order disruption control: not run here because an honest test would require re-estimation from reordered trajectories rather than post hoc reshuffling of already-derived reachability summaries",
        "",
    ]
    if not shockable.empty:
        lines.extend(["## Shockable-only subset", ""])
        for _, row in shockable.iterrows():
            lines.append(
                f"- `{row['metric']}`: medians `{row['cpc1_median']:.3f}` vs `{row['cpc5_median']:.3f}`, "
                f"Cohen's `d = {row['cohens_d']:.3f}`, Mann-Whitney `p = {row['mannwhitney_p']:.3g}`"
            )
        lines.append("")
    if not nonshockable.empty:
        lines.extend(["## Non-shockable-only subset", ""])
        for _, row in nonshockable.iterrows():
            lines.append(
                f"- `{row['metric']}`: medians `{row['cpc1_median']:.3f}` vs `{row['cpc5_median']:.3f}`, "
                f"Cohen's `d = {row['cohens_d']:.3f}`, Mann-Whitney `p = {row['mannwhitney_p']:.3g}`"
            )
        lines.append("")
    if not qc_model_summary.empty:
        row = qc_model_summary.iloc[0]
        available_qc = [
            column
            for column in QC_COLUMNS
            if column in frame.columns and pd.to_numeric(frame[column], errors="coerce").notna().sum() > 0
        ]
        lines.extend(
            [
                "## QC / coverage-only prediction model",
                "",
                f"- features: `{', '.join(available_qc)}`",
                f"- ROC AUC: `{row['roc_auc_mean']:.3f} +/- {row['roc_auc_sd']:.3f}`",
                f"- AUPRC: `{row['average_precision_mean']:.3f} +/- {row['average_precision_sd']:.3f}`",
                f"- Brier: `{row['brier_score_mean']:.3f} +/- {row['brier_score_sd']:.3f}`",
                "",
            ]
        )
    if not correlations.empty:
        lines.extend(["## Geometry versus QC associations (Spearman)", ""])
        for _, row in correlations.iterrows():
            lines.append(
                f"- `{row['metric']}` vs `{row['qc_variable']}`: rho=`{row['spearman_rho']:.3f}`, p=`{row['spearman_p']:.3g}` (n=`{int(row['n'])}`)"
            )
        lines.append("")
    if not permutation_summary.empty:
        lines.extend(["## Patient-label permutation", ""])
        for _, row in permutation_summary.iterrows():
            lines.append(
                f"- `{row['metric']}`: observed max/abs `d = {row['observed_abs_cohens_d']:.3f}`, "
                f"null mean `{row['null_mean_abs_cohens_d']:.3f}`, null p95 `{row['null_p95_abs_cohens_d']:.3f}`, empirical `p = {row['empirical_p']:.3g}`"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    frame = load_cohort(config)
    shockable_mask = pd.to_numeric(frame["clinical__shockable_rhythm"], errors="coerce") == 1.0
    nonshockable_mask = pd.to_numeric(frame["clinical__shockable_rhythm"], errors="coerce") == 0.0

    shockable = subset_metric_contrasts(frame, "shockable_only", shockable_mask)
    nonshockable = subset_metric_contrasts(frame, "nonshockable_only", nonshockable_mask)
    correlations = qc_metric_correlations(frame)
    qc_scores = evaluate_qc_only_model(frame, config)
    qc_summary = summarize_qc_model(qc_scores)
    permutation_summary, permutation_max = run_label_permutation(frame, config)

    frame.to_csv(config.output_dir / "robustness_cohort.csv", index=False)
    shockable.to_csv(config.output_dir / "shockable_only_selected_metric_contrasts.csv", index=False)
    nonshockable.to_csv(config.output_dir / "nonshockable_only_selected_metric_contrasts.csv", index=False)
    correlations.to_csv(config.output_dir / "geometry_qc_correlations.csv", index=False)
    qc_scores.to_csv(config.output_dir / "qc_only_model_fold_scores.csv", index=False)
    qc_summary.to_csv(config.output_dir / "qc_only_model_summary.csv", index=False)
    permutation_summary.to_csv(config.output_dir / "label_permutation_summary.csv", index=False)
    permutation_max.to_csv(config.output_dir / "label_permutation_max_abs_d_null.csv", index=False)
    (config.output_dir / "robustness_checks_summary.md").write_text(
        write_summary(frame, shockable, nonshockable, correlations, qc_summary, permutation_summary),
        encoding="utf-8",
    )
    (config.output_dir / "robustness_checks_manifest.json").write_text(
        json.dumps(
            {
                "results_dir": str(config.results_dir),
                "timeline_dir": str(config.timeline_dir),
                "incremental_dir": str(config.incremental_dir),
                "primary_time_bin": config.primary_time_bin,
                "selected_geometry_columns": GEOMETRY_COLUMNS,
                "qc_columns": QC_COLUMNS,
                "n_permutations": config.n_permutations,
                "notes": {
                    "artifact_detector": "constant false in locked export; direct artifact burden unavailable",
                    "wlst": "not available in locked manuscript result bundle",
                    "time_shuffle": "not performed because it would require upstream re-estimation from reordered trajectories",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote robustness checks to {config.output_dir}")


if __name__ == "__main__":
    main()
