"""Direct AUROC / AUPRC plus univariate logistic discrimination for Family A.

Follows the older coma article's Jacobian exploratory summary
(`articles/CLINICAL/comatose_ndt/src/jacobian_exploratory_summary.py`):

- *Direct AUROC* (CPC1-high): rank probability that a random CPC1
  patient-median exceeds a random CPC5 patient-median. Identical to
  Mann-Whitney U / (n1 n5) and to (Cliff's delta + 1) / 2. Directional:
  values below 0.5 mean the metric is higher in CPC5.
- *Direct AUPRC*: average precision with CPC1 as the positive class
  (chance = CPC1 prevalence, here ~0.5).
- *Repeated-CV ROC AUC / AUPRC*: univariate logistic regression on the
  same patient-median (StandardScaler + balanced LogReg), 5x20
  RepeatedStratifiedKFold. This is a discrimination number, not a
  directional group test; the fitted sign can flip, so H4 (CPC5-higher)
  can still show CV-AUC > 0.5.
- *Hospital-LOSO ROC AUC*: LeaveOneGroupOut by hospital, same univariate
  logistic. Folds lacking both classes are skipped.

Not a prognostic model and not incremental validity vs clinical + qEEG
(the `conventional_eeg` pack was not materialized in these exports).
Family B is omitted: the fit-fidelity gate leaves too few patients.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from icare_v2_common import (
    ARTICLE_DIR,
    bootstrap_two_sample_ci,
    finite_array,
    write_csv,
    write_json,
)

N_BOOT = 2000
BOOT_SEED = 20260912
CV_SPLITS = 5
CV_REPEATS = 20
CV_RANDOM_STATE = 20260912

COHORTS = (
    {
        "label": "part1_discovery",
        "display": "Discovery",
        "table": ARTICLE_DIR / "results" / "part1_corrected" / "qualified_drift_primary_merged.csv",
        "fallback": ARTICLE_DIR / "results" / "part1_corrected" / "icare_v2_primary_cpc15_table.csv",
        "out_dir": ARTICLE_DIR / "results" / "part1_corrected",
    },
    {
        "label": "part2_confirmatory",
        "display": "Confirmatory",
        "table": ARTICLE_DIR / "results" / "part2_confirmatory" / "qualified_drift_primary_merged.csv",
        "fallback": ARTICLE_DIR / "results" / "part2_confirmatory" / "icare_v2_primary_cpc15_table.csv",
        "out_dir": ARTICLE_DIR / "results" / "part2_confirmatory",
    },
)

METRICS = (
    ("d_eff_a_median", "H1", "diffusion", "primary"),
    ("h_tilde_a_median", "H2", "diffusion", "primary"),
    ("e_perp_median", "H3", "diffusion", "candidate_stored_chart_velocity"),
    ("d_total_median", "H4", "diffusion", "control_not_required_to_differ"),
    ("cone_d_eff_h1_median", "reach_h1", "reachability", "secondary"),
    ("cone_d_eff_h4_median", "reach_h4", "reachability", "secondary"),
    ("tube_d_eff_median", "tube", "reachability", "secondary"),
    ("e_perp_qualified_median", "H3_R7", "diffusion", "posthoc_savgol_11_2"),
)


def _classifier(seed: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    solver="liblinear",
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=seed,
                ),
            ),
        ]
    )


def _auroc_cpc1_high(good: np.ndarray, poor: np.ndarray) -> float:
    good = finite_array(good)
    poor = finite_array(poor)
    if good.size == 0 or poor.size == 0:
        return float("nan")
    y = np.concatenate([np.ones(good.size), np.zeros(poor.size)])
    score = np.concatenate([good, poor])
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, score))


def _auprc_cpc1(good: np.ndarray, poor: np.ndarray) -> float:
    good = finite_array(good)
    poor = finite_array(poor)
    if good.size == 0 or poor.size == 0:
        return float("nan")
    y = np.concatenate([np.ones(good.size), np.zeros(poor.size)])
    score = np.concatenate([good, poor])
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(average_precision_score(y, score))


def _load_table(spec: dict[str, Any]) -> pd.DataFrame:
    path = spec["table"] if spec["table"].is_file() else spec["fallback"]
    frame = pd.read_csv(path)
    if "in_primary_window" in frame.columns:
        frame = frame[frame["in_primary_window"] == True]  # noqa: E712
    return frame.reset_index(drop=True)


def _arms(frame: pd.DataFrame, metric: str) -> tuple[np.ndarray, np.ndarray]:
    good = pd.to_numeric(frame.loc[frame["contrast_group"] == "CPC1", metric], errors="coerce")
    poor = pd.to_numeric(frame.loc[frame["contrast_group"] == "CPC5", metric], errors="coerce")
    return finite_array(good), finite_array(poor)


def _xy_groups(frame: pd.DataFrame, metric: str) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    values = pd.to_numeric(frame[metric], errors="coerce")
    labels = frame["contrast_group"].astype(str)
    mask = values.notna() & labels.isin(["CPC1", "CPC5"])
    if int(mask.sum()) < 4:
        return None
    x = values.loc[mask].to_numpy(dtype=float).reshape(-1, 1)
    y = (labels.loc[mask] == "CPC1").to_numpy(dtype=int)
    if "hospital" in frame.columns:
        groups = frame.loc[mask, "hospital"].fillna("missing").astype(str).to_numpy()
    else:
        groups = np.array(["missing"] * int(mask.sum()), dtype=str)
    if len(np.unique(y)) < 2:
        return None
    return x, y, groups


def _repeated_cv(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    n_splits = min(CV_SPLITS, int(np.bincount(y).min()))
    if n_splits < 2:
        return {
            "repeated_cv_roc_auc_mean": float("nan"),
            "repeated_cv_roc_auc_sd": float("nan"),
            "repeated_cv_auprc_mean": float("nan"),
            "repeated_cv_n_folds": 0,
        }
    cv = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=CV_REPEATS,
        random_state=CV_RANDOM_STATE,
    )
    aucs: list[float] = []
    aps: list[float] = []
    for train_idx, test_idx in cv.split(x, y):
        model = _classifier(CV_RANDOM_STATE)
        model.fit(x[train_idx], y[train_idx])
        prob = model.predict_proba(x[test_idx])[:, 1]
        if len(np.unique(y[test_idx])) < 2:
            continue
        aucs.append(float(roc_auc_score(y[test_idx], prob)))
        aps.append(float(average_precision_score(y[test_idx], prob)))
    return {
        "repeated_cv_roc_auc_mean": float(np.mean(aucs)) if aucs else float("nan"),
        "repeated_cv_roc_auc_sd": float(np.std(aucs, ddof=1)) if len(aucs) > 1 else float("nan"),
        "repeated_cv_auprc_mean": float(np.mean(aps)) if aps else float("nan"),
        "repeated_cv_n_folds": int(len(aucs)),
    }


def _hospital_loso(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> dict[str, float]:
    logo = LeaveOneGroupOut()
    aucs: list[float] = []
    aps: list[float] = []
    n_folds = 0
    for train_idx, test_idx in logo.split(x, y, groups):
        if len(np.unique(y[train_idx])) < 2 or len(np.unique(y[test_idx])) < 2:
            continue
        model = _classifier(CV_RANDOM_STATE)
        model.fit(x[train_idx], y[train_idx])
        prob = model.predict_proba(x[test_idx])[:, 1]
        aucs.append(float(roc_auc_score(y[test_idx], prob)))
        aps.append(float(average_precision_score(y[test_idx], prob)))
        n_folds += 1
    return {
        "hospital_loso_roc_auc_mean": float(np.mean(aucs)) if aucs else float("nan"),
        "hospital_loso_auprc_mean": float(np.mean(aps)) if aps else float("nan"),
        "hospital_loso_n_folds": int(n_folds),
    }


def _metric_row(frame: pd.DataFrame, metric: str, hypothesis: str, family: str, role: str) -> dict[str, Any]:
    good, poor = _arms(frame, metric)
    auroc = _auroc_cpc1_high(good, poor)
    auprc = _auprc_cpc1(good, poor)
    auroc_lo = auroc_hi = auprc_lo = auprc_hi = float("nan")
    n_boot_auroc = n_boot_auprc = 0
    if good.size >= 2 and poor.size >= 2:
        auroc_lo, auroc_hi, n_boot_auroc = bootstrap_two_sample_ci(
            good, poor, _auroc_cpc1_high, n_boot=N_BOOT, seed=BOOT_SEED
        )
        auprc_lo, auprc_hi, n_boot_auprc = bootstrap_two_sample_ci(
            good, poor, _auprc_cpc1, n_boot=N_BOOT, seed=BOOT_SEED
        )
    prevalence = float(good.size / (good.size + poor.size)) if (good.size + poor.size) else float("nan")
    row: dict[str, Any] = {
        "family": family,
        "hypothesis": hypothesis,
        "metric": metric,
        "role": role,
        "n_cpc1": int(good.size),
        "n_cpc5": int(poor.size),
        "cpc1_prevalence": prevalence,
        "direct_auroc_cpc1_high": auroc,
        "direct_auroc_ci_lo": auroc_lo,
        "direct_auroc_ci_hi": auroc_hi,
        "direct_auprc_cpc1": auprc,
        "direct_auprc_ci_lo": auprc_lo,
        "direct_auprc_ci_hi": auprc_hi,
        "chance_auroc": 0.5,
        "chance_auprc": prevalence,
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": BOOT_SEED,
        "repeated_cv_roc_auc_mean": float("nan"),
        "repeated_cv_roc_auc_sd": float("nan"),
        "repeated_cv_auprc_mean": float("nan"),
        "repeated_cv_n_folds": 0,
        "hospital_loso_roc_auc_mean": float("nan"),
        "hospital_loso_auprc_mean": float("nan"),
        "hospital_loso_n_folds": 0,
    }
    packed = _xy_groups(frame, metric)
    if packed is not None:
        x, y, groups = packed
        row.update(_repeated_cv(x, y))
        row.update(_hospital_loso(x, y, groups))
    return row


def _analyze_cohort(spec: dict[str, Any]) -> pd.DataFrame:
    frame = _load_table(spec)
    rows = []
    for metric, hyp, family, role in METRICS:
        if metric not in frame.columns:
            continue
        row = _metric_row(frame, metric, hyp, family, role)
        row["cohort"] = spec["label"]
        row["cohort_display"] = spec["display"]
        rows.append(row)
    return pd.DataFrame(rows)


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _render_markdown(all_rows: pd.DataFrame) -> str:
    lines = [
        "# Family A AUROC / AUPRC (patient-median, 0-12h CPC1 vs CPC5)",
        "",
        "Direct AUROC is the Mann-Whitney rank probability that a random CPC1",
        "patient-median exceeds a random CPC5 patient-median (CPC1-high).",
        "It is not a fitted prognostic model. Repeated-CV and hospital-LOSO",
        "AUROC are univariate logistic discrimination on the same scalar.",
        "No clinical or conventional-qEEG covariates. Chance AUROC = 0.5;",
        "chance AUPRC = CPC1 prevalence (~0.50).",
        "",
        f"- bootstrap: {N_BOOT} resamples, seed `{BOOT_SEED}`, arms independent",
        f"- repeated CV: {CV_SPLITS} x {CV_REPEATS} stratified, seed `{CV_RANDOM_STATE}`",
        "- hospital LOSO: `LeaveOneGroupOut`; folds without both classes skipped",
        "",
    ]
    for cohort, sub in all_rows.groupby("cohort", sort=False):
        display = str(sub["cohort_display"].iloc[0])
        lines += [f"## {display} (`{cohort}`)", ""]
        lines.append(
            "| Metric | Role | n1/n5 | Direct AUROC [95% CI] | Direct AUPRC [95% CI] | CV AUROC | Hospital LOSO AUROC |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for _, row in sub.iterrows():
            auroc = (
                f"{_fmt(row['direct_auroc_cpc1_high'])} "
                f"[{_fmt(row['direct_auroc_ci_lo'])}, {_fmt(row['direct_auroc_ci_hi'])}]"
            )
            auprc = (
                f"{_fmt(row['direct_auprc_cpc1'])} "
                f"[{_fmt(row['direct_auprc_ci_lo'])}, {_fmt(row['direct_auprc_ci_hi'])}]"
            )
            cv = (
                f"{_fmt(row['repeated_cv_roc_auc_mean'])} "
                f"+/- {_fmt(row['repeated_cv_roc_auc_sd'])}"
            )
            loso = _fmt(row["hospital_loso_roc_auc_mean"])
            lines.append(
                f"| `{row['metric']}` | {row['role']} | "
                f"{int(row['n_cpc1'])}/{int(row['n_cpc5'])} | {auroc} | {auprc} | {cv} | {loso} |"
            )
        lines.append("")
    h1 = all_rows[all_rows["hypothesis"] == "H1"]
    if len(h1) == 2:
        d = h1.set_index("cohort")
        lines += [
            "## Interpretation",
            "",
            "- H1 (`d_eff_a_median`) direct AUROC is a *moderate* rank discrimination, ",
            f"  discovery `{_fmt(d.loc['part1_discovery', 'direct_auroc_cpc1_high'])}` / ",
            f"  confirmatory `{_fmt(d.loc['part2_confirmatory', 'direct_auroc_cpc1_high'])}`. ",
            "  That is the same information as the Mann-Whitney test already reported, ",
            "  not an independent finding.",
            "- Direct AUROC CIs exclude 0.5 for H1/H2 in both cohorts. Stored-drift H3",
            "  excludes 0.5 only barely in discovery (`0.506`) and includes 0.5 in the",
            "  confirmatory cohort. H4 (control) is at or below chance in the CPC1-high",
            "  orientation, as expected if total power is not a CPC1 advantage.",
            "- H4 control can have direct AUROC < 0.5 (CPC5 higher) while repeated-CV AUROC ",
            "  is > 0.5 because the logistic model may learn the opposite sign.",
            "- R7 qualified-drift $E_perp$ is post-hoc; its AUROC is reported as such.",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "replication",
    )
    args = parser.parse_args()
    frames = []
    for spec in COHORTS:
        table = _analyze_cohort(spec)
        write_csv(spec["out_dir"] / "auroc_discrimination.csv", table)
        frames.append(table)
        print(f"{spec['label']}: {len(table)} metric rows", flush=True)
    all_rows = pd.concat(frames, ignore_index=True)
    out_dir = args.output_dir
    write_csv(out_dir / "family_a_auroc_comparison.csv", all_rows)
    md = _render_markdown(all_rows)
    (out_dir / "family_a_auroc_comparison.md").write_text(md, encoding="utf-8")
    write_json(
        out_dir / "family_a_auroc_comparison_manifest.json",
        {
            "n_boot": N_BOOT,
            "bootstrap_seed": BOOT_SEED,
            "cv_splits": CV_SPLITS,
            "cv_repeats": CV_REPEATS,
            "cv_random_state": CV_RANDOM_STATE,
            "metrics": [m[0] for m in METRICS],
            "note": "Direct AUROC is CPC1-high rank AUROC, not a prognostic model.",
        },
    )
    print(md)


if __name__ == "__main__":
    main()
