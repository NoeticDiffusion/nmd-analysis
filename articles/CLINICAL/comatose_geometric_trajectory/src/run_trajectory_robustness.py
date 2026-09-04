from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from compute_trajectory_metrics import (
    filtered_run_table,
    fit_codebook,
    noetic_action_metrics,
    read_run_coords,
    repertoire_metrics,
)
from trajectory_support import (
    GOOD_CPC,
    POOR_CPC,
    PRIMARY_COORDINATE_CONTRACT,
    PRIMARY_TIME_BIN,
    REPERTOIRE_STATES_BY_DIM,
    RESULT_STAMP,
    TIMELINE_PART1_DIR,
    TIMELINE_PART2_DIR,
    cohens_d,
    ensure_dir,
)


ROBUSTNESS_DIR = Path(
    f"J:/repos/NoeticDiffusion/articles/CLINICAL/comatose_geometric_trajectory/results/robustness_{RESULT_STAMP}_trajectory"
)

SELECTED_METRICS_BY_DIM: dict[int, tuple[str, ...]] = {
    3: ("noetic_action", "irreversibility", "noetic_action_jerk", "entropy_rate", "entropy_production"),
    9: ("noetic_action", "noetic_action_jerk", "entropy_rate", "irreversibility", "entropy_production"),
}
VARIANTS: tuple[str, ...] = ("observed", "time_shuffled", "reverse_time")
QC_COLUMNS: tuple[str, ...] = (
    "n_runs_support",
    "n_windows_total",
    "channel_count_median",
    "channel_coverage_frac_median",
)
PRIMARY_SUMMARY_ROWS: tuple[tuple[str, str], ...] = (
    ("trajectory_geometry_subject_anchored_3d", "noetic_action"),
    ("trajectory_geometry_subject_anchored_3d", "irreversibility"),
    ("trajectory_geometry_subject_anchored_9d", "noetic_action_jerk"),
    ("trajectory_geometry_subject_anchored_9d", "noetic_action"),
    ("trajectory_geometry_subject_anchored_9d", "entropy_rate"),
)


def analysis_type_for_dim(dim: int) -> str:
    if dim == 3:
        return "trajectory_geometry_subject_anchored_3d"
    if dim == 9:
        return "trajectory_geometry_subject_anchored_9d"
    raise ValueError(f"Unsupported dim={dim}")


def load_pooled_tables(
    timeline_dirs: dict[str, Path] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if timeline_dirs is None:
        timeline_dirs = {"part1": TIMELINE_PART1_DIR, "part2": TIMELINE_PART2_DIR}
    run_blocks: list[pd.DataFrame] = []
    patient_blocks: list[pd.DataFrame] = []
    for part, timeline_dir in timeline_dirs.items():
        run_frame = pd.read_csv(timeline_dir / "run_timing_metadata.csv", low_memory=False)
        run_frame = filtered_run_table(run_frame, primary_time_bin=PRIMARY_TIME_BIN)
        run_frame["source_cohort"] = part
        run_frame["pooled_subject"] = part + "::" + run_frame["subject"].astype(str)
        run_frame["pooled_run_key"] = (
            run_frame["pooled_subject"].astype(str)
            + "_run-"
            + run_frame["run"].astype(str).str.zfill(3)
            + "_acq-"
            + run_frame["acq"].astype(str)
        )
        run_blocks.append(run_frame)

        patient_frame = pd.read_csv(timeline_dir / "patient_timebin_summaries.csv", low_memory=False)
        patient_frame["cpc_numeric"] = pd.to_numeric(patient_frame["cpc"], errors="coerce")
        patient_frame = patient_frame[
            (patient_frame["time_bin"] == PRIMARY_TIME_BIN)
            & (patient_frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)]))
        ].copy()
        patient_frame["label"] = np.where(patient_frame["cpc_numeric"] == float(GOOD_CPC), 1, 0)
        patient_frame["source_cohort"] = part
        patient_frame["pooled_subject"] = part + "::" + patient_frame["subject"].astype(str)
        patient_blocks.append(patient_frame)
    return pd.concat(run_blocks, ignore_index=True), pd.concat(patient_blocks, ignore_index=True)


def transform_coords(coords: np.ndarray, *, variant: str, rng: np.random.Generator) -> np.ndarray:
    if variant == "observed":
        return np.asarray(coords, dtype=float)
    if variant == "time_shuffled":
        indices = rng.permutation(len(coords))
        return np.asarray(coords, dtype=float)[indices]
    if variant == "reverse_time":
        return np.asarray(coords, dtype=float)[::-1]
    raise ValueError(f"Unsupported variant={variant!r}")


def selected_metric_values(
    coords: np.ndarray,
    time: np.ndarray,
    *,
    dim: int,
    model: Any,
    metric_diag: np.ndarray,
) -> dict[str, float]:
    states = model.predict(coords)
    rep = repertoire_metrics(states, n_states=REPERTOIRE_STATES_BY_DIM[dim])
    action = noetic_action_metrics(coords, time, metric_diag=metric_diag)
    values = {**rep, **action}
    return {metric: float(values.get(metric, np.nan)) for metric in SELECTED_METRICS_BY_DIM[dim]}


def build_run_variant_metrics(run_table: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    fit_lookup: dict[int, tuple[Any, np.ndarray]] = {}
    for dim in (3, 9):
        model, metric_diag, _ = fit_codebook(run_table, dim=dim, coordinate_contract=PRIMARY_COORDINATE_CONTRACT)
        fit_lookup[dim] = (model, metric_diag)

    for row_idx, (_, run_row) in enumerate(run_table.iterrows()):
        for dim in (3, 9):
            coords, time, _ = read_run_coords(run_row, dim=dim, coordinate_contract=PRIMARY_COORDINATE_CONTRACT)
            if len(coords) < 16:
                continue
            model, metric_diag = fit_lookup[dim]
            for variant_idx, variant in enumerate(VARIANTS):
                rng = np.random.default_rng(20260601 + row_idx * 100 + dim * 10 + variant_idx)
                coords_variant = transform_coords(coords, variant=variant, rng=rng)
                metric_values = selected_metric_values(
                    coords_variant,
                    time,
                    dim=dim,
                    model=model,
                    metric_diag=metric_diag,
                )
                for metric_name, value in metric_values.items():
                    rows.append(
                        {
                            "source_cohort": run_row["source_cohort"],
                            "pooled_subject": run_row["pooled_subject"],
                            "pooled_run_key": run_row["pooled_run_key"],
                            "subject": run_row["subject"],
                            "run": run_row["run"],
                            "acq": run_row["acq"],
                            "analysis_type": analysis_type_for_dim(dim),
                            "metric": metric_name,
                            "variant": variant,
                            "value": value,
                            "label": run_row["label"],
                            "cpc": run_row["cpc"],
                            "n_windows": run_row["n_windows"],
                        }
                    )
    return pd.DataFrame(rows)


def aggregate_patient_metrics(run_variant_metrics: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["source_cohort", "pooled_subject", "subject", "analysis_type", "metric", "variant", "label", "cpc"]
    return (
        run_variant_metrics.groupby(group_cols, as_index=False)
        .agg(
            value=("value", "median"),
            n_runs_support=("pooled_run_key", "nunique"),
            n_windows_total=("n_windows", "sum"),
        )
        .reset_index(drop=True)
    )


def metric_effect_summary(patient_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    observed_lookup: dict[tuple[str, str], float] = {}
    for (analysis_type, metric, variant), group in patient_metrics.groupby(["analysis_type", "metric", "variant"], dropna=False):
        good = pd.to_numeric(group.loc[group["label"] == 1, "value"], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(group.loc[group["label"] == 0, "value"], errors="coerce").dropna().to_numpy(dtype=float)
        if good.size < 2 or poor.size < 2:
            continue
        u_stat, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
        d_value = cohens_d(good, poor)
        if variant == "observed":
            observed_lookup[(analysis_type, metric)] = float(d_value)
        rows.append(
            {
                "analysis_type": analysis_type,
                "metric": metric,
                "variant": variant,
                "cpc1_median": float(np.median(good)),
                "cpc5_median": float(np.median(poor)),
                "cohens_d": float(d_value),
                "mannwhitney_u": float(u_stat),
                "mannwhitney_p": float(p_value),
                "n_cpc1": int(good.size),
                "n_cpc5": int(poor.size),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["observed_abs_d"] = out.apply(
        lambda row: abs(observed_lookup.get((row["analysis_type"], row["metric"]), np.nan)),
        axis=1,
    )
    out["attenuation_vs_observed"] = out.apply(
        lambda row: abs(row["cohens_d"]) / row["observed_abs_d"]
        if np.isfinite(row["observed_abs_d"]) and row["observed_abs_d"] > 0
        else np.nan,
        axis=1,
    )
    return out.sort_values(["analysis_type", "metric", "variant"]).reset_index(drop=True)


def transform_correlations(run_variant_metrics: pd.DataFrame) -> pd.DataFrame:
    observed = (
        run_variant_metrics[run_variant_metrics["variant"] == "observed"][
            ["pooled_run_key", "analysis_type", "metric", "value"]
        ]
        .rename(columns={"value": "observed_value"})
        .copy()
    )
    transformed = run_variant_metrics[run_variant_metrics["variant"] != "observed"].copy()
    merged = transformed.merge(observed, on=["pooled_run_key", "analysis_type", "metric"], how="inner")
    rows: list[dict[str, Any]] = []
    for (analysis_type, metric, variant), group in merged.groupby(["analysis_type", "metric", "variant"], dropna=False):
        x = pd.to_numeric(group["observed_value"], errors="coerce")
        y = pd.to_numeric(group["value"], errors="coerce")
        mask = np.isfinite(x) & np.isfinite(y)
        if int(mask.sum()) < 3:
            continue
        rho, p_value = stats.spearmanr(x[mask], y[mask])
        rows.append(
            {
                "analysis_type": analysis_type,
                "metric": metric,
                "variant": variant,
                "n_runs": int(mask.sum()),
                "spearman_rho": float(rho),
                "spearman_p": float(p_value),
                "median_abs_delta": float(np.median(np.abs(x[mask] - y[mask]))),
            }
        )
    return pd.DataFrame(rows).sort_values(["analysis_type", "metric", "variant"]).reset_index(drop=True)


def qc_metric_correlations(patient_metrics: pd.DataFrame, patient_summary: pd.DataFrame) -> pd.DataFrame:
    observed = patient_metrics[patient_metrics["variant"] == "observed"].copy()
    merged = observed.merge(
        patient_summary[["pooled_subject", "hospital", "shockable_rhythm", "channel_count_median", "channel_coverage_frac_median"]],
        on="pooled_subject",
        how="left",
    )
    rows: list[dict[str, Any]] = []
    for (analysis_type, metric), group in merged.groupby(["analysis_type", "metric"], dropna=False):
        values = pd.to_numeric(group["value"], errors="coerce")
        for qc_col in QC_COLUMNS:
            qc_values = pd.to_numeric(group[qc_col], errors="coerce")
            mask = np.isfinite(values) & np.isfinite(qc_values)
            if int(mask.sum()) < 3:
                rows.append(
                    {
                        "analysis_type": analysis_type,
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
                    "analysis_type": analysis_type,
                    "metric": metric,
                    "qc_variable": qc_col,
                    "n": int(mask.sum()),
                    "spearman_rho": float(rho),
                    "spearman_p": float(p_value),
                }
            )
    return pd.DataFrame(rows).sort_values(["analysis_type", "metric", "qc_variable"]).reset_index(drop=True)


def build_summary_markdown(
    effect_summary: pd.DataFrame,
    transform_summary: pd.DataFrame,
    qc_summary: pd.DataFrame,
) -> str:
    lines = [
        "# Trajectory robustness summary",
        "",
        "This summary focuses on the ideas1-selected trajectory candidates and checks whether their pooled signals survive basic temporal and QC stress tests.",
        "",
        "## Selected metrics",
        "",
    ]
    for analysis_type, metric in PRIMARY_SUMMARY_ROWS:
        lines.append(f"- `{analysis_type}` / `{metric}`")
    lines.extend(["", "## Pooled effect summary by transform", ""])

    for analysis_type, metric in PRIMARY_SUMMARY_ROWS:
        block = effect_summary[
            (effect_summary["analysis_type"] == analysis_type)
            & (effect_summary["metric"] == metric)
        ].copy()
        if block.empty:
            continue
        lines.extend([f"### `{analysis_type}` / `{metric}`", ""])
        for _, row in block.sort_values("variant").iterrows():
            extra = ""
            if row["variant"] != "observed" and np.isfinite(row["attenuation_vs_observed"]):
                extra = f", attenuation={row['attenuation_vs_observed']:.3f}"
            lines.append(
                f"- `{row['variant']}`: medians `{row['cpc1_median']:.6g}` vs `{row['cpc5_median']:.6g}`, "
                f"`d = {row['cohens_d']:.3f}`, `p = {row['mannwhitney_p']:.3g}`{extra}"
            )
        lines.append("")

    lines.extend(["## Observed vs transformed metric similarity", ""])
    for analysis_type, metric in PRIMARY_SUMMARY_ROWS:
        block = transform_summary[
            (transform_summary["analysis_type"] == analysis_type)
            & (transform_summary["metric"] == metric)
        ].copy()
        if block.empty:
            continue
        lines.extend([f"### `{analysis_type}` / `{metric}`", ""])
        for _, row in block.sort_values("variant").iterrows():
            lines.append(
                f"- `{row['variant']}`: rho=`{row['spearman_rho']:.3f}`, "
                f"p=`{row['spearman_p']:.3g}`, median abs delta=`{row['median_abs_delta']:.6g}`"
            )
        lines.append("")

    lines.extend(["## Strongest QC correlations", ""])
    qc_view = qc_summary.reindex(qc_summary["spearman_rho"].abs().sort_values(ascending=False).index).head(12)
    for _, row in qc_view.iterrows():
        lines.append(
            f"- `{row['analysis_type']}` / `{row['metric']}` vs `{row['qc_variable']}`: "
            f"rho=`{row['spearman_rho']:.3f}`, p=`{row['spearman_p']:.3g}`, n=`{int(row['n'])}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run pooled temporal robustness checks on geometric trajectory metrics."
    )
    parser.add_argument("--part1-timeline-dir", type=Path, default=TIMELINE_PART1_DIR)
    parser.add_argument("--part2-timeline-dir", type=Path, default=TIMELINE_PART2_DIR)
    parser.add_argument("--output-dir", type=Path, default=ROBUSTNESS_DIR)
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    ensure_dir(output_dir)
    timeline_dirs = {"part1": args.part1_timeline_dir, "part2": args.part2_timeline_dir}
    run_table, patient_summary = load_pooled_tables(timeline_dirs)
    run_variant_metrics = build_run_variant_metrics(run_table)
    patient_metrics = aggregate_patient_metrics(run_variant_metrics)
    effect_summary = metric_effect_summary(patient_metrics)
    transform_summary = transform_correlations(run_variant_metrics)
    qc_summary = qc_metric_correlations(patient_metrics, patient_summary)

    run_variant_metrics.to_csv(output_dir / "run_variant_metrics.csv", index=False)
    patient_metrics.to_csv(output_dir / "patient_variant_metrics.csv", index=False)
    effect_summary.to_csv(output_dir / "temporal_transform_effect_summary.csv", index=False)
    transform_summary.to_csv(output_dir / "temporal_transform_correlations.csv", index=False)
    qc_summary.to_csv(output_dir / "metric_qc_correlations.csv", index=False)

    (output_dir / "robustness_summary.md").write_text(
        build_summary_markdown(effect_summary, transform_summary, qc_summary),
        encoding="utf-8",
    )
    manifest = {
        "output_dir": str(output_dir),
        "part1_timeline_dir": str(args.part1_timeline_dir),
        "part2_timeline_dir": str(args.part2_timeline_dir),
        "good_cpc": GOOD_CPC,
        "poor_cpc": POOR_CPC,
        "primary_time_bin": PRIMARY_TIME_BIN,
        "coordinate_contract": PRIMARY_COORDINATE_CONTRACT,
        "variants": list(VARIANTS),
        "selected_metrics_by_dim": {str(key): list(value) for key, value in SELECTED_METRICS_BY_DIM.items()},
        "n_runs": int(run_table["pooled_run_key"].nunique()),
        "n_subjects": int(patient_summary["pooled_subject"].nunique()),
    }
    (output_dir / "robustness_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
