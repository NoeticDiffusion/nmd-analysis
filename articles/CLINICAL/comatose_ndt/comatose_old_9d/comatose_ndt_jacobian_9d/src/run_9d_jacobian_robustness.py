from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from jacobian_9d_support import (
    ALL_ARTICLE_METRICS,
    GOOD_CPC,
    POOR_CPC,
    ROBUSTNESS_DIR,
    assemble_pooled_cohort,
    cohens_d,
    winsorize,
)


N_SPLITS = 5
N_REPEATS = 20
N_PERMUTATIONS = 2000
QC_COLUMNS = (
    "n_windows_total",
    "channel_count_median",
    "channel_coverage_frac_median",
)


def make_classifier() -> Pipeline:
    return Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    solver="liblinear",
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=20260525,
                ),
            ),
        ]
    )


def resolve_split_count(y: np.ndarray, requested_splits: int) -> int:
    class_counts = pd.Series(y).value_counts().to_dict()
    if len(class_counts) < 2:
        raise ValueError("Robustness checks require both CPC groups in the filtered cohort.")
    return min(requested_splits, int(min(class_counts.values())))


def subset_metric_contrasts(frame: pd.DataFrame, subset_label: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric in ALL_ARTICLE_METRICS:
        if metric not in frame.columns:
            continue
        good = pd.to_numeric(frame[frame["label"] == 1][metric], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(frame[frame["label"] == 0][metric], errors="coerce").dropna().to_numpy(dtype=float)
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
    rows: list[dict[str, Any]] = []
    for metric in ALL_ARTICLE_METRICS:
        values = pd.to_numeric(frame[metric], errors="coerce")
        for qc_col in QC_COLUMNS:
            qc_values = pd.to_numeric(frame[qc_col], errors="coerce")
            mask = np.isfinite(values) & np.isfinite(qc_values)
            if int(mask.sum()) < 3:
                rows.append(
                    {
                        "metric": metric,
                        "qc_variable": qc_col,
                        "n": int(mask.sum()),
                        "spearman_rho": np.nan,
                        "spearman_p": np.nan,
                    }
                )
                continue
            rho, p_value = stats.spearmanr(values[mask], qc_values[mask])
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


def evaluate_qc_only_model(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_frame = frame[["subject", "label", *QC_COLUMNS]].copy().dropna(subset=list(QC_COLUMNS)).reset_index(drop=True)
    y = model_frame["label"].astype(int).to_numpy()
    x = model_frame[list(QC_COLUMNS)]
    n_splits = resolve_split_count(y, N_SPLITS)
    splitter = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=N_REPEATS, random_state=20260525)
    rows = []
    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x, y)):
        model = make_classifier()
        model.fit(x.iloc[train_idx], y[train_idx])
        y_prob = model.predict_proba(x.iloc[test_idx])[:, 1]
        rows.append(
            {
                "fold": int(fold_idx),
                "roc_auc": float(roc_auc_score(y[test_idx], y_prob)),
                "average_precision": float(average_precision_score(y[test_idx], y_prob)),
                "brier_score": float(brier_score_loss(y[test_idx], y_prob)),
            }
        )
    scores = pd.DataFrame(rows)
    summary = pd.DataFrame(
        [
            {
                "n_subjects": int(len(model_frame)),
                "n_folds": int(len(scores)),
                "roc_auc_mean": float(scores["roc_auc"].mean()),
                "roc_auc_sd": float(scores["roc_auc"].std(ddof=1)),
                "average_precision_mean": float(scores["average_precision"].mean()),
                "average_precision_sd": float(scores["average_precision"].std(ddof=1)),
                "brier_score_mean": float(scores["brier_score"].mean()),
                "brier_score_sd": float(scores["brier_score"].std(ddof=1)),
            }
        ]
    )
    return scores, summary


def run_label_permutation(frame: pd.DataFrame) -> pd.DataFrame:
    base = frame[["subject", "label", *ALL_ARTICLE_METRICS]].copy()
    labels = base["label"].astype(int).to_numpy(dtype=int)
    rng = np.random.default_rng(20260525)
    observed_abs_d = {}
    for metric in ALL_ARTICLE_METRICS:
        good = pd.to_numeric(base[base["label"] == 1][metric], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(base[base["label"] == 0][metric], errors="coerce").dropna().to_numpy(dtype=float)
        observed_abs_d[metric] = abs(cohens_d(good, poor))

    perm_rows = []
    max_abs_values = []
    numeric_cache = {
        metric: pd.to_numeric(base[metric], errors="coerce").to_numpy(dtype=float) for metric in ALL_ARTICLE_METRICS
    }
    for perm_idx in range(N_PERMUTATIONS):
        shuffled = rng.permutation(labels)
        max_abs_d = 0.0
        for metric in ALL_ARTICLE_METRICS:
            values = numeric_cache[metric]
            good = values[shuffled == 1]
            poor = values[shuffled == 0]
            perm_d = abs(cohens_d(good, poor))
            perm_rows.append({"permutation": perm_idx, "metric": metric, "abs_cohens_d": float(perm_d)})
            if np.isfinite(perm_d):
                max_abs_d = max(max_abs_d, float(perm_d))
        max_abs_values.append(max_abs_d)
    perm_df = pd.DataFrame(perm_rows)
    rows = []
    for metric in ALL_ARTICLE_METRICS:
        metric_null = perm_df[perm_df["metric"] == metric]["abs_cohens_d"].to_numpy(dtype=float)
        rows.append(
            {
                "metric": metric,
                "observed_abs_cohens_d": float(observed_abs_d[metric]),
                "null_mean": float(np.nanmean(metric_null)),
                "null_p95": float(np.nanquantile(metric_null, 0.95)),
                "empirical_p": float((np.sum(metric_null >= observed_abs_d[metric]) + 1) / (len(metric_null) + 1)),
            }
        )
    max_abs_values = np.asarray(max_abs_values, dtype=float)
    rows.append(
        {
            "metric": "max_abs_cohens_d_across_article_metrics",
            "observed_abs_cohens_d": float(max(observed_abs_d.values())),
            "null_mean": float(np.nanmean(max_abs_values)),
            "null_p95": float(np.nanquantile(max_abs_values, 0.95)),
            "empirical_p": float((np.sum(max_abs_values >= max(observed_abs_d.values())) + 1) / (len(max_abs_values) + 1)),
        }
    )
    return pd.DataFrame(rows)


def winsorized_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric in ALL_ARTICLE_METRICS:
        full_values = pd.to_numeric(frame[metric], errors="coerce")
        low, high = np.nanquantile(full_values, [0.01, 0.99])
        clipped = full_values.clip(lower=low, upper=high)
        good_orig = pd.to_numeric(frame[frame["label"] == 1][metric], errors="coerce").dropna().to_numpy(dtype=float)
        poor_orig = pd.to_numeric(frame[frame["label"] == 0][metric], errors="coerce").dropna().to_numpy(dtype=float)
        good_clip = clipped[frame["label"] == 1].dropna().to_numpy(dtype=float)
        poor_clip = clipped[frame["label"] == 0].dropna().to_numpy(dtype=float)
        rows.append(
            {
                "metric": metric,
                "clip_low": float(low),
                "clip_high": float(high),
                "original_d": cohens_d(good_orig, poor_orig),
                "winsorized_d": cohens_d(good_clip, poor_clip),
                "delta_d": float(cohens_d(good_clip, poor_clip) - cohens_d(good_orig, poor_orig)),
            }
        )
    return pd.DataFrame(rows)


def leave_one_site_out_effects(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for held_out_site in sorted(frame["hospital"].fillna("missing").astype(str).unique()):
        subset = frame[frame["hospital"].fillna("missing").astype(str) != held_out_site].copy()
        for metric in ALL_ARTICLE_METRICS:
            good = pd.to_numeric(subset[subset["label"] == 1][metric], errors="coerce").dropna().to_numpy(dtype=float)
            poor = pd.to_numeric(subset[subset["label"] == 0][metric], errors="coerce").dropna().to_numpy(dtype=float)
            if good.size < 2 or poor.size < 2:
                continue
            u_stat, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
            rows.append(
                {
                    "held_out_site": held_out_site,
                    "metric": metric,
                    "n_cpc1": int(good.size),
                    "n_cpc5": int(poor.size),
                    "cohens_d": cohens_d(good, poor),
                    "mannwhitney_u": float(u_stat),
                    "mannwhitney_p": float(p_value),
                }
            )
    return pd.DataFrame(rows)


def build_summary_markdown(
    frame: pd.DataFrame,
    subset_contrasts: pd.DataFrame,
    qc_summary: pd.DataFrame,
    correlations: pd.DataFrame,
    permutation: pd.DataFrame,
    winsorized: pd.DataFrame,
) -> str:
    lines = [
        "# 9D Jacobian Robustness Summary",
        "",
        f"- n_subjects: `{int(len(frame))}`",
        f"- CPC1: `{int((frame['label'] == 1).sum())}`",
        f"- CPC5: `{int((frame['label'] == 0).sum())}`",
        f"- shockable available: `{int(frame['shockable_rhythm'].notna().sum())}`",
        "",
        "## Full-cohort contrasts",
        "",
    ]
    full = subset_contrasts[subset_contrasts["subset"] == "full"].copy()
    for _, row in full.sort_values("mannwhitney_p").iterrows():
        lines.append(
            f"- `{row['metric']}`: medians `{row['cpc1_median']:.6g}` vs `{row['cpc5_median']:.6g}`, "
            f"`d = {row['cohens_d']:.3f}`, `p = {row['mannwhitney_p']:.3g}`"
        )
    for subset_label in ("shockable_only", "nonshockable_only"):
        subset = subset_contrasts[subset_contrasts["subset"] == subset_label].copy()
        if subset.empty:
            continue
        lines.extend(["", f"## {subset_label.replace('_', ' ').title()}", ""])
        for _, row in subset.sort_values("mannwhitney_p").iterrows():
            lines.append(
                f"- `{row['metric']}`: medians `{row['cpc1_median']:.6g}` vs `{row['cpc5_median']:.6g}`, "
                f"`d = {row['cohens_d']:.3f}`, `p = {row['mannwhitney_p']:.3g}`"
            )
    lines.extend(
        [
            "",
            "## QC-only model",
            "",
            f"- ROC AUC: `{qc_summary.iloc[0]['roc_auc_mean']:.3f} +/- {qc_summary.iloc[0]['roc_auc_sd']:.3f}`",
            f"- AUPRC: `{qc_summary.iloc[0]['average_precision_mean']:.3f} +/- {qc_summary.iloc[0]['average_precision_sd']:.3f}`",
            f"- Brier: `{qc_summary.iloc[0]['brier_score_mean']:.3f} +/- {qc_summary.iloc[0]['brier_score_sd']:.3f}`",
            "",
            "## Strongest QC correlations",
            "",
        ]
    )
    corr_view = correlations.reindex(correlations["spearman_rho"].abs().sort_values(ascending=False).index).head(8)
    for _, row in corr_view.iterrows():
        lines.append(
            f"- `{row['metric']}` vs `{row['qc_variable']}`: rho=`{row['spearman_rho']:.3f}`, p=`{row['spearman_p']:.3g}`"
        )
    lines.extend(["", "## Label permutation", ""])
    for _, row in permutation.iterrows():
        lines.append(
            f"- `{row['metric']}`: observed abs `d = {row['observed_abs_cohens_d']:.3f}`, "
            f"null p95 `{row['null_p95']:.3f}`, empirical `p = {row['empirical_p']:.4f}`"
        )
    lines.extend(["", "## Winsorization sensitivity", ""])
    for _, row in winsorized.sort_values("delta_d", key=np.abs, ascending=False).iterrows():
        lines.append(
            f"- `{row['metric']}`: original `d = {row['original_d']:.3f}`, winsorized `d = {row['winsorized_d']:.3f}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ROBUSTNESS_DIR.mkdir(parents=True, exist_ok=True)
    frame = assemble_pooled_cohort(include_reachability=False)
    full = subset_metric_contrasts(frame, "full")
    shockable = subset_metric_contrasts(frame[frame["shockable_rhythm"] == 1.0].copy(), "shockable_only")
    nonshockable = subset_metric_contrasts(frame[frame["shockable_rhythm"] == 0.0].copy(), "nonshockable_only")
    subset_contrasts = pd.concat([full, shockable, nonshockable], ignore_index=True)
    qc_scores, qc_summary = evaluate_qc_only_model(frame)
    correlations = qc_metric_correlations(frame)
    permutation = run_label_permutation(frame)
    winsorized = winsorized_sensitivity(frame)
    site_leaveout = leave_one_site_out_effects(frame)

    subset_contrasts.to_csv(ROBUSTNESS_DIR / "subset_metric_contrasts.csv", index=False)
    qc_scores.to_csv(ROBUSTNESS_DIR / "qc_only_model_fold_scores.csv", index=False)
    qc_summary.to_csv(ROBUSTNESS_DIR / "qc_only_model_summary.csv", index=False)
    correlations.to_csv(ROBUSTNESS_DIR / "metric_qc_correlations.csv", index=False)
    permutation.to_csv(ROBUSTNESS_DIR / "label_permutation_summary.csv", index=False)
    winsorized.to_csv(ROBUSTNESS_DIR / "winsorization_sensitivity.csv", index=False)
    site_leaveout.to_csv(ROBUSTNESS_DIR / "leave_one_site_out_effects.csv", index=False)
    (ROBUSTNESS_DIR / "robustness_summary.md").write_text(
        build_summary_markdown(frame, subset_contrasts, qc_summary, correlations, permutation, winsorized),
        encoding="utf-8",
    )
    manifest = {
        "output_dir": str(ROBUSTNESS_DIR),
        "n_subjects": int(len(frame)),
        "good_cpc": GOOD_CPC,
        "poor_cpc": POOR_CPC,
        "article_metrics": list(ALL_ARTICLE_METRICS),
        "qc_columns": list(QC_COLUMNS),
        "n_splits": N_SPLITS,
        "n_repeats": N_REPEATS,
        "n_permutations": N_PERMUTATIONS,
    }
    (ROBUSTNESS_DIR / "robustness_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote 9D Jacobian robustness outputs to {ROBUSTNESS_DIR}")


if __name__ == "__main__":
    main()
