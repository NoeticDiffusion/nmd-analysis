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
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold

from incremental_validity_analysis import make_classifier, resolve_split_count


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis_20260524_combined_cpc15_primary12h_9d"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "jacobian_exploratory_20260524_combined_cpc15"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_RANDOM_STATE = 20260524
DEFAULT_N_SPLITS = 5
DEFAULT_N_REPEATS = 20

METRIC_SPECS = [
    ("jacobian_fro_median", "MNJ Frobenius norm"),
    ("jacobian_spectral_radius_median", "MNJ spectral radius"),
]


@dataclass(frozen=True)
class Config:
    timeline_dir: Path
    output_dir: Path
    primary_time_bin: str
    good_cpc: int
    poor_cpc: int
    n_splits: int
    n_repeats: int
    random_state: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Summarize exploratory pooled Jacobian discrimination metrics for the coma cohort."
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=DEFAULT_PRIMARY_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    parser.add_argument("--n-splits", type=int, default=DEFAULT_N_SPLITS)
    parser.add_argument("--n-repeats", type=int, default=DEFAULT_N_REPEATS)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    args = parser.parse_args()
    return Config(
        timeline_dir=args.timeline_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        n_splits=args.n_splits,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
    )


def load_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.timeline_dir / "patient_timebin_summaries.csv")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(config.good_cpc), 1, 0)
    frame["hospital"] = frame["hospital"].fillna("missing").astype(str)
    return frame.reset_index(drop=True)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (good.size + poor.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def bootstrap_auc_ci(y_true: np.ndarray, score: np.ndarray, *, seed: int, n_boot: int = 2000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y_true))
    samples: List[float] = []
    while len(samples) < n_boot:
        sample_idx = rng.choice(idx, size=len(idx), replace=True)
        y_sample = y_true[sample_idx]
        if len(np.unique(y_sample)) < 2:
            continue
        samples.append(float(roc_auc_score(y_sample, score[sample_idx])))
    low, high = np.quantile(np.asarray(samples, dtype=float), [0.025, 0.975])
    return float(low), float(high)


def evaluate_repeated_cv(x: np.ndarray, y: np.ndarray, config: Config) -> Dict[str, float]:
    n_splits = resolve_split_count(y, config.n_splits)
    cv = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=config.n_repeats,
        random_state=config.random_state,
    )
    aucs: List[float] = []
    aps: List[float] = []
    briers: List[float] = []
    for train_idx, test_idx in cv.split(x, y):
        model = make_classifier(config.random_state)
        model.fit(x[train_idx], y[train_idx])
        prob = model.predict_proba(x[test_idx])[:, 1]
        aucs.append(float(roc_auc_score(y[test_idx], prob)))
        aps.append(float(average_precision_score(y[test_idx], prob)))
        briers.append(float(brier_score_loss(y[test_idx], prob)))
    return {
        "repeated_cv_roc_auc_mean": float(np.mean(aucs)),
        "repeated_cv_roc_auc_sd": float(np.std(aucs, ddof=1)) if len(aucs) > 1 else 0.0,
        "repeated_cv_auprc_mean": float(np.mean(aps)),
        "repeated_cv_brier_mean": float(np.mean(briers)),
    }


def evaluate_loso(x: np.ndarray, y: np.ndarray, groups: np.ndarray, config: Config) -> Dict[str, float]:
    logo = LeaveOneGroupOut()
    aucs: List[float] = []
    aps: List[float] = []
    briers: List[float] = []
    rows_used = 0
    for train_idx, test_idx in logo.split(x, y, groups):
        if len(np.unique(y[train_idx])) < 2 or len(np.unique(y[test_idx])) < 2:
            continue
        model = make_classifier(config.random_state)
        model.fit(x[train_idx], y[train_idx])
        prob = model.predict_proba(x[test_idx])[:, 1]
        aucs.append(float(roc_auc_score(y[test_idx], prob)))
        aps.append(float(average_precision_score(y[test_idx], prob)))
        briers.append(float(brier_score_loss(y[test_idx], prob)))
        rows_used += 1
    return {
        "loso_n_folds": int(rows_used),
        "loso_roc_auc_mean": float(np.mean(aucs)) if aucs else float("nan"),
        "loso_auprc_mean": float(np.mean(aps)) if aps else float("nan"),
        "loso_brier_mean": float(np.mean(briers)) if briers else float("nan"),
    }


def summarize_metric(frame: pd.DataFrame, metric: str, label: str, config: Config, metric_idx: int) -> Dict[str, Any]:
    if metric not in frame.columns:
        return {
            "metric": metric,
            "label": label,
            "status": "missing_column",
        }
    values = pd.to_numeric(frame[metric], errors="coerce")
    mask = np.isfinite(values.to_numpy(dtype=float))
    sub = frame.loc[mask].copy()
    x = values.loc[mask].to_numpy(dtype=float)
    y = sub["label"].astype(int).to_numpy()
    groups = sub["hospital"].astype(str).to_numpy()

    good = x[y == 1]
    poor = x[y == 0]
    if x.size == 0 or good.size == 0 or poor.size == 0 or len(np.unique(y)) < 2:
        return {
            "metric": metric,
            "label": label,
            "status": "insufficient_groups",
            "n_cpc1": int(good.size),
            "n_cpc5": int(poor.size),
            "cpc1_median": float(np.median(good)) if good.size else float("nan"),
            "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
            "cohens_d": cohens_d(good, poor),
            "mannwhitney_p": float("nan"),
            "direct_auc": float("nan"),
            "direct_auc_ci_low": float("nan"),
            "direct_auc_ci_high": float("nan"),
            "repeated_cv_roc_auc_mean": float("nan"),
            "repeated_cv_roc_auc_sd": float("nan"),
            "repeated_cv_auprc_mean": float("nan"),
            "repeated_cv_brier_mean": float("nan"),
            "loso_n_folds": 0,
            "loso_roc_auc_mean": float("nan"),
            "loso_auprc_mean": float("nan"),
            "loso_brier_mean": float("nan"),
        }
    direct_score = -x if np.median(good) < np.median(poor) else x
    direct_auc = float(roc_auc_score(y, direct_score))
    auc_ci_low, auc_ci_high = bootstrap_auc_ci(y, direct_score, seed=config.random_state + metric_idx)
    mannwhitney = stats.mannwhitneyu(good, poor, alternative="two-sided")

    row: Dict[str, Any] = {
        "metric": metric,
        "label": label,
        "n_cpc1": int(good.size),
        "n_cpc5": int(poor.size),
        "cpc1_median": float(np.median(good)),
        "cpc5_median": float(np.median(poor)),
        "cohens_d": cohens_d(good, poor),
        "mannwhitney_p": float(mannwhitney.pvalue),
        "direct_auc": direct_auc,
        "direct_auc_ci_low": auc_ci_low,
        "direct_auc_ci_high": auc_ci_high,
        "status": "ok",
    }
    row.update(evaluate_repeated_cv(x.reshape(-1, 1), y, config))
    row.update(evaluate_loso(x.reshape(-1, 1), y, groups, config))
    return row


def write_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Exploratory Jacobian Summary",
        "",
        "| Metric | d | Direct AUROC | Repeated-CV AUROC | Repeated-CV AUPRC | Repeated-CV Brier | LOSO AUROC |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    ok = summary[summary.get("status", "ok") == "ok"].copy()
    for _, row in ok.iterrows():
        lines.append(
            f"| {row['label']} | {row['cohens_d']:+.3f} | "
            f"{row['direct_auc']:.3f} [{row['direct_auc_ci_low']:.3f}, {row['direct_auc_ci_high']:.3f}] | "
            f"{row['repeated_cv_roc_auc_mean']:.3f} | "
            f"{row['repeated_cv_auprc_mean']:.3f} | "
            f"{row['repeated_cv_brier_mean']:.3f} | "
            f"{row['loso_roc_auc_mean']:.3f} |"
        )
    unavailable = summary[summary.get("status", "ok") != "ok"].copy()
    if not unavailable.empty:
        lines.extend(["", "## Unavailable metrics", ""])
        for _, row in unavailable.iterrows():
            lines.append(f"- `{row['label']}` (`{row['metric']}`): `{row['status']}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    frame = load_frame(config)
    rows = [summarize_metric(frame, metric, label, config, idx) for idx, (metric, label) in enumerate(METRIC_SPECS)]
    summary = pd.DataFrame(rows)

    summary.to_csv(config.output_dir / "jacobian_exploratory_summary.csv", index=False)
    (config.output_dir / "jacobian_exploratory_summary.md").write_text(write_markdown(summary), encoding="utf-8")
    (config.output_dir / "jacobian_exploratory_manifest.json").write_text(
        json.dumps(
            {
                "timeline_dir": str(config.timeline_dir),
                "primary_time_bin": config.primary_time_bin,
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "n_splits": config.n_splits,
                "n_repeats": config.n_repeats,
                "metrics": METRIC_SPECS,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote Jacobian exploratory summary to {config.output_dir}")


if __name__ == "__main__":
    main()
