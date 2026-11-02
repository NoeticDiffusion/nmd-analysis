"""Bounded duration/support robustness checks for ds004511 NDT v1.

This module does not re-fit any measurement family.  It re-aggregates the
already exported chart-Jacobian spectral-abscissa series on a fixed prefix of
100 windows (400 s at the pinned 4 s sampling interval), then audits whether
the recording-level L4 amplitude summaries are associated with recording
duration within task.  L4 truncation is deliberately not attempted because
the export contains only one ``a_q``/``v_norm`` scalar per recording.

The outputs are exploratory sensitivity diagnostics and do not alter the
production task or level panels.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from ds04511_common import (
    ARTICLE_DIR,
    DEFAULT_H5_ROOT,
    MIN_VALID_FRACTION,
    MIN_VALID_TIMEPOINTS,
    TASK_DISPLAY,
    json_safe,
    sha256_file,
    write_json,
)
from ds04511_level_panel import LEVEL_CONTRASTS, LEVEL_METRICS
from ds04511_stats import bh_fdr
from ds04511_task_part1 import (
    LABELS_DEFAULT,
    SUPPORT_DEFAULT,
    paired_differences,
    contrast_row,
    load_cohort,
)


ANALYSIS_ID = "duration_support_robustness_20260922"
BALANCED_WINDOWS = 100
BALANCED_DURATION_SEC = 400.0
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_duration_robustness_20260922"
LEVEL_DEFAULT = ARTICLE_DIR / "results" / "v1_level_20260921"
TASK_DEFAULT = ARTICLE_DIR / "results" / "v1_task_20260921"


def fixed_prefix_median(
    path: Path,
    *,
    n_windows: int = BALANCED_WINDOWS,
    min_valid_n: int = MIN_VALID_TIMEPOINTS,
    min_valid_fraction: float = MIN_VALID_FRACTION,
) -> dict[str, Any]:
    """Median of the finite exported alpha series in a fixed prefix.

    The support threshold is the same minimum count/fraction used by the
    production recording aggregation.  A recording shorter than the fixed
    prefix is missing rather than padded or extrapolated.
    """
    row: dict[str, Any] = {
        "source_h5": str(path),
        "window_start": 0,
        "window_end_exclusive": int(n_windows),
        "n_available": 0,
        "n_valid": 0,
        "valid_fraction": float("nan"),
        "included": False,
        "jacobian_alpha_fixed_median": float("nan"),
        "reason": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            values = np.asarray(
                handle["jacobian/derived_metrics/v1/series/spectral_abscissa"][()],
                dtype=float,
            ).reshape(-1)
        row["n_available"] = int(values.size)
        if values.size < n_windows:
            row["reason"] = "shorter_than_fixed_prefix"
            return row
        prefix = values[:n_windows]
        finite = np.isfinite(prefix)
        n_valid = int(finite.sum())
        fraction = float(n_valid / n_windows)
        row["n_valid"] = n_valid
        row["valid_fraction"] = fraction
        if n_valid < min_valid_n or fraction < min_valid_fraction:
            row["reason"] = "insufficient_fixed_prefix_support"
            return row
        row["included"] = True
        row["jacobian_alpha_fixed_median"] = float(np.median(prefix[finite]))
        row["reason"] = "ok"
        return row
    except Exception as exc:  # noqa: BLE001
        row["reason"] = f"read_error:{type(exc).__name__}"
        return row


def extract_fixed_alpha(
    labels_path: Path,
    *,
    n_windows: int = BALANCED_WINDOWS,
    workers: int = 1,
) -> pd.DataFrame:
    """Extract fixed-prefix alpha values while preserving G1 identity labels."""
    labels = pd.read_csv(labels_path)
    paths = labels["source_h5"].astype(str).tolist()
    worker = lambda value: fixed_prefix_median(Path(value), n_windows=n_windows)
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            extracted = list(pool.map(worker, paths))
    else:
        extracted = [worker(value) for value in paths]
    return labels.merge(pd.DataFrame(extracted), on="source_h5", how="left")


def make_fixed_subject_task(recordings: pd.DataFrame) -> pd.DataFrame:
    """Collapse fixed-window recording values to subject/task medians."""
    rows: list[dict[str, Any]] = []
    for (subject, task), group in recordings.groupby(["subject_id", "task_label"], dropna=False):
        usable = pd.to_numeric(
            group.loc[group["included"] == True, "jacobian_alpha_fixed_median"],  # noqa: E712
            errors="coerce",
        ).dropna()
        rows.append(
            {
                "subject_id": subject,
                "task_label": task,
                "n_recordings": int(len(group)),
                "n_recordings_included": int(len(usable)),
                "jacobian_alpha_fixed": float(usable.median()) if len(usable) else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def fixed_alpha_contrasts(subjects: pd.DataFrame) -> pd.DataFrame:
    """Run the pre-existing paired contrast statistic on fixed-window alpha."""
    spec = next(metric for metric in LEVEL_METRICS if metric.metric_id == "jacobian_alpha")
    rows: list[dict[str, Any]] = []
    for contrast in LEVEL_CONTRASTS:
        later = subjects.loc[
            subjects["task_label"] == contrast.later_task,
            ["subject_id", "jacobian_alpha_fixed"],
        ].rename(columns={"jacobian_alpha_fixed": "jacobian_alpha"})
        earlier = subjects.loc[
            subjects["task_label"] == contrast.earlier_task,
            ["subject_id", "jacobian_alpha_fixed"],
        ].rename(columns={"jacobian_alpha_fixed": "jacobian_alpha"})
        pair = later.merge(earlier, on="subject_id", how="inner")
        pair["difference"] = pair["jacobian_alpha_x"] - pair["jacobian_alpha_y"]
        pair = pair.rename(columns={"jacobian_alpha_x": "later", "jacobian_alpha_y": "earlier"})
        pair["contrast_id"] = contrast.contrast_id
        pair["metric"] = "jacobian_alpha_fixed"
        row = contrast_row(pair, spec, contrast)
        row["metric"] = "jacobian_alpha_fixed"
        row["window_count"] = BALANCED_WINDOWS
        rows.append(row)
    table = pd.DataFrame(rows)
    if not table.empty:
        table["bh_q_fixed_alpha_family"] = bh_fdr(table["wilcoxon_p"].to_numpy())
    return table


def load_l4_duration_audit(
    *,
    task_run_level_path: Path,
    support_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Audit duration association for existing recording-level L4 scalars."""
    run = pd.read_csv(task_run_level_path)
    support = pd.read_csv(support_path)
    support_cols = [
        column
        for column in ("source_h5", "n_steps", "modal_dt_sec", "regular_grid")
        if column in support.columns
    ]
    audit = run.merge(support[support_cols], on="source_h5", how="left", suffixes=("", "_support"))
    n_steps = pd.to_numeric(audit.get("n_steps"), errors="coerce")
    modal_dt = pd.to_numeric(audit.get("modal_dt_sec"), errors="coerce")
    n_timepoints = pd.to_numeric(audit.get("n_timepoints"), errors="coerce")
    audit["duration_sec"] = n_steps * modal_dt
    fallback = audit["duration_sec"].isna()
    audit.loc[fallback, "duration_sec"] = (n_timepoints[fallback] - 1.0) * modal_dt[fallback]
    audit["l4_duration_status"] = "audit_only_recording_level_scalar"
    keep = [
        "source_h5",
        "subject_id",
        "task_label",
        "n_timepoints",
        "n_steps",
        "modal_dt_sec",
        "regular_grid",
        "duration_sec",
        "reach_a_q_median",
        "reach_v_norm_median",
        "reach_a_q_included",
        "reach_v_norm_included",
        "l4_duration_status",
    ]
    audit = audit[[column for column in keep if column in audit.columns]].copy()

    summary_rows: list[dict[str, Any]] = []
    correlation_rows: list[dict[str, Any]] = []
    for task, group in audit.groupby("task_label", dropna=False):
        durations = pd.to_numeric(group["duration_sec"], errors="coerce").dropna()
        summary_rows.append(
            {
                "task_label": task,
                "task_display": TASK_DISPLAY.get(task, task),
                "n_recordings": int(len(group)),
                "n_duration_finite": int(len(durations)),
                "duration_min_sec": float(durations.min()) if len(durations) else float("nan"),
                "duration_p05_sec": float(durations.quantile(0.05)) if len(durations) else float("nan"),
                "duration_median_sec": float(durations.median()) if len(durations) else float("nan"),
                "duration_p95_sec": float(durations.quantile(0.95)) if len(durations) else float("nan"),
                "duration_max_sec": float(durations.max()) if len(durations) else float("nan"),
            }
        )
        for metric in ("reach_a_q_median", "reach_v_norm_median"):
            values = pd.to_numeric(group[metric], errors="coerce")
            mask = values.notna() & pd.to_numeric(group["duration_sec"], errors="coerce").notna()
            x = pd.to_numeric(group.loc[mask, "duration_sec"], errors="coerce").to_numpy(float)
            y = values.loc[mask].to_numpy(float)
            if len(x) >= 3 and np.unique(x).size > 1 and np.unique(y).size > 1:
                rho, p_value = stats.spearmanr(x, y)
            else:
                rho, p_value = float("nan"), float("nan")
            correlation_rows.append(
                {
                    "task_label": task,
                    "metric": metric,
                    "n_finite": int(len(x)),
                    "spearman_rho": float(rho),
                    "spearman_p": float(p_value),
                    "status": "audit_only_no_l4_truncation",
                }
            )
    summary = pd.DataFrame(summary_rows)
    correlations = pd.DataFrame(correlation_rows)
    return audit, summary, correlations


def compare_primary(
    fixed: pd.DataFrame,
    *,
    primary_level_path: Path,
) -> pd.DataFrame:
    """Attach production chart-alpha rows for a direct sensitivity comparison."""
    primary = pd.read_csv(primary_level_path / "level_contrasts.csv")
    primary = primary.loc[primary["metric"] == "jacobian_alpha", [
        "contrast_id", "n_pairs", "median_paired_difference", "cohens_dz", "wilcoxon_p", "bh_q"
    ]].rename(
        columns={
            "n_pairs": "primary_n_pairs",
            "median_paired_difference": "primary_median_paired_difference",
            "cohens_dz": "primary_cohens_dz",
            "wilcoxon_p": "primary_wilcoxon_p",
            "bh_q": "primary_bh_q",
        }
    )
    merged = fixed.merge(primary, on="contrast_id", how="left")
    merged["same_effect_sign"] = np.sign(merged["median_paired_difference"]) == np.sign(
        merged["primary_median_paired_difference"]
    )
    merged["delta_ratio_fixed_over_primary"] = (
        merged["median_paired_difference"] / merged["primary_median_paired_difference"]
    )
    merged["sensitivity_status"] = "fixed_prefix_reaggregation_only"
    return merged


def write_report(
    path: Path,
    *,
    contrasts: pd.DataFrame,
    duration_summary: pd.DataFrame,
    correlations: pd.DataFrame,
) -> None:
    lines = [
        "# ds004511 fixed-duration/support robustness pilot",
        "",
        f"Analysis id: `{ANALYSIS_ID}`. Exploratory sensitivity only; production measurements and panels are unchanged.",
        "",
        f"Chart-Jacobian α was re-aggregated from the exported per-window series over the deterministic first {BALANCED_WINDOWS} windows ({BALANCED_DURATION_SEC:g} s at the pinned 4 s modal dt). No padding, interpolation, relaxed support, or re-fitting was used. The existing minimum support rule (30 finite windows and ≥50%) was retained.",
        "",
        "## Fixed-prefix chart-Jacobian α",
        "",
        "| Contrast | n | Δ median | d_z | Wilcoxon p | BH q (three alpha contrasts) | primary sign agrees |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in contrasts.iterrows():
        lines.append(
            f"| `{row['contrast_id']}` | {int(row['n_pairs'])} | {row['median_paired_difference']:.6g} | {row['cohens_dz']:.4g} | {row['wilcoxon_p']:.4g} | {row['bh_q_fixed_alpha_family']:.4g} | {bool(row['same_effect_sign'])} |"
        )
    lines.extend(
        [
            "",
            "## Recording duration",
            "",
            "| Task | n | min s | median s | max s |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in duration_summary.iterrows():
        lines.append(
            f"| {row['task_label']} | {int(row['n_recordings'])} | {row['duration_min_sec']:.4g} | {row['duration_median_sec']:.4g} | {row['duration_max_sec']:.4g} |"
        )
    lines.extend(
        [
            "",
            "## L4 duration audit",
            "",
            "The export contains only recording-level `reach_a_q` and `reach_v_norm` scalars; it has no L4 per-window series. Therefore L4 cannot be re-estimated on the fixed prefix without introducing a new estimator. The following within-task correlations are an audit, not a duration-adjusted L4 result.",
            "",
            "| Task | Metric | n | Spearman rho | p |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in correlations.iterrows():
        lines.append(
            f"| {row['task_label']} | `{row['metric']}` | {int(row['n_finite'])} | {row['spearman_rho']:.4g} | {row['spearman_p']:.4g} |"
        )
    lines.extend(
        [
            "",
            "Interpretation ceiling: fixed-prefix alpha tests support only a sampling-support sensitivity statement. The L4 audit cannot establish that the large task contrasts are duration-independent because task duration ranges are non-overlapping and L4 is not exported as a time series.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    *,
    labels_path: Path,
    support_path: Path,
    task_run_level_path: Path,
    primary_level_path: Path,
    output_root: Path,
    n_windows: int = BALANCED_WINDOWS,
    workers: int = 1,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    recordings = extract_fixed_alpha(labels_path, n_windows=n_windows, workers=workers)
    recordings.to_csv(output_root / "duration_jacobian_run_level.csv", index=False)
    subjects = make_fixed_subject_task(recordings)
    subjects.to_csv(output_root / "duration_jacobian_subject_task.csv", index=False)

    pairs_frames: list[pd.DataFrame] = []
    for contrast in LEVEL_CONTRASTS:
        later = subjects.loc[subjects["task_label"] == contrast.later_task, ["subject_id", "jacobian_alpha_fixed"]]
        earlier = subjects.loc[subjects["task_label"] == contrast.earlier_task, ["subject_id", "jacobian_alpha_fixed"]]
        pair = later.merge(earlier, on="subject_id", how="inner")
        pair["difference"] = pair["jacobian_alpha_fixed_x"] - pair["jacobian_alpha_fixed_y"]
        pair["contrast_id"] = contrast.contrast_id
        pairs_frames.append(pair.rename(columns={"jacobian_alpha_fixed_x": "later", "jacobian_alpha_fixed_y": "earlier"}))
    pairs = pd.concat(pairs_frames, ignore_index=True) if pairs_frames else pd.DataFrame()
    pairs.to_csv(output_root / "duration_jacobian_paired_differences.csv", index=False)
    contrasts = fixed_alpha_contrasts(subjects)

    comparison = compare_primary(contrasts, primary_level_path=primary_level_path)
    comparison.to_csv(output_root / "duration_jacobian_contrasts.csv", index=False)

    audit, duration_summary, correlations = load_l4_duration_audit(
        task_run_level_path=task_run_level_path,
        support_path=support_path,
    )
    audit.to_csv(output_root / "l4_duration_audit_run_level.csv", index=False)
    duration_summary.to_csv(output_root / "l4_duration_summary.csv", index=False)
    correlations.to_csv(output_root / "l4_duration_correlations.csv", index=False)
    write_report(
        output_root / "duration_robustness.md",
        contrasts=comparison,
        duration_summary=duration_summary,
        correlations=correlations,
    )

    script_path = Path(__file__).resolve()
    manifest = {
        "schema": "ds004511_ndt_v1.duration_robustness.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "method_limited_sensitivity",
        "confirmatory_contrasts": False,
        "n_recordings": int(len(recordings)),
        "n_fixed_alpha_included": int(recordings["included"].sum()),
        "n_windows": int(n_windows),
        "fixed_duration_sec": float(n_windows * 4.0),
        "minimum_valid_windows": int(MIN_VALID_TIMEPOINTS),
        "minimum_valid_fraction": float(MIN_VALID_FRACTION),
        "production_measurements_changed": False,
        "typst_files_changed": False,
        "l4_truncation_status": "unavailable_recording_level_only",
        "input_sha256": {
            "labels": sha256_file(labels_path),
            "support": sha256_file(support_path),
            "task_run_level": sha256_file(task_run_level_path),
            "primary_level": sha256_file(primary_level_path / "level_contrasts.csv"),
            "script": sha256_file(script_path),
        },
        "note": (
            "Fixed-prefix chart alpha is a reaggregation of exported per-window values. "
            "L4 duration correlations are audit-only and cannot remove between-task duration confounding."
        ),
    }
    write_json(output_root / "duration_robustness_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--support", type=Path, default=SUPPORT_DEFAULT)
    parser.add_argument("--task-run-level", type=Path, default=TASK_DEFAULT / "task_run_level.csv")
    parser.add_argument("--primary-level", type=Path, default=LEVEL_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--n-windows", type=int, default=BALANCED_WINDOWS)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    if args.n_windows < MIN_VALID_TIMEPOINTS:
        raise SystemExit(f"--n-windows must be >= {MIN_VALID_TIMEPOINTS}")
    manifest = run(
        labels_path=args.labels,
        support_path=args.support,
        task_run_level_path=args.task_run_level,
        primary_level_path=args.primary_level,
        output_root=args.output_root,
        n_windows=args.n_windows,
        workers=args.workers,
    )
    print(json.dumps({
        "output_root": str(args.output_root),
        "n_recordings": manifest["n_recordings"],
        "n_fixed_alpha_included": manifest["n_fixed_alpha_included"],
        "l4_truncation_status": manifest["l4_truncation_status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
