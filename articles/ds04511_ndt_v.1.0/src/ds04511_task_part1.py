"""Within-subject Rest / CC / GG contrasts. Exploratory; G4 not locked.

Recording median -> subject/task median -> paired later-minus-earlier.
Occupancy is chart state, not MNJ and not reachability.
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

from ds04511_aggregate import recording_median, sign_test_denominator
from ds04511_common import (
    ARTICLE_DIR,
    DEFAULT_H5_ROOT,
    MIN_VALID_FRACTION,
    MIN_VALID_TIMEPOINTS,
    TASK_DISPLAY,
    TASKS,
    json_safe,
    scalar,
    sha256_file,
    write_json,
)
from ds04511_panel import (
    BOOTSTRAP_N,
    BOOTSTRAP_SEED,
    CONFIRMATORY_STATUS,
    CONTRASTS,
    METRICS,
    QC_ONLY_METRIC_IDS,
    SUBSTANTIVE_METRIC_IDS,
    MIN_TESTABLE_N,
    ContrastSpec,
    MetricSpec,
    metric_test_scope,
)
from ds04511_stats import bh_fdr, cohens_dz, exact_sign_test_p, friedman_p, percentile_bootstrap, wilcoxon_p

ANALYSIS_ID = "task_within_subject_20260922_d_eff_qc_excluded"
LABELS_DEFAULT = ARTICLE_DIR / "results" / "ingest_20260921" / "g1_recording_labels.csv"
SUPPORT_DEFAULT = ARTICLE_DIR / "results" / "ingest_20260921" / "g2_recording_support.csv"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_task_20260922_d_eff_qc_excluded"
LEGACY_CONTRASTS_DEFAULT = ARTICLE_DIR / "results" / "v1_task_20260921" / "task_contrasts.csv"


def _read_array(handle: h5py.File, path: str | None) -> np.ndarray | None:
    if path is None or path not in handle:
        return None
    node = handle[path]
    if isinstance(node, h5py.Group):
        return None
    return np.asarray(node[()], dtype=float)


def reduce_series(array: np.ndarray, reduce: str | None, column: int | None = None) -> np.ndarray:
    values = np.asarray(array, dtype=float)
    if column is not None:
        if values.ndim < 2:
            raise ValueError(f"column reduce requires >=2D array, got {values.shape}")
        values = values[:, column]
    if reduce is None or values.ndim <= 1:
        return values.reshape(-1)
    if reduce == "frobenius":
        if values.ndim == 2:
            return np.asarray([float(np.linalg.norm(values, ord="fro"))], dtype=float)
        return np.linalg.norm(values.reshape(values.shape[0], -1), axis=1)
    if reduce == "l2":
        return np.linalg.norm(values.reshape(values.shape[0], -1), axis=1)
    if reduce == "trace":
        if values.ndim == 2:
            return np.asarray([float(np.trace(values))], dtype=float)
        if values.ndim == 3 and values.shape[-1] == values.shape[-2]:
            return np.trace(values, axis1=1, axis2=2)
        raise ValueError(f"trace reduce requires square trailing axes, got {values.shape}")
    raise ValueError(f"unknown reduce {reduce!r}")


def _status(handle: h5py.File, cert_path: str) -> str:
    key = f"{cert_path}/computation_status"
    if key not in handle:
        return "not_recorded"
    return str(scalar(handle[key][()]) or "not_recorded")


def _metric_value(handle: h5py.File, spec: MetricSpec, *, exclude_floor: bool = False) -> dict[str, Any]:
    status = _status(handle, spec.cert_path)
    prefix = spec.metric_id if not exclude_floor else f"{spec.metric_id}_nopsd"
    out = {
        f"{prefix}_computation_status": status,
        f"{prefix}_included": False,
        f"{prefix}_median": float("nan"),
        f"{prefix}_n_valid": 0,
        f"{prefix}_n_exported": 0,
    }
    status_ok = (status == "computed") or (not spec.require_computed and status in {"computed", "not_recorded"})
    if not status_ok:
        out[f"{prefix}_reason"] = f"computation_status={status}"
        return out
    if spec.grain == "summary":
        raw = _read_array(handle, spec.value_path)
        values = None if raw is None else reduce_series(raw, spec.reduce, spec.column)
        if values is None or values.size == 0 or not np.isfinite(values.reshape(-1)[0]):
            out[f"{prefix}_reason"] = "missing_or_nonfinite_summary"
            return out
        value = float(values.reshape(-1)[0])
        out[f"{prefix}_included"] = True
        out[f"{prefix}_median"] = value
        out[f"{prefix}_n_valid"] = 1
        out[f"{prefix}_n_exported"] = 1
        out[f"{prefix}_reason"] = "ok"
        return out
    raw = _read_array(handle, spec.value_path)
    if raw is None:
        out[f"{prefix}_reason"] = "missing_series"
        return out
    values = reduce_series(raw, spec.reduce, spec.column)
    valid = _read_array(handle, spec.valid_path)
    if valid is not None:
        valid = reduce_series(valid, None)
    if valid is None or valid.size != values.size:
        valid = np.isfinite(values).astype(float)
    extra = None
    if exclude_floor and spec.extra_exclude_path:
        extra_raw = _read_array(handle, spec.extra_exclude_path)
        extra = None if extra_raw is None else reduce_series(extra_raw, None)
    min_n = 1 if spec.grain == "broadcast" else MIN_VALID_TIMEPOINTS
    min_frac = 0.0 if spec.grain == "broadcast" else MIN_VALID_FRACTION
    result = recording_median(values, valid, min_n=min_n, min_frac=min_frac, extra_exclude=extra)
    if spec.grain == "broadcast" and result["n_valid"] >= 1:
        finite = values[np.isfinite(values)]
        if finite.size and np.unique(np.round(finite, 12)).size <= 1:
            result["included"] = True
            result["median"] = float(finite[0])
    out[f"{prefix}_included"] = bool(result["included"])
    out[f"{prefix}_median"] = float(result["median"])
    out[f"{prefix}_n_valid"] = int(result["n_valid"])
    out[f"{prefix}_n_exported"] = int(result["n_exported"])
    out[f"{prefix}_reason"] = "ok" if result["included"] else "insufficient_support"
    return out


def extract_one(path: str, metrics: tuple[MetricSpec, ...] | None = None) -> dict[str, Any]:
    specs = metrics if metrics is not None else METRICS
    row: dict[str, Any] = {"source_h5": path, "read_ok": False, "read_error": None}
    try:
        with h5py.File(path, "r") as handle:
            for spec in specs:
                row.update(_metric_value(handle, spec))
                if spec.extra_exclude_path is not None:
                    row.update(_metric_value(handle, spec, exclude_floor=True))
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def load_cohort(labels_path: Path, support_path: Path) -> pd.DataFrame:
    labels = pd.read_csv(labels_path)
    support = pd.read_csv(support_path)
    keep_support = [
        column
        for column in (
            "source_h5",
            "h1_h2_support_included",
            "h1_h2_psd_floor_excluded_included",
            "diffusion_computation_status",
            "one_step_computation_status",
        )
        if column in support.columns
    ]
    merged = labels.merge(support[keep_support], on="source_h5", how="left")
    if merged["task_label"].isna().any():
        raise RuntimeError("task analysis requires G1 labels on every recording")
    return merged


def extract_recordings(
    cohort: pd.DataFrame,
    *,
    workers: int,
    metrics: tuple[MetricSpec, ...] | None = None,
) -> pd.DataFrame:
    from functools import partial

    paths = cohort["source_h5"].astype(str).tolist()
    worker = partial(extract_one, metrics=metrics)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        extracted = list(pool.map(worker, paths))
    return cohort.merge(pd.DataFrame(extracted), on="source_h5", how="left")


def _metric_columns(spec: MetricSpec, *, sensitivity: bool = False) -> tuple[str, str]:
    name = spec.metric_id if not sensitivity else f"{spec.metric_id}_nopsd"
    return f"{name}_median", f"{name}_included"


def subject_task_table(
    recordings: pd.DataFrame,
    metrics: tuple[MetricSpec, ...] | None = None,
) -> pd.DataFrame:
    specs = metrics if metrics is not None else METRICS
    rows = []
    for (subject, task), group in recordings.groupby(["subject_id", "task_label"], dropna=False):
        row: dict[str, Any] = {
            "subject_id": subject,
            "task_label": task,
            "n_recordings": int(len(group)),
        }
        for spec in specs:
            median_col, included_col = _metric_columns(spec)
            if included_col not in group.columns or median_col not in group.columns:
                row[spec.metric_id] = float("nan")
                row[f"{spec.metric_id}_n_recordings_included"] = 0
                continue
            usable = group.loc[group[included_col] == True, median_col]  # noqa: E712
            if spec.role == "L1" and spec.family == "diffusion" and "h1_h2_support_included" in group.columns:
                usable = group.loc[
                    (group[included_col] == True) & (group["h1_h2_support_included"] == True),  # noqa: E712
                    median_col,
                ]
            values = pd.to_numeric(usable, errors="coerce").dropna()
            row[spec.metric_id] = float(values.median()) if len(values) else float("nan")
            row[f"{spec.metric_id}_n_recordings_included"] = int(len(values))
            if spec.extra_exclude_path is not None:
                sm, si = _metric_columns(spec, sensitivity=True)
                if si not in group.columns or sm not in group.columns:
                    row[f"{spec.metric_id}_nopsd"] = float("nan")
                    continue
                floor_ok = group[si] == True  # noqa: E712
                if "h1_h2_psd_floor_excluded_included" in group.columns:
                    floor_ok = floor_ok & (group["h1_h2_psd_floor_excluded_included"] == True)  # noqa: E712
                svals = pd.to_numeric(group.loc[floor_ok, sm], errors="coerce").dropna()
                row[f"{spec.metric_id}_nopsd"] = float(svals.median()) if len(svals) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def paired_differences(subjects: pd.DataFrame, contrast: ContrastSpec, metric_id: str) -> pd.DataFrame:
    later = subjects.loc[
        subjects["task_label"] == contrast.later_task,
        ["subject_id", metric_id],
    ].rename(columns={metric_id: "later"})
    earlier = subjects.loc[
        subjects["task_label"] == contrast.earlier_task,
        ["subject_id", metric_id],
    ].rename(columns={metric_id: "earlier"})
    paired = later.merge(earlier, on="subject_id", how="inner")
    paired["difference"] = paired["later"] - paired["earlier"]
    paired["contrast_id"] = contrast.contrast_id
    paired["metric"] = metric_id
    paired["test_scope"] = metric_test_scope(metric_id)
    paired["later_task"] = contrast.later_task
    paired["earlier_task"] = contrast.earlier_task
    return paired


def contrast_row(paired: pd.DataFrame, spec: MetricSpec, contrast: ContrastSpec) -> dict[str, Any]:
    diffs = pd.to_numeric(paired["difference"], errors="coerce")
    finite = diffs[np.isfinite(diffs)]
    counts = sign_test_denominator(finite.to_numpy())
    median_diff = float(np.median(finite)) if len(finite) else float("nan")
    mean_diff = float(np.mean(finite)) if len(finite) else float("nan")
    dz = cohens_dz(finite.to_numpy())
    dz_lo, dz_hi, _ = percentile_bootstrap(finite.to_numpy(), cohens_dz, n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED)
    med_lo, med_hi, n_boot = percentile_bootstrap(
        finite.to_numpy(), lambda sample: float(np.median(sample)), n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED
    )
    n_later = int(pd.to_numeric(paired["later"], errors="coerce").notna().sum())
    n_earlier = int(pd.to_numeric(paired["earlier"], errors="coerce").notna().sum())
    n_pairs = int(len(finite))
    testable = n_pairs >= MIN_TESTABLE_N and int(counts["n_nonzero"]) >= MIN_TESTABLE_N
    return {
        "family": spec.family,
        "role": spec.role,
        "level": spec.level or spec.role,
        "metric": spec.metric_id,
        "test_scope": metric_test_scope(spec.metric_id),
        "contrast_id": contrast.contrast_id,
        "later_task": contrast.later_task,
        "earlier_task": contrast.earlier_task,
        "primary_contrast": contrast.primary,
        "prediction": spec.prediction_primary if contrast.primary else "two-sided descriptive",
        "n_pairs": n_pairs,
        "n_later": n_later,
        "n_earlier": n_earlier,
        "n_zero": int(counts["n_zero"]),
        "n_nonzero": int(counts["n_nonzero"]),
        "n_positive": int(counts["n_positive"]),
        "n_negative": int(counts["n_negative"]),
        "later_median": float(np.median(pd.to_numeric(paired["later"], errors="coerce").dropna()))
        if n_later
        else float("nan"),
        "earlier_median": float(np.median(pd.to_numeric(paired["earlier"], errors="coerce").dropna()))
        if n_earlier
        else float("nan"),
        "median_paired_difference": median_diff,
        "mean_paired_difference": mean_diff,
        "median_diff_ci_lo": med_lo,
        "median_diff_ci_hi": med_hi,
        "cohens_dz": dz,
        "cohens_dz_ci_lo": dz_lo,
        "cohens_dz_ci_hi": dz_hi,
        "sign_test_p": exact_sign_test_p(finite.to_numpy()),
        "wilcoxon_p": wilcoxon_p(finite.to_numpy()),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_boot_used": n_boot,
        "family_testable": testable,
        "min_testable_n": MIN_TESTABLE_N,
        "confirmatory_status": CONFIRMATORY_STATUS,
        "scaling_note": "subject_anchored local chart geometry; occupancy != MNJ != reachability",
    }


def friedman_rows(subjects: pd.DataFrame, metrics: tuple[MetricSpec, ...]) -> pd.DataFrame:
    rows = []
    for spec in metrics:
        pivot = subjects.pivot_table(index="subject_id", columns="task_label", values=spec.metric_id)
        present = [task for task in TASKS if task in pivot.columns]
        if len(present) < 3:
            continue
        common = pivot[list(present)].dropna()
        chi2, p_value, n = friedman_p(*(common[task].to_numpy() for task in present))
        rows.append(
            {
                "family": spec.family,
                "role": spec.role,
                "level": spec.level or spec.role,
                "metric": spec.metric_id,
                "test_scope": metric_test_scope(spec.metric_id),
                "friedman_chi2": chi2,
                "friedman_p": p_value,
                "n_subjects": n,
                "tasks": "|".join(present),
            }
        )
    table = pd.DataFrame(rows)
    if not table.empty:
        table["bh_q"] = np.nan
        substantive = table["test_scope"] == "substantive"
        table.loc[substantive, "bh_q"] = bh_fdr(
            table.loc[substantive, "friedman_p"].to_numpy()
        )
    return table


def _fmt(value: float, digits: int = 4) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}g}"


def write_part1_md(
    path: Path,
    contrasts: pd.DataFrame,
    friedman: pd.DataFrame,
    missing: pd.DataFrame,
) -> None:
    substantive = contrasts[contrasts["test_scope"] == "substantive"].copy()
    qc_only = contrasts[contrasts["test_scope"] != "substantive"].copy()
    sig = substantive[(substantive["bh_q"] < 0.05) & (substantive["n_pairs"] >= 10)].copy()
    sig = sig.reindex(sig["cohens_dz"].abs().sort_values(ascending=False).index)
    top = substantive[substantive["n_pairs"] >= 10]
    top = top.reindex(top["cohens_dz"].abs().sort_values(ascending=False).index).head(12)
    lines = [
        f"# ds004511 within-subject Rest / CC / GG contrasts ({ANALYSIS_ID})",
        "",
        "Paired later-minus-earlier on subject/task medians, complete-case per contrast. "
        "BH-FDR is across the frozen occupancy + MNJ + L1 + L4-amplitude Wilcoxon family. "
        "The rank-degenerate reachability effective-dimension row is retained as QC-only "
        "and excluded from all BH/Friedman/significance families. "
        f"Status: `{CONFIRMATORY_STATUS}`. Occupancy is not MNJ and not reachability. "
        "Export is `subject_anchored`. Not confirmatory amplitude. Not consciousness.",
        "",
        f"Bootstrap {BOOTSTRAP_N}, seed {BOOTSTRAP_SEED}. "
        f"`sub-S200203` has no Gambling Game EEG (documented OpenNeuro gap).",
        "",
        "## Missingness (recordings with a finite included median)",
        "",
        "| Level | Metric | n finite / recordings |",
        "| --- | --- | ---: |",
    ]
    for _, row in missing.iterrows():
        lines.append(
            f"| {row['level']} | `{row['metric']}` | {int(row['n_finite'])}/{int(row['n_recordings'])} |"
        )
    if not friedman.empty:
        lines.extend(
            [
                "",
                "## Friedman across Rest / CC / GG (complete triplet)",
                "",
                "| Level | Metric | n | chi2 | p | BH q |",
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in friedman[friedman["test_scope"] == "substantive"].iterrows():
            lines.append(
                "| {level} | `{metric}` | {n} | {chi} | {p} | {q} |".format(
                    level=row["level"],
                    metric=row["metric"],
                    n=int(row["n_subjects"]),
                    chi=_fmt(row["friedman_chi2"]),
                    p=_fmt(row["friedman_p"]),
                    q=_fmt(row["bh_q"]),
                )
            )
    for contrast in CONTRASTS:
        block = contrasts[
            (contrasts["contrast_id"] == contrast.contrast_id)
            & (contrasts["test_scope"] == "substantive")
        ]
        later = TASK_DISPLAY.get(contrast.later_task, contrast.later_task)
        earlier = TASK_DISPLAY.get(contrast.earlier_task, contrast.earlier_task)
        lines.extend(
            [
                "",
                f"## {later} − {earlier}",
                "",
                "| Level | Metric | n | later med | earlier med | Δ med | d_z | Wilcoxon p | BH q |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in block.iterrows():
            lines.append(
                "| {level} | `{metric}` | {n} | {later} | {earlier} | {delta} | {d} | {p} | {q} |".format(
                    level=row["level"],
                    metric=row["metric"],
                    n=int(row["n_pairs"]),
                    later=_fmt(row["later_median"]),
                    earlier=_fmt(row["earlier_median"]),
                    delta=_fmt(row["median_paired_difference"]),
                    d=_fmt(row["cohens_dz"], 3),
                    p=_fmt(row["wilcoxon_p"]),
                    q=_fmt(row["bh_q"]),
                )
            )
    if not qc_only.empty:
        lines.extend(
            [
                "",
                "## QC-only reachability effective dimension (excluded from inference)",
                "",
                "`reach_d_eff` is retained below to preserve the raw degeneracy audit. "
                "Its raw Wilcoxon p-values are descriptive QC only: no BH q is assigned, "
                "and these rows are excluded from Friedman BH, FDR-significance, and |d_z| sorting.",
                "",
                "| Contrast | n | Δ med | d_z | raw Wilcoxon p |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in qc_only.iterrows():
            lines.append(
                "| `{contrast}` | {n} | {delta} | {d} | {p} |".format(
                    contrast=row["contrast_id"],
                    n=int(row["n_pairs"]),
                    delta=_fmt(row["median_paired_difference"]),
                    d=_fmt(row["cohens_dz"], 3),
                    p=_fmt(row["wilcoxon_p"]),
                )
            )
        qc_friedman = friedman[friedman["test_scope"] != "substantive"]
        if not qc_friedman.empty:
            lines.extend(
                [
                    "",
                    "## QC-only Friedman rows (excluded from inference)",
                    "",
                    "The raw omnibus QC statistic is retained, but no BH q is assigned.",
                    "",
                    "| Metric | n | chi2 | raw p |",
                    "| --- | ---: | ---: | ---: |",
                ]
            )
            for _, row in qc_friedman.iterrows():
                lines.append(
                    "| `{metric}` | {n} | {chi} | {p} |".format(
                        metric=row["metric"],
                        n=int(row["n_subjects"]),
                        chi=_fmt(row["friedman_chi2"]),
                        p=_fmt(row["friedman_p"]),
                    )
                )
    lines.extend(["", "## FDR-significant pairwise rows (n≥10, |d_z| order)", ""])
    if sig.empty:
        lines.append("No Wilcoxon BH q < 0.05 among complete-case tests with n≥10.")
    else:
        lines.extend(
            [
                "| Contrast | Level | Metric | n | Δ med | d_z | Wilcoxon p | BH q |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in sig.iterrows():
            lines.append(
                "| `{contrast}` | {level} | `{metric}` | {n} | {delta} | {d} | {p} | {q} |".format(
                    contrast=row["contrast_id"],
                    level=row["level"],
                    metric=row["metric"],
                    n=int(row["n_pairs"]),
                    delta=_fmt(row["median_paired_difference"]),
                    d=_fmt(row["cohens_dz"], 3),
                    p=_fmt(row["wilcoxon_p"]),
                    q=_fmt(row["bh_q"]),
                )
            )
    lines.extend(
        [
            "",
            "## Largest |d_z| with n≥10",
            "",
            "| Contrast | Level | Metric | n | d_z | Wilcoxon p | BH q |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in top.iterrows():
        lines.append(
            "| `{contrast}` | {level} | `{metric}` | {n} | {d} | {p} | {q} |".format(
                contrast=row["contrast_id"],
                level=row["level"],
                metric=row["metric"],
                n=int(row["n_pairs"]),
                d=_fmt(row["cohens_dz"], 3),
                p=_fmt(row["wilcoxon_p"]),
                q=_fmt(row["bh_q"]),
            )
        )
    lines.extend(
        [
            "",
            "Do not read occupancy change as a Jacobian or reachability result. "
            "Do not treat subject_anchored amplitudes as confirmatory between-subject levels.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_l1_supplement(
    output_root: Path,
    contrasts: pd.DataFrame,
    friedman: pd.DataFrame,
) -> dict[str, str]:
    """Write the complete four-metric L1 contrast/omnibus supplement tables."""
    l1_metrics = [spec.metric_id for spec in METRICS if spec.level == "L1"]
    l1_contrasts = contrasts[
        contrasts["metric"].isin(l1_metrics)
        & (contrasts["test_scope"] == "substantive")
    ].copy()
    l1_friedman = friedman[friedman["metric"].isin(l1_metrics)].copy()
    expected_contrast_rows = len(l1_metrics) * len(CONTRASTS)
    if len(l1_contrasts) != expected_contrast_rows or len(l1_friedman) != len(l1_metrics):
        raise RuntimeError(
            "L1 supplement cardinality mismatch: "
            f"contrasts={len(l1_contrasts)} expected={expected_contrast_rows}, "
            f"friedman={len(l1_friedman)} expected={len(l1_metrics)}"
        )
    contrast_path = output_root / "task_l1_supplement_contrasts.csv"
    friedman_path = output_root / "task_l1_supplement_friedman.csv"
    markdown_path = output_root / "task_l1_supplement.md"
    l1_contrasts.to_csv(contrast_path, index=False)
    l1_friedman.to_csv(friedman_path, index=False)

    lines = [
        "# ds004511 L1 local-law supplement table",
        "",
        "Complete L1 table: four frozen L1 metrics × three within-subject contrasts. "
        "BH q values use the substantive occupancy/MNJ/L1/L4-amplitude task family; "
        "reachability `d_eff` is not part of this family.",
        "",
        "## Pairwise contrasts",
        "",
        "| Contrast | Metric | n | Δ med | d_z | Wilcoxon p | BH q |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in l1_contrasts.iterrows():
        lines.append(
            "| `{contrast}` | `{metric}` | {n} | {delta} | {d} | {p} | {q} |".format(
                contrast=row["contrast_id"],
                metric=row["metric"],
                n=int(row["n_pairs"]),
                delta=_fmt(row["median_paired_difference"]),
                d=_fmt(row["cohens_dz"], 3),
                p=_fmt(row["wilcoxon_p"]),
                q=_fmt(row["bh_q"]),
            )
        )
    lines.extend(
        [
            "",
            "## Omnibus Friedman tests",
            "",
            "| Metric | n | chi2 | p | BH q |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in l1_friedman.iterrows():
        lines.append(
            "| `{metric}` | {n} | {chi} | {p} | {q} |".format(
                metric=row["metric"],
                n=int(row["n_subjects"]),
                chi=_fmt(row["friedman_chi2"]),
                p=_fmt(row["friedman_p"]),
                q=_fmt(row["bh_q"]),
            )
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "contrasts_csv": str(contrast_path),
        "friedman_csv": str(friedman_path),
        "markdown": str(markdown_path),
    }


def write_bh_comparison(
    output_root: Path,
    contrasts: pd.DataFrame,
    *,
    legacy_path: Path = LEGACY_CONTRASTS_DEFAULT,
) -> str | None:
    """Persist exact old/new BH-q differences for provenance review."""
    if not legacy_path.is_file():
        return None
    old = pd.read_csv(legacy_path)
    keys = ["contrast_id", "metric"]
    old = old[keys + ["wilcoxon_p", "bh_q"]].rename(
        columns={"wilcoxon_p": "legacy_wilcoxon_p", "bh_q": "legacy_bh_q"}
    )
    new = contrasts[keys + ["test_scope", "wilcoxon_p", "bh_q"]].rename(
        columns={"wilcoxon_p": "new_wilcoxon_p", "bh_q": "new_bh_q"}
    )
    comparison = old.merge(new, on=keys, how="outer")
    comparison["q_delta_new_minus_legacy"] = comparison["new_bh_q"] - comparison["legacy_bh_q"]
    old_q = comparison["legacy_bh_q"].to_numpy(dtype=float)
    new_q = comparison["new_bh_q"].to_numpy(dtype=float)
    comparison["q_changed"] = (
        (np.isfinite(old_q) != np.isfinite(new_q))
        | (np.isfinite(old_q) & np.isfinite(new_q) & (old_q != new_q))
    )
    comparison["comparison_status"] = np.where(
        comparison["test_scope"] == "qc_only_degenerate",
        "qc_only_removed_from_bh",
        "substantive_family_recomputed",
    )
    path = output_root / "task_bh_comparison.csv"
    comparison.to_csv(path, index=False)
    return str(path)


def write_friedman_bh_comparison(
    output_root: Path,
    friedman: pd.DataFrame,
    *,
    legacy_path: Path = ARTICLE_DIR / "results" / "v1_task_20260921" / "task_friedman.csv",
) -> str | None:
    """Persist exact old/new Friedman BH-q differences for provenance review."""
    if not legacy_path.is_file():
        return None
    old = pd.read_csv(legacy_path)
    keys = ["metric"]
    old = old[keys + ["friedman_p", "bh_q"]].rename(
        columns={"friedman_p": "legacy_friedman_p", "bh_q": "legacy_bh_q"}
    )
    new = friedman[keys + ["test_scope", "friedman_p", "bh_q"]].rename(
        columns={"friedman_p": "new_friedman_p", "bh_q": "new_bh_q"}
    )
    comparison = old.merge(new, on=keys, how="outer")
    comparison["q_delta_new_minus_legacy"] = comparison["new_bh_q"] - comparison["legacy_bh_q"]
    old_q = comparison["legacy_bh_q"].to_numpy(dtype=float)
    new_q = comparison["new_bh_q"].to_numpy(dtype=float)
    comparison["q_changed"] = (
        (np.isfinite(old_q) != np.isfinite(new_q))
        | (np.isfinite(old_q) & np.isfinite(new_q) & (old_q != new_q))
    )
    comparison["comparison_status"] = np.where(
        comparison["test_scope"] == "qc_only_degenerate",
        "qc_only_removed_from_bh",
        "substantive_family_recomputed",
    )
    path = output_root / "task_friedman_bh_comparison.csv"
    comparison.to_csv(path, index=False)
    return str(path)


def run(*, labels_path: Path, support_path: Path, output_root: Path, workers: int) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort(labels_path, support_path)
    recordings = extract_recordings(cohort, workers=workers)
    recordings.to_csv(output_root / "task_run_level.csv", index=False)
    subjects = subject_task_table(recordings)
    subjects.to_csv(output_root / "task_subject_task.csv", index=False)

    pair_frames = []
    contrast_rows = []
    for contrast in CONTRASTS:
        for spec in METRICS:
            paired = paired_differences(subjects, contrast, spec.metric_id)
            pair_frames.append(paired)
            contrast_rows.append(contrast_row(paired, spec, contrast))
    pairs = pd.concat(pair_frames, ignore_index=True)
    pairs.to_csv(output_root / "task_paired_differences.csv", index=False)
    contrasts = pd.DataFrame(contrast_rows)
    substantive = contrasts["test_scope"] == "substantive"
    contrasts["bh_q"] = np.nan
    contrasts.loc[substantive, "bh_q"] = bh_fdr(
        contrasts.loc[substantive, "wilcoxon_p"].to_numpy()
    )
    contrasts["bh_q_within_contrast"] = np.nan
    contrasts["bh_q_within_level"] = np.nan
    for _, index in contrasts.groupby("contrast_id").groups.items():
        index = [item for item in index if bool(substantive.loc[item])]
        if index:
            contrasts.loc[index, "bh_q_within_contrast"] = bh_fdr(
                contrasts.loc[index, "wilcoxon_p"].to_numpy()
            )
    for _, index in contrasts.groupby("level").groups.items():
        index = [item for item in index if bool(substantive.loc[item])]
        if index:
            contrasts.loc[index, "bh_q_within_level"] = bh_fdr(
                contrasts.loc[index, "wilcoxon_p"].to_numpy()
            )
    contrasts.to_csv(output_root / "task_contrasts.csv", index=False)

    friedman = friedman_rows(subjects, METRICS)
    friedman.to_csv(output_root / "task_friedman.csv", index=False)
    friedman_bh_comparison_path = write_friedman_bh_comparison(output_root, friedman)

    missing_rows = []
    for spec in METRICS:
        median_col, included_col = _metric_columns(spec)
        finite = pd.to_numeric(
            recordings.loc[recordings[included_col] == True, median_col],  # noqa: E712
            errors="coerce",
        )
        missing_rows.append(
            {
                "level": spec.level or spec.role,
                "metric": spec.metric_id,
                "n_recordings": int(len(recordings)),
                "n_finite": int(finite.notna().sum()),
            }
        )
    missing = pd.DataFrame(missing_rows)
    missing.to_csv(output_root / "task_missingness.csv", index=False)
    write_part1_md(output_root / "task_part1.md", contrasts, friedman, missing)
    l1_paths = write_l1_supplement(output_root, contrasts, friedman)
    bh_comparison_path = write_bh_comparison(output_root, contrasts)

    usable = contrasts[
        (contrasts["test_scope"] == "substantive") & (contrasts["n_pairs"] >= 10)
    ]
    top = usable.reindex(usable["cohens_dz"].abs().sort_values(ascending=False).index).head(12)
    manifest = {
        "schema": "ds004511_ndt_v1.task_contrasts.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_status": CONFIRMATORY_STATUS,
        "confirmatory_contrasts": False,
        "n_recordings": int(len(recordings)),
        "n_subjects": int(recordings["subject_id"].nunique()),
        "n_metrics": int(len(METRICS)),
        "n_contrasts": int(len(CONTRASTS)),
        "n_tests_in_bh_family": int(
            contrasts.loc[contrasts["test_scope"] == "substantive", "wilcoxon_p"].notna().sum()
        ),
        "n_tests_in_friedman_bh_family": int(
            friedman.loc[friedman["test_scope"] == "substantive", "friedman_p"].notna().sum()
        ),
        "n_bh_q_lt_0_05": int(
            ((contrasts["test_scope"] == "substantive")
             & (contrasts["bh_q"] < 0.05)
             & (contrasts["n_pairs"] >= 10)).sum()
        ),
        "n_qc_only_metrics": int(len(QC_ONLY_METRIC_IDS)),
        "qc_only_metric_ids": sorted(QC_ONLY_METRIC_IDS),
        "n_qc_only_wilcoxon_rows": int((contrasts["test_scope"] != "substantive").sum()),
        "substantive_metric_ids": list(SUBSTANTIVE_METRIC_IDS),
        "l1_supplement_paths": l1_paths,
        "bh_comparison_path": bh_comparison_path,
        "friedman_bh_comparison_path": friedman_bh_comparison_path,
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "labels_sha256": sha256_file(labels_path) if labels_path.is_file() else None,
        "h5_root": str(DEFAULT_H5_ROOT),
        "largest_abs_dz": top[
            ["level", "contrast_id", "metric", "n_pairs", "cohens_dz", "wilcoxon_p", "bh_q"]
        ].to_dict("records"),
        "note": (
            "Complete-case within-subject Rest/CC/GG contrasts on occupancy, MNJ, L1 local law, "
            "and recording-level reachability summaries. reach_d_eff is QC-only and excluded "
            "from substantive Wilcoxon/Friedman BH families and significance sorting. G3/G4 not locked."
        ),
    }
    write_json(output_root / "task_part1_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--support", type=Path, default=SUPPORT_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    manifest = run(
        labels_path=args.labels,
        support_path=args.support,
        output_root=args.output_root,
        workers=args.workers,
    )
    print(json.dumps({
        "output_root": str(args.output_root),
        "n_bh_q_lt_0_05": manifest.get("n_bh_q_lt_0_05"),
        "n_tests_in_bh_family": manifest.get("n_tests_in_bh_family"),
        "largest_abs_dz": (manifest.get("largest_abs_dz") or [])[:8],
        "confirmatory_status": manifest.get("confirmatory_status"),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
