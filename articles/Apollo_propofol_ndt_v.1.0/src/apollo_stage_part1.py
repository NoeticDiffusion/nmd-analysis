"""Within-subject Apollo stage contrasts. Exploratory; G4 not locked.

Recording median -> subject/phase median -> paired later-minus-earlier.
No between-subject pooling of subject_anchored amplitudes as confirmatory.
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

from apollo_aggregate import recording_median, sign_test_denominator
from apollo_common import (
    ARTICLE_DIR,
    DEFAULT_H5_ROOT,
    MIN_VALID_FRACTION,
    MIN_VALID_TIMEPOINTS,
    json_safe,
    scalar,
    sha256_file,
    write_json,
)
from apollo_panel import (
    ANALYSIS_ID,
    BOOTSTRAP_N,
    BOOTSTRAP_SEED,
    CONFIRMATORY_STATUS,
    CONTRASTS,
    METRICS,
    MIN_TESTABLE_N,
    ContrastSpec,
    MetricSpec,
)
from apollo_stats import bh_fdr, cohens_dz, exact_sign_test_p, holm, percentile_bootstrap, wilcoxon_p

LABELS_DEFAULT = ARTICLE_DIR / "results" / "ingest_20260920" / "g1_recording_labels.csv"
SUPPORT_DEFAULT = ARTICLE_DIR / "results" / "ingest_20260920" / "g2_recording_support.csv"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_stage_20260921"


def _read_array(handle: h5py.File, path: str | None) -> np.ndarray | None:
    if path is None or path not in handle:
        return None
    node = handle[path]
    if isinstance(node, h5py.Group):
        return None
    return np.asarray(node[()], dtype=float)


def reduce_series(array: np.ndarray, reduce: str | None) -> np.ndarray:
    values = np.asarray(array, dtype=float)
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
    if status != "computed":
        out[f"{prefix}_reason"] = f"computation_status={status}"
        return out
    if spec.grain == "summary":
        raw = _read_array(handle, spec.value_path)
        values = None if raw is None else reduce_series(raw, spec.reduce)
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
    values = reduce_series(raw, spec.reduce)
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


def load_cohort(
    labels_path: Path,
    support_path: Path,
) -> pd.DataFrame:
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
    if merged["protocol_phase_label"].isna().any():
        raise RuntimeError("stage analysis requires G1 labels on every recording")
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


def subject_phase_table(
    recordings: pd.DataFrame,
    metrics: tuple[MetricSpec, ...] | None = None,
) -> pd.DataFrame:
    specs = metrics if metrics is not None else METRICS
    rows = []
    for (subject, phase), group in recordings.groupby(["subject_id", "protocol_phase_label"], dropna=False):
        row: dict[str, Any] = {
            "subject_id": subject,
            "protocol_phase_label": phase,
            "n_recordings": int(len(group)),
        }
        for spec in specs:
            median_col, included_col = _metric_columns(spec)
            if included_col not in group.columns or median_col not in group.columns:
                row[spec.metric_id] = float("nan")
                row[f"{spec.metric_id}_n_recordings_included"] = 0
                continue
            usable = group.loc[group[included_col] == True, median_col]  # noqa: E712
            if spec.role in {"H1", "H2"} and "h1_h2_support_included" in group.columns:
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
        subjects["protocol_phase_label"] == contrast.later_phase,
        ["subject_id", metric_id],
    ].rename(columns={metric_id: "later"})
    earlier = subjects.loc[
        subjects["protocol_phase_label"] == contrast.earlier_phase,
        ["subject_id", metric_id],
    ].rename(columns={metric_id: "earlier"})
    paired = later.merge(earlier, on="subject_id", how="inner")
    paired["difference"] = paired["later"] - paired["earlier"]
    paired["contrast_id"] = contrast.contrast_id
    paired["metric"] = metric_id
    paired["later_phase"] = contrast.later_phase
    paired["earlier_phase"] = contrast.earlier_phase
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
        "metric": spec.metric_id,
        "contrast_id": contrast.contrast_id,
        "later_phase": contrast.later_phase,
        "earlier_phase": contrast.earlier_phase,
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
        "scaling_note": "subject_anchored local chart geometry; not confirmatory absolute amplitude",
    }


def write_part1_md(path: Path, contrasts: pd.DataFrame, missing: pd.DataFrame) -> None:
    primary = contrasts[contrasts["contrast_id"] == "first_sedation_minus_baseline"].copy()
    sig = contrasts[contrasts["bh_q"] < 0.05].copy()
    sig = sig.reindex(sig["cohens_dz"].abs().sort_values(ascending=False).index)
    lines = [
        f"# Apollo within-subject stage contrasts ({ANALYSIS_ID})",
        "",
        "Paired later-minus-earlier on subject/phase medians. "
        "Holm is only H1/H2 sign tests on first sedation minus baseline. "
        "BH-FDR is across the frozen 15-metric × 6-contrast Wilcoxon family. "
        f"Status: `{CONFIRMATORY_STATUS}`. Not consciousness. Not confirmatory amplitude.",
        "",
        f"Subjects with both primary phases: see `n_pairs` in the primary block. Bootstrap {BOOTSTRAP_N}, seed {BOOTSTRAP_SEED}.",
        "",
        "## Missingness (recordings with a finite included median)",
        "",
        "| Metric | n finite / 80 |",
        "| --- | ---: |",
    ]
    for _, row in missing.iterrows():
        lines.append(f"| `{row['metric']}` | {int(row['n_finite'])}/{int(row['n_recordings'])} |")
    lines.extend(
        [
            "",
            "## Primary contrast: first protocol sedation − pre-drug baseline",
            "",
            "| Role | Metric | n | later med | base med | Δ med | d_z | sign p | Holm p | BH q |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in primary.iterrows():
        holm_p = row.get("holm_p_h1h2")
        holm_txt = f"{holm_p:.4g}" if pd.notna(holm_p) else "-"
        lines.append(
            "| {role} | `{metric}` | {n} | {later:.4g} | {base:.4g} | {delta:.4g} | {d:.3f} | {p:.4g} | {holm} | {q:.4g} |".format(
                role=row["role"],
                metric=row["metric"],
                n=int(row["n_pairs"]),
                later=row["later_median"],
                base=row["earlier_median"],
                delta=row["median_paired_difference"],
                d=row["cohens_dz"],
                p=row["sign_test_p"],
                holm=holm_txt,
                q=row["bh_q"],
            )
        )
    lines.extend(["", "## FDR-significant discovery rows (|d_z| order)", ""])
    if sig.empty:
        lines.append("No Wilcoxon BH q < 0.05 in the frozen family.")
    else:
        lines.extend(
            [
                "| Contrast | Metric | n | Δ med | d_z | Wilcoxon p | BH q |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in sig.iterrows():
            lines.append(
                "| `{contrast}` | `{metric}` | {n} | {delta:.4g} | {d:.3f} | {p:.4g} | {q:.4g} |".format(
                    contrast=row["contrast_id"],
                    metric=row["metric"],
                    n=int(row["n_pairs"]),
                    delta=row["median_paired_difference"],
                    d=row["cohens_dz"],
                    p=row["wilcoxon_p"],
                    q=row["bh_q"],
                )
            )
    lines.extend(
        [
            "",
            "Do not read protocol phase 3 as unresponsiveness. Do not treat recovery as a guaranteed reversal.",
            "H1/H2 remain exploratory local chart geometry because the export is `subject_anchored` with ComBat disabled.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, support_path: Path, output_root: Path, workers: int) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort(labels_path, support_path)
    recordings = extract_recordings(cohort, workers=workers)
    recordings.to_csv(output_root / "stage_run_level.csv", index=False)
    subjects = subject_phase_table(recordings)
    subjects.to_csv(output_root / "stage_subject_phase.csv", index=False)

    pair_frames = []
    contrast_rows = []
    for contrast in CONTRASTS:
        for spec in METRICS:
            paired = paired_differences(subjects, contrast, spec.metric_id)
            pair_frames.append(paired)
            contrast_rows.append(contrast_row(paired, spec, contrast))
    pairs = pd.concat(pair_frames, ignore_index=True)
    pairs.to_csv(output_root / "stage_paired_differences.csv", index=False)
    contrasts = pd.DataFrame(contrast_rows)
    contrasts["bh_q"] = bh_fdr(contrasts["wilcoxon_p"].to_numpy())
    contrasts["bh_q_within_contrast"] = np.nan
    for contrast_id, index in contrasts.groupby("contrast_id").groups.items():
        contrasts.loc[list(index), "bh_q_within_contrast"] = bh_fdr(
            contrasts.loc[list(index), "wilcoxon_p"].to_numpy()
        )
    holm_mask = (
        (contrasts["contrast_id"] == "first_sedation_minus_baseline")
        & (contrasts["metric"].isin(["diffusion_total", "diffusion_effective_dimension"]))
    )
    contrasts["holm_p_h1h2"] = np.nan
    if holm_mask.any():
        contrasts.loc[holm_mask, "holm_p_h1h2"] = holm(contrasts.loc[holm_mask, "sign_test_p"].tolist())
    contrasts.to_csv(output_root / "stage_contrasts.csv", index=False)

    missing_rows = []
    for spec in METRICS:
        median_col, included_col = _metric_columns(spec)
        finite = pd.to_numeric(recordings.loc[recordings[included_col] == True, median_col], errors="coerce")  # noqa: E712
        missing_rows.append(
            {
                "metric": spec.metric_id,
                "n_recordings": int(len(recordings)),
                "n_finite": int(finite.notna().sum()),
            }
        )
    missing = pd.DataFrame(missing_rows)
    missing.to_csv(output_root / "stage_missingness.csv", index=False)
    write_part1_md(output_root / "stage_part1.md", contrasts, missing)

    top = contrasts.reindex(contrasts["cohens_dz"].abs().sort_values(ascending=False).index).head(12)
    manifest = {
        "schema": "apollo_propofol_ndt_v1.stage_contrasts.v1",
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
        "n_tests_in_bh_family": int(len(contrasts)),
        "n_bh_q_lt_0_05": int((contrasts["bh_q"] < 0.05).sum()),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "labels_sha256": sha256_file(labels_path) if labels_path.is_file() else None,
        "h5_root": str(DEFAULT_H5_ROOT),
        "largest_abs_dz": top[["contrast_id", "metric", "cohens_dz", "wilcoxon_p", "bh_q"]].to_dict("records"),
        "note": (
            "Within-subject paired differences on a panel frozen 2026-09-21. "
            "G3 independent review and G4 lock were not completed before this user-requested analysis."
        ),
    }
    write_json(output_root / "stage_part1_manifest.json", json_safe(manifest))
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
        "largest_abs_dz": manifest.get("largest_abs_dz")[:8],
        "confirmatory_status": manifest.get("confirmatory_status"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
