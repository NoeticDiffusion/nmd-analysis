"""
tac_incremental_validity.py — does TAC 10 add AUROC over NDT-5 geometry?

Loads the existing incremental-validity cohort CSV (clinical + qEEG + NDT-5 geometry
features, one row per subject) and merges TAC 10 patient-level metrics from the TAC
results directory.  Runs two additional model tiers:

  clinical+qEEG+NDT5+TAC10   (adds tac10 cross/within band flux)
  TAC10 only

Uses the same 5×20 repeated stratified CV as the main NDT article.

Usage
-----
  python tac_incremental_validity.py \\
      --cohort-csv    J:/repos/.../incremental_validity_cohort.csv \\
      --tac-patient-csv J:/repos/.../patient_level_metrics.csv \\
      --output-dir    J:/repos/.../tac_incremental_validity_20260803_invalidityfix_gated
"""
from __future__ import annotations

import argparse
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

ARTICLE_DIR = Path(__file__).resolve().parents[1]
COMA_NDT_DIR = ARTICLE_DIR.parent / "comatose_ndt"

DEFAULT_COHORT_CSV = (
    COMA_NDT_DIR
    / "results"
    / "incremental_validity_20260606_combined_invalidityfix_primary12h_newgeom"
    / "incremental_validity_cohort.csv"
)
DEFAULT_TAC_PATIENT_CSV = (
    ARTICLE_DIR
    / "results"
    / "tac_sigma_jacobian_20260803_invalidityfix_gated"
    / "patient_level_metrics.csv"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "tac_incremental_validity_20260803_invalidityfix_gated"

# TAC 10 metrics to test (the two significant ones from the full-cohort run)
TAC10_FEATURES = [
    "tac10_9d_cross_band_flux_median",
    "tac10_9d_within_band_flux_median",
]
# All TAC features (for a full-TAC model)
TAC_ALL_FEATURES = [
    "tac6_3d_sigma_velocity_median",
    "tac6_9d_sigma_velocity_median",
    "tac8_3d_cone_twist_median",
    "tac8_9d_cone_twist_median",
    "tac10_9d_cross_band_flux_median",
    "tac10_9d_within_band_flux_median",
    "tac10_9d_cross_band_ratio_median",
]

NDT5_COLS = [
    "geom_tube_d_eff_median",
    "geom_persistence_log_det_median",
    "geom_persistence_log_eig_var_median",
    "geom_persistence_hysteresis_log_det_median",
    "geom_tube_capture_gate_median",
]

N_SPLITS = 5
N_REPEATS = 20
RANDOM_STATE = 20260517


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def make_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    penalty="l2", C=1.0, solver="lbfgs", max_iter=1000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def run_cv(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray | None = None,
) -> dict[str, Any]:
    cv = RepeatedStratifiedKFold(
        n_splits=N_SPLITS, n_repeats=N_REPEATS, random_state=RANDOM_STATE
    )
    fold_aurocs: list[float] = []
    fold_auprc: list[float] = []
    fold_brier: list[float] = []

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        pipe = make_pipeline()
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:, 1]
        fold_aurocs.append(float(roc_auc_score(y_test, proba)))
        fold_auprc.append(float(average_precision_score(y_test, proba)))
        fold_brier.append(float(brier_score_loss(y_test, proba)))

    auroc_arr = np.array(fold_aurocs)
    auprc_arr = np.array(fold_auprc)
    brier_arr = np.array(fold_brier)
    return {
        "n_folds": len(fold_aurocs),
        "roc_auc_mean": float(auroc_arr.mean()),
        "roc_auc_sd": float(auroc_arr.std()),
        "average_precision_mean": float(auprc_arr.mean()),
        "average_precision_sd": float(auprc_arr.std()),
        "brier_score_mean": float(brier_arr.mean()),
        "brier_score_sd": float(brier_arr.std()),
        "fold_aurocs": fold_aurocs,
        "fold_auprc": fold_auprc,
        "fold_brier": fold_brier,
    }


def delta_pvalue(base_folds: list[float], ext_folds: list[float]) -> float:
    diff = np.array(ext_folds) - np.array(base_folds)
    result = stats.ttest_1samp(diff, 0.0)
    return float(result.pvalue)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1].strip())
    parser.add_argument("--cohort-csv", type=Path, default=DEFAULT_COHORT_CSV)
    parser.add_argument("--tac-patient-csv", type=Path, default=DEFAULT_TAC_PATIENT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--n-splits", type=int, default=N_SPLITS)
    parser.add_argument("--n-repeats", type=int, default=N_REPEATS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    print(f"Loading cohort from {args.cohort_csv}...")
    cohort = pd.read_csv(args.cohort_csv, low_memory=False)
    print(f"  {len(cohort)} subjects")

    print(f"Loading TAC patient metrics from {args.tac_patient_csv}...")
    tac = pd.read_csv(args.tac_patient_csv, low_memory=False)
    # Rename TAC columns to avoid clash with existing geom_ prefix
    rename = {col: f"tac_{col}" if not col.startswith("tac") else col for col in TAC_ALL_FEATURES + TAC10_FEATURES}
    # tac columns already have tac prefix, no rename needed
    print(f"  {len(tac)} subjects in TAC file")

    # Merge on subject
    merged = cohort.merge(
        tac[["subject"] + TAC_ALL_FEATURES].drop_duplicates("subject"),
        on="subject",
        how="left",
    )
    print(f"  After merge: {len(merged)} subjects, {merged[TAC10_FEATURES[0]].notna().sum()} have TAC10 values")

    y = merged["label"].to_numpy(dtype=float)

    # Identify clinical + qEEG columns: only the pre-processed prefixed columns
    # (clinical__, cat__, eeg__) — excludes raw string categorical columns like `hospital`
    clinical_eeg_cols = [
        c for c in cohort.columns
        if c.startswith("clinical__") or c.startswith("cat__") or c.startswith("eeg__")
    ]

    # Define model feature sets
    models: dict[str, list[str]] = {
        "clinical_plus_eeg": clinical_eeg_cols,
        "clinical_plus_eeg_plus_NDT5": clinical_eeg_cols + NDT5_COLS,
        "clinical_plus_eeg_plus_NDT5_plus_TAC10": clinical_eeg_cols + NDT5_COLS + TAC10_FEATURES,
        "clinical_plus_eeg_plus_NDT5_plus_TACAll": clinical_eeg_cols + NDT5_COLS + TAC_ALL_FEATURES,
        "TAC10_only": TAC10_FEATURES,
        "NDT5_only": NDT5_COLS,
        "NDT5_plus_TAC10": NDT5_COLS + TAC10_FEATURES,
    }

    results: list[dict[str, Any]] = []
    base_folds: list[float] = []

    for model_name, feat_cols in models.items():
        available = [c for c in feat_cols if c in merged.columns]
        if len(available) < 1:
            print(f"  SKIP {model_name}: no available columns")
            continue

        X = merged[available].to_numpy(dtype=float)
        print(f"Running {model_name} ({len(available)} features, {X.shape[0]} subjects)...")
        cv_result = run_cv(X, y)

        row: dict[str, Any] = {
            "model": model_name,
            "n_features": len(available),
            **{k: v for k, v in cv_result.items() if not isinstance(v, list)},
        }

        if model_name == "clinical_plus_eeg":
            base_folds = cv_result["fold_aurocs"]
            row["delta_roc_auc_mean"] = 0.0
            row["delta_roc_auc_p"] = float("nan")
        elif base_folds:
            delta = np.array(cv_result["fold_aurocs"]) - np.array(base_folds)
            row["delta_roc_auc_mean"] = float(delta.mean())
            row["delta_roc_auc_p"] = delta_pvalue(base_folds, cv_result["fold_aurocs"])
        else:
            row["delta_roc_auc_mean"] = float("nan")
            row["delta_roc_auc_p"] = float("nan")

        results.append(row)
        print(
            f"  -> AUROC {cv_result['roc_auc_mean']:.3f} +/- {cv_result['roc_auc_sd']:.3f}"
            + (f"  delta {row['delta_roc_auc_mean']:+.3f}  p={row['delta_roc_auc_p']:.2e}" if "delta_roc_auc_mean" in row else "")
        )

    summary = pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, list)} for r in results])
    summary.to_csv(args.output_dir / "tac_incremental_validity_summary.csv", index=False)

    # Markdown summary
    lines = [
        "# TAC Incremental Validity over NDT-5",
        "",
        f"- CV: {N_REPEATS}x{N_SPLITS} repeated stratified",
        f"- n_subjects: {len(merged)}",
        "",
        "| Model | n feat | AUROC mean | AUROC sd | Delta AUROC | Delta p |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        delta_str = f"{r.get('delta_roc_auc_mean', float('nan')):+.3f}" if np.isfinite(r.get("delta_roc_auc_mean", float("nan"))) else "—"
        p_str = f"{r.get('delta_roc_auc_p', float('nan')):.2e}" if np.isfinite(r.get("delta_roc_auc_p", float("nan"))) else "—"
        lines.append(
            f"| `{r['model']}` | {r['n_features']} "
            f"| {r['roc_auc_mean']:.3f} | {r['roc_auc_sd']:.3f} "
            f"| {delta_str} | {p_str} |"
        )
    md = "\n".join(lines)
    (args.output_dir / "tac_incremental_validity_summary.md").write_text(md, encoding="utf-8")

    manifest = {
        "cohort_csv": str(args.cohort_csv),
        "tac_patient_csv": str(args.tac_patient_csv),
        "output_dir": str(args.output_dir),
        "n_subjects": len(merged),
        "n_splits": args.n_splits,
        "n_repeats": args.n_repeats,
        "random_state": RANDOM_STATE,
        "models": list(models.keys()),
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nWrote results to {args.output_dir}")


if __name__ == "__main__":
    main()
