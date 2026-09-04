from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.metrics import roc_auc_score


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
JAC9D_SRC_DIR = ARTICLE_DIR.parent / "comatose_ndt_jacobian_9d" / "src"
if str(JAC9D_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(JAC9D_SRC_DIR))

from jacobian_9d_support import assemble_part_cohort, assemble_pooled_cohort  # noqa: E402


DEFAULT_WAVE1_SUBJECT_METRICS = (
    ARTICLE_DIR / "results" / "wave1_geometry_pilots_20260526_part1_cpc15" / "subject_wave1_metrics.csv"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "wave1_residual_tests_20260526_part1_cpc15"

DEFAULT_WAVE1_METRICS: tuple[str, ...] = (
    "mnj_reactivity_median",
    "mnj_non_normality_median",
    "mnj_henrici_departure_median",
    "mnj_reactivity_gap_median",
    "largest_lyapunov_per_hour",
    "lyapunov_positive_sum_per_hour",
)
DEFAULT_CONTROL_METRICS: tuple[str, ...] = (
    "spectral_radius_median",
    "anisotropy_abs_eig_median",
    "frobenius_norm_median",
    "rotational_power_mean",
    "mdr_median",
)


@dataclass(frozen=True)
class Config:
    wave1_subject_metrics_path: Path
    output_dir: Path
    cohort_part: str
    wave1_metrics: tuple[str, ...]
    control_metrics: tuple[str, ...]
    lower_winsor_q: float
    upper_winsor_q: float


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Residual-test wave1 geometry metrics against the established revised 9D Jacobian panel "
            "and export contrast/correlation summaries."
        )
    )
    parser.add_argument("--wave1-subject-metrics", type=Path, default=DEFAULT_WAVE1_SUBJECT_METRICS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cohort-part", choices=("part1", "part2", "pooled"), default="part1")
    parser.add_argument("--lower-winsor-q", type=float, default=0.01)
    parser.add_argument("--upper-winsor-q", type=float, default=0.99)
    args = parser.parse_args()
    return Config(
        wave1_subject_metrics_path=args.wave1_subject_metrics,
        output_dir=args.output_dir,
        cohort_part=str(args.cohort_part),
        wave1_metrics=DEFAULT_WAVE1_METRICS,
        control_metrics=DEFAULT_CONTROL_METRICS,
        lower_winsor_q=float(args.lower_winsor_q),
        upper_winsor_q=float(args.upper_winsor_q),
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if len(good) < 2 or len(poor) < 2:
        return float("nan")
    pooled = ((len(good) - 1) * np.var(good, ddof=1) + (len(poor) - 1) * np.var(poor, ddof=1)) / (
        len(good) + len(poor) - 2
    )
    if pooled <= 0 or not np.isfinite(pooled):
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if len(good) == 0 or len(poor) == 0:
        return float("nan")
    comparisons = np.subtract.outer(good, poor)
    return float((np.sum(comparisons > 0) - np.sum(comparisons < 0)) / comparisons.size)


def winsorize_series(series: pd.Series, *, lower_q: float, upper_q: float) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    finite = numeric.dropna()
    if finite.empty:
        return numeric
    low, high = np.quantile(finite, [lower_q, upper_q])
    return numeric.clip(lower=low, upper=high)


def load_existing_9d_cohort(part: str) -> pd.DataFrame:
    if part == "part1":
        frame = assemble_part_cohort(part="part1", include_reachability=False)
    elif part == "part2":
        frame = assemble_part_cohort(part="part2", include_reachability=False)
    elif part == "pooled":
        frame = assemble_pooled_cohort(include_reachability=False)
    else:
        raise ValueError(f"Unsupported cohort part: {part}")
    return frame.copy()


def build_merged_frame(config: Config) -> pd.DataFrame:
    wave1 = pd.read_csv(config.wave1_subject_metrics_path)
    existing = load_existing_9d_cohort(config.cohort_part)
    keep_columns = ["subject", "label", "label_name", *config.control_metrics]
    existing = existing[keep_columns].copy()
    for metric in config.control_metrics:
        existing[metric] = pd.to_numeric(existing[metric], errors="coerce")
    merged = wave1.merge(existing, on=["subject", "label", "label_name"], how="inner", validate="one_to_one")
    for metric in config.wave1_metrics:
        merged[metric] = pd.to_numeric(merged[metric], errors="coerce")
        merged[f"{metric}__winsor"] = winsorize_series(
            merged[metric],
            lower_q=config.lower_winsor_q,
            upper_q=config.upper_winsor_q,
        )
    for metric in config.control_metrics:
        merged[f"{metric}__winsor"] = winsorize_series(
            merged[metric],
            lower_q=config.lower_winsor_q,
            upper_q=config.upper_winsor_q,
        )
    return merged


def build_correlation_rows(frame: pd.DataFrame, *, wave1_metrics: tuple[str, ...], control_metrics: tuple[str, ...]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for wave_metric in wave1_metrics:
        for control_metric in control_metrics:
            subset = frame[[f"{wave_metric}__winsor", f"{control_metric}__winsor"]].dropna()
            if len(subset) < 3:
                continue
            pearson = float(np.corrcoef(subset.iloc[:, 0], subset.iloc[:, 1])[0, 1])
            spearman = float(spearmanr(subset.iloc[:, 0], subset.iloc[:, 1]).statistic)
            rows.append(
                {
                    "wave1_metric": wave_metric,
                    "control_metric": control_metric,
                    "n_subjects": int(len(subset)),
                    "pearson_r": pearson,
                    "spearman_rho": spearman,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_spearman_rho"] = out["spearman_rho"].abs()
    return out.sort_values(["wave1_metric", "abs_spearman_rho"], ascending=[True, False]).reset_index(drop=True)


def residualize_joint(
    target: pd.Series,
    controls: pd.DataFrame,
) -> tuple[pd.Series, dict[str, float]]:
    y = pd.to_numeric(target, errors="coerce")
    x = controls.apply(pd.to_numeric, errors="coerce")
    complete = y.notna() & x.notna().all(axis=1)
    residual = pd.Series(np.nan, index=target.index, dtype=float)
    if int(complete.sum()) < max(10, x.shape[1] + 3):
        return residual, {"n_subjects": int(complete.sum()), "r_squared": float("nan")}

    y_fit = y.loc[complete].to_numpy(dtype=float)
    x_fit = x.loc[complete].to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(x_fit), dtype=float), x_fit])
    beta, *_ = np.linalg.lstsq(design, y_fit, rcond=None)
    fitted = design @ beta
    residual_values = y_fit - fitted
    residual.loc[complete] = residual_values

    ss_res = float(np.sum((y_fit - fitted) ** 2))
    ss_tot = float(np.sum((y_fit - np.mean(y_fit)) ** 2))
    r_squared = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    metadata = {"n_subjects": int(complete.sum()), "r_squared": r_squared}
    for idx, column in enumerate(x.columns, start=1):
        metadata[f"beta_{column}"] = float(beta[idx])
    metadata["beta_intercept"] = float(beta[0])
    return residual, metadata


def build_residual_contrasts(frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    contrast_rows: list[dict[str, Any]] = []
    residual_columns: dict[str, pd.Series] = {}

    control_columns = [f"{metric}__winsor" for metric in config.control_metrics]
    control_frame = frame[control_columns].copy()

    for wave_metric in config.wave1_metrics:
        residual, metadata = residualize_joint(frame[f"{wave_metric}__winsor"], control_frame)
        residual_name = f"{wave_metric}__resid_joint"
        residual_columns[residual_name] = residual

        subset = pd.DataFrame({"residual": residual, "label": frame["label"]}).dropna()
        good = subset.loc[subset["label"] == 1, "residual"].to_numpy(dtype=float)
        poor = subset.loc[subset["label"] == 0, "residual"].to_numpy(dtype=float)
        if len(good) == 0 or len(poor) == 0:
            continue
        try:
            mw_p = float(mannwhitneyu(good, poor, alternative="two-sided").pvalue)
        except ValueError:
            mw_p = float("nan")
        try:
            direct_auroc = float(roc_auc_score(subset["label"].astype(int), subset["residual"].astype(float)))
        except ValueError:
            direct_auroc = float("nan")

        raw_subset = pd.DataFrame({"value": frame[wave_metric], "label": frame["label"]}).dropna()
        raw_auc = (
            float(roc_auc_score(raw_subset["label"].astype(int), raw_subset["value"].astype(float)))
            if not raw_subset.empty
            else float("nan")
        )
        raw_best = float(max(raw_auc, 1.0 - raw_auc)) if np.isfinite(raw_auc) else float("nan")
        resid_best = float(max(direct_auroc, 1.0 - direct_auroc)) if np.isfinite(direct_auroc) else float("nan")

        contrast_rows.append(
            {
                "wave1_metric": wave_metric,
                "residual_metric": residual_name,
                "cpc1_residual_median": float(np.median(good)),
                "cpc5_residual_median": float(np.median(poor)),
                "cohens_d_residual": cohens_d(good, poor),
                "cliffs_delta_residual": cliffs_delta(good, poor),
                "mann_whitney_p_residual": mw_p,
                "direct_auroc_residual": direct_auroc,
                "best_direction_auroc_residual": resid_best,
                "raw_best_direction_auroc": raw_best,
                "delta_best_direction_auroc": float(resid_best - raw_best) if np.isfinite(raw_best) and np.isfinite(resid_best) else np.nan,
                **metadata,
            }
        )

    contrast_frame = pd.DataFrame(contrast_rows)
    if not contrast_frame.empty:
        contrast_frame = contrast_frame.sort_values(
            ["best_direction_auroc_residual", "cohens_d_residual"],
            ascending=[False, False],
        ).reset_index(drop=True)
    residual_frame = pd.DataFrame({"subject": frame["subject"], "label": frame["label"], "label_name": frame["label_name"], **residual_columns})
    return contrast_frame, residual_frame


def build_summary_markdown(
    merged: pd.DataFrame,
    correlations: pd.DataFrame,
    residual_contrasts: pd.DataFrame,
    config: Config,
) -> str:
    n_subjects = int(merged["subject"].nunique())
    n_good = int((merged["label"] == 1).sum())
    n_poor = int((merged["label"] == 0).sum())
    top_residual = residual_contrasts.head(6)
    lines = [
        "# Wave1 Residual Tests",
        "",
        f"- cohort part: `{config.cohort_part}`",
        f"- wave1 subject metrics: `{config.wave1_subject_metrics_path}`",
        f"- subjects in merged residual frame: `{n_subjects}` (`CPC1` = `{n_good}`, `CPC5` = `{n_poor}`)",
        f"- wave1 metrics tested: `{', '.join(config.wave1_metrics)}`",
        f"- controls: `{', '.join(config.control_metrics)}`",
        "",
        "## Best Joint Residual Metrics",
        "",
        "| Metric | Residual AUROC | Raw AUROC | Delta | R^2 |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in top_residual.iterrows():
        lines.append(
            "| {metric} | {resid:.3f} | {raw:.3f} | {delta:+.3f} | {r2:.3f} |".format(
                metric=row["wave1_metric"],
                resid=float(row["best_direction_auroc_residual"]),
                raw=float(row["raw_best_direction_auroc"]),
                delta=float(row["delta_best_direction_auroc"]),
                r2=float(row["r_squared"]),
            )
        )
    lines.extend(
        [
            "",
            "## Strongest Spearman Correlations",
            "",
        ]
    )
    for wave_metric in config.wave1_metrics:
        subset = correlations[correlations["wave1_metric"] == wave_metric].head(2)
        if subset.empty:
            continue
        lines.append(f"- `{wave_metric}`:")
        for _, row in subset.iterrows():
            lines.append(
                "  - vs `{control}`: rho `{rho:.3f}` (n=`{n}`)".format(
                    control=row["control_metric"],
                    rho=float(row["spearman_rho"]),
                    n=int(row["n_subjects"]),
                )
            )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Residuals are computed by joint linear regression against the established revised 9D control panel with an intercept.",
            "- Both wave1 targets and controls are winsorized before regression, using the configured quantile bounds.",
            "- This is a stricter test of incremental structure than the raw wave1 contrasts alone.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    merged = build_merged_frame(config)
    correlations = build_correlation_rows(
        merged,
        wave1_metrics=config.wave1_metrics,
        control_metrics=config.control_metrics,
    )
    residual_contrasts, residual_values = build_residual_contrasts(merged, config)

    merged.to_csv(config.output_dir / "wave1_existing_9d_merged.csv", index=False)
    correlations.to_csv(config.output_dir / "wave1_control_correlations.csv", index=False)
    residual_contrasts.to_csv(config.output_dir / "wave1_joint_residual_contrasts.csv", index=False)
    residual_values.to_csv(config.output_dir / "wave1_joint_residual_values.csv", index=False)
    (config.output_dir / "wave1_residual_summary.md").write_text(
        build_summary_markdown(merged, correlations, residual_contrasts, config),
        encoding="utf-8",
    )

    manifest = {
        "cohort_part": config.cohort_part,
        "wave1_subject_metrics_path": str(config.wave1_subject_metrics_path),
        "output_dir": str(config.output_dir),
        "n_subjects_merged": int(merged["subject"].nunique()),
        "n_rows_merged": int(len(merged)),
        "wave1_metrics": list(config.wave1_metrics),
        "control_metrics": list(config.control_metrics),
        "winsor_quantiles": [float(config.lower_winsor_q), float(config.upper_winsor_q)],
        "notes": [
            "Residuals are joint linear residuals against the established revised 9D control panel.",
            "Controls follow the current five-metric panel: spectral_radius, anisotropy, frobenius, rotational_power_mean, mdr.",
        ],
        "config": {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in asdict(config).items()
        },
    }
    (config.output_dir / "wave1_residual_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote outputs to {config.output_dir}", flush=True)


if __name__ == "__main__":
    main()
