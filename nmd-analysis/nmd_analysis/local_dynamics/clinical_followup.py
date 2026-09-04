"""Focused clinical follow-up analyses for local-dynamics exports.

This module intentionally keeps the ds003478 follow-up separate from the
generic parquet pipeline.  It implements the frozen BDI model and the
9D-coverage audit without changing the upstream measurement contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


BDI_BANDS = ["BDI 0-13", "BDI 14-19", "BDI 20-63"]
JACOBIAN_9D = "jacobian_metrics_9d_recording"
FTR_9D = "finite_time_response_9d_recording_horizon"

FROZEN_METRICS = {
    "jacobian_metrics_3d_recording": [
        "mean_spectral_abscissa",
        "mean_numerical_abscissa",
        "mean_reactivity_gap",
        "stable_reactive_fraction",
    ],
    "jacobian_metrics_9d_recording": [
        "mean_spectral_abscissa",
        "mean_numerical_abscissa",
        "mean_reactivity_gap",
        "stable_reactive_fraction",
    ],
    "finite_time_response_3d_recording_horizon": [
        "mean_log_g_max",
        "mean_d_resp",
        "mean_c_1",
    ],
    "finite_time_response_9d_recording_horizon": [
        "mean_log_g_max",
        "mean_d_resp",
        "mean_c_1",
    ],
}


def _latest(root: Path, stem: str) -> Path:
    matches = sorted(root.glob(f"ds003478_{stem}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No ds003478 {stem} parquet under {root}")
    return matches[-1]


def _finite_bool(series: pd.Series, *, default: bool = False) -> pd.Series:
    return series.map(lambda value: default if pd.isna(value) else bool(value))


def _finite_numeric(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return np.isfinite(values)


def _bh(values: pd.Series) -> pd.Series:
    raw = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(raw.shape, np.nan, dtype=float)
    valid = np.isfinite(raw)
    if not valid.any():
        return pd.Series(out, index=values.index, dtype=float)
    order = np.argsort(raw[valid])
    ranked = raw[valid][order]
    adjusted = ranked * ranked.size / np.arange(1, ranked.size + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    restored = np.empty_like(adjusted)
    restored[order] = np.clip(adjusted, 0.0, 1.0)
    out[valid] = restored
    return pd.Series(out, index=values.index, dtype=float)


def _fit_ols(values: pd.DataFrame, *, quadratic: bool) -> dict[str, Any]:
    work = values[["BDI", "value"]].copy()
    work["BDI"] = pd.to_numeric(work["BDI"], errors="coerce")
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work[np.isfinite(work["BDI"]) & np.isfinite(work["value"])].copy()
    n = len(work)
    parameter_count = 3 if quadratic else 2
    if n <= parameter_count:
        return {"n": n, "slope_per_10_bdi": np.nan, "p_value": np.nan, "r_squared": np.nan}

    x = work["BDI"].to_numpy(dtype=float) / 10.0
    y = work["value"].to_numpy(dtype=float)
    columns = [np.ones(n), x]
    if quadratic:
        columns.append(x**2)
    design = np.column_stack(columns)
    if np.linalg.matrix_rank(design) < parameter_count:
        return {"n": n, "slope_per_10_bdi": np.nan, "p_value": np.nan, "r_squared": np.nan}

    coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    residual = y - design @ coefficients
    degrees_of_freedom = n - parameter_count
    residual_ss = float(np.sum(residual**2))
    total_ss = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - residual_ss / total_ss if total_ss > 0 else np.nan
    covariance = (residual_ss / degrees_of_freedom) * np.linalg.inv(design.T @ design)
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    coefficient_index = 2 if quadratic else 1
    estimate = float(coefficients[coefficient_index])
    standard_error = float(standard_errors[coefficient_index])
    t_value = estimate / standard_error if standard_error > 0 else np.nan
    p_value = float(2.0 * stats.t.sf(abs(t_value), degrees_of_freedom)) if np.isfinite(t_value) else np.nan
    return {
        "n": n,
        "slope_per_10_bdi": estimate,
        "slope_se": standard_error,
        "t_value": float(t_value) if np.isfinite(t_value) else np.nan,
        "p_value": p_value,
        "r_squared": float(r_squared),
        "quadratic": quadratic,
    }


def _recording_coverage(
    cleaned_root: Path,
    *,
    analysis_type: str,
    metric: str,
    horizon_steps: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_parquet(_latest(cleaned_root, analysis_type))
    if horizon_steps is not None and "horizon_steps" in frame.columns:
        frame = frame[pd.to_numeric(frame["horizon_steps"], errors="coerce") == horizon_steps].copy()

    frame["metric_finite"] = _finite_numeric(frame[metric])
    frame["recording_valid"] = (
        _finite_bool(frame.get("finite_ok", pd.Series(False, index=frame.index)))
        & ~_finite_bool(frame.get("not_testable", pd.Series(True, index=frame.index)))
        & frame["metric_finite"]
    )
    failure = frame.get("failure_reason", pd.Series(pd.NA, index=frame.index, dtype="object"))
    not_testable = frame.get("not_testable_reason", pd.Series(pd.NA, index=frame.index, dtype="object"))
    frame["capability_available"] = ~failure.astype("string").eq("capability_missing")
    frame["gate_reason"] = failure.astype("string").fillna(not_testable.astype("string"))

    subject = (
        frame.groupby("subject_id", dropna=False)
        .agg(
            n_recordings=("subject_id", "size"),
            n_capability_available=("capability_available", "sum"),
            n_recordings_valid=("recording_valid", "sum"),
            any_recording_valid=("recording_valid", "any"),
            all_recordings_valid=("recording_valid", "all"),
        )
        .reset_index()
    )
    reasons = (
        frame.groupby(["gate_reason"], dropna=False)
        .size()
        .reset_index(name="n_recordings")
        .assign(analysis_type=analysis_type, metric=metric)
    )
    return subject, reasons


def build_coverage_audit(
    *,
    cleaned_root: str | Path,
    subject_metrics_path: str | Path,
    participants_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build subject-level 9D eligibility, BDI selection, and gate tables."""

    cleaned = Path(cleaned_root)
    participants = pd.read_csv(participants_path, sep="\t")
    participants["BDI"] = pd.to_numeric(participants["BDI"], errors="coerce")

    jacobian_subject, jacobian_reasons = _recording_coverage(
        cleaned,
        analysis_type=JACOBIAN_9D,
        metric="mean_spectral_abscissa",
    )
    ftr_subject, ftr_reasons = _recording_coverage(
        cleaned,
        analysis_type=FTR_9D,
        metric="mean_log_g_max",
        horizon_steps=4,
    )
    jacobian_subject = jacobian_subject.add_prefix("jacobian9d_").rename(
        columns={"jacobian9d_subject_id": "subject_id"}
    )
    ftr_subject = ftr_subject.add_prefix("ftr9d_").rename(columns={"ftr9d_subject_id": "subject_id"})

    subject_metrics = pd.read_parquet(subject_metrics_path)
    strict_specs = [
        (JACOBIAN_9D, "mean_spectral_abscissa", "jacobian9d_inferential_eligible"),
        (FTR_9D, "mean_log_g_max", "ftr9d_inferential_eligible"),
    ]
    strict = pd.DataFrame({"subject_id": subject_metrics["subject_id"].drop_duplicates()})
    for analysis_type, metric, output_column in strict_specs:
        rows = subject_metrics[
            (subject_metrics["analysis_type"] == analysis_type)
            & (subject_metrics["metric"] == metric)
        ].copy()
        rows[output_column] = (
            _finite_bool(rows.get("finite_ok", pd.Series(False, index=rows.index)))
            & ~_finite_bool(rows.get("not_testable", pd.Series(True, index=rows.index)))
            & _finite_numeric(rows["value"])
        )
        strict = strict.merge(rows[["subject_id", output_column]], on="subject_id", how="left")
    for column in ["jacobian9d_inferential_eligible", "ftr9d_inferential_eligible"]:
        strict[column] = strict[column].fillna(False).astype(bool)

    audit = (
        participants[["participant_id", "BDI"]]
        .rename(columns={"participant_id": "subject_id"})
        .merge(jacobian_subject, on="subject_id", how="left")
        .merge(ftr_subject, on="subject_id", how="left")
        .merge(strict, on="subject_id", how="left")
    )
    bool_columns = [
        "jacobian9d_any_recording_valid",
        "jacobian9d_all_recordings_valid",
        "ftr9d_any_recording_valid",
        "ftr9d_all_recordings_valid",
        "jacobian9d_inferential_eligible",
        "ftr9d_inferential_eligible",
    ]
    for column in bool_columns:
        audit[column] = audit[column].fillna(False).astype(bool)

    summary_rows: list[dict[str, Any]] = []
    eligibility_columns = [
        "jacobian9d_any_recording_valid",
        "jacobian9d_all_recordings_valid",
        "jacobian9d_inferential_eligible",
        "ftr9d_any_recording_valid",
        "ftr9d_all_recordings_valid",
        "ftr9d_inferential_eligible",
    ]
    bdi_known = np.isfinite(audit["BDI"])
    for column in eligibility_columns:
        eligible = audit.loc[bdi_known & audit[column], "BDI"]
        excluded = audit.loc[bdi_known & ~audit[column], "BDI"]
        eligibility = audit.loc[bdi_known, column].astype(float)
        bdi = audit.loc[bdi_known, "BDI"]
        rho, rho_p = stats.spearmanr(bdi, eligibility)
        if len(eligible) >= 2 and len(excluded) >= 2:
            bdi_difference_p = float(stats.ttest_ind(eligible, excluded, equal_var=False).pvalue)
        else:
            bdi_difference_p = np.nan
        summary_rows.append(
            {
                "eligibility": column,
                "n_bdi_known": int(bdi_known.sum()),
                "n_eligible": int(len(eligible)),
                "n_excluded": int(len(excluded)),
                "eligible_rate": float(eligibility.mean()),
                "eligible_bdi_mean": float(eligible.mean()) if len(eligible) else np.nan,
                "excluded_bdi_mean": float(excluded.mean()) if len(excluded) else np.nan,
                "bdi_difference_p": bdi_difference_p,
                "spearman_rho": float(rho),
                "spearman_p": float(rho_p),
            }
        )

    band = pd.cut(
        audit["BDI"],
        bins=[-0.1, 13, 19, 63],
        labels=BDI_BANDS,
        include_lowest=True,
    )
    band_rows: list[dict[str, Any]] = []
    for column in eligibility_columns:
        grouped = audit.assign(bdi_band=band).groupby("bdi_band", observed=False)
        for label, group in grouped:
            known = group["BDI"].notna()
            band_rows.append(
                {
                    "eligibility": column,
                    "bdi_band": str(label),
                    "n_bdi_known": int(known.sum()),
                    "n_eligible": int(group.loc[known, column].sum()),
                    "eligible_rate": float(group.loc[known, column].mean()) if known.any() else np.nan,
                }
            )
    summary = pd.DataFrame(summary_rows)
    summary = pd.concat([summary, pd.DataFrame(band_rows)], ignore_index=True, sort=False)
    gate_reasons = pd.concat([jacobian_reasons, ftr_reasons], ignore_index=True)
    return audit, summary, gate_reasons


def build_continuous_bdi_results(
    *,
    subject_metrics_path: str | Path,
    coverage_audit: pd.DataFrame,
) -> pd.DataFrame:
    """Fit the frozen linear BDI model and one quadratic sensitivity model."""

    subject_metrics = pd.read_parquet(subject_metrics_path)
    bdi = coverage_audit[["subject_id", "BDI"]]
    rows: list[dict[str, Any]] = []
    for analysis_type, metrics in FROZEN_METRICS.items():
        space = "3d" if "_3d_" in analysis_type else "9d"
        for metric in metrics:
            frame = subject_metrics[
                (subject_metrics["analysis_type"] == analysis_type)
                & (subject_metrics["metric"] == metric)
            ].copy()
            frame = frame.merge(bdi, on="subject_id", how="left")
            eligible = (
                _finite_bool(frame.get("finite_ok", pd.Series(False, index=frame.index)))
                & ~_finite_bool(frame.get("not_testable", pd.Series(True, index=frame.index)))
                & _finite_numeric(frame["value"])
                & _finite_numeric(frame["BDI"])
            )
            fit = _fit_ols(frame.loc[eligible, ["BDI", "value"]], quadratic=False)
            rows.append(
                {
                    "model": "linear",
                    "space": space,
                    "analysis_type": analysis_type,
                    "metric": metric,
                    "n": fit["n"],
                    "slope_per_10_bdi": fit["slope_per_10_bdi"],
                    "slope_se": fit.get("slope_se", np.nan),
                    "t_value": fit.get("t_value", np.nan),
                    "p_value": fit["p_value"],
                    "r_squared": fit["r_squared"],
                    "inference_status": (
                        "primary_testable" if space == "3d" else "selection_limited_exploratory"
                    ),
                }
            )
            if space == "3d":
                nonlinear = _fit_ols(frame.loc[eligible, ["BDI", "value"]], quadratic=True)
                rows.append(
                    {
                        "model": "quadratic_sensitivity",
                        "space": space,
                        "analysis_type": analysis_type,
                        "metric": metric,
                        "n": nonlinear["n"],
                        "slope_per_10_bdi": nonlinear["slope_per_10_bdi"],
                        "quadratic_term_per_100_bdi2": nonlinear["slope_per_10_bdi"],
                        "slope_se": nonlinear.get("slope_se", np.nan),
                        "t_value": nonlinear.get("t_value", np.nan),
                        "p_value": nonlinear["p_value"],
                        "r_squared": nonlinear["r_squared"],
                        "inference_status": "secondary_sensitivity",
                    }
                )

    results = pd.DataFrame(rows)
    for model in ["linear", "quadratic_sensitivity"]:
        mask = results["model"] == model
        results.loc[mask, "q_value"] = results.loc[mask].groupby("space")["p_value"].transform(_bh)
    return results


def run_ds003478_followup(
    *,
    cleaned_root: str | Path,
    subject_metrics_path: str | Path,
    participants_path: str | Path,
    output_root: str | Path,
) -> dict[str, str]:
    """Run and persist the ds003478 coverage and continuous-BDI follow-up."""

    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    audit, summary, gate_reasons = build_coverage_audit(
        cleaned_root=cleaned_root,
        subject_metrics_path=subject_metrics_path,
        participants_path=participants_path,
    )
    results = build_continuous_bdi_results(
        subject_metrics_path=subject_metrics_path,
        coverage_audit=audit,
    )
    paths = {
        "coverage_audit": output / "ds003478_9d_coverage_subject_audit.csv",
        "coverage_summary": output / "ds003478_9d_coverage_summary.csv",
        "gate_reasons": output / "ds003478_9d_gate_reasons.csv",
        "continuous_bdi": output / "ds003478_continuous_bdi_results.csv",
    }
    audit.to_csv(paths["coverage_audit"], index=False)
    summary.to_csv(paths["coverage_summary"], index=False)
    gate_reasons.to_csv(paths["gate_reasons"], index=False)
    results.to_csv(paths["continuous_bdi"], index=False)
    manifest = {
        "dataset": "ds003478",
        "bdi_bins": BDI_BANDS,
        "frozen_primary_surface": FROZEN_METRICS,
        "linear_model_scale": "slope per 10 BDI points",
        "quadratic_model": "one predefined quadratic sensitivity on 3D only",
        "nine_d_inference_status": "selection_limited_exploratory",
        "paths": {key: str(value) for key, value in paths.items()},
    }
    manifest_path = output / "ds003478_continuous_bdi_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    paths["manifest"] = manifest_path
    return {key: str(value) for key, value in paths.items()}
