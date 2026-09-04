from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold

from jacobian_9d_support import ARTICLE_DIR, REACHABILITY_FEATURES, REVISED_CORE_METRICS
from run_9d_jacobian_incremental_validity import (
    build_model_frame,
    compute_metrics,
    get_feature_sets,
    make_classifier,
    resolve_split_count,
    summarize_scores,
)


DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "subset_scan_20260526_cpc15_primary12h"
N_SPLITS = 5
DEFAULT_N_REPEATS = 20
RANDOM_STATE = 20260525

DISPLAY_NAMES = {
    "spectral_radius_median": "spectral_radius_median",
    "anisotropy_abs_eig_median": "anisotropy_abs_eig_median",
    "mdr_median": "mdr_median",
    "rotational_power_mean": "rotational_power_mean",
    "rotational_power_median": "rotational_power_median",
    "tube_d_eff_median": "tube_d_eff_median",
    "persistence_kappa_median": "persistence_kappa_median",
    "persistence_log_eig_var_median": "persistence_log_eig_var_median",
    "tube_a_operator_norm_median": "tube_a_operator_norm_median",
    "tube_capture_gate_median": "tube_capture_gate_median",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an exploratory subset scan for revised 9D Jacobian and mixed reachability models."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--n-repeats", type=int, default=DEFAULT_N_REPEATS)
    return parser.parse_args()


def feature_label(feature: str) -> str:
    return feature.split("__", 1)[1]


def model_label(features: list[str]) -> str:
    return "+".join(feature_label(feature) for feature in features)


def add_model(
    feature_sets: dict[str, list[str]],
    metadata_rows: list[dict[str, object]],
    *,
    model_name: str,
    features: list[str],
    display_features: list[str] | None = None,
    category: str,
    base_model: str | None,
    scan_family: str,
    subset_size: int,
) -> None:
    feature_sets[model_name] = list(features)
    display = list(display_features or features)
    raw_metrics = [feature_label(feature) for feature in display]
    metadata_rows.append(
        {
            "model": model_name,
            "category": category,
            "scan_family": scan_family,
            "base_model": base_model or "",
            "subset_size": int(subset_size),
            "n_features": int(len(features)),
            "metric_label": model_label(display),
            "metrics_json": json.dumps(raw_metrics),
            "includes_jacobian9d": bool(any(feature.startswith("jac9d__") for feature in features)),
            "includes_reachability": bool(any(feature.startswith("reach__") for feature in features)),
        }
    )


def build_feature_catalog(frame: pd.DataFrame) -> tuple[dict[str, list[str]], pd.DataFrame]:
    feature_sets: dict[str, list[str]] = {}
    metadata_rows: list[dict[str, object]] = []

    base_sets = get_feature_sets(frame)
    baseline_models = {
        "clinical_plus_eeg": base_sets["clinical_plus_eeg"],
        "jacobian9d_only": base_sets["jacobian9d_only"],
        "reachability_only": base_sets["reachability_only"],
        "clinical_plus_eeg_plus_jacobian9d": base_sets["clinical_plus_eeg_plus_jacobian9d"],
        "clinical_plus_eeg_plus_reachability": base_sets["clinical_plus_eeg_plus_reachability"],
        "clinical_plus_eeg_plus_reachability_plus_jacobian9d": base_sets[
            "clinical_plus_eeg_plus_reachability_plus_jacobian9d"
        ],
    }
    for model_name, features in baseline_models.items():
        add_model(
            feature_sets,
            metadata_rows,
            model_name=model_name,
            features=features,
            display_features=features,
            category="baseline",
            base_model=None,
            scan_family="baseline",
            subset_size=0,
        )

    revised_features = [f"jac9d__{metric}" for metric in REVISED_CORE_METRICS]
    reach_features = [f"reach__{metric}" for metric in REACHABILITY_FEATURES]
    clinical_plus_eeg = list(base_sets["clinical_plus_eeg"])
    clinical_plus_eeg_plus_reachability = list(base_sets["clinical_plus_eeg_plus_reachability"])

    for subset_size in range(1, len(revised_features) + 1):
        for combo in itertools.combinations(revised_features, subset_size):
            combo_features = list(combo)
            combo_label = model_label(combo_features)
            add_model(
                feature_sets,
                metadata_rows,
                model_name=f"revised_only__{combo_label}",
                features=combo_features,
                display_features=combo_features,
                category="revised_only",
                base_model="jacobian9d_only",
                scan_family="revised_9d",
                subset_size=subset_size,
            )
            add_model(
                feature_sets,
                metadata_rows,
                model_name=f"clinical_plus_eeg__revised__{combo_label}",
                features=clinical_plus_eeg + combo_features,
                display_features=combo_features,
                category="clinical_plus_eeg_plus_revised_subset",
                base_model="clinical_plus_eeg_plus_jacobian9d",
                scan_family="revised_9d",
                subset_size=subset_size,
            )
            add_model(
                feature_sets,
                metadata_rows,
                model_name=f"clinical_plus_eeg_plus_reachability__revised__{combo_label}",
                features=clinical_plus_eeg_plus_reachability + combo_features,
                display_features=combo_features,
                category="clinical_plus_eeg_plus_reachability_plus_revised_subset",
                base_model="clinical_plus_eeg_plus_reachability_plus_jacobian9d",
                scan_family="revised_9d",
                subset_size=subset_size,
            )

    mixed_pool = revised_features + reach_features
    for subset_size in (2, 3):
        for combo in itertools.combinations(mixed_pool, subset_size):
            combo_features = list(combo)
            has_jacobian = any(feature.startswith("jac9d__") for feature in combo_features)
            has_reachability = any(feature.startswith("reach__") for feature in combo_features)
            if not (has_jacobian and has_reachability):
                continue
            combo_label = model_label(combo_features)
            add_model(
                feature_sets,
                metadata_rows,
                model_name=f"mixed_only__{combo_label}",
                features=combo_features,
                display_features=combo_features,
                category=f"mixed_cross_family_only_size_{subset_size}",
                base_model=None,
                scan_family="mixed_cross_family",
                subset_size=subset_size,
            )
            add_model(
                feature_sets,
                metadata_rows,
                model_name=f"clinical_plus_eeg__mixed__{combo_label}",
                features=clinical_plus_eeg + combo_features,
                display_features=combo_features,
                category=f"clinical_plus_eeg_plus_mixed_cross_family_size_{subset_size}",
                base_model="clinical_plus_eeg",
                scan_family="mixed_cross_family",
                subset_size=subset_size,
            )

    metadata = pd.DataFrame(metadata_rows).drop_duplicates(subset=["model"]).reset_index(drop=True)
    return feature_sets, metadata


def evaluate_repeated_cv(frame: pd.DataFrame, feature_sets: dict[str, list[str]], *, n_repeats: int) -> pd.DataFrame:
    y = frame["label"].astype(int).to_numpy()
    x_all = frame.drop(columns=["subject", "hospital", "label", "label_name"]).copy()
    n_splits = resolve_split_count(y, N_SPLITS)
    splitter = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=RANDOM_STATE)
    rows: list[dict[str, object]] = []
    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x_all, y)):
        for model_name, columns in feature_sets.items():
            model = make_classifier()
            model.fit(x_all.iloc[train_idx][columns], y[train_idx])
            y_prob = model.predict_proba(x_all.iloc[test_idx][columns])[:, 1]
            rows.append(
                {
                    "evaluation": "repeated_stratified_cv",
                    "fold": int(fold_idx),
                    "model": model_name,
                    "n_features": int(len(columns)),
                    **compute_metrics(y[test_idx], y_prob),
                }
            )
    return pd.DataFrame(rows)


def evaluate_leave_one_site_out(frame: pd.DataFrame, feature_sets: dict[str, list[str]]) -> pd.DataFrame:
    y = frame["label"].astype(int).to_numpy()
    groups = frame["hospital"].fillna("missing").astype(str).to_numpy()
    x_all = frame.drop(columns=["subject", "hospital", "label", "label_name"]).copy()
    splitter = LeaveOneGroupOut()
    rows: list[dict[str, object]] = []
    for model_name, columns in feature_sets.items():
        loso_columns = [column for column in columns if not column.startswith("cat__hospital_")]
        for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x_all, y, groups)):
            if len(np.unique(y[train_idx])) < 2 or len(np.unique(y[test_idx])) < 2:
                continue
            model = make_classifier()
            model.fit(x_all.iloc[train_idx][loso_columns], y[train_idx])
            y_prob = model.predict_proba(x_all.iloc[test_idx][loso_columns])[:, 1]
            rows.append(
                {
                    "evaluation": "leave_one_site_out",
                    "fold": int(fold_idx),
                    "held_out_site": groups[test_idx][0],
                    "model": model_name,
                    "n_features": int(len(loso_columns)),
                    **compute_metrics(y[test_idx], y_prob),
                }
            )
    return pd.DataFrame(rows)


def merge_summaries(metadata: pd.DataFrame, repeated_scores: pd.DataFrame, loso_scores: pd.DataFrame) -> pd.DataFrame:
    repeated_summary = summarize_scores(repeated_scores).add_prefix("repeated_")
    repeated_summary = repeated_summary.rename(columns={"repeated_model": "model"})
    loso_summary = summarize_scores(loso_scores).add_prefix("loso_")
    loso_summary = loso_summary.rename(columns={"loso_model": "model"})
    summary = metadata.merge(repeated_summary, on="model", how="left").merge(loso_summary, on="model", how="left")

    repeated_ref = summary.set_index("model")["repeated_roc_auc_mean"].to_dict()
    repeated_ap_ref = summary.set_index("model")["repeated_average_precision_mean"].to_dict()
    repeated_brier_ref = summary.set_index("model")["repeated_brier_score_mean"].to_dict()
    loso_ref = summary.set_index("model")["loso_roc_auc_mean"].to_dict()

    summary["repeated_delta_roc_auc_vs_base"] = summary.apply(
        lambda row: float(row["repeated_roc_auc_mean"] - repeated_ref[row["base_model"]])
        if row["base_model"] and row["base_model"] in repeated_ref and pd.notna(row["repeated_roc_auc_mean"])
        else np.nan,
        axis=1,
    )
    summary["repeated_delta_auprc_vs_base"] = summary.apply(
        lambda row: float(row["repeated_average_precision_mean"] - repeated_ap_ref[row["base_model"]])
        if row["base_model"] and row["base_model"] in repeated_ap_ref and pd.notna(row["repeated_average_precision_mean"])
        else np.nan,
        axis=1,
    )
    summary["repeated_delta_brier_vs_base"] = summary.apply(
        lambda row: float(row["repeated_brier_score_mean"] - repeated_brier_ref[row["base_model"]])
        if row["base_model"] and row["base_model"] in repeated_brier_ref and pd.notna(row["repeated_brier_score_mean"])
        else np.nan,
        axis=1,
    )
    summary["loso_delta_roc_auc_vs_base"] = summary.apply(
        lambda row: float(row["loso_roc_auc_mean"] - loso_ref[row["base_model"]])
        if row["base_model"] and row["base_model"] in loso_ref and pd.notna(row["loso_roc_auc_mean"])
        else np.nan,
        axis=1,
    )
    return summary.sort_values(
        ["category", "subset_size", "repeated_roc_auc_mean", "loso_roc_auc_mean"],
        ascending=[True, True, False, False],
    ).reset_index(drop=True)


def build_revised_core_correlation(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [f"jac9d__{metric}" for metric in REVISED_CORE_METRICS]
    corr = frame[columns].corr(method="spearman")
    corr.index = [feature_label(index) for index in corr.index]
    corr.columns = [feature_label(column) for column in corr.columns]
    return corr


def write_correlation_heatmap(corr: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    matrix = corr.to_numpy(dtype=float)
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-1.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(corr.columns)))
    ax.set_xticklabels(list(corr.columns), rotation=45, ha="right")
    ax.set_yticks(np.arange(len(corr.index)))
    ax.set_yticklabels(list(corr.index))
    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            ax.text(col_idx, row_idx, f"{matrix[row_idx, col_idx]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Exploratory Spearman correlation within revised 9D Jacobian core")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="rho")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def top_rows(summary: pd.DataFrame, *, category: str, subset_size: int | None = None, limit: int = 5) -> pd.DataFrame:
    subset = summary[summary["category"] == category].copy()
    if subset_size is not None:
        subset = subset[subset["subset_size"] == subset_size].copy()
    return subset.sort_values(["repeated_roc_auc_mean", "loso_roc_auc_mean"], ascending=[False, False]).head(limit)


def lookup_metric_combo(summary: pd.DataFrame, metrics: tuple[str, ...]) -> pd.Series | None:
    wanted = "+".join(metrics)
    subset = summary[summary["metric_label"] == wanted].copy()
    if subset.empty:
        return None
    return subset.sort_values("repeated_roc_auc_mean", ascending=False).iloc[0]


def format_summary_line(row: pd.Series) -> str:
    repeated_ci_low = row.get("repeated_roc_auc_ci_low", np.nan)
    repeated_ci_high = row.get("repeated_roc_auc_ci_high", np.nan)
    loso_auc = row.get("loso_roc_auc_mean", np.nan)
    delta = row.get("repeated_delta_roc_auc_vs_base", np.nan)
    pieces = [
        f"`{row['metric_label']}`",
        f"repeated-CV AUROC `{row['repeated_roc_auc_mean']:.3f} [{repeated_ci_low:.3f}, {repeated_ci_high:.3f}]`",
        f"AUPRC `{row['repeated_average_precision_mean']:.3f}`",
        f"Brier `{row['repeated_brier_score_mean']:.3f}`",
    ]
    if pd.notna(loso_auc):
        pieces.append(f"LOSO AUROC `{loso_auc:.3f}`")
    if pd.notna(delta):
        pieces.append(f"delta vs base `{delta:+.3f}`")
    return ", ".join(pieces)


def build_summary_markdown(frame: pd.DataFrame, summary: pd.DataFrame) -> str:
    full_jacobian = summary[summary["model"] == "jacobian9d_only"].iloc[0]
    full_combined = summary[summary["model"] == "clinical_plus_eeg_plus_reachability_plus_jacobian9d"].iloc[0]
    appendix_trio = lookup_metric_combo(
        summary[summary["category"] == "mixed_cross_family_only_size_3"].copy(),
        ("rotational_power_mean", "tube_d_eff_median", "persistence_log_eig_var_median"),
    )

    lines = [
        "# Exploratory Jacobian 9D Subset Scan",
        "",
        "> This export is exploratory and post hoc. The same pooled cohort was used for subset search and evaluation, and no nested CV or external validation was added here.",
        "",
        f"- n_subjects: `{int(len(frame))}`",
        f"- CPC1: `{int((frame['label'] == 1).sum())}`",
        f"- CPC5: `{int((frame['label'] == 0).sum())}`",
        f"- full revised `9D` family: repeated-CV AUROC `{full_jacobian['repeated_roc_auc_mean']:.3f}`",
        f"- full `clinical+qEEG+reachability+9D` ladder: repeated-CV AUROC `{full_combined['repeated_roc_auc_mean']:.3f}`, LOSO AUROC `{full_combined['loso_roc_auc_mean']:.3f}`",
        "",
        "## Best revised 9D-only subsets",
        "",
    ]
    for subset_size, title in ((1, "Singletons"), (2, "Pairs"), (3, "Triples")):
        lines.extend([f"### {title}", ""])
        for _, row in top_rows(summary, category="revised_only", subset_size=subset_size, limit=5).iterrows():
            lines.append(f"- {format_summary_line(row)}")
        lines.append("")

    lines.extend(["## Best revised 9D subsets added to `clinical+qEEG`", ""])
    for _, row in top_rows(summary, category="clinical_plus_eeg_plus_revised_subset", limit=5).iterrows():
        lines.append(f"- {format_summary_line(row)}")
    lines.extend(["", "## Best revised 9D subsets added to `clinical+qEEG+reachability`", ""])
    for _, row in top_rows(summary, category="clinical_plus_eeg_plus_reachability_plus_revised_subset", limit=5).iterrows():
        lines.append(f"- {format_summary_line(row)}")

    lines.extend(["", "## Best mixed cross-family pairs", ""])
    for _, row in top_rows(summary, category="mixed_cross_family_only_size_2", limit=5).iterrows():
        lines.append(f"- {format_summary_line(row)}")

    lines.extend(["", "## Best mixed cross-family triples", ""])
    for _, row in top_rows(summary, category="mixed_cross_family_only_size_3", limit=5).iterrows():
        lines.append(f"- {format_summary_line(row)}")

    lines.extend(["", "## Best `clinical+qEEG` plus mixed cross-family subsets", ""])
    for category in ("clinical_plus_eeg_plus_mixed_cross_family_size_2", "clinical_plus_eeg_plus_mixed_cross_family_size_3"):
        for _, row in top_rows(summary, category=category, limit=5).iterrows():
            lines.append(f"- {format_summary_line(row)}")

    if appendix_trio is not None:
        lines.extend(
            [
                "",
                "## Appendix trio check",
                "",
                f"- {format_summary_line(appendix_trio)}",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- Treat the ranked subsets as exploratory search outputs, not frozen article claims.",
            "- The cleanest manuscript-facing use is to support appendix language about complementarity and redundancy, not to replace the current frozen predictive ladder.",
            "- If any subset is promoted beyond appendix status, the next step should be nested CV or a truly held-out evaluation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Building pooled subset-scan cohort...")
    frame = build_model_frame()
    feature_sets, metadata = build_feature_catalog(frame)
    print(f"Prepared {len(feature_sets)} models for exploratory subset scanning.")

    print("Evaluating repeated stratified CV...")
    repeated_scores = evaluate_repeated_cv(frame, feature_sets, n_repeats=args.n_repeats)
    print("Evaluating leave-one-site-out...")
    loso_scores = evaluate_leave_one_site_out(frame, feature_sets)
    summary = merge_summaries(metadata, repeated_scores, loso_scores)

    revised_corr = build_revised_core_correlation(frame)
    write_correlation_heatmap(revised_corr, args.output_dir / "revised_core_correlation_heatmap.png")

    repeated_scores.to_csv(args.output_dir / "subset_scan_repeated_cv_fold_scores.csv", index=False)
    loso_scores.to_csv(args.output_dir / "subset_scan_loso_fold_scores.csv", index=False)
    summary.to_csv(args.output_dir / "subset_scan_model_summary.csv", index=False)
    metadata.to_csv(args.output_dir / "subset_scan_model_manifest.csv", index=False)
    revised_corr.to_csv(args.output_dir / "revised_core_correlation_matrix.csv")

    summary[summary["category"] == "revised_only"].to_csv(args.output_dir / "revised_only_summary.csv", index=False)
    summary[summary["category"] == "clinical_plus_eeg_plus_revised_subset"].to_csv(
        args.output_dir / "clinical_plus_eeg_plus_revised_subset_summary.csv", index=False
    )
    summary[summary["category"] == "clinical_plus_eeg_plus_reachability_plus_revised_subset"].to_csv(
        args.output_dir / "clinical_plus_eeg_plus_reachability_plus_revised_subset_summary.csv", index=False
    )
    summary[summary["category"] == "mixed_cross_family_only_size_2"].to_csv(
        args.output_dir / "mixed_cross_family_pair_summary.csv", index=False
    )
    summary[summary["category"] == "mixed_cross_family_only_size_3"].to_csv(
        args.output_dir / "mixed_cross_family_triple_summary.csv", index=False
    )
    summary[summary["category"] == "clinical_plus_eeg_plus_mixed_cross_family_size_2"].to_csv(
        args.output_dir / "clinical_plus_eeg_plus_mixed_pair_summary.csv", index=False
    )
    summary[summary["category"] == "clinical_plus_eeg_plus_mixed_cross_family_size_3"].to_csv(
        args.output_dir / "clinical_plus_eeg_plus_mixed_triple_summary.csv", index=False
    )

    summary_md = build_summary_markdown(frame, summary)
    (args.output_dir / "subset_scan_summary.md").write_text(summary_md, encoding="utf-8")

    manifest = {
        "output_dir": str(args.output_dir),
        "n_subjects": int(len(frame)),
        "n_cpc1": int((frame["label"] == 1).sum()),
        "n_cpc5": int((frame["label"] == 0).sum()),
        "n_models": int(len(feature_sets)),
        "n_repeats": int(args.n_repeats),
        "n_splits": int(resolve_split_count(frame["label"].astype(int).to_numpy(), N_SPLITS)),
        "revised_core_metrics": list(REVISED_CORE_METRICS),
        "reachability_features": list(REACHABILITY_FEATURES),
    }
    (args.output_dir / "subset_scan_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote exploratory subset-scan outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
