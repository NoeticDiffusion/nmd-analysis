"""Fixed-duration sensitivity pilot for the frozen ds004511 L1 family.

The pilot re-aggregates already exported per-window L1 series over a
deterministic 100-window prefix (400 s at the pinned 4 s grid). It uses the
exported validity masks and the production L1 reductions; it does not refit
diffusion or drift, relax support, exclude PSD-floor values, or fill missing
values. Results are a sensitivity family, not a replacement for the frozen
full-recording task panel.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from ds04511_common import (
    ARTICLE_DIR,
    MIN_VALID_FRACTION,
    MIN_VALID_TIMEPOINTS,
    TASK_DISPLAY,
    json_safe,
    sha256_file,
    write_json,
)
from ds04511_panel import CONTRASTS, METRICS, MetricSpec
from ds04511_stats import bh_fdr
from ds04511_task_part1 import (
    contrast_row,
    load_cohort,
    paired_differences,
    reduce_series,
)
from ds04511_task_part1 import LABELS_DEFAULT, SUPPORT_DEFAULT
from ds04511_task_part1 import friedman_rows


ANALYSIS_ID = "l1_duration_support_robustness_20260922"
BALANCED_WINDOWS = 100
MODAL_DT_SEC = 4.0
FIXED_DURATION_SEC = BALANCED_WINDOWS * MODAL_DT_SEC
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_l1_duration_robustness_20260922"
FULL_RECORDING_ROOT = ARTICLE_DIR / "results" / "v1_task_20260922_d_eff_qc_excluded"

L1_METRICS = tuple(spec for spec in METRICS if spec.level == "L1")
L1_METRIC_IDS = tuple(spec.metric_id for spec in L1_METRICS)


def _read_array(handle: h5py.File, path: str | None) -> np.ndarray | None:
    if path is None or path not in handle:
        return None
    node = handle[path]
    if isinstance(node, h5py.Group):
        return None
    return np.asarray(node[()], dtype=float)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def fixed_prefix_metric(
    path: Path,
    spec: MetricSpec,
    *,
    support_included: bool = True,
    n_windows: int = BALANCED_WINDOWS,
    min_valid_n: int = MIN_VALID_TIMEPOINTS,
    min_valid_fraction: float = MIN_VALID_FRACTION,
) -> dict[str, Any]:
    """Aggregate one exported series over a fixed prefix with strict validity."""
    prefix = f"fixed_{spec.metric_id}"
    row: dict[str, Any] = {
        f"{prefix}_included": False,
        f"{prefix}_median": float("nan"),
        f"{prefix}_n_available": 0,
        f"{prefix}_n_exported": 0,
        f"{prefix}_n_valid": 0,
        f"{prefix}_valid_fraction": float("nan"),
        f"{prefix}_n_psd_floor_applied": 0,
        f"{prefix}_reason": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            raw = _read_array(handle, spec.value_path)
            valid_raw = _read_array(handle, spec.valid_path)
            floor_raw = _read_array(handle, spec.extra_exclude_path)
        if raw is None:
            row[f"{prefix}_reason"] = "missing_value_series"
            return row
        if valid_raw is None:
            row[f"{prefix}_reason"] = "missing_validity_series"
            return row
        values = reduce_series(raw, spec.reduce, spec.column)
        valid = reduce_series(valid_raw, None)
        row[f"{prefix}_n_available"] = int(values.size)
        if valid.size != values.size:
            row[f"{prefix}_reason"] = "validity_length_mismatch"
            return row
        if values.size < n_windows:
            row[f"{prefix}_reason"] = "shorter_than_fixed_prefix"
            return row
        if floor_raw is not None:
            floor = reduce_series(floor_raw, None)
            if floor.size == values.size:
                row[f"{prefix}_n_psd_floor_applied"] = int(np.sum(floor[:n_windows] == 1))
        if spec.family == "diffusion" and not support_included:
            row[f"{prefix}_reason"] = "h1_h2_support_not_included"
            return row
        prefix_values = values[:n_windows]
        prefix_valid = valid[:n_windows] == 1
        finite_valid = prefix_valid & np.isfinite(prefix_values)
        n_valid = int(finite_valid.sum())
        fraction = float(n_valid / n_windows)
        row[f"{prefix}_n_exported"] = int(n_windows)
        row[f"{prefix}_n_valid"] = n_valid
        row[f"{prefix}_valid_fraction"] = fraction
        if n_valid < min_valid_n or fraction < min_valid_fraction:
            row[f"{prefix}_reason"] = "insufficient_fixed_prefix_support"
            return row
        row[f"{prefix}_included"] = True
        row[f"{prefix}_median"] = float(np.median(prefix_values[finite_valid]))
        row[f"{prefix}_reason"] = "ok"
        return row
    except Exception as exc:  # noqa: BLE001
        row[f"{prefix}_reason"] = f"read_error:{type(exc).__name__}"
        return row


def extract_fixed_prefix(
    labels_path: Path,
    support_path: Path,
    *,
    n_windows: int = BALANCED_WINDOWS,
    workers: int = 1,
) -> pd.DataFrame:
    cohort = load_cohort(labels_path, support_path)
    specs = L1_METRICS

    def extract_one(item: tuple[str, bool]) -> dict[str, Any]:
        source_h5, support_included = item
        row: dict[str, Any] = {"source_h5": source_h5}
        for spec in specs:
            row.update(
                fixed_prefix_metric(
                    Path(source_h5),
                    spec,
                    support_included=support_included,
                    n_windows=n_windows,
                )
            )
        return row

    items = [
        (str(source), _truthy(support))
        for source, support in zip(
            cohort["source_h5"].astype(str),
            cohort["h1_h2_support_included"].tolist(),
        )
    ]
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            extracted = list(pool.map(extract_one, items))
    else:
        extracted = [extract_one(item) for item in items]
    return cohort.merge(pd.DataFrame(extracted), on="source_h5", how="left")


def make_subject_task(recordings: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (subject, task), group in recordings.groupby(["subject_id", "task_label"], dropna=False):
        row: dict[str, Any] = {
            "subject_id": subject,
            "task_label": task,
            "n_recordings": int(len(group)),
        }
        for spec in L1_METRICS:
            name = f"fixed_{spec.metric_id}"
            included = group[name + "_included"] == True  # noqa: E712
            values = pd.to_numeric(group.loc[included, name + "_median"], errors="coerce").dropna()
            row[spec.metric_id] = float(values.median()) if len(values) else float("nan")
            row[name + "_n_recordings_included"] = int(len(values))
        rows.append(row)
    return pd.DataFrame(rows)


def make_contrasts(subjects: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pair_frames: list[pd.DataFrame] = []
    rows: list[dict[str, Any]] = []
    for contrast in CONTRASTS:
        for spec in L1_METRICS:
            paired = paired_differences(subjects, contrast, spec.metric_id)
            pair_frames.append(paired)
            rows.append(contrast_row(paired, spec, contrast))
    pairs = pd.concat(pair_frames, ignore_index=True)
    table = pd.DataFrame(rows)
    table["bh_q_l1_sensitivity_family"] = bh_fdr(table["wilcoxon_p"].to_numpy())
    return pairs, table


def compare_full_recording(fixed: pd.DataFrame, full_root: Path) -> pd.DataFrame:
    full = pd.read_csv(full_root / "task_contrasts.csv")
    full = full[full["metric"].isin(L1_METRIC_IDS)][
        ["contrast_id", "metric", "n_pairs", "median_paired_difference", "cohens_dz", "wilcoxon_p", "bh_q"]
    ].rename(
        columns={
            "n_pairs": "full_n_pairs",
            "median_paired_difference": "full_median_difference",
            "cohens_dz": "full_cohens_dz",
            "wilcoxon_p": "full_wilcoxon_p",
            "bh_q": "full_bh_q_45_family",
        }
    )
    result = fixed.merge(full, on=["contrast_id", "metric"], how="left")
    result = result.rename(
        columns={
            "n_pairs": "fixed_n_pairs",
            "median_paired_difference": "fixed_median_difference",
            "cohens_dz": "fixed_cohens_dz",
            "wilcoxon_p": "fixed_wilcoxon_p",
            "bh_q_l1_sensitivity_family": "fixed_bh_q_12_family",
        }
    )
    result["same_effect_sign"] = np.sign(result["fixed_median_difference"]) == np.sign(
        result["full_median_difference"]
    )
    result["dz_delta_fixed_minus_full"] = result["fixed_cohens_dz"] - result["full_cohens_dz"]
    result["median_delta_fixed_minus_full"] = (
        result["fixed_median_difference"] - result["full_median_difference"]
    )
    result["q_comparison_note"] = "full q=45-test task family; fixed q=12-test L1 sensitivity family"
    return result


def compare_full_friedman(fixed: pd.DataFrame, full_root: Path) -> pd.DataFrame:
    full = pd.read_csv(full_root / "task_friedman.csv")
    full = full[full["metric"].isin(L1_METRIC_IDS)][
        ["metric", "n_subjects", "friedman_chi2", "friedman_p", "bh_q"]
    ].rename(
        columns={
            "n_subjects": "full_n_subjects",
            "friedman_chi2": "full_friedman_chi2",
            "friedman_p": "full_friedman_p",
            "bh_q": "full_friedman_bh_q_15_family",
        }
    )
    result = fixed.merge(full, on="metric", how="left")
    result = result.rename(
        columns={
            "n_subjects": "fixed_n_subjects",
            "friedman_chi2": "fixed_friedman_chi2",
            "friedman_p": "fixed_friedman_p",
            "bh_q": "fixed_friedman_bh_q_4_family",
        }
    )
    result["friedman_p_delta_fixed_minus_full"] = (
        result["fixed_friedman_p"] - result["full_friedman_p"]
    )
    result["q_comparison_note"] = "full q=15-test Friedman family; fixed q=4-test L1 sensitivity family"
    return result


def write_report(
    path: Path,
    comparison: pd.DataFrame,
    friedman_comparison: pd.DataFrame,
    missingness: pd.DataFrame,
) -> None:
    lines = [
        "# ds004511 fixed-duration L1 robustness pilot",
        "",
        f"Analysis id: `{ANALYSIS_ID}`. Exploratory sensitivity only; the production task panel and Typst sources are unchanged.",
        "",
        f"All four frozen L1 series were re-aggregated over the deterministic first {BALANCED_WINDOWS} windows ({FIXED_DURATION_SEC:g} s at the pinned 4 s grid). Exported validity masks and the existing minimum support rule (30 finite windows and ≥50%) were required. No refit, interpolation, zero filling, PSD-floor exclusion, or relaxed support was used.",
        "",
        "## Pairwise sensitivity (12-test L1 family)",
        "",
        "Full-recording q values come from the corrected 45-test task family; fixed-prefix q values are BH-corrected within the 12-test L1 sensitivity family and are not directly comparable as multiplicity-adjusted values.",
        "",
        "| Contrast | Metric | n full/fixed | Δ full | Δ fixed | d_z full | d_z fixed | fixed p | fixed q | sign agrees |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in comparison.iterrows():
        lines.append(
            "| `{contrast}` | `{metric}` | {nf}/{nx} | {df} | {dx} | {zf} | {zx} | {p} | {q} | {same} |".format(
                contrast=row["contrast_id"],
                metric=row["metric"],
                nf=int(row["full_n_pairs"]),
                nx=int(row["fixed_n_pairs"]),
                df=_fmt(row["full_median_difference"]),
                dx=_fmt(row["fixed_median_difference"]),
                zf=_fmt(row["full_cohens_dz"], 3),
                zx=_fmt(row["fixed_cohens_dz"], 3),
                p=_fmt(row["fixed_wilcoxon_p"]),
                q=_fmt(row["fixed_bh_q_12_family"]),
                same=bool(row["same_effect_sign"]),
            )
        )
    lines.extend(
        [
            "",
            "## Omnibus sensitivity (four-test L1 Friedman family)",
            "",
            "| Metric | n full/fixed | chi2 full | chi2 fixed | p full | p fixed | fixed BH q |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in friedman_comparison.iterrows():
        lines.append(
            "| `{metric}` | {nf}/{nx} | {cf} | {cx} | {pf} | {px} | {q} |".format(
                metric=row["metric"],
                nf=int(row["full_n_subjects"]),
                nx=int(row["fixed_n_subjects"]),
                cf=_fmt(row["full_friedman_chi2"]),
                cx=_fmt(row["fixed_friedman_chi2"]),
                pf=_fmt(row["full_friedman_p"]),
                px=_fmt(row["fixed_friedman_p"]),
                q=_fmt(row["fixed_friedman_bh_q_4_family"]),
            )
        )
    lines.extend(
        [
            "",
            "## Prefix support",
            "",
            "| Metric | included | short | support/validity failures |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in missingness.iterrows():
        lines.append(
            "| `{metric}` | {inc} | {short} | {fail} |".format(
                metric=row["metric"],
                inc=int(row["n_included"]),
                short=int(row["n_short_prefix"]),
                fail=int(row["n_failure"]),
            )
        )
    lines.extend(
        [
            "",
            "Interpretation ceiling: agreement in sign and effect size is a fixed-support sensitivity result for chart-level L1 summaries. It does not establish estimator invariance across horizons, mechanism, or a duration-independent task effect. Full-recording and prefix q values use different BH families.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt(value: Any, digits: int = 4) -> str:
    value = float(value)
    if not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}g}"


def run(
    *,
    labels_path: Path,
    support_path: Path,
    full_root: Path,
    output_root: Path,
    n_windows: int = BALANCED_WINDOWS,
    workers: int = 1,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    recordings = extract_fixed_prefix(
        labels_path,
        support_path,
        n_windows=n_windows,
        workers=workers,
    )
    recordings.to_csv(output_root / "l1_duration_run_level.csv", index=False)
    subjects = make_subject_task(recordings)
    subjects.to_csv(output_root / "l1_duration_subject_task.csv", index=False)

    pairs, contrasts = make_contrasts(subjects)
    pairs.to_csv(output_root / "l1_duration_paired_differences.csv", index=False)
    full_comparison = compare_full_recording(contrasts, full_root)
    full_comparison.to_csv(output_root / "l1_duration_contrasts.csv", index=False)

    friedman = friedman_rows(subjects, L1_METRICS)
    friedman.to_csv(output_root / "l1_duration_friedman.csv", index=False)
    friedman_comparison = compare_full_friedman(friedman, full_root)
    friedman_comparison.to_csv(output_root / "l1_duration_friedman_comparison.csv", index=False)

    missing_rows = []
    for spec in L1_METRICS:
        prefix = f"fixed_{spec.metric_id}"
        reasons = recordings[prefix + "_reason"].astype(str)
        missing_rows.append(
            {
                "metric": spec.metric_id,
                "n_recordings": int(len(recordings)),
                "n_included": int(recordings[prefix + "_included"].sum()),
                "n_short_prefix": int((reasons == "shorter_than_fixed_prefix").sum()),
                "n_failure": int((reasons != "ok").sum()),
                "n_missing_validity": int((reasons == "missing_validity_series").sum()),
                "n_mask_mismatch": int((reasons == "validity_length_mismatch").sum()),
                "n_support_excluded": int((reasons == "h1_h2_support_not_included").sum()),
                "min_valid_fraction": float(recordings[prefix + "_valid_fraction"].min()),
            }
        )
    missingness = pd.DataFrame(missing_rows)
    missingness.to_csv(output_root / "l1_duration_missingness.csv", index=False)
    write_report(
        output_root / "l1_duration_robustness.md",
        full_comparison,
        friedman_comparison,
        missingness,
    )

    script_path = Path(__file__).resolve()
    manifest = {
        "schema": "ds004511_ndt_v1.l1_duration_robustness.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "method_limited_sensitivity",
        "confirmatory_contrasts": False,
        "n_recordings": int(len(recordings)),
        "n_fixed_prefix_included_all_metrics": int(
            recordings[[f"fixed_{metric}_included" for metric in L1_METRIC_IDS]].all(axis=1).sum()
        ),
        "n_windows": int(n_windows),
        "fixed_duration_sec": float(n_windows * MODAL_DT_SEC),
        "modal_dt_sec": MODAL_DT_SEC,
        "minimum_valid_windows": int(MIN_VALID_TIMEPOINTS),
        "minimum_valid_fraction": float(MIN_VALID_FRACTION),
        "l1_metric_ids": list(L1_METRIC_IDS),
        "n_pairwise_sensitivity_tests": int(len(contrasts)),
        "n_friedman_sensitivity_tests": int(len(friedman)),
        "production_measurements_changed": False,
        "typst_files_changed": False,
        "validity_semantics": (
            "strict exported per-window validity masks; diffusion retains the production "
            "h1_h2_support_included gate; PSD-floor values are not excluded, matching the "
            "primary full-recording task panel"
        ),
        "full_recording_root": str(full_root),
        "input_sha256": {
            "labels": sha256_file(labels_path),
            "support": sha256_file(support_path),
            "full_task_contrasts": sha256_file(full_root / "task_contrasts.csv"),
            "full_task_friedman": sha256_file(full_root / "task_friedman.csv"),
            "script": sha256_file(script_path),
        },
        "note": (
            "Fixed-prefix L1 reaggregation only. Full-recording and sensitivity BH q values "
            "are from different families and must not be compared as if one family."
        ),
    }
    write_json(output_root / "l1_duration_robustness_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--support", type=Path, default=SUPPORT_DEFAULT)
    parser.add_argument("--full-root", type=Path, default=FULL_RECORDING_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--n-windows", type=int, default=BALANCED_WINDOWS)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    if args.n_windows < MIN_VALID_TIMEPOINTS:
        raise SystemExit(f"--n-windows must be >= {MIN_VALID_TIMEPOINTS}")
    manifest = run(
        labels_path=args.labels,
        support_path=args.support,
        full_root=args.full_root,
        output_root=args.output_root,
        n_windows=args.n_windows,
        workers=args.workers,
    )
    print(
        json.dumps(
            {
                "output_root": str(args.output_root),
                "n_recordings": manifest["n_recordings"],
                "n_fixed_prefix_included_all_metrics": manifest["n_fixed_prefix_included_all_metrics"],
                "n_pairwise_sensitivity_tests": manifest["n_pairwise_sensitivity_tests"],
                "n_friedman_sensitivity_tests": manifest["n_friedman_sensitivity_tests"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
